#include "PluginEditor.h"
#include "BinaryData.h"

namespace psxl
{
using juce::Graphics;
using juce::Rectangle;
using juce::String;

namespace
{
constexpr int kBaseW = 1260, kBaseH = 700, kKeysH = 150;
constexpr int kBarH = 44, kSynthY = 48, kSynthH = 270, kTabY = 322, kTabH = 28, kLowerY = 354, kLowerH = 274, kMacroY = 632, kMacroH = 66;

juce::Image loadImage (const char* name)
{
    int size = 0;
    if (auto* data = BinaryData::getNamedResource (name, size)) return juce::ImageCache::getFromMemory (data, size);
    return {};
}
} // namespace

PSXLEditor::PSXLEditor (PSXLProcessor& p)
    : juce::AudioProcessorEditor (p), proc (p), masterKnob (p, "master_vol", "Volume", true),
      pitchPanel (p), oscPanel (p), noisePanel (p), filterPanel (p), insertPanel (p), ampPanel (p), fxPanel (p),
      voiceView (p), routingView (p), modEditor (p), perfEditor (p), macroStrip (p), keyboard (p), browser (p)
{
    auto& st = proc.getSettings();
    Theme::setDark (st.getBoolValue ("darkMode", true));
    laf.applyTheme();
    setLookAndFeel (&laf);
    kbOpen = st.getBoolValue ("keyboardOpen", false);
    scale = juce::jlimit (0.75, 2.0, st.getDoubleValue ("uiScale", 1.0));
    toastCallback() = [this] (const String& s) { showToast (s); };

    addAndMakeVisible (content);
    content.onPaint = [this] (Graphics& g) { paintContent (g); };

    for (auto* c : std::initializer_list<juce::Component*> { &menuBtn, &prevBtn, &nextBtn, &presetBtn, &undoBtn, &redoBtn, &themeBtn, &keysBtn, &mainTabs, &lowerTabs, &masterKnob,
                                                             &pitchPanel, &oscPanel, &noisePanel, &filterPanel, &insertPanel, &ampPanel, &fxPanel,
                                                             &voiceView, &routingView, &modEditor, &perfEditor, &macroStrip, &keyboard })
        content.addAndMakeVisible (*c);
    content.addChildComponent (browser);
    content.setSize (kBaseW, kBaseH);

    mainTabs.setTabs ({ "Edit", "Browse" });
    mainTabs.onChange = [this] (int i) { setBrowsing (i == 1); };

    juce::StringArray names { "Voice", "Routing", "Amp Env" };
    std::vector<juce::Colour> cols { Theme::p().textDim, Theme::p().text, Theme::p().accent };
    for (int s = 2; s <= kNumMods; ++s) { names.add ("Mod " + String (s)); cols.push_back (Theme::p().accent); }
    for (int i = 1; i <= kNumPerf; ++i) { names.add ("Perf " + String (i)); cols.push_back (Theme::p().accent3); }
    lowerTabs.setTabs (names, cols);
    lowerTabs.onChange = [this] (int i) { showLower (i); };

    menuBtn.onClick = [this] { showMainMenu(); };
    prevBtn.onClick = [this] { stepPreset (-1); };
    nextBtn.onClick = [this] { stepPreset (1); };
    presetBtn.onClick = [this] { mainTabs.setSelected (browsing ? 0 : 1); };
    undoBtn.onClick = [this] { proc.undoManager.undo(); };
    redoBtn.onClick = [this] { proc.undoManager.redo(); };
    themeBtn.onClick = [this] { setTheme (! Theme::isDark()); };
    keysBtn.onClick = [this] { toggleKeyboard(); };
    browser.onClose = [this] { mainTabs.setSelected (0); };

    keyboard.setVisible (kbOpen);
    keysBtn.setToggleState (kbOpen, juce::dontSendNotification);
    presetBtn.setButtonText (proc.presetName);
    themeBtn.setButtonText (Theme::isDark() ? "Light" : "Dark");
    showLower (1);
    lowerTabs.setSelected (1, false);

    setConstrainer (&constrainer);
    setResizable (true, true);
    updateSize();
    proc.addChangeListener (this);
    startTimerHz (30);
}

PSXLEditor::~PSXLEditor()
{
    stopTimer();
    proc.removeChangeListener (this);
    toastCallback() = nullptr;
    setLookAndFeel (nullptr);
}

int PSXLEditor::baseHeight() const { return kBaseH + (kbOpen ? kKeysH : 0); }

void PSXLEditor::updateSize()
{
    const int bh = baseHeight();
    constrainer.setFixedAspectRatio ((double) kBaseW / (double) bh);
    constrainer.setSizeLimits ((int) (kBaseW * 0.75), (int) (bh * 0.75), kBaseW * 2, bh * 2);
    content.setSize (kBaseW, bh);
    setSize (juce::roundToInt ((double) kBaseW * scale), juce::roundToInt ((double) bh * scale));
}

void PSXLEditor::setUiScale (double s)
{
    scale = juce::jlimit (0.75, 2.0, s);
    updateSize();
}

void PSXLEditor::toggleKeyboard()
{
    kbOpen = ! kbOpen;
    keyboard.setVisible (kbOpen);
    keysBtn.setToggleState (kbOpen, juce::dontSendNotification);
    proc.getSettings().setValue ("keyboardOpen", kbOpen);
    updateSize();
}

void PSXLEditor::setTheme (bool dark)
{
    Theme::setDark (dark);
    proc.getSettings().setValue ("darkMode", dark);
    laf.applyTheme();
    themeBtn.setButtonText (dark ? "Light" : "Dark");
    sendLookAndFeelChange();
    content.repaint();
    repaint();
}

void PSXLEditor::setBrowsing (bool b)
{
    browsing = b;
    if (b) { browser.refresh(); browser.setVisible (true); browser.toFront (false); }
    else browser.setVisible (false);
    mainTabs.setSelected (b ? 1 : 0, false);
}

void PSXLEditor::showLower (int i)
{
    voiceView.setVisible (i == 0);
    routingView.setVisible (i == 1);
    modEditor.setVisible (i >= 2 && i <= 10);
    perfEditor.setVisible (i >= 11);
    if (i >= 2 && i <= 10) modEditor.setSlot (i - 1);
    if (i >= 11) perfEditor.setPerf (i - 11);
}

void PSXLEditor::stepPreset (int dir)
{
    const auto& all = proc.presets.all();
    if (all.empty()) return;
    int cur = -1;
    for (int i = 0; i < (int) all.size(); ++i) if (all[(size_t) i].name == proc.presetName) cur = i;
    const int n = (int) all.size();
    const int next = cur < 0 ? (dir > 0 ? 0 : n - 1) : (cur + dir + n) % n;
    proc.loadPresetIndex (next);
}

void PSXLEditor::showToast (const String& s)
{
    toastText = s;
    toastUntil = juce::Time::getMillisecondCounter() + 3800;
    content.repaint();
}

void PSXLEditor::changeListenerCallback (juce::ChangeBroadcaster*)
{
    presetBtn.setButtonText (proc.presetName);
}

void PSXLEditor::timerCallback()
{
    content.repaint (meterRect);
    undoBtn.setEnabled (proc.undoManager.canUndo());
    redoBtn.setEnabled (proc.undoManager.canRedo());
    if (toastText.isNotEmpty())
    {
        if (juce::Time::getMillisecondCounter() > toastUntil) toastText.clear();
        content.repaint (0, kBarH, kBaseW, 36);
    }
}

void PSXLEditor::showMainMenu()
{
    juce::PopupMenu m, settings, scaleMenu, octMenu;
    m.addItem (1, "Load Init (Blank)");
    m.addItem (2, "Save preset...");
    m.addItem (3, "Open user preset folder");
    m.addSeparator();
    m.addItem (4, "Mutate sound (subtle)");
    m.addItem (5, "Mutate sound (wild)");
    m.addItem (6, "Undo", proc.undoManager.canUndo());
    m.addItem (7, "Redo", proc.undoManager.canRedo());
    m.addSeparator();
    settings.addItem (10, "Dark theme", true, Theme::isDark());
    settings.addItem (11, "Light theme", true, ! Theme::isDark());
    for (int pct : { 75, 100, 125, 150, 175, 200 }) scaleMenu.addItem (20 + pct, String (pct) + "%", true, std::abs (scale * 100.0 - pct) < 3.0);
    settings.addSubMenu ("Interface size", scaleMenu);
    for (int n = 2; n <= 8; ++n) octMenu.addItem (30 + n, String (n) + " octaves", true, keyboard.getOctaves() == n);
    settings.addSubMenu ("Keyboard size", octMenu);
    settings.addSeparator();
    settings.addItem (40, "Import wavetable...");
    settings.addItem (41, "Load Scala tuning (.scl)...");
    settings.addItem (42, "Reset tuning to 12-TET");
    m.addSubMenu ("Settings", settings);
    m.addSeparator();
    m.addItem (50, "About Massive PSXL");

    juce::Component::SafePointer<PSXLEditor> safe (this);
    m.showMenuAsync (juce::PopupMenu::Options().withTargetComponent (&menuBtn), [safe] (int id)
    {
        if (safe == nullptr || id == 0) return;
        auto& pr = safe->proc;
        if (id == 1) pr.initBlank();
        else if (id == 2) { safe->mainTabs.setSelected (1); }   // the browser hosts the save dialog
        else if (id == 3) { auto d = PresetManager::userPresetDirectory(); d.createDirectory(); d.revealToUser(); }
        else if (id == 4) pr.mutateSound (0.06f);
        else if (id == 5) pr.mutateSound (0.25f);
        else if (id == 6) pr.undoManager.undo();
        else if (id == 7) pr.undoManager.redo();
        else if (id == 10) safe->setTheme (true);
        else if (id == 11) safe->setTheme (false);
        else if (id >= 95 && id <= 220) safe->setUiScale ((double) (id - 20) / 100.0);
        else if (id >= 32 && id <= 38) { safe->keyboard.setOctaves (id - 30); pr.getSettings().setValue ("keyboardOctaves", id - 30); }
        else if (id == 40 || id == 41)
        {
            const bool wt = id == 40;
            safe->chooser = std::make_shared<juce::FileChooser> (wt ? "Import wavetable" : "Load Scala tuning", juce::File(), wt ? "*.wav;*.aif;*.aiff;*.flac;*.ogg" : "*.scl");
            safe->chooser->launchAsync (juce::FileBrowserComponent::openMode | juce::FileBrowserComponent::canSelectFiles, [safe, wt] (const juce::FileChooser& c)
            {
                if (safe == nullptr || c.getResult() == juce::File()) return;
                if (wt)
                {
                    const int slot = safe->proc.importWavetable (c.getResult());
                    if (slot >= 0) { if (auto* prm = safe->proc.apvts.getParameter ("o1_wt")) prm->setValueNotifyingHost (prm->convertTo0to1 ((float) slot)); safe->showToast ("Imported \"" + safe->proc.getTableName (slot) + "\" into Osc 1"); }
                    else safe->showToast ("Could not read that audio file");
                }
                else safe->showToast (safe->proc.loadScala (c.getResult()) ? "Tuning loaded: " + safe->proc.getTuningName() : "Not a valid .scl file");
            });
        }
        else if (id == 42) pr.resetTuning();
        else if (id == 50)
            juce::AlertWindow::showMessageBoxAsync (juce::MessageBoxIconType::InfoIcon, "About Massive PSXL",
                                                    "Massive PSXL 1.0.0\nWavetable synthesizer by Phil S Audio\n\nBuilt with the JUCE framework.", "OK");
    });
}

void PSXLEditor::paintContent (Graphics& g)
{
    const auto& p = Theme::p();
    const int h = content.getHeight();
    g.fillAll (p.bg);
    const auto bg = loadImage (Theme::isDark() ? "bg_dark_png" : "bg_light_png");
    if (bg.isValid())
    {
        g.setOpacity (Theme::isDark() ? 0.55f : 0.45f);
        g.drawImage (bg, 0, 0, kBaseW, h, 0, 0, bg.getWidth(), bg.getHeight());
        g.setOpacity (1.0f);
    }

    // top bar
    g.setColour (p.panel.withAlpha (0.92f));
    g.fillRect (0, 0, kBaseW, kBarH);
    g.setColour (p.outline);
    g.drawHorizontalLine (kBarH - 1, 0.0f, (float) kBaseW);
    const auto mark = loadImage ("logo_mark_png");
    if (mark.isValid()) g.drawImage (mark, juce::Rectangle<float> (8.0f, 5.0f, 34.0f, 34.0f), juce::RectanglePlacement::centred);
    g.setFont (Theme::font (17.0f, true));
    g.setColour (p.text);
    g.drawText ("MASSIVE", 48, 6, 90, 32, juce::Justification::centredLeft);
    g.setColour (p.accent);
    g.drawText ("PSXL", 128, 6, 70, 32, juce::Justification::centredLeft);
    g.setColour (p.textDim); g.setFont (Theme::font (9.5f));
    g.drawText ("Phil S Audio", 48, 28, 100, 12, juce::Justification::centredLeft);

    // output meters
    meterRect = Rectangle<int> (kBaseW - 22, 6, 12, 32);
    auto drawMeter = [&] (int x, float v)
    {
        const float lvl = juce::jlimit (0.0f, 1.0f, std::sqrt (v));
        g.setColour (p.knobTrack); g.fillRoundedRectangle ((float) x, 6.0f, 4.0f, 32.0f, 2.0f);
        g.setColour (lvl > 0.92f ? p.accent3 : p.good); g.fillRoundedRectangle ((float) x, 38.0f - 32.0f * lvl, 4.0f, 32.0f * lvl, 2.0f);
    };
    drawMeter (kBaseW - 22, proc.shared.outPeakL.load());
    drawMeter (kBaseW - 14, proc.shared.outPeakR.load());

    // toast
    if (toastText.isNotEmpty())
    {
        g.setFont (Theme::font (12.5f, true));
        const int w = juce::jmin (kBaseW - 40, juce::GlyphArrangement::getStringWidthInt (g.getCurrentFont(), toastText) + 36);
        auto r = Rectangle<int> (w, 26).withCentre ({ kBaseW / 2, kBarH + 14 });
        g.setColour (p.accent2.withAlpha (0.95f)); g.fillRoundedRectangle (r.toFloat(), 13.0f);
        g.setColour (juce::Colours::white);
        g.drawText (toastText, r, juce::Justification::centred);
    }
}

void PSXLEditor::resized()
{
    scale = juce::jmax (0.1, (double) getWidth() / (double) kBaseW);
    content.setTransform (juce::AffineTransform::scale ((float) scale));
    content.setBounds (0, 0, kBaseW, baseHeight());
    proc.getSettings().setValue ("uiScale", scale);

    menuBtn.setBounds (212, 8, 52, 28);
    mainTabs.setBounds (276, 8, 140, 28);
    prevBtn.setBounds (440, 8, 30, 28);
    presetBtn.setBounds (474, 8, 320, 28);
    nextBtn.setBounds (798, 8, 30, 28);
    keysBtn.setBounds (kBaseW - 100, 8, 64, 28);
    themeBtn.setBounds (kBaseW - 172, 8, 64, 28);
    redoBtn.setBounds (kBaseW - 228, 8, 52, 28);
    undoBtn.setBounds (kBaseW - 284, 8, 52, 28);
    masterKnob.setBounds (kBaseW - 346, 0, 56, 44);

    int x = 6;
    auto place = [&] (juce::Component& c, int w) { c.setBounds (x, kSynthY, w, kSynthH); x += w + 6; };
    place (pitchPanel, 100); place (oscPanel, 342); place (noisePanel, 96); place (filterPanel, 226);
    place (insertPanel, 124); place (ampPanel, 92); place (fxPanel, 232);

    lowerTabs.setBounds (6, kTabY, kBaseW - 12, kTabH);
    const Rectangle<int> lower (6, kLowerY, kBaseW - 12, kLowerH);
    voiceView.setBounds (lower); routingView.setBounds (lower); modEditor.setBounds (lower); perfEditor.setBounds (lower);
    browser.setBounds (6, kSynthY, kBaseW - 12, kLowerY + kLowerH - kSynthY);
    macroStrip.setBounds (6, kMacroY, kBaseW - 12, kMacroH);
    keyboard.setBounds (6, kBaseH + 2, kBaseW - 12, kKeysH - 6);
}
} // namespace psxl
