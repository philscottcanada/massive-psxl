#pragma once
#include "Panels.h"

namespace psxl
{
class PSXLEditor : public juce::AudioProcessorEditor, public juce::DragAndDropContainer,
                   private juce::ChangeListener, private juce::Timer
{
public:
    explicit PSXLEditor (PSXLProcessor& p);
    ~PSXLEditor() override;
    void resized() override;
    void paint (juce::Graphics&) override {}

private:
    class Content : public juce::Component
    {
    public:
        std::function<void (juce::Graphics&)> onPaint;
        void paint (juce::Graphics& g) override { if (onPaint) onPaint (g); }
    };

    void paintContent (juce::Graphics&);
    void changeListenerCallback (juce::ChangeBroadcaster*) override;
    void timerCallback() override;
    void showLower (int index);
    void setBrowsing (bool b);
    void showMainMenu();
    void setTheme (bool dark);
    void setUiScale (double s);
    void toggleKeyboard();
    void stepPreset (int dir);
    void updateSize();
    void showToast (const juce::String& s);
    int baseHeight() const;

    PSXLProcessor& proc;
    PSLookAndFeel laf;
    juce::ComponentBoundsConstrainer constrainer;
    Content content;
    double scale = 1.0;
    bool kbOpen = false, browsing = false;
    juce::String toastText;
    juce::uint32 toastUntil = 0;

    juce::TextButton menuBtn { "Menu" }, prevBtn { "<" }, nextBtn { ">" }, presetBtn, undoBtn { "Undo" }, redoBtn { "Redo" }, themeBtn, keysBtn { "Keys" };
    TabStrip mainTabs, lowerTabs;
    PSKnob masterKnob;
    PitchPanel pitchPanel;
    OscPanel oscPanel;
    NoisePanel noisePanel;
    FilterPanel filterPanel;
    InsertPanel insertPanel;
    AmpPanel ampPanel;
    FxPanel fxPanel;
    VoiceView voiceView;
    RoutingView routingView;
    ModEditor modEditor;
    PerfEditor perfEditor;
    MacroStrip macroStrip;
    KeyboardDrawer keyboard;
    BrowserView browser;
    std::shared_ptr<juce::FileChooser> chooser;

    juce::Rectangle<int> meterRect;
    int lastUndoState = -1;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (PSXLEditor)
};
} // namespace psxl
