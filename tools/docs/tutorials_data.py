"""Tutorial recipes for the Massive PSXL manual (and referenced by the video scripts).

Node indices for wires: 0 Osc 1, 1 Osc 2, 2 Noise, 3 Filter 1, 4 Filter 2, 5 Insert, 6 Out.
Every value is a "starting point" - tune by ear. Parameter names are the on-screen labels.
"""

O1, O2, NZ, F1, F2, INS, OUT = range(7)

QS101 = "right-click an empty spot in the Routing tab > <b>Osc 1 > Filter 1 > Out</b>"
QS102 = "right-click an empty spot in the Routing tab > <b>Osc 1 + Osc 2 > Filter 1 > Out</b>"
QS106 = "right-click an empty spot in the Routing tab > <b>Noise > Filter 1 > Insert > Out (drums / FX)</b>"

TUTORIALS = []


def T(**kw):
    kw.setdefault("mods", [])
    kw.setdefault("tips", [])
    kw.setdefault("group", "")
    kw["n"] = len(TUTORIALS) + 1
    TUTORIALS.append(kw)


# ============================================================================================ DRUMS
T(title="Kick drum", group="Drums", preset="Kick Tight, Kick Punch (punchier), Kick Deep 808 (long and low)",
  goal="A punchy sine kick: a sine tone whose pitch falls quickly, plus a touch of noise for the click.",
  wires=[(O1, F1), (F1, INS), (NZ, INS), (INS, OUT)],
  routing="Osc 1 > Filter 1 > Insert > Out, and Noise > Insert (the click skips the filter). Draw the wires by hand: drag from the right-edge port of each node to the left-edge port of the next.",
  steps=[
      "<b>Menu > Load Init (Blank)</b>. Open the <b>Routing</b> tab and draw the four wires listed above.",
      "Select <b>Osc 1</b>. Set the wavetable to <b>Morph Basic</b> and <b>Pos</b> to 0 (pure sine). Set <b>Level</b> 0.95.",
      "Open the <b>Amp Env</b> tab: Attack 0.001, Decay 0.28, Sustain 0, Release 0.08 and switch <b>OneShot</b> on, so the drum rings out even on a short tap.",
      "Open the <b>Mod 2</b> tab (Type: Envelope): Attack 0.0005, Decay 0.11, Sustain 0, Release 0.05, OneShot on. Drag the <b>Mod 2</b> chip onto the Osc 1 <b>Pitch</b> knob, then right-click the knob > <b>Edit amount</b> and set +0.28.",
      "Set the Noise, Filter 1 and Insert values from the table. Play low notes (C0 to C1 on the keyboard).",
  ],
  settings=[
      ("Osc 1", "Wavetable / Pos", "Morph Basic / 0"), ("Osc 1", "Pitch / Level", "0 / 0.95"),
      ("Noise", "Level / Color / Type", "0.10 / 0.85 / White"),
      ("Filter 1", "Model / Mode / Cutoff / Reso", "Ladder / LP 24 / 9000 Hz / 0.05"),
      ("Insert", "Type / Drive / Mix", "TanH / 0.25 / 1.0"),
      ("Amp Env", "Attack / Decay / Sustain / Release", "0.001 / 0.28 / 0 / 0.08 (OneShot on)"),
      ("Mod 2 (Envelope)", "Attack / Decay / Sustain / Release", "0.0005 / 0.11 / 0 / 0.05 (OneShot on)"),
  ],
  mods=[("Mod 2", "Osc 1 Pitch", "+0.28", "About 27 semitones of downward sweep in the first 100 ms: the 'thump'.")],
  tips=["For a long 808-style kick set Osc 1 <b>Pitch</b> to -12, Amp Env Decay to 0.9 and Insert Drive to 0.15 (that is the factory <i>Kick Deep 808</i>).",
        "More click: raise Noise Level to 0.2 or add Filter 1 Cutoff modulation. Less click: lower Noise Level to 0.",
        "The pitch sweep depth sets the character: 0.2 is soft and round, 0.33 is hard and snappy.",
        ])

T(title="Snare drum", group="Drums", preset="Snare Crack, Snare Tight",
  goal="A band-passed noise burst with a short sine body underneath.",
  wires=[(O1, F1), (NZ, F1), (F1, INS), (INS, OUT)],
  routing="Noise and Osc 1 > Filter 1 > Insert > Out (quick setup 'Noise > Filter 1 > Insert > Out', then add Osc 1 > Filter 1).",
  steps=[
      "<b>Menu > Load Init (Blank)</b>. Routing tab: " + QS106 + ". Then drag a wire from <b>Osc 1</b> to <b>Filter 1</b>.",
      "Noise panel: Level 0.9, Type White, Color 0.55. Osc 1: <b>Morph Basic</b>, Pos 0, Pitch +12, Level 0.5.",
      "Filter 1: choose Model <b>State Variable</b>, Mode <b>BP</b>, Cutoff 2400, Reso 0.35.",
      "Insert: Type <b>Fold</b>, Drive 0.2, Mix 1.0.",
      "Amp Env: Attack 0.0008, Decay 0.22, Sustain 0, Release 0.05, OneShot on.",
  ],
  settings=[
      ("Noise", "Level / Color / Type", "0.9 / 0.55 / White"), ("Osc 1", "Wavetable / Pos / Pitch / Level", "Morph Basic / 0 / +12 / 0.5"),
      ("Filter 1", "Model / Mode / Cutoff / Reso", "State Variable / BP / 2400 Hz / 0.35"),
      ("Insert", "Type / Drive / Mix", "Fold / 0.2 / 1.0"),
      ("Amp Env", "Attack / Decay / Sustain / Release", "0.0008 / 0.22 / 0 / 0.05 (OneShot on)"),
  ],
  tips=["Shorter and tighter (<i>Snare Tight</i>): Decay 0.14, Cutoff 3200, Osc 1 Pitch +16, Osc 1 Level 0.4.",
        "A little reverb (Verb tab, Mix 0.15) makes it sit in a room; a delay on a snare is rarely wanted.",
        "A Rim Shot is the same recipe with Decay 0.05, Cutoff 1800, Reso 0.55, Osc 1 Pitch +24, Level 0.6 (factory <i>Rim Shot</i>)."])

T(title="Closed and open hi-hats", group="Drums", preset="Hat Closed, Hat Open, Shaker",
  goal="High-passed noise with a very short (closed) or longer (open) envelope.",
  wires=[(NZ, F1), (F1, INS), (INS, OUT)],
  routing="Noise > Filter 1 > Insert > Out.",
  steps=[
      "<b>Menu > Load Init (Blank)</b>. Routing tab: " + QS106 + ".",
      "Noise: Level 0.9, Type White, Color 0.9 (the Color knob above 0.5 is a high-pass).",
      "Filter 1: <b>State Variable</b> / <b>HP</b>, Cutoff 9000, Reso 0.15.",
      "Insert: leave Mix at 0 for a clean hat (or Type Fold, Drive 0.3, Mix 0.3 for a metallic edge).",
      "<b>Closed hat</b>: Amp Env Attack 0.0008, Decay 0.045, Sustain 0, Release 0.05, OneShot on. <b>Open hat</b>: Decay 0.35, Release 0.2 (save this variation as a second preset).",
  ],
  settings=[
      ("Noise", "Level / Color / Type", "0.9 / 0.9 / White"),
      ("Filter 1", "Model / Mode / Cutoff / Reso", "State Variable / HP / 9000 Hz / 0.15 (open hat: 8000 Hz)"),
      ("Insert", "Mix", "0 (transparent)"),
      ("Amp Env (closed)", "Attack / Decay / Sustain / Release", "0.0008 / 0.045 / 0 / 0.05, OneShot on"),
      ("Amp Env (open)", "Attack / Decay / Sustain / Release", "0.0008 / 0.35 / 0 / 0.2, OneShot on"),
  ],
  tips=["There is no hat choke group: an open hat rings for its full Decay even if you then play a closed hat. Keep Decay and Release short enough for your tempo, or set Voice Mode to Mono on the open-hat patch so repeated hits cut the previous one.",
        "Shaker: Decay 0.09, Hold 0.02, Cutoff 7000, Reso 0.3, Color 0.8 (factory <i>Shaker</i>).",
        "Metallic hat: set Noise Type to <b>Crackle</b> or Filter 1 Model to <b>Comb</b> with Cutoff 700 and Reso 0.8."])

T(title="Hand clap", group="Drums", preset="Clap Room",
  goal="A noise burst whose level is flickered by a Performer so it sounds like several hands.",
  wires=[(NZ, F1), (F1, INS), (INS, OUT)],
  routing="Noise > Filter 1 > Insert > Out.",
  steps=[
      "<b>Menu > Load Init (Blank)</b>. Routing: " + QS106 + ".",
      "Noise: Level 0.9, Color 0.6, Type White. Filter 1: <b>State Variable</b> / <b>BP</b>, Cutoff 1500, Reso 0.45. Insert Mix 0.",
      "Amp panel: set <b>Level</b> to 0 (the performer will supply the level). Amp Env: Attack 0.0008, Decay 0.16, Sustain 0, Release 0.05, OneShot on.",
      "Open <b>Perf 1</b>: Steps 6, Sync off, Rate 28 Hz, Smooth 0.3. Draw the bars roughly: 1.0, 0.05, 0.85, 0.05, 0.7, 0.35 (full height, nearly empty, 85 percent, nearly empty, 70 percent, a third).",
      "Drag the <b>Perf 1</b> chip onto the Amp <b>Level</b> knob and set the amount to +0.80. Play a note: the clap now stutters 3 times then tails off.",
  ],
  settings=[
      ("Noise", "Level / Color / Type", "0.9 / 0.6 / White"),
      ("Filter 1", "Model / Mode / Cutoff / Reso", "State Variable / BP / 1500 Hz / 0.45"),
      ("Amp", "Level", "0 (performer takes over)"),
      ("Amp Env", "Attack / Decay / Sustain / Release", "0.0008 / 0.16 / 0 / 0.05, OneShot on"),
      ("Perf 1", "Steps / Sync / Rate / Smooth", "6 / off / 28 Hz / 0.3"),
  ],
  mods=[("Perf 1", "Amp Level", "+0.80", "Each step sets the loudness of one hand-clap flam.")],
  tips=["The factory <i>Clap Room</i> uses the synced alternative: Sync on, Division 1/32, 8 steps. Sync off with a Rate near 30 Hz gives tighter flams.",
        "Add Reverb Mix 0.2 for a roomy clap. Add a second Performer on Filter 1 Cutoff for variation between hands."])

T(title="Tom", group="Drums", preset="Tom Low, Tom High",
  goal="Like the kick but higher, with a gentler sweep and a longer tone.",
  wires=[(O1, F1), (F1, OUT)],
  routing="Osc 1 > Filter 1 > Out (quick setup 'Osc 1 > Filter 1 > Out').",
  steps=[
      "<b>Menu > Load Init (Blank)</b>. Routing: " + QS101 + ".",
      "Osc 1: <b>Morph Basic</b>, Pos 0, Pitch +5, Level 0.95. Filter 1: Cutoff 9000, Reso 0.05.",
      "Amp Env: Attack 0.001, Decay 0.5, Sustain 0, Release 0.08, OneShot on.",
      "Mod 2 (Envelope): Attack 0.0005, Decay 0.145, Sustain 0, Release 0.05, OneShot on. Drag the Mod 2 chip onto Osc 1 <b>Pitch</b>, amount +0.12.",
  ],
  settings=[
      ("Osc 1", "Wavetable / Pos / Pitch / Level", "Morph Basic / 0 / +5 / 0.95"),
      ("Filter 1", "Cutoff / Reso", "9000 Hz / 0.05"),
      ("Amp Env", "Attack / Decay / Sustain / Release", "0.001 / 0.5 / 0 / 0.08, OneShot on"),
      ("Mod 2 (Envelope)", "Attack / Decay / Sustain / Release", "0.0005 / 0.145 / 0 / 0.05, OneShot on"),
  ],
  mods=[("Mod 2", "Osc 1 Pitch", "+0.12", "About 11 semitones of sweep.")],
  tips=["High tom (<i>Tom High</i>): Osc 1 Pitch +17, Decay 0.35. Play a fill across several keys for a tuned set.",
        "Add Noise Level 0.05 (Color 0.8) routed to Filter 1 for a stick attack."])

# ============================================================================================ BASS
T(title="Sub bass", group="Bass", preset="Sub Pillar, Deep Weight",
  goal="A clean low sine with a second sine an octave below.",
  wires=[(O1, F1), (O2, F1), (F1, OUT)],
  routing="Osc 1 + Osc 2 > Filter 1 > Out.",
  steps=[
      "<b>Menu > Load Init (Blank)</b>. Routing: " + QS102 + ".",
      "Osc 1: <b>Morph Basic</b>, Pos 0. Osc 2: change the wavetable to <b>Morph Basic</b> (it defaults to Pulse Sweep), Pos 0, Pitch -12, Level 0.5.",
      "Filter 1: Ladder / LP 24, Cutoff 380, Reso 0.1.",
      "Amp Env: Attack 0.004, Decay 0.3, Sustain 0.95, Release 0.18.",
  ],
  settings=[
      ("Osc 1", "Wavetable / Pos / Level", "Morph Basic / 0 / 0.8"),
      ("Osc 2", "Wavetable / Pos / Pitch / Level", "Morph Basic / 0 / -12 / 0.5"),
      ("Filter 1", "Model / Mode / Cutoff / Reso", "Ladder / LP 24 / 380 Hz / 0.1"),
      ("Amp Env", "Attack / Decay / Sustain / Release", "0.004 / 0.3 / 0.95 / 0.18"),
  ],
  tips=["<i>Deep Weight</i> adds harmonics so small speakers can hear it: Osc 1 Pos 0.12, Osc 2 Level 0.7, Cutoff 300, plus Insert (TanH, Drive 0.35, Mix 0.6) after Filter 1.",
        "Set Voice Mode to <b>Mono</b> (Pitch panel) with Glide 0.05 for sliding 808 style lines.",
        "Check the bass on small speakers: sines below 60 Hz are inaudible on laptops without harmonic content."])

T(title="Wobble bass", group="Bass", preset="Wobble Machine, Dub Wobble",
  goal="A saw bass whose filter is swept by a tempo-synced LFO.",
  wires=[(O1, F1), (F1, OUT)],
  routing="Osc 1 > Filter 1 > Out.",
  steps=[
      "<b>Menu > Load Init (Blank)</b>. Routing: " + QS101 + ".",
      "Osc 1: <b>Morph Basic</b>, Pos 0.66 (saw), Unison 3, Detune 10.",
      "Filter 1: Ladder / LP 24, Cutoff 520, Reso 0.5, Drive 0.2. Amp Env: Attack 0.003, Decay 0.3, Sustain 0.9, Release 0.15.",
      "Open <b>Mod 2</b>, set Type to <b>LFO</b>, Shape <b>Sine</b>, switch <b>Sync</b> on and choose Division <b>1/8</b>.",
      "Drag the Mod 2 chip onto Filter 1 <b>Cutoff</b> and set the amount to +0.34. Play low notes.",
  ],
  settings=[
      ("Osc 1", "Wavetable / Pos / Unison / Detune", "Morph Basic / 0.66 / 3 / 10 ct"),
      ("Filter 1", "Model / Mode / Cutoff / Reso / Drive", "Ladder / LP 24 / 520 Hz / 0.5 / 0.2"),
      ("Amp Env", "Attack / Decay / Sustain / Release", "0.003 / 0.3 / 0.9 / 0.15"),
      ("Mod 2 (LFO)", "Shape / Sync / Division / Bipolar", "Sine / on / 1/8 / on"),
  ],
  mods=[("Mod 2 (LFO)", "Filter 1 Cutoff", "+0.34", "The cutoff swings both ways around the knob position, in time with the host tempo.")],
  tips=["Dub version (<i>Dub Wobble</i>): Shape Triangle, Division 1/4, Reso 0.55, Cutoff 450, and Delay Mix 0.25 (Sync on, Division 1/8).",
        "Faster or slower wobble: change the Division (1/16 is aggressive, 1/2 is slow). With Sync off use Rate in Hz.",
        "If the wobble sounds too thin lower the base Cutoff; to hear more of the bottom raise the amount instead.",
        "In a DAW the synced LFO follows the project tempo. When no host tempo is available (for example in the standalone app) tempo-synced features assume 120 BPM."])

T(title="Acid bass", group="Bass", preset="Acid Line, Mono Acid Lead",
  goal="Resonant ladder filter with a fast envelope and legato slides.",
  wires=[(O1, F1), (F1, OUT)],
  routing="Osc 1 > Filter 1 > Out.",
  steps=[
      "<b>Menu > Load Init (Blank)</b>. Routing: " + QS101 + ".",
      "Osc 1: <b>Morph Basic</b>, Pos 0.66 (saw). Pitch panel: Voice Mode <b>Legato</b>, Glide 0.07.",
      "Filter 1: Ladder / LP 24, Cutoff 560, Reso 0.72, Drive 0.35. Amp Env: Attack 0.002, Decay 0.25, Sustain 0.85, Release 0.1.",
      "Mod 2 (Envelope): Attack 0.002, Decay 0.2, Sustain 0, Release 0.15. Drag its chip onto Filter 1 <b>Cutoff</b>, amount +0.34.",
      "Play a pattern with overlapping notes: legato notes slide and do not retrigger the envelopes; detached notes re-pluck the filter.",
  ],
  settings=[
      ("Osc 1", "Wavetable / Pos", "Morph Basic / 0.66"),
      ("Pitch panel", "Voice Mode / Glide", "Legato / 0.07 s"),
      ("Filter 1", "Model / Mode / Cutoff / Reso / Drive", "Ladder / LP 24 / 560 Hz / 0.72 / 0.35"),
      ("Amp Env", "Attack / Decay / Sustain / Release", "0.002 / 0.25 / 0.85 / 0.1"),
      ("Mod 2 (Envelope)", "Attack / Decay / Sustain / Release", "0.002 / 0.2 / 0 / 0.15"),
  ],
  mods=[("Mod 2", "Filter 1 Cutoff", "+0.34", "Each retriggered note snaps the filter open then closes it.")],
  tips=["Accents: drag the <b>Velocity</b> chip (left of the macro strip) onto Filter 1 Cutoff at +0.2 and play some notes harder.",
        "Higher Reso gives the squelch; above 0.9 the ladder starts to self-oscillate.",
        "Add Delay (Sync on, Division 1/8, Mix 0.2) and Dist Mix 0.2 for the classic dirty acid sound."])

T(title="Reese bass", group="Bass", preset="Reese Beast",
  goal="Two heavily detuned saw stacks beating against each other, with slow filter movement.",
  wires=[(O1, F1), (O2, F1), (F1, OUT)],
  routing="Osc 1 + Osc 2 > Filter 1 > Out.",
  steps=[
      "<b>Menu > Load Init (Blank)</b>. Routing: " + QS102 + ".",
      "Osc 1: <b>Morph Basic</b>, Pos 0.66, Unison 4, Detune 24. Osc 2: <b>Morph Basic</b>, Pos 0.66, Fine +9, Unison 4, Detune 20.",
      "Filter 1: Ladder / LP 24, Cutoff 1000, Reso 0.2. Amp Env: Attack 0.01, Decay 0.4, Sustain 0.9, Release 0.3.",
      "Mod 2: Type <b>LFO</b>, Shape <b>Triangle</b>, Rate 0.3 Hz (Sync off). Drag its chip onto Filter 1 Cutoff, amount +0.12.",
      "Chorus tab: Mix 0.25 to widen. Play low, long notes.",
  ],
  settings=[
      ("Osc 1", "Wavetable / Pos / Unison / Detune", "Morph Basic / 0.66 / 4 / 24 ct"),
      ("Osc 2", "Wavetable / Pos / Fine / Unison / Detune", "Morph Basic / 0.66 / +9 ct / 4 / 20 ct"),
      ("Filter 1", "Model / Mode / Cutoff / Reso", "Ladder / LP 24 / 1000 Hz / 0.2"),
      ("Amp Env", "Attack / Decay / Sustain / Release", "0.01 / 0.4 / 0.9 / 0.3"),
      ("Mod 2 (LFO)", "Shape / Rate", "Triangle / 0.3 Hz"),
      ("FX: Chorus", "Mix", "0.25"),
  ],
  mods=[("Mod 2 (LFO)", "Filter 1 Cutoff", "+0.12", "Slow breathing of the brightness.")],
  tips=["The movement comes from the beating between the two detuned stacks; change Osc 2 Fine to alter the beat speed.",
        "Add Insert (Fold or TanH, Mix 0.4) after Filter 1 for the growl (connect Filter 1 > Insert > Out)."])

# ============================================================================================ LEADS
T(title="Supersaw lead", group="Leads", preset="Super Stack, Detuned Trance",
  goal="A big, wide stack of eight detuned saws.",
  wires=[(O1, F1), (F1, OUT)],
  routing="Osc 1 > Filter 1 > Out.",
  steps=[
      "<b>Menu > Load Init (Blank)</b>. Routing: " + QS101 + ".",
      "Osc 1: <b>Morph Basic</b>, Pos 0.66, <b>Unison</b> 8, <b>Detune</b> 34.",
      "Filter 1: Ladder / LP 24, Cutoff 7000, Reso 0.15. Amp Env: Attack 0.006, Decay 0.3, Sustain 0.85, Release 0.35.",
      "FX: Chorus Mix 0.25; Reverb Size 0.6, Mix 0.2.",
  ],
  settings=[
      ("Osc 1", "Wavetable / Pos / Unison / Detune", "Morph Basic / 0.66 / 8 / 34 ct"),
      ("Filter 1", "Model / Mode / Cutoff / Reso", "Ladder / LP 24 / 7000 Hz / 0.15"),
      ("Amp Env", "Attack / Decay / Sustain / Release", "0.006 / 0.3 / 0.85 / 0.35"),
      ("FX", "Chorus Mix / Reverb Size / Reverb Mix", "0.25 / 0.6 / 0.2"),
  ],
  tips=["Trance version (<i>Detuned Trance</i>): Osc 1 Unison 7, Detune 28; add Osc 2 (Morph Basic, Pos 0.66) at Pitch +12, Unison 3, Detune 14, Level 0.35; Delay Sync on 1/8, Mix 0.3.",
        "Each unison voice has a random starting phase, so no two notes sound exactly alike.",
        "Playing chords with 8 unison voices uses 8 oscillators per note: lower Polyphony if your computer struggles."])

T(title="Mono lead (expressive)", group="Leads", preset="Classic Saw Lead, Expressive Lead",
  goal="A single-voice lead with portamento, plus mod wheel and aftertouch expression.",
  wires=[(O1, F1), (F1, OUT)],
  routing="Osc 1 > Filter 1 > Out.",
  steps=[
      "<b>Menu > Load Init (Blank)</b>. Routing: " + QS101 + ".",
      "Osc 1: <b>Morph Basic</b>, Pos 0.66, Unison 3, Detune 14. Pitch panel: Voice Mode <b>Mono</b>, Glide 0.03.",
      "Filter 1: Ladder / LP 24, Cutoff 5000, Reso 0.18. Amp Env: Attack 0.004, Decay 0.3, Sustain 0.85, Release 0.3.",
      "FX: Delay Sync on, Division 1/8, Feedback 0.35, Mix 0.2; Reverb Mix 0.15.",
      "Expression: drag the <b>ModWhl</b> chip (macro strip, left) onto Osc 1 <b>Pos</b> (+0.4) and onto Filter 1 <b>Cutoff</b> (+0.25); drag <b>AftTch</b> onto Cutoff (+0.15).",
      "Vibrato: Mod 3 Type LFO, Shape Sine, Rate 5.2 Hz, Fade In 0.6. Drag its chip onto the Pitch panel <b>Pitch</b> knob with amount +0.003 (about a third of a semitone).",
  ],
  settings=[
      ("Osc 1", "Wavetable / Pos / Unison / Detune", "Morph Basic / 0.66 / 3 / 14 ct"),
      ("Pitch panel", "Voice Mode / Glide", "Mono / 0.03 s"),
      ("Filter 1", "Model / Mode / Cutoff / Reso", "Ladder / LP 24 / 5000 Hz / 0.18 (Expressive: 2500 Hz / 0.25)"),
      ("Amp Env", "Attack / Decay / Sustain / Release", "0.004 / 0.3 / 0.85 / 0.3"),
      ("Mod 3 (LFO)", "Shape / Rate / Fade In", "Sine / 5.2 Hz / 0.6 s"),
      ("FX", "Delay (Sync, 1/8, Fb 0.35) / Reverb", "Mix 0.2 / Mix 0.15"),
  ],
  mods=[("Mod Wheel", "Osc 1 Position", "+0.40", "Wheel morphs the timbre."),
        ("Mod Wheel", "Filter 1 Cutoff", "+0.25", "Wheel opens the filter."),
        ("Aftertouch", "Filter 1 Cutoff", "+0.15", "Pressing harder brightens."),
        ("Mod 3 (LFO)", "Pitch", "+0.003", "Delayed vibrato (the Fade In ramps it up).")],
  tips=["Mono mode retriggers every note; choose <b>Legato</b> to slide between overlapping notes without re-striking the envelopes.",
        "The on-screen keyboard has mod and pitch wheels. Aftertouch needs hardware that sends channel pressure.",
        "Pitch bend range is set in the Voice tab (Bend Range, default 2 semitones)."])

# ============================================================================================ PLUCKS AND KEYS
T(title="Pluck", group="Plucks and Keys", preset="Classic Pluck, Soft Pluck, Detuned Pluck",
  goal="A short saw note whose filter snaps shut: the basis of plucks, stabs and arps.",
  wires=[(O1, F1), (F1, OUT)],
  routing="Osc 1 > Filter 1 > Out.",
  steps=[
      "<b>Menu > Load Init (Blank)</b>. Routing: " + QS101 + ".",
      "Osc 1: <b>Morph Basic</b>, Pos 0.66. Filter 1: Cutoff 700, Reso 0.2.",
      "Amp Env: Attack 0.001, Decay 0.45, Sustain 0, Release 0.25.",
      "Mod 2 (Envelope): Attack 0.001, Decay 0.25, Sustain 0, Release 0.2. Drag its chip onto Filter 1 <b>Cutoff</b>, amount +0.40.",
      "FX: Delay Sync on, Division 1/8, Mix 0.15; Reverb Mix 0.2.",
  ],
  settings=[
      ("Osc 1", "Wavetable / Pos", "Morph Basic / 0.66"),
      ("Filter 1", "Cutoff / Reso", "700 Hz / 0.2"),
      ("Amp Env", "Attack / Decay / Sustain / Release", "0.001 / 0.45 / 0 / 0.25"),
      ("Mod 2 (Envelope)", "Attack / Decay / Sustain / Release", "0.001 / 0.25 / 0 / 0.2"),
      ("FX", "Delay (Sync, 1/8) / Reverb", "Mix 0.15 / Mix 0.2"),
  ],
  mods=[("Mod 2", "Filter 1 Cutoff", "+0.40", "Bright attack that darkens quickly.")],
  tips=["Detuned Pluck: Unison 4, Detune 16, Cutoff 900. Soft Pluck: Pos 0.3, Cutoff 600, amount +0.30.",
        "Because Sustain is 0 the note decays even when you hold the key; Decay is the pluck length.",
        "EDM Stab: Unison 6, Detune 26, Decay 0.28, Cutoff 2000 (factory <i>EDM Stab</i>)."])

T(title="Bell", group="Plucks and Keys", preset="Bell Pluck, Glass Pluck",
  goal="A bright inharmonic strike from the FM Bells wavetable, ringing out.",
  wires=[(O1, F1), (F1, OUT)],
  routing="Osc 1 > Filter 1 > Out.",
  steps=[
      "<b>Menu > Load Init (Blank)</b>. Routing: " + QS101 + ".",
      "Osc 1: wavetable <b>FM Bells</b>, Pos 0.4. Filter 1: Cutoff 6000, Reso 0.12.",
      "Amp Env: Attack 0.001, Decay 0.9, Sustain 0, Release 0.5.",
      "Mod 2 (Envelope): Attack 0.001, Decay 0.4, Sustain 0, Release 0.3, chip onto Filter 1 <b>Cutoff</b>, amount +0.10.",
      "FX: Reverb Mix 0.2; Delay Sync on, Division 1/8, Mix 0.15.",
  ],
  settings=[
      ("Osc 1", "Wavetable / Pos", "FM Bells / 0.4"),
      ("Filter 1", "Cutoff / Reso", "6000 Hz / 0.12"),
      ("Amp Env", "Attack / Decay / Sustain / Release", "0.001 / 0.9 / 0 / 0.5"),
      ("Mod 2 (Envelope)", "Attack / Decay / Sustain / Release", "0.001 / 0.4 / 0 / 0.3"),
  ],
  mods=[("Mod 2", "Filter 1 Cutoff", "+0.10", "Softens the strike as the note rings.")],
  tips=["Move Osc 1 <b>Pos</b> from 0 (soft, near-sine) to 1 (bright, harsh) to change the bell's character.",
        "Glass Pluck: wavetable Glass Harmonics, Pos 0.35, Cutoff 7000, Decay 0.8.",
        "Play high notes: bells sit best two to three octaves above middle C."])

T(title="Electric piano", group="Plucks and Keys", preset="Warm E-Piano, Soft Rhodes, Tine Keys",
  goal="Soft FM tines with velocity-controlled brightness and a gentle chorus.",
  wires=[(O1, F1), (F1, OUT)],
  routing="Osc 1 > Filter 1 > Out.",
  steps=[
      "<b>Menu > Load Init (Blank)</b>. Routing: " + QS101 + ".",
      "Osc 1: wavetable <b>FM Bells</b>, Pos 0.12. Filter 1: Cutoff 3500, Reso 0.1. Open the <b>Voice</b> tab and set <b>Vel Sens</b> to 0.9.",
      "Amp Env: Attack 0.002, Decay 1.2, Sustain 0, Release 0.5.",
      "Mod 2 (Envelope): Attack 0.001, Decay 0.5, Sustain 0.2, Release 0.3; chip onto Filter 1 <b>Cutoff</b> at +0.15.",
      "Drag the <b>Velocity</b> chip onto Osc 1 <b>Pos</b> at +0.2: harder keys give brighter tines.",
      "FX: Chorus Mix 0.3, Reverb Mix 0.2.",
  ],
  settings=[
      ("Osc 1", "Wavetable / Pos", "FM Bells / 0.12"),
      ("Filter 1", "Cutoff / Reso", "3500 Hz / 0.1"),
      ("Voice tab", "Vel Sens", "0.9"),
      ("Amp Env", "Attack / Decay / Sustain / Release", "0.002 / 1.2 / 0 / 0.5"),
      ("Mod 2 (Envelope)", "Attack / Decay / Sustain / Release", "0.001 / 0.5 / 0.2 / 0.3"),
      ("FX", "Chorus Mix / Reverb Mix", "0.3 / 0.2"),
  ],
  mods=[("Mod 2", "Filter 1 Cutoff", "+0.15", "Tine attack."), ("Velocity", "Osc 1 Position", "+0.20", "Touch-sensitive brightness.")],
  tips=["Sustain 0 gives a piano-like decay even while holding the key; lengthen Decay for a more sustained electric piano.",
        "Soft Rhodes: Pos 0.08, Cutoff 2800, Decay 1.5, Velocity onto Filter 1 Cutoff +0.2 instead of Position."])

T(title="Drawbar organ", group="Plucks and Keys", preset="Drawbar Organ, Rock Organ",
  goal="The Drawbar Organ wavetable turns the position knob into a registration control.",
  wires=[(O1, F1), (F1, OUT)],
  routing="Osc 1 > Filter 1 > Out.",
  steps=[
      "<b>Menu > Load Init (Blank)</b>. Routing: " + QS101 + ".",
      "Osc 1: wavetable <b>Drawbar Organ</b>, Pos 0.3. Filter 1: Cutoff 9000, Reso 0.",
      "Amp Env: Attack 0.003, Decay 0.2, Sustain 1.0, Release 0.08 (organs have no decay).",
      "FX: Chorus Mix 0.3 (stand-in for the rotary speaker), Reverb Mix 0.15, Dist Drive 0.3, Dist Mix 0.15.",
      "Drag macro chip <b>M1</b> onto Osc 1 <b>Pos</b>. M1 is renamed 'Osc 1 Position': turn it live to change registrations.",
  ],
  settings=[
      ("Osc 1", "Wavetable / Pos", "Drawbar Organ / 0.3"),
      ("Filter 1", "Cutoff / Reso", "9000 Hz / 0"),
      ("Amp Env", "Attack / Decay / Sustain / Release", "0.003 / 0.2 / 1.0 / 0.08"),
      ("FX", "Chorus Mix / Reverb Mix / Dist Drive / Dist Mix", "0.3 / 0.15 / 0.3 / 0.15"),
  ],
  mods=[("Macro 1", "Osc 1 Position", "+0.5 (default)", "Live registration control; the macro takes the knob's name.")],
  tips=["Rock Organ: Pos 0.7, Dist Drive 0.5, Dist Mix 0.4, Chorus Mix 0.2.",
        "Position morphs through different mixes of the 1st, 2nd, 3rd, 4th, 6th, 8th, 10th, 12th and 16th harmonics.",
        "Add key click: Noise Level 0.05, Color 0.9, routed to Filter 1, with a very short Mod envelope on Noise Level."])

# ============================================================================================ PADS
T(title="String pad", group="Pads", preset="Warm Strings, Wide Saw Wash, Velvet",
  goal="A slow-attack saw ensemble with chorus and a long reverb.",
  wires=[(O1, F1), (F1, OUT)],
  routing="Osc 1 > Filter 1 > Out.",
  steps=[
      "<b>Menu > Load Init (Blank)</b>. Routing: " + QS101 + ".",
      "Osc 1: <b>Morph Basic</b>, Pos 0.66, Unison 6, Detune 22. Filter 1: Cutoff 2400, Reso 0.1.",
      "Amp Env: Attack 0.8, Decay 0.6, Sustain 0.85, Release 1.6.",
      "FX: Chorus Mix 0.35; Reverb Size 0.75, Mix 0.3.",
  ],
  settings=[
      ("Osc 1", "Wavetable / Pos / Unison / Detune", "Morph Basic / 0.66 / 6 / 22 ct"),
      ("Filter 1", "Cutoff / Reso", "2400 Hz / 0.1"),
      ("Amp Env", "Attack / Decay / Sustain / Release", "0.8 / 0.6 / 0.85 / 1.6"),
      ("FX", "Chorus Mix / Reverb Size / Reverb Mix", "0.35 / 0.75 / 0.3"),
  ],
  tips=["Add Osc 2 (Morph Basic, Pos 0.66) a fifth up or an octave down at a lower Level for body.",
        "A slow filter envelope (Mod 2: Attack 1.5, amount +0.35 on Cutoff) makes the pad 'open' as you hold it (factory <i>Sunrise</i>).",
        "Drag M1 onto Filter 1 Cutoff and M2 onto Reverb Mix to play the pad's brightness and space."])

T(title="Choir and vowel pad", group="Pads", preset="Choir Dream, Evolving Vowels, Aurora",
  goal="The Vowel Choir wavetable scanned slowly by an LFO.",
  wires=[(O1, F1), (F1, OUT)],
  routing="Osc 1 > Filter 1 > Out.",
  steps=[
      "<b>Menu > Load Init (Blank)</b>. Routing: " + QS101 + ".",
      "Osc 1: wavetable <b>Vowel Choir</b>, Pos 0.3, Unison 5, Detune 14. Filter 1: Cutoff 7000, Reso 0.15.",
      "Amp Env: Attack 0.8, Decay 0.6, Sustain 0.85, Release 1.6.",
      "Mod 2: Type <b>LFO</b>, Shape <b>Sine</b>, Rate 0.2 Hz. Chip onto Osc 1 <b>Pos</b>, amount +0.12.",
      "FX: Reverb Size 0.85, Mix 0.45.",
  ],
  settings=[
      ("Osc 1", "Wavetable / Pos / Unison / Detune", "Vowel Choir / 0.3 / 5 / 14 ct"),
      ("Filter 1", "Cutoff / Reso", "7000 Hz / 0.15"),
      ("Amp Env", "Attack / Decay / Sustain / Release", "0.8 / 0.6 / 0.85 / 1.6"),
      ("Mod 2 (LFO)", "Shape / Rate", "Sine / 0.2 Hz"),
      ("FX: Reverb", "Size / Mix", "0.85 / 0.45"),
  ],
  mods=[("Mod 2 (LFO)", "Osc 1 Position", "+0.12", "Drifts between neighbouring vowels.")],
  tips=["Position 0, 0.25, 0.5, 0.75 and 1.0 are the vowels A, E, I, O, U. The vowel shapes are baked into the waveform, so they shift with the note you play: they sound most natural in the low-to-middle register.",
        "Evolving Vowels: Pos 0, LFO Rate 0.07 Hz, amount +0.8 sweeps the whole vowel range slowly."])

T(title="Brass stab", group="Pads", preset="Cinematic Brass Lead (slower), EDM Stab (shorter)",
  goal="Two saws with a filter envelope that opens quickly: brass swells and stabs.",
  wires=[(O1, F1), (O2, F1), (F1, OUT)],
  routing="Osc 1 + Osc 2 > Filter 1 > Out.",
  steps=[
      "<b>Menu > Load Init (Blank)</b>. Routing: " + QS102 + ".",
      "Osc 1: <b>Morph Basic</b>, Pos 0.66, Unison 4, Detune 12. Osc 2: <b>Morph Basic</b>, Pos 0.66, Fine +6, Unison 2, Level 0.5.",
      "Filter 1: Ladder / LP 24, Cutoff 1200, Reso 0.15.",
      "Amp Env: Attack 0.03, Decay 0.25, Sustain 0.7, Release 0.15.",
      "Mod 2 (Envelope): Attack 0.04, Decay 0.3, Sustain 0.35, Release 0.2; chip onto Filter 1 <b>Cutoff</b>, amount +0.35.",
      "FX: Reverb Mix 0.2.",
  ],
  settings=[
      ("Osc 1", "Wavetable / Pos / Unison / Detune", "Morph Basic / 0.66 / 4 / 12 ct"),
      ("Osc 2", "Wavetable / Pos / Fine / Unison / Level", "Morph Basic / 0.66 / +6 ct / 2 / 0.5"),
      ("Filter 1", "Cutoff / Reso", "1200 Hz / 0.15"),
      ("Amp Env", "Attack / Decay / Sustain / Release", "0.03 / 0.25 / 0.7 / 0.15"),
      ("Mod 2 (Envelope)", "Attack / Decay / Sustain / Release", "0.04 / 0.3 / 0.35 / 0.2"),
  ],
  mods=[("Mod 2", "Filter 1 Cutoff", "+0.35", "The 'blat' as the brass opens up.")],
  tips=["For a slow orchestral swell (<i>Cinematic Brass Lead</i> style) use Amp Attack 0.1, Mod 2 Attack 0.12, Decay 0.4, Sustain 0.6 and a bigger reverb.",
        "Drag Velocity onto Filter 1 Cutoff (+0.2) so harder hits sound more brassy."])

# ============================================================================================ FX / TEXTURES
T(title="Riser and sweep", group="Effects", preset="Riser, Downlifter",
  goal="A long build: a noisy saw stack whose filter and pitch rise over several seconds.",
  wires=[(O1, F1), (NZ, F1), (F1, OUT)],
  routing="Osc 1 and Noise > Filter 1 > Out.",
  steps=[
      "<b>Menu > Load Init (Blank)</b>. Routing: " + QS101 + ", then drag a wire from <b>Noise</b> to <b>Filter 1</b>.",
      "Osc 1: wavetable <b>Digital Grit</b>, Pos 0.2, Unison 4, Detune 40. Noise: Level 0.35, Color 0.8, Type White.",
      "Filter 1: Ladder / LP 24, Cutoff 300, Reso 0.4. Amp Env: Attack 1.0, Decay 0.5, Sustain 1.0, Release 1.0.",
      "Mod 2 (Envelope): Attack 6.0, Decay 0.1, Sustain 1.0, Release 0.5. Chip onto Filter 1 <b>Cutoff</b> (+0.70) and Osc 1 <b>Pitch</b> (+0.15).",
      "FX: Reverb Mix 0.35. Hold a note for at least 6 seconds.",
  ],
  settings=[
      ("Osc 1", "Wavetable / Pos / Unison / Detune", "Digital Grit / 0.2 / 4 / 40 ct"),
      ("Noise", "Level / Color / Type", "0.35 / 0.8 / White"),
      ("Filter 1", "Cutoff / Reso", "300 Hz / 0.4"),
      ("Amp Env", "Attack / Decay / Sustain / Release", "1.0 / 0.5 / 1.0 / 1.0"),
      ("Mod 2 (Envelope)", "Attack / Decay / Sustain / Release", "6.0 / 0.1 / 1.0 / 0.5"),
  ],
  mods=[("Mod 2", "Filter 1 Cutoff", "+0.70", "The sweep upwards."), ("Mod 2", "Osc 1 Pitch", "+0.15", "About 14 semitones of rise.")],
  tips=["Downlifter: Cutoff 9000, Mod 2 Attack 0.001, Decay 4.0, Sustain 0, amounts -0.6 (Cutoff) and -0.12 (Pitch), Amp Env Decay 4.0.",
        "To make the riser fit the music: attack seconds = beats x 60 / BPM (8 beats at 120 BPM = 4 s). The longest attack is 10 s."])

T(title="Laser zap", group="Effects", preset="Laser Zap",
  goal="A very fast downward pitch sweep on a hard-sync tone.",
  wires=[(O1, F1), (F1, OUT)],
  routing="Osc 1 > Filter 1 > Out.",
  steps=[
      "<b>Menu > Load Init (Blank)</b>. Routing: " + QS101 + ".",
      "Osc 1: wavetable <b>Hard Sync</b>, Pos 0.4. Filter 1: Cutoff 9000, Reso 0.3.",
      "Amp Env: Attack 0.001, Decay 0.3, Sustain 0, Release 0.1.",
      "Mod 2 (Envelope): Attack 0.0005, Decay 0.15, Sustain 0, Release 0.1. Chip onto Osc 1 <b>Pitch</b>, amount +0.35.",
      "FX: Delay Sync on, Division 1/8, Mix 0.25.",
  ],
  settings=[
      ("Osc 1", "Wavetable / Pos", "Hard Sync / 0.4"),
      ("Filter 1", "Cutoff / Reso", "9000 Hz / 0.3"),
      ("Amp Env", "Attack / Decay / Sustain / Release", "0.001 / 0.3 / 0 / 0.1"),
      ("Mod 2 (Envelope)", "Attack / Decay / Sustain / Release", "0.0005 / 0.15 / 0 / 0.1"),
  ],
  mods=[("Mod 2", "Osc 1 Pitch", "+0.35", "About 34 semitones of fall in 150 ms.")],
  tips=["Reverse the sign (-0.35) for an upward 'power-up' blip.",
        "Longer Mod 2 Decay (0.4) makes slower, more cartoonish zaps; higher Osc 1 Pos makes a more metallic zap."])

T(title="Wind and ocean", group="Effects", preset="Wind Texture, Ocean Wash",
  goal="Filtered noise with a slow random filter movement and a long envelope.",
  wires=[(NZ, F1), (F1, OUT)],
  routing="Noise > Filter 1 > Out.",
  steps=[
      "<b>Menu > Load Init (Blank)</b>. Routing: drag one wire from the Noise out-port to the Filter 1 in-port, and one from Filter 1 to Out.",
      "<b>Wind</b>: Noise Level 0.9, Type <b>Pink</b>, Color 0.4. Filter 1: Cutoff 900, Reso 0.4. Amp Env: Attack 1.5, Decay 0.5, Sustain 1.0, Release 2.0.",
      "Mod 2: Type <b>LFO</b>, Shape <b>Smooth Random</b>, Rate 0.13 Hz. Chip onto Filter 1 <b>Cutoff</b>, amount +0.30.",
      "FX: Reverb Size 0.9, Mix 0.4.",
      "<b>Ocean</b>: Type <b>Brown</b>, Color 0.35, Cutoff 600, Reso 0.2, Amp Attack 2.0 / Release 3.0, LFO Shape Sine at 0.09 Hz, amount +0.35, Reverb Mix 0.45.",
  ],
  settings=[
      ("Noise (wind)", "Level / Type / Color", "0.9 / Pink / 0.4"),
      ("Filter 1 (wind)", "Cutoff / Reso", "900 Hz / 0.4"),
      ("Amp Env", "Attack / Decay / Sustain / Release", "1.5 / 0.5 / 1.0 / 2.0"),
      ("Mod 2 (LFO)", "Shape / Rate", "Smooth Random / 0.13 Hz"),
      ("Noise (ocean)", "Type / Color", "Brown / 0.35"),
  ],
  mods=[("Mod 2 (LFO)", "Filter 1 Cutoff", "+0.30 (wind), +0.35 (ocean)", "Slow gusting / surf swell.")],
  tips=["Oscillators stay silent because they are not routed. You do not need to lower their levels.",
        "A stormier wind: raise Filter 1 Reso to 0.6 and the LFO amount to +0.45."])

# ============================================================================================ PERFORMERS / SPECIAL
T(title="Arpeggio with a Performer", group="Sequenced and special", preset="Minor Arp, Major Arp",
  goal="A step sequence that moves Osc 1's pitch every 1/16 note while you hold a single key.",
  wires=[(O1, F1), (F1, OUT)],
  routing="Osc 1 > Filter 1 > Out.",
  steps=[
      "<b>Menu > Load Init (Blank)</b>. Routing: " + QS101 + ". Osc 1: <b>Morph Basic</b>, Pos 0.66. Filter 1: Cutoff 2600, Reso 0.25.",
      "Amp Env: Attack 0.001, Decay 0.2, Sustain 0.8, Release 0.1. Mod 2 (Envelope): Attack 0.001, Decay 0.15, Sustain 0.2, Release 0.1, chip onto Filter 1 Cutoff at +0.25.",
      "Open <b>Perf 1</b>. Steps 8, Sync on, Division <b>1/16</b>, Smooth 0.",
      "Drag the <b>Perf 1</b> chip onto Osc 1 <b>Pitch</b> and edit the amount to +0.25. With this amount a full-height bar is +24 semitones.",
      "Draw the bars (minor arpeggio): step heights 0, 0.125, 0.29, 0.5, 0.625, 0.5, 0.29, 0.125. That is 0, +3, +7, +12, +15, +12, +7, +3 semitones. Hold a key: the arpeggio climbs and falls.",
      "FX: Delay Sync on, 1/8, Mix 0.25; Reverb Mix 0.2.",
  ],
  settings=[
      ("Osc 1", "Wavetable / Pos", "Morph Basic / 0.66"),
      ("Filter 1", "Cutoff / Reso", "2600 Hz / 0.25"),
      ("Amp Env", "Attack / Decay / Sustain / Release", "0.001 / 0.2 / 0.8 / 0.1"),
      ("Perf 1", "Steps / Sync / Division / Smooth", "8 / on / 1/16 / 0"),
      ("Perf 1 bars", "Heights (steps 1 to 8)", "0, 0.125, 0.29, 0.5, 0.625, 0.5, 0.29, 0.125"),
  ],
  mods=[("Perf 1", "Osc 1 Pitch", "+0.25", "Full bar = 24 semitones; height x 24 = semitones."),
        ("Mod 2", "Filter 1 Cutoff", "+0.25", "A little pluck at the start of the note.")],
  tips=["Performer pitch steps are continuous, not snapped to semitones, so drawn bars can be a few cents out. For exact values use <b>Patterns > Save pattern...</b> to create a .psxlperf file, edit it in a text editor so it contains <i>0,0.125,0.292,0.5,0.625,0.5,0.292,0.125,0,0,0,0,0,0,0,0</i>, then <b>Patterns > Load pattern...</b>. Setting the interface to 150 to 200 percent (Menu > Settings > Interface size) also helps when drawing.",
        "Quick shapes live in <b>Patterns</b>: Ramp up, Ramp down, Triangle, Alternate high / low, Random, Flat, All zero, Gate on/off pairs.",
        "The factory <i>Minor Arp</i> uses amount +0.125 (12 st per bar); its 15-semitone step exceeds the bar range and plays as 12 semitones.",
        "Each note has its own performer that restarts on note-on, so chords stay in step when played together."])

T(title="Trance gate with a Performer", group="Sequenced and special", preset="Trance Gate Lead, Gate Pad",
  goal="A rhythmic gate: a Performer opens and closes the amp level in 16th notes.",
  wires=[(O1, F1), (F1, OUT)],
  routing="Osc 1 > Filter 1 > Out.",
  steps=[
      "<b>Menu > Load Init (Blank)</b>. Routing: " + QS101 + ". Osc 1: <b>Morph Basic</b>, Pos 0.66, Unison 6, Detune 24. Filter 1: Cutoff 6000, Reso 0.15.",
      "Amp Env: Attack 0.005, Decay 0.3, Sustain 1.0, Release 0.2. In the <b>Amp</b> panel set <b>Level</b> to 0 (the performer will open it).",
      "Open <b>Perf 1</b>: Steps 16, Sync on, Division 1/16, Smooth 0.15.",
      "Draw the pattern (1 = full bar, 0 = empty): 1 0 1 1 0 1 0 1 1 0 1 0 1 1 0 0. Quickest route: <b>Patterns > Gate: on/off pairs</b> then adjust bars.",
      "Drag the <b>Perf 1</b> chip onto the Amp <b>Level</b> knob; edit the amount to +0.75.",
      "FX: Delay Sync on, 1/8, Mix 0.3; Reverb Mix 0.25. Hold a chord.",
  ],
  settings=[
      ("Osc 1", "Wavetable / Pos / Unison / Detune", "Morph Basic / 0.66 / 6 / 24 ct"),
      ("Filter 1", "Cutoff / Reso", "6000 Hz / 0.15"),
      ("Amp", "Level", "0"),
      ("Amp Env", "Attack / Decay / Sustain / Release", "0.005 / 0.3 / 1.0 / 0.2"),
      ("Perf 1", "Steps / Sync / Division / Smooth", "16 / on / 1/16 / 0.15"),
  ],
  mods=[("Perf 1", "Amp Level", "+0.75", "Bars become the gate pattern; a small Smooth avoids clicks.")],
  tips=["The gate pattern restarts on each note-on, so play notes on the beat to keep it in time.",
        "For a gentler pulse keep the empty bars at 0.2 instead of 0.",
        "<i>Gate Pad</i> uses 8 steps (1 1 0 1 1 0 1 0) and a pad sound instead of a lead."])

T(title="Talking filter (formant)", group="Sequenced and special", preset="Talking Bass, Robot Voice",
  goal="The Formant filter model sweeps through vowels as the Cutoff moves.",
  wires=[(O1, F1), (F1, OUT)],
  routing="Osc 1 > Filter 1 > Out.",
  steps=[
      "<b>Menu > Load Init (Blank)</b>. Routing: " + QS101 + ". Osc 1: <b>Morph Basic</b>, Pos 0.66 (saw).",
      "Filter 1: Model <b>Formant</b>, Mode <b>Male</b>, Cutoff 700, Reso 0.55. Amp Env: Attack 0.003, Decay 0.3, Sustain 0.9, Release 0.15.",
      "Mod 2: Type <b>LFO</b>, Shape <b>Triangle</b>, Sync on, Division 1/4. Chip onto Filter 1 <b>Cutoff</b>, amount +0.22.",
      "Play sustained notes: the sound says a repeating 'ah - eh - ee - oh'.",
  ],
  settings=[
      ("Osc 1", "Wavetable / Pos", "Morph Basic / 0.66"),
      ("Filter 1", "Model / Mode / Cutoff / Reso", "Formant / Male / 700 Hz / 0.55"),
      ("Amp Env", "Attack / Decay / Sustain / Release", "0.003 / 0.3 / 0.9 / 0.15"),
      ("Mod 2 (LFO)", "Shape / Sync / Division", "Triangle / on / 1/4"),
  ],
  mods=[("Mod 2 (LFO)", "Filter 1 Cutoff", "+0.22", "Sweeps roughly from 'ah' toward 'oh' and back.")],
  tips=["Cutoff maps to vowels logarithmically: lowest = A, about 110 Hz = E, about 630 Hz = I, about 3.5 kHz = O, highest = U.",
        "Modes: Male, Female, Child (all formants higher) and Alien (lower, with a shifted second formant).",
        "Robot voice (<i>Robot Voice</i>): wavetable Vowel Choir, Filter 1 Model Comb, Cutoff 300, Reso 0.7, and a Sample & Hold LFO on Osc 1 Pos."])

T(title="FM bell with Phase Mod", group="Sequenced and special", preset="No factory preset uses Phase Mod. Compare Bell Pluck and Cowbell FM (FM Bells wavetable).",
  goal="Osc 2 silently phase-modulates Osc 1: a classic two-operator FM bell whose brightness decays.",
  wires=[(O1, F1), (F1, OUT)],
  routing="Osc 1 > Filter 1 > Out. Osc 2 is not routed: it works as a modulator only.",
  steps=[
      "<b>Menu > Load Init (Blank)</b>. Routing: " + QS101 + " (only Osc 1 is heard).",
      "Osc 1: wavetable <b>Morph Basic</b>, Pos 0 (sine), Level 0.8, <b>PhaseMod</b> 0.10. Phase Mod on Osc 1 means <i>Osc 2 modulates Osc 1</i>.",
      "Osc 2: wavetable <b>Morph Basic</b>, Pos 0 (sine), Pitch +22. Level can stay at its default: Osc 2 is not routed, so it is inaudible, but it still modulates Osc 1.",
      "Filter 1: Cutoff 9000, Reso 0.05. Amp Env: Attack 0.001, Decay 1.8, Sustain 0, Release 1.0.",
      "Mod 2 (Envelope): Attack 0.001, Decay 0.6, Sustain 0, Release 0.4. Chip onto Osc 1 <b>PhaseMod</b>, amount +0.50: the FM index starts high and decays.",
      "FX: Reverb Size 0.7, Mix 0.3.",
  ],
  settings=[
      ("Osc 1", "Wavetable / Pos / PhaseMod", "Morph Basic / 0 / 0.10"),
      ("Osc 2", "Wavetable / Pos / Pitch", "Morph Basic / 0 / +22 (about ratio 3.4:1)"),
      ("Filter 1", "Cutoff / Reso", "9000 Hz / 0.05"),
      ("Amp Env", "Attack / Decay / Sustain / Release", "0.001 / 1.8 / 0 / 1.0"),
      ("Mod 2 (Envelope)", "Attack / Decay / Sustain / Release", "0.001 / 0.6 / 0 / 0.4"),
      ("FX: Reverb", "Size / Mix", "0.7 / 0.3"),
  ],
  mods=[("Mod 2", "Osc 1 PhaseMod", "+0.50", "Bright inharmonic strike that mellows as the index decays.")],
  tips=["Pitch +12 / +19 / +24 on Osc 2 gives harmonic ratios 2, 3, 4 (organ or e-piano). Odd values such as +22 or Osc 2 Fine give bells.",
        "Osc 2's own Phase Mod is driven by Osc 1 (feedback-style FM); leave it at 0 for a clean two-operator bell.",
        "Raise Osc 1 Fold for extra metallic edge."])

T(title="Tempo-synced stutter", group="Sequenced and special", preset="Glitch Stutter",
  goal="A square LFO chops the Amp Level into 1/16 note gates, with a bit-crusher for grit.",
  wires=[(O1, F1), (F1, INS), (INS, OUT)],
  routing="Osc 1 > Filter 1 > Insert > Out.",
  steps=[
      "<b>Menu > Load Init (Blank)</b>. Routing tab: draw Osc 1 > Filter 1, Filter 1 > Insert, Insert > Out.",
      "Osc 1: wavetable <b>Digital Grit</b>, Pos 0.5. Filter 1: Cutoff 3000, Reso 0.3. Insert: Type <b>Bitcrush</b>, Drive 0.6, Mix 0.9.",
      "Amp Env: Attack 0.003, Decay 0.3, Sustain 0.9, Release 0.2.",
      "Mod 2: Type <b>LFO</b>, Shape <b>Square</b>, Sync on, Division 1/16, <b>Bipolar off</b>. Chip onto Amp <b>Level</b>, amount -0.90.",
      "Hold a note: the sound chops on and off in 16th notes.",
  ],
  settings=[
      ("Osc 1", "Wavetable / Pos", "Digital Grit / 0.5"),
      ("Filter 1", "Cutoff / Reso", "3000 Hz / 0.3"),
      ("Insert", "Type / Drive / Mix", "Bitcrush / 0.6 / 0.9"),
      ("Amp Env", "Attack / Decay / Sustain / Release", "0.003 / 0.3 / 0.9 / 0.2"),
      ("Mod 2 (LFO)", "Shape / Sync / Division / Bipolar", "Square / on / 1/16 / off"),
  ],
  mods=[("Mod 2 (LFO)", "Amp Level", "-0.90", "Unipolar square: the LFO pushes the level to zero for half of each cycle.")],
  tips=["Change Division to 1/8 or 1/8T for different grooves; Phase shifts where in the bar the gate begins.",
        "Use Smooth Random or Sample & Hold on a second LFO onto Filter 1 Cutoff to vary each chop."])

# ============================================================================================ WORKFLOW
T(title="Build your own macro-controlled patch", group="Workflow", preset="Sweep Machine (macros set up for a bass)",
  goal="Make a simple lead and put its best controls on macros, using automatic macro naming.",
  wires=[(O1, F1), (O2, F1), (F1, OUT)],
  routing="Osc 1 + Osc 2 > Filter 1 > Out.",
  steps=[
      "<b>Menu > Load Init (Blank)</b>. Routing: " + QS102 + ".",
      "Osc 1: <b>Morph Basic</b>, Pos 0.66, Unison 3, Detune 14. Osc 2: <b>Morph Basic</b>, Pos 0.66, Pitch -12, Level 0.5. Filter 1: Cutoff 1500, Reso 0.2. Amp Env: Attack 0.01, Decay 0.4, Sustain 0.8, Release 0.4.",
      "Select the <b>Filter 1</b> tab so its Cutoff and Reso knobs are visible. Drag the <b>M1</b> chip (the little crosshair under the first macro knob) onto the <b>Cutoff</b> knob. Look at the toast: Macro 1 now controls Filter 1 Cutoff, and the macro knob is relabelled 'Filter 1 Cutoff'.",
      "Drag <b>M2</b> onto <b>Reso</b>. Select the <b>Osc 1</b> tab and drag <b>M3</b> onto <b>Pos</b>. Open the <b>Verb</b> tab (right panel) and drag <b>M4</b> onto <b>Mix</b>: this is a global effect, which macros are allowed to control.",
      "Right-click the Cutoff knob > <b>Edit amount: Macro 1</b> and set it to +0.50. Right-click Reso and set +0.25.",
      "Drag <b>M5</b> onto Dist <b>Drive</b> and <b>M5</b> again onto Dist <b>Mix</b> (Dist tab). The macro keeps the name of the first target. Double-click the M5 chip (or right-click > Rename macro...) and call it 'Grit'.",
      "Menu > Save preset... switches to the Browse tab; click <b>Save preset...</b>, give it a name, pick a category and Save. The macro names are saved with the preset.",
  ],
  settings=[
      ("Osc 1", "Wavetable / Pos / Unison / Detune", "Morph Basic / 0.66 / 3 / 14 ct"),
      ("Osc 2", "Wavetable / Pos / Pitch / Level", "Morph Basic / 0.66 / -12 / 0.5"),
      ("Filter 1", "Cutoff / Reso", "1500 Hz / 0.2"),
      ("Amp Env", "Attack / Decay / Sustain / Release", "0.01 / 0.4 / 0.8 / 0.4"),
  ],
  mods=[("Macro 1", "Filter 1 Cutoff", "+0.50", "Macro auto-named 'Filter 1 Cutoff'."),
        ("Macro 2", "Filter 1 Reso", "+0.25", "Auto-named 'Filter 1 Reso'."),
        ("Macro 3", "Osc 1 Position", "+0.5 (default)", "Auto-named 'Osc 1 Position'."),
        ("Macro 4", "Reverb Mix", "+0.5 (default)", "A global target."),
        ("Macro 5", "Dist Drive and Dist Mix", "+0.5 (default)", "Renamed by you to 'Grit'.")],
  tips=["Right-click a macro knob > <b>MIDI Learn</b>, then move a hardware knob: the macro follows it (mapped CCs are stored with your DAW project).",
        "A macro can drive many parameters at once with different amounts, including negative ones: this is how one knob can open the filter while closing the reverb.",
        "Remove an assignment from the target knob: right-click > Remove Macro 1. If you did not rename the macro by hand its name returns to 'Macro 1' when its last assignment is removed."])

T(title="Import your own wavetable", group="Workflow", preset="Not applicable (user content)",
  goal="Turn any audio file into a playable wavetable and morph through it with Pos.",
  wires=[(O1, F1), (F1, OUT)],
  routing="Osc 1 > Filter 1 > Out.",
  steps=[
      "<b>Menu > Load Init (Blank)</b>. Routing: " + QS101 + ".",
      "Prepare a WAV, AIFF, FLAC or OGG file. Best results: a single cycle of 2048 samples (a one-frame table), or several 2048-sample cycles joined end to end (a multi-frame table).",
      "Drop the file on the oscillator display (the waveform window in the Oscillator panel), or press the <b>+</b> button next to the wavetable menu, or use <b>Menu > Settings > Import wavetable...</b>. The toast says 'Imported ... into Osc N'.",
      "The new table appears in the wavetable drop-down as 'User: filename' and is selected on the active oscillator. Sweep <b>Pos</b> through it.",
      "Set Filter 1 and Amp Env to taste (try Cutoff 8000, Attack 0.005, Decay 0.4, Sustain 0.8, Release 0.3) and save the preset: the imported table is saved inside user presets and your DAW project.",
  ],
  settings=[
      ("Osc 1", "Wavetable / Pos", "User: your file / 0 to 1"),
      ("Filter 1", "Cutoff / Reso", "8000 Hz / 0.15"),
      ("Amp Env", "Attack / Decay / Sustain / Release", "0.005 / 0.4 / 0.8 / 0.3"),
  ],
  tips=["How files are sliced: the file is mixed to mono and divided into frames of about 2048 samples (length divided by 2048, rounded, between 1 and 256 frames), each resampled to 2048 points. A short file becomes a single frame; a one-second 44.1 kHz recording becomes about 22 frames. The maximum is 256 frames, and very long files are read only up to about a million samples (roughly 24 seconds at 44.1 kHz) and squeezed into those 256 frames.",
        "Each frame is peak-normalised and its DC offset removed. Expect a texture, not a recording: the file is played as a looping cycle at the pitch of the key.",
        "There are 22 user slots (the drop-down shows them as 'User: ...'); when all are full the last one is replaced. The Voice tab lists user tables."])
