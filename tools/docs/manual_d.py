"""Manual part D: NKS, reference tables, shortcuts, troubleshooting, glossary, preset appendix."""
import os
import xml.etree.ElementTree as ET

import psxl_docs as D
from psxl_docs import *
import params_data


def ch17_nks():
    st = [Banner(17, "NKS Status", "What is and is not implemented, stated plainly")]
    st += [
        P("NKS (Native Kontrol Standard) is a standard, owned by Native Instruments, that lets compatible hardware and software browse presets and control plug-ins through "
          "eight-knob pages. This chapter is the one place in the manual that names it, and it is deliberately factual."),
        callout("warn", "<b>Massive PSXL is not an officially NKS-certified product.</b> It does not carry the NKS logo, is not listed in any NKS browser, and ships no .nksf preset files. "
                        "Nothing here has been tested with NKS hardware."),
        H2("17.1  What is implemented in the plug-in"),
    ]
    st += bullets([
        "<b>Parameter exposure.</b> Every sound parameter is a normal host-automatable parameter organised into groups (VST3 units) that follow the eight-parameter page idea: both Macro groups come first, then Oscillator 1, Oscillator 2, Noise, Filter 1, Filter 2, Insert + Amp, Voice + Master, the amp envelope, eight modulators, three Performers and the effects.",
        "<b>Smart macro naming.</b> A macro takes the name of the knob it controls, and the plug-in tells the host that parameter information changed, so hosts and controllers that read parameter names can show 'Filter 1 Cutoff' instead of 'Macro 1' (chapter 12). Names are saved in presets and plug-in state.",
        "<b>A page map.</b> The file <b>nks/psxl_nks_pages.json</b> in the project lists 24 intended eight-parameter controller pages (Macros 1-8 and 9-16 first, then Oscillators, Noise + Filter 1, Filter 2, Insert + Amp, Voice, Amp Envelope, Mod 2 to Mod 9, three Performers, EQ, Delay + Reverb and Chorus + Dist).",
        "<b>Provisional artwork.</b> Plug-in logos, banners and eight category tiles (bass, leads, pads, plucks, keys, drums, fx, sequence) are in Resources/art/nks. The sizes are placeholders and must be checked against the official requirements.",
        "<b>Categories.</b> Presets are organised as Bass, Leads, Pads, Plucks, Keys, Drums, FX and Sequence.",
    ])
    st += [
        H2("17.2  What is not possible without the standard's owner"),
    ]
    st += bullets([
        "The <b>NKS developer kit, the NKS logo and a partner listing</b> are issued by Native Instruments on application. Until a product is approved it cannot use the NKS badge or appear in their browser.",
        "<b>.nksf preset files</b> (the preset format used by NKS browsers) and the exact artwork specifications come from that kit. Once available, the factory presets can be converted using the page map and artwork described above.",
    ])
    st += [
        H2("17.3  What to expect today"),
        P("In NKS-capable host software the plug-in should behave as a normal VST3 or Audio Unit in generic plug-in mode, where parameter pages follow the host's parameter order. "
          "Because the macros are first, the first pages of controls are the macros with their automatic names. This is the intended behaviour; it has not been verified on hardware."),
        callout("tip", "Whatever your hardware, you can get the benefit today: assign your eight favourite controls to Macros 1 to 8, let the automatic names appear, and map your controller's knobs to those macros "
                       "(through your host's parameter mapping, or with MIDI Learn on the macro knobs)."),
    ]
    return st


def ch18_reference():
    st = [Banner(18, "Parameter Reference", "Every parameter, range and default")]
    secs = params_data.sections()
    total = sum(len(r) for _, _, r in secs)
    st += [
        P(f"Massive PSXL has <b>{total} automatable parameters</b>. The tables list the parameter ID (as used by hosts and in preset files), the on-screen or host name, the range, the default and notes. "
          "The last column says whether the parameter can be a modulation target: <b>V</b> = voice modulation (any source), <b>G</b> = global (macros, mod wheel, aftertouch, pitch bend only), "
          "blank = not modulatable."),
        P("Discrete parameters show their choices in the Range column. The Mode of each filter is stored as a number (Mode 1 to Mode 4) and shown with names depending on the Model."),
    ]
    for title, group, rows in secs:
        if title.startswith("Modulator") and title != "Modulator 2":
            continue
        head = [H3(title + ("   (host group: " + group + ")" if group != title else ""))]
        data = [["ID", "Name", "Range", "Default", "Notes", "Mod"]]
        for r in rows:
            data.append([f"<font name='Courier' size='7.4'>{r[0]}</font>", r[1], r[2], r[3], r[4], r[5]])
        if title == "Modulator 2":
            title_note = P("The eight modulator slots share the same layout. Slot 2 is shown here as the example: for Mod 3 to Mod 9 replace the prefix <font name='Courier'>m2_</font> with "
                           "<font name='Courier'>m3_</font> ... <font name='Courier'>m9_</font> and 'Mod 2' with 'Mod 3' ... 'Mod 9'. All slots default to Type = Envelope. The Amp Envelope uses prefix <font name='Courier'>m1_</font> and has no Type, Rate, Shape, Phase, Fade In, Bipolar, Sync or Division.", "small")
            st += head + [title_note]
        else:
            st += head
        st.append(tbl(data, [0.95, 1.3, 1.15, 0.6, 2.05, 0.5], font="cell7", align_center=(5,)))
        st.append(spacer(3))
    st += [
        H2("18.1  Quick counts"),
        tbl([["Item", "Count"],
             ["Parameters", str(total)],
             ["Modulation sources", "34 (9 envelope/LFO slots including the amp envelope, 3 Performers, 16 macros, Velocity, Key Track, Random, Mod Wheel, Aftertouch, Pitch Bend)"],
             ["Modulation destinations", "42 (28 voice, 14 global)"],
             ["Maximum modulation assignments", "256"],
             ["Routing nodes / possible wires", "7 nodes; 6 sources (Osc 1, Osc 2, Noise, Filter 1, Filter 2, Insert) and 4 destinations (Filter 1, Filter 2, Insert, Out); 14 possible wires"],
             ["Wavetable slots", "32 (10 built in, 22 user)"],
             ["Wavetable frame size", "2048 samples, up to 256 frames"],
             ["Voices", "up to 16"]],
            [1.6, 4], first_bold=True),
    ]
    return st


def ch19_shortcuts():
    st = [Banner(19, "Mouse and Keyboard Reference", "Every gesture in one place")]
    st += [
        tbl([["Where", "Gesture", "Result"],
             ["Any knob", "Drag up / right (down / left)", "Increase (decrease) the value"],
             ["Any knob", "Mouse wheel", "Nudge the value"],
             ["Any knob", "Hover", "Label turns into the exact value and unit"],
             ["Any knob", "Right-click", "MIDI Learn, Clear MIDI mapping, Reset to default; Edit amount / Remove for each modulation source"],
             ["Any knob", "Drop a chip on it", "Create a modulation assignment (amount +0.5)"],
             ["Modulation chip", "Drag onto a knob", "Assign (a crosshair follows the pointer)"],
             ["Macro chip (M1 to M16)", "Double-click or right-click", "Rename macro; Reset name"],
             ["Wavetable display", "Click / drag", "Set Pos"],
             ["Wavetable display", "Drop an audio file", "Import it as a wavetable on the open oscillator"],
             ["Routing view", "Drag from an output port to an input port", "Create a wire"],
             ["Routing view", "Click a wire, then Delete or Backspace", "Remove the wire"],
             ["Routing view", "Double-click a wire", "Remove it"],
             ["Routing view", "Right-click a wire", "Remove connection; Gain 25, 50, 75, 100, 150%"],
             ["Routing view", "Right-click empty space", "Quick setups; Clear all connections"],
             ["Envelope display", "Drag the three handles", "Attack; Decay and Sustain; Release"],
             ["Performer bars", "Click or drag", "Set step heights"],
             ["Preset list", "Click; double-click; Return", "Load; load and close; load"],
             ["Top bar < >", "Click", "Previous / next preset"],
             ["Preset name button", "Click", "Open / close the browser"],
             ["On-screen keys", "Click (height sets velocity)", "Play a note"],
             ["Pitch / Mod wheels", "Drag", "Pitch bend (springs back) / mod wheel (stays)"],
             ["Window corner", "Drag", "Resize (75 to 200 percent, fixed shape)"],
             ["Dialogs", "Return / Escape", "OK or Save / Cancel"]],
            [1.4, 2, 2.6], first_bold=True),
        spacer(4),
        callout("note", "Massive PSXL does not define its own global keyboard shortcuts. Your host may provide shortcuts of its own for Undo / Redo."),
    ]
    return st


def ch20_trouble():
    st = [Banner(20, "Troubleshooting", "When something does not behave")]
    rows = [["Symptom", "Likely cause", "What to do"],
            ["No sound at all after Load Init (Blank)", "Init (Blank) has no routing.", "Open the Routing tab and connect a source through to Out, or right-click empty space and choose a quick setup (chapter 5)."],
            ["No sound, but wires exist", "A node in the chain has no input, a Level or Amp Level is 0, Volume is 0, or the amp envelope is silent (Sustain 0 with a very short Decay).", "Follow the glowing wires; check the node activity meters; raise Level, Amp Level and Volume."],
            ["Drums only blip, or cut off when I release the key", "The amp envelope is not OneShot, or its Sustain is above 0.", "Turn OneShot on in the Amp Env tab and set Sustain to 0."],
            ["A modulation does nothing", "The source is voice-type and the target is a master effect, or the amount is 0, or the source is idle (an envelope with Sustain 0, or a Performer with Steps at zero height).", "Check the toast. For effects use a macro, mod wheel or aftertouch. Right-click the knob and check Edit amount."],
            ["Toast: 'Voice modulators can't control global effects'", "You dropped an envelope, LFO, Performer, Velocity, Key Track or Random on a master-effect knob.", "Use a macro (and drive the macro from a controller or automation), mod wheel or aftertouch."],
            ["Toast: 'Signal flows left to right...'", "You tried to connect backwards or to a source node.", "Connect only to a later node: Osc/Noise > Filter 1 > Filter 2 > Insert > Out."],
            ["The plug-in does not appear in my DAW", "Not installed, wrong folder, or the host has not rescanned.", "Check the install paths in chapter 2 and rescan plug-ins. Logic runs its own Audio Unit validation for new components."],
            ["macOS says the plug-in or installer cannot be opened", "Ad-hoc signed, not notarised, and quarantined by a download.", "Control-click the installer and choose Open, use Privacy and Security > Open Anyway, or clear the quarantine flag as shown in chapter 2."],
            ["Crackling, dropouts or high CPU", "Too many unison voices, high polyphony or a small audio buffer.", "Reduce Unison, Polyphony or the number of held notes; raise the buffer size."],
            ["Stuck note", "A missing note-off or sustain pedal state.", "Send All Notes Off from the host or stop and restart playback; release the sustain pedal."],
            ["Delay or LFO timing is wrong", "No host tempo is available.", "Without a host tempo (for example in the standalone app) synced features use 120 BPM. Use a DAW tempo or turn Sync off."],
            ["Wavetable import fails ('Could not read that audio file')", "Unsupported or damaged file.", "Use WAV, AIFF, FLAC or OGG. Make sure the file is longer than a few dozen samples."],
            ["Imported wavetable sounds like noise", "The file is not a single-cycle waveform; it is being sliced into 2048-sample frames.", "Prepare a single cycle, or use Pos to find the musical region and treat it as a texture."],
            ["A preset sounds different from my last session", "A wavetable that the preset needs was not saved, or tuning was changed.", "Factory presets use only built-in tables. Check the tuning in the Voice tab and reset to 12-TET if needed."],
            ["Macro name does not update on my controller", "The host does not refresh parameter names live.", "Reload the plug-in window or re-select the plug-in in the host's parameter list."],
            ["Pitch arpeggio is slightly out of tune", "Performer steps are continuous values drawn by hand.", "Increase the interface size, or write exact values into a .psxlperf pattern file (chapter 11, tutorial 22)."],
            ["Interface too small or too large", "Display scaling.", "Menu > Settings > Interface size, or drag the window corner."]]
    st.append(tbl(rows, [1.5, 1.8, 2.5], first_bold=False))
    return st


GLOSSARY = [
    ("Amp envelope", "The envelope (slot 1) that shapes each note's loudness."),
    ("Amount", "How strongly a source moves a destination, -1 to +1, as a fraction of the knob's travel."),
    ("Assignment", "A source-to-destination modulation link with an amount."),
    ("Band-limited", "Containing no harmonics above half the sample rate, which avoids aliasing."),
    ("Bipolar", "Swinging both above and below zero (-1 to +1)."),
    ("Chip", "The small crosshair control you drag onto a knob to assign a modulation source."),
    ("Comb filter", "A short feedback delay that makes regularly spaced resonances."),
    ("Cutoff", "The frequency where a filter begins to act (the vowel selector in the Formant model)."),
    ("Destination", "A knob that can be modulated."),
    ("Detune", "The spread in cents between unison voices."),
    ("Division", "A musical note length (1/4, 1/8T and so on) used by synced LFOs, Performers and the delay."),
    ("Envelope", "A shape that evolves over a note: delay, attack, hold, decay, sustain, release."),
    ("Fold", "A wavefolder that reflects a wave back on itself."),
    ("Formant", "A resonant peak of the vocal tract; three of them make a vowel."),
    ("Frame", "One single-cycle waveform inside a wavetable."),
    ("Glide", "Portamento: sliding pitch between notes."),
    ("Init (Blank)", "The default sound with no routing and no modulation."),
    ("Insert", "The per-voice waveshaping node."),
    ("Key Track", "Making a filter or modulation follow the pitch of the note played."),
    ("Legato", "A voice mode where overlapping notes change pitch without retriggering."),
    ("LFO", "Low-frequency oscillator, a repeating modulation shape."),
    ("Macro", "A knob that you assign to other knobs; it takes the name of the first target."),
    ("Mip level", "A progressively band-limited version of a wavetable used at higher pitches."),
    ("Node", "A box in the Routing view (Osc, Noise, Filter, Insert, Out)."),
    ("One Shot", "An envelope that ignores key release."),
    ("Performer", "A 16-step modulation sequencer."),
    ("Phase Mod", "Phase modulation of one oscillator by the other (FM-like)."),
    ("Port", "The circle on a node's edge where wires start and end."),
    ("Reso", "Resonance: emphasis at the filter's cutoff."),
    ("Routing", "Which sources feed which processors, shown as wires."),
    ("Sample and Hold", "An LFO shape that picks a random value each cycle and holds it."),
    ("Scala", "A file format (.scl) describing musical scales for microtuning."),
    ("Source", "Anything that modulates: envelopes, LFOs, Performers, macros, controllers."),
    ("Unison", "Several detuned copies of an oscillator played together."),
    ("Wavetable", "A set of frames scanned by the Pos control."),
    ("Wire", "A connection between two node ports. It glows with the passing audio."),
]


def ch21_glossary():
    st = [Banner(21, "Glossary", "Terms used in this manual")]
    st.append(tbl([["Term", "Meaning"]] + [[a, b] for a, b in GLOSSARY], [1.1, 4.6], first_bold=True))
    return st


def appendix_presets():
    path = os.path.join(D.ROOT, "Resources", "presets", "factory_presets.xml")
    root = ET.parse(path).getroot()
    cats = {}
    for e in root.findall("PSXL"):
        cats.setdefault(e.get("category"), []).append(e.get("name"))
    order = ["Bass", "Leads", "Pads", "Plucks", "Keys", "Drums", "FX", "Sequence"]
    st = [Banner("A", "Factory Presets", "All 117 presets by category")]
    total = sum(len(v) for v in cats.values())
    st.append(P(f"The browser shows presets sorted by category, then name. Total: <b>{total}</b>."))
    for c in order:
        names = sorted(cats.get(c, []), key=str.lower)
        st.append(H3(f"{c}  ({len(names)})"))
        n = len(names)
        half = (n + 2) // 3
        cols = [names[i * half:(i + 1) * half] for i in range(3)]
        rows = []
        for i in range(half):
            rows.append([cols[k][i] if i < len(cols[k]) else "" for k in range(3)])
        st.append(tbl(rows, [1, 1, 1], header=False, zebra=True))
        st.append(spacer(2))
    return st


def build():
    return [ch17_nks(), ch18_reference(), ch19_shortcuts(), ch20_trouble(), ch21_glossary()], appendix_presets()
