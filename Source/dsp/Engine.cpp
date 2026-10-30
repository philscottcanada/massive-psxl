#include "Engine.h"

namespace psxl
{
constexpr float kPi = juce::MathConstants<float>::pi;
constexpr int kCtl = 16;   // control-rate interval in samples

// =============================================================================================
// Voice
// =============================================================================================
void Voice::prepare (double sr)
{
    sampleRate = sr;
    filt1.prepare (sr); filt2.prepare (sr);
    kill();
}

void Voice::kill()
{
    active = false; keyHeld = false; sustained = false; note = -1;
    for (auto& e : env) { e = Envelope(); }
    for (auto& p : perf) p.reset();
    for (auto& p : peak) p = 0.0f;
}

void Voice::start (int n, float vel, float startNote, bool retrigger, const BlockParams& bp, juce::uint32 seed)
{
    const bool wasActive = active;
    active = true; keyHeld = true; sustained = false; note = n; velocity = vel;
    curNote = startNote; targetNote = (float) n;
    if (bp.glide > 0.001f) glideStep = std::abs (targetNote - curNote) / bp.glide; else curNote = targetNote;

    noiseRng = seed * 2654435761u + 7u;
    auto rnd = [this] { noiseRng = noiseRng * 1664525u + 1013904223u; return (float) (noiseRng >> 8) / 16777216.0f; };
    randomVal = rnd() * 2.0f - 1.0f;

    if (retrigger || !wasActive)
    {
        for (size_t s = 0; s < (size_t) kNumMods; ++s)
        {
            if (s == 0 || bp.slot[s].type == 0) env[s].noteOn (bp.slot[s]);
            else lfo[s].reset (bp.slot[s], seed + (juce::uint32) s * 77u);
        }
        for (auto& p : perf) p.reset();
        for (size_t u = 0; u < 8; ++u) { osc1.phase[u] = u == 0 ? 0.0f : rnd(); osc2.phase[u] = u == 0 ? 0.0f : rnd(); }
    }
    if (!wasActive)
    {
        filt1.reset(); filt2.reset(); outPrev = 0.0f; lastOsc2 = 0.0f;
        for (auto& p : pink) p = 0.0f;
        brown = 0.0f; noiseLp = 0.0f; crackle = 0.0f;
        firstControl = true;
    }
}

void Voice::changeNote (int n, float vel)
{
    note = n; velocity = vel; targetNote = (float) n; keyHeld = true; sustained = false;
    glideStep = 0.0f;   // recomputed by control() from the caller-provided glide time
}

void Voice::release()
{
    keyHeld = false; sustained = false;
    for (auto& e : env) e.noteOff();
}

static inline float insertFx (float x, float drive, float mix, int type, float& crushHold, int& crushCount)
{
    const float d = 1.0f + drive * 14.0f;
    float y;
    switch (type)
    {
        case 0: y = std::tanh (x * d) * 0.8f; break;
        case 1: y = std::sin (x * d * 1.2f) * 0.9f; break;
        case 2:
        {
            const float q = std::pow (2.0f, 15.0f - drive * 12.0f);
            const int hold = 1 + (int) (drive * drive * 12.0f);
            if (--crushCount <= 0) { crushHold = std::round (x * q) / q; crushCount = hold; }
            y = crushHold; break;
        }
        case 3: y = juce::jlimit (-1.0f, 1.0f, x * d) * 0.8f; break;
        case 4: y = std::tanh (std::abs (x * d)) * 1.2f - 0.5f; break;
        default: y = std::sin (x * d * kPi * 0.5f) * 0.9f; break;
    }
    return x * (1.0f - mix) + y * mix;
}

float Voice::oscSample (Osc& o, const Wavetable* wt, float framePos, float pm, float fold)
{
    if (wt == nullptr) return 0.0f;
    const int nf = wt->numFrames;
    const float fp = juce::jlimit (0.0f, 1.0f, framePos) * (float) (nf - 1);
    const int f0 = juce::jmin (nf - 1, (int) fp), f1 = juce::jmin (nf - 1, f0 + 1);
    const float ff = fp - (float) f0;
    const float* a = wt->frame (o.level, f0);
    const float* b = wt->frame (o.level, f1);
    float sum = 0.0f;
    for (int u = 0; u < o.n; ++u)
    {
        float ph = o.phase[(size_t) u] + pm;
        ph -= std::floor (ph);
        const float idx = ph * (float) Wavetable::kFrameSize;
        int i0 = (int) idx;
        const float fr = idx - (float) i0;
        const int i1 = (i0 + 1) & (Wavetable::kFrameSize - 1);
        i0 &= (Wavetable::kFrameSize - 1);
        const float va = a[i0] + (a[i1] - a[i0]) * fr;
        const float vb = b[i0] + (b[i1] - b[i0]) * fr;
        sum += va + (vb - va) * ff;
        float np = o.phase[(size_t) u] + o.inc[(size_t) u];
        if (np >= 1.0f) np -= 1.0f;
        o.phase[(size_t) u] = np;
    }
    sum *= o.gain;
    if (fold > 0.001f)
    {
        const float folded = std::sin (sum * (1.0f + fold * 8.0f) * kPi * 0.5f);
        const float amt = juce::jmin (1.0f, fold * 5.0f);
        sum += (folded - sum) * amt;
    }
    return sum;
}

void Voice::control (float dt, int c, const RenderContext& ctx)
{
    const auto& bp = *ctx.bp;
    auto& sh = *ctx.shared;
    const float sr = ctx.sampleRate;

    // glide
    if (curNote != targetNote)
    {
        const float diff = targetNote - curNote;
        if (bp.glide <= 0.001f) curNote = targetNote;
        else if (bp.glideExpo) { curNote += diff * (1.0f - std::exp (-dt * 5.0f / bp.glide)); if (std::abs (targetNote - curNote) < 0.002f) curNote = targetNote; }
        else
        {
            if (glideStep <= 0.0f) glideStep = std::abs (diff) / bp.glide;
            const float step = glideStep * dt;
            if (std::abs (diff) <= step) curNote = targetNote; else curNote += diff > 0 ? step : -step;
        }
    }

    // modulators
    const float beatsPerSec = (float) (bp.bpm / 60.0);
    for (size_t s = 0; s < (size_t) kNumMods; ++s)
    {
        const auto& sp = bp.slot[s];
        if (s == 0 || sp.type == 0) srcVal[s] = env[s].step (dt, sp);
        else
        {
            const float rate = sp.sync ? beatsPerSec / divisionBeats (sp.div) : sp.rate;
            srcVal[s] = lfo[s].step (dt, rate, sp);
        }
    }
    for (size_t p = 0; p < (size_t) kNumPerf; ++p)
    {
        const auto& pp = bp.perf[p];
        const float sps = pp.sync ? beatsPerSec / divisionBeats (pp.div) : pp.rate;
        srcVal[S_Perf1 + (int) p] = perf[p].step (dt, sps, pp, sh.perfSteps[p]);
    }
    for (int i = 0; i < kNumMacros; ++i) srcVal[S_Macro1 + i] = bp.macro[(size_t) i];
    srcVal[S_Velocity] = velocity;
    srcVal[S_Keytrack] = juce::jlimit (-1.0f, 1.0f, (curNote - 60.0f) / 60.0f);
    srcVal[S_Random] = randomVal;
    srcVal[S_ModWheel] = ctx.modWheel; srcVal[S_Aftertouch] = ctx.aftertouch; srcVal[S_PitchBend] = ctx.pitchBend;

    float add[kNumVoiceDests] = {};
    const int na = juce::jmin (kMaxAssign, sh.numAssign.load (std::memory_order_relaxed));
    for (int a = 0; a < na; ++a)
    {
        const int s = sh.aSrc[a].load (std::memory_order_relaxed), d = sh.aDst[a].load (std::memory_order_relaxed);
        if (s < 0 || s >= S_Count || d < 0 || d >= kNumVoiceDests) continue;
        add[d] += sh.aAmt[a].load (std::memory_order_relaxed) * srcVal[s];
    }
    auto norm = [&] (int d) { return juce::jlimit (0.0f, 1.0f, bp.destNorm[(size_t) d] + add[d]); };
    auto eff = [&] (int d)
    {
        const auto& r = (*ctx.ranges)[(size_t) d];
        const float n = norm (d);
        return r.interval > 0.0f ? r.start + (r.end - r.start) * n : r.convertFrom0to1 (n);   // keep stepped params smooth under modulation
    };

    if (ctx.lead)
    {
        for (size_t s = 0; s < (size_t) kNumMods; ++s)
        {
            const bool isEnv = s == 0 || bp.slot[s].type == 0;
            sh.uiStage[s].store (isEnv ? (int) env[s].stage : -2);
            sh.uiProg[s].store (env[s].progress);
            sh.uiLfoPhase[s].store (lfo[s].phase);
            sh.uiVal[s].store (srcVal[s]);
        }
        for (size_t p = 0; p < (size_t) kNumPerf; ++p) { sh.uiPerfIdx[p].store (perf[p].index); sh.uiPerfPhase[p].store (perf[p].phase); }
        for (int d = 0; d < kNumVoiceDests; ++d) sh.uiDest[d].store (norm (d));
    }

    auto setRamp = [&] (Ramp& r, float t) { if (firstControl) r.snap (t); r.set (t, c); };

    // oscillators
    float baseFreq;
    {
        const int i = juce::jlimit (0, 126, (int) std::floor (curNote));
        const float fr = curNote - (float) i;
        const float f0 = sh.tuning[i].load (std::memory_order_relaxed), f1 = sh.tuning[i + 1].load (std::memory_order_relaxed);
        baseFreq = f0 * std::pow (f1 / f0, juce::jlimit (0.0f, 1.0f, fr));
    }
    const float pitchSemis = eff (D_PITCH) + ctx.pitchBend * (float) bp.bendRange;
    auto setupOsc = [&] (Osc& o, float semis, int uni, float detuneCents)
    {
        o.n = juce::jlimit (1, 8, uni);
        const float freq = juce::jlimit (4.0f, sr * 0.45f, baseFreq * std::exp2 ((semis + pitchSemis) / 12.0f));
        for (int u = 0; u < o.n; ++u)
        {
            const float cents = o.n > 1 ? detuneCents * ((float) u / (float) (o.n - 1) * 2.0f - 1.0f) : 0.0f;
            o.inc[(size_t) u] = freq * std::exp2 (cents / 1200.0f) / sr;
        }
        o.level = Wavetable::levelForFrequency (freq * std::exp2 (detuneCents / 1200.0f), sr);
        o.gain = 1.0f / std::sqrt ((float) o.n);
    };
    setupOsc (osc1, eff (D_O1_PITCH) + eff (D_O1_FINE) / 100.0f, bp.uni1, eff (D_O1_DETUNE));
    setupOsc (osc2, eff (D_O2_PITCH) + eff (D_O2_FINE) / 100.0f, bp.uni2, eff (D_O2_DETUNE));
    wt1 = sh.tables[juce::jlimit (0, kNumTableSlots - 1, bp.wt1)].load();
    wt2 = sh.tables[juce::jlimit (0, kNumTableSlots - 1, bp.wt2)].load();
    setRamp (pos1, eff (D_O1_POS)); setRamp (pos2, eff (D_O2_POS));
    setRamp (lvl1, eff (D_O1_LEVEL)); setRamp (lvl2, eff (D_O2_LEVEL));
    setRamp (pm1, eff (D_O1_PM)); setRamp (pm2, eff (D_O2_PM));
    setRamp (fold1, eff (D_O1_FOLD)); setRamp (fold2, eff (D_O2_FOLD));
    setRamp (nzLvl, eff (D_NZ_LEVEL));

    // noise colour: <0.5 low-pass, >0.5 high-pass
    noiseKind = bp.noiseType;
    {
        const float col = eff (D_NZ_COLOR);
        float fc;
        if (col < 0.5f) { noiseColorMode = 0; fc = 100.0f * std::pow (200.0f, col * 2.0f); }
        else { noiseColorMode = 1; fc = 20.0f * std::pow (500.0f, (col - 0.5f) * 2.0f); }
        noiseCoef = 1.0f - std::exp (-2.0f * kPi * juce::jmin (fc, sr * 0.45f) / sr);
        if (col > 0.495f && col < 0.505f) noiseColorMode = 2;   // neutral
    }

    // filters
    const float ktr1 = std::exp2 (bp.f1Ktr * (curNote - 60.0f) / 12.0f), ktr2 = std::exp2 (bp.f2Ktr * (curNote - 60.0f) / 12.0f);
    filt1.setParams (bp.f1Model, bp.f1Mode, eff (D_F1_CUT) * ktr1, eff (D_F1_RES), eff (D_F1_DRIVE));
    filt2.setParams (bp.f2Model, bp.f2Mode, eff (D_F2_CUT) * ktr2, eff (D_F2_RES), eff (D_F2_DRIVE));

    insType = bp.insType;
    setRamp (insDrive, eff (D_INS_DRIVE)); setRamp (insMix, eff (D_INS_MIX));
    setRamp (fbAmt, eff (D_AMP_FB));

    // amp
    {
        const float velScale = 1.0f - bp.velSens + bp.velSens * velocity;
        const float g = srcVal[0] * eff (D_AMP_LEVEL) * velScale * 1.414f;
        const float angle = (eff (D_AMP_PAN) + 1.0f) * kPi * 0.25f;
        setRamp (panL, g * std::cos (angle)); setRamp (panR, g * std::sin (angle));
    }

    for (int s = 0; s < kRouteSrc; ++s)
        for (int d = 0; d < kRouteDst; ++d)
            routeG[s][d] = routeAllowed (s, d) ? sh.routeGain[s][d].load (std::memory_order_relaxed) : 0.0f;

    firstControl = false;
}

void Voice::render (float* left, float* right, int numSamples, const RenderContext& ctx)
{
    if (!active) return;
    const float dtPerSample = 1.0f / ctx.sampleRate;
    int done = 0;
    while (done < numSamples)
    {
        const int c = juce::jmin (kCtl, numSamples - done);
        control ((float) c * dtPerSample, c, ctx);

        bool hasIn[kRouteDst];
        for (int d = 0; d < kRouteDst; ++d)
        {
            hasIn[d] = false;
            for (int s = 0; s < kRouteSrc; ++s) if (routeG[s][d] > 0.0f) hasIn[d] = true;
        }

        for (int i = 0; i < c; ++i)
        {
            const float l1 = lvl1.next(), l2 = lvl2.next();
            const float r1 = oscSample (osc1, wt1, pos1.next(), pm1.next() * lastOsc2 * 0.75f, fold1.next());
            const float r2 = oscSample (osc2, wt2, pos2.next(), pm2.next() * r1 * 0.75f, fold2.next());
            lastOsc2 = r2;

            // noise
            noiseRng = noiseRng * 1664525u + 1013904223u;
            const float w = (float) (noiseRng >> 8) / 8388608.0f - 1.0f;
            float n0 = w;
            switch (noiseKind)
            {
                case 1:
                    pink[0] = 0.99886f * pink[0] + w * 0.0555179f; pink[1] = 0.99332f * pink[1] + w * 0.0750759f;
                    pink[2] = 0.96900f * pink[2] + w * 0.1538520f; pink[3] = 0.86650f * pink[3] + w * 0.3104856f;
                    pink[4] = 0.55000f * pink[4] + w * 0.5329522f; pink[5] = -0.7616f * pink[5] - w * 0.0168980f;
                    n0 = (pink[0] + pink[1] + pink[2] + pink[3] + pink[4] + pink[5] + pink[6] + w * 0.5362f) * 0.11f;
                    pink[6] = w * 0.115926f; break;
                case 2: brown = (brown + 0.02f * w) / 1.02f; n0 = brown * 3.5f; break;
                case 3: if (std::abs (w) > 0.996f) crackle = w * 3.0f; crackle *= 0.85f; n0 = crackle; break;
                default: break;
            }
            if (noiseColorMode != 2) { noiseLp += noiseCoef * (n0 - noiseLp); n0 = noiseColorMode == 0 ? noiseLp : n0 - noiseLp; }

            float s[kRouteSrc];
            s[N_Osc1] = r1 * l1; s[N_Osc2] = r2 * l2; s[N_Noise] = n0 * nzLvl.next();
            const float fb = fbAmt.next() * std::tanh (outPrev);

            float in1 = 0.0f;
            for (int k = 0; k < 3; ++k) in1 += routeG[k][0] * s[k];
            if (hasIn[0]) in1 += fb;
            s[N_Filt1] = hasIn[0] ? filt1.process (in1) : 0.0f;

            float in2 = 0.0f;
            for (int k = 0; k < 4; ++k) in2 += routeG[k][1] * s[k];
            s[N_Filt2] = hasIn[1] ? filt2.process (in2) : 0.0f;

            float inI = 0.0f;
            for (int k = 0; k < 5; ++k) inI += routeG[k][2] * s[k];
            if (hasIn[2] && !hasIn[0]) inI += fb;
            s[N_Insert] = hasIn[2] ? insertFx (inI, insDrive.next(), insMix.next(), insType, crushHold, crushCount) : 0.0f;
            if (!hasIn[2]) { insDrive.next(); insMix.next(); }

            float out = 0.0f;
            for (int k = 0; k < 6; ++k) out += routeG[k][3] * s[k];
            if (!std::isfinite (out)) { out = 0.0f; filt1.reset(); filt2.reset(); }
            outPrev = out;
            left[done + i] += out * panL.next();
            right[done + i] += out * panR.next();

            for (int k = 0; k < kRouteSrc; ++k) peak[k] = juce::jmax (peak[k], std::abs (s[k]));
            peak[N_Out] = juce::jmax (peak[N_Out], std::abs (out));
        }
        done += c;
    }
    if (!env[0].active()) { active = false; note = -1; }
}

// =============================================================================================
// Master effects
// =============================================================================================
void MasterFx::prepare (double sr, int)
{
    sampleRate = sr;
    const int dlySize = (int) (sr * 2.1) + 16;
    for (int c = 0; c < 2; ++c) { dlyBuf[c].assign ((size_t) dlySize, 0.0f); chorusBuf[c].assign (4096, 0.0f); }
    reverb.setSampleRate (sr);
    reset();
}

void MasterFx::reset()
{
    for (auto& ch : chorusBuf) std::fill (ch.begin(), ch.end(), 0.0f);
    for (auto& ch : dlyBuf) std::fill (ch.begin(), ch.end(), 0.0f);
    chorusPos = dlyPos = 0; chorusPhase = 0.0f; dlyLpL = dlyLpR = 0.0f; dlyLen = 0.0f;
    for (auto& c : eq) for (auto& f : c) f.reset();
    for (auto& l : lastEq) l = -999.0f;
    reverb.reset();
    dcX[0] = dcX[1] = dcY[0] = dcY[1] = 0.0f;
}

void MasterFx::process (float* left, float* right, int n, const Params& p)
{
    float* ch[2] = { left, right };

    // DC blocker, then EQ
    for (int c = 0; c < 2; ++c)
        for (int i = 0; i < n; ++i)
        {
            const float x = ch[c][i];
            const float y = x - dcX[c] + 0.995f * dcY[c];
            dcX[c] = x; dcY[c] = y; ch[c][i] = y;
        }

    const float eqNow[7] = { p.eqLoG, p.eqLoF, p.eqMidF, p.eqMidG, p.eqMidQ, p.eqHiG, p.eqHiF };
    bool changed = false;
    for (int i = 0; i < 7; ++i) if (std::abs (eqNow[i] - lastEq[i]) > 1.0e-4f) changed = true;
    const bool eqOn = std::abs (p.eqLoG) > 0.05f || std::abs (p.eqMidG) > 0.05f || std::abs (p.eqHiG) > 0.05f;
    if (changed && eqOn)
    {
        auto lo = juce::dsp::IIR::Coefficients<float>::makeLowShelf (sampleRate, p.eqLoF, 0.707f, juce::Decibels::decibelsToGain (p.eqLoG));
        auto mid = juce::dsp::IIR::Coefficients<float>::makePeakFilter (sampleRate, p.eqMidF, p.eqMidQ, juce::Decibels::decibelsToGain (p.eqMidG));
        auto hi = juce::dsp::IIR::Coefficients<float>::makeHighShelf (sampleRate, juce::jmin (p.eqHiF, (float) sampleRate * 0.45f), 0.707f, juce::Decibels::decibelsToGain (p.eqHiG));
        for (int c = 0; c < 2; ++c) { eq[c][0].coefficients = lo; eq[c][1].coefficients = mid; eq[c][2].coefficients = hi; }
        for (int i = 0; i < 7; ++i) lastEq[i] = eqNow[i];
    }
    if (eqOn && eq[0][0].coefficients != nullptr)
        for (int c = 0; c < 2; ++c)
            for (int i = 0; i < n; ++i)
                ch[c][i] = eq[c][2].processSample (eq[c][1].processSample (eq[c][0].processSample (ch[c][i])));

    // distortion
    if (p.distMix > 0.001f)
    {
        const float d = 1.0f + p.distDrive * 12.0f;
        for (int c = 0; c < 2; ++c)
            for (int i = 0; i < n; ++i) ch[c][i] = ch[c][i] * (1.0f - p.distMix) + std::tanh (ch[c][i] * d) * 0.9f * p.distMix;
    }

    // chorus
    if (p.choMix > 0.001f)
    {
        const float inc = p.choRate / (float) sampleRate;
        for (int i = 0; i < n; ++i)
        {
            for (int c = 0; c < 2; ++c) chorusBuf[c][(size_t) chorusPos] = ch[c][i];
            for (int c = 0; c < 2; ++c)
            {
                const float lfo = std::sin (juce::MathConstants<float>::twoPi * (chorusPhase + (c == 0 ? 0.0f : 0.25f)));
                const float dly = (0.012f + p.choDepth * 0.006f * lfo) * (float) sampleRate;
                float rp = (float) chorusPos - dly; while (rp < 0.0f) rp += 4096.0f;
                const int i0 = (int) rp & 4095, i1 = (i0 + 1) & 4095; const float fr = rp - std::floor (rp);
                const float wet = chorusBuf[c][(size_t) i0] * (1.0f - fr) + chorusBuf[c][(size_t) i1] * fr;
                ch[c][i] = ch[c][i] * (1.0f - 0.4f * p.choMix) + wet * 0.7f * p.choMix;
            }
            chorusPos = (chorusPos + 1) & 4095;
            chorusPhase += inc; if (chorusPhase >= 1.0f) chorusPhase -= 1.0f;
        }
    }

    // stereo delay (cross-fed feedback)
    if (p.dlyMix > 0.001f)
    {
        const int size = (int) dlyBuf[0].size();
        const float target = juce::jlimit (1.0f, (float) size - 4.0f, p.dlyMs * 0.001f * (float) sampleRate);
        if (dlyLen < 1.0f) dlyLen = target;
        for (int i = 0; i < n; ++i)
        {
            dlyLen += (target - dlyLen) * 0.0015f;
            float rp = (float) dlyPos - dlyLen; while (rp < 0.0f) rp += (float) size;
            const int i0 = (int) rp % size, i1 = (i0 + 1) % size; const float fr = rp - std::floor (rp);
            const float dl = dlyBuf[0][(size_t) i0] * (1.0f - fr) + dlyBuf[0][(size_t) i1] * fr;
            const float dr = dlyBuf[1][(size_t) i0] * (1.0f - fr) + dlyBuf[1][(size_t) i1] * fr;
            dlyLpL += 0.45f * (dl - dlyLpL); dlyLpR += 0.45f * (dr - dlyLpR);
            dlyBuf[0][(size_t) dlyPos] = ch[0][i] + p.dlyFb * dlyLpR;
            dlyBuf[1][(size_t) dlyPos] = ch[1][i] + p.dlyFb * dlyLpL;
            ch[0][i] += dl * p.dlyMix; ch[1][i] += dr * p.dlyMix;
            dlyPos = (dlyPos + 1) % size;
        }
    }

    // reverb
    if (p.revMix > 0.001f)
    {
        juce::Reverb::Parameters rp;
        rp.roomSize = p.revSize; rp.damping = p.revDamp; rp.wetLevel = p.revMix * 0.35f; rp.dryLevel = 1.0f - p.revMix * 0.5f; rp.width = 1.0f; rp.freezeMode = 0.0f;
        reverb.setParameters (rp);
        reverb.processStereo (left, right, n);
    }

    // master volume + soft safety clip
    const float g = p.master * p.master * 2.0f;
    for (int c = 0; c < 2; ++c)
        for (int i = 0; i < n; ++i)
        {
            float x = ch[c][i] * g;
            const float ax = std::abs (x);
            if (ax > 0.95f) x = (x < 0 ? -1.0f : 1.0f) * (0.95f + 0.05f * std::tanh ((ax - 0.95f) / 0.05f));
            ch[c][i] = std::isfinite (x) ? x : 0.0f;
        }
}

// =============================================================================================
// Engine
// =============================================================================================
void SynthEngine::prepare (double sr, int maxBlock)
{
    sampleRate = sr;
    for (auto& v : voices) v.prepare (sr);
    fx.prepare (sr, maxBlock);
    voiceBuf.setSize (2, juce::jmax (maxBlock, 64));
    heldNotes.clear(); heldNotes.reserve (128);
}

void SynthEngine::reset()
{
    for (auto& v : voices) v.kill();
    fx.reset(); heldNotes.clear(); sustainDown = false; haveLastNote = false;
}

Voice* SynthEngine::findFreeVoice (int limit)
{
    limit = juce::jlimit (1, kMaxVoices, limit);
    for (int i = 0; i < limit; ++i) if (!voices[(size_t) i].isActive()) return &voices[(size_t) i];
    Voice* best = nullptr;
    for (int i = 0; i < limit; ++i)   // oldest voice whose key is up
        if (voices[(size_t) i].isReleasing() && (best == nullptr || voices[(size_t) i].age < best->age)) best = &voices[(size_t) i];
    if (best) return best;
    for (int i = 0; i < limit; ++i)
        if (best == nullptr || voices[(size_t) i].age < best->age) best = &voices[(size_t) i];
    return best;
}

void SynthEngine::noteOn (int note, float vel, const BlockParams& bp)
{
    if (bp.voiceMode != 0) { monoNoteOn (note, vel, bp); return; }
    if (auto* v = findFreeVoice (bp.voices))
    {
        const float startNote = haveLastNote && bp.glide > 0.001f ? lastNote : (float) note;
        v->start (note, vel, startNote, true, bp, seedCounter++);
        v->age = ++ageCounter;
    }
    lastNote = (float) note; haveLastNote = true;
}

void SynthEngine::noteOff (int note)
{
    for (auto& v : voices)
        if (v.isActive() && v.note == note && v.keyHeld)
        {
            if (sustainDown) { v.keyHeld = false; v.sustained = true; }
            else v.release();
        }
}

void SynthEngine::monoNoteOn (int note, float vel, const BlockParams& bp)
{
    heldNotes.erase (std::remove (heldNotes.begin(), heldNotes.end(), note), heldNotes.end());
    heldNotes.push_back (note);
    auto& v = voices[0];
    for (size_t i = 1; i < voices.size(); ++i) if (voices[i].isActive()) voices[i].release();   // switching from poly
    const bool legato = bp.voiceMode == 2 && v.isActive() && v.keyHeld;
    if (legato)
    {
        const float from = (float) v.note;
        v.changeNote (note, vel);
        (void) from;
    }
    else
    {
        const float startNote = haveLastNote && bp.glide > 0.001f ? lastNote : (float) note;
        v.start (note, vel, startNote, true, bp, seedCounter++);
        v.age = ++ageCounter;
    }
    lastNote = (float) note; haveLastNote = true;
}

void SynthEngine::monoNoteOff (int note, const BlockParams& bp)
{
    heldNotes.erase (std::remove (heldNotes.begin(), heldNotes.end(), note), heldNotes.end());
    auto& v = voices[0];
    if (!v.isActive()) return;
    if (!heldNotes.empty())
    {
        v.changeNote (heldNotes.back(), 1.0f);
        lastNote = (float) heldNotes.back();
        (void) bp;
    }
    else if (v.note == note)
    {
        if (sustainDown) { v.keyHeld = false; v.sustained = true; } else v.release();
    }
}

void SynthEngine::handleMidi (const juce::MidiMessage& m, const BlockParams& bp)
{
    if (m.isNoteOn())
        noteOn (m.getNoteNumber(), m.getFloatVelocity(), bp);
    else if (m.isNoteOff())
    {
        if (bp.voiceMode != 0) monoNoteOff (m.getNoteNumber(), bp); else noteOff (m.getNoteNumber());
    }
    else if (m.isAllNotesOff() || m.isAllSoundOff())
    {
        for (auto& v : voices) { if (m.isAllSoundOff()) v.kill(); else v.release(); }
        heldNotes.clear();
    }
    else if (m.isController())
    {
        if (m.getControllerNumber() == 1) modWheel = (float) m.getControllerValue() / 127.0f;
        else if (m.getControllerNumber() == 64)
        {
            const bool down = m.getControllerValue() >= 64;
            if (sustainDown && !down) for (auto& v : voices) if (v.sustained) v.release();
            sustainDown = down;
        }
    }
    else if (m.isPitchWheel()) pitchBend = ((float) m.getPitchWheelValue() - 8192.0f) / 8192.0f;
    else if (m.isChannelPressure()) aftertouch = (float) m.getChannelPressureValue() / 127.0f;
}

float SynthEngine::modulatedGlobal (int dest, const BlockParams& bp, const std::array<juce::NormalisableRange<float>, D_COUNT>& ranges, const float* src) const
{
    float n = bp.destNorm[(size_t) dest];
    const int na = juce::jmin (kMaxAssign, shared.numAssign.load (std::memory_order_relaxed));
    for (int a = 0; a < na; ++a)
        if (shared.aDst[a].load (std::memory_order_relaxed) == dest)
        {
            const int s = shared.aSrc[a].load (std::memory_order_relaxed);
            if (s >= 0 && s < S_Count && isGlobalSource (s)) n += shared.aAmt[a].load (std::memory_order_relaxed) * src[s];
        }
    n = juce::jlimit (0.0f, 1.0f, n);
    shared.uiDest[dest].store (n, std::memory_order_relaxed);
    return ranges[(size_t) dest].convertFrom0to1 (n);
}

void SynthEngine::process (juce::AudioBuffer<float>& out, const juce::MidiBuffer& midi, const BlockParams& bp,
                           const std::array<juce::NormalisableRange<float>, D_COUNT>& ranges)
{
    const int total = out.getNumSamples();
    out.clear();
    if (out.getNumChannels() < 2) return;
    if (voiceBuf.getNumSamples() < total) voiceBuf.setSize (2, total, false, false, true);

    RenderContext ctx;
    ctx.bp = &bp; ctx.shared = &shared; ctx.ranges = &ranges; ctx.sampleRate = (float) sampleRate;

    // global modulation sources (macros and wheels) for the master effects
    float srcG[S_Count] = {};
    for (int i = 0; i < kNumMacros; ++i) srcG[S_Macro1 + i] = bp.macro[(size_t) i];
    auto buildFx = [&]
    {
        srcG[S_ModWheel] = modWheel; srcG[S_Aftertouch] = aftertouch; srcG[S_PitchBend] = pitchBend;
        MasterFx::Params fp;
        fp.eqLoG = modulatedGlobal (D_EQ_LO_GAIN, bp, ranges, srcG); fp.eqLoF = bp.eqLoFreq;
        fp.eqMidF = modulatedGlobal (D_EQ_MID_FREQ, bp, ranges, srcG); fp.eqMidG = modulatedGlobal (D_EQ_MID_GAIN, bp, ranges, srcG); fp.eqMidQ = bp.eqMidQ;
        fp.eqHiG = modulatedGlobal (D_EQ_HI_GAIN, bp, ranges, srcG); fp.eqHiF = bp.eqHiFreq;
        fp.dlyMs = bp.dlySync ? (float) (60000.0 / bp.bpm) * divisionBeats (bp.dlyDiv) : bp.dlyTimeMs;
        fp.dlyFb = modulatedGlobal (D_DLY_FB, bp, ranges, srcG); fp.dlyMix = modulatedGlobal (D_DLY_MIX, bp, ranges, srcG);
        fp.revSize = modulatedGlobal (D_REV_SIZE, bp, ranges, srcG); fp.revDamp = bp.revDamp; fp.revMix = modulatedGlobal (D_REV_MIX, bp, ranges, srcG);
        fp.choRate = modulatedGlobal (D_CHO_RATE, bp, ranges, srcG); fp.choDepth = modulatedGlobal (D_CHO_DEPTH, bp, ranges, srcG);
        fp.choMix = modulatedGlobal (D_CHO_MIX, bp, ranges, srcG);
        fp.distDrive = modulatedGlobal (D_DIST_DRIVE, bp, ranges, srcG); fp.distMix = modulatedGlobal (D_DIST_MIX, bp, ranges, srcG);
        fp.master = modulatedGlobal (D_MASTER_VOL, bp, ranges, srcG);
        return fp;
    };

    for (auto& v : voices) for (auto& p : v.peak) p = 0.0f;

    int pos = 0;
    auto renderSegment = [&] (int start, int len)
    {
        if (len <= 0) return;
        voiceBuf.clear (0, len);   // clears the first len samples of every channel
        Voice* lead = nullptr;
        for (auto& v : voices) if (v.isActive() && (lead == nullptr || v.age > lead->age)) lead = &v;
        ctx.modWheel = modWheel; ctx.aftertouch = aftertouch; ctx.pitchBend = pitchBend;
        for (auto& v : voices)
        {
            ctx.lead = &v == lead;
            v.render (voiceBuf.getWritePointer (0), voiceBuf.getWritePointer (1), len, ctx);
        }
        const auto fp = buildFx();
        fx.process (voiceBuf.getWritePointer (0), voiceBuf.getWritePointer (1), len, fp);
        out.copyFrom (0, start, voiceBuf, 0, 0, len);
        out.copyFrom (1, start, voiceBuf, 1, 0, len);
    };

    for (const auto meta : midi)
    {
        const int evPos = juce::jlimit (pos, total, meta.samplePosition);
        renderSegment (pos, evPos - pos);
        pos = evPos;
        handleMidi (meta.getMessage(), bp);
    }
    renderSegment (pos, total - pos);

    // meters and activity
    int count = 0;
    float nodePk[N_Count] = {};
    for (auto& v : voices) { if (v.isActive()) ++count; for (int k = 0; k < N_Count; ++k) nodePk[k] = juce::jmax (nodePk[k], v.peak[k]); }
    shared.activeVoices.store (count);
    for (int k = 0; k < N_Count; ++k)
        shared.nodePeak[k].store (juce::jmax (nodePk[k], shared.nodePeak[k].load() * 0.92f));
    shared.outPeakL.store (juce::jmax (out.getMagnitude (0, 0, total), shared.outPeakL.load() * 0.93f));
    shared.outPeakR.store (juce::jmax (out.getMagnitude (1, 0, total), shared.outPeakR.load() * 0.93f));
    shared.wheelPitch.store (pitchBend); shared.wheelMod.store (modWheel); shared.wheelAftertouch.store (aftertouch);
    if (count == 0) for (int s = 0; s < kNumMods; ++s) shared.uiStage[s].store (-1);
}
} // namespace psxl
