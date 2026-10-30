<div align="center">

<img src="Resources/art/icon_256.png" width="140" alt="Massive PSXL icon"/>

# ðŸŽ¹ Massive PSXL

### A wavetable synthesizer by **Phil S Audio** ðŸŽ›ï¸

`VST3` Â· `Audio Unit` Â· `Standalone` Â· ðŸŽ **macOS Apple Silicon (M1/M2/M3)**

</div>

---

> âš ï¸ **Status: code-complete, first build pending.** This source was written on a Windows PC that can't produce macOS
> binaries, so it has **not been compiled or run yet** ðŸ§ª. Expect a short round of compile fixes on the very first
> build. The GitHub Actions workflow in this repo is the fastest way to find and fix them. See [ðŸ”¨ Building](#-building).

## âœ¨ Features

| | Area | What you get |
|---|---|---|
| ðŸ”Š | **Engine** | 16 voices (poly / mono / legato), glide, microtuning |
| ðŸŒŠ | **Oscillators** | 2 wavetable oscillators Â· 10 built-in tables Â· drag-and-drop audio import Â· unison Ã—8 Â· detune Â· phase mod Â· wavefold |
| ðŸŒ«ï¸ | **Noise** | White / pink / brown / crackle with colour control |
| ðŸ§ª | **Filters** | 2 filters Ã— 4 models: **Ladder**, **State Variable**, **Comb**, **Formant** |
| ðŸ’¥ | **Insert + FX** | 6 insert distortions Â· EQ Â· distortion Â· chorus Â· tempo-synced stereo delay Â· reverb |
| ðŸŽšï¸ | **Modulation** | Amp envelope + 8 envelope/LFO slots Â· 3 Ã— 16-step performers Â· 16 macros Â· velocity, key track, random, mod wheel, aftertouch, pitch bend |
| ðŸ“ˆ | **Live visuals** | Moving playheads on every envelope and LFO Â· glowing signal wires |
| ðŸ”Œ | **Routing** | Drag-wire node editor. **Load Init (Blank)** starts with *no* connections |
| ðŸª„ | **Smart macros** | Drag a macro onto a knob and it **renames itself** to that knob. The host-visible name updates instantly ðŸ“Ÿ |
| ðŸŽ¹ | **Keyboard** | Pull-down on-screen keyboard with pitch + mod wheels Â· keys light up for incoming MIDI |
| ðŸŒ— | **Themes** | Light and dark mode Â· resize 75 â€“ 200 % |
| â†©ï¸ | **Workflow** | Undo/redo Â· MIDI learn Â· preset browser Â· performer pattern templates |
| ðŸŽ¼ | **Presets** | **117 original factory presets** across 8 categories |

## ðŸŽ¼ Factory presets

| ðŸŽ¸ Bass | ðŸŽ¤ Leads | ðŸŒŒ Pads | ðŸª• Plucks | ðŸŽ¹ Keys | ðŸ¥ Drums | ðŸ›¸ FX | ðŸ” Sequence |
|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| 20 | 19 | 20 | 15 | 10 | 15 | 10 | 8 |

Your own presets live in `~/Music/Phil S Audio/Massive PSXL/Presets` ðŸ“

## ðŸ”¨ Building

### Option A Â· â˜ï¸ Let GitHub build it (no Mac needed)
1. Push to GitHub (already done if you're reading this there ðŸ˜„).
2. Open the **Actions** tab â†’ **Build Massive PSXL (macOS arm64)** â†’ **Run workflow**.
3. After ~10â€“15 minutes, download the **`Massive-PSXL-macOS-arm64`** artifact. It contains the `.pkg` installer ðŸ“¦.
4. If the build fails, open the failed step and copy the error lines. The first run may well fail, which is expected âœ….

### Option B Â· ðŸ’» Build on your MacBook
```bash
xcode-select --install            # command-line tools (skip if installed)
brew install cmake                # needs Homebrew

git clone https://github.com/philscottcanada/massive-psxl.git
cd massive-psxl

cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release --parallel     # first build: ~5-15 min (compiles JUCE too) â˜•
```

Then check the sound engine ðŸ§ª and install it:
```bash
build/PSXLTest_artefacts/Release/psxl_test ./test_audio    # offline test, writes a few .wav files
bash installer/install_local.sh build                       # installs for your user, no password
```
Restart your DAW and rescan plug-ins ðŸ”„.

> ðŸ›¡ï¸ **macOS blocking it?** Builds are ad-hoc signed. If macOS refuses a *downloaded* installer or plug-in, right-click â†’
> **Open**, or run `xattr -dr com.apple.quarantine <path>`. Anything you build yourself runs without this.

## ðŸ“ Where things install

| ðŸ§© Format | ðŸ“‚ Location |
|---|---|
| **VST3** | `/Library/Audio/Plug-Ins/VST3/Phil S Audio/Massive PSXL.vst3` â† appears under **Phil S Audio** ðŸŽ‰ |
| **Audio Unit** | `/Library/Audio/Plug-Ins/Components/Massive PSXL.component` *(macOS doesn't allow AU sub-folders; hosts group it by the manufacturer name "Phil S Audio")* |
| **Standalone** | `/Applications/Phil S Audio/Massive PSXL.app` |

## ðŸš€ Quick start

1. Open the standalone app (or load the plug-in in your DAW).
2. Menu â†’ **Load Init (Blank)** â†’ the synth is silent on purpose ðŸ¤«
3. Open the **Routing** tab and drag a wire from **Osc 1** â†’ **Filter 1** â†’ **Out** ðŸ”Œ
4. Play the keyboard ðŸŽ¹ (click **Keys** to pull it down) or send MIDI.
5. Drag a **macro** chip from the bottom strip onto **Filter 1 Cutoff** and watch the macro rename itself ðŸª„

## ðŸ—‚ï¸ Project layout

```
ðŸ“ Source/       plug-in code   (dsp/ = engine, ui/ = editor)
ðŸ“ Resources/    art/ (icon, backgrounds, NKS artwork) Â· presets/factory_presets.xml
ðŸ“ tools/        gen_presets.py Â· gen_art.py Â· docs generators
ðŸ“ installer/    macOS .pkg builder + local install script
ðŸ“ nks/          NKS notes + controller page map
ðŸ“ tests/        offline engine test
ðŸ“ docs/         manual + video scripts (PDF)
ðŸ“ .github/      macOS CI build
```

## ðŸ“š Documentation ðŸ“–
- ðŸ“˜ **User manual + tutorials** â†’ `docs/Massive_PSXL_Manual.pdf`
- ðŸŽ¬ **Video scripts** (for NotebookLM / Gemini) â†’ `docs/video_scripts/`

## ðŸŽ›ï¸ NKS (Native Kontrol Standard)

| âœ… Ready | â³ Needs Native Instruments |
|---|---|
| Parameter pages (macros first) Â· live macro names Â· artwork Â· categories | Official NKS badge Â· `.nksf` preset files Â· Komplete Kontrol browser listing (free NKS Developer Kit, by application) |

Details in [`nks/README.md`](nks/README.md).

## ðŸ§¾ Good to know

- ðŸ” **Signing:** local builds are ad-hoc signed. To share with others you need an Apple Developer ID (+ notarisation). The installer script supports `DEVELOPER_ID_APP`, `DEVELOPER_ID_INSTALLER`, `NOTARY_PROFILE`.
- âš–ï¸ **JUCE licence:** JUCE is AGPLv3 or commercial. Distributing closed-source needs a JUCE commercial licence. Keep this repo **private** unless you're open-sourcing it.
- ðŸŽ¨ **Originality:** presets, wavetables, artwork and UI are all original. No third-party preset content was copied or converted.
- ðŸ‘‚ **Not tuned by ear yet:** sounds were designed from parameter knowledge, so expect to tweak them.

---

<div align="center">

Made with ðŸ’œ by **Phil S Audio** ðŸŽ¶

</div>
