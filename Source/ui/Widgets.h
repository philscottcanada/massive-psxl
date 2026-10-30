#pragma once
#include "../PluginProcessor.h"
#include "Theme.h"

namespace psxl
{
class PSLookAndFeel : public juce::LookAndFeel_V4
{
public:
    PSLookAndFeel() { applyTheme(); }
    void applyTheme();
    void drawComboBox (juce::Graphics&, int w, int h, bool down, int, int, int, int, juce::ComboBox&) override;
    void drawToggleButton (juce::Graphics&, juce::ToggleButton&, bool highlighted, bool down) override;
    juce::Font getComboBoxFont (juce::ComboBox&) override { return Theme::font (12.0f); }
    juce::Font getPopupMenuFont() override { return Theme::font (13.0f); }
    void positionComboBoxText (juce::ComboBox&, juce::Label&) override;
    void drawLinearSlider (juce::Graphics&, int x, int y, int w, int h, float pos, float, float, juce::Slider::SliderStyle, juce::Slider&) override;
};

// Rotary knob bound to a parameter. Accepts modulation drops, shows modulation rings, supports MIDI learn.
class PSKnob : public juce::Slider, public juce::DragAndDropTarget, private juce::ChangeListener, private juce::Timer
{
public:
    PSKnob (PSXLProcessor& p, const juce::String& paramId, const juce::String& label, bool bigKnob = false);
    ~PSKnob() override;
    void paint (juce::Graphics&) override;
    void mouseDown (const juce::MouseEvent&) override;
    void mouseEnter (const juce::MouseEvent& e) override { hover = true; juce::Slider::mouseEnter (e); repaint(); }
    void mouseExit (const juce::MouseEvent& e) override { hover = false; juce::Slider::mouseExit (e); repaint(); }
    bool isInterestedInDragSource (const SourceDetails&) override;
    void itemDragEnter (const SourceDetails&) override { dropHover = true; repaint(); }
    void itemDragExit (const SourceDetails&) override { dropHover = false; repaint(); }
    void itemDropped (const SourceDetails&) override;
    void setLabel (const juce::String& s) { label = s; repaint(); }
    const juce::String& getParamId() const { return paramId; }

private:
    void changeListenerCallback (juce::ChangeBroadcaster*) override { refreshAssignments(); repaint(); }
    void timerCallback() override;
    void refreshAssignments();
    void showMenu();
    void showAmountEditor (int src);

    PSXLProcessor& proc;
    juce::String paramId, label;
    int dest = -1;
    bool hover = false, dropHover = false, big = false;
    std::vector<Assignment> assigns;
    float lastLive = -1.0f;
    std::unique_ptr<juce::SliderParameterAttachment> attachment;
};

// Parameter-bound toggle pill.
class PSToggle : public juce::ToggleButton
{
public:
    PSToggle (PSXLProcessor& p, const juce::String& paramId, const juce::String& text);
private:
    std::unique_ptr<juce::ButtonParameterAttachment> attachment;
};

// Parameter-bound choice menu.
class PSCombo : public juce::ComboBox
{
public:
    PSCombo (PSXLProcessor& p, const juce::String& paramId);
    void refreshItems (const juce::StringArray& items);   // for choice lists that change at runtime (e.g. filter modes)
private:
    PSXLProcessor& proc;
    juce::String paramId;
    std::unique_ptr<juce::ComboBoxParameterAttachment> attachment;
};

// Horizontal strip of tab buttons.
class TabStrip : public juce::Component
{
public:
    std::function<void (int)> onChange;
    void setTabs (const juce::StringArray& names, const std::vector<juce::Colour>& colours = {});
    void setSelected (int i, bool notify = true);
    int getSelected() const { return selected; }
    void paint (juce::Graphics&) override;
    void mouseDown (const juce::MouseEvent&) override;
private:
    juce::StringArray names;
    std::vector<juce::Colour> colours;
    int selected = 0;
};

// A draggable crosshair handle that carries a modulation source onto knobs.
class ModSourceChip : public juce::Component
{
public:
    ModSourceChip (PSXLProcessor& p, int source, const juce::String& text);
    void setText (const juce::String& t) { text = t; repaint(); }
    void paint (juce::Graphics&) override;
    void mouseDrag (const juce::MouseEvent&) override;
    void mouseUp (const juce::MouseEvent&) override { dragging = false; repaint(); }
    void mouseDoubleClick (const juce::MouseEvent&) override { if (onDoubleClick) onDoubleClick(); }
    void mouseDown (const juce::MouseEvent& e) override { if (e.mods.isPopupMenu() && onRightClick) onRightClick(); }
    std::function<void()> onDoubleClick, onRightClick;
    int getSource() const { return source; }
    bool compact = false;
private:
    PSXLProcessor& proc;
    int source;
    juce::String text;
    bool dragging = false;
};

juce::Image makeCrosshairImage (juce::Colour c);
void drawPanel (juce::Graphics& g, juce::Rectangle<float> r, const juce::String& title);
} // namespace psxl
