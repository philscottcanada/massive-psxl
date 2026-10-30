#include "Widgets.h"

namespace psxl
{
using juce::Colour;
using juce::Graphics;
using juce::String;
constexpr float kPi = juce::MathConstants<float>::pi;

// ---------------------------------------------------------------------------------------------
void PSLookAndFeel::applyTheme()
{
    const auto& p = Theme::p();
    setColour (juce::ResizableWindow::backgroundColourId, p.bg);
    setColour (juce::ComboBox::backgroundColourId, p.panelHi);
    setColour (juce::ComboBox::textColourId, p.text);
    setColour (juce::ComboBox::outlineColourId, p.outline);
    setColour (juce::ComboBox::arrowColourId, p.textDim);
    setColour (juce::PopupMenu::backgroundColourId, p.panel);
    setColour (juce::PopupMenu::textColourId, p.text);
    setColour (juce::PopupMenu::highlightedBackgroundColourId, p.accent.withAlpha (0.35f));
    setColour (juce::PopupMenu::highlightedTextColourId, p.text);
    setColour (juce::PopupMenu::headerTextColourId, p.textDim);
    setColour (juce::Label::textColourId, p.text);
    setColour (juce::TextEditor::backgroundColourId, p.panelHi);
    setColour (juce::TextEditor::textColourId, p.text);
    setColour (juce::TextEditor::outlineColourId, p.outline);
    setColour (juce::TextEditor::focusedOutlineColourId, p.accent);
    setColour (juce::TextButton::buttonColourId, p.panelHi);
    setColour (juce::TextButton::textColourOffId, p.text);
    setColour (juce::TextButton::textColourOnId, p.text);
    setColour (juce::ListBox::backgroundColourId, p.panel);
    setColour (juce::ListBox::textColourId, p.text);
    setColour (juce::ScrollBar::thumbColourId, p.knobTrack);
    setColour (juce::Slider::thumbColourId, p.accent);
    setColour (juce::Slider::trackColourId, p.accent);
    setColour (juce::Slider::backgroundColourId, p.knobTrack);
    setColour (juce::Slider::textBoxTextColourId, p.text);
    setColour (juce::Slider::textBoxBackgroundColourId, p.panelHi);
    setColour (juce::Slider::textBoxOutlineColourId, p.outline);
    setColour (juce::AlertWindow::backgroundColourId, p.panel);
    setColour (juce::AlertWindow::textColourId, p.text);
    setColour (juce::AlertWindow::outlineColourId, p.outline);
}

void PSLookAndFeel::positionComboBoxText (juce::ComboBox& box, juce::Label& label)
{
    label.setBounds (6, 1, box.getWidth() - 20, box.getHeight() - 2);
    label.setFont (getComboBoxFont (box));
}

void PSLookAndFeel::drawComboBox (Graphics& g, int w, int h, bool down, int, int, int, int, juce::ComboBox& box)
{
    const auto& p = Theme::p();
    auto r = juce::Rectangle<float> (0, 0, (float) w, (float) h).reduced (0.5f);
    g.setColour (down ? p.panelHi.brighter (0.15f) : p.panelHi);
    g.fillRoundedRectangle (r, 5.0f);
    g.setColour (box.hasKeyboardFocus (true) ? p.accent : p.outline);
    g.drawRoundedRectangle (r, 5.0f, 1.0f);
    juce::Path arrow;
    const float ax = (float) w - 11.0f, ay = (float) h * 0.5f;
    arrow.addTriangle (ax - 3.5f, ay - 1.5f, ax + 3.5f, ay - 1.5f, ax, ay + 2.5f);
    g.setColour (p.textDim);
    g.fillPath (arrow);
}

void PSLookAndFeel::drawToggleButton (Graphics& g, juce::ToggleButton& b, bool highlighted, bool)
{
    const auto& p = Theme::p();
    auto r = b.getLocalBounds().toFloat().reduced (0.5f);
    const bool on = b.getToggleState();
    g.setColour (on ? p.accent.withAlpha (0.9f) : (highlighted ? p.panelHi.brighter (0.1f) : p.panelHi));
    g.fillRoundedRectangle (r, 5.0f);
    g.setColour (on ? p.accent : p.outline);
    g.drawRoundedRectangle (r, 5.0f, 1.0f);
    g.setColour (on ? (Theme::isDark() ? juce::Colours::black : juce::Colours::white) : p.text);
    g.setFont (Theme::font (11.5f, true));
    g.drawText (b.getButtonText(), b.getLocalBounds(), juce::Justification::centred);
}

void PSLookAndFeel::drawLinearSlider (Graphics& g, int x, int y, int w, int h, float pos, float, float, juce::Slider::SliderStyle style, juce::Slider& s)
{
    const auto& p = Theme::p();
    const bool vertical = style == juce::Slider::LinearVertical;
    juce::Rectangle<float> track = vertical ? juce::Rectangle<float> ((float) x + (float) w * 0.5f - 2.0f, (float) y, 4.0f, (float) h)
                                            : juce::Rectangle<float> ((float) x, (float) y + (float) h * 0.5f - 2.0f, (float) w, 4.0f);
    g.setColour (p.knobTrack);
    g.fillRoundedRectangle (track, 2.0f);
    g.setColour (s.findColour (juce::Slider::trackColourId));
    if (vertical) g.fillRoundedRectangle (track.withTop (pos), 2.0f); else g.fillRoundedRectangle (track.withRight (pos), 2.0f);
    const float cx = vertical ? track.getCentreX() : pos, cy = vertical ? pos : track.getCentreY();
    g.setColour (p.text);
    g.fillEllipse (cx - 6.0f, cy - 6.0f, 12.0f, 12.0f);
    g.setColour (s.findColour (juce::Slider::thumbColourId));
    g.fillEllipse (cx - 4.0f, cy - 4.0f, 8.0f, 8.0f);
}

// ---------------------------------------------------------------------------------------------
PSKnob::PSKnob (PSXLProcessor& p, const String& id, const String& lbl, bool bigKnob)
    : proc (p), paramId (id), label (lbl), big (bigKnob)
{
    dest = destIndexForId (id);
    setSliderStyle (juce::Slider::RotaryHorizontalVerticalDrag);
    setTextBoxStyle (juce::Slider::NoTextBox, true, 0, 0);
    setMouseDragSensitivity (160);
    setScrollWheelEnabled (true);
    if (auto* prm = p.apvts.getParameter (id)) attachment = std::make_unique<juce::SliderParameterAttachment> (*prm, *this, nullptr);
    proc.addChangeListener (this);
    refreshAssignments();
}

PSKnob::~PSKnob() { proc.removeChangeListener (this); }

void PSKnob::refreshAssignments()
{
    assigns = dest >= 0 ? proc.assignmentsForDest (dest) : std::vector<Assignment>();
    if (assigns.empty()) stopTimer();               // only animate knobs that are being modulated
    else if (! isTimerRunning()) startTimerHz (24);
}

void PSKnob::timerCallback()
{
    if (assigns.empty() || dest < 0 || ! isShowing()) return;
    const float live = proc.shared.uiDest[dest].load();
    if (std::abs (live - lastLive) > 0.002f) { lastLive = live; repaint(); }
}

void PSKnob::paint (Graphics& g)
{
    const auto& p = Theme::p();
    auto area = getLocalBounds().toFloat();
    auto labelArea = area.removeFromBottom (13.0f);
    const float d = juce::jmin (area.getWidth(), area.getHeight()) - 6.0f;
    const auto c = area.getCentre();
    const float r = d * 0.5f;
    const float a0 = -kPi * 0.75f, a1 = kPi * 0.75f;
    const float norm = (float) valueToProportionOfLength (getValue());

    // body
    g.setColour (p.knobBody);
    g.fillEllipse (c.x - r * 0.78f, c.y - r * 0.78f, r * 1.56f, r * 1.56f);

    auto arc = [&] (float from, float to, float radius, float thick, Colour col)
    {
        if (std::abs (to - from) < 0.002f) return;
        juce::Path path;
        path.addCentredArc (c.x, c.y, radius, radius, 0.0f, from, to, true);
        g.setColour (col);
        g.strokePath (path, juce::PathStrokeType (thick, juce::PathStrokeType::curved, juce::PathStrokeType::rounded));
    };
    arc (a0, a1, r - 1.5f, 2.5f, p.knobTrack);
    const auto range = getRange();
    const bool bipolar = range.getStart() < 0.0 && range.getEnd() > 0.0;
    const float zero = bipolar ? a0 + (a1 - a0) * (float) valueToProportionOfLength (0.0) : a0;
    const float va = a0 + (a1 - a0) * norm;
    arc (juce::jmin (zero, va), juce::jmax (zero, va), r - 1.5f, 2.5f, isEnabled() ? p.accent : p.textDim);

    // modulation rings
    for (const auto& a : assigns)
    {
        const float target = juce::jlimit (0.0f, 1.0f, norm + a.amount);
        arc (a0 + (a1 - a0) * juce::jmin (norm, target), a0 + (a1 - a0) * juce::jmax (norm, target), r + 1.5f, 2.0f, Theme::sourceColour (a.src).withAlpha (0.9f));
    }
    if (! assigns.empty() && dest >= 0)
    {
        const float live = proc.shared.uiDest[dest].load();
        const float la = a0 + (a1 - a0) * live;
        g.setColour (p.text);
        g.fillEllipse (c.x + std::sin (la) * (r - 1.5f) - 2.0f, c.y - std::cos (la) * (r - 1.5f) - 2.0f, 4.0f, 4.0f);
    }

    // pointer
    {
        const float len = r * 0.62f;
        juce::Path ptr;
        ptr.startNewSubPath (c.x + std::sin (va) * r * 0.2f, c.y - std::cos (va) * r * 0.2f);
        ptr.lineTo (c.x + std::sin (va) * len, c.y - std::cos (va) * len);
        g.setColour (p.text);
        g.strokePath (ptr, juce::PathStrokeType (2.0f, juce::PathStrokeType::curved, juce::PathStrokeType::rounded));
    }

    if (dropHover)
    {
        g.setColour (p.accent2);
        g.drawEllipse (c.x - r - 2.0f, c.y - r - 2.0f, (r + 2.0f) * 2.0f, (r + 2.0f) * 2.0f, 2.5f);
    }
    else if (proc.learningParamId() == paramId)
    {
        g.setColour (p.accent3);
        g.drawEllipse (c.x - r - 2.0f, c.y - r - 2.0f, (r + 2.0f) * 2.0f, (r + 2.0f) * 2.0f, 2.0f);
    }

    // label / value
    g.setFont (Theme::font (big ? 11.5f : 10.5f));
    g.setColour (hover || isMouseButtonDown() ? p.text : p.textDim);
    String text = label;
    if (hover || isMouseButtonDown())
        if (auto* prm = proc.apvts.getParameter (paramId)) text = prm->getCurrentValueAsText() + (prm->getLabel().isNotEmpty() ? " " + prm->getLabel() : String());
    g.drawFittedText (text, labelArea.toNearestInt(), juce::Justification::centred, 1);
}

bool PSKnob::isInterestedInDragSource (const SourceDetails& d)
{
    return dest >= 0 && d.description.toString().startsWith ("mod:");
}

void PSKnob::itemDropped (const SourceDetails& d)
{
    dropHover = false;
    const int src = d.description.toString().substring (4).getIntValue();
    String err;
    if (proc.addAssignment (src, dest, 0.5f, err))
    {
        String msg = sourceName (src) + " now controls " + proc.apvts.getParameter (paramId)->getName (40);
        if (src >= S_Macro1 && src < S_Macro1 + kNumMacros && ! proc.isMacroUserNamed (src - S_Macro1))
            msg += "  (macro renamed to \"" + proc.getMacroName (src - S_Macro1) + "\")";
        toast (msg);
    }
    else toast (err);
    repaint();
}

void PSKnob::mouseDown (const juce::MouseEvent& e)
{
    if (e.mods.isPopupMenu()) { showMenu(); return; }
    juce::Slider::mouseDown (e);
}

void PSKnob::showMenu()
{
    juce::PopupMenu m;
    const bool mapped = proc.ccForParam (paramId).isNotEmpty();
    m.addItem (1, proc.learningParamId() == paramId ? "Waiting for MIDI CC... (click to cancel)" : "MIDI Learn");
    if (mapped) m.addItem (2, "Clear MIDI mapping (" + proc.ccForParam (paramId) + ")");
    m.addItem (3, "Reset to default");
    if (! assigns.empty())
    {
        m.addSeparator();
        for (size_t i = 0; i < assigns.size(); ++i)
        {
            const int pct = (int) std::round (assigns[i].amount * 100.0f);
            m.addItem (100 + (int) i, "Edit amount: " + sourceName (assigns[i].src) + " (" + String (pct) + "%)");
            m.addItem (200 + (int) i, "Remove " + sourceName (assigns[i].src));
        }
    }
    juce::Component::SafePointer<PSKnob> safe (this);
    m.showMenuAsync (juce::PopupMenu::Options().withTargetComponent (this), [safe] (int id)
    {
        if (safe == nullptr || id == 0) return;
        auto& pr = safe->proc;
        if (id == 1) { if (pr.learningParamId() == safe->paramId) pr.cancelMidiLearn(); else pr.startMidiLearn (safe->paramId); }
        else if (id == 2) pr.clearMidiMapping (safe->paramId);
        else if (id == 3) { if (auto* prm = pr.apvts.getParameter (safe->paramId)) prm->setValueNotifyingHost (prm->getDefaultValue()); }
        else if (id >= 200 && id - 200 < (int) safe->assigns.size()) { const auto a = safe->assigns[(size_t) (id - 200)]; pr.removeAssignment (a.src, a.dest); }
        else if (id >= 100 && id - 100 < (int) safe->assigns.size()) safe->showAmountEditor (safe->assigns[(size_t) (id - 100)].src);
        safe->repaint();
    });
}

void PSKnob::showAmountEditor (int src)
{
    float current = 0.5f;
    for (auto& a : assigns) if (a.src == src) current = a.amount;
    auto s = std::make_unique<juce::Slider> (juce::Slider::LinearHorizontal, juce::Slider::TextBoxRight);
    s->setRange (-1.0, 1.0, 0.01);
    s->setValue (current, juce::dontSendNotification);
    s->setTextBoxStyle (juce::Slider::TextBoxRight, false, 52, 22);
    s->setSize (260, 36);
    auto* pr = &proc; const int d = dest;
    auto* raw = s.get();
    s->onValueChange = [pr, src, d, raw] { pr->setAssignmentAmount (src, d, (float) raw->getValue()); };
    juce::CallOutBox::launchAsynchronously (std::move (s), getScreenBounds(), nullptr);
}

// ---------------------------------------------------------------------------------------------
PSToggle::PSToggle (PSXLProcessor& p, const String& id, const String& text) : juce::ToggleButton (text)
{
    if (auto* prm = dynamic_cast<juce::RangedAudioParameter*> (p.apvts.getParameter (id)))
        attachment = std::make_unique<juce::ButtonParameterAttachment> (*prm, *this, nullptr);
}

PSCombo::PSCombo (PSXLProcessor& p, const String& id) : proc (p), paramId (id)
{
    if (auto* prm = dynamic_cast<juce::AudioParameterChoice*> (p.apvts.getParameter (id)))
    {
        addItemList (prm->choices, 1);
        attachment = std::make_unique<juce::ComboBoxParameterAttachment> (*prm, *this, nullptr);
    }
}

void PSCombo::refreshItems (const juce::StringArray& items)
{
    const int sel = getSelectedItemIndex();
    clear (juce::dontSendNotification);
    addItemList (items, 1);
    setSelectedItemIndex (sel, juce::dontSendNotification);
}

// ---------------------------------------------------------------------------------------------
void TabStrip::setTabs (const juce::StringArray& n, const std::vector<Colour>& c) { names = n; colours = c; repaint(); }
void TabStrip::setSelected (int i, bool notify)
{
    selected = juce::jlimit (0, juce::jmax (0, names.size() - 1), i);
    repaint();
    if (notify && onChange) onChange (selected);
}

void TabStrip::paint (Graphics& g)
{
    const auto& p = Theme::p();
    if (names.isEmpty()) return;
    const float w = (float) getWidth() / (float) names.size();
    for (int i = 0; i < names.size(); ++i)
    {
        auto r = juce::Rectangle<float> (w * (float) i, 0.0f, w, (float) getHeight()).reduced (1.5f, 2.0f);
        const bool on = i == selected;
        const Colour col = i < (int) colours.size() ? colours[(size_t) i] : p.accent;
        g.setColour (on ? col.withAlpha (0.22f) : p.panelHi.withAlpha (0.6f));
        g.fillRoundedRectangle (r, 4.0f);
        if (on) { g.setColour (col); g.fillRoundedRectangle (r.removeFromBottom (2.5f), 1.0f); }
        g.setColour (on ? p.text : p.textDim);
        g.setFont (Theme::font (11.5f, on));
        g.drawText (names[i], juce::Rectangle<float> (w * (float) i, 0.0f, w, (float) getHeight()).toNearestInt(), juce::Justification::centred);
    }
}

void TabStrip::mouseDown (const juce::MouseEvent& e)
{
    if (names.isEmpty()) return;
    setSelected ((int) ((float) e.x / ((float) getWidth() / (float) names.size())));
}

// ---------------------------------------------------------------------------------------------
juce::Image makeCrosshairImage (Colour c)
{
    juce::Image img (juce::Image::ARGB, 30, 30, true);
    Graphics g (img);
    g.setColour (c.withAlpha (0.25f)); g.fillEllipse (2.0f, 2.0f, 26.0f, 26.0f);
    g.setColour (c); g.drawEllipse (4.0f, 4.0f, 22.0f, 22.0f, 2.0f);
    g.drawLine (15.0f, 1.0f, 15.0f, 29.0f, 1.5f); g.drawLine (1.0f, 15.0f, 29.0f, 15.0f, 1.5f);
    return img;
}

ModSourceChip::ModSourceChip (PSXLProcessor& p, int src, const String& t) : proc (p), source (src), text (t)
{
    setMouseCursor (juce::MouseCursor::DraggingHandCursor);
}

void ModSourceChip::paint (Graphics& g)
{
    const auto& p = Theme::p();
    const Colour col = Theme::sourceColour (source);
    auto r = getLocalBounds().toFloat().reduced (1.0f);
    const bool used = proc.countAssignmentsForSource (source) > 0;
    g.setColour (col.withAlpha (dragging ? 0.55f : (used ? 0.30f : 0.15f)));
    g.fillRoundedRectangle (r, 5.0f);
    g.setColour (col.withAlpha (used ? 1.0f : 0.6f));
    g.drawRoundedRectangle (r, 5.0f, 1.0f);
    // crosshair glyph
    const float cx = r.getX() + 11.0f, cy = r.getCentreY();
    g.drawEllipse (cx - 4.5f, cy - 4.5f, 9.0f, 9.0f, 1.3f);
    g.drawLine (cx, cy - 7.0f, cx, cy + 7.0f, 1.0f); g.drawLine (cx - 7.0f, cy, cx + 7.0f, cy, 1.0f);
    if (! compact)
    {
        g.setColour (p.text);
        g.setFont (Theme::font (10.5f, true));
        g.drawFittedText (text, getLocalBounds().withTrimmedLeft (22).withTrimmedRight (2), juce::Justification::centredLeft, 1);
    }
}

void ModSourceChip::mouseDrag (const juce::MouseEvent& e)
{
    if (dragging || e.getDistanceFromDragStart() < 5) return;
    if (auto* c = juce::DragAndDropContainer::findParentDragContainerFor (this))
    {
        dragging = true;
        c->startDragging ("mod:" + String (source), this, juce::ScaledImage (makeCrosshairImage (Theme::sourceColour (source))), true);
        repaint();
    }
}

void drawPanel (Graphics& g, juce::Rectangle<float> r, const String& title)
{
    const auto& p = Theme::p();
    g.setColour (p.panel);
    g.fillRoundedRectangle (r, 8.0f);
    g.setColour (p.outline);
    g.drawRoundedRectangle (r.reduced (0.5f), 8.0f, 1.0f);
    if (title.isNotEmpty())
    {
        g.setColour (p.textDim);
        g.setFont (Theme::font (11.0f, true));
        g.drawText (title, r.reduced (10.0f, 5.0f).removeFromTop (14.0f), juce::Justification::centredLeft);
    }
}
} // namespace psxl
