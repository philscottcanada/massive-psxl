#pragma once
#include <juce_core/juce_core.h>
#include <algorithm>
#include <array>
#include <cmath>
#include <vector>

namespace psxl
{
// One voice filter. Four models: 0 Ladder, 1 State Variable, 2 Comb, 3 Formant.
// cutoff is in Hz, res and drive are 0..1.
class VoiceFilter
{
public:
    void prepare (double sr) { sampleRate = (float) sr; comb.assign (8192, 0.0f); reset(); }
    void reset()
    {
        s1 = s2 = s3 = s4 = y4 = 0.0f; ic1 = ic2 = 0.0f; fbLp = 0.0f; wpos = 0;
        std::fill (comb.begin(), comb.end(), 0.0f);
        for (auto& f : formIc) f = { 0.0f, 0.0f };
    }

    void setParams (int newModel, int newMode, float cutoffHz, float resonance, float driveAmt)
    {
        if (newModel != model) { model = newModel; }
        mode = newMode;
        res = juce::jlimit (0.0f, 1.0f, resonance);
        drive = 1.0f + juce::jlimit (0.0f, 1.0f, driveAmt) * 7.0f;
        cutoff = juce::jlimit (16.0f, sampleRate * 0.45f, cutoffHz);
        switch (model)
        {
            case 0: { g = std::tan (juce::MathConstants<float>::pi * cutoff / sampleRate); G = g / (1.0f + g); k = res * 3.95f; break; }
            case 1: { g = std::tan (juce::MathConstants<float>::pi * cutoff / sampleRate); kk = 2.0f - 1.96f * res; a1 = 1.0f / (1.0f + g * (g + kk)); a2 = g * a1; a3 = g * a2; break; }
            case 2: { combDelay = juce::jlimit (2.0f, 4000.0f, sampleRate / cutoff); break; }
            default: setFormants(); break;
        }
    }

    inline float process (float in)
    {
        in = std::tanh (in * drive) / std::tanh (drive);   // drive stage (unity at small signal)
        switch (model)
        {
            case 0: return ladder (in);
            case 1: return svf (in);
            case 2: return combFilter (in);
            default: return formant (in);
        }
    }

private:
    inline float ladder (float x)
    {
        const float u = std::tanh ((x * (1.0f + k * 0.4f)) - k * y4);
        auto stage = [this] (float v, float& s) { const float vv = (v - s) * G; const float y = vv + s; s = y + vv; return y; };
        const float y1 = stage (u, s1), y2 = stage (y1, s2), y3 = stage (y2, s3);
        y4 = stage (y3, s4);
        switch (mode)
        {
            case 0: return y4;
            case 1: return y2;
            case 2: return (y2 - y4) * 2.0f;
            default: return u - 4.0f * y1 + 6.0f * y2 - 4.0f * y3 + y4;
        }
    }
    inline float svf (float x)
    {
        const float v3 = x - ic2;
        const float v1 = a1 * ic1 + a2 * v3;
        const float v2 = ic2 + a2 * ic1 + a3 * v3;
        ic1 = 2.0f * v1 - ic1; ic2 = 2.0f * v2 - ic2;
        switch (mode)
        {
            case 0: return v2;
            case 1: return v1 * kk;
            case 2: return x - kk * v1 - v2;
            default: return x - kk * v1;
        }
    }
    inline float combFilter (float x)
    {
        const float fbAmt = res * 0.97f;
        float rp = (float) wpos - combDelay; while (rp < 0.0f) rp += (float) comb.size();
        const int i0 = (int) rp; const float fr = rp - (float) i0;
        const float d = comb[(size_t) i0] * (1.0f - fr) + comb[(size_t) ((i0 + 1) % (int) comb.size())] * fr;
        float y;
        switch (mode)
        {
            case 0: y = x + fbAmt * d; break;
            case 1: y = x - fbAmt * d; break;
            case 2: y = 0.5f * (x + d); fbLp = 0; comb[(size_t) wpos] = x; wpos = (wpos + 1) % (int) comb.size(); return y;
            default: fbLp += 0.5f * (d - fbLp); y = x * 0.2f + fbAmt * fbLp; break;   // damped feedback (plucked string)
        }
        comb[(size_t) wpos] = std::tanh (y);
        wpos = (wpos + 1) % (int) comb.size();
        return y * (1.0f - 0.5f * fbAmt);
    }
    void setFormants()
    {
        static const float male[5][3] = { { 730, 1090, 2440 }, { 530, 1840, 2480 }, { 270, 2290, 3010 }, { 570, 840, 2410 }, { 300, 870, 2240 } };
        static const float female[5][3] = { { 850, 1220, 2810 }, { 610, 2330, 2990 }, { 310, 2790, 3310 }, { 590, 920, 2710 }, { 370, 950, 2670 } };
        const float pos = juce::jlimit (0.0f, 0.9999f, std::log (cutoff / 20.0f) / std::log (1000.0f)) * 4.0f;
        const int a = (int) pos; const float x = pos - (float) a;
        const float scale = mode == 2 ? 1.35f : (mode == 3 ? 0.7f : 1.0f);
        const float q = 4.0f + res * 24.0f;
        for (int f = 0; f < 3; ++f)
        {
            const auto& t = mode == 1 ? female : male;
            float freq = (t[a][f] * (1.0f - x) + t[juce::jmin (4, a + 1)][f] * x) * scale;
            if (mode == 3) freq *= (f == 1 ? 1.5f : 1.0f);
            freq = juce::jlimit (60.0f, sampleRate * 0.45f, freq);
            const float gg = std::tan (juce::MathConstants<float>::pi * freq / sampleRate);
            const float kq = 1.0f / q;
            formA1[(size_t) f] = 1.0f / (1.0f + gg * (gg + kq)); formA2[(size_t) f] = gg * formA1[(size_t) f]; formA3[(size_t) f] = gg * formA2[(size_t) f]; formK[(size_t) f] = kq;
        }
    }
    inline float formant (float x)
    {
        static const float gains[3] = { 1.0f, 0.7f, 0.45f };
        float out = 0.0f;
        for (size_t f = 0; f < 3; ++f)
        {
            auto& st = formIc[f];
            const float v3 = x - st[1];
            const float v1 = formA1[f] * st[0] + formA2[f] * v3;
            const float v2 = st[1] + formA2[f] * st[0] + formA3[f] * v3;
            st[0] = 2.0f * v1 - st[0]; st[1] = 2.0f * v2 - st[1];
            out += v1 * formK[f] * gains[f];
        }
        return out * 1.6f;
    }

    float sampleRate = 44100.0f, cutoff = 1000.0f, res = 0.0f, drive = 1.0f;
    int model = 0, mode = 0;
    // ladder
    float g = 0, G = 0, k = 0, s1 = 0, s2 = 0, s3 = 0, s4 = 0, y4 = 0;
    // svf
    float kk = 1, a1 = 0, a2 = 0, a3 = 0, ic1 = 0, ic2 = 0;
    // comb
    std::vector<float> comb; int wpos = 0; float combDelay = 100.0f, fbLp = 0.0f;
    // formant
    std::array<std::array<float, 2>, 3> formIc {};
    std::array<float, 3> formA1 {}, formA2 {}, formA3 {}, formK {};
};
} // namespace psxl
