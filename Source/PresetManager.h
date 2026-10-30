#pragma once
#include <juce_core/juce_core.h>
#include <memory>
#include <vector>

namespace psxl
{
struct PresetInfo
{
    juce::String name, category, author;
    bool factory = true;
    juce::File file;                         // user presets only
    std::shared_ptr<juce::XmlElement> xml;   // factory presets (parsed once)
};

// Holds the factory library (embedded XML) and scans the user preset folders.
class PresetManager
{
public:
    PresetManager();
    static juce::StringArray categories();
    static juce::File userPresetDirectory();

    const std::vector<PresetInfo>& all() const { return presets; }
    void rescanUser();
    int numFactory() const { return factoryCount; }
    std::unique_ptr<juce::XmlElement> load (int index) const;

    static juce::File saveUserPreset (const juce::XmlElement& xml, const juce::String& name, const juce::String& category);

private:
    std::vector<PresetInfo> presets;
    int factoryCount = 0;
};
} // namespace psxl
