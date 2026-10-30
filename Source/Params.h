#pragma once
#include <juce_audio_processors/juce_audio_processors.h>
#include <array>
#include <atomic>

// Parameter definitions and shared constants for Massive PSXL.
namespace psxl
{
constexpr int kNumMods = 9;           // modulator slots (slot 1 is the amp envelope)
constexpr int kNumPerf = 3;           // performer (step) modulators
constexpr int kNumMacros = 16;
constexpr int kPerfSteps = 16;
constexpr int kNumTableSlots = 32;    // wavetable slots (builtin + user)
constexpr int kNumBuiltinTables = 10;
constexpr int kMaxAssign = 256;       // maximum modulation assignments
constexpr int kMaxVoices = 16;

// Signal-flow nodes used by the routing matrix.
enum Node { N_Osc1 = 0, N_Osc2, N_Noise, N_Filt1, N_Filt2, N_Insert, N_Out, N_Count };
constexpr int kRouteSrc = 6;  // Osc1, Osc2, Noise, Filt1, Filt2, Insert
constexpr int kRouteDst = 4;  // Filt1, Filt2, Insert, Out  (dst index = node - N_Filt1)
inline bool routeAllowed (int src, int dstIdx) { return src >= 0 && src < kRouteSrc && dstIdx >= 0 && dstIdx < kRouteDst && src < dstIdx + (int) N_Filt1; }
inline const char* nodeName (int n)
{
    static const char* names[] = { "Osc 1", "Osc 2", "Noise", "Filter 1", "Filter 2", "Insert", "Out" };
    return names[juce::jlimit (0, (int) N_Count - 1, n)];
}

// Modulation sources.
enum Source
{
    S_Mod1 = 0,                 // 0..8
    S_Perf1 = 9,                // 9..11
    S_Macro1 = 12,              // 12..27
    S_Velocity = 28, S_Keytrack, S_Random, S_ModWheel, S_Aftertouch, S_PitchBend,
    S_Count
};
inline bool isGlobalSource (int s) { return (s >= S_Macro1 && s < S_Velocity) || s >= S_ModWheel; }
juce::String sourceName (int s);

// Modulation destinations (continuous parameters). Voice destinations come first.
enum Dest
{
    D_O1_POS, D_O1_PITCH, D_O1_FINE, D_O1_LEVEL, D_O1_DETUNE, D_O1_PM, D_O1_FOLD,
    D_O2_POS, D_O2_PITCH, D_O2_FINE, D_O2_LEVEL, D_O2_DETUNE, D_O2_PM, D_O2_FOLD,
    D_NZ_LEVEL, D_NZ_COLOR,
    D_F1_CUT, D_F1_RES, D_F1_DRIVE,
    D_F2_CUT, D_F2_RES, D_F2_DRIVE,
    D_INS_DRIVE, D_INS_MIX, D_AMP_LEVEL, D_AMP_PAN, D_AMP_FB, D_PITCH,
    kNumVoiceDests,
    D_MASTER_VOL = kNumVoiceDests,
    D_EQ_LO_GAIN, D_EQ_MID_FREQ, D_EQ_MID_GAIN, D_EQ_HI_GAIN,
    D_DLY_FB, D_DLY_MIX, D_REV_SIZE, D_REV_MIX,
    D_CHO_RATE, D_CHO_DEPTH, D_CHO_MIX, D_DIST_DRIVE, D_DIST_MIX,
    D_COUNT
};
const char* destId (int d);
bool destIsVoice (int d);
int destIndexForId (const juce::String& id);   // -1 if not modulatable

// String helpers for parameter ids.
juce::String oscId (int osc, const char* name);        // osc = 1..2  -> "o1_pos"
juce::String filtId (int f, const char* name);         // f = 1..2    -> "f1_cut"
juce::String modId (int slot, const char* name);       // slot = 1..9 -> "m2_att"
juce::String perfId (int p, const char* name);         // p = 1..3    -> "p1_rate"
juce::String macroId (int index);                      // index = 0..15 -> "macro1"

juce::StringArray divisionNames();
float divisionBeats (int div);                         // length of a division in quarter-note beats
juce::StringArray lfoShapeNames();
juce::StringArray filterModelNames();
juce::StringArray filterModeNames (int model);
juce::StringArray insertTypeNames();
juce::StringArray noiseTypeNames();
juce::StringArray voiceModeNames();

// A macro parameter whose host-visible name can change at runtime (smart macro naming).
class MacroParameter : public juce::AudioParameterFloat
{
public:
    explicit MacroParameter (int index);
    juce::String getName (int maximumStringLength) const override;
    void setDisplayName (const juce::String& newName);
    juce::String getDisplayName() const;
private:
    mutable juce::SpinLock lock;
    juce::String displayName;
};

juce::AudioProcessorValueTreeState::ParameterLayout createParameterLayout();

// ---- Plain-float snapshot of everything the audio engine needs, filled once per block. ----
struct SlotParams
{
    int type = 0;       // 0 envelope, 1 LFO
    float dly = 0, att = 0.001f, hold = 0, dec = 0.3f, sus = 0.7f, rel = 0.2f, level = 1;
    float rate = 1, phase = 0, fade = 0;
    int shape = 0, div = 2;
    bool oneShot = false, bipolar = true, sync = false;
};
struct PerfParams { int steps = 8; float rate = 4; bool sync = true; int div = 3; float smooth = 0; };

struct BlockParams
{
    std::array<float, D_COUNT> destNorm {};          // base (unmodulated) normalised values
    int wt1 = 0, wt2 = 1, uni1 = 1, uni2 = 1;
    int f1Model = 0, f1Mode = 0, f2Model = 0, f2Mode = 0, insType = 0, noiseType = 0;
    float f1Ktr = 0, f2Ktr = 0;
    int voiceMode = 0, voices = 8, bendRange = 2;
    float glide = 0, velSens = 0.5f;
    bool glideExpo = false;
    std::array<SlotParams, kNumMods> slot;
    std::array<PerfParams, kNumPerf> perf;
    std::array<float, kNumMacros> macro {};
    // global fx values that are not modulation destinations
    float eqLoFreq = 120, eqHiFreq = 6000, eqMidQ = 1, dlyTimeMs = 350, revDamp = 0.5f;
    bool dlySync = false;
    int dlyDiv = 3;
    double bpm = 120.0;
};

// Cached pointers into the APVTS raw (denormalised) parameter values.
struct ParamPtrs
{
    void bind (juce::AudioProcessorValueTreeState& apvts);
    void snapshot (BlockParams& bp) const;

    std::array<std::atomic<float>*, D_COUNT> dest {};
    std::array<juce::NormalisableRange<float>, D_COUNT> destRange;
    std::atomic<float> *wt1, *wt2, *uni1, *uni2, *f1Model, *f1Mode, *f2Model, *f2Mode, *f1Ktr, *f2Ktr, *insType, *noiseType;
    std::atomic<float> *voiceMode, *voices, *bendRange, *glide, *glideExpo, *velSens;
    std::atomic<float> *eqLoFreq, *eqHiFreq, *eqMidQ, *dlyTime, *dlySync, *dlyDiv, *revDamp;
    struct Slot { std::atomic<float> *type, *dly, *att, *hold, *dec, *sus, *rel, *level, *rate, *shape, *phase, *fade, *oneShot, *bipolar, *sync, *div; };
    std::array<Slot, kNumMods> slot {};
    struct Perf { std::atomic<float> *steps, *rate, *sync, *div, *smooth; };
    std::array<Perf, kNumPerf> perf {};
    std::array<std::atomic<float>*, kNumMacros> macro {};
};
} // namespace psxl
