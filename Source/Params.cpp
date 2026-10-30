#include "Params.h"

namespace psxl
{
using juce::String;
using juce::StringArray;

static const char* const kDestIds[D_COUNT] = {
    "o1_pos", "o1_pitch", "o1_fine", "o1_level", "o1_detune", "o1_pm", "o1_fold",
    "o2_pos", "o2_pitch", "o2_fine", "o2_level", "o2_detune", "o2_pm", "o2_fold",
    "n_level", "n_color",
    "f1_cut", "f1_res", "f1_drive",
    "f2_cut", "f2_res", "f2_drive",
    "ins_drive", "ins_mix", "amp_level", "amp_pan", "amp_fb", "pitch",
    "master_vol", "eq_lo_g", "eq_mid_f", "eq_mid_g", "eq_hi_g",
    "dly_fb", "dly_mix", "rev_size", "rev_mix",
    "cho_rate", "cho_depth", "cho_mix", "dist_drive", "dist_mix" };

const char* destId (int d) { return kDestIds[juce::jlimit (0, (int) D_COUNT - 1, d)]; }
bool destIsVoice (int d) { return d >= 0 && d < kNumVoiceDests; }
int destIndexForId (const String& id)
{
    for (int i = 0; i < D_COUNT; ++i)
        if (id == kDestIds[i]) return i;
    return -1;
}

String oscId (int o, const char* n) { return "o" + String (o) + "_" + n; }
String filtId (int f, const char* n) { return "f" + String (f) + "_" + n; }
String modId (int s, const char* n) { return "m" + String (s) + "_" + n; }
String perfId (int p, const char* n) { return "p" + String (p) + "_" + n; }
String macroId (int i) { return "macro" + String (i + 1); }

String sourceName (int s)
{
    if (s >= S_Mod1 && s < S_Mod1 + kNumMods) return s == 0 ? "Amp Env" : "Mod " + String (s + 1);
    if (s >= S_Perf1 && s < S_Perf1 + kNumPerf) return "Perf " + String (s - S_Perf1 + 1);
    if (s >= S_Macro1 && s < S_Macro1 + kNumMacros) return "Macro " + String (s - S_Macro1 + 1);
    switch (s) {
        case S_Velocity: return "Velocity";
        case S_Keytrack: return "Key Track";
        case S_Random: return "Random";
        case S_ModWheel: return "Mod Wheel";
        case S_Aftertouch: return "Aftertouch";
        case S_PitchBend: return "Pitch Bend";
    }
    return "?";
}

StringArray divisionNames() { return { "1/1", "1/2", "1/4", "1/8", "1/16", "1/32", "1/4T", "1/8T", "1/16T" }; }
float divisionBeats (int d)
{
    static const float b[] = { 4.f, 2.f, 1.f, 0.5f, 0.25f, 0.125f, 2.f / 3.f, 1.f / 3.f, 1.f / 6.f };
    return b[juce::jlimit (0, 8, d)];
}
StringArray lfoShapeNames() { return { "Sine", "Triangle", "Saw Up", "Saw Down", "Square", "Sample & Hold", "Smooth Random" }; }
StringArray filterModelNames() { return { "Ladder", "State Variable", "Comb", "Formant" }; }
StringArray filterModeNames (int model)
{
    switch (model) {
        case 0: return { "LP 24", "LP 12", "BP", "HP 24" };
        case 1: return { "LP", "BP", "HP", "Notch" };
        case 2: return { "Comb +", "Comb -", "Flange", "Pluck" };
        default: return { "Male", "Female", "Child", "Alien" };
    }
}
StringArray insertTypeNames() { return { "TanH", "Fold", "Bitcrush", "Hard Clip", "Rectify", "Sine" }; }
StringArray noiseTypeNames() { return { "White", "Pink", "Brown", "Crackle" }; }
StringArray voiceModeNames() { return { "Poly", "Mono", "Legato" }; }

// ---------------------------------------------------------------------------------------------
MacroParameter::MacroParameter (int index)
    : juce::AudioParameterFloat (juce::ParameterID { macroId (index), 1 }, "Macro " + String (index + 1),
                                 juce::NormalisableRange<float> (0.f, 1.f), 0.f),
      displayName ("Macro " + String (index + 1)) {}

String MacroParameter::getName (int maxLen) const
{
    const juce::SpinLock::ScopedLockType sl (lock);
    return maxLen > 0 ? displayName.substring (0, maxLen) : displayName;
}
void MacroParameter::setDisplayName (const String& n) { const juce::SpinLock::ScopedLockType sl (lock); displayName = n; }
String MacroParameter::getDisplayName() const { const juce::SpinLock::ScopedLockType sl (lock); return displayName; }

// ---------------------------------------------------------------------------------------------
using Group = juce::AudioProcessorParameterGroup;
using PID = juce::ParameterID;

static std::unique_ptr<juce::AudioParameterFloat> mkF (const String& id, const String& name, float lo, float hi, float def,
                                                       float centre = -1.f, float interval = 0.f, const String& label = {})
{
    juce::NormalisableRange<float> r (lo, hi, interval);
    if (centre > lo && centre < hi) r.setSkewForCentre (centre);
    return std::make_unique<juce::AudioParameterFloat> (PID { id, 1 }, name, r, def, juce::AudioParameterFloatAttributes().withLabel (label));
}
static std::unique_ptr<juce::AudioParameterChoice> mkC (const String& id, const String& name, const StringArray& c, int def = 0)
{ return std::make_unique<juce::AudioParameterChoice> (PID { id, 1 }, name, c, def); }
static std::unique_ptr<juce::AudioParameterBool> mkB (const String& id, const String& name, bool def)
{ return std::make_unique<juce::AudioParameterBool> (PID { id, 1 }, name, def); }
static std::unique_ptr<juce::AudioParameterInt> mkI (const String& id, const String& name, int lo, int hi, int def)
{ return std::make_unique<juce::AudioParameterInt> (PID { id, 1 }, name, lo, hi, def); }

juce::AudioProcessorValueTreeState::ParameterLayout createParameterLayout()
{
    juce::AudioProcessorValueTreeState::ParameterLayout layout;

    // Page order matters: hosts and NKS controllers expose parameters in groups of eight, so each
    // group below is one controller page. Macros come first.
    for (int page = 0; page < 2; ++page)
    {
        auto g = std::make_unique<Group> ("macros" + String (page + 1), "Macros " + String (page * 8 + 1) + "-" + String (page * 8 + 8), "|");
        for (int i = 0; i < 8; ++i) g->addChild (std::make_unique<MacroParameter> (page * 8 + i));
        layout.add (std::move (g));
    }

    for (int o = 1; o <= 2; ++o)
    {
        const String n = "Osc " + String (o) + " ";
        auto g = std::make_unique<Group> ("osc" + String (o), "Oscillator " + String (o), "|");
        g->addChild (mkF (oscId (o, "pos"), n + "Position", 0.f, 1.f, 0.f));
        g->addChild (mkF (oscId (o, "pitch"), n + "Pitch", -48.f, 48.f, 0.f, -1.f, 1.f, "st"));
        g->addChild (mkF (oscId (o, "fine"), n + "Fine", -100.f, 100.f, 0.f, -1.f, 0.f, "ct"));
        g->addChild (mkF (oscId (o, "level"), n + "Level", 0.f, 1.f, 0.8f));
        g->addChild (mkI (oscId (o, "uni"), n + "Unison", 1, 8, 1));
        g->addChild (mkF (oscId (o, "detune"), n + "Detune", 0.f, 100.f, 15.f, 20.f, 0.f, "ct"));
        g->addChild (mkF (oscId (o, "pm"), n + "Phase Mod", 0.f, 1.f, 0.f));
        g->addChild (mkF (oscId (o, "fold"), n + "Fold", 0.f, 1.f, 0.f));
        g->addChild (mkI (oscId (o, "wt"), n + "Wavetable", 0, kNumTableSlots - 1, o == 1 ? 0 : 1));
        layout.add (std::move (g));
    }

    {
        auto g = std::make_unique<Group> ("noisefilt", "Noise + Filter 1", "|");
        g->addChild (mkF ("n_level", "Noise Level", 0.f, 1.f, 0.5f));
        g->addChild (mkF ("n_color", "Noise Color", 0.f, 1.f, 0.5f));
        g->addChild (mkC ("n_type", "Noise Type", noiseTypeNames()));
        layout.add (std::move (g));
    }
    for (int f = 1; f <= 2; ++f)
    {
        const String n = "Filter " + String (f) + " ";
        auto g = std::make_unique<Group> ("filt" + String (f), "Filter " + String (f), "|");
        g->addChild (mkF (filtId (f, "cut"), n + "Cutoff", 20.f, 20000.f, f == 1 ? 12000.f : 8000.f, 1000.f, 0.f, "Hz"));
        g->addChild (mkF (filtId (f, "res"), n + "Reso", 0.f, 1.f, 0.15f));
        g->addChild (mkF (filtId (f, "drive"), n + "Drive", 0.f, 1.f, 0.f));
        g->addChild (mkF (filtId (f, "ktr"), n + "Key Track", -1.f, 1.f, 0.f));
        g->addChild (mkC (filtId (f, "model"), n + "Model", filterModelNames()));
        g->addChild (mkC (filtId (f, "mode"), n + "Mode", { "Mode 1", "Mode 2", "Mode 3", "Mode 4" }));
        layout.add (std::move (g));
    }
    {
        auto g = std::make_unique<Group> ("insert", "Insert + Amp", "|");
        g->addChild (mkC ("ins_type", "Insert Type", insertTypeNames()));
        g->addChild (mkF ("ins_drive", "Insert Drive", 0.f, 1.f, 0.3f));
        g->addChild (mkF ("ins_mix", "Insert Mix", 0.f, 1.f, 0.5f));
        g->addChild (mkF ("amp_level", "Amp Level", 0.f, 1.f, 0.7f));
        g->addChild (mkF ("amp_pan", "Amp Pan", -1.f, 1.f, 0.f));
        g->addChild (mkF ("amp_fb", "Amp Feedback", 0.f, 1.f, 0.f));
        layout.add (std::move (g));
    }
    {
        auto g = std::make_unique<Group> ("voice", "Voice + Master", "|");
        g->addChild (mkF ("master_vol", "Volume", 0.f, 1.f, 0.7f));
        g->addChild (mkF ("pitch", "Pitch", -48.f, 48.f, 0.f, -1.f, 0.f, "st"));
        g->addChild (mkF ("glide", "Glide Time", 0.f, 5.f, 0.f, 0.4f, 0.f, "s"));
        g->addChild (mkB ("glide_expo", "Glide Expo", false));
        g->addChild (mkC ("voice_mode", "Voice Mode", voiceModeNames()));
        g->addChild (mkI ("voices", "Polyphony", 1, kMaxVoices, 8));
        g->addChild (mkI ("bend_range", "Bend Range", 0, 24, 2));
        g->addChild (mkF ("vel_sens", "Velocity Sens", 0.f, 1.f, 0.5f));
        layout.add (std::move (g));
    }

    // Modulator slots. Slot 1 is always the amp envelope.
    for (int s = 1; s <= kNumMods; ++s)
    {
        const String n = s == 1 ? "Amp Env " : "Mod " + String (s) + " ";
        auto g = std::make_unique<Group> ("mod" + String (s), s == 1 ? "Amp Envelope" : "Modulator " + String (s), "|");
        if (s > 1) g->addChild (mkC (modId (s, "type"), n + "Type", { "Envelope", "LFO" }, 0));
        g->addChild (mkF (modId (s, "att"), n + "Attack", 0.0005f, 10.f, s == 1 ? 0.005f : 0.01f, 0.3f, 0.f, "s"));
        g->addChild (mkF (modId (s, "dec"), n + "Decay", 0.001f, 10.f, 0.4f, 0.4f, 0.f, "s"));
        g->addChild (mkF (modId (s, "sus"), n + "Sustain", 0.f, 1.f, s == 1 ? 0.8f : 0.5f));
        g->addChild (mkF (modId (s, "rel"), n + "Release", 0.001f, 10.f, s == 1 ? 0.25f : 0.3f, 0.4f, 0.f, "s"));
        g->addChild (mkF (modId (s, "dly"), n + "Delay", 0.f, 5.f, 0.f, 0.3f, 0.f, "s"));
        g->addChild (mkF (modId (s, "hold"), n + "Hold", 0.f, 5.f, 0.f, 0.3f, 0.f, "s"));
        g->addChild (mkF (modId (s, "level"), n + "Level", 0.f, 1.f, 1.f));
        g->addChild (mkB (modId (s, "oneshot"), n + "One Shot", false));
        if (s > 1)
        {
            g->addChild (mkF (modId (s, "rate"), n + "Rate", 0.01f, 50.f, 2.f, 2.f, 0.f, "Hz"));
            g->addChild (mkC (modId (s, "shape"), n + "Shape", lfoShapeNames()));
            g->addChild (mkF (modId (s, "phase"), n + "Phase", 0.f, 1.f, 0.f));
            g->addChild (mkF (modId (s, "fade"), n + "Fade In", 0.f, 10.f, 0.f, 0.5f, 0.f, "s"));
            g->addChild (mkB (modId (s, "bipolar"), n + "Bipolar", true));
            g->addChild (mkB (modId (s, "sync"), n + "Sync", false));
            g->addChild (mkC (modId (s, "div"), n + "Division", divisionNames(), 2));
        }
        layout.add (std::move (g));
    }

    for (int p = 1; p <= kNumPerf; ++p)
    {
        const String n = "Perf " + String (p) + " ";
        auto g = std::make_unique<Group> ("perf" + String (p), "Performer " + String (p), "|");
        g->addChild (mkI (perfId (p, "steps"), n + "Steps", 1, kPerfSteps, 8));
        g->addChild (mkF (perfId (p, "rate"), n + "Rate", 0.1f, 40.f, 4.f, 4.f, 0.f, "Hz"));
        g->addChild (mkB (perfId (p, "sync"), n + "Sync", true));
        g->addChild (mkC (perfId (p, "div"), n + "Division", divisionNames(), 4));
        g->addChild (mkF (perfId (p, "smooth"), n + "Smooth", 0.f, 1.f, 0.f));
        layout.add (std::move (g));
    }

    {
        auto g = std::make_unique<Group> ("fx1", "EQ + Distortion", "|");
        g->addChild (mkF ("eq_lo_g", "EQ Low Gain", -18.f, 18.f, 0.f, -1.f, 0.f, "dB"));
        g->addChild (mkF ("eq_lo_f", "EQ Low Freq", 40.f, 400.f, 120.f, 120.f, 0.f, "Hz"));
        g->addChild (mkF ("eq_mid_g", "EQ Mid Gain", -18.f, 18.f, 0.f, -1.f, 0.f, "dB"));
        g->addChild (mkF ("eq_mid_f", "EQ Mid Freq", 200.f, 8000.f, 1000.f, 1500.f, 0.f, "Hz"));
        g->addChild (mkF ("eq_mid_q", "EQ Mid Q", 0.3f, 6.f, 1.f, 1.f));
        g->addChild (mkF ("eq_hi_g", "EQ High Gain", -18.f, 18.f, 0.f, -1.f, 0.f, "dB"));
        g->addChild (mkF ("eq_hi_f", "EQ High Freq", 2000.f, 16000.f, 6000.f, 6000.f, 0.f, "Hz"));
        g->addChild (mkF ("dist_drive", "Dist Drive", 0.f, 1.f, 0.3f));
        g->addChild (mkF ("dist_mix", "Dist Mix", 0.f, 1.f, 0.f));
        layout.add (std::move (g));
    }
    {
        auto g = std::make_unique<Group> ("fx2", "Delay + Reverb + Chorus", "|");
        g->addChild (mkF ("dly_time", "Delay Time", 1.f, 2000.f, 350.f, 300.f, 0.f, "ms"));
        g->addChild (mkB ("dly_sync", "Delay Sync", false));
        g->addChild (mkC ("dly_div", "Delay Division", divisionNames(), 3));
        g->addChild (mkF ("dly_fb", "Delay Feedback", 0.f, 0.95f, 0.35f));
        g->addChild (mkF ("dly_mix", "Delay Mix", 0.f, 1.f, 0.f));
        g->addChild (mkF ("rev_size", "Reverb Size", 0.f, 1.f, 0.5f));
        g->addChild (mkF ("rev_damp", "Reverb Damping", 0.f, 1.f, 0.5f));
        g->addChild (mkF ("rev_mix", "Reverb Mix", 0.f, 1.f, 0.f));
        g->addChild (mkF ("cho_rate", "Chorus Rate", 0.05f, 8.f, 0.6f, 0.8f, 0.f, "Hz"));
        g->addChild (mkF ("cho_depth", "Chorus Depth", 0.f, 1.f, 0.5f));
        g->addChild (mkF ("cho_mix", "Chorus Mix", 0.f, 1.f, 0.f));
        layout.add (std::move (g));
    }
    return layout;
}

// ---------------------------------------------------------------------------------------------
void ParamPtrs::bind (juce::AudioProcessorValueTreeState& apvts)
{
    auto raw = [&] (const String& id) { auto* p = apvts.getRawParameterValue (id); jassert (p != nullptr); return p; };
    for (int d = 0; d < D_COUNT; ++d) { dest[(size_t) d] = raw (destId (d)); destRange[(size_t) d] = apvts.getParameterRange (destId (d)); }
    wt1 = raw ("o1_wt"); wt2 = raw ("o2_wt"); uni1 = raw ("o1_uni"); uni2 = raw ("o2_uni");
    f1Model = raw ("f1_model"); f1Mode = raw ("f1_mode"); f2Model = raw ("f2_model"); f2Mode = raw ("f2_mode");
    f1Ktr = raw ("f1_ktr"); f2Ktr = raw ("f2_ktr"); insType = raw ("ins_type"); noiseType = raw ("n_type");
    voiceMode = raw ("voice_mode"); voices = raw ("voices"); bendRange = raw ("bend_range");
    glide = raw ("glide"); glideExpo = raw ("glide_expo"); velSens = raw ("vel_sens");
    eqLoFreq = raw ("eq_lo_f"); eqHiFreq = raw ("eq_hi_f"); eqMidQ = raw ("eq_mid_q");
    dlyTime = raw ("dly_time"); dlySync = raw ("dly_sync"); dlyDiv = raw ("dly_div"); revDamp = raw ("rev_damp");
    for (int s = 1; s <= kNumMods; ++s)
    {
        auto& sl = slot[(size_t) s - 1];
        sl.type = s > 1 ? raw (modId (s, "type")) : nullptr;
        sl.att = raw (modId (s, "att")); sl.dec = raw (modId (s, "dec")); sl.sus = raw (modId (s, "sus")); sl.rel = raw (modId (s, "rel"));
        sl.dly = raw (modId (s, "dly")); sl.hold = raw (modId (s, "hold")); sl.level = raw (modId (s, "level")); sl.oneShot = raw (modId (s, "oneshot"));
        const bool lfo = s > 1;
        sl.rate = lfo ? raw (modId (s, "rate")) : nullptr; sl.shape = lfo ? raw (modId (s, "shape")) : nullptr;
        sl.phase = lfo ? raw (modId (s, "phase")) : nullptr; sl.fade = lfo ? raw (modId (s, "fade")) : nullptr;
        sl.bipolar = lfo ? raw (modId (s, "bipolar")) : nullptr; sl.sync = lfo ? raw (modId (s, "sync")) : nullptr;
        sl.div = lfo ? raw (modId (s, "div")) : nullptr;
    }
    for (int p = 1; p <= kNumPerf; ++p)
    {
        auto& pp = perf[(size_t) p - 1];
        pp.steps = raw (perfId (p, "steps")); pp.rate = raw (perfId (p, "rate")); pp.sync = raw (perfId (p, "sync"));
        pp.div = raw (perfId (p, "div")); pp.smooth = raw (perfId (p, "smooth"));
    }
    for (int i = 0; i < kNumMacros; ++i) macro[(size_t) i] = raw (macroId (i));
}

void ParamPtrs::snapshot (BlockParams& bp) const
{
    for (int d = 0; d < D_COUNT; ++d)
        bp.destNorm[(size_t) d] = destRange[(size_t) d].convertTo0to1 (dest[(size_t) d]->load());
    bp.wt1 = (int) wt1->load(); bp.wt2 = (int) wt2->load(); bp.uni1 = (int) uni1->load(); bp.uni2 = (int) uni2->load();
    bp.f1Model = (int) f1Model->load(); bp.f1Mode = (int) f1Mode->load(); bp.f2Model = (int) f2Model->load(); bp.f2Mode = (int) f2Mode->load();
    bp.f1Ktr = f1Ktr->load(); bp.f2Ktr = f2Ktr->load(); bp.insType = (int) insType->load(); bp.noiseType = (int) noiseType->load();
    bp.voiceMode = (int) voiceMode->load(); bp.voices = (int) voices->load(); bp.bendRange = (int) bendRange->load();
    bp.glide = glide->load(); bp.glideExpo = glideExpo->load() > 0.5f; bp.velSens = velSens->load();
    bp.eqLoFreq = eqLoFreq->load(); bp.eqHiFreq = eqHiFreq->load(); bp.eqMidQ = eqMidQ->load();
    bp.revDamp = revDamp->load();
    bp.dlyTimeMs = dlyTime->load(); bp.dlySync = dlySync->load() > 0.5f; bp.dlyDiv = (int) dlyDiv->load();
    for (size_t s = 0; s < (size_t) kNumMods; ++s)
    {
        const auto& sl = slot[s]; auto& o = bp.slot[s];
        o.type = sl.type ? (int) sl.type->load() : 0;
        o.att = sl.att->load(); o.dec = sl.dec->load(); o.sus = sl.sus->load(); o.rel = sl.rel->load();
        o.dly = sl.dly->load(); o.hold = sl.hold->load(); o.level = sl.level->load(); o.oneShot = sl.oneShot->load() > 0.5f;
        if (sl.rate) {
            o.rate = sl.rate->load(); o.shape = (int) sl.shape->load(); o.phase = sl.phase->load(); o.fade = sl.fade->load();
            o.bipolar = sl.bipolar->load() > 0.5f; o.sync = sl.sync->load() > 0.5f; o.div = (int) sl.div->load();
        }
    }
    for (size_t p = 0; p < (size_t) kNumPerf; ++p)
    {
        auto& o = bp.perf[p]; const auto& pp = perf[p];
        o.steps = (int) pp.steps->load(); o.rate = pp.rate->load(); o.sync = pp.sync->load() > 0.5f;
        o.div = (int) pp.div->load(); o.smooth = pp.smooth->load();
    }
    for (size_t i = 0; i < (size_t) kNumMacros; ++i) bp.macro[i] = macro[i]->load();
}
} // namespace psxl
