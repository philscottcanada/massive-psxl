#pragma once
#include "../Params.h"
#include <cmath>

namespace psxl
{
// ADSR with delay and hold. Stepped at control rate with dt in seconds.
struct Envelope
{
    enum Stage { Idle = 0, Delay, Attack, Hold, Decay, Sustain, Release };
    Stage stage = Idle;
    float value = 0.0f, timer = 0.0f, startValue = 0.0f, stageStart = 0.0f, progress = 0.0f;
    bool oneShot = false, gate = false;

    void noteOn (const SlotParams& p)
    {
        gate = true; oneShot = p.oneShot; startValue = value;
        timer = 0.0f;
        if (p.dly > 0.0005f) stage = Delay; else enterAttack();
    }
    void noteOff()
    {
        gate = false;
        if (!oneShot && stage != Idle) { stage = Release; stageStart = value; progress = 0.0f; }
    }
    bool active() const { return stage != Idle; }

    float step (float dt, const SlotParams& p)
    {
        switch (stage)
        {
            case Idle: value = 0.0f; progress = 0.0f; break;
            case Delay:
                timer += dt; progress = p.dly > 0 ? timer / p.dly : 1.0f;
                if (timer >= p.dly) enterAttack();
                break;
            case Attack:
            {
                const float t = juce::jmax (p.att, 0.0005f);
                timer += dt; progress = timer / t;
                value = startValue + (1.0f - startValue) * juce::jmin (1.0f, progress);
                if (timer >= t) { value = 1.0f; timer = 0.0f; if (p.hold > 0.0005f) stage = Hold; else enterDecay(); }
                break;
            }
            case Hold:
                timer += dt; progress = timer / p.hold;
                if (timer >= p.hold) enterDecay();
                break;
            case Decay:
            {
                const float coef = std::exp (-6.9f * dt / juce::jmax (p.dec, 0.001f));
                value = p.sus + (value - p.sus) * coef;
                const float span = juce::jmax (1.0e-4f, stageStart - p.sus);
                progress = juce::jlimit (0.0f, 1.0f, 1.0f - (value - p.sus) / span);
                if (value - p.sus < 0.001f)
                {
                    value = p.sus; progress = 0.0f;
                    if (oneShot || !gate) { stage = Release; stageStart = value; }   // one-shot envelopes run straight into release
                    else stage = Sustain;
                }
                break;
            }
            case Sustain:
                value = p.sus; progress = 0.0f;
                if (!gate && !oneShot) { stage = Release; stageStart = value; }
                break;
            case Release:
            {
                const float coef = std::exp (-6.9f * dt / juce::jmax (p.rel, 0.001f));
                value *= coef;
                progress = juce::jlimit (0.0f, 1.0f, stageStart > 1.0e-5f ? 1.0f - value / stageStart : 1.0f);
                if (value < 0.0005f) { value = 0.0f; stage = Idle; }
                break;
            }
        }
        return value * p.level;
    }

private:
    void enterAttack() { stage = Attack; timer = 0.0f; startValue = value; }
    void enterDecay() { stage = Decay; timer = 0.0f; stageStart = value; }
};

struct Lfo
{
    float phase = 0.0f, fadeTimer = 0.0f, held = 0.0f, smoothTarget = 0.0f, smoothValue = 0.0f;
    juce::uint32 rng = 12345u;

    float nextRandom() { rng = rng * 1664525u + 1013904223u; return (float) (rng >> 8) / 8388608.0f - 1.0f; }

    void reset (const SlotParams& p, juce::uint32 seed)
    {
        phase = p.phase; fadeTimer = 0.0f; rng = seed * 2654435761u + 1u; held = nextRandom();
        smoothValue = nextRandom(); smoothTarget = nextRandom();
    }

    // returns bipolar -1..1 (or 0..1 when unipolar) scaled by level and fade-in
    float step (float dt, float rateHz, const SlotParams& p)
    {
        const float prev = phase;
        phase += rateHz * dt;
        const bool wrapped = phase >= 1.0f;
        if (wrapped) { phase -= std::floor (phase); held = nextRandom(); smoothValue = smoothTarget; smoothTarget = nextRandom(); }
        (void) prev;
        float v = 0.0f;
        switch (p.shape)
        {
            case 0: v = std::sin (juce::MathConstants<float>::twoPi * phase); break;
            case 1: v = 1.0f - 4.0f * std::abs (phase - 0.5f); break;
            case 2: v = 2.0f * phase - 1.0f; break;
            case 3: v = 1.0f - 2.0f * phase; break;
            case 4: v = phase < 0.5f ? 1.0f : -1.0f; break;
            case 5: v = held; break;
            default: { const float x = phase * phase * (3.0f - 2.0f * phase); v = smoothValue + (smoothTarget - smoothValue) * x; break; }
        }
        fadeTimer += dt;
        const float fade = p.fade > 0.001f ? juce::jmin (1.0f, fadeTimer / p.fade) : 1.0f;
        if (!p.bipolar) v = 0.5f * (v + 1.0f);
        return v * p.level * fade;
    }
};

struct Performer
{
    float phase = 0.0f;      // 0..1 within the current step
    int index = 0;
    float value = 0.0f;

    void reset() { phase = 0.0f; index = 0; }

    float step (float dt, float stepsPerSecond, const PerfParams& p, const std::atomic<float>* steps)
    {
        phase += stepsPerSecond * dt;
        while (phase >= 1.0f) { phase -= 1.0f; index = (index + 1) % juce::jmax (1, p.steps); }
        const float cur = steps[index].load (std::memory_order_relaxed);
        if (p.smooth <= 0.001f) { value = cur; return value; }
        const float next = steps[(index + 1) % juce::jmax (1, p.steps)].load (std::memory_order_relaxed);
        // glide across the final part of the step; smooth=1 glides across the whole step
        const float x = juce::jlimit (0.0f, 1.0f, (phase - (1.0f - p.smooth)) / juce::jmax (0.001f, p.smooth));
        value = cur + (next - cur) * (x * x * (3.0f - 2.0f * x));
        return value;
    }
};
} // namespace psxl
