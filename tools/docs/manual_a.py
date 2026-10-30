"""Manual part A: front matter and chapters 1-5."""
import psxl_docs as D
from psxl_docs import *


def front_matter():
    st = []
    st.append(Heading("About this manual", S["h2"], 0, "About this manual"))
    st += [
        P("This manual documents Massive PSXL version 1.0.0 by Phil S Audio exactly as the plug-in is built. "
          "Part I is the reference manual. Part II is a set of step-by-step tutorials that start from "
          "<b>Load Init (Blank)</b> and build real sounds. Appendix A lists the 117 factory presets."),
        H3("Conventions"),
    ]
    st += bullets([
        "<b>Bold</b> text is something you can see on screen: a button, tab, knob label, menu item or panel.",
        "<b>Menu > Settings > Interface size</b> means: press the Menu button, open the Settings sub-menu, then choose Interface size.",
        "Knob values are written the way the knob shows them: 0 to 1 amounts, Hz, seconds, semitones (st) or cents (ct).",
        "Modulation amounts run from -1 to +1 and are fractions of the target knob's full travel (chapter 11).",
        "Middle C is MIDI note 60 and is labelled C3 on the on-screen keyboard.",
        "Values in tutorials are <b>starting points</b>: adjust them by ear.",
    ])
    st.append(callout("note", "The interface drawings in this manual are schematic illustrations drawn from the plug-in's layout, not screenshots. "
                              "Names, tab order and menu wording follow the plug-in's source code."))
    st.append(H3("What is in the box"))
    st += bullets([
        "<b>Massive PSXL.vst3</b> (VST3 plug-in), <b>Massive PSXL.component</b> (Audio Unit) and <b>Massive PSXL.app</b> (standalone), built for Apple Silicon Macs.",
        "117 original factory presets in 8 categories (Bass, Leads, Pads, Plucks, Keys, Drums, FX, Sequence).",
        "10 built-in wavetables, plus 22 slots for your own.",
    ])
    return st


def ch1():
    st = [Banner(1, "Welcome", "What Massive PSXL is and what it can do")]
    st += [
        P("Massive PSXL is a wavetable synthesizer. Two oscillators scan through tables of waveforms, three sources "
          "(Oscillator 1, Oscillator 2 and a noise generator) feed a patchable chain of two filters and an insert effect, "
          "and a master effects section finishes the sound. Everything you hear can be shaped by envelopes, LFOs, "
          "step-sequence Performers, macros and performance controllers."),
        P("The design idea is a <b>visible signal path</b>. Instead of a fixed chain, the <b>Routing</b> tab is a node editor: you "
          "see the oscillators, filters and insert as boxes and connect them with wires that glow with the audio passing through them."),
        H2("Feature summary"),
    ]
    rows = [["Area", "What you get"],
            ["Oscillators", "2 wavetable oscillators. Unison of 1 to 8 voices with detune, Phase Mod (each oscillator can phase-modulate the other), Fold, Pitch +/-48 st, Fine +/-100 ct."],
            ["Wavetables", "10 built-in tables of 32 frames each; import WAV, AIFF, FLAC or OGG files into 22 user slots. Band-limited playback."],
            ["Noise", "White, Pink, Brown and Crackle noise with a low-pass/high-pass Color control."],
            ["Filters", "2 filters, each with 4 models (Ladder, State Variable, Comb, Formant) and 4 modes per model, plus Drive and Key Track."],
            ["Insert", "6 per-voice shapers: TanH, Fold, Bitcrush, Hard Clip, Rectify, Sine."],
            ["Routing", "Node editor: any source can feed any later node (Osc 1/2/Noise to Filter 1, Filter 2, Insert, Out). Per-wire gain up to 150 percent."],
            ["Amp", "Amp envelope, Level, Pan, Feedback and velocity sensitivity."],
            ["Master FX", "EQ (low shelf, mid peak, high shelf), Distortion, Chorus, tempo-syncable stereo Delay, Reverb."],
            ["Modulation", "Amp envelope + 8 slots (each an envelope or LFO), 3 Performers (16-step sequencers), 16 Macros, Velocity, Key Track, Random, Mod Wheel, Aftertouch, Pitch Bend. 42 destinations, up to 256 assignments."],
            ["Voices", "Poly (1 to 16 voices), Mono and Legato modes, glide (linear or exponential), pitch bend range 0 to 24 st, sustain pedal."],
            ["Tuning", "Scala (.scl) microtuning, reset to 12-tone equal temperament."],
            ["Presets", "117 factory presets, searchable browser, user presets in your Music folder, Mutate (subtle / wild)."],
            ["Workflow", "Undo / Redo, MIDI Learn on any parameter, drag-to-assign modulation, smart macro naming, light and dark themes, resizable interface (75 to 200 percent), on-screen keyboard with pitch and mod wheels."]]
    st.append(tbl(rows, [1.1, 4.5], first_bold=True))
    st += [
        H2("Formats and requirements"),
        tbl([["Item", "Detail"],
             ["Formats", "VST3, Audio Unit (AU, instrument) and Standalone application."],
             ["Platform", "macOS 11.0 or later on Apple Silicon (M1, M2, M3 and later). The default build is native arm64; the project can also be built as a universal (arm64 + x86_64) binary."],
             ["Audio", "Stereo output, no audio input. Works at any sample rate your host provides."],
             ["MIDI", "Receives notes, velocity, pitch bend, mod wheel (CC 1), sustain (CC 64), channel pressure and learnable CCs."],
             ["Plug-in IDs", "Manufacturer code PhSA, plug-in code Psxl (used for Audio Unit validation)."]],
            [1, 4.6], first_bold=True),
        spacer(4),
        H2("How a sound is made (the short version)"),
    ]
    st += numbered([
        "<b>Sources</b> make raw sound: Osc 1, Osc 2 and Noise.",
        "The <b>Routing</b> view sends sources through <b>Filter 1</b>, <b>Filter 2</b> and the <b>Insert</b> and finally to <b>Out</b>.",
        "The <b>amp envelope</b>, level and pan turn that into a note you play. This part runs once per voice.",
        "All voices are summed and pass through the <b>master effects</b> (EQ, Distortion, Chorus, Delay, Reverb) and the master Volume.",
        "<b>Modulators</b> (envelopes, LFOs, Performers, macros, controllers) move the knobs while you play.",
    ])
    return st


def ch2():
    st = [Banner(2, "Installation", "macOS package, per-user script and first launch")]
    st += [
        P("Massive PSXL is built for macOS on Apple Silicon. There are two ways to install it: the installer package (recommended) "
          "and a per-user script that needs no administrator password."),
        H2("Installer package"),
    ]
    st += numbered([
        "Open <b>Massive-PSXL-1.0.0.pkg</b> and follow the installer. It needs an administrator password because it installs to the system-wide folders.",
        "The package installs three items (below). A plain zip of the same three bundles is also produced for manual installs.",
        "Restart your DAW, or rescan plug-ins, so it finds the new instrument.",
    ])
    st.append(tbl([
        ["Item", "Installed to"],
        ["VST3 plug-in", "/Library/Audio/Plug-Ins/VST3/Phil S Audio/Massive PSXL.vst3"],
        ["Audio Unit", "/Library/Audio/Plug-Ins/Components/Massive PSXL.component  (grouped under the manufacturer name Phil S Audio)"],
        ["Standalone app", "/Applications/Phil S Audio/Massive PSXL.app"],
    ], [1, 4.6], first_bold=True))
    st += [
        spacer(4),
        callout("note", "The VST3 goes in a <b>Phil S Audio</b> sub-folder, so in hosts that show folders it appears under that name."),
        H2("Per-user install script (no password)"),
        P("If you build the plug-in from source, or you just want a copy for your own user account, run the script from the project folder:"),
        Paragraph("<font name='Courier' size='8.5'>installer/install_local.sh [build-dir]</font>", S["body"]),
        P("The build folder defaults to <b>build</b>. The script copies the three bundles to your home folder, "
          "signs each one with an ad-hoc signature, and restarts the Audio Unit registrar so hosts see the new plug-in:"),
        tbl([["Item", "Installed to"],
             ["VST3", "~/Library/Audio/Plug-Ins/VST3/Phil S Audio/Massive PSXL.vst3"],
             ["Audio Unit", "~/Library/Audio/Plug-Ins/Components/Massive PSXL.component"],
             ["Standalone", "~/Applications/Phil S Audio/Massive PSXL.app"]],
            [1, 4.6], first_bold=True),
        H2("Building from source (developers)"),
        P("The project uses CMake and fetches JUCE 8.0.8 automatically. On an Apple Silicon Mac:"),
        Paragraph("<font name='Courier' size='8.5'>cmake -S . -B build -DCMAKE_BUILD_TYPE=Release<br/>"
                  "cmake --build build --config Release --parallel<br/>"
                  "bash installer/build_installer.sh build</font>", S["body"]),
        P("The last command produces <b>dist/Massive-PSXL-1.0.0.pkg</b> and a zip of the plug-in bundles. Add <b>-DPSXL_UNIVERSAL=ON</b> to the first command for a universal binary."),
        H2("Gatekeeper and ad-hoc signing"),
        P("Apple Silicon Macs refuse to load unsigned native code, so the installer script signs the bundles with an <b>ad-hoc signature</b> "
          "(identity \"-\"). An ad-hoc signature satisfies the CPU requirement but is <b>not</b> a Developer ID signature and is not notarised. "
          "Unless the package was signed and notarised with a Developer ID by the person who built it, macOS may show a warning the first time."),
    ]
    st += bullets([
        "<b>Installer blocked:</b> Control-click (right-click) the .pkg and choose <b>Open</b>, then confirm. Or open <b>System Settings > Privacy and Security</b> and press <b>Open Anyway</b> next to the blocked item.",
        "<b>Plug-in or app blocked after a download:</b> remove the quarantine flag in Terminal, for example:<br/>"
        "<font name='Courier' size='8'>xattr -dr com.apple.quarantine \"/Library/Audio/Plug-Ins/VST3/Phil S Audio/Massive PSXL.vst3\"</font>",
        "Repeat for the .component and .app if needed. Files you build and install yourself with <b>install_local.sh</b> are not quarantined.",
    ])
    st += [
        H2("First launch"),
    ]
    st += numbered([
        "<b>Standalone:</b> open <b>Massive PSXL.app</b> from /Applications/Phil S Audio. Use the standalone window's audio and MIDI settings to choose your interface and keyboard.",
        "<b>In a DAW:</b> create an instrument track and choose <b>Massive PSXL</b> (manufacturer Phil S Audio). Logic Pro lists it as an Audio Unit instrument; other hosts list the VST3.",
        "A brand-new instance starts as <b>Init (Blank)</b>: the <b>Routing</b> tab is open and the synth is silent until you connect something or load a preset. That is expected: see chapter 3.",
        "Click <b>Keys</b> in the top bar to pull down the on-screen keyboard, or play your MIDI keyboard.",
    ])
    st.append(callout("tip", "If a host does not list the plug-in, rescan plug-ins. For Audio Units, Logic runs its own validation on new components; "
                             "the project also includes a validation step using Apple's <b>auval</b> tool (type aumu, subtype Psxl, manufacturer PhSA)."))
    st += [
        H2("Where Massive PSXL keeps its files"),
        tbl([["What", "Location"],
             ["User presets", "~/Music/Phil S Audio/Massive PSXL/Presets/  (files end in .psxlpreset; presets saved in a category go in a sub-folder)"],
             ["Performer patterns", "~/Music/Phil S Audio/Massive PSXL/Presets/Patterns/  (.psxlperf)"],
             ["Settings (theme, size, keyboard)", "~/Library/Application Support/Phil S Audio/Massive PSXL.settings"],
             ["Factory presets and artwork", "Built into the plug-in; nothing to install separately"]],
            [1.2, 4.4], first_bold=True),
        H2("Uninstalling"),
        P("Delete the three items listed above. Your presets and settings files are separate: delete the "
          "<b>Phil S Audio</b> folders under Music and Application Support as well if you want a clean removal."),
    ]
    return st


def ch3():
    st = [Banner(3, "Quick Start", "Silence, routing, and your first note in five steps")]
    st += [
        P("Massive PSXL has two ways to start: load a ready-made <b>factory preset</b>, or build from scratch with "
          "<b>Load Init (Blank)</b>. This chapter does the second, because it teaches the most important idea in the synth: <b>nothing is "
          "connected until you connect it</b>."),
        callout("warn", "<b>Load Init (Blank)</b> resets every parameter to its default and removes all routing and all modulation. "
                        "With no routing the synth is <b>silent</b> until you connect something in the Routing tab. That is by design, not a fault."),
        H2("Step by step"),
    ]
    st += numbered([
        "<b>Load the blank slate.</b> Press <b>Menu</b> (top bar) and choose <b>Load Init (Blank)</b>. The preset name in the top bar becomes <b>Init (Blank)</b>. "
        "The <b>Routing</b> tab shows seven boxes and the message 'No routing connections - the synth is silent.'",
        "<b>Connect Osc 1 to Filter 1.</b> Put the mouse over the little circle on the <i>right edge</i> of the <b>Osc 1</b> box (its output port), "
        "press and hold, drag to the circle on the <i>left edge</i> of <b>Filter 1</b> (its input port) and release. A wire appears.",
        "<b>Connect Filter 1 to Out.</b> Drag from Filter 1's right-edge port to the left-edge port of the <b>Out</b> box.",
        "<b>Play.</b> Click <b>Keys</b> in the top bar and click a key, or play your MIDI keyboard. The wire glows while sound passes through it, and the output meters at the top right move.",
        "<b>Shape it.</b> In the <b>Osc</b> panel drag the <b>Pos</b> knob and watch the wavetable display scan through its frames. "
        "Switch the <b>Filter 1</b> panel's <b>Cutoff</b> down to make it darker.",
    ])
    st.append(node_diagram(D.FW, 130, [(0, 3), (3, 6)], title="Minimum routing: Osc 1 > Filter 1 > Out (the dashes show the order)"))
    st.append(cap("The smallest working patch. Everything else is optional."))
    st += [
        H2("Shortcut: quick setups"),
        P("Right-click an <b>empty spot</b> in the Routing view to open a menu of quick setups. They clear the routing and wire a common arrangement for you:"),
    ]
    st += bullets([
        "<b>Osc 1 > Filter 1 > Out</b>",
        "<b>Osc 1 + Osc 2 > Filter 1 > Out</b>",
        "<b>Serial: Osc 1 + 2 > Filter 1 > Filter 2 > Out</b>",
        "<b>Parallel: Osc 1 > Filter 1, Osc 2 > Filter 2 > Out</b>",
        "<b>Osc 1 + 2 + Noise > Insert > Out</b>",
        "<b>Noise > Filter 1 > Insert > Out (drums / FX)</b>",
        "<b>Clear all connections</b>",
    ])
    st += [
        H2("Make it move"),
    ]
    st += numbered([
        "Open the <b>Mod 2</b> tab (lower tab strip). Choose Type <b>LFO</b>.",
        "Drag the <b>Mod 2</b> chip (top-left of that tab) onto the <b>Cutoff</b> knob of <b>Filter 1</b>. The knob grows a coloured ring: the filter is now modulated.",
        "Right-click the Cutoff knob and choose <b>Edit amount: Mod 2</b> to change how far it sweeps.",
        "Drag macro chip <b>M1</b> (under the first knob in the macro strip) onto any knob. Macro 1 takes that knob's name automatically.",
    ])
    st += [
        H2("Or just load a preset"),
        P("Press <b>Browse</b> (next to the preset name) or the preset name itself, pick a category such as <b>Pads</b> and click a preset. "
          "A single click loads it. Double-click loads it and closes the browser. The <b>&lt;</b> and <b>&gt;</b> arrows beside the preset name step through the whole library. "
          "Factory presets already include their routing, so they sound as soon as you play."),
        H2("No sound? Checklist"),
    ]
    st += bullets([
        "Is there at least one wire from a source to <b>Out</b> (possibly through filters)? Check the Routing tab.",
        "Is the signal chain complete? A filter or insert with nothing connected into it produces nothing; any wire into Out must come from a node that has input.",
        "Is the source's <b>Level</b> up (Osc Level, Noise Level)? Is <b>Amp Level</b> and the master <b>Volume</b> above zero?",
        "Is the amp envelope Sustain and Release sensible? A Decay with Sustain 0 plays only a short blip.",
        "Is the note reaching the plug-in? The on-screen keys light when MIDI arrives.",
    ])
    return st


def ch4():
    st = [Banner(4, "Interface Tour", "Every panel, tab and button")]
    st += [
        P("The plug-in window is 1260 by 700 units (850 with the keyboard open) and scales from 75 to 200 percent. It is divided into a "
          "<b>top bar</b>, a row of <b>synth panels</b>, a <b>lower tab area</b>, the <b>macro strip</b> and an optional <b>keyboard</b>."),
        ui_layout_diagram(D.FW, keys=True),
        cap("Figure 4.1: Overview of the editor. Numbers refer to the table below."),
    ]
    rows = [["#", "Area", "What it does"],
            ["1", "Logo and name", "Massive PSXL by Phil S Audio."],
            ["2", "Menu", "Presets, Mutate, Undo/Redo, Settings and About (see 4.2)."],
            ["3", "Edit | Browse tabs, < > and preset name", "Switch between the synth and the preset browser; step through presets. Pressing the preset name toggles the browser."],
            ["4", "Volume, meters, Undo, Redo, Light/Dark, Keys", "Master volume knob, stereo output meters, undo history buttons, theme toggle, keyboard drawer."],
            ["5", "PITCH panel", "Global Pitch (+/-48 st), Glide, Voice Mode (Poly / Mono / Legato) and the Expo glide switch."],
            ["6", "Oscillator panel", "Osc 1 | Osc 2 tabs, 3D wavetable display, table selector, + import button and eight knobs."],
            ["7", "NOISE panel", "Level, Color and the noise Type."],
            ["8", "Filter panel", "Filter 1 | Filter 2 tabs, Model and Mode menus, Cutoff, Reso, Drive and KeyTrk."],
            ["9", "INSERT panel", "Insert Type, Drive and Mix."],
            ["10", "AMP panel", "Amp Level, Pan and Feedback."],
            ["11", "FX panel", "EQ, Delay, Verb, Chor and Dist tabs for the master effects."],
            ["12", "Lower tab strip", "Voice, Routing, Amp Env, Mod 2 to Mod 9, Perf 1 to Perf 3."],
            ["13", "Performance source chips", "Pitch, ModWhl, AftTch, Velocity, KeyTrk and Random chips for modulation."],
            ["14", "Macro strip", "16 macro knobs, each with an M1 to M16 assignment chip."],
            ["15", "Keyboard drawer", "Pitch and Mod wheels, octave buttons and the piano keys."]]
    st.append(tbl(rows, [0.3, 1.7, 4], first_bold=False, align_center=(0,)))
    st += [
        H2("4.1  The top bar"),
        tbl([["Control", "Function"],
             ["Menu", "Opens the main menu (4.2)."],
             ["Edit | Browse", "Two tabs. <b>Edit</b> shows the synth. <b>Browse</b> opens the preset browser over the synth panels."],
             ["< and >", "Load the previous or next preset in the full list (factory first, then your own), wrapping around."],
             ["Preset name", "Shows the current preset. Pressing it toggles the browser."],
             ["Volume knob", "The master Volume (default 0.7). It is a modulation target for macros, mod wheel and aftertouch."],
             ["Meters", "Two thin bars (left and right) at the far right; they turn amber near full level."],
             ["Undo / Redo", "Step back and forward through parameter edits, routing changes, modulation assignments and macro renames. They grey out when empty."],
             ["Light / Dark", "Toggles the theme. The button is labelled with the theme you will switch to."],
             ["Keys", "Slides the on-screen keyboard in or out. The setting is remembered."]],
            [1.1, 4.5], first_bold=True),
        H2("4.2  The Menu"),
        tbl([["Menu item", "What it does"],
             ["Load Init (Blank)", "Resets every parameter to default, clears routing, modulation and macro names, sets all Performer steps to 0.5 and names the preset 'Init (Blank)'. Silent until you route something."],
             ["Save preset...", "Opens the Browse tab, where you press <b>Save preset...</b> to name and file the sound."],
             ["Open user preset folder", "Reveals ~/Music/Phil S Audio/Massive PSXL/Presets in Finder (creating it if needed)."],
             ["Mutate sound (subtle)", "Randomly nudges the voice parameters by up to +/-6 percent of each knob's range."],
             ["Mutate sound (wild)", "The same with up to +/-25 percent. The Pitch and Fine knobs, the oscillator Levels and Amp Level are left alone."],
             ["Undo / Redo", "Same as the top-bar buttons."],
             ["Settings > Dark theme / Light theme", "Choose the theme."],
             ["Settings > Interface size", "75, 100, 125, 150, 175 or 200 percent."],
             ["Settings > Keyboard size", "2 to 8 octaves for the on-screen keyboard."],
             ["Settings > Import wavetable...", "Choose an audio file; it becomes a user wavetable on Osc 1."],
             ["Settings > Load Scala tuning (.scl)...", "Load a microtuning file."],
             ["Settings > Reset tuning to 12-TET", "Back to 12-tone equal temperament."],
             ["About Massive PSXL", "Version and credits."]],
            [1.5, 4.1], first_bold=True),
        callout("note", "Mutate changes only continuous voice parameters (oscillator position, detune, filter, insert, noise and so on). "
                        "It never changes wavetable choice, filter models, routing or the master effects. Use Undo to return."),
        H2("4.3  Knobs: the basics"),
        P("All knobs behave the same way:"),
    ]
    st += bullets([
        "<b>Drag</b> up or right to increase, down or left to decrease (about 160 pixels for the full range).",
        "<b>Mouse wheel</b> over a knob nudges it.",
        "<b>Hover</b> over a knob and its label is replaced by the exact value and unit.",
        "<b>Right-click</b> opens a menu with <b>MIDI Learn</b>, <b>Clear MIDI mapping</b> (when mapped) and <b>Reset to default</b>. A modulated knob adds <b>Edit amount</b> and <b>Remove</b> entries for each modulation source.",
        "<b>Drop a modulation chip</b> on a knob to assign it. A magenta ring appears around a knob that will accept the drop.",
        "A knob with modulation grows a <b>coloured arc</b> showing how far each source can move it, and a <b>white dot</b> showing the live value while you play.",
    ])
    st += [
        H2("4.4  Pitch panel"),
        P("The leftmost panel holds the global voice settings you reach for most:"),
        tbl([["Control", "Range / choices", "Notes"],
             ["Pitch", "-48 to +48 st (continuous)", "Transposes everything. A modulation target (the LFO vibrato target)."],
             ["Glide", "0 to 5 s", "Portamento time between notes (see chapter 13)."],
             ["Voice Mode menu", "Poly, Mono, Legato", ""],
             ["Expo", "on / off", "Exponential glide curve."]],
            [1.2, 1.6, 2.8], first_bold=True),
        H2("4.5  Oscillator panel"),
        P("Choose <b>Osc 1</b> or <b>Osc 2</b> with the tabs. The 3D <b>wavetable display</b> draws the frames of the current table as stacked waves; the highlighted line is the "
          "current <b>Pos</b>. <b>Click or drag in the display</b> to set Pos directly. The row below holds <b>&lt;</b> and <b>&gt;</b> buttons, the wavetable drop-down and a <b>+</b> button to import an audio file as a wavetable "
          "(or drop a file on the display). Eight knobs follow: <b>Pos, Pitch, Fine, Level, Unison, Detune, PhaseMod, Fold</b>. Chapter 6 describes each."),
        H2("4.6  Noise, Filter, Insert, Amp and FX panels"),
    ]
    st += bullets([
        "<b>NOISE</b>: Level, Color and a Type menu (White, Pink, Brown, Crackle).",
        "<b>Filter</b>: tabs <b>Filter 1</b> and <b>Filter 2</b>; a <b>Model</b> menu (Ladder, State Variable, Comb, Formant) and a <b>Mode</b> menu whose entries depend on the model; a large <b>Cutoff</b> knob; <b>Reso</b>, <b>Drive</b> and <b>KeyTrk</b>.",
        "<b>INSERT</b>: a Type menu (TanH, Fold, Bitcrush, Hard Clip, Rectify, Sine), <b>Drive</b> and <b>Mix</b>.",
        "<b>AMP</b>: <b>Level</b>, <b>Pan</b>, <b>Feedback</b>. The amp envelope lives in the Amp Env tab below.",
        "<b>FX</b>: tabs <b>EQ</b> (Lo Gain, Lo Freq, Mid Gain, Mid Freq, Mid Q, Hi Gain, Hi Freq), <b>Delay</b> (Time, Feedback, Mix, Sync toggle, Division), <b>Verb</b> (Size, Damping, Mix), <b>Chor</b> (Rate, Depth, Mix) and <b>Dist</b> (Drive, Mix).",
    ])
    st += [
        H2("4.7  The lower tab strip"),
        P("Fourteen tabs share the large area under the synth panels. The plug-in opens on <b>Routing</b>."),
        tbl([["Tab", "Content"],
             ["Voice", "Voice Mode, Polyphony, Glide, Bend Range, Vel Sens, Expo; a list of imported wavetables; <b>Import wavetable...</b> button; microtuning name with <b>Load Scala (.scl)...</b> and <b>12-TET</b> buttons."],
             ["Routing", "The node editor (chapter 5)."],
             ["Amp Env", "Envelope display and Delay, Attack, Hold, Decay, Sustain, Release, Env Level, OneShot."],
             ["Mod 2 to Mod 9", "Eight modulator slots. Each has a Type menu (Envelope or LFO), a source chip, and an envelope or LFO editor."],
             ["Perf 1 to Perf 3", "Three Performers: 16 draggable step bars, Steps, Rate, Smooth, Sync, Division, <b>Randomise</b> and <b>Patterns</b>."]],
            [1, 4.6], first_bold=True),
        H2("4.8  The macro strip and keyboard"),
        P("The strip along the bottom has two parts. On the left, six <b>performance-source chips</b>: <b>Pitch</b> (pitch bend), <b>ModWhl</b>, <b>AftTch</b>, <b>Velocity</b>, "
          "<b>KeyTrk</b> and <b>Random</b>. To their right are the <b>16 macro knobs</b>, each with a small crosshair chip (<b>M1</b> to <b>M16</b>) underneath. "
          "Drag any chip onto a knob to assign it. <b>Double-click</b> a macro chip (or right-click it) to rename the macro."),
        P("The <b>Keys</b> button pulls the keyboard down below the macro strip. Details are in chapter 15."),
        H2("4.9  Toasts and feedback"),
        P("Short messages appear as a coloured pill below the top bar for a few seconds, for example when a modulation is assigned, a file is imported, "
          "a preset is saved, or an action is refused (such as connecting a node backwards)."),
    ]
    return st


def ch5():
    st = [Banner(5, "Signal Flow and Routing", "The node editor and how audio travels")]
    st += [
        P("Massive PSXL does not have a fixed signal chain. The <b>Routing</b> tab shows seven nodes. You decide which sources feed which processors."),
        node_diagram(D.FW, 175, [(0, 3), (1, 3), (2, 3), (3, 4), (4, 5), (5, 6)], title="Example: everything in series"),
        cap("Figure 5.1: Seven nodes: three sources on the left, then Filter 1, Filter 2, Insert and Out."),
        H2("5.1  The seven nodes"),
        tbl([["Node", "Role", "Subtitle shows"],
             ["Osc 1, Osc 2", "Wavetable oscillators.", "The selected wavetable name."],
             ["Noise", "Noise generator.", "The noise type."],
             ["Filter 1, Filter 2", "Two independent filters.", "Model / Mode, e.g. 'Ladder / LP 24'."],
             ["Insert", "Per-voice waveshaper / distortion.", "The insert type."],
             ["Out", "The voice's stereo amp and pan, then the master effects.", "'Stereo amp'."]],
            [1.1, 2.6, 2], first_bold=True),
        P("Each node has an <b>activity meter</b> (thin bar along the bottom) and ports: an <b>output port</b> on the right edge and, for Filter 1, Filter 2, Insert and Out, an <b>input port</b> on the left edge."),
        H2("5.2  The one rule: left to right"),
        P("Signal can only flow forward. A source may feed any node that comes <b>later</b> in this order:"),
        Paragraph("<b>Osc 1, Osc 2, Noise &nbsp; > &nbsp; Filter 1 &nbsp; > &nbsp; Filter 2 &nbsp; > &nbsp; Insert &nbsp; > &nbsp; Out</b>", S["goal"]),
        tbl([["Output of", "Can connect to"],
             ["Osc 1, Osc 2, Noise", "Filter 1, Filter 2, Insert, Out"],
             ["Filter 1", "Filter 2, Insert, Out"],
             ["Filter 2", "Insert, Out"],
             ["Insert", "Out"]],
            [1.2, 3], first_bold=True),
        P("Trying to connect backwards gives a toast: <i>Signal flows left to right: Insert can't feed Filter 1</i>. While you drag a wire, valid input ports light up in amber."),
        H2("5.3  Making and removing connections"),
    ]
    st += bullets([
        "<b>Connect</b>: press on an <b>output port</b> (right edge of a node), drag to a compatible <b>input port</b> (left edge) and release. The new wire has gain 100 percent.",
        "<b>Wires glow with audio</b>: the thicker and brighter a wire, the more signal is passing through it, and small dots flow along it.",
        "<b>Select a wire</b> by clicking on it (it turns white), then press <b>Delete</b> or <b>Backspace</b> to remove it.",
        "<b>Double-click</b> a wire to remove it immediately.",
        "<b>Right-click a wire</b> for <b>Remove connection</b> and for <b>Gain 25%, 50%, 75%, 100% or 150%</b>. A wire that is not at 100 percent shows its gain in a small label at its midpoint.",
        "<b>Right-click empty space</b> for the quick setups (below) and <b>Clear all connections</b>.",
        "Many wires can enter one input: their signals are <b>summed</b>. One output can feed several inputs (fan-out).",
    ])
    st += [
        H2("5.4  Quick setups"),
        P("Quick setups replace the current routing (and can be undone with <b>Undo</b>):"),
    ]
    mini = []
    sets = [("Osc 1 > Filter 1 > Out", [(0, 3), (3, 6)]),
            ("Osc 1 + Osc 2 > Filter 1 > Out", [(0, 3), (1, 3), (3, 6)]),
            ("Serial: Osc 1 + 2 > Filter 1 > Filter 2 > Out", [(0, 3), (1, 3), (3, 4), (4, 6)]),
            ("Parallel: Osc 1 > Filter 1, Osc 2 > Filter 2 > Out", [(0, 3), (1, 4), (3, 6), (4, 6)]),
            ("Osc 1 + 2 + Noise > Insert > Out", [(0, 5), (1, 5), (2, 5), (5, 6)]),
            ("Noise > Filter 1 > Insert > Out (drums / FX)", [(2, 3), (3, 5), (5, 6)])]
    w = (D.FW - 10) / 2
    cells = [node_diagram(w, 88, wr, title=t, compact=True, subs=False) for t, wr in sets]
    t = Table([[cells[0], cells[1]], [cells[2], cells[3]], [cells[4], cells[5]]], colWidths=[w + 5, w + 5])
    t.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                           ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
    st.append(t)
    st.append(cap("Figure 5.2: The six quick setups available from the right-click menu."))
    st += [
        H2("5.5  Things to know about routing"),
    ]
    st += bullets([
        "<b>Silent by default.</b> After <b>Load Init (Blank)</b> there are no wires. With no wire into <b>Out</b> you hear nothing.",
        "<b>A processor with nothing connected to it is skipped.</b> Filter 1, Filter 2 or the Insert do nothing unless a wire enters them, and a wire from them to Out carries silence.",
        "<b>Sources always run.</b> An oscillator that is not wired still runs, so it can act as a <b>Phase Mod</b> partner for the other oscillator even though it is silent (see the FM bell tutorial).",
        "<b>Series and parallel.</b> Osc > Filter 1 > Filter 2 is series. Osc 1 > Filter 1 and Osc 2 > Filter 2, both into Out, is parallel.",
        "<b>Skipping stages.</b> Osc 1 can go straight to the Insert or to Out; Noise can bypass the filters; any filter can be bypassed.",
        "<b>Gain per wire.</b> 25 to 150 percent lets you balance sources into a filter or push a filter harder into the Insert.",
        "<b>Amp Feedback</b> (Amp panel) feeds a saturated copy of the voice's output back into <b>Filter 1</b>'s input. If Filter 1 has no input it feeds the <b>Insert</b> instead.",
        "Routing is saved in presets and in your DAW project, and is covered by <b>Undo / Redo</b>.",
    ])
    st.append(callout("tip", "A good habit when building a sound: connect the whole chain first so you can hear it, then refine. "
                             "The node activity meters and glowing wires tell you where signal is flowing and where it stops."))
    return st


def build():
    return front_matter(), [ch1(), ch2(), ch3(), ch4(), ch5()]
