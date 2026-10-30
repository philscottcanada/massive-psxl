#include "Views.h"

namespace psxl
{
using juce::Graphics;
using juce::Point;
using juce::Rectangle;
using juce::String;

// =============================================================================================
// ShapeView
// =============================================================================================
ShapeView::ShapeView (PSXLProcessor& p) : proc (p) { startTimerHz (30); }

float ShapeView::raw (const char* name) const
{
    if (auto* v = proc.apvts.getRawParameterValue (modId (slot, name))) return v->load();
    return 0.0f;
}

static float timeWidth (float t) { return std::pow (juce::jlimit (0.0f, 10.0f, t) / 10.0f, 0.4f); }

static float lfoShape (int shape, float ph, int cycle)
{
    auto hash = [] (int n) { unsigned u = (unsigned) n; u = (u << 13) ^ u; return 1.0f - (float) ((u * (u * u * 15731u + 789221u) + 1376312589u) & 0x7fffffffu) / 1073741824.0f; };
    switch (shape)
    {
        case 0: return std::sin (juce::MathConstants<float>::twoPi * ph);
        case 1: return 1.0f - 4.0f * std::abs (ph - 0.5f);
        case 2: return 2.0f * ph - 1.0f;
        case 3: return 1.0f - 2.0f * ph;
        case 4: return ph < 0.5f ? 1.0f : -1.0f;
        case 5: return hash ((int) (ph * 6.0f) + cycle * 6 + 3);
        default: { const float x = ph * 6.0f; const int i = (int) x; const float f = x - (float) i, s = f * f * (3.0f - 2.0f * f);
                   return hash (i + cycle * 6 + 3) * (1.0f - s) + hash (i + 1 + cycle * 6 + 3) * s; }
    }
}

void ShapeView::paint (Graphics& g)
{
    const auto& pal = Theme::p();
    auto full = getLocalBounds().toFloat();
    g.setColour (pal.panelHi);
    g.fillRoundedRectangle (full, 6.0f);
    g.setColour (pal.outline);
    g.drawRoundedRectangle (full.reduced (0.5f), 6.0f, 1.0f);
    auto area = full.reduced (12.0f, 14.0f);
    topY = area.getY(); botY = area.getBottom();

    g.setColour (pal.outline.withAlpha (0.5f));
    for (int i = 1; i < 4; ++i) g.drawHorizontalLine ((int) (area.getY() + area.getHeight() * (float) i / 4.0f), area.getX(), area.getRight());

    const int slotIdx = slot - 1;
    const bool isLfo = slot > 1 && (int) raw ("type") == 1;
    const int stage = proc.shared.uiStage[slotIdx].load();
    const float val = proc.shared.uiVal[slotIdx].load();
    const auto col = pal.accent;

    if (! isLfo)
    {
        const float dly = raw ("dly"), att = raw ("att"), hold = raw ("hold"), dec = raw ("dec"), sus = raw ("sus"), rel = raw ("rel"), level = raw ("level");
        float w[6] = { timeWidth (dly) + 0.02f, timeWidth (att) + 0.03f, timeWidth (hold) + 0.01f, timeWidth (dec) + 0.03f, 0.25f, timeWidth (rel) + 0.03f };
        float sum = 0; for (float v : w) sum += v;
        xs[0] = area.getX();
        for (int i = 0; i < 6; ++i) xs[i + 1] = xs[i] + w[i] / sum * area.getWidth();
        sustainY = botY - sus * area.getHeight();

        juce::Path path;
        path.startNewSubPath (xs[0], botY);
        path.lineTo (xs[1], botY); path.lineTo (xs[2], topY); path.lineTo (xs[3], topY);
        for (int i = 1; i <= 24; ++i) { const float u = (float) i / 24.0f; path.lineTo (xs[3] + (xs[4] - xs[3]) * u, botY - (sus + (1.0f - sus) * std::exp (-6.9f * u)) * area.getHeight()); }
        path.lineTo (xs[5], sustainY);
        for (int i = 1; i <= 24; ++i) { const float u = (float) i / 24.0f; path.lineTo (xs[5] + (xs[6] - xs[5]) * u, botY - sus * std::exp (-6.9f * u) * area.getHeight()); }
        auto fill = path; fill.lineTo (xs[6], botY); fill.closeSubPath();
        g.setColour (col.withAlpha (0.14f)); g.fillPath (fill);
        g.setColour (col); g.strokePath (path, juce::PathStrokeType (2.0f, juce::PathStrokeType::curved, juce::PathStrokeType::rounded));
        for (auto pt : { Point<float> (xs[2], topY), Point<float> (xs[4], sustainY), Point<float> (xs[6], botY) })
        { g.setColour (pal.panel); g.fillEllipse (pt.x - 5, pt.y - 5, 10, 10); g.setColour (col); g.drawEllipse (pt.x - 5, pt.y - 5, 10, 10, 1.8f); }

        // playhead
        if (stage >= 1 && stage <= 6)
        {
            const float prog = proc.shared.uiProg[slotIdx].load();
            float px = xs[0];
            switch (stage)
            {
                case 1: px = xs[0] + prog * (xs[1] - xs[0]); break;
                case 2: px = xs[1] + prog * (xs[2] - xs[1]); break;
                case 3: px = xs[2] + prog * (xs[3] - xs[2]); break;
                case 4: px = xs[3] + prog * (xs[4] - xs[3]); break;
                case 5: px = 0.5f * (xs[4] + xs[5]); break;
                default: px = xs[5] + prog * (xs[6] - xs[5]); break;
            }
            const float py = botY - juce::jlimit (0.0f, 1.0f, level > 0.01f ? val / level : val) * area.getHeight();
            g.setColour (pal.text.withAlpha (0.55f)); g.drawVerticalLine ((int) px, topY, botY);
            g.setColour (pal.accent3); g.fillEllipse (px - 4.5f, py - 4.5f, 9.0f, 9.0f);
        }
    }
    else
    {
        const int shape = (int) raw ("shape");
        const bool bip = raw ("bipolar") > 0.5f;
        const float level = raw ("level");
        juce::Path path;
        const int N = 240;
        for (int i = 0; i <= N; ++i)
        {
            const float t = (float) i / (float) N * 2.0f;
            const int cycle = (int) t; const float ph = juce::jmin (0.9999f, t - (float) cycle);
            float v = lfoShape (shape, ph, cycle) * level;
            const float y = bip ? area.getCentreY() - v * area.getHeight() * 0.5f : botY - 0.5f * (v / juce::jmax (level, 0.01f) * level + level) * area.getHeight();
            const float x = area.getX() + (float) i / (float) N * area.getWidth();
            if (i == 0) path.startNewSubPath (x, y); else path.lineTo (x, y);
        }
        g.setColour (col); g.strokePath (path, juce::PathStrokeType (2.0f, juce::PathStrokeType::curved, juce::PathStrokeType::rounded));
        if (stage == -2)
        {
            const float ph = proc.shared.uiLfoPhase[slotIdx].load();
            for (int c = 0; c < 2; ++c)
            {
                const float px = area.getX() + (ph + (float) c) * 0.5f * area.getWidth();
                g.setColour (pal.text.withAlpha (c == 0 ? 0.6f : 0.25f)); g.drawVerticalLine ((int) px, topY, botY);
            }
            const float px = area.getX() + ph * 0.5f * area.getWidth();
            const float vv = juce::jlimit (-1.0f, 1.0f, val / juce::jmax (level, 0.01f));
            const float py = bip ? area.getCentreY() - vv * level * area.getHeight() * 0.5f : botY - vv * area.getHeight();
            g.setColour (pal.accent3); g.fillEllipse (px - 4.5f, py - 4.5f, 9.0f, 9.0f);
        }
    }
}

void ShapeView::mouseDown (const juce::MouseEvent& e)
{
    dragHandle = -1;
    if (slot > 1 && (int) raw ("type") == 1) return;
    const Point<float> pts[3] = { { xs[2], topY }, { xs[4], sustainY }, { xs[6], botY } };
    float best = 16.0f;
    for (int i = 0; i < 3; ++i)
        if (pts[i].getDistanceFrom (e.position) < best) { best = pts[i].getDistanceFrom (e.position); dragHandle = i; }
    lastMouse = e.position;
    if (dragHandle >= 0)
        for (auto* n : { "att", "dec", "sus", "rel" })
            if (auto* prm = proc.apvts.getParameter (modId (slot, n))) prm->beginChangeGesture();
}

void ShapeView::nudge (const char* name, float delta)
{
    if (auto* prm = proc.apvts.getParameter (modId (slot, name)))
        prm->setValueNotifyingHost (juce::jlimit (0.0f, 1.0f, prm->getValue() + delta));
}

void ShapeView::mouseDrag (const juce::MouseEvent& e)
{
    if (dragHandle < 0) return;
    const float dx = (e.position.x - lastMouse.x) / (float) getWidth(), dy = (e.position.y - lastMouse.y) / (float) getHeight();
    lastMouse = e.position;
    if (dragHandle == 0) nudge ("att", dx * 0.8f);
    else if (dragHandle == 1) { nudge ("dec", dx * 0.8f); nudge ("sus", -dy * 1.2f); }
    else nudge ("rel", dx * 0.8f);
}

void ShapeView::mouseUp (const juce::MouseEvent&)
{
    if (dragHandle >= 0)
        for (auto* n : { "att", "dec", "sus", "rel" })
            if (auto* prm = proc.apvts.getParameter (modId (slot, n))) prm->endChangeGesture();
    dragHandle = -1;
}

// =============================================================================================
// ModEditor
// =============================================================================================
ModEditor::ModEditor (PSXLProcessor& p) : proc (p), shape (p)
{
    addAndMakeVisible (shape);
    startTimerHz (10);
    rebuild();
}

void ModEditor::setSlot (int s) { slot = juce::jlimit (1, kNumMods, s); shape.setSlot (slot); rebuild(); }

void ModEditor::timerCallback()
{
    const int type = slot > 1 ? (int) proc.apvts.getRawParameterValue (modId (slot, "type"))->load() : 0;
    const int sync = slot > 1 ? (int) proc.apvts.getRawParameterValue (modId (slot, "sync"))->load() : 0;
    if (type * 2 + sync != builtType) rebuild();
}

void ModEditor::rebuild()
{
    knobs.clear(); toggles.clear(); typeCombo.reset(); shapeCombo.reset(); divCombo.reset(); chip.reset();
    const int type = slot > 1 ? (int) proc.apvts.getRawParameterValue (modId (slot, "type"))->load() : 0;
    const int sync = slot > 1 ? (int) proc.apvts.getRawParameterValue (modId (slot, "sync"))->load() : 0;
    builtType = type * 2 + sync;

    chip = std::make_unique<ModSourceChip> (proc, S_Mod1 + slot - 1, sourceName (S_Mod1 + slot - 1));
    addAndMakeVisible (*chip);
    if (slot > 1) { typeCombo = std::make_unique<PSCombo> (proc, modId (slot, "type")); addAndMakeVisible (*typeCombo); }

    auto knob = [this] (const char* id, const char* label) { knobs.push_back (std::make_unique<PSKnob> (proc, modId (slot, id), label)); addAndMakeVisible (*knobs.back()); };
    auto toggle = [this] (const char* id, const char* label) { toggles.push_back (std::make_unique<PSToggle> (proc, modId (slot, id), label)); addAndMakeVisible (*toggles.back()); };
    if (type == 0)
    {
        knob ("dly", "Delay"); knob ("att", "Attack"); knob ("hold", "Hold"); knob ("dec", "Decay");
        knob ("sus", "Sustain"); knob ("rel", "Release"); knob ("level", "Env Level"); toggle ("oneshot", "OneShot");
    }
    else
    {
        shapeCombo = std::make_unique<PSCombo> (proc, modId (slot, "shape")); addAndMakeVisible (*shapeCombo);
        if (sync) { divCombo = std::make_unique<PSCombo> (proc, modId (slot, "div")); addAndMakeVisible (*divCombo); }
        else knob ("rate", "Rate");
        knob ("phase", "Phase"); knob ("fade", "Fade In"); knob ("level", "Level");
        toggle ("bipolar", "Bipolar"); toggle ("sync", "Sync");
    }
    resized();
    repaint();
}

void ModEditor::paint (Graphics& g)
{
    drawPanel (g, getLocalBounds().toFloat(), {});
    g.setColour (Theme::p().text);
    g.setFont (Theme::font (13.0f, true));
    g.drawText (slot == 1 ? "Amp Envelope" : (builtType >= 2 ? "LFO " : "Envelope ") + String (slot), 130, 8, 200, 18, juce::Justification::centredLeft);
}

void ModEditor::resized()
{
    auto r = getLocalBounds().reduced (10);
    auto head = r.removeFromTop (26);
    if (chip) chip->setBounds (head.removeFromLeft (112));
    if (typeCombo) typeCombo->setBounds (head.removeFromRight (110));
    r.removeFromTop (6);
    auto left = r.removeFromLeft ((int) ((float) r.getWidth() * 0.52f));
    shape.setBounds (left);
    r.removeFromLeft (14);

    std::vector<juce::Component*> items;
    if (shapeCombo) items.push_back (shapeCombo.get());
    if (divCombo) items.push_back (divCombo.get());
    for (auto& k : knobs) items.push_back (k.get());
    for (auto& t : toggles) items.push_back (t.get());
    const int cols = 4, cw = r.getWidth() / cols, ch = 72;
    int i = 0;
    for (auto* c : items)
    {
        const int col = i % cols, row = i / cols;
        Rectangle<int> cell (r.getX() + col * cw, r.getY() + row * ch, cw, ch);
        if (dynamic_cast<PSKnob*> (c)) c->setBounds (cell.reduced (3));
        else c->setBounds (cell.withSizeKeepingCentre (cw - 8, 26));
        ++i;
    }
}

// =============================================================================================
// PerfEditor
// =============================================================================================
PerfEditor::PerfEditor (PSXLProcessor& p) : proc (p)
{
    addAndMakeVisible (randomBtn); addAndMakeVisible (patternBtn);
    randomBtn.onClick = [this] { proc.randomisePerf (perf); repaint(); };
    patternBtn.onClick = [this] { patternMenu(); };
    startTimerHz (30);
    rebuild();
}

void PerfEditor::setPerf (int i) { perf = juce::jlimit (0, kNumPerf - 1, i); rebuild(); }

void PerfEditor::rebuild()
{
    knobs.clear(); chip.reset(); divCombo.reset(); syncToggle.reset();
    const int p = perf + 1;
    chip = std::make_unique<ModSourceChip> (proc, S_Perf1 + perf, "Performer " + String (p));
    addAndMakeVisible (*chip);
    static const std::pair<const char*, const char*> perfKnobs[] = { { "steps", "Steps" }, { "rate", "Rate" }, { "smooth", "Smooth" } };
    for (const auto& k : perfKnobs)
    { knobs.push_back (std::make_unique<PSKnob> (proc, perfId (p, k.first), k.second)); addAndMakeVisible (*knobs.back()); }
    syncToggle = std::make_unique<PSToggle> (proc, perfId (p, "sync"), "Sync");
    divCombo = std::make_unique<PSCombo> (proc, perfId (p, "div"));
    addAndMakeVisible (*syncToggle); addAndMakeVisible (*divCombo);
    resized(); repaint();
}

Rectangle<int> PerfEditor::barsArea() const
{
    auto r = getLocalBounds().reduced (12);
    r.removeFromTop (30);
    return r.removeFromLeft ((int) ((float) r.getWidth() * 0.6f));
}

void PerfEditor::resized()
{
    auto r = getLocalBounds().reduced (12);
    auto head = r.removeFromTop (26);
    if (chip) chip->setBounds (head.removeFromLeft (130));
    r.removeFromTop (4);
    r.removeFromLeft ((int) ((float) (getWidth() - 24) * 0.6f) + 14);
    auto row1 = r.removeFromTop (74);
    const int cw = row1.getWidth() / 3;
    for (size_t i = 0; i < knobs.size(); ++i) knobs[i]->setBounds (row1.removeFromLeft (cw).reduced (3));
    r.removeFromTop (6);
    auto row2 = r.removeFromTop (26);
    if (syncToggle) syncToggle->setBounds (row2.removeFromLeft (70));
    row2.removeFromLeft (6);
    if (divCombo) divCombo->setBounds (row2.removeFromLeft (90));
    r.removeFromTop (10);
    auto row3 = r.removeFromTop (28);
    randomBtn.setBounds (row3.removeFromLeft (100)); row3.removeFromLeft (6);
    patternBtn.setBounds (row3.removeFromLeft (100));
}

void PerfEditor::paint (Graphics& g)
{
    const auto& pal = Theme::p();
    drawPanel (g, getLocalBounds().toFloat(), {});
    g.setColour (pal.text); g.setFont (Theme::font (13.0f, true));
    g.drawText ("Performer " + String (perf + 1) + "  -  step modulator", 148, 8, 260, 18, juce::Justification::centredLeft);

    auto area = barsArea().toFloat();
    const int steps = (int) proc.apvts.getRawParameterValue (perfId (perf + 1, "steps"))->load();
    const bool live = proc.shared.activeVoices.load() > 0;
    const int idx = proc.shared.uiPerfIdx[perf].load();
    const float bw = area.getWidth() / (float) kPerfSteps;
    g.setColour (pal.panelHi); g.fillRoundedRectangle (area.expanded (4.0f), 6.0f);
    for (int i = 0; i < kPerfSteps; ++i)
    {
        const float v = proc.getPerfStep (perf, i);
        auto bar = Rectangle<float> (area.getX() + bw * (float) i + 2.0f, area.getY(), bw - 4.0f, area.getHeight());
        const bool active = i < steps;
        g.setColour (pal.knobTrack.withAlpha (active ? 0.6f : 0.25f)); g.fillRoundedRectangle (bar, 3.0f);
        auto fill = bar.withTop (bar.getBottom() - bar.getHeight() * v);
        const bool playing = live && active && i == idx;
        g.setColour ((playing ? pal.text : pal.accent3).withAlpha (active ? 1.0f : 0.3f));
        g.fillRoundedRectangle (fill, 3.0f);
        g.setColour (pal.textDim); g.setFont (Theme::font (9.5f));
        g.drawText (String (i + 1), bar.withTop (bar.getBottom() - 12.0f), juce::Justification::centred);
    }
}

void PerfEditor::setStepFromMouse (const juce::MouseEvent& e)
{
    auto area = barsArea();
    if (! area.expanded (4).contains (e.getPosition())) return;
    const int i = (int) ((float) (e.x - area.getX()) / ((float) area.getWidth() / (float) kPerfSteps));
    if (i < 0 || i >= kPerfSteps) return;
    proc.setPerfStep (perf, i, 1.0f - (float) (e.y - area.getY()) / (float) area.getHeight());
    repaint();
}

void PerfEditor::patternMenu()
{
    juce::PopupMenu m;
    m.addItem (1, "Ramp up"); m.addItem (2, "Ramp down"); m.addItem (3, "Triangle"); m.addItem (4, "Alternate high / low");
    m.addItem (5, "Random"); m.addItem (6, "Flat (centre)"); m.addItem (7, "All zero"); m.addItem (8, "Gate: on/off pairs");
    m.addSeparator(); m.addItem (20, "Save pattern..."); m.addItem (21, "Load pattern...");
    juce::Component::SafePointer<PerfEditor> safe (this);
    m.showMenuAsync (juce::PopupMenu::Options().withTargetComponent (&patternBtn), [safe] (int id)
    {
        if (safe == nullptr || id == 0) return;
        auto& pr = safe->proc; const int p = safe->perf;
        if (id == 5) pr.randomisePerf (p);
        else if (id < 20)
            for (int i = 0; i < kPerfSteps; ++i)
            {
                float v = 0.5f;
                switch (id)
                {
                    case 1: v = (float) i / 15.0f; break;
                    case 2: v = 1.0f - (float) i / 15.0f; break;
                    case 3: v = i < 8 ? (float) i / 7.0f : 1.0f - (float) (i - 8) / 7.0f; break;
                    case 4: v = (i & 1) ? 0.15f : 0.9f; break;
                    case 6: v = 0.5f; break;
                    case 7: v = 0.0f; break;
                    case 8: v = ((i / 2) & 1) ? 0.0f : 1.0f; break;
                    default: break;
                }
                pr.setPerfStep (p, i, v);
            }
        else
        {
            const auto dir = PresetManager::userPresetDirectory().getChildFile ("Patterns");
            dir.createDirectory();
            auto fc = std::make_shared<juce::FileChooser> (id == 20 ? "Save performer pattern" : "Load performer pattern", dir, "*.psxlperf");
            const int flags = id == 20 ? (juce::FileBrowserComponent::saveMode | juce::FileBrowserComponent::canSelectFiles | juce::FileBrowserComponent::warnAboutOverwriting)
                                       : (juce::FileBrowserComponent::openMode | juce::FileBrowserComponent::canSelectFiles);
            fc->launchAsync (flags, [safe, fc, id, p] (const juce::FileChooser& c)
            {
                auto f = c.getResult();
                if (safe == nullptr || f == juce::File()) return;
                if (id == 20)
                {
                    juce::StringArray vals;
                    for (int i = 0; i < kPerfSteps; ++i) vals.add (String (safe->proc.getPerfStep (p, i), 3));
                    f.withFileExtension ("psxlperf").replaceWithText (vals.joinIntoString (","));
                }
                else
                {
                    juce::StringArray vals; vals.addTokens (f.loadFileAsString(), ",", "");
                    for (int i = 0; i < juce::jmin (kPerfSteps, vals.size()); ++i) safe->proc.setPerfStep (p, i, vals[i].getFloatValue());
                }
                safe->repaint();
            });
        }
        safe->repaint();
    });
}

// =============================================================================================
// VoiceView
// =============================================================================================
VoiceView::VoiceView (PSXLProcessor& p)
    : proc (p), modeCombo (p, "voice_mode"), expoToggle (p, "glide_expo", "Expo")
{
    addAndMakeVisible (modeCombo); addAndMakeVisible (expoToggle);
    static const std::pair<const char*, const char*> voiceKnobs[] = { { "voices", "Polyphony" }, { "glide", "Glide" }, { "bend_range", "Bend Range" }, { "vel_sens", "Vel Sens" } };
    for (const auto& k : voiceKnobs)
    { knobs.push_back (std::make_unique<PSKnob> (p, k.first, k.second, true)); addAndMakeVisible (*knobs.back()); }
    addAndMakeVisible (importBtn); addAndMakeVisible (scalaBtn); addAndMakeVisible (resetTuneBtn);
    proc.addChangeListener (this);

    importBtn.onClick = [this]
    {
        chooser = std::make_shared<juce::FileChooser> ("Import wavetable (single-cycle or multi-frame audio file)", juce::File(), "*.wav;*.aif;*.aiff;*.flac;*.ogg");
        chooser->launchAsync (juce::FileBrowserComponent::openMode | juce::FileBrowserComponent::canSelectFiles, [this] (const juce::FileChooser& c)
        {
            if (c.getResult() == juce::File()) return;
            const int slot = proc.importWavetable (c.getResult());
            if (slot >= 0) { if (auto* prm = proc.apvts.getParameter ("o1_wt")) prm->setValueNotifyingHost (prm->convertTo0to1 ((float) slot)); toast ("Imported \"" + proc.getTableName (slot) + "\" into Osc 1"); }
            else toast ("Could not read that audio file");
        });
    };
    scalaBtn.onClick = [this]
    {
        chooser = std::make_shared<juce::FileChooser> ("Load Scala tuning", juce::File(), "*.scl");
        chooser->launchAsync (juce::FileBrowserComponent::openMode | juce::FileBrowserComponent::canSelectFiles, [this] (const juce::FileChooser& c)
        {
            if (c.getResult() == juce::File()) return;
            toast (proc.loadScala (c.getResult()) ? "Tuning loaded: " + proc.getTuningName() : "Not a valid .scl file");
        });
    };
    resetTuneBtn.onClick = [this] { proc.resetTuning(); };
}

VoiceView::~VoiceView() { proc.removeChangeListener (this); }

void VoiceView::resized()
{
    auto r = getLocalBounds().reduced (14);
    auto left = r.removeFromLeft (r.getWidth() / 2);
    left.removeFromTop (18);
    modeCombo.setBounds (left.removeFromTop (26).removeFromLeft (130));
    left.removeFromTop (10);
    auto row = left.removeFromTop (80);
    for (auto& k : knobs) k->setBounds (row.removeFromLeft (80).reduced (4));
    expoToggle.setBounds (left.removeFromTop (28).removeFromLeft (80).translated (0, 4));
    r.removeFromLeft (16);
    r.removeFromTop (18);
    importBtn.setBounds (r.removeFromTop (26).removeFromLeft (180));
    r.removeFromTop (150);
    auto t = r.removeFromTop (26);
    scalaBtn.setBounds (t.removeFromLeft (170)); t.removeFromLeft (6); resetTuneBtn.setBounds (t.removeFromLeft (70));
}

void VoiceView::paint (Graphics& g)
{
    const auto& pal = Theme::p();
    drawPanel (g, getLocalBounds().toFloat(), {});
    g.setColour (pal.textDim); g.setFont (Theme::font (11.0f, true));
    auto r = getLocalBounds().reduced (14);
    g.drawText ("VOICE", r.getX(), r.getY() - 6, 200, 16, juce::Justification::centredLeft);
    const int rx = r.getX() + r.getWidth() / 2 + 16;
    g.drawText ("WAVETABLE LIBRARY  (drop an audio file on the oscillator display to import)", rx, r.getY() - 6, 420, 16, juce::Justification::centredLeft);
    g.setFont (Theme::font (12.0f));
    int y = r.getY() + 54;
    for (int s = kNumBuiltinTables; s < kNumTableSlots && y < r.getBottom() - 50; ++s)
        if (proc.isTableLoaded (s)) { g.setColour (pal.text); g.drawText ("User " + String (s - kNumBuiltinTables + 1) + ":  " + proc.getTableName (s), rx, y, 360, 16, juce::Justification::centredLeft); y += 16; }
    if (y == r.getY() + 54) { g.setColour (pal.textDim); g.drawText ("No user wavetables loaded", rx, y, 300, 16, juce::Justification::centredLeft); }
    g.setColour (pal.textDim); g.setFont (Theme::font (11.0f, true));
    g.drawText ("MICROTUNING:  " + proc.getTuningName(), rx, r.getBottom() - 56, 460, 16, juce::Justification::centredLeft);
}
} // namespace psxl
