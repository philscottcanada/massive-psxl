"""Parameter reference data for Massive PSXL, transcribed from Source/Params.cpp.

Each section: (title, host group name, [rows]); a row is
(id, display name, range, default, notes, mod) with mod in {"V": voice modulation target,
"G": global modulation target, "": not a modulation target}.
"""

DIV = "1/1, 1/2, 1/4, 1/8, 1/16, 1/32, 1/4T, 1/8T, 1/16T"
LFO_SHAPES = "Sine, Triangle, Saw Up, Saw Down, Square, Sample & Hold, Smooth Random"
MODELS = "Ladder, State Variable, Comb, Formant"
INS_TYPES = "TanH, Fold, Bitcrush, Hard Clip, Rectify, Sine"
NOISE_TYPES = "White, Pink, Brown, Crackle"
VOICE_MODES = "Poly, Mono, Legato"
WT_NAMES = ("Morph Basic, Pulse Sweep, Harmonic Tilt, Vowel Choir, Hard Sync, FM Bells, "
            "Drawbar Organ, Glass Harmonics, Digital Grit, Fold Sweep")


def sections():
    S = []
    S.append(("Macros", "Macros 1-8 and Macros 9-16 (two host groups)",
              [(f"macro{i}", f"Macro {i}", "0 to 1", "0",
                "Display name changes at runtime (smart macro naming). Modulation SOURCE, not a target.", "") for i in range(1, 17)]))
    for o in (1, 2):
        n = f"Osc {o} "
        S.append((f"Oscillator {o}", f"Oscillator {o}", [
            (f"o{o}_pos", n + "Position", "0 to 1", "0", "Scans through the frames of the selected wavetable.", "V"),
            (f"o{o}_pitch", n + "Pitch", "-48 to +48 st", "0", "Whole-semitone steps on the knob; modulation is smooth (not quantised).", "V"),
            (f"o{o}_fine", n + "Fine", "-100 to +100 ct", "0", "", "V"),
            (f"o{o}_level", n + "Level", "0 to 1", "0.8", "Level into the routing. Phase modulation still uses the oscillator at Level 0.", "V"),
            (f"o{o}_uni", n + "Unison", "1 to 8", "1", "Number of stacked voices (integer).", ""),
            (f"o{o}_detune", n + "Detune", "0 to 100 ct", "15", "Total unison spread (+/- cents across the stack). Mid-travel = 20 ct.", "V"),
            (f"o{o}_pm", n + "Phase Mod", "0 to 1", "0", "Osc 2's output modulates Osc 1's phase (and Osc 1 modulates Osc 2).", "V"),
            (f"o{o}_fold", n + "Fold", "0 to 1", "0", "Wavefolder after the oscillator.", "V"),
            (f"o{o}_wt", n + "Wavetable", "0 to 31 (slot)", "0" if o == 1 else "1",
             f"Slots 0-9 are built in ({WT_NAMES}); slots 10-31 hold imported tables.", ""),
        ]))
    S.append(("Noise", "Noise + Filter 1", [
        ("n_level", "Noise Level", "0 to 1", "0.5", "", "V"),
        ("n_color", "Noise Color", "0 to 1", "0.5", "Below 0.5 = low-pass, 0.5 = unfiltered, above 0.5 = high-pass.", "V"),
        ("n_type", "Noise Type", NOISE_TYPES, "White", "", ""),
    ]))
    for f in (1, 2):
        n = f"Filter {f} "
        S.append((f"Filter {f}", f"Filter {f}", [
            (f"f{f}_cut", n + "Cutoff", "20 to 20000 Hz", "12000" if f == 1 else "8000", "Skewed: mid-travel = 1000 Hz. In Comb it sets the comb pitch, in Formant the vowel.", "V"),
            (f"f{f}_res", n + "Reso", "0 to 1", "0.15", "", "V"),
            (f"f{f}_drive", n + "Drive", "0 to 1", "0", "Saturation ahead of the filter (about 1x to 8x gain).", "V"),
            (f"f{f}_ktr", n + "Key Track", "-1 to +1", "0", "+1 = cutoff follows the keyboard 1:1 around note 60 (middle C).", ""),
            (f"f{f}_model", n + "Model", MODELS, "Ladder", "", ""),
            (f"f{f}_mode", n + "Mode", "Mode 1 to Mode 4", "Mode 1",
             "Names depend on the Model: Ladder = LP 24, LP 12, BP, HP 24; State Variable = LP, BP, HP, Notch; "
             "Comb = Comb +, Comb -, Flange, Pluck; Formant = Male, Female, Child, Alien.", ""),
        ]))
    S.append(("Insert and Amp", "Insert + Amp", [
        ("ins_type", "Insert Type", INS_TYPES, "TanH", "", ""),
        ("ins_drive", "Insert Drive", "0 to 1", "0.3", "", "V"),
        ("ins_mix", "Insert Mix", "0 to 1", "0.5", "Dry/wet within the insert.", "V"),
        ("amp_level", "Amp Level", "0 to 1", "0.7", "Per-voice level after the amp envelope.", "V"),
        ("amp_pan", "Amp Pan", "-1 to +1", "0", "Equal-power pan.", "V"),
        ("amp_fb", "Amp Feedback", "0 to 1", "0", "Feeds a saturated copy of the voice output back into Filter 1 (or the Insert).", "V"),
    ]))
    S.append(("Voice and Master", "Voice + Master", [
        ("master_vol", "Volume", "0 to 1", "0.7", "Master gain follows volume squared (x2): 0.7 is about unity, 1.0 is +6 dB.", "G"),
        ("pitch", "Pitch", "-48 to +48 st", "0", "Global transpose in continuous semitones.", "V"),
        ("glide", "Glide Time", "0 to 5 s", "0", "Skewed: mid-travel = 0.4 s.", ""),
        ("glide_expo", "Glide Expo", "Off / On", "Off", "Exponential glide curve instead of constant time.", ""),
        ("voice_mode", "Voice Mode", VOICE_MODES, "Poly", "", ""),
        ("voices", "Polyphony", "1 to 16", "8", "Maximum simultaneous voices in Poly mode.", ""),
        ("bend_range", "Bend Range", "0 to 24 st", "2", "Pitch wheel range.", ""),
        ("vel_sens", "Velocity Sens", "0 to 1", "0.5", "0 = every note at full level; 1 = fully velocity-controlled.", ""),
    ]))
    S.append(("Amp Envelope", "Amp Envelope", mod_rows(1)))
    for s in range(2, 10):
        S.append((f"Modulator {s}", f"Modulator {s}", mod_rows(s)))
    for p in (1, 2, 3):
        n = f"Perf {p} "
        S.append((f"Performer {p}", f"Performer {p}", [
            (f"p{p}_steps", n + "Steps", "1 to 16", "8", "Loop length.", ""),
            (f"p{p}_rate", n + "Rate", "0.1 to 40 Hz", "4", "Steps per second when Sync is off. Mid-travel = 4 Hz.", ""),
            (f"p{p}_sync", n + "Sync", "Off / On", "On", "Locks the step rate to the host tempo.", ""),
            (f"p{p}_div", n + "Division", DIV, "1/16", "Length of one step when Sync is on.", ""),
            (f"p{p}_smooth", n + "Smooth", "0 to 1", "0", "Glide between steps; 1 = glide across the whole step.", ""),
        ]))
    S.append(("EQ and Distortion", "EQ + Distortion", [
        ("eq_lo_g", "EQ Low Gain", "-18 to +18 dB", "0", "Low shelf.", "G"),
        ("eq_lo_f", "EQ Low Freq", "40 to 400 Hz", "120", "", ""),
        ("eq_mid_g", "EQ Mid Gain", "-18 to +18 dB", "0", "Peaking band.", "G"),
        ("eq_mid_f", "EQ Mid Freq", "200 to 8000 Hz", "1000", "Skewed: mid-travel = 1500 Hz.", "G"),
        ("eq_mid_q", "EQ Mid Q", "0.3 to 6", "1", "", ""),
        ("eq_hi_g", "EQ High Gain", "-18 to +18 dB", "0", "High shelf.", "G"),
        ("eq_hi_f", "EQ High Freq", "2000 to 16000 Hz", "6000", "", ""),
        ("dist_drive", "Dist Drive", "0 to 1", "0.3", "", "G"),
        ("dist_mix", "Dist Mix", "0 to 1", "0", "Distortion is bypassed at 0.", "G"),
    ]))
    S.append(("Delay, Reverb and Chorus", "Delay + Reverb + Chorus", [
        ("dly_time", "Delay Time", "1 to 2000 ms", "350", "Skewed: mid-travel = 300 ms. Ignored while Sync is on.", ""),
        ("dly_sync", "Delay Sync", "Off / On", "Off", "", ""),
        ("dly_div", "Delay Division", DIV, "1/8", "Used when Sync is on.", ""),
        ("dly_fb", "Delay Feedback", "0 to 0.95", "0.35", "", "G"),
        ("dly_mix", "Delay Mix", "0 to 1", "0", "", "G"),
        ("rev_size", "Reverb Size", "0 to 1", "0.5", "", "G"),
        ("rev_damp", "Reverb Damping", "0 to 1", "0.5", "", ""),
        ("rev_mix", "Reverb Mix", "0 to 1", "0", "", "G"),
        ("cho_rate", "Chorus Rate", "0.05 to 8 Hz", "0.6", "Skewed: mid-travel = 0.8 Hz.", "G"),
        ("cho_depth", "Chorus Depth", "0 to 1", "0.5", "", "G"),
        ("cho_mix", "Chorus Mix", "0 to 1", "0", "", "G"),
    ]))
    return S


def mod_rows(s):
    n = "Amp Env " if s == 1 else f"Mod {s} "
    rows = []
    if s > 1:
        rows.append((f"m{s}_type", n + "Type", "Envelope, LFO", "Envelope", "Chooses what the slot does.", ""))
    rows += [
        (f"m{s}_att", n + "Attack", "0.5 ms to 10 s", "5 ms" if s == 1 else "10 ms", "Skewed: mid-travel = 0.3 s. Linear ramp.", ""),
        (f"m{s}_dec", n + "Decay", "1 ms to 10 s", "0.4 s", "Skewed: mid-travel = 0.4 s. Exponential.", ""),
        (f"m{s}_sus", n + "Sustain", "0 to 1", "0.8" if s == 1 else "0.5", "", ""),
        (f"m{s}_rel", n + "Release", "1 ms to 10 s", "0.25 s" if s == 1 else "0.3 s", "Skewed: mid-travel = 0.4 s. Exponential.", ""),
        (f"m{s}_dly", n + "Delay", "0 to 5 s", "0", "Wait before the attack starts. Skewed: mid-travel = 0.3 s.", ""),
        (f"m{s}_hold", n + "Hold", "0 to 5 s", "0", "Time held at the peak. Skewed: mid-travel = 0.3 s.", ""),
        (f"m{s}_level", n + "Level", "0 to 1", "1", "Scales the output of the slot (shown as Env Level for envelopes).", ""),
        (f"m{s}_oneshot", n + "One Shot", "Off / On", "Off", "Envelope ignores key release and runs through to its release stage.", ""),
    ]
    if s > 1:
        rows += [
            (f"m{s}_rate", n + "Rate", "0.01 to 50 Hz", "2", "LFO speed when Sync is off. Skewed: mid-travel = 2 Hz.", ""),
            (f"m{s}_shape", n + "Shape", LFO_SHAPES, "Sine", "", ""),
            (f"m{s}_phase", n + "Phase", "0 to 1", "0", "Start phase at note-on.", ""),
            (f"m{s}_fade", n + "Fade In", "0 to 10 s", "0", "Fades the LFO in after note-on. Skewed: mid-travel = 0.5 s.", ""),
            (f"m{s}_bipolar", n + "Bipolar", "Off / On", "On", "On = -1 to +1; Off = 0 to +1.", ""),
            (f"m{s}_sync", n + "Sync", "Off / On", "Off", "Locks the LFO to host tempo.", ""),
            (f"m{s}_div", n + "Division", DIV, "1/4", "Used when Sync is on.", ""),
        ]
    return rows
