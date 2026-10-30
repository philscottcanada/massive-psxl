"""Manual part C: chapters 11-16 (modulation, macros, voice, presets, MIDI, themes)."""
import psxl_docs as D
from psxl_docs import *

DEST_V = [
    ("Osc 1", "Position, Pitch, Fine, Level, Detune, Phase Mod, Fold"),
    ("Osc 2", "Position, Pitch, Fine, Level, Detune, Phase Mod, Fold"),
    ("Noise", "Level, Color"),
    ("Filter 1", "Cutoff, Reso, Drive"),
    ("Filter 2", "Cutoff, Reso, Drive"),
    ("Insert and Amp", "Insert Drive, Insert Mix, Amp Level, Amp Pan, Amp Feedback"),
    ("Voice", "Pitch (the global Pitch knob)"),
]
DEST_G = [
    ("Master", "Volume"),
    ("EQ", "Low Gain, Mid Freq, Mid Gain, High Gain"),
    ("Delay", "Feedback, Mix"),
    ("Reverb", "Size, Mix"),
    ("Chorus", "Rate, Depth, Mix"),
    ("Distortion", "Drive, Mix"),
]


def ch11():
    st = [Banner(11, "Modulation", "Envelopes, LFOs, Performers, macros and controllers")]
    st += [
        P("Modulation is anything that moves a knob for you while you play. Every modulation is an <b>assignment</b>: a <b>source</b> controlling a <b>destination</b> knob by an <b>amount</b>. "
          "You can have up to 256 assignments, several sources on one knob, and one source on many knobs."),
        H2("11.1  How modulation adds up"),
        P("The destination's <b>final value</b> = knob position + (amount x source value) for every assignment, limited to the knob's range. "
          "All of it is done on the knob's own 0 to 1 travel, so the amount is a <b>fraction of the knob's full travel</b>:"),
    ]
    st += bullets([
        "An amount of <b>+0.50</b> lets the source push the knob half of its travel upward at the source's maximum; <b>-0.50</b> pulls it downward.",
        "Because Cutoff has a skewed scale, +0.4 from a 1 kHz knob position (halfway) reaches about 12.6 kHz at the source's peak.",
        "For a Pitch knob (range 96 st from -48 to +48) an amount of <b>0.125 = 12 semitones</b>, 0.25 = 24 st, and 0.003 is a gentle 0.3 st vibrato.",
        "Bipolar sources (LFO, Key Track, Random, Pitch Bend) move the value both above and below the knob; unipolar ones (envelopes, Performers, macros, wheels) move it one way from the knob position.",
    ])
    st += [
        mod_assign_diagram(D.FW),
        cap("Figure 11.1: Dragging any modulation chip onto a knob creates an assignment."),
        H2("11.2  Sources"),
        tbl([["Source", "Value range", "Scope", "Notes"],
             ["Amp Env", "0 to 1 (x Level)", "Voice", "Slot 1, always an envelope. Its chip is in the Amp Env tab."],
             ["Mod 2 to Mod 9", "Envelope 0 to 1 (x Level); LFO -1 to +1 (or 0 to +1 when Bipolar is off), x Level", "Voice", "Eight slots; each is an envelope or an LFO."],
             ["Perf 1 to Perf 3", "0 to 1", "Voice", "The current step's bar height."],
             ["Macro 1 to Macro 16", "0 to 1", "Global", "The macro knobs. Can control anything, including master effects."],
             ["Velocity", "0 to 1", "Voice", "Key velocity of the note."],
             ["Key Track", "-1 to +1", "Voice", "(note - 60) / 60, so middle C = 0, MIDI note 0 = -1 and 120 = +1."],
             ["Random", "-1 to +1", "Voice", "A new random value for each note."],
             ["Mod Wheel", "0 to 1", "Global", "MIDI CC 1 (or the on-screen Mod wheel)."],
             ["Aftertouch", "0 to 1", "Global", "MIDI channel pressure."],
             ["Pitch Bend", "-1 to +1", "Global", "The pitch wheel position (independent of Bend Range, which only controls actual pitch)."]],
            [1.1, 1.8, 0.6, 2.4], first_bold=True),
        callout("warn", "<b>Voice sources cannot control the master effects.</b> The effects process the combined signal of all notes, so a per-note envelope or LFO has no single value to apply. "
                        "Dropping one on a master-effect knob shows the toast: <i>Voice modulators can't control global effects. Use a macro, mod wheel or aftertouch.</i>"),
        H2("11.3  Envelopes"),
        P("Slot 1 (<b>Amp Env</b>) is always an envelope and controls the loudness of every note. <b>Mod 2 to Mod 9</b> can be envelopes too (Type: Envelope). "
          "All of them have the same stages:"),
        envelope_diagram(D.FW * 0.95, 150),
        cap("Figure 11.2: Delay, Attack, Hold, Decay, Sustain (while the key is down) and Release (after key up)."),
        tbl([["Knob", "Range", "Default (Amp Env / Mod)", "Meaning"],
             ["Delay", "0 to 5 s", "0", "Wait after key down before the attack begins."],
             ["Attack", "0.5 ms to 10 s", "5 ms / 10 ms", "Linear rise to the peak."],
             ["Hold", "0 to 5 s", "0", "Time spent at the peak before decay."],
             ["Decay", "1 ms to 10 s", "0.4 s", "Fall toward the Sustain level (exponential)."],
             ["Sustain", "0 to 1", "0.8 / 0.5", "Level held while the key is down."],
             ["Release", "1 ms to 10 s", "0.25 s / 0.3 s", "Fall to zero after key up (exponential)."],
             ["Env Level", "0 to 1", "1", "Scales the whole envelope's output (the 'Level' parameter)."],
             ["OneShot", "on / off", "off", "Ignores key release: the envelope plays through its stages and releases by itself."]],
            [0.8, 1.1, 1.3, 2.4], first_bold=True),
    ]
    st += bullets([
        "Decay and Release are exponential: they get (practically) all the way to their target in the time shown, which sounds natural for percussion and plucks.",
        "A new attack starts from the envelope's current value, so retriggering never clicks.",
        "<b>OneShot</b> is the key to drums: with OneShot on, a short tap plays the whole decay. For percussion also set Sustain to 0.",
        "<b>Drag the three handles</b> on the envelope display: the peak point sets Attack, the middle point sets Decay (horizontal) and Sustain (vertical), the end point sets Release. A dot shows the live position of the newest note.",
        "The voice (and its CPU use) ends when the Amp Env has finished its release.",
    ])
    st += [
        H2("11.4  LFOs"),
        P("Choose <b>Type: LFO</b> in Mod 2 to Mod 9 to make the slot an LFO. LFOs are <b>per voice</b>: each note starts its own LFO at note-on."),
        lfo_shapes_diagram(D.FW),
        cap("Figure 11.3: The seven LFO shapes."),
        tbl([["Control", "Range", "Default", "Meaning"],
             ["Shape", "Sine, Triangle, Saw Up, Saw Down, Square, Sample & Hold, Smooth Random", "Sine", "Waveform. Sample & Hold picks a new random level each cycle; Smooth Random glides between them."],
             ["Rate", "0.01 to 50 Hz", "2 Hz", "Speed (when Sync is off)."],
             ["Sync / Division", "off, on / 1/1 to 1/16T", "off / 1/4", "With Sync on, the Rate knob is replaced by a Division menu and the LFO follows host tempo (120 BPM if none)."],
             ["Phase", "0 to 1", "0", "Where in its cycle the LFO starts at each note-on."],
             ["Fade In", "0 to 10 s", "0", "Fades the LFO in after note-on (delayed vibrato)."],
             ["Level", "0 to 1", "1", "Output depth."],
             ["Bipolar", "on / off", "on", "On: swings -1 to +1 around the knob. Off: only 0 to +1 (it never pulls the knob below its setting)."]],
            [1, 2.3, 0.8, 1.7], first_bold=True),
        H2("11.5  Performers"),
        P("A <b>Performer</b> is a 16-step sequencer that outputs a value between 0 and 1 per step. There are three. Draw the steps in the <b>Perf 1, 2, 3</b> tabs, then drag the Performer's chip onto any knob."),
        performer_diagram(D.FW * 0.95, 130),
        cap("Figure 11.4: Steps 1 to 8 loop (Steps = 8). The outlined bar is the step currently playing."),
        tbl([["Control", "Range", "Default", "Meaning"],
             ["Steps", "1 to 16", "8", "Loop length. Bars beyond Steps are dimmed."],
             ["Sync / Division", "on, off / 1/1 to 1/16T", "on / 1/16", "With Sync on, one step lasts one Division at the host tempo."],
             ["Rate", "0.1 to 40 Hz", "4 Hz", "Steps per second when Sync is off."],
             ["Smooth", "0 to 1", "0", "Glide between steps; 1 glides across the whole step, 0 jumps."],
             ["Randomise", "button", "", "Fills the bars with random values."],
             ["Patterns", "menu", "", "Ramp up, Ramp down, Triangle, Alternate high / low, Random, Flat (centre), All zero, Gate: on/off pairs; Save pattern...; Load pattern..."]],
            [1.2, 1.7, 0.8, 1.9], first_bold=True),
    ]
    st += bullets([
        "<b>Click or drag across the bars</b> to draw values. Bar height is the modulation value.",
        "Each note has its own Performer position that restarts at <b>note-on</b>, so chords played together stay in step.",
        "The steps are shared by all notes and saved in presets.",
        "<b>Save pattern...</b> writes a small text file (.psxlperf, sixteen comma-separated values between 0 and 1) to the Presets/Patterns folder. <b>Load pattern...</b> reads one back. You can write exact values yourself in a text editor: this is the precise way to program pitch arpeggios.",
        "Typical uses: pitch (arpeggio), Amp Level (gate), Filter 1 Cutoff (stepped filter), Osc Position (stepping timbre), Pan, Insert Mix.",
    ])
    st += [
        H2("11.6  Macros and performance sources"),
        P("The 16 <b>macros</b> are knobs in the bottom strip. A macro does nothing by itself: assign it to one or more knobs and it moves them all. "
          "Macros are global, so they can control master effects. They are normal host-automatable parameters, and can be MIDI-learned. Chapter 12 explains automatic naming."),
        P("The six chips at the left of the macro strip are the performance sources: <b>Pitch</b> (pitch bend), <b>ModWhl</b>, <b>AftTch</b>, <b>Velocity</b>, <b>KeyTrk</b> and <b>Random</b>. "
          "Their chips are green; Mod chips are cyan, Performer chips amber and macro chips magenta."),
        H2("11.7  Assigning, editing and removing"),
    ]
    st += numbered([
        "Make the destination knob visible (for example open the Filter 1 tab, or the Osc 2 tab).",
        "Press and drag a <b>chip</b>: a crosshair appears under the pointer. Chips live in: the top-left of each Mod tab, the Amp Env tab, each Perf tab, and the macro strip.",
        "Drop it on the knob. A toast confirms: <i>Mod 2 now controls Filter 1 Cutoff</i>. The default amount is <b>+0.50</b>.",
        "To change the amount, <b>right-click the knob</b> and choose <b>Edit amount: Mod 2 (50%)</b>. A small slider from -1 to +1 appears; drag it and listen. Negative values invert the effect.",
        "To remove, right-click the knob and choose <b>Remove Mod 2</b>.",
        "Dropping the same chip on the same knob again simply resets its amount to 0.5.",
    ])
    st += bullets([
        "A knob with modulation shows a coloured <b>ring</b> in the source's colour: it is the range the source can reach. A <b>white dot</b> shows the live modulated value.",
        "A source chip is brighter when it is in use.",
        "Assignments, amounts and macro names are saved in presets and your DAW project, and are covered by Undo / Redo (editing the amount slider is applied live and not stored as separate undo steps).",
        "Not every knob can be modulated: see the destination list below. Switches, menus, Unison, the wavetable choice, filter Model/Mode, KeyTrk, envelope and LFO settings themselves cannot be modulated.",
    ])
    st += [
        H2("11.8  Modulation destinations (42)"),
        P("<b>Voice destinations</b> (28) can be controlled by any source:"),
        tbl([["Section", "Destinations"]] + [[a, b] for a, b in DEST_V], [1, 4.6], first_bold=True),
        spacer(4),
        P("<b>Global destinations</b> (14) are the master effects and volume. Only macros, Mod Wheel, Aftertouch and Pitch Bend can control them:"),
        tbl([["Section", "Destinations"]] + [[a, b] for a, b in DEST_G], [1, 4.6], first_bold=True),
    ]
    return st


def ch12():
    st = [Banner(12, "Smart Macro Naming", "Macros take the name of what they control")]
    st += [
        P("When you drag a macro chip onto a knob, the macro is automatically <b>renamed after the knob</b>. The label under the macro knob changes from 'Macro 1' to, for example, "
          "'Filter 1 Cutoff'. This also changes the <b>parameter name that the plug-in reports to your host</b>. Controllers and hardware that display parameter names "
          "(see the note below) therefore show a meaningful label instead of 'Macro 1'."),
        H2("12.1  The rules"),
    ]
    st += bullets([
        "A macro takes the <b>full parameter name of the first knob</b> it is dropped on, such as 'Filter 1 Cutoff', 'Osc 1 Position', 'Reverb Mix' or 'Amp Feedback'. The toast reads: <i>Macro 1 now controls Filter 1 Cutoff (macro renamed to \"Filter 1 Cutoff\")</i>.",
        "Dropping the same macro on more knobs <b>keeps the first name</b>, so a macro that controls Dist Drive and Dist Mix stays 'Dist Drive'.",
        "If you <b>remove the macro's last assignment</b> and you never renamed it by hand, the name returns to 'Macro n'.",
        "If you <b>rename a macro yourself</b> (double-click its chip, or right-click the chip and choose <b>Rename macro...</b>), your name is kept until you choose <b>Reset name</b>. Typing an empty name also resets it.",
        "Names are limited to 32 characters when generated and are saved in presets and in the DAW project.",
        "Renaming and assignment are undoable.",
    ])
    st += [
        H2("12.2  Renaming by hand"),
        P("Double-click a macro chip (the small crosshair under the macro knob). A dialog titled <b>Rename Macro n</b> appears with a text box and the note that the name is also shown on hardware displays. "
          "Press <b>OK</b> to keep it. Right-clicking a chip gives <b>Rename macro...</b> and <b>Reset name</b>."),
        H2("12.3  Hardware and host displays"),
        P("The macro parameters (Macro 1 to 16) come first in the plug-in's parameter list, in two groups of eight: <b>Macros 1-8</b> and <b>Macros 9-16</b>. "
          "That means a controller that shows parameters eight at a time (an eight-knob page layout, a host's generic controller mapping, or an automation list) "
          "shows the macros first. When a name changes, Massive PSXL tells the host that the parameter information has changed; hosts that react to that notification refresh "
          "the labels straight away. How quickly or whether a particular host or controller updates its display depends on that host."),
        callout("tip", "Design a patch so its eight most useful controls are Macros 1 to 8 and give each a sensible name. They will then also be the first page on a hardware controller. "
                       "Most factory synth presets map Macro 1 to Filter 1 Cutoff, Macro 2 to Filter 1 Reso, Macro 3 to Osc 1 Position and Macro 4 to Reverb Mix."),
        H2("12.4  Macros and MIDI"),
        P("Right-click a macro knob and choose <b>MIDI Learn</b>, then move a hardware knob or fader: the CC is now tied to that macro (chapter 15)."),
    ]
    return st


def ch13():
    st = [Banner(13, "Voice, Glide and Tuning", "Polyphony, mono modes, portamento and microtuning")]
    st += [
        P("Voice settings are in the <b>PITCH</b> panel (Pitch, Glide, Voice Mode, Expo) and in the <b>Voice</b> lower tab (Voice Mode, Polyphony, Glide, Bend Range, Vel Sens, Expo, wavetable library and tuning)."),
        tbl([["Control", "Range / choices", "Default", "Notes"],
             ["Voice Mode", "Poly, Mono, Legato", "Poly", ""],
             ["Polyphony", "1 to 16", "8", "Maximum simultaneous notes in Poly mode."],
             ["Glide", "0 to 5 s", "0 (off)", "Time to slide from the previous note to the new one."],
             ["Expo", "on / off", "off", "Exponential glide curve (fast at first, slowing down)."],
             ["Bend Range", "0 to 24 st", "2", "How far the pitch wheel bends."],
             ["Vel Sens", "0 to 1", "0.5", "How much key velocity affects loudness."],
             ["Pitch", "-48 to +48 st", "0", "Global transpose, continuous."]],
            [1, 1.5, 0.8, 2.3], first_bold=True),
        H2("13.1  Voice modes"),
    ]
    st += bullets([
        "<b>Poly</b>: up to Polyphony notes at once. When all voices are in use, the oldest note that has been released is stolen first, then the oldest sounding note.",
        "<b>Mono</b>: a single voice. Every new note re-triggers the envelopes. Releasing a key while others are held jumps back to the last held note.",
        "<b>Legato</b>: like Mono, but a note played while another is held <b>changes pitch without retriggering</b> the envelopes and Performers. Detached notes retrigger normally. Together with Glide this gives slides (acid lines, expressive leads).",
        "Switching from Poly to Mono or Legato releases the extra voices.",
    ])
    st += [
        H2("13.2  Glide"),
        P("With <b>Glide</b> above 0, a new note starts from the pitch of the previous note and slides to the new pitch. In the default (linear) curve the slide always takes the Glide time "
          "whatever the interval. With <b>Expo</b> on the slide is exponential: it starts fast and settles in about the Glide time. Glide also works in Poly mode (each new note slides from the last played note)."),
        H2("13.3  Pitch, bend and sustain"),
        P("<b>Pitch wheel</b> moves pitch by up to <b>Bend Range</b> semitones (set it to 0 to ignore the wheel for pitch while still using Pitch Bend as a modulation source). "
          "The <b>sustain pedal</b> (CC 64) holds released notes until the pedal comes up. <b>All Notes Off</b> releases every voice; <b>All Sound Off</b> silences them at once."),
        H2("13.4  Microtuning with Scala files"),
        P("Massive PSXL can play any scale defined in a standard Scala <b>.scl</b> file."),
    ]
    st += numbered([
        "Open the <b>Voice</b> tab and press <b>Load Scala (.scl)...</b> (or use <b>Menu > Settings > Load Scala tuning (.scl)...</b>).",
        "Choose a .scl file. The toast says 'Tuning loaded: name' and the Voice tab shows <b>MICROTUNING: name</b>.",
        "The scale repeats every period (usually the octave). Degree 0 of the scale sits on MIDI note 60 (middle C, 261.6256 Hz).",
        "<b>12-TET</b> (Voice tab) or <b>Menu > Settings > Reset tuning to 12-TET</b> restores equal temperament. A file that is not a valid scale shows 'Not a valid .scl file'.",
    ])
    st.append(callout("note", "The tuning is saved with your DAW project (the plug-in's state) and is not changed by loading presets. "
                              "Only .scl scale files are supported (not .kbm keyboard maps). Ratios, cents and the usual Scala formats are accepted."))
    return st


def ch14():
    st = [Banner(14, "Presets and the Browser", "117 factory sounds, your own library")]
    st += [
        P("Click <b>Browse</b> (top bar) or the preset name to open the browser over the synth panels. Press <b>Edit</b> (or <b>Close</b>) to return."),
        H2("14.1  Browsing"),
        tbl([["Part", "What it does"],
             ["Category list (left)", "All, Bass, Leads, Pads, Plucks, Keys, Drums, FX, Sequence, User."],
             ["Search box", "Type part of a preset name, category or author to filter the current list."],
             ["Preset list", "Name, category and author. A <b>single click loads</b> the preset (the current one is highlighted). A <b>double-click</b> or Return loads it and closes the browser."],
             ["Save preset...", "Names and saves your sound (14.3)."],
             ["Open user folder", "Opens your presets folder in Finder."],
             ["Close", "Returns to the synth."],
             ["Header", "'PRESET BROWSER - 117 factory presets'."]],
            [1.4, 4.2], first_bold=True),
        P("The <b>&lt;</b> and <b>&gt;</b> arrows in the top bar step through the whole library in browser order (category, then name; your presets follow the factory ones) without opening the browser."),
        H2("14.2  The factory library"),
        P("All 117 presets were written for Massive PSXL. Each loads with its own routing, modulation and macro names. See Appendix A for the complete list."),
        tbl([["Category", "Presets", "Flavour"],
             ["Bass", "20", "Subs, wobbles, reese, acid, FM, formant and distorted basses."],
             ["Leads", "19", "Saw, supersaw, PWM, sync, FM, glass, vowel, brass and expressive mono leads."],
             ["Pads", "20", "Strings, glass, choirs, evolving and ambient pads."],
             ["Plucks", "15", "Plucks, bells, marimba, kalimba, koto, steel drum and stabs."],
             ["Keys", "10", "E-pianos, organs, clav, digital piano."],
             ["Drums", "15", "Kicks, snares, hats, clap, shaker, rim, toms, cowbell. Play around C0 to C3. Their amp envelopes are OneShot, so a tap plays the whole hit."],
             ["FX", "10", "Risers, falls, zaps, textures, drones and hits."],
             ["Sequence", "8", "Arpeggios and gates built with Performers. Hold a note or chord."]],
            [0.9, 0.7, 4], first_bold=True),
        H2("14.3  Saving your own presets"),
    ]
    st += numbered([
        "Choose <b>Menu > Save preset...</b> (it opens the Browse tab) or open the browser yourself.",
        "Press <b>Save preset...</b>. A dialog asks for a <b>name</b> (a fresh Init patch suggests 'My Preset') and a <b>category</b> (Bass, Leads, Pads, Plucks, Keys, Drums, FX, Sequence or User).",
        "Press <b>Save</b>. The toast says <i>Saved preset \"name\"</i>.",
        "The file is stored in <b>~/Music/Phil S Audio/Massive PSXL/Presets</b>. A preset saved in a category goes in a sub-folder with that name; <b>User</b> saves in the main folder. Files end in <b>.psxlpreset</b>.",
    ])
    st += bullets([
        "A user preset stores every parameter, the routing, all modulation assignments with their amounts, macro names, the three Performer patterns and any imported wavetables.",
        "Your presets appear under <b>User</b> (and in search). Copy a .psxlpreset file to another Mac to share it. The browser rescans your folder every time it opens.",
        "Saving with an existing name overwrites that file.",
        "<b>Undo</b> history is cleared whenever a preset loads.",
    ])
    st += [
        H2("14.4  Init and Mutate"),
        P("<b>Menu > Load Init (Blank)</b> gives a completely blank slate: defaults for everything, <b>no routing</b>, no modulation, macros named 'Macro 1' to 'Macro 16', Performer bars at 0.5. "
          "<b>Menu > Mutate sound (subtle / wild)</b> randomly nudges the continuous voice parameters. Use it to explore around a sound; <b>Undo</b> reverts it."),
        H2("14.5  Presets, programs and your DAW"),
        P("The plug-in presents its 117 factory presets to the host as <b>programs</b>, so hosts with a program or preset menu can select them. "
          "Your own presets are loaded from the Massive PSXL browser. The full sound (including routing, modulation, macro names, Performer bars, "
          "user wavetables, tuning and MIDI-learn mappings) is saved inside your DAW project, so a session reopens exactly as you left it."),
    ]
    return st


def ch15():
    st = [Banner(15, "MIDI, Keyboard and MIDI Learn", "Playing, controllers and mapping")]
    st += [
        H2("15.1  MIDI messages understood"),
        tbl([["Message", "Effect"],
             ["Note on / off", "Plays notes. Velocity controls loudness (Vel Sens) and is available as a modulation source. All MIDI channels are accepted."],
             ["Pitch bend", "Bends pitch by Bend Range; also the Pitch Bend modulation source."],
             ["CC 1 (mod wheel)", "The Mod Wheel modulation source."],
             ["CC 64 (sustain)", "Sustain pedal (value 64 or more = down)."],
             ["Channel pressure", "The Aftertouch modulation source."],
             ["All Notes Off / All Sound Off", "Releases or silences all voices."],
             ["Other CCs", "Can be mapped to any parameter with MIDI Learn."]],
            [1.3, 4.3], first_bold=True),
        H2("15.2  The on-screen keyboard"),
        P("Press <b>Keys</b> in the top bar. The window grows 150 units taller and a keyboard slides in under the macro strip. Press <b>Keys</b> again to hide it. "
          "The setting is remembered."),
    ]
    st += bullets([
        "<b>Pitch wheel</b> (left): drag up or down; it springs back to the centre when released.",
        "<b>Mod wheel</b> (next to it): stays where you leave it. Both wheels also follow incoming MIDI from your hardware.",
        "The small <b>&lt;</b> and <b>&gt;</b> buttons shift the keyboard down or up by one octave; the label below them shows the lowest octave (C0 at the start; middle C is C3).",
        "<b>Menu > Settings > Keyboard size</b> sets 2 to 8 octaves (default 5).",
        "The height at which you click a key sets the velocity (lower on the key = harder).",
        "<b>Keys light up when MIDI arrives</b> from a hardware keyboard or the DAW, so you can see what the plug-in receives.",
        "With the keyboard focused the computer's typing keys also play notes using the standard on-screen-keyboard mapping (A, W, S, E, D, F, T, G, Y, H, U, J, K...).",
    ])
    st += [
        H2("15.3  MIDI Learn"),
        P("Any <b>knob</b> (including the macro knobs) can be tied to a MIDI controller. Switches and menus are not learnable."),
    ]
    st += numbered([
        "<b>Right-click the control</b> and choose <b>MIDI Learn</b>. The control gets an amber ring and the menu entry reads 'Waiting for MIDI CC... (click to cancel)'.",
        "Move a knob, fader or button on your controller. The first CC received becomes the mapping.",
        "The control now follows that CC (value 0 to 127 spans the control's range). Right-click it to see <b>Clear MIDI mapping (CC n)</b>.",
    ])
    st += bullets([
        "CC 1 (mod wheel), CC 64 (sustain) and the channel-mode messages (CC 120 and above) are ignored for learning because they already have jobs.",
        "A CC can control one parameter; learning it again on another control moves the mapping.",
        "Mappings are saved with your DAW project (plug-in state), not inside presets.",
        "MIDI-learned controls do not include modulation amounts: use a macro for that.",
    ])
    return st


def ch16():
    st = [Banner(16, "Themes, Scaling and Settings", "Make it fit your screen and your eyes")]
    st += [
        H2("16.1  Light and dark themes"),
        P("The default is the <b>dark indigo</b> theme with cyan, magenta and amber accents. Use the <b>Light / Dark</b> button in the top bar (it is labelled with the theme it will switch to) or "
          "<b>Menu > Settings > Dark theme / Light theme</b>. The choice is remembered."),
        tbl([["Colour", "Meaning on screen"],
             ["Cyan", "Oscillators, the modulation chips for Mod slots, knob values."],
             ["Magenta", "Filters, macros, selection and drag highlights."],
             ["Amber", "Performers, the Insert, active input ports and the learn ring."],
             ["Green", "Noise, performance source chips and healthy meter level."]],
            [1, 4.6], first_bold=True),
        H2("16.2  Interface size"),
        P("Choose <b>Menu > Settings > Interface size</b> and pick 75, 100, 125, 150, 175 or 200 percent, or <b>drag the corner of the window</b>: the shape stays fixed and the size runs from 75 to 200 percent. "
          "Opening the keyboard makes the window taller but keeps the same scale. The size is remembered."),
        callout("tip", "A larger interface also makes it easier to draw Performer bars and to hit small knobs."),
        H2("16.3  Where settings are stored"),
        P("Theme, size, keyboard visibility and keyboard octaves are stored in <b>~/Library/Application Support/Phil S Audio/Massive PSXL.settings</b>. "
          "Everything about the sound itself is stored in presets and in the DAW project."),
        H2("16.4  Undo and Redo"),
        P("The Undo and Redo buttons (and the Menu entries) cover knob edits, routing changes, modulation assignments and removals, and macro renames. "
          "Loading a preset or Init clears the history."),
        H2("16.5  Tooltips and messages"),
        P("The oscillator <b>+</b> button has a tooltip. Most feedback is given as a short on-screen message (toast) below the top bar: assignments, imports, saves and refusals."),
    ]
    return st


def build():
    return [ch11(), ch12(), ch13(), ch14(), ch15(), ch16()]
