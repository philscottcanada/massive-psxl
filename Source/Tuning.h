#pragma once
#include <juce_core/juce_core.h>
#include <array>
#include <cmath>
#include <vector>

namespace psxl
{
// Scala (.scl) microtuning support. Degree 0 of the scale sits on MIDI note 60 (261.6256 Hz).
inline bool parseScala (const juce::String& text, std::array<float, 128>& out, juce::String& description)
{
    juce::StringArray lines;
    lines.addLines (text);
    std::vector<juce::String> body;
    for (auto& l : lines)
        if (! l.trim().startsWith ("!")) body.push_back (l.trim());
    if (body.size() < 2) return false;

    description = body[0];
    const int count = body[1].getIntValue();
    if (count < 1 || (int) body.size() < 2 + count) return false;

    std::vector<double> ratios { 1.0 };
    for (int i = 0; i < count; ++i)
    {
        juce::String s = body[(size_t) (2 + i)].upToFirstOccurrenceOf (" ", false, false);
        s = s.upToFirstOccurrenceOf ("\t", false, false);
        double r;
        if (s.containsChar ('.')) r = std::pow (2.0, s.getDoubleValue() / 1200.0);
        else if (s.containsChar ('/')) { const double d = s.fromFirstOccurrenceOf ("/", false, false).getDoubleValue(); r = d != 0.0 ? s.upToFirstOccurrenceOf ("/", false, false).getDoubleValue() / d : 0.0; }
        else r = s.getDoubleValue();
        if (r <= 0.0) return false;
        ratios.push_back (r);
    }
    const double period = ratios.back();
    ratios.pop_back();   // ratios[0..count-1] are the degrees; the last entry is the period
    const int n = count;
    for (int note = 0; note < 128; ++note)
    {
        const int rel = note - 60;
        int degree = rel % n; int octave = rel / n;
        if (degree < 0) { degree += n; --octave; }
        out[(size_t) note] = (float) (261.6256 * std::pow (period, octave) * ratios[(size_t) degree]);
    }
    return true;
}

inline void equalTemperament (std::array<float, 128>& out)
{
    for (int n = 0; n < 128; ++n) out[(size_t) n] = 440.0f * std::pow (2.0f, ((float) n - 69.0f) / 12.0f);
}
} // namespace psxl
