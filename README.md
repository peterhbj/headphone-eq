# headphone-eq

Conecte o fone, rode um comando e ele passa a soar neutro em **todos os apps**.

```sh
./autoeq-setup
```

O script descobre qual fone está tocando, procura ele no
[AutoEq](https://github.com/jaakkopasanen/AutoEq) (mais de 8 mil perfis
medidos), baixa a curva de correção e aplica no sistema inteiro pelo
[EasyEffects](https://github.com/wwmm/easyeffects). A correção entra só quando
aquele fone é a saída de áudio. Se você troca para o alto-falante ou o HDMI,
ela sai sozinha.

É a mesma ideia da "otimização de headphone" que o Spotify testa no Android,
mas aqui vale para qualquer app (navegador, jogos, Spotifast), usa o perfil
paramétrico completo do AutoEq e se integra ao equalizador do widget de música
do serpantinum (quickshell).

## Começando

```sh
git clone git@github.com:peterhbj/headphone-eq.git
cd headphone-eq
./install.sh        # instala o widget e os presets
./autoeq-setup      # com o fone conectado: detecta e configura
```

Requisitos: PipeWire (`pactl`), EasyEffects 8, Python 3 (só biblioteca padrão),
`jq`. O widget do serpantinum é opcional; sem ele, o EasyEffects é configurado
direto.

## O que o `autoeq-setup` faz

```
saída de áudio em uso ──> nome do fone ──> índice do AutoEq ──> melhor medição
                                                                     │
  EasyEffects carrega <── preset live_eq_<fone> <── devices.json <── ParametricEQ.txt
  (e troca sozinho pela regra de autoload daquela saída)
```

1. **Detecta a saída.** Usa o sink padrão do PipeWire. Se o padrão for o
   próprio `easyeffects_sink`, usa o primeiro dispositivo bluetooth ou USB.
2. **Descobre o nome.** No bluetooth, é o nome que o fone anuncia ("JBL Live
   770NC", "WH-1000XM4"). Sufixos como "Analog Stereo" são removidos.
3. **Procura no AutoEq.** Compara com o `INDEX.md` do AutoEq, guardado em
   `~/.cache/autoeq/` por 7 dias, e tolera diferenças de escrita: "WH1000XM5"
   encontra "Sony WH-1000XM5" e "AirPods Pro 2" encontra "Apple Airpods Pro 2".
4. **Escolhe a medição.** Prioriza o nome exato e sem variante (sem "(ANC on)"),
   e entre as fontes segue a ordem de preferência do próprio AutoEq:
   oratory1990 → crinacle → Rtings → Innerfidelity → demais.
5. **Instala.** Baixa o `ParametricEQ.txt`, registra o fone em `devices.json`,
   cria a regra de autoload do EasyEffects para aquela saída e recarrega o
   widget, que gera o preset `live_eq_<fone>`.

Exemplo:

```
$ ./autoeq-setup --name "HD 600" --list
procurando no AutoEq: HD 600
  1. Sennheiser HD 600  —  oratory1990
  2. Sennheiser HD 600  —  crinacle on GRAS 43AG-7
  3. Sennheiser HD 600  —  Rtings on Bruel & Kjaer 5128
  4. Sennheiser HD 600  —  Innerfidelity
```

### Opções

| Opção | Para quê |
|---|---|
| `--list` | só mostra os candidatos, sem instalar nada |
| `--pick N` | usa o N-ésimo candidato (outra fonte, ou a variante ANC on/off) |
| `--name "..."` | procura por esse nome; necessário para fone com fio na P2, que não anuncia nome |
| `--sink NOME` | configura essa saída em vez da padrão (`pactl list sinks short`) |
| `--refresh` | baixa o índice do AutoEq de novo |
| `--no-apply` | baixa e registra, mas não mexe no EasyEffects agora |

Rodar de novo para um fone já registrado atualiza o perfil e mantém o nome do
preset.

## Como o som é processado

```
app (Spotifast, navegador, jogos...)
  └─> easyeffects_sink
        └─> equalizer#0  correção do fone (AutoEq, modo APO (DR))
        └─> equalizer#1  sliders do widget (Flat, Bass, Rock...)
              └─> fone
```

- **Correção primeiro, gosto depois.** A correção deixa o fone com resposta
  neutra, e os presets do widget somam por cima sem desfazê-la. Em **Flat**
  você ouve só a correção.
- **Só no fone certo.** `live_eq` tem só os sliders e vale para alto-falante,
  P2 e HDMI. Cada fone registrado ganha um `live_eq_<fone>`. As regras de
  autoload trocam o preset quando a saída muda, e o widget escolhe o mesmo
  preset quando você mexe nos sliders.
- **Fiel ao AutoEq.** Os filtros rodam no modo `APO (DR)` do EasyEffects, o
  mesmo biquad do Equalizer APO para o qual o AutoEq calcula os perfis, com o
  preamp do perfil para evitar clipping.

### O registro: `devices.json`

`~/.local/share/autoeq-profiles/devices.json` liga cada saída ao seu perfil:

```json
{
    "bluez_output.AA_BB_CC_DD_EE_FF": {
        "name": "JBL Live 770NC",
        "source": "Rtings on Bruel & Kjaer 5128",
        "profile": "JBL Live 770NC ParametricEQ.txt",
        "preset": "live_eq_jbl"
    }
}
```

No bluetooth, a chave é o sink sem o sufixo `.1`, que pode mudar entre
conexões. Para tirar um fone, apague a entrada e a regra dele em
`~/.local/share/easyeffects/autoload/output/`.

## Exemplo: JBL Live 770NC

O fone para o qual este repo nasceu. O `autoeq-setup` escolhe a medição
da **Rtings com o B&K 5128**, o equipamento mais preciso entre as
fontes que mediram esse fone (preamp de -3,5 dB). O perfil fica em
`profiles/` como referência:

| # | Tipo | Fc (Hz) | Ganho (dB) | Q |
|---|------|--------:|-----------:|---:|
| 1 | Low shelf | 105 | -7,0 | 0,70 |
| 2 | Peaking | 110 | -6,0 | 1,69 |
| 3 | Peaking | 504 | +3,7 | 1,02 |
| 4 | Peaking | 2450 | +3,5 | 3,16 |
| 5 | Peaking | 283 | -2,0 | 2,09 |
| 6 | High shelf | 10000 | +3,5 | 0,70 |
| 7 | Peaking | 6563 | -5,0 | 5,67 |
| 8 | Peaking | 3647 | -4,6 | 6,00 |
| 9 | Peaking | 4853 | +3,2 | 4,50 |
| 10 | Peaking | 9256 | -1,8 | 2,55 |

O Live 770NC vem de fábrica com graves bem inchados, então a correção corta
grave e abre os agudos. O **Tune 770NC** é outro fone, com outra curva: o
`autoeq-setup` distingue os dois, mas confira com `--list` se o nome anunciado
for ambíguo.

## Arquivos

| No repo | Vai para | O que é |
|---|---|---|
| `autoeq-setup` | (roda daqui) | detecta o fone, busca no AutoEq e configura |
| `install.sh` | — | instala tudo, com backup `*.bak-pre-autoeq` do que já existe |
| `widget/equalizer.sh` | `~/.local/share/serpantinum/src/quickshell/media/` | script do widget; gera os presets e carrega o do fone em uso |
| `widget/eq_preset.py` | idem | gera `live_eq` e um `live_eq_<fone>` por entrada de `devices.json` |
| `profiles/devices.json` | `~/.local/share/autoeq-profiles/` | registro saída → perfil → preset; vem vazio, o `autoeq-setup` preenche (o `install.sh` não sobrescreve) |
| `profiles/*.txt` | idem | perfis paramétricos do AutoEq |
| `easyeffects/*.json` | `~/.local/share/easyeffects/output/` | presets de referência (widget em Flat) |
| `easyeffects/autoload/*.json` | `~/.local/share/easyeffects/autoload/output/` | `live_eq` nas saídas internas de um Dell Inspiron 15 5510 (alto-falante, P2, HDMI); as dos fones o `autoeq-setup` cria |
| `patches/equalizer.sh.patch` | — | diff do `equalizer.sh` original do serpantinum para o deste repo |

## Problemas comuns

| Sintoma | Causa e solução |
|---|---|
| A correção sumiu depois de atualizar o serpantinum | A atualização sobrescreveu `equalizer.sh`. Rode `./install.sh` de novo ou aplique `patches/equalizer.sh.patch`. |
| "nada parecido com ... no AutoEq" | O nome anunciado é genérico (P2, placa USB). Use `--name` com o modelo. |
| Achou o modelo errado | `--list` para ver os candidatos e `--pick N` para escolher. |
| O som ficou com correção em dobro | Desligue o equalizador do app (no Spotifast: Configurações → Equalizador). |
| `easyeffects` aborta ao rodar por SSH ou fora da sessão | Falta `WAYLAND_DISPLAY`. Rode na sessão gráfica ou exporte `WAYLAND_DISPLAY=wayland-1`. |
| EasyEffects caiu ao instalar | Ele lê a pasta de autoload enquanto ela muda. Por isso, todos os arquivos são escritos de forma atômica. Inicie com `setsid -f easyeffects`. |

## Notas

- O EasyEffects 8 lê presets de `~/.local/share/easyeffects`. O script original
  do widget escrevia em `~/.config/easyeffects` e só funcionava porque o
  EasyEffects migrava o arquivo de pasta.
- A primeira tentativa foi a correção dentro do EQ de 10 bandas do Spotifast.
  Funciona como aproximação, mas vale só para aquele app e perde os filtros
  estreitos. O EasyEffects resolve as duas coisas.

## Créditos

Perfis do [AutoEq](https://github.com/jaakkopasanen/AutoEq) (licença MIT,
© Jaakko Pasanen), a partir de medições de oratory1990, crinacle,
[Rtings](https://www.rtings.com/) e outros.
