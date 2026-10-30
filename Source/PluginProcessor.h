#pragma once
#include <juce_audio_utils/juce_audio_utils.h>
#include "Params.h"
#include "PresetManager.h"
#include "Tuning.h"
#include "dsp/Engine.h"

namespace psxl
{
struct Assignment { int src = 0; int dest = 0; float amount = 0.5f; };

// Everything that is not a plain automatable parameter: routing, modulation assignments, macro names.
struct Structure
{
    float route[kRouteSrc][kRouteDst] {};
    std::vector<Assignment> assigns;
    std::array<juce::String, kNumMacros> macroName;
    std::array<bool, kNumMacros> macroUser {};
};

class PSXLProcessor : public juce::AudioProcessor, public juce::ChangeBroadcaster
{
public:
    PSXLProcessor();
    ~PSXLProcessor() override;

    // --- juce::AudioProcessor ---
    void prepareToPlay (double sampleRate, int samplesPerBlock) override;
    void releaseResources() override {}
    bool isBusesLayoutSupported (const BusesLayout& layouts) const override;
    void processBlock (juce::AudioBuffer<float>&, juce::MidiBuffer&) override;
    juce::AudioProcessorEditor* createEditor() override;
    bool hasEditor() const override { return true; }
    const juce::String getName() const override { return "Massive PSXL"; }
    bool acceptsMidi() const override { return true; }
    bool producesMidi() const override { return false; }
    bool isMidiEffect() const override { return false; }
    double getTailLengthSeconds() const override { return 4.0; }
    int getNumPrograms() override { return juce::jmax (1, presets.numFactory()); }
    int getCurrentProgram() override { return currentProgram; }
    void setCurrentProgram (int index) override;
    const juce::String getProgramName (int index) override;
    void changeProgramName (int, const juce::String&) override {}
    void getStateInformation (juce::MemoryBlock&) override;
    void setStateInformation (const void*, int) override;

    // --- shared objects used by the editor ---
    juce::UndoManager undoManager;
    juce::AudioProcessorValueTreeState apvts;
    EngineShared shared;
    juce::MidiKeyboardState keyboardState;
    juce::MidiMessageCollector uiMidi;      // wheels and other UI-generated MIDI
    PresetManager presets;
    juce::PropertiesFile& getSettings() { return *settings; }

    // --- routing ---
    float getRoute (int src, int dstIdx) const { return structure.route[src][dstIdx]; }
    void setRoute (int src, int dstIdx, float gain);          // gain <= 0 removes the wire
    void clearRouting();

    // --- modulation assignments ---
    bool addAssignment (int src, int dest, float amount, juce::String& error);
    void setAssignmentAmount (int src, int dest, float amount);
    void removeAssignment (int src, int dest);
    std::vector<Assignment> getAssignments() const { return structure.assigns; }
    std::vector<Assignment> assignmentsForDest (int dest) const;
    int countAssignmentsForSource (int src) const;

    // --- macros (host-visible names update automatically) ---
    juce::String getMacroName (int i) const { return structure.macroName[(size_t) i]; }
    bool isMacroUserNamed (int i) const { return structure.macroUser[(size_t) i]; }
    void setMacroName (int i, const juce::String& name);       // empty restores the default

    // --- performers ---
    void setPerfStep (int p, int step, float value);
    float getPerfStep (int p, int step) const { return shared.perfSteps[p][step].load(); }
    void randomisePerf (int p);

    // --- wavetables ---
    juce::String getTableName (int slot) const;
    bool isTableLoaded (int slot) const { return shared.tables[slot].load() != nullptr; }
    int importWavetable (const juce::File& file);              // returns slot or -1
    const Wavetable* getTable (int slot) const { return shared.tables[slot].load(); }

    // --- tuning ---
    bool loadScala (const juce::File& file);
    void resetTuning();
    juce::String getTuningName() const { return tuningName; }

    // --- presets ---
    void initBlank();
    void loadPresetIndex (int index);
    bool loadPresetXml (const juce::XmlElement& xml, bool fromHostState = false);
    std::unique_ptr<juce::XmlElement> exportXml (bool includeTables) const;
    juce::String presetName = "Init (Blank)", presetCategory = "Init";
    void saveUserPreset (const juce::String& name, const juce::String& category);
    void mutateSound (float amount);

    // --- MIDI learn ---
    void startMidiLearn (const juce::String& paramId);
    void cancelMidiLearn() { learnTarget = -1; }
    bool isLearning() const { return learnTarget.load() >= 0; }
    juce::String learningParamId() const;
    juce::String ccForParam (const juce::String& paramId) const;
    void clearMidiMapping (const juce::String& paramId);

    MacroParameter* macroParam (int i) const { return macros[(size_t) i]; }

private:
    friend class StructureAction;
    void changeStructure (const std::function<void (Structure&)>& mutate, const juce::String& name);
    void applyStructure (const Structure& s);
    void publishStructure();
    void installTable (int slot, std::shared_ptr<Wavetable> wt);

    Structure structure;
    ParamPtrs ptrs;
    BlockParams bp;
    SynthEngine engine;
    std::vector<std::shared_ptr<Wavetable>> tableStore;   // tables are retained for the plugin's lifetime (audio thread holds raw pointers)
    std::array<juce::MemoryBlock, kNumTableSlots> tableBytes;
    std::array<juce::String, kNumTableSlots> tableNames;
    std::array<MacroParameter*, kNumMacros> macros {};
    std::vector<juce::RangedAudioParameter*> paramList;
    std::atomic<int> ccMap[128];
    std::atomic<int> learnTarget { -1 };
    std::unique_ptr<juce::PropertiesFile> settings;
    juce::String tuningName = "12-tone equal", tuningText;
    int currentProgram = 0;
    juce::Random rng;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (PSXLProcessor)
};
} // namespace psxl
