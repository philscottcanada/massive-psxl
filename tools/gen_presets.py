#!/usr/bin/env python
"""Generates Resources/presets/factory_presets.xml - the original Massive PSXL factory library.

Every preset is written from scratch (none are converted from any other product). Each one lists only
the parameters that differ from the plug-in defaults; the loader resets everything else first.

Run:  python tools/gen_presets.py
"""
import os
from xml.sax.saxutils import quoteattr

OUT = os.path.join(os.path.dirname(__file__), "..", "Resources", "presets", "factory_presets.xml")

# ---- node / source ids (must match Params.h) ----------------------------------------------------
OSC1, OSC2, NOISE, F1, F2, INS = 0, 1, 2, 3, 4, 5
TO_F1, TO_F2, TO_INS, TO_OUT = 0, 1, 2, 3
AMP = 0
def MOD(s): return s - 1            # modulator slot 1..9
def PERF(p): return 9 + p - 1       # performer 1..3
def MACRO(i): return 12 + i         # macro 0..15
VEL, KEY, RND, MW, AT, PB = 28, 29, 30, 31, 32, 33

FRIENDLY = {
    "o1_pos": "Osc 1 Position", "o1_pitch": "Osc 1 Pitch", "o1_fine": "Osc 1 Fine", "o1_level": "Osc 1 Level", "o1_detune": "Osc 1 Detune",
    "o1_pm": "Osc 1 Phase Mod", "o1_fold": "Osc 1 Fold", "o2_pos": "Osc 2 Position", "o2_pitch": "Osc 2 Pitch", "o2_fine": "Osc 2 Fine",
    "o2_level": "Osc 2 Level", "o2_detune": "Osc 2 Detune", "o2_pm": "Osc 2 Phase Mod", "o2_fold": "Osc 2 Fold",
    "n_level": "Noise Level", "n_color": "Noise Color", "f1_cut": "Filter 1 Cutoff", "f1_res": "Filter 1 Reso", "f1_drive": "Filter 1 Drive",
    "f2_cut": "Filter 2 Cutoff", "f2_res": "Filter 2 Reso", "f2_drive": "Filter 2 Drive", "ins_drive": "Insert Drive", "ins_mix": "Insert Mix",
    "amp_level": "Amp Level", "amp_pan": "Amp Pan", "amp_fb": "Amp Feedback", "pitch": "Pitch", "master_vol": "Volume",
    "eq_lo_g": "EQ Low Gain", "eq_mid_f": "EQ Mid Freq", "eq_mid_g": "EQ Mid Gain", "eq_hi_g": "EQ High Gain",
    "dly_fb": "Delay Feedback", "dly_mix": "Delay Mix", "rev_size": "Reverb Size", "rev_mix": "Reverb Mix",
    "cho_rate": "Chorus Rate", "cho_depth": "Chorus Depth", "cho_mix": "Chorus Mix", "dist_drive": "Dist Drive", "dist_mix": "Dist Mix",
}

# wavetable slots
BASIC, PULSE, TILT, VOWEL, SYNC, BELLS, ORGAN, GLASS, GRIT, FOLD = range(10)
# filter models
LADDER, SVF, COMB, FORMANT = range(4)

PRESETS = []   # (category, xml-string)


def envp(slot, att=None, dec=None, sus=None, rel=None, dly=None, hold=None, level=None, oneshot=None):
    d = {}
    for k, v in (("att", att), ("dec", dec), ("sus", sus), ("rel", rel), ("dly", dly), ("hold", hold), ("level", level), ("oneshot", oneshot)):
        if v is not None:
            d["m%d_%s" % (slot, k)] = v
    if slot > 1:
        d["m%d_type" % slot] = 0
    return d


def lfop(slot, rate=2.0, shape=0, sync=False, div=3, bipolar=True, phase=None, fade=None, level=1.0):
    d = {"m%d_type" % slot: 1, "m%d_shape" % slot: shape, "m%d_level" % slot: level, "m%d_bipolar" % slot: 1 if bipolar else 0}
    if sync:
        d["m%d_sync" % slot] = 1; d["m%d_div" % slot] = div
    else:
        d["m%d_rate" % slot] = rate
    if phase is not None: d["m%d_phase" % slot] = phase
    if fade is not None: d["m%d_fade" % slot] = fade
    return d


def emit(name, cat, params, routes, assigns, perf, macro_names, macro_values):
    lines = ['  <PSXL name=%s category=%s author="Phil S Audio" version="1">' % (quoteattr(name), quoteattr(cat))]
    for k, v in sorted(params.items()):
        lines.append('    <P id=%s v="%s"/>' % (quoteattr(k), repr(float(v))))
    for (s, d, g) in routes:
        lines.append('    <ROUTE src="%d" dst="%d" gain="%s"/>' % (s, d, g))
    for (s, dest, amt) in assigns:
        lines.append('    <ASSIGN src="%d" dest=%s amount="%s"/>' % (s, quoteattr(dest), amt))
    for i in sorted(macro_names):
        lines.append('    <MACRO i="%d" name=%s user="0"/>' % (i, quoteattr(macro_names[i])))
    for p, steps in sorted(perf.items()):
        lines.append('    <PERF i="%d" steps="%s"/>' % (p - 1, ",".join("%.3f" % s for s in steps)))
    for i, v in sorted(macro_values.items()):
        lines.append('    <P id="macro%d" v="%s"/>' % (i + 1, v))
    lines.append("  </PSXL>")
    PRESETS.append((cat, "\n".join(lines)))


DEFAULT_MACROS = [(0, "f1_cut", 0.35), (1, "f1_res", 0.30), (2, "o1_pos", 0.45), (3, "rev_mix", 0.40)]


def voice(name, cat, *, wt1=BASIC, pos1=0.0, pitch1=0, fine1=0, uni1=1, det1=15, lvl1=0.8,
          wt2=None, pos2=0.0, pitch2=0, fine2=0, uni2=1, det2=15, lvl2=0.6,
          model=LADDER, mode=0, cut=8000, res=0.2, fdrive=0, ktr=0.0,
          noise=0.0, ntype=0, ncolor=0.5,
          amp=(0.005, 0.4, 0.8, 0.25), fenv=None, fx=None, vmode=0, glide=0.0, voices=8,
          lfo=None, assigns=None, extra=None, routes=None, perf=None, macros="default", oneshot=False,
          f2=None, ins=None, vel_sens=0.5):
    p = {"o1_wt": wt1, "o1_pos": pos1, "o1_pitch": pitch1, "o1_fine": fine1, "o1_uni": uni1, "o1_detune": det1, "o1_level": lvl1,
         "f1_model": model, "f1_mode": mode, "f1_cut": cut, "f1_res": res, "f1_drive": fdrive, "f1_ktr": ktr,
         "voice_mode": vmode, "glide": glide, "voices": voices, "vel_sens": vel_sens}
    r = [(OSC1, TO_F1, 1.0)]
    if wt2 is not None:
        p.update({"o2_wt": wt2, "o2_pos": pos2, "o2_pitch": pitch2, "o2_fine": fine2, "o2_uni": uni2, "o2_detune": det2, "o2_level": lvl2})
        r.append((OSC2, TO_F1, 1.0))
    if noise > 0:
        p.update({"n_level": noise, "n_type": ntype, "n_color": ncolor}); r.append((NOISE, TO_F1, 1.0))
    r.append((F1, TO_OUT, 1.0))
    if f2:   # second filter in series: dict of params
        p.update(f2); r = [x for x in r if x[:2] != (F1, TO_OUT)] + [(F1, TO_F2, 1.0), (F2, TO_OUT, 1.0)]
    if ins:  # insert in series before the output
        p.update(ins); last = F2 if f2 else F1
        r = [x for x in r if x[:2] != (last, TO_OUT)] + [(last, TO_INS, 1.0), (INS, TO_OUT, 1.0)]
    if routes is not None:
        r = routes
    p.update(envp(1, *amp))
    a = []
    if fenv:
        amount, fa, fd, fs, fr = fenv
        p.update(envp(2, fa, fd, fs, fr)); a.append((MOD(2), "f1_cut", amount))
    if lfo:
        p.update(lfo["params"]); a.extend(lfo["assigns"])
    if fx: p.update(fx)
    if extra: p.update(extra)
    if assigns: a.extend(assigns)
    names, values = {}, {}
    if macros == "default":
        for (i, dest, amt) in DEFAULT_MACROS:
            a.append((MACRO(i), dest, amt)); names[i] = FRIENDLY[dest]; values[i] = 0.0 if dest != "o1_pos" else 0.0
    elif macros:
        for (i, dest, amt) in macros:
            a.append((MACRO(i), dest, amt)); names[i] = FRIENDLY[dest]; values[i] = 0.0
    emit(name, cat, p, r, a, perf or {}, names, values)


def lfo_on(slot, dest, amount, **kw):
    return {"params": lfop(slot, **kw), "assigns": [(MOD(slot), dest, amount)]}


def lfo_multi(slot, targets, **kw):
    return {"params": lfop(slot, **kw), "assigns": [(MOD(slot), d, a) for d, a in targets]}


# ==================================================================================================
# BASS
# ==================================================================================================
B = "Bass"
voice("Sub Pillar", B, wt1=BASIC, pos1=0.0, cut=380, res=0.1, wt2=BASIC, pitch2=-12, lvl2=0.5, amp=(0.004, 0.3, 0.95, 0.18))
voice("Deep Weight", B, wt1=BASIC, pos1=0.12, cut=300, res=0.15, wt2=BASIC, pitch2=-12, lvl2=0.7, ins=dict(ins_type=0, ins_drive=0.35, ins_mix=0.6), amp=(0.004, 0.3, 0.95, 0.2))
voice("Analog Growl", B, wt1=BASIC, pos1=0.66, uni1=3, det1=12, cut=700, res=0.32, fdrive=0.3, fenv=(0.22, 0.003, 0.25, 0.25, 0.2), amp=(0.003, 0.3, 0.85, 0.15))
voice("Wobble Machine", B, wt1=BASIC, pos1=0.66, uni1=3, det1=10, cut=520, res=0.5, fdrive=0.2, lfo=lfo_on(2, "f1_cut", 0.34, sync=True, div=3, shape=0), amp=(0.003, 0.3, 0.9, 0.15))
voice("Dub Wobble", B, wt1=BASIC, pos1=0.4, cut=450, res=0.55, lfo=lfo_on(2, "f1_cut", 0.4, sync=True, div=2, shape=1), amp=(0.003, 0.3, 0.9, 0.2), fx=dict(dly_mix=0.25, dly_fb=0.45, dly_sync=1, dly_div=3))
voice("Reese Beast", B, wt1=BASIC, pos1=0.66, uni1=4, det1=24, wt2=BASIC, pos2=0.66, fine2=9, uni2=4, det2=20, cut=1000, res=0.2, lfo=lfo_on(2, "f1_cut", 0.12, rate=0.3, shape=1), amp=(0.01, 0.4, 0.9, 0.3), fx=dict(cho_mix=0.25))
voice("FM Growler", B, wt1=BELLS, pos1=0.55, cut=1500, res=0.2, lfo=lfo_on(2, "o1_pos", 0.2, sync=True, div=3, shape=1), amp=(0.003, 0.3, 0.85, 0.15))
voice("Pulse Punch", B, wt1=PULSE, pos1=0.3, cut=1400, res=0.25, fenv=(0.3, 0.002, 0.18, 0.1, 0.12), amp=(0.002, 0.25, 0.7, 0.12))
voice("Acid Line", B, wt1=BASIC, pos1=0.66, cut=560, res=0.72, fdrive=0.35, vmode=2, glide=0.07, fenv=(0.34, 0.002, 0.2, 0.0, 0.15), amp=(0.002, 0.25, 0.85, 0.1))
voice("Rubber Band", B, wt1=SYNC, pos1=0.4, cut=700, res=0.42, vmode=1, glide=0.05, fenv=(0.25, 0.003, 0.3, 0.15, 0.18), amp=(0.003, 0.3, 0.8, 0.12))
voice("Grit Bass", B, wt1=GRIT, pos1=0.3, uni1=2, det1=8, cut=1100, res=0.3, ins=dict(ins_type=1, ins_drive=0.4, ins_mix=0.5), amp=(0.003, 0.3, 0.85, 0.15))
voice("Fold Sub", B, wt1=FOLD, pos1=0.2, cut=520, res=0.2, lfo=lfo_on(2, "o1_pos", 0.18, rate=0.5, shape=1), amp=(0.004, 0.3, 0.95, 0.2))
voice("Distorted Saw", B, wt1=BASIC, pos1=0.7, uni1=3, det1=14, cut=2000, res=0.2, ins=dict(ins_type=3, ins_drive=0.6, ins_mix=0.7), amp=(0.003, 0.3, 0.9, 0.15))
voice("Talking Bass", B, wt1=BASIC, pos1=0.66, model=FORMANT, mode=0, cut=700, res=0.55, lfo=lfo_on(2, "f1_cut", 0.22, sync=True, div=2, shape=1), amp=(0.003, 0.3, 0.9, 0.15))
voice("Mono Lead Bass", B, wt1=BASIC, pos1=0.9, uni1=2, det1=10, cut=2600, res=0.25, vmode=1, glide=0.04, amp=(0.003, 0.3, 0.9, 0.12))
voice("Electro Pluck Bass", B, wt1=BASIC, pos1=0.55, cut=450, res=0.35, fenv=(0.4, 0.001, 0.14, 0.0, 0.1), amp=(0.001, 0.22, 0.0, 0.1))
voice("Bit Bass", B, wt1=BASIC, pos1=0.7, cut=3000, res=0.15, ins=dict(ins_type=2, ins_drive=0.55, ins_mix=0.8), amp=(0.003, 0.3, 0.9, 0.15))
voice("Detuned Square Bass", B, wt1=PULSE, pos1=0.0, uni1=4, det1=18, cut=900, res=0.2, amp=(0.004, 0.3, 0.9, 0.2), fx=dict(cho_mix=0.2))
voice("Dark Rumble", B, wt1=TILT, pos1=0.2, cut=240, res=0.3, wt2=BASIC, pitch2=-12, lvl2=0.6, amp=(0.02, 0.5, 0.9, 0.5), fx=dict(rev_mix=0.2, rev_size=0.7))
voice("Sweep Machine", B, wt1=BASIC, pos1=0.66, uni1=2, cut=250, res=0.45, amp=(0.005, 0.3, 0.9, 0.2), macros=[(0, "f1_cut", 0.6), (1, "f1_res", 0.4), (2, "o1_pos", 0.5), (3, "ins_drive", 0.4)],
      ins=dict(ins_type=0, ins_drive=0.2, ins_mix=0.5))

# ==================================================================================================
# LEADS
# ==================================================================================================
L = "Leads"
voice("Classic Saw Lead", L, wt1=BASIC, pos1=0.66, uni1=3, det1=14, cut=5000, res=0.18, amp=(0.004, 0.3, 0.85, 0.3), vmode=1, glide=0.03, fx=dict(dly_mix=0.2, dly_fb=0.35, dly_sync=1, dly_div=3, rev_mix=0.15))
voice("Super Stack", L, wt1=BASIC, pos1=0.66, uni1=8, det1=34, cut=7000, res=0.15, amp=(0.006, 0.3, 0.85, 0.35), fx=dict(cho_mix=0.25, rev_mix=0.2, rev_size=0.6))
voice("Square Lead", L, wt1=PULSE, pos1=0.0, uni1=2, det1=8, cut=4200, res=0.2, vmode=1, glide=0.05, lfo=lfo_on(2, "pitch", 0.003, rate=5.5, shape=0, fade=0.5), amp=(0.005, 0.3, 0.85, 0.25))
voice("PWM Dreamer", L, wt1=PULSE, pos1=0.2, uni1=3, det1=10, cut=5000, res=0.15, lfo=lfo_on(2, "o1_pos", 0.45, rate=0.6, shape=1), amp=(0.01, 0.3, 0.85, 0.4), fx=dict(cho_mix=0.3, rev_mix=0.2))
voice("Sync Screamer", L, wt1=SYNC, pos1=0.3, cut=7500, res=0.2, vmode=1, glide=0.04, lfo=lfo_on(2, "o1_pos", 0.4, rate=0.4, shape=1), amp=(0.003, 0.3, 0.85, 0.2), fenv=(0.0, 0.01, 0.3, 0.5, 0.2))
voice("Expressive Lead", L, wt1=BASIC, pos1=0.5, uni1=2, det1=10, cut=2500, res=0.25, vmode=1, glide=0.06,
      assigns=[(MW, "o1_pos", 0.4), (MW, "f1_cut", 0.25), (AT, "f1_cut", 0.15)], lfo=lfo_on(2, "pitch", 0.003, rate=5.2, shape=0, fade=0.6), amp=(0.01, 0.3, 0.9, 0.3))
voice("FM Lead", L, wt1=BELLS, pos1=0.35, cut=9000, res=0.1, vmode=1, glide=0.03, lfo=lfo_on(2, "o1_pos", 0.3, rate=0.8, shape=1), amp=(0.003, 0.3, 0.8, 0.25), fx=dict(dly_mix=0.2, dly_sync=1, dly_div=3, rev_mix=0.15))
voice("Glass Lead", L, wt1=GLASS, pos1=0.3, uni1=3, det1=9, cut=9000, res=0.12, amp=(0.01, 0.4, 0.85, 0.45), fx=dict(rev_mix=0.3, rev_size=0.7, dly_mix=0.15, dly_sync=1, dly_div=3))
voice("Vowel Lead", L, wt1=VOWEL, pos1=0.1, cut=8000, res=0.1, lfo=lfo_on(2, "o1_pos", 0.7, rate=0.35, shape=1), amp=(0.02, 0.4, 0.85, 0.4), fx=dict(rev_mix=0.25))
voice("Mono Acid Lead", L, wt1=BASIC, pos1=0.66, cut=1800, res=0.6, fdrive=0.3, vmode=2, glide=0.08, fenv=(0.3, 0.002, 0.25, 0.3, 0.15), amp=(0.003, 0.3, 0.85, 0.12))
voice("Detuned Trance", L, wt1=BASIC, pos1=0.66, uni1=7, det1=28, wt2=BASIC, pos2=0.66, pitch2=12, uni2=3, det2=14, lvl2=0.35, cut=8500, res=0.1, amp=(0.004, 0.4, 0.8, 0.35), fx=dict(dly_mix=0.3, dly_fb=0.4, dly_sync=1, dly_div=3, rev_mix=0.25, rev_size=0.7))
voice("Retro Poly Lead", L, wt1=BASIC, pos1=0.66, uni1=2, det1=8, cut=3200, res=0.22, fenv=(0.2, 0.02, 0.4, 0.4, 0.3), amp=(0.01, 0.4, 0.8, 0.35), fx=dict(cho_mix=0.35))
voice("Whistle", L, wt1=BASIC, pos1=0.0, cut=9000, res=0.0, vmode=1, glide=0.08, lfo=lfo_on(2, "pitch", 0.004, rate=5.0, shape=0, fade=0.8), amp=(0.08, 0.3, 0.9, 0.3), fx=dict(rev_mix=0.25))
voice("Hoover Lead", L, wt1=SYNC, pos1=0.6, uni1=6, det1=40, cut=6000, res=0.25, vmode=1, glide=0.12, fx=dict(cho_mix=0.3, rev_mix=0.2), amp=(0.01, 0.3, 0.9, 0.3))
voice("Bright Pluck Lead", L, wt1=BASIC, pos1=0.66, uni1=3, det1=12, cut=3000, res=0.25, fenv=(0.35, 0.002, 0.3, 0.2, 0.2), amp=(0.002, 0.5, 0.6, 0.3), fx=dict(dly_mix=0.25, dly_sync=1, dly_div=3, rev_mix=0.2))
voice("Digital Edge", L, wt1=GRIT, pos1=0.2, uni1=2, cut=9000, res=0.15, vmode=1, glide=0.03, lfo=lfo_on(2, "o1_pos", 0.6, rate=0.7, shape=1), amp=(0.003, 0.3, 0.85, 0.2))
voice("Fold Lead", L, wt1=FOLD, pos1=0.3, cut=9000, res=0.1, vmode=1, glide=0.05, assigns=[(MW, "o1_pos", 0.5), (VEL, "o1_fold", 0.3)], amp=(0.004, 0.3, 0.85, 0.25), fx=dict(dly_mix=0.2, dly_sync=1, dly_div=3))
voice("Cinematic Brass Lead", L, wt1=BASIC, pos1=0.66, uni1=4, det1=14, cut=1200, res=0.15, fenv=(0.3, 0.12, 0.4, 0.6, 0.3), amp=(0.1, 0.4, 0.9, 0.35), fx=dict(rev_mix=0.3, rev_size=0.75))
voice("Theremin", L, wt1=BASIC, pos1=0.0, cut=6000, res=0.05, vmode=2, glide=0.18, lfo=lfo_on(2, "pitch", 0.004, rate=5.6, shape=0, fade=1.0), amp=(0.12, 0.3, 0.9, 0.4), fx=dict(rev_mix=0.3))

# ==================================================================================================
# PADS
# ==================================================================================================
P = "Pads"
slow = (0.8, 0.6, 0.85, 1.6)
voice("Warm Strings", P, wt1=BASIC, pos1=0.66, uni1=6, det1=22, cut=2400, res=0.1, amp=slow, fx=dict(cho_mix=0.35, rev_mix=0.3, rev_size=0.75))
voice("Glass Pad", P, wt1=GLASS, pos1=0.25, uni1=4, det1=14, cut=9000, res=0.1, lfo=lfo_on(2, "o1_pos", 0.35, rate=0.12, shape=1), amp=slow, fx=dict(rev_mix=0.4, rev_size=0.85, cho_mix=0.2))
voice("Evolving Vowels", P, wt1=VOWEL, pos1=0.0, uni1=3, det1=12, cut=9000, res=0.1, lfo=lfo_on(2, "o1_pos", 0.8, rate=0.07, shape=1), amp=slow, fx=dict(rev_mix=0.4, rev_size=0.8))
voice("Dark Ambience", P, wt1=TILT, pos1=0.15, uni1=4, det1=16, cut=900, res=0.2, lfo=lfo_on(2, "f1_cut", 0.15, rate=0.09, shape=1), amp=(1.2, 0.8, 0.9, 2.5), fx=dict(rev_mix=0.5, rev_size=0.9))
voice("Choir Dream", P, wt1=VOWEL, pos1=0.3, uni1=5, det1=14, cut=7000, res=0.15, amp=slow, lfo=lfo_on(2, "o1_pos", 0.12, rate=0.2, shape=1), fx=dict(rev_mix=0.45, rev_size=0.85))
voice("Analog Poly Pad", P, wt1=PULSE, pos1=0.25, uni1=3, det1=10, cut=1800, res=0.2, lfo=lfo_on(2, "o1_pos", 0.4, rate=0.4, shape=1), fenv=(0.2, 0.3, 0.6, 0.6, 0.8), amp=(0.3, 0.5, 0.85, 1.0), fx=dict(cho_mix=0.4, rev_mix=0.2))
voice("Cathedral Organ Pad", P, wt1=ORGAN, pos1=0.4, uni1=2, det1=6, cut=6000, res=0.1, amp=(0.2, 0.5, 0.95, 1.2), fx=dict(rev_mix=0.5, rev_size=0.9, cho_mix=0.2))
voice("Frozen Bells Pad", P, wt1=BELLS, pos1=0.2, uni1=3, det1=10, cut=9000, res=0.1, lfo=lfo_on(2, "o1_pos", 0.3, rate=0.1, shape=1), amp=(0.6, 0.8, 0.8, 2.0), fx=dict(rev_mix=0.5, rev_size=0.9, dly_mix=0.25, dly_sync=1, dly_div=3))
voice("Sunrise", P, wt1=BASIC, pos1=0.5, uni1=6, det1=20, cut=1500, res=0.1, fenv=(0.35, 1.5, 1.0, 0.8, 1.5), amp=(1.5, 0.8, 0.9, 2.0), fx=dict(cho_mix=0.3, rev_mix=0.4, rev_size=0.8))
voice("Wide Saw Wash", P, wt1=BASIC, pos1=0.66, uni1=8, det1=38, cut=3500, res=0.1, amp=(0.5, 0.5, 0.9, 1.4), fx=dict(cho_mix=0.45, rev_mix=0.35, rev_size=0.8))
voice("Hollow Reed", P, wt1=PULSE, pos1=0.4, uni1=2, det1=8, cut=2200, res=0.3, lfo=lfo_on(2, "o1_pos", 0.2, rate=0.25, shape=1), amp=(0.25, 0.5, 0.85, 0.9), fx=dict(rev_mix=0.3))
voice("Shimmer Wash", P, wt1=GLASS, pos1=0.5, uni1=5, det1=18, cut=9500, res=0.05, amp=slow, fx=dict(rev_mix=0.55, rev_size=0.95, dly_mix=0.2, dly_sync=1, dly_div=2, cho_mix=0.3))
voice("Soft Piano Pad", P, wt1=TILT, pos1=0.4, uni1=2, det1=6, cut=3000, res=0.1, fenv=(0.25, 0.01, 0.8, 0.3, 1.0), amp=(0.01, 1.2, 0.6, 1.4), fx=dict(rev_mix=0.35, rev_size=0.8))
voice("Motion Pad", P, wt1=BASIC, pos1=0.66, uni1=5, det1=18, cut=1400, res=0.3, lfo=lfo_multi(2, [("f1_cut", 0.25), ("o1_pos", 0.15)], sync=True, div=0, shape=1), amp=(0.6, 0.5, 0.9, 1.2), fx=dict(rev_mix=0.35, cho_mix=0.25))
voice("Dust Drift", P, wt1=GRIT, pos1=0.3, uni1=4, det1=16, cut=2500, res=0.15, noise=0.08, ncolor=0.7, lfo=lfo_on(2, "o1_pos", 0.4, rate=0.08, shape=6), amp=(1.0, 0.6, 0.9, 2.0), fx=dict(rev_mix=0.45, rev_size=0.85))
voice("Orbit", P, wt1=SYNC, pos1=0.2, uni1=3, det1=12, cut=4500, res=0.15, lfo=lfo_on(2, "o1_pos", 0.5, rate=0.15, shape=1), amp=slow, fx=dict(rev_mix=0.4, dly_mix=0.2, dly_sync=1, dly_div=3))
voice("Aurora", P, wt1=VOWEL, pos1=0.6, uni1=6, det1=20, cut=8000, res=0.1, lfo=lfo_multi(2, [("o1_pos", 0.3), ("f1_cut", 0.1)], rate=0.06, shape=6), amp=(1.4, 0.8, 0.9, 2.5), fx=dict(rev_mix=0.55, rev_size=0.95, cho_mix=0.3))
voice("Velvet", P, wt1=BASIC, pos1=0.3, uni1=4, det1=14, cut=1100, res=0.1, amp=(0.7, 0.6, 0.9, 1.4), fx=dict(cho_mix=0.3, rev_mix=0.35))
voice("Cold Fusion", P, wt1=FOLD, pos1=0.3, uni1=3, det1=12, cut=5000, res=0.1, lfo=lfo_on(2, "o1_pos", 0.35, rate=0.1, shape=1), amp=slow, fx=dict(rev_mix=0.45, rev_size=0.85, cho_mix=0.2))
voice("Breathing Pad", P, wt1=BASIC, pos1=0.5, uni1=4, det1=14, cut=1600, res=0.2, lfo=lfo_on(2, "f1_cut", 0.25, rate=0.2, shape=0), amp=slow, fx=dict(rev_mix=0.4, cho_mix=0.3))

# ==================================================================================================
# PLUCKS
# ==================================================================================================
K = "Plucks"
def pluck(name, **kw):
    base = dict(wt1=BASIC, pos1=0.66, cut=700, res=0.2, fenv=(0.4, 0.001, 0.25, 0.0, 0.2), amp=(0.001, 0.45, 0.0, 0.25),
                fx=dict(rev_mix=0.2, dly_mix=0.15, dly_sync=1, dly_div=3), oneshot=True)
    base.update(kw)
    base.pop("oneshot", None)
    voice(name, K, **base)
pluck("Classic Pluck")
pluck("Soft Pluck", pos1=0.3, cut=600, fenv=(0.3, 0.001, 0.3, 0.0, 0.2))
pluck("Bell Pluck", wt1=BELLS, pos1=0.4, cut=6000, fenv=(0.1, 0.001, 0.4, 0.0, 0.3), amp=(0.001, 0.9, 0.0, 0.5))
pluck("Glass Pluck", wt1=GLASS, pos1=0.35, cut=7000, fenv=(0.15, 0.001, 0.3, 0.0, 0.3), amp=(0.001, 0.8, 0.0, 0.5))
pluck("Pulse Pluck", wt1=PULSE, pos1=0.25, cut=1200)
pluck("Detuned Pluck", uni1=4, det1=16, cut=900)
pluck("Marimba", wt1=BASIC, pos1=0.0, cut=2500, res=0.1, fenv=(0.3, 0.001, 0.12, 0.0, 0.1), amp=(0.001, 0.35, 0.0, 0.2), wt2=BELLS, pos2=0.2, pitch2=24, lvl2=0.15)
pluck("Kalimba", wt1=BASIC, pos1=0.0, wt2=BELLS, pos2=0.3, pitch2=19, lvl2=0.2, cut=3500, res=0.1, amp=(0.001, 0.6, 0.0, 0.4))
pluck("Harp-ish", wt1=TILT, pos1=0.6, cut=2200, res=0.1, amp=(0.001, 0.9, 0.0, 0.5), fenv=(0.2, 0.001, 0.4, 0.0, 0.3))
pluck("Wood Block", wt1=BASIC, pos1=0.0, pitch1=12, cut=1800, res=0.3, amp=(0.001, 0.07, 0.0, 0.05), fenv=(0.3, 0.001, 0.05, 0.0, 0.05))
pluck("EDM Stab", wt1=BASIC, pos1=0.66, uni1=6, det1=26, cut=2000, res=0.25, amp=(0.001, 0.28, 0.0, 0.2), fenv=(0.35, 0.001, 0.25, 0.0, 0.2), fx=dict(rev_mix=0.25, dly_mix=0.2, dly_sync=1, dly_div=3))
pluck("Pizzicato", wt1=BASIC, pos1=0.5, cut=900, res=0.15, amp=(0.001, 0.2, 0.0, 0.1), fenv=(0.4, 0.001, 0.12, 0.0, 0.1))
pluck("Steel Drum", wt1=BELLS, pos1=0.25, pitch1=0, cut=5000, amp=(0.001, 0.7, 0.0, 0.4), lfo=lfo_on(2, "o1_pos", 0.15, rate=5, shape=0))
pluck("Koto", wt1=TILT, pos1=0.5, wt2=PULSE, pos2=0.3, pitch2=12, lvl2=0.25, cut=2600, res=0.15, amp=(0.001, 0.8, 0.0, 0.4), fenv=(0.2, 0.001, 0.3, 0.0, 0.2))
pluck("Synth Strum", wt1=BASIC, pos1=0.66, uni1=3, det1=14, cut=1500, amp=(0.001, 0.6, 0.0, 0.4), fx=dict(rev_mix=0.3, cho_mix=0.25))

# ==================================================================================================
# KEYS
# ==================================================================================================
Y = "Keys"
voice("Warm E-Piano", Y, wt1=BELLS, pos1=0.12, cut=3500, res=0.1, amp=(0.002, 1.2, 0.0, 0.5), fenv=(0.15, 0.001, 0.5, 0.2, 0.3), extra=dict(vel_sens=0.9), fx=dict(cho_mix=0.3, rev_mix=0.2), assigns=[(VEL, "o1_pos", 0.2)])
voice("Tine Keys", Y, wt1=BELLS, pos1=0.3, cut=5000, res=0.1, amp=(0.002, 1.0, 0.0, 0.5), assigns=[(VEL, "o1_pos", 0.3)], fx=dict(cho_mix=0.25, rev_mix=0.2))
voice("Drawbar Organ", Y, wt1=ORGAN, pos1=0.3, cut=9000, res=0.0, amp=(0.003, 0.2, 1.0, 0.08), fx=dict(cho_mix=0.3, rev_mix=0.15, dist_mix=0.15, dist_drive=0.3))
voice("Rock Organ", Y, wt1=ORGAN, pos1=0.7, cut=9000, res=0.0, amp=(0.003, 0.2, 1.0, 0.08), fx=dict(dist_mix=0.4, dist_drive=0.5, cho_mix=0.2))
voice("Clav Funk", Y, wt1=PULSE, pos1=0.35, cut=1500, res=0.35, fenv=(0.35, 0.001, 0.12, 0.0, 0.1), amp=(0.001, 0.3, 0.0, 0.08))
voice("Soft Rhodes", Y, wt1=BELLS, pos1=0.08, cut=2800, res=0.05, amp=(0.003, 1.5, 0.0, 0.6), fx=dict(cho_mix=0.35, rev_mix=0.25), assigns=[(VEL, "f1_cut", 0.2)])
voice("Wurly Bite", Y, wt1=BELLS, pos1=0.18, cut=3200, res=0.1, ins=dict(ins_type=0, ins_drive=0.3, ins_mix=0.4), amp=(0.002, 1.0, 0.0, 0.4))
voice("Digital Piano", Y, wt1=TILT, pos1=0.55, cut=5000, res=0.05, amp=(0.001, 1.8, 0.0, 0.7), fenv=(0.2, 0.001, 0.6, 0.2, 0.3), fx=dict(rev_mix=0.25, rev_size=0.6))
voice("Vox Keys", Y, wt1=VOWEL, pos1=0.35, cut=8000, res=0.1, amp=(0.02, 0.5, 0.9, 0.5), fx=dict(rev_mix=0.3, cho_mix=0.2))
voice("Glass Keys", Y, wt1=GLASS, pos1=0.4, cut=9000, res=0.05, amp=(0.002, 1.0, 0.1, 0.8), fx=dict(rev_mix=0.3, cho_mix=0.2))

# ==================================================================================================
# DRUMS  (play these around C1 - C3; the amp envelope is one-shot so notes ring out)
# ==================================================================================================
D = "Drums"
def drum(name, p, routes, assigns=(), amp=(0.001, 0.3, 0.0, 0.1), extra=None, perf=None):
    q = dict(p)
    q.update(envp(1, *amp, oneshot=1))
    if extra: q.update(extra)
    emit(name, D, q, routes, list(assigns), perf or {}, {}, {})

def kick(name, base_pitch, sweep, decay, click=0.0, drive=0.0, wt=BASIC):
    p = {"o1_wt": wt, "o1_pos": 0.0, "o1_pitch": base_pitch, "o1_level": 0.95, "f1_cut": 9000, "f1_res": 0.05, "n_level": click, "n_type": 0, "n_color": 0.85,
         "ins_type": 0, "ins_drive": drive, "ins_mix": 1.0 if drive > 0 else 0.0}
    p.update(envp(2, 0.0005, 0.07 + decay * 0.15, 0.0, 0.05, oneshot=1))
    r = [(OSC1, TO_F1, 1.0), (F1, TO_INS, 1.0), (INS, TO_OUT, 1.0)]
    if click > 0: r.append((NOISE, TO_INS, 1.0))
    drum(name, p, r, assigns=[(MOD(2), "o1_pitch", sweep)], amp=(0.001, decay, 0.0, 0.08))

kick("Kick Deep 808", -12, 0.2, 0.9, click=0.0, drive=0.15)
kick("Kick Tight", 0, 0.28, 0.28, click=0.1, drive=0.25)
kick("Kick Punch", -5, 0.3, 0.4, click=0.15, drive=0.4)
kick("Kick Sub Boom", -20, 0.18, 1.2, drive=0.1)
kick("Kick Hard", 0, 0.33, 0.35, click=0.2, drive=0.7, wt=FOLD)

def noise_voice(name, cut, res, model_mode, decay, noise_color=0.6, tone=0.0, tone_pitch=0, drive=0.0, hold=0.0, ntype=0, rel=0.05, perf=None, assigns=(), more=None):
    p = {"o1_wt": BASIC, "o1_pos": 0.0, "o1_pitch": tone_pitch, "o1_level": tone, "n_level": 0.9, "n_type": ntype, "n_color": noise_color,
         "f1_model": SVF, "f1_mode": model_mode, "f1_cut": cut, "f1_res": res, "ins_type": 1, "ins_drive": drive, "ins_mix": 1.0 if drive > 0 else 0.0}
    r = [(NOISE, TO_F1, 1.0), (F1, TO_INS, 1.0), (INS, TO_OUT, 1.0)]
    if tone > 0: r.append((OSC1, TO_F1, 1.0))
    p.update(envp(2, 0.0005, 0.05 + decay * 0.1, 0.0, 0.05, oneshot=1))
    ex = {"m1_hold": hold}
    if more: ex.update(more)
    drum(name, p, r, assigns=assigns, amp=(0.0008, decay, 0.0, rel), extra=ex, perf=perf)

noise_voice("Snare Crack", 2400, 0.35, 1, 0.22, noise_color=0.55, tone=0.5, tone_pitch=12, drive=0.2)
noise_voice("Snare Tight", 3200, 0.3, 1, 0.14, noise_color=0.6, tone=0.4, tone_pitch=16)
noise_voice("Hat Closed", 9000, 0.15, 2, 0.045, noise_color=0.9)
noise_voice("Hat Open", 8000, 0.15, 2, 0.35, noise_color=0.9, rel=0.2)
noise_voice("Clap Room", 1500, 0.45, 1, 0.16, noise_color=0.6, perf={1: [1, 0.15, 0.85, 0.1, 0.7, 0.1, 0.5, 0.0] + [0.5] * 8},
            assigns=[(PERF(1), "amp_level", 0.8)], more={"amp_level": 0.0, "p1_steps": 8, "p1_sync": 1, "p1_div": 5})
noise_voice("Shaker", 7000, 0.3, 1, 0.09, noise_color=0.8, hold=0.02)
noise_voice("Rim Shot", 1800, 0.55, 1, 0.05, noise_color=0.5, tone=0.6, tone_pitch=24)

# toms and a FM cowbell/perc
kick("Tom Low", 5, 0.12, 0.5)
kick("Tom High", 17, 0.12, 0.35)
drum("Cowbell FM", {"o1_wt": BELLS, "o1_pos": 0.6, "o1_pitch": 12, "o1_level": 0.8, "f1_cut": 4500, "f1_res": 0.2, "f1_model": SVF, "f1_mode": 1}, [(OSC1, TO_F1, 1.0), (F1, TO_OUT, 1.0)], amp=(0.001, 0.25, 0.0, 0.1))

# ==================================================================================================
# FX
# ==================================================================================================
X = "FX"
voice("Riser", X, wt1=GRIT, pos1=0.2, cut=300, res=0.4, noise=0.35, ntype=0, ncolor=0.8, uni1=4, det1=40, lfo=None,
      assigns=[(MOD(2), "f1_cut", 0.7), (MOD(2), "o1_pitch", 0.15)], extra=dict(**envp(2, 6.0, 0.1, 1.0, 0.5)), amp=(1.0, 0.5, 1.0, 1.0), fx=dict(rev_mix=0.35))
voice("Downlifter", X, wt1=GRIT, pos1=0.4, cut=9000, res=0.3, noise=0.3, uni1=3, det1=30,
      assigns=[(MOD(2), "f1_cut", -0.6), (MOD(2), "o1_pitch", -0.12)], extra=dict(**envp(2, 0.001, 4.0, 0.0, 1.0)), amp=(0.01, 4.0, 0.0, 1.0), fx=dict(rev_mix=0.35))
voice("Laser Zap", X, wt1=SYNC, pos1=0.4, cut=9000, res=0.3, assigns=[(MOD(2), "o1_pitch", 0.35)], extra=dict(**envp(2, 0.0005, 0.15, 0.0, 0.1)), amp=(0.001, 0.3, 0.0, 0.1), fx=dict(dly_mix=0.25, dly_sync=1, dly_div=3))
voice("Alien Transmission", X, wt1=VOWEL, pos1=0.4, cut=4000, res=0.4, lfo=lfo_multi(2, [("o1_pos", 0.6), ("f1_cut", 0.2), ("o1_pitch", 0.03)], rate=3.3, shape=5), amp=(0.05, 0.5, 0.9, 0.6), fx=dict(dly_mix=0.35, dly_fb=0.55, dly_sync=1, dly_div=3, rev_mix=0.3))
voice("Wind Texture", X, wt1=BASIC, pos1=0.0, lvl1=0.0, noise=0.9, ntype=1, ncolor=0.4, cut=900, res=0.4, lfo=lfo_on(2, "f1_cut", 0.3, rate=0.13, shape=6), amp=(1.5, 0.5, 1.0, 2.0), fx=dict(rev_mix=0.4, rev_size=0.9),
      routes=[(NOISE, TO_F1, 1.0), (F1, TO_OUT, 1.0)])
voice("Ocean Wash", X, wt1=BASIC, lvl1=0.0, noise=0.9, ntype=2, ncolor=0.35, cut=600, res=0.2, lfo=lfo_on(2, "f1_cut", 0.35, rate=0.09, shape=0), amp=(2.0, 0.5, 1.0, 3.0), fx=dict(rev_mix=0.45, rev_size=0.9),
      routes=[(NOISE, TO_F1, 1.0), (F1, TO_OUT, 1.0)])
voice("Robot Voice", X, wt1=VOWEL, pos1=0.2, model=COMB, mode=0, cut=300, res=0.7, lfo=lfo_on(2, "o1_pos", 0.7, sync=True, div=3, shape=5), amp=(0.003, 0.3, 0.9, 0.2))
voice("Metal Hit", X, wt1=BELLS, pos1=0.9, model=COMB, mode=0, cut=700, res=0.8, noise=0.2, ncolor=0.8, amp=(0.001, 1.4, 0.0, 0.6), fx=dict(rev_mix=0.3, rev_size=0.7))
voice("Sci-Fi Drone", X, wt1=FOLD, pos1=0.6, uni1=3, det1=20, cut=1500, res=0.4, lfo=lfo_multi(2, [("o1_pos", 0.4), ("f1_cut", 0.2)], rate=0.18, shape=6), amp=(2.0, 0.5, 1.0, 3.0), fx=dict(rev_mix=0.5, dly_mix=0.3, dly_sync=1, dly_div=2))
voice("Glitch Stutter", X, wt1=GRIT, pos1=0.5, cut=3000, res=0.3, ins=dict(ins_type=2, ins_drive=0.6, ins_mix=0.9), lfo=lfo_on(2, "amp_level", -0.9, sync=True, div=4, shape=4, bipolar=False), amp=(0.003, 0.3, 0.9, 0.2))

# ==================================================================================================
# SEQUENCE (performers / tempo-synced modulation - hold a note or a chord)
# ==================================================================================================
Q = "Sequence"
def semis(*s): return [round(x / 12.0, 3) for x in s] + [0.0] * (16 - len(s))
def semis24(*s): return [round(x / 24.0, 3) for x in s] + [0.0] * (16 - len(s))   # amount 0.25 = 24 semitones per full bar
voice("Minor Arp", Q, wt1=BASIC, pos1=0.66, cut=2600, res=0.25, amp=(0.001, 0.2, 0.8, 0.1), fenv=(0.25, 0.001, 0.15, 0.2, 0.1),
      assigns=[(PERF(1), "o1_pitch", 0.25)], extra=dict(p1_steps=8, p1_sync=1, p1_div=4), perf={1: semis24(0, 3, 7, 12, 15, 12, 7, 3)}, fx=dict(dly_mix=0.25, dly_sync=1, dly_div=3, rev_mix=0.2))
voice("Major Arp", Q, wt1=PULSE, pos1=0.3, cut=3200, res=0.2, amp=(0.001, 0.2, 0.8, 0.1), assigns=[(PERF(1), "o1_pitch", 0.125)], extra=dict(p1_steps=6, p1_sync=1, p1_div=4),
      perf={1: semis(0, 4, 7, 12, 7, 4)}, fx=dict(dly_mix=0.25, dly_sync=1, dly_div=3, rev_mix=0.2))
voice("Gate Pad", Q, wt1=BASIC, pos1=0.66, uni1=5, det1=18, cut=3500, res=0.1, amp=(0.01, 0.3, 1.0, 0.3), assigns=[(PERF(1), "amp_level", 0.75)], extra=dict(p1_steps=8, p1_sync=1, p1_div=4, amp_level=0.0),
      perf={1: [1, 1, 0, 1, 1, 0, 1, 0] + [0] * 8}, fx=dict(rev_mix=0.3, dly_mix=0.2, dly_sync=1, dly_div=3))
voice("Filter Stepper", Q, wt1=BASIC, pos1=0.66, uni1=2, det1=10, cut=450, res=0.45, amp=(0.005, 0.3, 0.9, 0.2), assigns=[(PERF(1), "f1_cut", 0.5)], extra=dict(p1_steps=16, p1_sync=1, p1_div=4),
      perf={1: [0.1, 0.5, 0.2, 0.8, 0.3, 0.6, 0.15, 0.9, 0.1, 0.4, 0.25, 0.7, 0.35, 0.55, 0.2, 1.0]})
voice("Bouncing Ball", Q, wt1=BELLS, pos1=0.3, cut=6000, res=0.1, amp=(0.001, 0.25, 0.7, 0.2), assigns=[(PERF(1), "o1_pitch", 0.25)], extra=dict(p1_steps=8, p1_sync=1, p1_div=4, p1_smooth=0.0),
      perf={1: [1.0, 0.0, 0.5, 0.0, 0.75, 0.0, 0.25, 0.0] + [0.0] * 8}, fx=dict(dly_mix=0.3, dly_sync=1, dly_div=3, rev_mix=0.3))
voice("Pulse Motion", Q, wt1=PULSE, pos1=0.0, uni1=3, det1=10, cut=2500, res=0.3, amp=(0.005, 0.3, 0.9, 0.3), assigns=[(PERF(1), "o1_pos", 0.8), (PERF(2), "f1_cut", 0.3)],
      extra=dict(p1_steps=8, p1_sync=1, p1_div=4, p1_smooth=0.5, p2_steps=5, p2_sync=1, p2_div=3, p2_smooth=0.3),
      perf={1: [0.0, 0.6, 0.2, 1.0, 0.4, 0.8, 0.1, 0.5] + [0] * 8, 2: [0.2, 0.9, 0.4, 0.7, 0.1] + [0.5] * 11})
voice("Trance Gate Lead", Q, wt1=BASIC, pos1=0.66, uni1=6, det1=24, cut=6000, res=0.15, amp=(0.005, 0.3, 1.0, 0.2), assigns=[(PERF(1), "amp_level", 0.75)], extra=dict(p1_steps=16, p1_sync=1, p1_div=4, amp_level=0.0),
      perf={1: [1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 0]}, fx=dict(dly_mix=0.3, dly_sync=1, dly_div=3, rev_mix=0.25))
voice("Random Bleeps", Q, wt1=PULSE, pos1=0.15, cut=5000, res=0.3, amp=(0.001, 0.12, 0.0, 0.08), assigns=[(PERF(1), "o1_pitch", 0.2)],
      extra=dict(p1_steps=16, p1_sync=1, p1_div=4), perf={1: [0.1, 0.8, 0.35, 0.6, 0.0, 0.95, 0.5, 0.25, 0.7, 0.15, 0.85, 0.4, 0.55, 0.05, 0.9, 0.3]},
      fx=dict(dly_mix=0.3, dly_sync=1, dly_div=3, dly_fb=0.5, rev_mix=0.2))


def main():
    out = ["<PRESETS>"]
    for cat, xml in PRESETS:
        out.append(xml)
    out.append("</PRESETS>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    counts = {}
    for cat, _ in PRESETS:
        counts[cat] = counts.get(cat, 0) + 1
    print("wrote %d presets to %s" % (len(PRESETS), os.path.normpath(OUT)))
    for c, n in counts.items():
        print("  %-9s %d" % (c, n))


if __name__ == "__main__":
    main()
