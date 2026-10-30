#include "Wavetable.h"
#include "../Params.h"
#include <complex>

namespace psxl
{
using Frame = std::vector<float>;
constexpr int N = Wavetable::kFrameSize;
constexpr float kPi = juce::MathConstants<float>::pi;
constexpr float kTwoPi = juce::MathConstants<float>::twoPi;

static juce::dsp::FFT& fft()
{
    static juce::dsp::FFT f (11);   // 2^11 = 2048
    return f;
}

std::shared_ptr<Wavetable> Wavetable::fromFrames (const juce::String& name, const std::vector<Frame>& frames)
{
    auto wt = std::make_shared<Wavetable>();
    wt->name = name;
    wt->numFrames = juce::jlimit (1, kMaxFrames, (int) frames.size());
    for (auto& d : wt->data) d.assign ((size_t) wt->numFrames * N, 0.0f);

    std::vector<std::complex<float>> spec ((size_t) N), tmp ((size_t) N), out ((size_t) N);
    for (int f = 0; f < wt->numFrames; ++f)
    {
        for (int i = 0; i < N; ++i) tmp[(size_t) i] = { frames[(size_t) f][(size_t) i], 0.0f };
        fft().perform (tmp.data(), spec.data(), false);
        spec[0] = 0.0f;   // remove DC

        float gain = 1.0f;
        for (int level = 0; level < kMipLevels; ++level)
        {
            const int maxH = maxHarmonics (level);
            for (int k = 0; k < N; ++k)
            {
                const int h = k <= N / 2 ? k : N - k;
                tmp[(size_t) k] = h <= maxH ? spec[(size_t) k] : std::complex<float> (0.0f, 0.0f);
            }
            fft().perform (tmp.data(), out.data(), true);
            float* dst = wt->data[(size_t) level].data() + (size_t) f * N;
            if (level == 0)
            {
                float peak = 1.0e-6f;
                for (int i = 0; i < N; ++i) peak = juce::jmax (peak, std::abs (out[(size_t) i].real()));
                gain = 0.95f / peak;   // peak-normalise each frame using the full-bandwidth version
            }
            for (int i = 0; i < N; ++i) dst[i] = out[(size_t) i].real() * gain;
        }
    }
    return wt;
}

// ---------------------------------------------------------------------------------------------
// Factory wavetables. Each generator fills one single-cycle frame for morph position t in 0..1.
// ---------------------------------------------------------------------------------------------
static const char* const kBuiltinNames[kNumBuiltinTables] = {
    "Morph Basic", "Pulse Sweep", "Harmonic Tilt", "Vowel Choir", "Hard Sync",
    "FM Bells", "Drawbar Organ", "Glass Harmonics", "Digital Grit", "Fold Sweep" };

juce::String Wavetable::builtinName (int i) { return kBuiltinNames[juce::jlimit (0, kNumBuiltinTables - 1, i)]; }

// Additive helper: sum of sin(h*theta) * amp(h) for h = 1..maxH, evaluated via FFT-free direct sum
// restricted to a modest harmonic count (generation only runs once at startup).
template <typename AmpFn>
static Frame additive (int maxH, AmpFn amp, const float* phases = nullptr)
{
    std::vector<std::complex<float>> spec ((size_t) N, { 0.0f, 0.0f }), out ((size_t) N);
    for (int h = 1; h <= juce::jmin (maxH, N / 2 - 1); ++h)
    {
        // a * sin (h*theta + ph) == a * cos (h*theta + ph - pi/2)
        const float ph = (phases != nullptr ? phases[h % 200] : 0.0f) - kPi * 0.5f;
        const std::complex<float> c = amp (h) * std::complex<float> (std::cos (ph), std::sin (ph));   // amp may be negative
        spec[(size_t) h] = c;
        spec[(size_t) (N - h)] = std::conj (c);
    }
    fft().perform (spec.data(), out.data(), true);
    Frame fr ((size_t) N);
    for (int i = 0; i < N; ++i) fr[(size_t) i] = out[(size_t) i].real();
    return fr;
}

static float saw (float th) { return 1.0f - 2.0f * std::fmod (th / kTwoPi + 1.0f, 1.0f); }

std::shared_ptr<Wavetable> Wavetable::createBuiltin (int index)
{
    constexpr int F = 32;
    std::vector<Frame> frames;
    juce::Random rng (1234 + index);
    // random phases for the "grit" table are drawn once so every frame shares them
    std::array<float, 200> randPh {};
    for (auto& r : randPh) r = rng.nextFloat() * kTwoPi;

    for (int f = 0; f < F; ++f)
    {
        const float t = (float) f / (float) (F - 1);
        Frame fr;
        switch (index)
        {
            case 0: // sine -> triangle -> saw -> square
            {
                const float seg = t * 3.0f; const int s0 = juce::jmin (2, (int) seg); const float x = seg - (float) s0;
                auto coef = [] (int shape, int h) -> float {
                    switch (shape) {
                        case 0: return h == 1 ? 1.0f : 0.0f;
                        case 1: return (h & 1) ? ((((h - 1) / 2) & 1) ? -1.0f : 1.0f) * 8.0f / (kPi * kPi * (float) h * (float) h) : 0.0f;
                        case 2: return 2.0f / (kPi * (float) h);
                        default: return (h & 1) ? 4.0f / (kPi * (float) h) : 0.0f;
                    }
                };
                fr = additive (180, [&] (int h) { return coef (s0, h) * (1.0f - x) + coef (s0 + 1, h) * x; });
                break;
            }
            case 1: // pulse width sweep
            {
                const float w = 0.5f - 0.47f * t;
                fr.resize ((size_t) N);
                for (int i = 0; i < N; ++i) fr[(size_t) i] = ((float) i / (float) N) < w ? 1.0f : -1.0f;
                break;
            }
            case 2: // spectral tilt: from dull to bright
            {
                const float slope = 2.4f - 2.2f * t;
                fr = additive (200, [&] (int h) { return std::pow ((float) h, -slope); });
                break;
            }
            case 3: // vowel formants: a e i o u
            {
                static const float v[5][3] = { { 730, 1090, 2440 }, { 530, 1840, 2480 }, { 270, 2290, 3010 }, { 570, 840, 2410 }, { 300, 870, 2240 } };
                const float seg = t * 4.0f; const int a = juce::jmin (3, (int) seg); const float x = seg - (float) a;
                float fm[3]; for (int k = 0; k < 3; ++k) fm[k] = v[a][k] * (1.0f - x) + v[a + 1][k] * x;
                const float f0 = 110.0f;
                fr = additive (120, [&] (int h) {
                    const float fr0 = (float) h * f0; float g = 0.0f;
                    for (int k = 0; k < 3; ++k) { const float d = (fr0 - fm[k]) / (90.0f + 0.08f * fm[k]); g += std::exp (-d * d) * (k == 0 ? 1.0f : 0.6f / (float) k); }
                    return g / (float) h * (float) std::pow ((float) h, 0.6f);
                });
                break;
            }
            case 4: // hard sync sweep
            {
                const float ratio = 1.0f + 7.0f * t;
                fr.resize ((size_t) N);
                for (int i = 0; i < N; ++i) fr[(size_t) i] = saw (std::fmod (kTwoPi * (float) i / (float) N * ratio, kTwoPi));
                break;
            }
            case 5: // FM bells
            {
                const float idx = 0.2f + 6.0f * t; const float ratio = 1.0f + std::floor (t * 5.0f);   // integer ratios keep the cycle periodic
                fr.resize ((size_t) N);
                for (int i = 0; i < N; ++i) { const float th = kTwoPi * (float) i / (float) N; fr[(size_t) i] = std::sin (th + idx * std::sin (ratio * th)); }
                break;
            }
            case 6: // drawbar organ morphing through registrations
            {
                static const int hs[9] = { 1, 2, 3, 4, 6, 8, 10, 12, 16 };
                fr = additive (24, [&] (int h) {
                    float s = 0.0f;
                    for (int k = 0; k < 9; ++k) if (hs[k] == h) {
                        const float w = 0.5f + 0.5f * std::sin (kTwoPi * (t * (1.0f + 0.37f * (float) k) + 0.11f * (float) k));
                        s = 0.15f + w; }
                    return s;
                });
                break;
            }
            case 7: // glass: odd inharmonic-ish stack with moving peak
            {
                const float peak = 3.0f + 40.0f * t;
                fr = additive (160, [&] (int h) {
                    if (h % 2 == 0 && h > 2) return 0.0f;
                    const float d = ((float) h - peak) / 4.0f;
                    return (std::exp (-d * d) * 1.2f + 0.15f / (float) h);
                });
                break;
            }
            case 8: // digital grit: random-phase band, narrows and shifts
            {
                const int lo = 1 + (int) (t * 20.0f), hi = 24 + (int) (t * 150.0f);
                fr = additive (hi, [&] (int h) { return h >= lo ? 1.0f / std::sqrt ((float) h) : 0.0f; }, randPh.data());
                break;
            }
            default: // wavefold sweep
            {
                const float k = 0.5f + 7.0f * t;
                fr.resize ((size_t) N);
                for (int i = 0; i < N; ++i) { const float th = kTwoPi * (float) i / (float) N; fr[(size_t) i] = std::sin (k * std::sin (th) * kPi * 0.5f); }
                break;
            }
        }
        frames.push_back (std::move (fr));
    }
    return fromFrames (builtinName (index), frames);
}

// ---------------------------------------------------------------------------------------------
std::shared_ptr<Wavetable> Wavetable::fromAudio (const juce::String& name, const juce::AudioBuffer<float>& audio)
{
    const int len = audio.getNumSamples();
    if (len < 32) return nullptr;

    std::vector<float> mono ((size_t) len, 0.0f);
    for (int c = 0; c < audio.getNumChannels(); ++c)
        for (int i = 0; i < len; ++i) mono[(size_t) i] += audio.getSample (c, i) / (float) audio.getNumChannels();

    // Files that are whole multiples of 2048 are sliced directly; anything else is resampled so that
    // each ~2048-sample region becomes one frame (a short single-cycle file becomes one frame).
    const int numFrames = juce::jlimit (1, kMaxFrames, (int) std::round ((double) len / (double) N));
    std::vector<Frame> frames;
    for (int f = 0; f < numFrames; ++f)
    {
        const double start = (double) f * len / numFrames, span = (double) len / numFrames;
        Frame fr ((size_t) N);
        for (int i = 0; i < N; ++i)
        {
            const double pos = start + span * (double) i / (double) N;
            const int i0 = juce::jlimit (0, len - 1, (int) pos), i1 = juce::jmin (len - 1, i0 + 1);
            const float fr0 = (float) (pos - (double) i0);
            fr[(size_t) i] = mono[(size_t) i0] * (1.0f - fr0) + mono[(size_t) i1] * fr0;
        }
        frames.push_back (std::move (fr));
    }
    return fromFrames (name, frames);
}

std::shared_ptr<Wavetable> Wavetable::fromAudioData (const juce::String& name, const void* data, size_t size)
{
    juce::AudioFormatManager fm;
    fm.registerBasicFormats();
    auto stream = std::make_unique<juce::MemoryInputStream> (data, size, false);
    std::unique_ptr<juce::AudioFormatReader> reader (fm.createReaderFor (std::move (stream)));
    if (reader == nullptr || reader->lengthInSamples < 32) return nullptr;
    const int len = (int) juce::jmin<juce::int64> (reader->lengthInSamples, (juce::int64) kMaxFrames * N * 2);
    juce::AudioBuffer<float> buf ((int) reader->numChannels, len);
    reader->read (&buf, 0, len, 0, true, true);
    return fromAudio (name, buf);
}
} // namespace psxl
