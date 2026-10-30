#pragma once
#include <juce_gui_basics/juce_gui_basics.h>
#include <functional>

namespace psxl
{
struct Palette
{
    juce::Colour bg, panel, panelHi, outline, text, textDim, accent, accent2, accent3, knobBody, knobTrack, good;
};

// Light / dark theme. Components read the current palette every time they paint.
struct Theme
{
    static bool& darkFlag() { static bool d = true; return d; }
    static bool isDark() { return darkFlag(); }
    static void setDark (bool d) { darkFlag() = d; }

    static const Palette& p()
    {
        static const Palette dark { juce::Colour (0xff0b0d14), juce::Colour (0xff151925), juce::Colour (0xff1e2333), juce::Colour (0xff2c3350),
                                    juce::Colour (0xffe9edf9), juce::Colour (0xff8a93b0), juce::Colour (0xff35d4ff), juce::Colour (0xffd24bff),
                                    juce::Colour (0xffffb43a), juce::Colour (0xff222840), juce::Colour (0xff30385a), juce::Colour (0xff4be08a) };
        static const Palette light { juce::Colour (0xffe6e9f2), juce::Colour (0xfffbfcff), juce::Colour (0xffeef1f9), juce::Colour (0xffbec5da),
                                     juce::Colour (0xff141828), juce::Colour (0xff576079), juce::Colour (0xff0877d0), juce::Colour (0xff9a28d0),
                                     juce::Colour (0xffd47a00), juce::Colour (0xffdde2f0), juce::Colour (0xffc4cbe0), juce::Colour (0xff12a35a) };
        return isDark() ? dark : light;
    }

    static juce::Font font (float h, bool bold = false)
    {
        return juce::Font (juce::FontOptions (h, bold ? juce::Font::bold : juce::Font::plain));
    }

    // modulation source colour: mods cyan, performers amber, macros magenta, performance sources green
    static juce::Colour sourceColour (int src)
    {
        if (src < 9) return p().accent;
        if (src < 12) return p().accent3;
        if (src < 28) return p().accent2;
        return p().good;
    }
};

// Transient message shown by the editor (e.g. "Voice modulators can't control global effects").
inline std::function<void (const juce::String&)>& toastCallback() { static std::function<void (const juce::String&)> f; return f; }
inline void toast (const juce::String& s) { if (toastCallback()) toastCallback() (s); }
} // namespace psxl
