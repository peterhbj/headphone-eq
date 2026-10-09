#!/usr/bin/env bash
# Instala a correção AutoEq dos fones no EasyEffects e no widget de música
# do serpantinum. Faz backup de cada arquivo que já existe antes de sobrescrever.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
widget="$HOME/.local/share/serpantinum/src/quickshell/media"
ee="$HOME/.local/share/easyeffects"
profiles="$HOME/.local/share/autoeq-profiles"

backup() {
    if [ -e "$1" ] && [ ! -e "$1.bak-pre-autoeq" ]; then
        cp "$1" "$1.bak-pre-autoeq"
    fi
}

mkdir -p "$profiles" "$ee/output" "$ee/autoload/output"
cp "$here/profiles/"*.txt "$profiles/"
# devices.json é o registro dos fones; o autoeq-setup acrescenta neles, então não sobrescreve.
[ -e "$profiles/devices.json" ] || cp "$here/profiles/devices.json" "$profiles/"

if [ -d "$widget" ]; then
    backup "$widget/equalizer.sh"
    install -m755 "$here/widget/equalizer.sh" "$widget/equalizer.sh"
    install -m644 "$here/widget/eq_preset.py" "$widget/eq_preset.py"
else
    echo "aviso: widget do serpantinum não encontrado em $widget; só o EasyEffects será configurado" >&2
fi

for preset in "$here/easyeffects/"*.json; do
    backup "$ee/output/$(basename "$preset")"
    cp "$preset" "$ee/output/"
done

# Escreve cada arquivo de autoload atomicamente: o EasyEffects observa a pasta
# e já caiu uma vez lendo um arquivo pela metade.
for rule in "$here/easyeffects/autoload/"*.json; do
    tmp="$(mktemp "$ee/autoload/output/.tmp.XXXXXX")"
    cp "$rule" "$tmp"
    mv "$tmp" "$ee/autoload/output/$(basename "$rule")"
done

if [ -x "$widget/equalizer.sh" ]; then
    "$widget/equalizer.sh" apply
else
    state="$(mktemp)"
    echo '{"b1":0,"b2":0,"b3":0,"b4":0,"b5":0,"b6":0,"b7":0,"b8":0,"b9":0,"b10":0}' > "$state"
    setsid -f easyeffects -l "$(python3 "$here/widget/eq_preset.py" "$state" "$ee/output" "$profiles/devices.json")" >/dev/null 2>&1
    rm -f "$state"
fi
echo "pronto. Para outro fone, conecte-o e rode ./autoeq-setup"
