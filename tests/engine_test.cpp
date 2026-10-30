// Offline test: drives the real plugin processor without a host and checks the audio it produces.
#include "PluginProcessor.h"
#include <iostream>

using namespace psxl;

static int failures = 0;
#define CHECK(cond, msg) do { if (!(cond)) { ++failures; std::cout << "  FAIL: " << msg << std::endl; } else { std::cout << "  ok:   " << msg << std::endl; } } while (0)

static void setParam (PSXLProcessor& p, const juce::String& id, float raw)
{
    auto* prm = p.apvts.getParameter (id);
    jassert (prm != nullptr);
    prm->setValueNotifyingHost (prm->convertTo0to1 (raw));
}

struct Result { float peak = 0, rms = 0, freq = 0; bool finite = true; juce::AudioBuffer<float> audio; };

static Result render (PSXLProcessor& p, int note, float seconds, float noteLen, double sr = 48000.0)
{
    const int block = 512, total = (int) (seconds * sr);
    p.prepareToPlay (sr, block);
    Result r; r.audio.setSize (2, total);
    juce::MidiBuffer midi;
    juce::AudioBuffer<float> buf (2, block);
    for (int pos = 0; pos < total; pos += block)
    {
        midi.clear();
        if (pos == 0) midi.addEvent (juce::MidiMessage::noteOn (1, note, 0.8f), 0);
        const int offAt = (int) (noteLen * sr);
        if (offAt >= pos && offAt < pos + block) midi.addEvent (juce::MidiMessage::noteOff (1, note), offAt - pos);
        buf.clear();
        p.processBlock (buf, midi);
        const int n = juce::jmin (block, total - pos);
        for (int c = 0; c < 2; ++c) r.audio.copyFrom (c, pos, buf, c, 0, n);
    }
    double sum = 0;
    for (int i = 0; i < total; ++i)
    {
        const float v = r.audio.getSample (0, i);
        if (! std::isfinite (v)) r.finite = false;
        r.peak = juce::jmax (r.peak, std::abs (v)); sum += (double) v * v;
    }
    r.rms = (float) std::sqrt (sum / total);
    // fundamental estimate by autocorrelation on a steady segment
    const int start = (int) (0.1 * sr), len = 4096;
    if (start + len + 2000 < total)
    {
        double best = 0; int bestLag = 0;
        for (int lag = (int) (sr / 2000); lag < (int) (sr / 40); ++lag)
        {
            double acc = 0;
            for (int i = 0; i < len; ++i) acc += (double) r.audio.getSample (0, start + i) * r.audio.getSample (0, start + i + lag);
            if (acc > best) { best = acc; bestLag = lag; }
        }
        if (bestLag > 0) r.freq = (float) (sr / bestLag);
    }
    return r;
}

static void writeWav (const juce::File& f, const juce::AudioBuffer<float>& b, double sr)
{
    f.deleteFile();
    juce::WavAudioFormat wav;
    if (auto stream = f.createOutputStream())
        if (std::unique_ptr<juce::AudioFormatWriter> w (wav.createWriterFor (stream.release(), sr, 2, 16, {}, 0)); w != nullptr)
            w->writeFromAudioSampleBuffer (b, 0, b.getNumSamples());
}

int main (int argc, char** argv)
{
    juce::ScopedJuceInitialiser_GUI init;
    juce::File outDir = argc > 1 ? juce::File (argv[1]) : juce::File::getCurrentWorkingDirectory();
    outDir.createDirectory();

    PSXLProcessor p;
    std::cout << "factory presets: " << p.presets.numFactory() << std::endl;

    std::cout << "[1] blank init produces silence" << std::endl;
    p.initBlank();
    auto r = render (p, 60, 0.5f, 0.3f);
    CHECK (r.peak == 0.0f, "no routing -> exactly silent");

    std::cout << "[2] Osc1 -> Out plays at the right pitch" << std::endl;
    p.setRoute (N_Osc1, N_Filt1 - N_Filt1 + 3, 1.0f);   // dst index 3 = Out
    setParam (p, "f1_cut", 20000.f);
    r = render (p, 60, 1.0f, 0.6f);
    std::cout << "     peak " << r.peak << " rms " << r.rms << " freq " << r.freq << std::endl;
    CHECK (r.finite && r.peak > 0.05f && r.peak < 1.2f, "audible, finite, not clipping");
    CHECK (std::abs (r.freq - 261.6f) < 4.0f, "fundamental ~261.6 Hz");
    writeWav (outDir.getChildFile ("test_osc1.wav"), r.audio, 48000.0);

    std::cout << "[3] every wavetable x filter model/mode is finite and bounded" << std::endl;
    int bad = 0;
    p.setRoute (N_Osc1, 0, 1.0f); p.setRoute (N_Filt1, 1, 1.0f); p.setRoute (N_Filt2, 3, 1.0f);   // Osc1 -> F1 -> F2 -> Out
    for (int wt = 0; wt < kNumBuiltinTables; ++wt)
        for (int model = 0; model < 4; ++model)
            for (int mode = 0; mode < 4; ++mode)
            {
                setParam (p, "o1_wt", (float) wt); setParam (p, "f1_model", (float) model); setParam (p, "f1_mode", (float) mode);
                setParam (p, "f2_model", (float) ((model + 1) % 4)); setParam (p, "f1_res", 0.9f); setParam (p, "f1_cut", 900.f); setParam (p, "o1_uni", 4.f);
                auto t = render (p, 48, 0.4f, 0.25f);
                if (! t.finite || t.peak > 2.0f) { ++bad; std::cout << "     bad: wt " << wt << " model " << model << " mode " << mode << " peak " << t.peak << std::endl; }
            }
    CHECK (bad == 0, "no NaN/Inf/blow-ups across 160 combinations");

    std::cout << "[4] smart macro naming" << std::endl;
    p.initBlank();
    juce::String err;
    CHECK (p.getMacroName (0) == "Macro 1", "macro starts with default name");
    CHECK (p.addAssignment (S_Macro1, D_F1_CUT, 0.5f, err), "assign macro 1 -> filter 1 cutoff");
    std::cout << "     macro 1 is now named '" << p.getMacroName (0) << "', host param name '" << p.macroParam (0)->getName (64) << "'" << std::endl;
    CHECK (p.getMacroName (0) == "Filter 1 Cutoff", "macro renamed to the parameter name");
    CHECK (p.macroParam (0)->getName (64) == "Filter 1 Cutoff", "host-visible parameter name updated");
    CHECK (! p.addAssignment (S_Mod1 + 2, D_REV_MIX, 0.5f, err), "voice modulator cannot target global FX");
    p.setMacroName (1, "My Name");
    p.addAssignment (S_Macro1 + 1, D_O1_POS, 0.5f, err);
    CHECK (p.getMacroName (1) == "My Name", "user-named macro keeps its name");
    p.undoManager.undo();
    p.undoManager.undo();
    std::cout << "     after undo: macro 1 = '" << p.getMacroName (0) << "'" << std::endl;

    std::cout << "[5] macro modulates cutoff" << std::endl;
    p.initBlank();
    p.setRoute (N_Osc1, 0, 1.0f); p.setRoute (N_Filt1, 3, 1.0f);
    setParam (p, "o1_wt", 2.f); setParam (p, "f1_cut", 300.f); setParam (p, "f1_res", 0.2f);
    auto dark = render (p, 48, 0.5f, 0.4f);
    p.addAssignment (S_Macro1, D_F1_CUT, 0.8f, err);
    setParam (p, "macro1", 1.0f);
    auto bright = render (p, 48, 0.5f, 0.4f);
    std::cout << "     rms dark " << dark.rms << " bright " << bright.rms << std::endl;
    CHECK (bright.rms > dark.rms * 1.3f, "raising the macro opens the filter");

    std::cout << "[6] preset round trip" << std::endl;
    p.setRoute (N_Noise, 3, 0.7f);
    juce::MemoryBlock mb; p.getStateInformation (mb);
    PSXLProcessor q; q.setStateInformation (mb.getData(), (int) mb.getSize());
    CHECK (std::abs (q.getRoute (N_Noise, 3) - 0.7f) < 1.0e-4f, "route survives state save/load");
    CHECK (q.getAssignments().size() == p.getAssignments().size(), "assignments survive state save/load");
    CHECK (q.getMacroName (0) == "Filter 1 Cutoff", "macro name survives state save/load");

    std::cout << "[7] factory presets" << std::endl;
    int presetBad = 0;
    for (int i = 0; i < p.presets.numFactory(); ++i)
    {
        p.loadPresetIndex (i);
        auto t = render (p, 48, 1.2f, 0.7f);
        if (! t.finite || t.peak > 1.5f || t.peak < 0.001f) { ++presetBad; std::cout << "     preset '" << p.presetName << "' peak " << t.peak << std::endl; }
        if (i % 8 == 0) writeWav (outDir.getChildFile ("preset_" + juce::String (i) + ".wav"), t.audio, 48000.0);
    }
    CHECK (presetBad == 0, "all factory presets render audibly and safely");

    std::cout << (failures == 0 ? "ALL TESTS PASSED" : "TESTS FAILED") << std::endl;
    return failures;
}
