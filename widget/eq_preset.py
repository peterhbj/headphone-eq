#!/usr/bin/env python3
"""Writes the Easy Effects presets for the music popup's equalizer.

live_eq      the popup's ten sliders only.
live_eq_*    for each headphone in DEVICES_FILE, its AutoEq correction, then the sliders.

DEVICES_FILE maps a sink to {"profile": "<name> ParametricEQ.txt", "preset": "live_eq_..."};
autoeq-setup fills it. Prints the preset for the output in use.

Usage: eq_preset.py STATE_FILE PRESET_DIR DEVICES_FILE
"""
import json
import os
import re
import subprocess
import sys
import tempfile

FREQS = [32, 40, 50, 63, 80, 100, 125, 160, 200, 250, 315, 400, 500, 630, 800, 1000,
         1250, 1600, 2000, 2500, 3150, 4000, 5000, 6300, 8000, 10000, 12500, 16000,
         20000, 22000, 24000, 24000]
# Slider n drives every third band, starting at 32 Hz.
SLIDER_BANDS = {0: 0, 1: 3, 2: 6, 3: 9, 4: 12, 5: 15, 6: 18, 7: 21, 8: 24, 9: 27}
AUTOEQ_TYPES = {"PK": "Bell", "LSC": "Lo-shelf", "HSC": "Hi-shelf"}


def band(freq, gain, q, kind="Bell", mode="RLC (BT)"):
    return {"type": kind, "mode": mode, "slope": "x1", "frequency": freq, "gain": gain,
            "q": q, "width": 1.0, "mute": False, "solo": False}


def equalizer(bands, input_gain=0.0):
    numbered = {f"band{i}": b for i, b in enumerate(bands)}
    return {"bypass": False, "input-gain": input_gain, "output-gain": 0.0,
            "left": numbered, "right": numbered, "mode": "IIR",
            "num-bands": len(bands), "split-channels": False}


def sliders(state):
    gains = [float(state[f"b{i + 1}"]) for i in range(10)]
    bands = []
    for i, freq in enumerate(FREQS):
        gain = next((gains[s] for s, b in SLIDER_BANDS.items() if b == i), 0.0)
        bands.append(band(freq, gain, 1.0))
    return equalizer(bands)


def correction(path):
    """An AutoEq ParametricEQ.txt as an equalizer using Equalizer APO's filters."""
    preamp = 0.0
    bands = []
    for line in open(path):
        if m := re.match(r"Preamp:\s*(-?[\d.]+)", line):
            preamp = float(m.group(1))
        elif m := re.match(r"Filter \d+: ON (\w+) Fc (-?[\d.]+) Hz Gain (-?[\d.]+) dB Q ([\d.]+)", line):
            kind, fc, gain, q = m.groups()
            bands.append(band(float(fc), float(gain), float(q), AUTOEQ_TYPES[kind], "APO (DR)"))
    return equalizer(bands, preamp)


def write(path, preset):
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path))
    with os.fdopen(fd, "w") as f:
        json.dump(preset, f, indent=4)
    os.replace(tmp, path)


def current_preset(devices):
    """The correction belongs only on the headphones it was measured for. With Easy
    Effects as the default sink, a registered device that is connected is the one playing."""
    pactl = lambda *a: subprocess.run(["pactl", *a], capture_output=True, text=True).stdout
    default = pactl("get-default-sink").strip()
    connected = [line.split("\t")[1] for line in pactl("list", "sinks", "short").splitlines()]
    playing = [default] if default != "easyeffects_sink" else connected
    for sink in playing:
        for key, device in devices.items():
            if sink == key or sink.startswith(key + "."):
                return device["preset"]
    return "live_eq"


def main():
    state_file, preset_dir, devices_file = sys.argv[1:4]
    taste = sliders(json.load(open(state_file)))
    write(os.path.join(preset_dir, "live_eq.json"), {"output": {
        "blocklist": [], "plugins_order": ["equalizer#0"], "equalizer#0": taste}})
    devices = {}
    if os.path.isfile(devices_file):
        devices = {k: d for k, d in json.load(open(devices_file)).items()
                   if os.path.isfile(os.path.join(os.path.dirname(devices_file), d["profile"]))}
    for device in devices.values():
        profile = os.path.join(os.path.dirname(devices_file), device["profile"])
        write(os.path.join(preset_dir, device["preset"] + ".json"), {"output": {
            "blocklist": [], "plugins_order": ["equalizer#0", "equalizer#1"],
            "equalizer#0": correction(profile), "equalizer#1": taste}})
    print(current_preset(devices))


if __name__ == "__main__":
    main()
