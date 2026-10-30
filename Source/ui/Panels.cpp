#include "Panels.h"

namespace psxl
{
using juce::Graphics;
using juce::Rectangle;
using juce::String;

// =============================================================================================
PitchPanel::PitchPanel (PSXLProcessor& p)
    : pitch (p, "pitch", "Pitch", true), glide (p, "glide", "Glide"), mode (p, "voice_mode"), expo (p, "glide_expo", "Expo")
{
    addAndMakeVisible (pitch); addAndMakeVisible (glide); addAndMakeVisible (mode); addAndMakeVisible (expo);
}
void PitchPanel::paint (Graphics& g) { drawPanel (g, getLocalBounds().toFloat(), "PITCH"); }
void PitchPanel::resized()
{
    pitch.setBounds (10, 28, 80, 96);
    glide.setBounds (20, 132, 60, 66);
    mode.setBounds (10, 206, 80, 24);
    expo.setBounds (10, 236, 80, 22);
}

// =============================================================================================
OscPanel::OscPanel (PSXLProcessor& p) : proc (p), view (p)
{
    tabs.setTabs ({ "Osc 1", "Osc 2" });
    tabs.onChange = [this] (int i) { showOsc (i + 1); };
    addAndMakeVisible (tabs); addAndMakeVisible (view);
    addAndMakeVisible (tableBox); addAndMakeVisible (prev); addAndMakeVisible (next); addAndMakeVisible (importBtn);
    importBtn.setTooltip ("Import a wavetable from an audio file (or drop one on the display)");

    static const std::pair<const char*, const char*> defs[] = { { "pos", "Pos" }, { "pitch", "Pitch" }, { "fine", "Fine" }, { "level", "Level" },
                                                                { "uni", "Unison" }, { "detune", "Detune" }, { "pm", "PhaseMod" }, { "fold", "Fold" } };
    for (int o = 1; o <= 2; ++o)
        for (const auto& d : defs)
        {
            knobs[o - 1].push_back (std::make_unique<PSKnob> (p, oscId (o, d.first), d.second));
            addChildComponent (*knobs[o - 1].back());
        }

    tableBox.onChange = [this]
    {
        const int slot = tableBox.getSelectedId() - 1;
        if (slot >= 0)
            if (auto* prm = proc.apvts.getParameter (oscId (osc, "wt"))) prm->setValueNotifyingHost (prm->convertTo0to1 ((float) slot));
    };
    prev.onClick = [this] { stepTable (-1); };
    next.onClick = [this] { stepTable (1); };
    importBtn.onClick = [this]
    {
        chooser = std::make_shared<juce::FileChooser> ("Import wavetable", juce::File(), "*.wav;*.aif;*.aiff;*.flac;*.ogg");
        chooser->launchAsync (juce::FileBrowserComponent::openMode | juce::FileBrowserComponent::canSelectFiles, [this] (const juce::FileChooser& c)
        {
            if (c.getResult() == juce::File()) return;
            const int slot = proc.importWavetable (c.getResult());
            if (slot < 0) { toast ("Could not read that audio file"); return; }
            if (auto* prm = proc.apvts.getParameter (oscId (osc, "wt"))) prm->setValueNotifyingHost (prm->convertTo0to1 ((float) slot));
            toast ("Imported \"" + proc.getTableName (slot) + "\"");
        });
    };
    proc.addChangeListener (this);
    refreshTables();
    showOsc (1);
    startTimerHz (10);
}

OscPanel::~OscPanel() { proc.removeChangeListener (this); }

void OscPanel::refreshTables()
{
    tableBox.clear (juce::dontSendNotification);
    for (int s = 0; s < kNumTableSlots; ++s)
        if (proc.isTableLoaded (s)) tableBox.addItem (String (s < kNumBuiltinTables ? "" : "User: ") + proc.getTableName (s), s + 1);
    timerCallback();
}

void OscPanel::timerCallback()
{
    const int slot = (int) proc.apvts.getRawParameterValue (oscId (osc, "wt"))->load();
    if (tableBox.getSelectedId() != slot + 1) tableBox.setSelectedId (slot + 1, juce::dontSendNotification);
}

void OscPanel::stepTable (int dir)
{
    int slot = (int) proc.apvts.getRawParameterValue (oscId (osc, "wt"))->load();
    for (int i = 0; i < kNumTableSlots; ++i)
    {
        slot = (slot + dir + kNumTableSlots) % kNumTableSlots;
        if (proc.isTableLoaded (slot)) break;
    }
    if (auto* prm = proc.apvts.getParameter (oscId (osc, "wt"))) prm->setValueNotifyingHost (prm->convertTo0to1 ((float) slot));
}

void OscPanel::showOsc (int o)
{
    osc = o;
    view.setOsc (o);
    for (int i = 0; i < 2; ++i) for (auto& k : knobs[i]) k->setVisible (i == o - 1);
    tabs.setSelected (o - 1, false);
    timerCallback();
}

void OscPanel::paint (Graphics& g) { drawPanel (g, getLocalBounds().toFloat(), {}); }

void OscPanel::resized()
{
    auto r = getLocalBounds().reduced (10, 8);
    tabs.setBounds (r.removeFromTop (22));
    r.removeFromTop (4);
    view.setBounds (r.removeFromTop (104));
    r.removeFromTop (4);
    auto row = r.removeFromTop (24);
    prev.setBounds (row.removeFromLeft (26)); row.removeFromLeft (4);
    importBtn.setBounds (row.removeFromRight (30)); row.removeFromRight (4);
    next.setBounds (row.removeFromRight (26)); row.removeFromRight (4);
    tableBox.setBounds (row);
    r.removeFromTop (6);
    const int cw = r.getWidth() / 8;
    for (int i = 0; i < 2; ++i)
    {
        auto kr = r;
        for (auto& k : knobs[i]) k->setBounds (kr.removeFromLeft (cw).withHeight (70));
    }
}

// =============================================================================================
NoisePanel::NoisePanel (PSXLProcessor& p) : level (p, "n_level", "Level", true), color (p, "n_color", "Color", true), type (p, "n_type")
{
    addAndMakeVisible (level); addAndMakeVisible (color); addAndMakeVisible (type);
}
void NoisePanel::paint (Graphics& g) { drawPanel (g, getLocalBounds().toFloat(), "NOISE"); }
void NoisePanel::resized()
{
    level.setBounds (8, 30, 80, 88);
    color.setBounds (8, 124, 80, 88);
    type.setBounds (8, 222, 80, 24);
}

// =============================================================================================
FilterPanel::FilterPanel (PSXLProcessor& p) : proc (p)
{
    tabs.setTabs ({ "Filter 1", "Filter 2" }, { Theme::p().accent2, Theme::p().accent2 });
    tabs.onChange = [this] (int i) { showFilter (i + 1); };
    addAndMakeVisible (tabs);
    static const std::pair<const char*, const char*> defs[] = { { "cut", "Cutoff" }, { "res", "Reso" }, { "drive", "Drive" }, { "ktr", "KeyTrk" } };
    for (int f = 1; f <= 2; ++f)
    {
        model[f - 1] = std::make_unique<PSCombo> (p, filtId (f, "model"));
        mode[f - 1] = std::make_unique<PSCombo> (p, filtId (f, "mode"));
        addChildComponent (*model[f - 1]); addChildComponent (*mode[f - 1]);
        for (const auto& d : defs)
        {
            knobs[f - 1].push_back (std::make_unique<PSKnob> (p, filtId (f, d.first), d.second, String (d.first) == "cut"));
            addChildComponent (*knobs[f - 1].back());
        }
    }
    showFilter (1);
    startTimerHz (10);
}

void FilterPanel::timerCallback()
{
    for (int f = 0; f < 2; ++f)
    {
        const int m = (int) proc.apvts.getRawParameterValue (filtId (f + 1, "model"))->load();
        if (m != shownModel[f]) { shownModel[f] = m; mode[f]->refreshItems (filterModeNames (m)); }
    }
}

void FilterPanel::showFilter (int f)
{
    filt = f;
    for (int i = 0; i < 2; ++i)
    {
        model[i]->setVisible (i == f - 1); mode[i]->setVisible (i == f - 1);
        for (auto& k : knobs[i]) k->setVisible (i == f - 1);
    }
    tabs.setSelected (f - 1, false);
}

void FilterPanel::paint (Graphics& g) { drawPanel (g, getLocalBounds().toFloat(), {}); }

void FilterPanel::resized()
{
    auto r = getLocalBounds().reduced (10, 8);
    tabs.setBounds (r.removeFromTop (22));
    r.removeFromTop (6);
    for (int i = 0; i < 2; ++i)
    {
        auto row = r.withHeight (24);
        model[i]->setBounds (row.removeFromLeft (row.getWidth() / 2 - 3));
        row.removeFromLeft (6);
        mode[i]->setBounds (row);
        auto cut = r.withTrimmedTop (32).withHeight (112).withSizeKeepingCentre (110, 112);
        knobs[i][0]->setBounds (cut);
        auto small = Rectangle<int> (r.getX(), r.getY() + 150, r.getWidth(), 72);
        const int w = small.getWidth() / 3;
        for (int k = 1; k < 4; ++k) knobs[i][(size_t) k]->setBounds (small.removeFromLeft (w).reduced (2));
    }
}

// =============================================================================================
InsertPanel::InsertPanel (PSXLProcessor& p) : type (p, "ins_type"), drive (p, "ins_drive", "Drive", true), mix (p, "ins_mix", "Mix", true)
{
    addAndMakeVisible (type); addAndMakeVisible (drive); addAndMakeVisible (mix);
}
void InsertPanel::paint (Graphics& g) { drawPanel (g, getLocalBounds().toFloat(), "INSERT"); }
void InsertPanel::resized()
{
    type.setBounds (10, 28, 104, 24);
    drive.setBounds (14, 62, 96, 100);
    mix.setBounds (22, 170, 80, 84);
}

AmpPanel::AmpPanel (PSXLProcessor& p) : level (p, "amp_level", "Level", true), pan (p, "amp_pan", "Pan", true), feedback (p, "amp_fb", "Feedback", true)
{
    addAndMakeVisible (level); addAndMakeVisible (pan); addAndMakeVisible (feedback);
}
void AmpPanel::paint (Graphics& g) { drawPanel (g, getLocalBounds().toFloat(), "AMP"); }
void AmpPanel::resized()
{
    level.setBounds (8, 28, 76, 78);
    pan.setBounds (8, 110, 76, 78);
    feedback.setBounds (8, 192, 76, 78);
}

// =============================================================================================
FxPanel::FxPanel (PSXLProcessor& p) : proc (p)
{
    tabs.setTabs ({ "EQ", "Delay", "Verb", "Chor", "Dist" }, { Theme::p().accent, Theme::p().accent, Theme::p().accent, Theme::p().accent, Theme::p().accent });
    tabs.onChange = [this] (int i) { showTab (i); };
    addAndMakeVisible (tabs);

    struct Def { const char* id; const char* label; };
    auto make = [&] (std::initializer_list<Def> defs)
    {
        Group g;
        for (auto& d : defs) g.items.push_back (std::make_unique<PSKnob> (p, d.id, d.label));
        return g;
    };
    groups.push_back (make ({ { "eq_lo_g", "Lo Gain" }, { "eq_lo_f", "Lo Freq" }, { "eq_mid_g", "Mid Gain" }, { "eq_mid_f", "Mid Freq" },
                              { "eq_mid_q", "Mid Q" }, { "eq_hi_g", "Hi Gain" }, { "eq_hi_f", "Hi Freq" } }));
    {
        auto g = make ({ { "dly_time", "Time" }, { "dly_fb", "Feedback" }, { "dly_mix", "Mix" } });
        g.items.push_back (std::make_unique<PSToggle> (p, "dly_sync", "Sync"));
        g.items.push_back (std::make_unique<PSCombo> (p, "dly_div"));
        groups.push_back (std::move (g));
    }
    groups.push_back (make ({ { "rev_size", "Size" }, { "rev_damp", "Damping" }, { "rev_mix", "Mix" } }));
    groups.push_back (make ({ { "cho_rate", "Rate" }, { "cho_depth", "Depth" }, { "cho_mix", "Mix" } }));
    groups.push_back (make ({ { "dist_drive", "Drive" }, { "dist_mix", "Mix" } }));
    for (auto& g : groups) for (auto& c : g.items) addChildComponent (*c);
    showTab (0);
}

void FxPanel::showTab (int t)
{
    tab = t;
    for (size_t i = 0; i < groups.size(); ++i) for (auto& c : groups[i].items) c->setVisible ((int) i == t);
    tabs.setSelected (t, false);
}

void FxPanel::paint (Graphics& g) { drawPanel (g, getLocalBounds().toFloat(), {}); }

void FxPanel::resized()
{
    auto r = getLocalBounds().reduced (8, 8);
    tabs.setBounds (r.removeFromTop (22));
    r.removeFromTop (8);
    const int cols = 4, cw = r.getWidth() / cols, ch = 84;
    for (auto& g : groups)
    {
        int i = 0;
        for (auto& c : g.items)
        {
            Rectangle<int> cell (r.getX() + (i % cols) * cw, r.getY() + (i / cols) * ch, cw, ch);
            if (dynamic_cast<PSKnob*> (c.get())) c->setBounds (cell.reduced (1));
            else c->setBounds (cell.withSizeKeepingCentre (cw * (dynamic_cast<PSCombo*> (c.get()) ? 2 : 1) - 6, 24));
            ++i;
        }
    }
}
} // namespace psxl
