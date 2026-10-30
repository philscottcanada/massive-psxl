"""Manual part B: chapters 6-10 (oscillators, noise, filters, insert/amp, master FX)."""
import psxl_docs as D
from psxl_docs import *


def ch6():
    st = [Banner(6, "Oscillators and Wavetables", "Two scanning oscillators, ten tables, your own audio")]
    st += [
        P("A wavetable is a stack of single-cycle waveforms called <b>frames</b>. The <b>Pos</b> (position) knob chooses which frame you hear and "
          "crossfades between neighbouring frames, so turning it morphs the timbre smoothly. Both oscillators have the same controls and can use the same or "
          "different tables."),
        H2("6.1  Oscillator controls"),
        tbl([["Knob", "Range", "Default", "What it does"],
             ["Pos", "0 to 1", "0", "Scans through the frames of the wavetable. Click or drag in the 3D display to set it directly."],
             ["Pitch", "-48 to +48 st", "0", "Coarse tuning in whole semitones. Under modulation it moves smoothly."],
             ["Fine", "-100 to +100 ct", "0", "Fine tuning. Pitch and Fine add together."],
             ["Level", "0 to 1", "0.8", "Output level into the routing."],
             ["Unison", "1 to 8", "1", "Number of stacked voices per note. Output is scaled by 1/sqrt(n) so the level stays steady."],
             ["Detune", "0 to 100 ct", "15", "Spread of the unison stack: voices are spread evenly from -Detune to +Detune cents."],
             ["PhaseMod", "0 to 1", "0", "Phase modulation from the <i>other</i> oscillator (6.4)."],
             ["Fold", "0 to 1", "0", "Wavefolder after the oscillator (6.5)."]],
            [0.9, 1, 0.7, 3.4], first_bold=True),
        P("The oscillator tab (Osc 1 or Osc 2) you are looking at decides which oscillator the knobs, the table menu and the display control. "
          "Osc 1 defaults to the first table, <b>Morph Basic</b>; Osc 2 defaults to the second, <b>Pulse Sweep</b>."),
        H2("6.2  The ten built-in wavetables"),
        P("Every built-in table has 32 frames. The table below says what you hear as Pos goes from 0 to 1."),
        tbl([["#", "Wavetable", "What Pos does", "Good for"],
             ["1", "Morph Basic", "Sine (0), triangle (about 0.33), saw (about 0.66), square (1.0), smoothly morphing between them.", "Everything: basses, leads, pads, drums."],
             ["2", "Pulse Sweep", "Pulse width from a 50 percent square (0) to a very narrow pulse of about 3 percent (1).", "PWM leads and pads, hollow basses, clavs."],
             ["3", "Harmonic Tilt", "Spectral slope from dull and almost sine-like (0) to very bright and buzzy (1).", "Keys, soft pads, harp-like plucks."],
             ["4", "Vowel Choir", "Vowels A, E, I, O, U at about 0, 0.25, 0.5, 0.75 and 1. The formants are fixed in the wave shape, so they move with the note you play.", "Choirs, vocal leads, talking sounds."],
             ["5", "Hard Sync", "A saw whose sync ratio rises from 1 (plain saw) to 8 (screaming sync).", "Sync leads, zaps, bass."],
             ["6", "FM Bells", "A sine with FM that gets brighter and moves through harmonic ratios 1 to 6 as Pos rises.", "Bells, electric piano, mallets, FM bass."],
             ["7", "Drawbar Organ", "Morphs through different drawbar-style registrations of harmonics 1, 2, 3, 4, 6, 8, 10, 12 and 16.", "Organs, reed-like pads."],
             ["8", "Glass Harmonics", "A bright, odd-harmonic stack with a resonant peak that travels from the low harmonics (3rd) up to about the 43rd.", "Glassy pads, bells, shimmering leads."],
             ["9", "Digital Grit", "A random-phase band of harmonics that starts narrow and low and widens and brightens.", "Gritty basses, noise-like risers and textures."],
             ["10", "Fold Sweep", "A sine that is progressively wavefolded: 0 is mild, 1 is heavily folded.", "Metallic leads and basses."]],
            [0.3, 1.1, 3.1, 1.6], align_center=(0,)),
        spacer(4),
        callout("tip", "Wavetables are band-limited: the engine chooses a version with fewer harmonics at high pitches, so even bright tables stay clean (little aliasing) up the keyboard."),
        H2("6.3  Unison"),
        P("<b>Unison</b> stacks up to eight copies of the oscillator, evenly detuned across <b>Detune</b>. Each note's unison voices start at random phases (the first voice always starts at phase 0), "
          "which gives the lush, never-identical supersaw character. Unison costs CPU: 8 unison voices on 8 notes is 64 oscillators. "
          "Reduce <b>Polyphony</b> (Voice tab) or Unison if your computer struggles."),
        H2("6.4  Phase Mod"),
        P("Each oscillator can phase-modulate the other: <b>Osc 1's PhaseMod</b> is driven by Osc 2's output, and <b>Osc 2's PhaseMod</b> by Osc 1's. "
          "This is the same idea as FM synthesis. The key points:"),
    ]
    st += bullets([
        "Both oscillators always run, even when not wired into the routing or when their Level is 0, so a <b>silent oscillator can still be the modulator</b>.",
        "The modulator's <b>Pitch</b> sets the carrier-to-modulator ratio. Whole-number ratios (+12 st = 2:1, +19 st = 3:1, +24 st = 4:1) give harmonic tones; other values give bells and clangs.",
        "Modulating <b>PhaseMod</b> with an envelope makes the tone start bright and mellow out, the classic FM pluck.",
        "Setting both oscillators' PhaseMod above zero makes them modulate each other (feedback-like FM) and gets rough quickly.",
    ])
    st += [
        H2("6.5  Fold"),
        P("<b>Fold</b> pushes the oscillator output into a sine-shaped wavefolder. Low settings add harmonics gently; high settings fold the wave back on itself for metallic, "
          "hollow timbres. It reacts to the oscillator's level, so Unison and the table choice matter."),
        H2("6.6  Wavetable library and importing your own"),
        P("The wavetable menu shows the ten built-in tables, then your imported tables labelled <b>User: name</b>. There are <b>22 user slots</b>. "
          "Use <b>&lt;</b> and <b>&gt;</b> beside the menu to step through the loaded tables."),
        H3("Three ways to import"),
    ]
    st += bullets([
        "<b>Drag and drop</b> a WAV, AIFF, FLAC or OGG file onto the wavetable display. It loads into the oscillator whose tab is open. The display's frame lights up magenta while you hover.",
        "Press the <b>+</b> button next to the wavetable menu in the Oscillator panel (also loads into the open oscillator).",
        "<b>Menu > Settings > Import wavetable...</b> or the <b>Import wavetable...</b> button in the <b>Voice</b> tab (these load into Osc 1).",
    ])
    st += [
        H3("How a file becomes a wavetable"),
    ]
    st += bullets([
        "The file is mixed down to mono.",
        "It is divided into frames: the number of frames is the length divided by 2048 samples, rounded, and limited to 1 to 256. Each frame is resampled to 2048 points.",
        "A short single-cycle file (say 2048 samples) therefore becomes <b>one frame</b>; a long recording becomes a many-frame table you can scan with Pos.",
        "Each frame has its DC offset removed and is peak-normalised, then band-limited like the built-in tables.",
        "The new table is named after the file, placed in the first free user slot (when all 22 are full the last slot is replaced) and selected automatically.",
        "Imported tables are saved with the DAW session and with <b>user presets</b>, so presets that use them travel with the table data. Factory presets only use built-in tables.",
        "If the file cannot be read, the toast says <i>Could not read that audio file</i>.",
    ])
    st.append(callout("tip", "For the cleanest results use single-cycle waveforms of exactly 2048 samples, or several of them joined end to end (for example 64 cycles = 131072 samples). "
                             "Recordings of voices, instruments or field sounds work too: they become evolving textures."))
    return st


def ch7():
    st = [Banner(7, "Noise", "White, pink, brown and crackle")]
    st += [
        P("The <b>NOISE</b> panel is a third source. Like the oscillators it does nothing until you wire the <b>Noise</b> node in the Routing tab."),
        tbl([["Control", "Range / choices", "Default", "What it does"],
             ["Level", "0 to 1", "0.5", "Output level into the routing."],
             ["Color", "0 to 1", "0.5", "A tone control: below 0.5 a low-pass (darker, from 20 kHz down to about 100 Hz at 0), 0.5 is neutral (unfiltered), above 0.5 a high-pass (thinner, up to about 10 kHz at 1)."],
             ["Type", "White, Pink, Brown, Crackle", "White", "Noise colour (spectrum) or texture."]],
            [0.8, 1.4, 0.7, 3.2], first_bold=True),
        H2("Noise types"),
        tbl([["Type", "Character", "Typical use"],
             ["White", "Equal energy at every frequency: bright, hissy.", "Hats, snares, risers, breath."],
             ["Pink", "Energy falls 3 dB per octave: balanced, natural.", "Wind, rain, softer percussion."],
             ["Brown", "Energy falls 6 dB per octave: deep rumble.", "Ocean, thunder, low drones."],
             ["Crackle", "Sparse random clicks that decay quickly, like vinyl dust.", "Texture, lo-fi crackle, metallic hits through a Comb filter."]],
            [0.9, 3, 1.7], first_bold=True),
        callout("tip", "Noise is a modulation target: you can modulate its <b>Level</b> and <b>Color</b>. A short envelope on Noise Level gives a click on a kick; "
                       "a slow LFO on Color gives breathing, swooshing noise."),
    ]
    return st


def ch8():
    st = [Banner(8, "Filters", "Four models, sixteen modes, two filters")]
    st += [
        P("Each of the two filters has a <b>Model</b> and a <b>Mode</b>. Changing the Model changes the list of Modes. Controls common to all models:"),
        tbl([["Control", "Range", "Default", "Notes"],
             ["Cutoff", "20 Hz to 20 kHz", "F1 12000 Hz, F2 8000 Hz", "Mid-travel is 1 kHz (a skewed scale, fine control at low frequencies). In Comb it sets the comb's pitch; in Formant it picks the vowel."],
             ["Reso", "0 to 1", "0.15", "Resonance. Its effect depends on the model."],
             ["Drive", "0 to 1", "0", "Saturation <i>before</i> the filter (gain from 1x up to 8x, with level compensation at low signals)."],
             ["KeyTrk", "-1 to +1", "0", "Key tracking around note 60. +1 makes the cutoff follow the keyboard 1:1 (an octave per octave); negative values open the filter on low notes."]],
            [0.8, 1.1, 1.3, 2.6], first_bold=True),
        H2("8.1  Ladder"),
        P("A four-stage transistor-ladder-style low-pass with a soft saturating feedback path. Warm, fat and the best for basses and acid lines. "
          "Near the top of the Reso range it rings almost like a sine."),
        tbl([["Mode", "Result", "Slope"],
             ["LP 24", "Four-pole low-pass: the classic fat filter.", "24 dB/octave"],
             ["LP 12", "Two-pole low-pass: brighter, more open.", "12 dB/octave"],
             ["BP", "Band-pass between the second and fourth stages: a narrow, nasal band.", "roughly 12 dB each side"],
             ["HP 24", "Four-pole high-pass: removes lows, good for thinning.", "24 dB/octave"]],
            [0.8, 3.7, 1.1], first_bold=True),
        H2("8.2  State Variable"),
        P("A clean 12 dB/octave multimode filter. Resonance is precise and musical rather than aggressive; Reso 1 is strongly resonant but stable."),
        tbl([["Mode", "Result"],
             ["LP", "Low-pass."], ["BP", "Band-pass: the choice for snares, claps and telephone tones."],
             ["HP", "High-pass: hats and shakers."], ["Notch", "Removes a band: phaser-like when swept."]],
            [0.8, 4.8], first_bold=True),
        H2("8.3  Comb"),
        P("A short feedback delay line. <b>Cutoff</b> sets the delay time as a frequency: the comb resonates at the Cutoff frequency and its harmonics. "
          "Set <b>KeyTrk</b> to +1 and tune <b>Cutoff</b> so the comb follows the keys. <b>Reso</b> controls the feedback."),
        tbl([["Mode", "Result"],
             ["Comb +", "Positive feedback: bright ringing at the comb frequency and all its harmonics."],
             ["Comb -", "Negative feedback: hollow, odd-harmonic resonance."],
             ["Flange", "Feed-forward comb: moving notches (jet-plane flanging when Cutoff is modulated). Reso has no effect in this mode."],
             ["Pluck", "Damped feedback: a Karplus-Strong style plucked-string resonance. Reso sets how long the string rings. Works with a noise or short sound as the exciter."]],
            [0.8, 4.8], first_bold=True),
        H2("8.4  Formant"),
        P("Three resonant band-pass filters tuned to vocal formants. <b>Cutoff</b> no longer means a frequency of cut-off: it <b>scans through the vowels</b> A, E, I, O, U. "
          "<b>Reso</b> sets the sharpness of the formants (from soft to very vowel-like)."),
        tbl([["Cutoff (approx.)", "Vowel"],
             ["20 Hz (fully anticlockwise)", "A"], ["about 110 Hz", "E"], ["about 630 Hz", "I"], ["about 3.5 kHz", "O"], ["20 kHz (fully clockwise)", "U (reached at the very end)"]],
            [1.6, 2.2], first_bold=True),
        tbl([["Mode", "Voice type"],
             ["Male", "Adult male formant frequencies."],
             ["Female", "Adult female formant frequencies (higher)."],
             ["Child", "The male set scaled up by 35 percent."],
             ["Alien", "The male set scaled down by 30 percent with the second formant shifted up by 50 percent."]],
            [0.8, 4.8], first_bold=True),
        P("Between the vowel points the formants interpolate smoothly, so sweeping the cutoff with an envelope or LFO makes the sound speak."),
        H2("8.5  Using two filters"),
    ]
    st += bullets([
        "<b>Series</b> (Filter 1 > Filter 2): steeper or combined responses, e.g. Ladder LP 24 into Formant for a vocal bass.",
        "<b>Parallel</b> (Osc 1 > Filter 1, Osc 2 > Filter 2, both to Out): each oscillator gets its own filter, e.g. a low-passed sub plus a high-passed layer.",
        "<b>Split roles</b>: one filter for tone (Ladder), the other for character (Comb or Formant).",
        "Filter 2 has its own Cutoff, Reso, Drive, KeyTrk, Model and Mode; its default Cutoff is 8000 Hz (Filter 1: 12000 Hz).",
    ])
    st.append(callout("tip", "<b>Filter Drive</b> and <b>Amp Feedback</b> are different: Drive saturates the signal entering a filter; Feedback loops the whole voice's output back to Filter 1. Both thicken the sound."))
    return st


def ch9():
    st = [Banner(9, "Insert and Amp", "Per-voice shaping, level, pan and feedback")]
    st += [
        H2("9.1  The Insert"),
        P("The <b>INSERT</b> is a waveshaping effect that sits inside each voice. It works like a node: wire a source or filter into it and wire it onward to Out (or nothing hears it). "
          "<b>Drive</b> (0 to 1, default 0.3) sets how hard the signal is pushed (about 1x to 15x gain) and <b>Mix</b> (0 to 1, default 0.5) blends dry and shaped signal. Both are modulation targets."),
        tbl([["Type", "What it does", "Sound"],
             ["TanH", "Smooth soft saturation.", "Warm analogue-style distortion; keeps low end tidy."],
             ["Fold", "Sine-shaped wavefolder.", "Metallic, hollow, rich overtones; reacts strongly to level."],
             ["Bitcrush", "Drive lowers the bit depth (from about 15 bits down to about 3) and holds each sample for up to 13 samples (reduces sample rate).", "Lo-fi, digital grit, aliasing."],
             ["Hard Clip", "Flat-tops the waveform at full scale.", "Aggressive, square-ish distortion."],
             ["Rectify", "Full-wave rectification (flips negative halves).", "Octave-up buzz and sub-bass reinforcement."],
             ["Sine", "A sine waveshaper that folds back at high drive.", "Smooth at low drive, glassy at high drive."]],
            [0.8, 2.5, 2.3], first_bold=True),
        callout("tip", "Drums: <i>Noise > Filter 1 > Insert > Out</i> is the quick setup for hats and snares. A fold or TanH insert with Mix 1.0 thickens a kick's attack."),
        H2("9.2  The Amp"),
        P("Every voice ends in the amp. Its controls are:"),
        tbl([["Control", "Range", "Default", "What it does"],
             ["Level", "0 to 1", "0.7", "Per-voice level after the amp envelope. A modulation target. Setting it to 0 and letting a Performer or LFO raise it is how gates work."],
             ["Pan", "-1 to +1", "0", "Equal-power stereo position of the voice. Modulate it for auto-pan."],
             ["Feedback", "0 to 1", "0", "Feeds a soft-saturated copy of the voice's output back into the input of Filter 1 (or the Insert if Filter 1 is not in use). Adds grit, resonance and instability."]],
            [0.8, 0.9, 0.7, 3.2], first_bold=True),
        P("The amp envelope is the <b>Amp Env</b> tab (chapter 11). The voice level is: amp envelope x Amp Level x velocity scale, where the velocity scale is "
          "(1 - Vel Sens) + Vel Sens x velocity. With Vel Sens 0 every note plays at full level; with 1 the level follows your playing."),
        callout("note", "The master <b>Volume</b> (top bar) is separate and comes after the effects. Its curve is volume squared (times 2), so 0.7 is close to unity gain and 1.0 is about +6 dB. "
                        "A soft safety limiter smooths peaks above about 0.95 (full scale)."),
    ]
    return st


def ch10():
    st = [Banner(10, "Master Effects", "EQ, distortion, chorus, delay and reverb")]
    st += [
        P("All voices are summed and sent through five stereo effects, always in this order, and finally through the master Volume. Each effect is bypassed when its Mix is 0 "
          "(the EQ when all three gains are about 0 dB), so unused effects cost no CPU."),
        fx_chain_diagram(D.FW),
        cap("Figure 10.1: Voice processing happens per note; the master effects process the summed stereo signal."),
        P("A DC blocker runs ahead of the EQ to remove any constant offset (for example from the Rectify insert). "
          "The effects are controlled in the <b>FX</b> panel on the right of the synth row, with five tabs."),
        H2("10.1  EQ"),
        P("A three-band equaliser: a low shelf, one fully parametric mid band and a high shelf."),
        tbl([["Control", "Range", "Default"],
             ["Lo Gain / Lo Freq", "-18 to +18 dB / 40 to 400 Hz", "0 dB / 120 Hz"],
             ["Mid Gain / Mid Freq / Mid Q", "-18 to +18 dB / 200 Hz to 8 kHz / 0.3 to 6", "0 dB / 1000 Hz / 1.0"],
             ["Hi Gain / Hi Freq", "-18 to +18 dB / 2 to 16 kHz", "0 dB / 6000 Hz"]],
            [2, 2.6, 1.4], first_bold=True),
        P("Modulatable: Lo Gain, Mid Gain, Mid Freq and Hi Gain (by macros, mod wheel, aftertouch or pitch bend)."),
        H2("10.2  Distortion"),
        P("<b>Dist</b> tab: <b>Drive</b> (0 to 1, default 0.3) is a tanh saturator with gain from 1x to 13x; <b>Mix</b> (0 to 1, default 0 = off) blends it with the dry signal. "
          "Because it comes after the EQ and before chorus, delay and reverb, it distorts the whole mix but not the effects tails."),
        H2("10.3  Chorus"),
        P("<b>Chor</b> tab: a stereo chorus with two short modulated delay lines (left and right a quarter cycle apart). <b>Rate</b> 0.05 to 8 Hz (default 0.6), <b>Depth</b> 0 to 1 (default 0.5), <b>Mix</b> 0 to 1 (default 0). "
          "Good for width on pads and basses."),
        H2("10.4  Delay"),
        P("<b>Delay</b> tab: a stereo delay with the left and right feedback paths crossed, and a low-pass in the feedback loop so repeats get darker."),
        tbl([["Control", "Range", "Default", "Notes"],
             ["Time", "1 to 2000 ms", "350 ms", "Skewed: 300 ms at mid-travel. Changes glide rather than click."],
             ["Sync", "on / off", "off", "When on, the delay time follows the host tempo and <b>Division</b>."],
             ["Division", "1/1, 1/2, 1/4, 1/8, 1/16, 1/32, 1/4T, 1/8T, 1/16T", "1/8", "Only used with Sync on. (T = triplet.)"],
             ["Feedback", "0 to 0.95", "0.35", "Modulatable."],
             ["Mix", "0 to 1", "0", "Wet level added on top of the dry signal. Modulatable."]],
            [0.8, 2.3, 0.8, 1.9], first_bold=True),
        P("At 120 BPM (also used when the host gives no tempo, as in the standalone app) a 1/8 note delay is 250 ms. The longest delay is about 2 seconds; at tempos slower than 120 BPM the longest divisions are limited to that."),
        H2("10.5  Reverb"),
        P("<b>Verb</b> tab: a stereo algorithmic reverb. <b>Size</b> (0 to 1, default 0.5) sets room size and decay, <b>Damping</b> (0 to 1, default 0.5) removes highs from the tail, <b>Mix</b> (0 to 1, default 0) is the amount. "
          "Mix raises the wet level and slightly lowers the dry. The plug-in reports a 4 second tail to the host."),
        H2("10.6  Master Volume and safety"),
        P("<b>Volume</b> (top bar, default 0.7) is the last stage, followed by a soft clip near full scale to keep stray peaks tidy. Volume is a modulation target for macros, mod wheel and aftertouch."),
        callout("note", "Voice modulators (envelopes, LFOs, Performers, Velocity, Key Track, Random) are different for every note, so they cannot control these shared master effects. "
                        "Use <b>macros, the mod wheel, aftertouch or pitch bend</b> to modulate effect parameters (chapter 11)."),
    ]
    return st


def build():
    return [ch6(), ch7(), ch8(), ch9(), ch10()]
