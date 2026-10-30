#pragma once
#include "Widgets.h"

namespace psxl
{
// 3D "waterfall" display of a wavetable with a draggable position cursor. Accepts dropped audio files.
class WavetableView : public juce::Component, public juce::FileDragAndDropTarget, private juce::Timer
{
public:
    explicit WavetableView (PSXLProcessor& p);
    void setOsc (int osc);   // 1 or 2
    void paint (juce::Graphics&) override;
    void mouseDown (const juce::MouseEvent& e) override { setFromMouse (e, true); }
    void mouseDrag (const juce::MouseEvent& e) override { setFromMouse (e, false); }
    void mouseUp (const juce::MouseEvent&) override;
    bool isInterestedInFileDrag (const juce::StringArray& files) override;
    void filesDropped (const juce::StringArray& files, int, int) override;
    void fileDragEnter (const juce::StringArray&, int, int) override { dropHover = true; repaint(); }
    void fileDragExit (const juce::StringArray&) override { dropHover = false; repaint(); }
private:
    void timerCallback() override;
    void rebuild (const Wavetable* wt);
    void setFromMouse (const juce::MouseEvent&, bool begin);
    PSXLProcessor& proc;
    int osc = 1;
    std::atomic<float> *wtRaw = nullptr, *posRaw = nullptr;
    juce::RangedAudioParameter* posParam = nullptr;
    std::vector<juce::Path> lines;
    const Wavetable* cached = nullptr;
    float lastPos = -1.0f;
    bool dropHover = false, gesture = false;
};

// Node-based routing editor: drag from an output port to an input port to connect; click a wire to select it.
class RoutingView : public juce::Component, private juce::Timer, private juce::ChangeListener
{
public:
    explicit RoutingView (PSXLProcessor& p);
    ~RoutingView() override;
    void paint (juce::Graphics&) override;
    void mouseDown (const juce::MouseEvent&) override;
    void mouseDrag (const juce::MouseEvent&) override;
    void mouseUp (const juce::MouseEvent&) override;
    void mouseDoubleClick (const juce::MouseEvent&) override;
    bool keyPressed (const juce::KeyPress&) override;
private:
    struct Wire { int src, dst; juce::Path path; };
    juce::Rectangle<float> nodeRect (int node) const;
    juce::Point<float> outPort (int node) const { auto r = nodeRect (node); return { r.getRight(), r.getCentreY() }; }
    juce::Point<float> inPort (int node) const { auto r = nodeRect (node); return { r.getX(), r.getCentreY() }; }
    juce::Path wirePath (juce::Point<float> a, juce::Point<float> b) const;
    bool hitWire (juce::Point<float> p, int& src, int& dst) const;
    int portAt (juce::Point<float> p, bool output) const;
    void applyTemplate (int id);
    void timerCallback() override { repaint(); }
    void changeListenerCallback (juce::ChangeBroadcaster*) override { repaint(); }
    juce::String subtitle (int node) const;

    PSXLProcessor& proc;
    int dragSrc = -1;
    juce::Point<float> dragPos;
    int selSrc = -1, selDst = -1;
};

// Envelope / LFO display with live playhead and draggable handles.
class ShapeView : public juce::Component, private juce::Timer
{
public:
    explicit ShapeView (PSXLProcessor& p);
    void setSlot (int slot) { this->slot = slot; repaint(); }
    void paint (juce::Graphics&) override;
    void mouseDown (const juce::MouseEvent&) override;
    void mouseDrag (const juce::MouseEvent&) override;
    void mouseUp (const juce::MouseEvent&) override;
private:
    void timerCallback() override { repaint(); }
    float raw (const char* name) const;
    void nudge (const char* name, float deltaNorm);
    PSXLProcessor& proc;
    int slot = 1;
    int dragHandle = -1;
    juce::Point<float> lastMouse;
    float xs[7] {};
    float sustainY = 0, topY = 0, botY = 0;
};

class ModEditor : public juce::Component, private juce::Timer
{
public:
    explicit ModEditor (PSXLProcessor& p);
    void setSlot (int slot);   // 1..9
    void resized() override;
    void paint (juce::Graphics&) override;
private:
    void rebuild();
    void timerCallback() override;
    PSXLProcessor& proc;
    int slot = 1, builtType = -1;
    ShapeView shape;
    std::unique_ptr<ModSourceChip> chip;
    std::unique_ptr<PSCombo> typeCombo, shapeCombo, divCombo;
    std::vector<std::unique_ptr<PSKnob>> knobs;
    std::vector<std::unique_ptr<PSToggle>> toggles;
};

class PerfEditor : public juce::Component, private juce::Timer
{
public:
    explicit PerfEditor (PSXLProcessor& p);
    void setPerf (int index);  // 0..2
    void resized() override;
    void paint (juce::Graphics&) override;
    void mouseDown (const juce::MouseEvent& e) override { setStepFromMouse (e); }
    void mouseDrag (const juce::MouseEvent& e) override { setStepFromMouse (e); }
private:
    void rebuild();
    void setStepFromMouse (const juce::MouseEvent&);
    void patternMenu();
    void timerCallback() override { repaint(); }
    juce::Rectangle<int> barsArea() const;
    PSXLProcessor& proc;
    int perf = 0;
    std::unique_ptr<ModSourceChip> chip;
    std::unique_ptr<PSCombo> divCombo;
    std::unique_ptr<PSToggle> syncToggle;
    std::vector<std::unique_ptr<PSKnob>> knobs;
    juce::TextButton randomBtn { "Randomise" }, patternBtn { "Patterns" };
};

class VoiceView : public juce::Component, private juce::ChangeListener
{
public:
    explicit VoiceView (PSXLProcessor& p);
    ~VoiceView() override;
    void resized() override;
    void paint (juce::Graphics&) override;
private:
    void changeListenerCallback (juce::ChangeBroadcaster*) override { repaint(); }
    PSXLProcessor& proc;
    PSCombo modeCombo;
    PSToggle expoToggle;
    std::vector<std::unique_ptr<PSKnob>> knobs;
    juce::TextButton importBtn { "Import wavetable..." }, scalaBtn { "Load Scala (.scl)..." }, resetTuneBtn { "12-TET" };
    std::shared_ptr<juce::FileChooser> chooser;
};

// 16 macro knobs with draggable assignment handles, plus the performance sources.
class MacroStrip : public juce::Component, private juce::ChangeListener
{
public:
    explicit MacroStrip (PSXLProcessor& p);
    ~MacroStrip() override;
    void resized() override;
    void paint (juce::Graphics&) override;
private:
    void changeListenerCallback (juce::ChangeBroadcaster*) override;
    void renameMacro (int i);
    PSXLProcessor& proc;
    std::vector<std::unique_ptr<PSKnob>> knobs;
    std::vector<std::unique_ptr<ModSourceChip>> chips;
    std::vector<std::unique_ptr<ModSourceChip>> special;
};

// Collapsible on-screen keyboard with pitch and mod wheels.
class KeyboardDrawer : public juce::Component, private juce::Timer
{
public:
    explicit KeyboardDrawer (PSXLProcessor& p);
    void resized() override;
    void paint (juce::Graphics&) override;
    void setOctaves (int n);
    int getOctaves() const { return octaves; }
private:
    void timerCallback() override;
    void layoutKeys();
    void sendPitch (float v);
    void sendMod (float v);
    PSXLProcessor& proc;
    juce::MidiKeyboardComponent keys;
    juce::Slider pitchWheel, modWheel;
    juce::TextButton down { "<" }, up { ">" };
    int octaves = 5, lowOctave = 2;
};

// Preset browser overlay.
class BrowserView : public juce::Component, private juce::ListBoxModel, private juce::ChangeListener
{
public:
    explicit BrowserView (PSXLProcessor& p);
    ~BrowserView() override;
    std::function<void()> onClose;
    void refresh();
    void resized() override;
    void paint (juce::Graphics&) override;
private:
    int getNumRows() override { return (int) shown.size(); }
    void paintListBoxItem (int row, juce::Graphics&, int w, int h, bool selected) override;
    void listBoxItemClicked (int row, const juce::MouseEvent&) override;
    void listBoxItemDoubleClicked (int row, const juce::MouseEvent&) override;
    void returnKeyPressed (int row) override { loadRow (row); }
    void loadRow (int row);
    void changeListenerCallback (juce::ChangeBroadcaster*) override { repaint(); }
    void rebuildList();
    void saveDialog();

    PSXLProcessor& proc;
    juce::TextEditor search;
    juce::ListBox catList, presetList;
    struct CatModel;
    std::unique_ptr<juce::ListBoxModel> catModel;
    juce::TextButton saveBtn { "Save preset..." }, folderBtn { "Open user folder" }, closeBtn { "Close" };
    juce::StringArray cats;
    int cat = 0;
    std::vector<int> shown;
    friend struct CatModel;
};
} // namespace psxl
