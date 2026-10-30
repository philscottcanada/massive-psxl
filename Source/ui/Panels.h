#pragma once
#include "Views.h"

namespace psxl
{
class PitchPanel : public juce::Component
{
public:
    explicit PitchPanel (PSXLProcessor& p);
    void paint (juce::Graphics&) override;
    void resized() override;
private:
    PSKnob pitch, glide;
    PSCombo mode;
    PSToggle expo;
};

class OscPanel : public juce::Component, private juce::ChangeListener, private juce::Timer
{
public:
    explicit OscPanel (PSXLProcessor& p);
    ~OscPanel() override;
    void paint (juce::Graphics&) override;
    void resized() override;
private:
    void changeListenerCallback (juce::ChangeBroadcaster*) override { refreshTables(); }
    void timerCallback() override;
    void refreshTables();
    void showOsc (int osc);
    void stepTable (int dir);
    PSXLProcessor& proc;
    int osc = 1;
    TabStrip tabs;
    WavetableView view;
    juce::ComboBox tableBox;
    juce::TextButton prev { "<" }, next { ">" }, importBtn { "+" };
    std::vector<std::unique_ptr<PSKnob>> knobs[2];
    std::shared_ptr<juce::FileChooser> chooser;
};

class NoisePanel : public juce::Component
{
public:
    explicit NoisePanel (PSXLProcessor& p);
    void paint (juce::Graphics&) override;
    void resized() override;
private:
    PSKnob level, color;
    PSCombo type;
};

class FilterPanel : public juce::Component, private juce::Timer
{
public:
    explicit FilterPanel (PSXLProcessor& p);
    void paint (juce::Graphics&) override;
    void resized() override;
private:
    void timerCallback() override;
    void showFilter (int f);
    PSXLProcessor& proc;
    int filt = 1;
    TabStrip tabs;
    std::unique_ptr<PSCombo> model[2], mode[2];
    std::vector<std::unique_ptr<PSKnob>> knobs[2];
    int shownModel[2] { -1, -1 };
};

class InsertPanel : public juce::Component
{
public:
    explicit InsertPanel (PSXLProcessor& p);
    void paint (juce::Graphics&) override;
    void resized() override;
private:
    PSCombo type;
    PSKnob drive, mix;
};

class AmpPanel : public juce::Component
{
public:
    explicit AmpPanel (PSXLProcessor& p);
    void paint (juce::Graphics&) override;
    void resized() override;
private:
    PSKnob level, pan, feedback;
};

class FxPanel : public juce::Component
{
public:
    explicit FxPanel (PSXLProcessor& p);
    void paint (juce::Graphics&) override;
    void resized() override;
private:
    void showTab (int t);
    struct Group { std::vector<std::unique_ptr<juce::Component>> items; };
    PSXLProcessor& proc;
    TabStrip tabs;
    std::vector<Group> groups;
    int tab = 0;
};
} // namespace psxl
