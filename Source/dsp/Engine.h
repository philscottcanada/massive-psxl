#pragma once
#include "Filters.h"
#include "Modulators.h"
#include "Wavetable.h"
#include <juce_audio_basics/juce_audio_basics.h>

namespace psxl
{
// State shared lock-free between the UI/message thread and the audio thread.
struct EngineShared
{
    std::atomic<float> routeGain[kRouteSrc][kRouteDst] {};
    std::atomic<int> numAssign { 0 };
    std::atomic<int> aSrc[kMaxAssign], aDst[kMaxAssign];
    std::atomic<float> aAmt[kMaxAssign];
    std::atomic<float> perfSteps[kNumPerf][kPerfSteps];
    std::atomic<const Wavetable*> tables[kNumTableSlots];
    std::atomic<float> tuning[128];

    // meters / visual feedback written by the audio thread
    std::atomic<float> nodePeak[N_Count] {};
    std::atomic<int> uiStage[kNumMods] {};
    std::atomic<float> uiProg[kNumMods] {}, uiVal[kNumMods] {}, uiLfoPhase[kNumMods] {};
    std::atomic<float> uiPerfPhase[kNumPerf] {};
    std::atomic<int> uiPerfIdx[kNumPerf] {};
    std::atomic<float> uiDest[D_COUNT] {};          // modulated normalised value of each destination
    std::atomic<float> outPeakL { 0.0f }, outPeakR { 0.0f };
    std::atomic<float> wheelPitch { 0.0f }, wheelMod { 0.0f }, wheelAftertouch { 0.0f };
    std::atomic<int> activeVoices { 0 };

    EngineShared()
    {
        for (int a = 0; a < kMaxAssign; ++a) { aSrc[a] = -1; aDst[a] = -1; aAmt[a] = 0.0f; }
        for (auto& p : perfSteps) for (auto& s : p) s = 0.5f;
        for (auto& t : tables) t = nullptr;
        for (int n = 0; n < 128; ++n) tuning[n] = 440.0f * std::pow (2.0f, ((float) n - 69.0f) / 12.0f);
    }
};

struct RenderContext
{
    const BlockParams* bp = nullptr;
    EngineShared* shared = nullptr;
    const std::array<juce::NormalisableRange<float>, D_COUNT>* ranges = nullptr;
    float modWheel = 0, aftertouch = 0, pitchBend = 0;   // pitchBend -1..1
    float sampleRate = 44100.0f;
    bool lead = false;                                    // publish modulation display values
};

class Voice
{
public:
    void prepare (double sr);
    void start (int note, float velocity, float startNote, bool retrigger, const BlockParams& bp, juce::uint32 seed);
    void changeNote (int note, float velocity);           // legato
    void release();
    void kill();
    void render (float* left, float* right, int numSamples, const RenderContext& ctx);

    bool isActive() const { return active; }
    bool isReleasing() const { return active && !keyHeld; }
    int note = -1;
    bool keyHeld = false, sustained = false;
    juce::uint32 age = 0;
    float peak[N_Count] {};

    // modulation values exposed for the UI (lead voice)
    float srcVal[S_Count] {};
    std::array<Envelope, kNumMods> env;
    std::array<Lfo, kNumMods> lfo;
    std::array<Performer, kNumPerf> perf;

private:
    struct Osc { std::array<float, 8> phase {}, inc {}; int n = 1; int level = 0; float gain = 1.0f; };
    void control (float dt, int numSamples, const RenderContext& ctx);
    float oscSample (Osc& o, const Wavetable* wt, float framePos, float pm, float fold);

    double sampleRate = 44100.0;
    bool active = false;
    float velocity = 1.0f, curNote = 60.0f, targetNote = 60.0f, glideStep = 0.0f, randomVal = 0.0f;
    Osc osc1, osc2;
    VoiceFilter filt1, filt2;
    juce::uint32 noiseRng = 1u;
    float pink[7] {}, brown = 0.0f, noiseLp = 0.0f, crackle = 0.0f, noiseCoef = 0.0f;
    int noiseColorMode = 0, noiseKind = 0;
    float crushHold = 0.0f; int crushCount = 0;

    // control-rate targets with per-sample ramps
    struct Ramp { float cur = 0.0f, inc = 0.0f; void set (float target, int n) { inc = (target - cur) / (float) juce::jmax (1, n); } float next() { cur += inc; return cur; } void snap (float v) { cur = v; inc = 0.0f; } };
    Ramp pos1, pos2, lvl1, lvl2, ampGain, panL, panR, nzLvl, pm1, pm2, fold1, fold2, insDrive, insMix, fbAmt;
    float outPrev = 0.0f;
    float routeG[kRouteSrc][kRouteDst] {};
    int insType = 0;
    const Wavetable *wt1 = nullptr, *wt2 = nullptr;
    float lastOsc2 = 0.0f;
    float mixHeld = 0.0f;
    bool firstControl = true;
};

class MasterFx
{
public:
    struct Params
    {
        float eqLoG = 0, eqLoF = 120, eqMidF = 1000, eqMidG = 0, eqMidQ = 1, eqHiG = 0, eqHiF = 6000;
        float dlyMs = 350, dlyFb = 0.3f, dlyMix = 0;
        float revSize = 0.5f, revDamp = 0.5f, revMix = 0;
        float choRate = 0.6f, choDepth = 0.5f, choMix = 0;
        float distDrive = 0.3f, distMix = 0, master = 0.7f;
    };
    void prepare (double sr, int maxBlock);
    void reset();
    void process (float* left, float* right, int n, const Params& p);

private:
    double sampleRate = 44100.0;
    juce::dsp::IIR::Filter<float> eq[2][3];
    float lastEq[7] { -999, -999, -999, -999, -999, -999, -999 };
    std::vector<float> chorusBuf[2], dlyBuf[2];
    int chorusPos = 0, dlyPos = 0;
    float chorusPhase = 0.0f, dlyLen = 0.0f, dlyLpL = 0.0f, dlyLpR = 0.0f;
    float dcX[2] {}, dcY[2] {};
    juce::Reverb reverb;
};

class SynthEngine
{
public:
    explicit SynthEngine (EngineShared& s) : shared (s) {}
    void prepare (double sr, int maxBlock);
    void reset();
    void process (juce::AudioBuffer<float>& out, const juce::MidiBuffer& midi, const BlockParams& bp,
                  const std::array<juce::NormalisableRange<float>, D_COUNT>& ranges);

private:
    void handleMidi (const juce::MidiMessage& m, const BlockParams& bp);
    void noteOn (int note, float vel, const BlockParams& bp);
    void noteOff (int note);
    void monoNoteOn (int note, float vel, const BlockParams& bp);
    void monoNoteOff (int note, const BlockParams& bp);
    Voice* findFreeVoice (int limit);
    float modulatedGlobal (int dest, const BlockParams& bp, const std::array<juce::NormalisableRange<float>, D_COUNT>& ranges, const float* srcGlobal) const;

    EngineShared& shared;
    double sampleRate = 44100.0;
    std::array<Voice, kMaxVoices> voices;
    juce::uint32 ageCounter = 0, seedCounter = 1;
    std::vector<int> heldNotes;      // mono note stack
    bool sustainDown = false;
    float lastNote = 60.0f;
    bool haveLastNote = false;
    float modWheel = 0, aftertouch = 0, pitchBend = 0;
    MasterFx fx;
    juce::AudioBuffer<float> voiceBuf;
};
} // namespace psxl
