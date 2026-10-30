#include "Views.h"

namespace psxl
{
using juce::Graphics;
using juce::Rectangle;
using juce::String;

// =============================================================================================
// WavetableView
// =============================================================================================
WavetableView::WavetableView (PSXLProcessor& p) : proc (p)
{
    setOsc (1);
    startTimerHz (30);
}

void WavetableView::setOsc (int o)
{
    osc = o;
    wtRaw = proc.apvts.getRawParameterValue (oscId (o, "wt"));
    posRaw = proc.apvts.getRawParameterValue (oscId (o, "pos"));
    posParam = proc.apvts.getParameter (oscId (o, "pos"));
    cached = nullptr;
    repaint();
}

void WavetableView::timerCallback()
{
    const bool live = proc.shared.activeVoices.load() > 0;
    const float pos = live ? proc.shared.uiDest[osc == 1 ? D_O1_POS : D_O2_POS].load() : posParam->getValue();
    const Wavetable* wt = proc.getTable ((int) wtRaw->load());
    if (std::abs (pos - lastPos) > 0.002f || wt != cached) { lastPos = pos; repaint(); }
}

void WavetableView::rebuild (const Wavetable* wt)
{
    cached = wt;
    lines.clear();
    if (wt == nullptr) return;
    const int n = juce::jmin (wt->numFrames, 32);
    constexpr int level = 3, pts = 128, stride = Wavetable::kFrameSize / pts;
    for (int l = 0; l < n; ++l)
    {
        const int fi = n > 1 ? l * (wt->numFrames - 1) / (n - 1) : 0;
        const float* fr = wt->frame (level, fi);
        juce::Path path;
        for (int i = 0; i <= pts; ++i)
        {
            const float x = (float) i / (float) pts, y = -fr[(i % pts) * stride];
            if (i == 0) path.startNewSubPath (x, y); else path.lineTo (x, y);
        }
        lines.push_back (std::move (path));
    }
}

void WavetableView::paint (Graphics& g)
{
    const auto& pal = Theme::p();
    auto full = getLocalBounds().toFloat();
    g.setColour (pal.panelHi); g.fillRoundedRectangle (full, 6.0f);
    g.setColour (dropHover ? pal.accent2 : pal.outline); g.drawRoundedRectangle (full.reduced (0.5f), 6.0f, dropHover ? 2.5f : 1.0f);

    const Wavetable* wt = proc.getTable ((int) wtRaw->load());
    if (wt != cached) rebuild (wt);
    if (lines.empty())
    {
        g.setColour (pal.textDim); g.setFont (Theme::font (12.0f));
        g.drawText ("Empty slot - drop an audio file here", getLocalBounds(), juce::Justification::centred);
        return;
    }

    auto area = full.reduced (12.0f, 10.0f);
    const int n = (int) lines.size();
    const float amp = area.getHeight() * 0.16f, span = area.getHeight() - amp * 2.2f;
    const bool live = proc.shared.activeVoices.load() > 0;
    const float pos = live ? proc.shared.uiDest[osc == 1 ? D_O1_POS : D_O2_POS].load() : posParam->getValue();
    const int hot = juce::jlimit (0, n - 1, (int) std::round (pos * (float) (n - 1)));

    for (int l = n - 1; l >= 0; --l)
    {
        const float depth = n > 1 ? (float) l / (float) (n - 1) : 0.0f;   // 0 = front
        const float yBase = area.getBottom() - amp * 1.2f - span * depth * 0.85f;
        const float xOff = area.getWidth() * 0.10f * depth, wid = area.getWidth() * 0.88f;
        const auto tf = juce::AffineTransform::scale (wid, amp).translated (area.getX() + xOff, yBase);

        juce::Path fill = lines[(size_t) l];
        fill.lineTo (1.0f, 1.4f); fill.lineTo (0.0f, 1.4f); fill.closeSubPath();   // hides lines behind this one
        g.setColour (pal.panelHi); g.fillPath (fill, tf);
        if (l == hot) { g.setColour (pal.accent.withAlpha (0.18f)); g.fillPath (fill, tf); }
        g.setColour (l == hot ? pal.accent : pal.textDim.withAlpha (0.30f + 0.45f * (1.0f - depth)));
        g.strokePath (lines[(size_t) l], juce::PathStrokeType (l == hot ? 2.2f : 1.0f), tf);
    }
    g.setColour (pal.text.withAlpha (0.9f)); g.setFont (Theme::font (11.0f, true));
    g.drawText (wt->name, getLocalBounds().reduced (10, 6).removeFromTop (14), juce::Justification::centredRight);
}

void WavetableView::setFromMouse (const juce::MouseEvent& e, bool begin)
{
    if (posParam == nullptr) return;
    if (begin) { posParam->beginChangeGesture(); gesture = true; }
    posParam->setValueNotifyingHost (juce::jlimit (0.0f, 1.0f, (e.position.x - 12.0f) / ((float) getWidth() - 24.0f)));
}

void WavetableView::mouseUp (const juce::MouseEvent&)
{
    if (gesture && posParam != nullptr) posParam->endChangeGesture();
    gesture = false;
}

bool WavetableView::isInterestedInFileDrag (const juce::StringArray& files)
{
    for (auto& f : files)
        if (juce::File (f).hasFileExtension ("wav;aif;aiff;flac;ogg")) return true;
    return false;
}

void WavetableView::filesDropped (const juce::StringArray& files, int, int)
{
    dropHover = false;
    for (auto& f : files)
    {
        const int slot = proc.importWavetable (juce::File (f));
        if (slot < 0) { toast ("Could not read " + juce::File (f).getFileName()); continue; }
        if (auto* prm = proc.apvts.getParameter (oscId (osc, "wt"))) prm->setValueNotifyingHost (prm->convertTo0to1 ((float) slot));
        toast ("Imported wavetable \"" + proc.getTableName (slot) + "\" into Osc " + String (osc));
        break;
    }
    repaint();
}

// =============================================================================================
// MacroStrip
// =============================================================================================
MacroStrip::MacroStrip (PSXLProcessor& p) : proc (p)
{
    for (int i = 0; i < kNumMacros; ++i)
    {
        knobs.push_back (std::make_unique<PSKnob> (proc, macroId (i), proc.getMacroName (i)));
        addAndMakeVisible (*knobs.back());
        auto chip = std::make_unique<ModSourceChip> (proc, S_Macro1 + i, "M" + String (i + 1));
        chip->compact = true;
        chip->onDoubleClick = [this, i] { renameMacro (i); };
        chip->onRightClick = [this, i]
        {
            juce::PopupMenu m;
            m.addItem (1, "Rename macro...");
            m.addItem (2, "Reset name");
            juce::Component::SafePointer<MacroStrip> safe (this);
            m.showMenuAsync ({}, [safe, i] (int id)
            {
                if (safe == nullptr) return;
                if (id == 1) safe->renameMacro (i);
                else if (id == 2) safe->proc.setMacroName (i, {});
            });
        };
        addAndMakeVisible (*chip);
        chips.push_back (std::move (chip));
    }
    static const std::pair<int, const char*> sources[] = { { S_PitchBend, "Pitch" }, { S_ModWheel, "ModWhl" }, { S_Aftertouch, "AftTch" },
                                                           { S_Velocity, "Velocity" }, { S_Keytrack, "KeyTrk" }, { S_Random, "Random" } };
    for (const auto& s : sources)
    {
        special.push_back (std::make_unique<ModSourceChip> (proc, s.first, s.second));
        addAndMakeVisible (*special.back());
    }
    proc.addChangeListener (this);
}

MacroStrip::~MacroStrip() { proc.removeChangeListener (this); }

void MacroStrip::changeListenerCallback (juce::ChangeBroadcaster*)
{
    for (int i = 0; i < kNumMacros; ++i) knobs[(size_t) i]->setLabel (proc.getMacroName (i));
    for (auto& c : chips) c->repaint();
    for (auto& c : special) c->repaint();
}

void MacroStrip::renameMacro (int i)
{
    auto* aw = new juce::AlertWindow ("Rename Macro " + String (i + 1), "This name is also shown on NKS hardware displays.", juce::MessageBoxIconType::NoIcon);
    aw->addTextEditor ("name", proc.getMacroName (i));
    aw->addButton ("OK", 1, juce::KeyPress (juce::KeyPress::returnKey));
    aw->addButton ("Cancel", 0, juce::KeyPress (juce::KeyPress::escapeKey));
    juce::Component::SafePointer<MacroStrip> safe (this);
    aw->enterModalState (true, juce::ModalCallbackFunction::create ([safe, aw, i] (int result)
    {
        if (result == 1 && safe != nullptr) safe->proc.setMacroName (i, aw->getTextEditorContents ("name"));
        delete aw;
    }), false);
}

void MacroStrip::paint (Graphics& g)
{
    drawPanel (g, getLocalBounds().toFloat(), {});
}

void MacroStrip::resized()
{
    auto r = getLocalBounds().reduced (6, 3);
    auto left = r.removeFromLeft (134);
    for (size_t i = 0; i < special.size(); ++i)
        special[i]->setBounds (left.getX() + (int) (i % 2) * 67, left.getY() + (int) (i / 2) * 21, 65, 19);
    r.removeFromLeft (8);
    const int cw = r.getWidth() / kNumMacros;
    for (int i = 0; i < kNumMacros; ++i)
    {
        Rectangle<int> cell (r.getX() + i * cw, r.getY(), cw, r.getHeight());
        knobs[(size_t) i]->setBounds (cell.removeFromTop (cell.getHeight() - 16));
        chips[(size_t) i]->setBounds (cell.withSizeKeepingCentre (28, 14));
    }
}

// =============================================================================================
// KeyboardDrawer
// =============================================================================================
KeyboardDrawer::KeyboardDrawer (PSXLProcessor& p)
    : proc (p), keys (p.keyboardState, juce::MidiKeyboardComponent::horizontalKeyboard),
      pitchWheel (juce::Slider::LinearVertical, juce::Slider::NoTextBox), modWheel (juce::Slider::LinearVertical, juce::Slider::NoTextBox)
{
    addAndMakeVisible (keys);
    keys.setMidiChannel (1);
    keys.setVelocity (0.85f, true);   // mouse height on the key sets the velocity
    keys.setScrollButtonsVisible (false);
    keys.setWantsKeyboardFocus (true);

    pitchWheel.setRange (-1.0, 1.0, 0.0); pitchWheel.setValue (0.0);
    pitchWheel.setDoubleClickReturnValue (true, 0.0);
    pitchWheel.onValueChange = [this] { if (pitchWheel.isMouseButtonDown()) sendPitch ((float) pitchWheel.getValue()); };
    pitchWheel.onDragEnd = [this] { pitchWheel.setValue (0.0, juce::dontSendNotification); sendPitch (0.0f); };   // spring back
    modWheel.setRange (0.0, 1.0, 0.0); modWheel.setValue (0.0);
    modWheel.onValueChange = [this] { if (modWheel.isMouseButtonDown()) sendMod ((float) modWheel.getValue()); };
    addAndMakeVisible (pitchWheel); addAndMakeVisible (modWheel);

    addAndMakeVisible (down); addAndMakeVisible (up);
    down.onClick = [this] { lowOctave = juce::jmax (0, lowOctave - 1); layoutKeys(); };
    up.onClick = [this] { lowOctave = juce::jmin (9 - octaves, lowOctave + 1); layoutKeys(); };
    octaves = proc.getSettings().getIntValue ("keyboardOctaves", 5);
    startTimerHz (20);
}

void KeyboardDrawer::setOctaves (int n)
{
    octaves = juce::jlimit (2, 8, n);
    lowOctave = juce::jlimit (0, 9 - octaves, lowOctave);
    layoutKeys();
}

void KeyboardDrawer::sendPitch (float v)
{
    auto m = juce::MidiMessage::pitchWheel (1, juce::jlimit (0, 16383, (int) std::round ((v * 0.5f + 0.5f) * 16383.0f)));
    m.setTimeStamp (juce::Time::getMillisecondCounterHiRes() * 0.001);
    proc.uiMidi.addMessageToQueue (m);
}

void KeyboardDrawer::sendMod (float v)
{
    auto m = juce::MidiMessage::controllerEvent (1, 1, juce::jlimit (0, 127, (int) std::round (v * 127.0f)));
    m.setTimeStamp (juce::Time::getMillisecondCounterHiRes() * 0.001);
    proc.uiMidi.addMessageToQueue (m);
}

void KeyboardDrawer::timerCallback()
{
    // wheels follow hardware MIDI when not being dragged
    if (! pitchWheel.isMouseButtonDown()) pitchWheel.setValue (proc.shared.wheelPitch.load(), juce::dontSendNotification);
    if (! modWheel.isMouseButtonDown()) modWheel.setValue (proc.shared.wheelMod.load(), juce::dontSendNotification);
}

void KeyboardDrawer::layoutKeys()
{
    const int low = lowOctave * 12, high = juce::jmin (127, low + octaves * 12);
    keys.setAvailableRange (low, high);
    const int whites = octaves * 7 + 1;
    if (keys.getWidth() > 0) keys.setKeyWidth ((float) keys.getWidth() / (float) whites);
    keys.setLowestVisibleKey (low);
    repaint();
}

void KeyboardDrawer::resized()
{
    auto r = getLocalBounds().reduced (6);
    auto left = r.removeFromLeft (120);
    pitchWheel.setBounds (left.removeFromLeft (34).reduced (2, 6).withTrimmedBottom (12));
    left.removeFromLeft (4);
    modWheel.setBounds (left.removeFromLeft (34).reduced (2, 6).withTrimmedBottom (12));
    left.removeFromLeft (6);
    down.setBounds (left.removeFromTop (30).reduced (0, 2));
    up.setBounds (left.removeFromTop (30).reduced (0, 2));
    r.removeFromLeft (4);
    keys.setBounds (r);
    layoutKeys();
}

void KeyboardDrawer::paint (Graphics& g)
{
    const auto& pal = Theme::p();
    drawPanel (g, getLocalBounds().toFloat(), {});
    keys.setColour (juce::MidiKeyboardComponent::whiteNoteColourId, Theme::isDark() ? juce::Colour (0xffe9edf9) : juce::Colours::white);
    keys.setColour (juce::MidiKeyboardComponent::blackNoteColourId, Theme::isDark() ? juce::Colour (0xff12141c) : juce::Colour (0xff222638));
    keys.setColour (juce::MidiKeyboardComponent::keySeparatorLineColourId, pal.outline);
    keys.setColour (juce::MidiKeyboardComponent::keyDownOverlayColourId, pal.accent.withAlpha (0.85f));
    keys.setColour (juce::MidiKeyboardComponent::mouseOverKeyOverlayColourId, pal.accent2.withAlpha (0.35f));
    keys.setColour (juce::MidiKeyboardComponent::textLabelColourId, pal.textDim);
    g.setColour (pal.textDim); g.setFont (Theme::font (9.5f, true));
    g.drawText ("PITCH", pitchWheel.getX(), getHeight() - 16, 34, 12, juce::Justification::centred);
    g.drawText ("MOD", modWheel.getX(), getHeight() - 16, 34, 12, juce::Justification::centred);
    g.drawText ("C" + String (lowOctave - 2), down.getX(), down.getBottom() + up.getHeight() - 2, 40, 12, juce::Justification::centredLeft);
}

// =============================================================================================
// BrowserView
// =============================================================================================
struct BrowserView::CatModel : public juce::ListBoxModel
{
    explicit CatModel (BrowserView& o) : owner (o) {}
    int getNumRows() override { return owner.cats.size(); }
    void paintListBoxItem (int row, Graphics& g, int w, int h, bool selected) override
    {
        const auto& pal = Theme::p();
        if (selected) { g.setColour (pal.accent.withAlpha (0.25f)); g.fillRoundedRectangle (4.0f, 1.0f, (float) w - 8.0f, (float) h - 2.0f, 4.0f); }
        g.setColour (selected ? pal.text : pal.textDim);
        g.setFont (Theme::font (13.0f, selected));
        g.drawText (owner.cats[row], 14, 0, w - 20, h, juce::Justification::centredLeft);
    }
    void selectedRowsChanged (int row) override { if (row >= 0) { owner.cat = row; owner.rebuildList(); } }
    BrowserView& owner;
};

BrowserView::BrowserView (PSXLProcessor& p) : proc (p), catList ("cats"), presetList ("presets")
{
    cats.add ("All");
    cats.addArray (PresetManager::categories());
    cats.add ("User");
    catModel = std::make_unique<CatModel> (*this);
    catList.setModel (catModel.get());
    catList.setRowHeight (28);
    presetList.setModel (this);
    presetList.setRowHeight (30);
    presetList.setColour (juce::ListBox::backgroundColourId, juce::Colours::transparentBlack);
    catList.setColour (juce::ListBox::backgroundColourId, juce::Colours::transparentBlack);
    addAndMakeVisible (catList); addAndMakeVisible (presetList);
    addAndMakeVisible (search); addAndMakeVisible (saveBtn); addAndMakeVisible (folderBtn); addAndMakeVisible (closeBtn);
    search.setTextToShowWhenEmpty ("Search presets, categories...", Theme::p().textDim);
    search.onTextChange = [this] { rebuildList(); };
    saveBtn.onClick = [this] { saveDialog(); };
    folderBtn.onClick = [this] { auto d = PresetManager::userPresetDirectory(); d.createDirectory(); d.revealToUser(); };
    closeBtn.onClick = [this] { if (onClose) onClose(); };
    proc.addChangeListener (this);
    catList.selectRow (0);
    rebuildList();
}

BrowserView::~BrowserView() { proc.removeChangeListener (this); }

void BrowserView::refresh() { proc.presets.rescanUser(); rebuildList(); }

void BrowserView::rebuildList()
{
    shown.clear();
    const auto q = search.getText().trim().toLowerCase();
    const auto& all = proc.presets.all();
    for (int i = 0; i < (int) all.size(); ++i)
    {
        const auto& pr = all[(size_t) i];
        if (cat > 0 && cat < cats.size() - 1 && pr.category != cats[cat]) continue;
        if (cat == cats.size() - 1 && pr.factory) continue;
        if (q.isNotEmpty() && ! (pr.name.toLowerCase().contains (q) || pr.category.toLowerCase().contains (q) || pr.author.toLowerCase().contains (q))) continue;
        shown.push_back (i);
    }
    presetList.updateContent();
    presetList.repaint();
}

void BrowserView::paintListBoxItem (int row, Graphics& g, int w, int h, bool selected)
{
    if (row < 0 || row >= (int) shown.size()) return;
    const auto& pal = Theme::p();
    const auto& pr = proc.presets.all()[(size_t) shown[(size_t) row]];
    const bool current = pr.name == proc.presetName;
    if (selected || current) { g.setColour (pal.accent.withAlpha (current ? 0.28f : 0.16f)); g.fillRoundedRectangle (4.0f, 1.0f, (float) w - 8.0f, (float) h - 2.0f, 4.0f); }
    g.setColour (pal.text); g.setFont (Theme::font (13.5f, current));
    g.drawText (pr.name, 14, 0, w / 2, h, juce::Justification::centredLeft);
    g.setColour (pal.textDim); g.setFont (Theme::font (11.5f));
    g.drawText (pr.category, w / 2, 0, w / 4, h, juce::Justification::centredLeft);
    g.drawText (pr.author, w * 3 / 4, 0, w / 4 - 12, h, juce::Justification::centredRight);
}

void BrowserView::loadRow (int row)
{
    if (row >= 0 && row < (int) shown.size()) proc.loadPresetIndex (shown[(size_t) row]);
}

void BrowserView::listBoxItemClicked (int row, const juce::MouseEvent&) { loadRow (row); }
void BrowserView::listBoxItemDoubleClicked (int row, const juce::MouseEvent&) { loadRow (row); if (onClose) onClose(); }

void BrowserView::saveDialog()
{
    auto* aw = new juce::AlertWindow ("Save preset", "Saved to your user preset folder.", juce::MessageBoxIconType::NoIcon);
    aw->addTextEditor ("name", proc.presetName == "Init (Blank)" ? String ("My Preset") : proc.presetName);
    juce::StringArray c = PresetManager::categories(); c.add ("User");
    aw->addComboBox ("cat", c);
    aw->addButton ("Save", 1, juce::KeyPress (juce::KeyPress::returnKey));
    aw->addButton ("Cancel", 0, juce::KeyPress (juce::KeyPress::escapeKey));
    juce::Component::SafePointer<BrowserView> safe (this);
    aw->enterModalState (true, juce::ModalCallbackFunction::create ([safe, aw, c] (int result)
    {
        if (result == 1 && safe != nullptr)
        {
            const auto name = aw->getTextEditorContents ("name").trim();
            if (name.isNotEmpty())
            {
                safe->proc.saveUserPreset (name, c[aw->getComboBoxComponent ("cat")->getSelectedItemIndex()]);
                safe->refresh();
                toast ("Saved preset \"" + name + "\"");
            }
        }
        delete aw;
    }), false);
}

void BrowserView::paint (Graphics& g)
{
    const auto& pal = Theme::p();
    drawPanel (g, getLocalBounds().toFloat(), {});
    g.setColour (pal.textDim); g.setFont (Theme::font (11.0f, true));
    g.drawText ("PRESET BROWSER  -  " + String (proc.presets.numFactory()) + " factory presets", 16, 10, 420, 16, juce::Justification::centredLeft);
}

void BrowserView::resized()
{
    auto r = getLocalBounds().reduced (12);
    auto head = r.removeFromTop (30);
    head.removeFromLeft (4);
    closeBtn.setBounds (head.removeFromRight (70)); head.removeFromRight (6);
    folderBtn.setBounds (head.removeFromRight (130)); head.removeFromRight (6);
    saveBtn.setBounds (head.removeFromRight (110)); head.removeFromRight (12);
    search.setBounds (head.removeFromRight (260));
    r.removeFromTop (6);
    catList.setBounds (r.removeFromLeft (170));
    r.removeFromLeft (8);
    presetList.setBounds (r);
}
} // namespace psxl
