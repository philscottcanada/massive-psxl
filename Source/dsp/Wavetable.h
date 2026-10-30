#pragma once
#include <juce_audio_formats/juce_audio_formats.h>
#include <juce_dsp/juce_dsp.h>
#include <array>
#include <memory>
#include <vector>

namespace psxl
{
// A band-limited wavetable: frames of 2048 samples, with mip levels that progressively drop harmonics.
struct Wavetable
{
    static constexpr int kFrameSize = 2048;
    static constexpr int kMipLevels = 10;
    static constexpr int kMaxFrames = 256;

    juce::String name;
    int numFrames = 0;
    std::array<std::vector<float>, kMipLevels> data;   // data[level][frame * kFrameSize + i]

    static int maxHarmonics (int level) { return (kFrameSize / 2) >> level; }
    const float* frame (int level, int f) const { return data[(size_t) level].data() + (size_t) f * kFrameSize; }

    // Picks the richest mip level that does not alias at the given frequency.
    static int levelForFrequency (float freq, float sampleRate)
    {
        const float ratio = 2048.0f * freq / sampleRate;
        if (ratio <= 1.0f) return 0;
        return juce::jmin (kMipLevels - 1, (int) std::ceil (std::log2 (ratio)));
    }

    // Build from single-cycle time-domain frames (each kFrameSize samples).
    static std::shared_ptr<Wavetable> fromFrames (const juce::String& name, const std::vector<std::vector<float>>& frames);

    // Build one of the factory wavetables (index 0..kNumBuiltinTables-1).
    static std::shared_ptr<Wavetable> createBuiltin (int index);
    static juce::String builtinName (int index);

    // Build from an audio file's samples. Returns nullptr on failure.
    static std::shared_ptr<Wavetable> fromAudio (const juce::String& name, const juce::AudioBuffer<float>& audio);
    static std::shared_ptr<Wavetable> fromAudioData (const juce::String& name, const void* data, size_t size);
};
} // namespace psxl
