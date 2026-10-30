#include "PresetManager.h"
#include "BinaryData.h"

namespace psxl
{
juce::StringArray PresetManager::categories() { return { "Bass", "Leads", "Pads", "Plucks", "Keys", "Drums", "FX", "Sequence" }; }

juce::File PresetManager::userPresetDirectory()
{
    return juce::File::getSpecialLocation (juce::File::userMusicDirectory).getChildFile ("Phil S Audio").getChildFile ("Massive PSXL").getChildFile ("Presets");
}

PresetManager::PresetManager()
{
    int size = 0;
    if (auto* data = BinaryData::getNamedResource ("factory_presets_xml", size))
        if (auto root = juce::XmlDocument::parse (juce::String::fromUTF8 (data, size)))
            for (auto* e : root->getChildWithTagNameIterator ("PSXL"))
            {
                PresetInfo p;
                p.name = e->getStringAttribute ("name"); p.category = e->getStringAttribute ("category", "FX");
                p.author = e->getStringAttribute ("author", "Phil S Audio"); p.factory = true;
                p.xml = std::make_shared<juce::XmlElement> (*e);
                presets.push_back (std::move (p));
            }
    std::stable_sort (presets.begin(), presets.end(), [] (const PresetInfo& a, const PresetInfo& b)
    {
        const int ca = categories().indexOf (a.category), cb = categories().indexOf (b.category);
        return ca != cb ? ca < cb : a.name.compareIgnoreCase (b.name) < 0;
    });
    factoryCount = (int) presets.size();
    rescanUser();
}

void PresetManager::rescanUser()
{
    presets.resize ((size_t) factoryCount);
    const auto dir = userPresetDirectory();
    if (! dir.isDirectory()) return;
    for (const auto& f : dir.findChildFiles (juce::File::findFiles, true, "*.psxlpreset"))
    {
        PresetInfo p;
        p.factory = false; p.file = f; p.name = f.getFileNameWithoutExtension();
        const auto rel = f.getParentDirectory().getRelativePathFrom (dir);
        p.category = f.getParentDirectory() == dir ? "User" : "User/" + rel.replaceCharacter ('\\', '/');
        p.author = "User";
        presets.push_back (std::move (p));
    }
}

std::unique_ptr<juce::XmlElement> PresetManager::load (int index) const
{
    if (index < 0 || index >= (int) presets.size()) return nullptr;
    const auto& p = presets[(size_t) index];
    if (p.factory) return p.xml ? std::make_unique<juce::XmlElement> (*p.xml) : nullptr;
    return juce::XmlDocument::parse (p.file);
}

juce::File PresetManager::saveUserPreset (const juce::XmlElement& xml, const juce::String& name, const juce::String& category)
{
    auto dir = userPresetDirectory();
    if (category.isNotEmpty() && category != "User") dir = dir.getChildFile (category);
    dir.createDirectory();
    auto file = dir.getChildFile (juce::File::createLegalFileName (name) + ".psxlpreset");
    xml.writeTo (file);
    return file;
}
} // namespace psxl
