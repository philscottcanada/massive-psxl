#include "PluginProcessor.h"
#include "ui/PluginEditor.h"

namespace psxl
{
// Undoable swap between two structure snapshots (routing, assignments, macro names).
class StructureAction : public juce::UndoableAction
{
public:
    StructureAction (PSXLProcessor& p, Structure o, Structure n) : proc (p), oldS (std::move (o)), newS (std::move (n)) {}
    bool perform() override { proc.applyStructure (newS); return true; }
    bool undo() override { proc.applyStructure (oldS); return true; }
private:
    PSXLProcessor& proc;
    Structure oldS, newS;
};

static juce::PropertiesFile::Options settingsOptions()
{
    juce::PropertiesFile::Options o;
    o.applicationName = "Massive PSXL";
    o.filenameSuffix = ".settings";
    o.folderName = "Phil S Audio";
    o.osxLibrarySubFolder = "Application Support";
    o.commonToAllUsers = false;
    return o;
}

PSXLProcessor::PSXLProcessor()
    : AudioProcessor (BusesProperties().withOutput ("Output", juce::AudioChannelSet::stereo(), true)),
      apvts (*this, &undoManager, "PSXL", createParameterLayout()),
      engine (shared)
{
    settings = std::make_unique<juce::PropertiesFile> (settingsOptions());
    ptrs.bind (apvts);
    for (auto& c : ccMap) c = -1;

    for (auto* p : getParameters())
        if (auto* r = dynamic_cast<juce::RangedAudioParameter*> (p)) paramList.push_back (r);
    for (int i = 0; i < kNumMacros; ++i)
    {
        macros[(size_t) i] = dynamic_cast<MacroParameter*> (apvts.getParameter (macroId (i)));
        structure.macroName[(size_t) i] = "Macro " + juce::String (i + 1);
    }

    for (int i = 0; i < kNumBuiltinTables; ++i) installTable (i, Wavetable::createBuiltin (i));
    publishStructure();
}

PSXLProcessor::~PSXLProcessor() = default;

bool PSXLProcessor::isBusesLayoutSupported (const BusesLayout& l) const
{
    return l.getMainOutputChannelSet() == juce::AudioChannelSet::stereo();
}

void PSXLProcessor::prepareToPlay (double sr, int block)
{
    engine.prepare (sr, block);
    uiMidi.reset (sr);
}

void PSXLProcessor::processBlock (juce::AudioBuffer<float>& buffer, juce::MidiBuffer& midi)
{
    juce::ScopedNoDenormals noDenormals;
    const int n = buffer.getNumSamples();

    keyboardState.processNextMidiBuffer (midi, 0, n, true);
    uiMidi.removeNextBlockOfMessages (midi, n);

    for (const auto meta : midi)
    {
        const auto m = meta.getMessage();
        if (! m.isController()) continue;
        const int cc = m.getControllerNumber();
        if (cc == 1 || cc == 64 || cc >= 120) continue;
        const int lt = learnTarget.load();
        if (lt >= 0) { ccMap[cc] = lt; learnTarget = -1; sendChangeMessage(); }
        const int pi = ccMap[cc].load();
        if (pi >= 0 && pi < (int) paramList.size()) paramList[(size_t) pi]->setValueNotifyingHost ((float) m.getControllerValue() / 127.0f);
    }

    bp.bpm = 120.0;
    if (auto* ph = getPlayHead())
        if (auto pos = ph->getPosition())
            if (auto bpm = pos->getBpm()) bp.bpm = juce::jmax (20.0, *bpm);
    ptrs.snapshot (bp);

    if (buffer.getNumChannels() < 2) { buffer.clear(); return; }
    engine.process (buffer, midi, bp, ptrs.destRange);
    midi.clear();
}

juce::AudioProcessorEditor* PSXLProcessor::createEditor() { return new PSXLEditor (*this); }

// ---------------------------------------------------------------------------------------------
// structure: routing + assignments + macro names
// ---------------------------------------------------------------------------------------------
void PSXLProcessor::changeStructure (const std::function<void (Structure&)>& mutate, const juce::String& name)
{
    Structure next = structure;
    mutate (next);
    undoManager.beginNewTransaction (name);
    undoManager.perform (new StructureAction (*this, structure, std::move (next)));
}

void PSXLProcessor::applyStructure (const Structure& s)
{
    bool namesChanged = false;
    structure = s;
    for (int i = 0; i < kNumMacros; ++i)
        if (macros[(size_t) i] != nullptr && macros[(size_t) i]->getDisplayName() != structure.macroName[(size_t) i])
        {
            macros[(size_t) i]->setDisplayName (structure.macroName[(size_t) i]);
            namesChanged = true;
        }
    publishStructure();
    // Tell the host (and NKS controllers) that parameter names changed so hardware displays refresh.
    if (namesChanged) updateHostDisplay (juce::AudioProcessorListener::ChangeDetails().withParameterInfoChanged (true));
    sendChangeMessage();
}

void PSXLProcessor::publishStructure()
{
    for (int s = 0; s < kRouteSrc; ++s)
        for (int d = 0; d < kRouteDst; ++d)
            shared.routeGain[s][d].store (routeAllowed (s, d) ? structure.route[s][d] : 0.0f);
    const int n = juce::jmin (kMaxAssign, (int) structure.assigns.size());
    shared.numAssign.store (0);
    for (int i = 0; i < n; ++i)
    {
        shared.aSrc[i].store (structure.assigns[(size_t) i].src);
        shared.aDst[i].store (structure.assigns[(size_t) i].dest);
        shared.aAmt[i].store (structure.assigns[(size_t) i].amount);
    }
    shared.numAssign.store (n);
}

void PSXLProcessor::setRoute (int src, int dstIdx, float gain)
{
    if (! routeAllowed (src, dstIdx)) return;
    changeStructure ([=] (Structure& s) { s.route[src][dstIdx] = juce::jlimit (0.0f, 2.0f, gain); }, "Edit routing");
}

void PSXLProcessor::clearRouting()
{
    changeStructure ([] (Structure& s) { for (auto& r : s.route) for (auto& g : r) g = 0.0f; }, "Clear routing");
}

bool PSXLProcessor::addAssignment (int src, int dest, float amount, juce::String& error)
{
    if (dest < 0 || dest >= D_COUNT || src < 0 || src >= S_Count) { error = "Invalid modulation target"; return false; }
    if (! destIsVoice (dest) && ! isGlobalSource (src))
    {
        error = "Voice modulators can't control global effects. Use a macro, mod wheel or aftertouch.";
        return false;
    }
    if ((int) structure.assigns.size() >= kMaxAssign) { error = "Modulation limit reached"; return false; }

    changeStructure ([=] (Structure& s)
    {
        bool found = false;
        for (auto& a : s.assigns) if (a.src == src && a.dest == dest) { a.amount = amount; found = true; }
        if (! found) s.assigns.push_back ({ src, dest, amount });
        // Smart macro naming: a macro inherits the name of the first parameter it is dragged onto.
        if (src >= S_Macro1 && src < S_Macro1 + kNumMacros)
        {
            const int m = src - S_Macro1;
            if (! s.macroUser[(size_t) m])
                if (auto* p = apvts.getParameter (destId (dest))) s.macroName[(size_t) m] = p->getName (32);
        }
    }, "Assign modulation");
    return true;
}

void PSXLProcessor::setAssignmentAmount (int src, int dest, float amount)
{
    for (auto& a : structure.assigns)
        if (a.src == src && a.dest == dest) { a.amount = juce::jlimit (-1.0f, 1.0f, amount); }
    publishStructure();   // continuous drags are applied immediately without flooding the undo history
}

void PSXLProcessor::removeAssignment (int src, int dest)
{
    changeStructure ([=] (Structure& s)
    {
        s.assigns.erase (std::remove_if (s.assigns.begin(), s.assigns.end(), [=] (const Assignment& a) { return a.src == src && a.dest == dest; }), s.assigns.end());
        if (src >= S_Macro1 && src < S_Macro1 + kNumMacros)
        {
            const int m = src - S_Macro1;
            bool any = false;
            for (auto& a : s.assigns) if (a.src == src) any = true;
            if (! any && ! s.macroUser[(size_t) m]) s.macroName[(size_t) m] = "Macro " + juce::String (m + 1);
        }
    }, "Remove modulation");
}

std::vector<Assignment> PSXLProcessor::assignmentsForDest (int dest) const
{
    std::vector<Assignment> r;
    for (auto& a : structure.assigns) if (a.dest == dest) r.push_back (a);
    return r;
}

int PSXLProcessor::countAssignmentsForSource (int src) const
{
    int c = 0;
    for (auto& a : structure.assigns) if (a.src == src) ++c;
    return c;
}

void PSXLProcessor::setMacroName (int i, const juce::String& name)
{
    changeStructure ([=] (Structure& s)
    {
        const auto trimmed = name.trim();
        s.macroUser[(size_t) i] = trimmed.isNotEmpty();
        s.macroName[(size_t) i] = trimmed.isNotEmpty() ? trimmed : "Macro " + juce::String (i + 1);
    }, "Rename macro");
}

// ---------------------------------------------------------------------------------------------
void PSXLProcessor::setPerfStep (int p, int step, float value)
{
    shared.perfSteps[p][step].store (juce::jlimit (0.0f, 1.0f, value));
}

void PSXLProcessor::randomisePerf (int p)
{
    for (int i = 0; i < kPerfSteps; ++i) shared.perfSteps[p][i].store (rng.nextFloat());
}

// ---------------------------------------------------------------------------------------------
// wavetables
// ---------------------------------------------------------------------------------------------
void PSXLProcessor::installTable (int slot, std::shared_ptr<Wavetable> wt)
{
    if (wt == nullptr || slot < 0 || slot >= kNumTableSlots) return;
    tableNames[(size_t) slot] = wt->name;
    shared.tables[slot].store (wt.get());
    tableStore.push_back (std::move (wt));   // old tables are intentionally kept alive; the audio thread may still read them
}

juce::String PSXLProcessor::getTableName (int slot) const
{
    if (slot < 0 || slot >= kNumTableSlots) return {};
    if (slot < kNumBuiltinTables) return Wavetable::builtinName (slot);
    return tableNames[(size_t) slot].isNotEmpty() ? tableNames[(size_t) slot] : "(empty)";
}

int PSXLProcessor::importWavetable (const juce::File& file)
{
    juce::MemoryBlock bytes;
    if (! file.loadFileAsData (bytes) || bytes.getSize() == 0) return -1;
    auto wt = Wavetable::fromAudioData (file.getFileNameWithoutExtension(), bytes.getData(), bytes.getSize());
    if (wt == nullptr) return -1;

    int slot = -1;
    for (int s = kNumBuiltinTables; s < kNumTableSlots; ++s)
        if (! isTableLoaded (s)) { slot = s; break; }
    if (slot < 0) slot = kNumTableSlots - 1;   // all user slots are full: replace the last one
    tableBytes[(size_t) slot] = bytes;
    installTable (slot, std::move (wt));
    sendChangeMessage();
    return slot;
}

// ---------------------------------------------------------------------------------------------
// tuning
// ---------------------------------------------------------------------------------------------
bool PSXLProcessor::loadScala (const juce::File& file)
{
    std::array<float, 128> t {};
    juce::String desc;
    const auto text = file.loadFileAsString();
    if (! parseScala (text, t, desc)) return false;
    for (int i = 0; i < 128; ++i) shared.tuning[i].store (t[(size_t) i]);
    tuningName = file.getFileNameWithoutExtension() + (desc.isNotEmpty() ? " - " + desc : juce::String());
    tuningText = text;
    sendChangeMessage();
    return true;
}

void PSXLProcessor::resetTuning()
{
    std::array<float, 128> t {};
    equalTemperament (t);
    for (int i = 0; i < 128; ++i) shared.tuning[i].store (t[(size_t) i]);
    tuningName = "12-tone equal"; tuningText = {};
    sendChangeMessage();
}

// ---------------------------------------------------------------------------------------------
// presets and state
// ---------------------------------------------------------------------------------------------
void PSXLProcessor::initBlank()
{
    for (auto* p : paramList) p->setValueNotifyingHost (p->getDefaultValue());
    Structure s;
    for (int i = 0; i < kNumMacros; ++i) s.macroName[(size_t) i] = "Macro " + juce::String (i + 1);
    for (int p = 0; p < kNumPerf; ++p) for (int i = 0; i < kPerfSteps; ++i) shared.perfSteps[p][i].store (0.5f);
    applyStructure (s);   // no routing, no modulation: a completely blank slate
    presetName = "Init (Blank)"; presetCategory = "Init";
    undoManager.clearUndoHistory();
    sendChangeMessage();
}

std::unique_ptr<juce::XmlElement> PSXLProcessor::exportXml (bool includeTables) const
{
    auto xml = std::make_unique<juce::XmlElement> ("PSXL");
    xml->setAttribute ("version", 1);
    xml->setAttribute ("name", presetName);
    xml->setAttribute ("category", presetCategory);
    for (auto* p : paramList)
        if (auto* pid = dynamic_cast<juce::AudioProcessorParameterWithID*> (p))
        {
            auto* e = xml->createNewChildElement ("P");
            e->setAttribute ("id", pid->paramID);
            e->setAttribute ("v", (double) p->convertFrom0to1 (p->getValue()));
        }
    for (int s = 0; s < kRouteSrc; ++s)
        for (int d = 0; d < kRouteDst; ++d)
            if (structure.route[s][d] > 0.0f)
            {
                auto* e = xml->createNewChildElement ("ROUTE");
                e->setAttribute ("src", s); e->setAttribute ("dst", d); e->setAttribute ("gain", (double) structure.route[s][d]);
            }
    for (auto& a : structure.assigns)
    {
        auto* e = xml->createNewChildElement ("ASSIGN");
        e->setAttribute ("src", a.src); e->setAttribute ("dest", destId (a.dest)); e->setAttribute ("amount", (double) a.amount);
    }
    for (int i = 0; i < kNumMacros; ++i)
    {
        auto* e = xml->createNewChildElement ("MACRO");
        e->setAttribute ("i", i); e->setAttribute ("name", structure.macroName[(size_t) i]); e->setAttribute ("user", structure.macroUser[(size_t) i] ? 1 : 0);
    }
    for (int p = 0; p < kNumPerf; ++p)
    {
        juce::StringArray vals;
        for (int i = 0; i < kPerfSteps; ++i) vals.add (juce::String (shared.perfSteps[p][i].load(), 3));
        auto* e = xml->createNewChildElement ("PERF");
        e->setAttribute ("i", p); e->setAttribute ("steps", vals.joinIntoString (","));
    }
    if (includeTables)
    {
        for (int s = kNumBuiltinTables; s < kNumTableSlots; ++s)
            if (tableBytes[(size_t) s].getSize() > 0)
            {
                auto* e = xml->createNewChildElement ("TABLE");
                e->setAttribute ("slot", s); e->setAttribute ("name", tableNames[(size_t) s]);
                e->addTextElement (tableBytes[(size_t) s].toBase64Encoding());
            }
        if (tuningText.isNotEmpty()) xml->createNewChildElement ("TUNING")->addTextElement (tuningText);
        for (int cc = 0; cc < 128; ++cc)
            if (ccMap[cc].load() >= 0)
                if (auto* pid = dynamic_cast<juce::AudioProcessorParameterWithID*> (paramList[(size_t) ccMap[cc].load()]))
                {
                    auto* e = xml->createNewChildElement ("LEARN");
                    e->setAttribute ("cc", cc); e->setAttribute ("param", pid->paramID);
                }
    }
    return xml;
}

bool PSXLProcessor::loadPresetXml (const juce::XmlElement& xml, bool fromHostState)
{
    if (! xml.hasTagName ("PSXL")) return false;

    // start from a clean slate so presets only need to list what differs from the defaults
    for (auto* p : paramList) p->setValueNotifyingHost (p->getDefaultValue());
    Structure s;
    for (int i = 0; i < kNumMacros; ++i) s.macroName[(size_t) i] = "Macro " + juce::String (i + 1);
    for (int p = 0; p < kNumPerf; ++p) for (int i = 0; i < kPerfSteps; ++i) shared.perfSteps[p][i].store (0.5f);

    for (auto* e : xml.getChildWithTagNameIterator ("P"))
        if (auto* p = apvts.getParameter (e->getStringAttribute ("id")))
            p->setValueNotifyingHost (p->convertTo0to1 ((float) e->getDoubleAttribute ("v")));
    for (auto* e : xml.getChildWithTagNameIterator ("ROUTE"))
    {
        const int src = e->getIntAttribute ("src"), dst = e->getIntAttribute ("dst");
        if (routeAllowed (src, dst)) s.route[src][dst] = (float) e->getDoubleAttribute ("gain", 1.0);
    }
    for (auto* e : xml.getChildWithTagNameIterator ("ASSIGN"))
    {
        const int dest = destIndexForId (e->getStringAttribute ("dest")), src = e->getIntAttribute ("src");
        if (dest >= 0 && src >= 0 && src < S_Count && (int) s.assigns.size() < kMaxAssign)
            s.assigns.push_back ({ src, dest, (float) e->getDoubleAttribute ("amount", 0.5) });
    }
    for (auto* e : xml.getChildWithTagNameIterator ("MACRO"))
    {
        const int i = e->getIntAttribute ("i");
        if (i >= 0 && i < kNumMacros) { s.macroName[(size_t) i] = e->getStringAttribute ("name", "Macro " + juce::String (i + 1)); s.macroUser[(size_t) i] = e->getBoolAttribute ("user"); }
    }
    for (auto* e : xml.getChildWithTagNameIterator ("PERF"))
    {
        const int p = e->getIntAttribute ("i");
        juce::StringArray vals; vals.addTokens (e->getStringAttribute ("steps"), ",", "");
        if (p >= 0 && p < kNumPerf) for (int i = 0; i < juce::jmin (kPerfSteps, vals.size()); ++i) shared.perfSteps[p][i].store (juce::jlimit (0.0f, 1.0f, vals[i].getFloatValue()));
    }
    for (auto* e : xml.getChildWithTagNameIterator ("TABLE"))
    {
        const int slot = e->getIntAttribute ("slot");
        juce::MemoryBlock mb;
        if (slot >= kNumBuiltinTables && slot < kNumTableSlots && mb.fromBase64Encoding (e->getAllSubText().trim()))
            if (auto wt = Wavetable::fromAudioData (e->getStringAttribute ("name"), mb.getData(), mb.getSize()))
            { tableBytes[(size_t) slot] = mb; installTable (slot, std::move (wt)); }
    }
    if (fromHostState)
    {
        if (auto* t = xml.getChildByName ("TUNING"))
        {
            std::array<float, 128> arr {}; juce::String desc;
            if (parseScala (t->getAllSubText(), arr, desc)) { for (int i = 0; i < 128; ++i) shared.tuning[i].store (arr[(size_t) i]); tuningText = t->getAllSubText(); tuningName = desc; }
        }
        for (auto& c : ccMap) c = -1;
        for (auto* e : xml.getChildWithTagNameIterator ("LEARN"))
        {
            const int cc = e->getIntAttribute ("cc");
            for (size_t i = 0; i < paramList.size(); ++i)
                if (auto* pid = dynamic_cast<juce::AudioProcessorParameterWithID*> (paramList[i]))
                    if (pid->paramID == e->getStringAttribute ("param") && cc >= 0 && cc < 128) ccMap[cc] = (int) i;
        }
    }

    applyStructure (s);
    presetName = xml.getStringAttribute ("name", "Untitled");
    presetCategory = xml.getStringAttribute ("category", "");
    undoManager.clearUndoHistory();
    sendChangeMessage();
    return true;
}

void PSXLProcessor::loadPresetIndex (int index)
{
    if (auto xml = presets.load (index)) { loadPresetXml (*xml); if (index < presets.numFactory()) currentProgram = index; }
}

void PSXLProcessor::setCurrentProgram (int index)
{
    if (index >= 0 && index < presets.numFactory()) loadPresetIndex (index);
}

const juce::String PSXLProcessor::getProgramName (int index)
{
    const auto& all = presets.all();
    return index >= 0 && index < (int) all.size() ? all[(size_t) index].name : presetName;
}

void PSXLProcessor::saveUserPreset (const juce::String& name, const juce::String& category)
{
    presetName = name; presetCategory = category.isEmpty() ? "User" : category;
    auto xml = exportXml (true);
    PresetManager::saveUserPreset (*xml, name, category == "User" ? juce::String() : category);
    presets.rescanUser();
    sendChangeMessage();
}

void PSXLProcessor::mutateSound (float amount)
{
    for (int d = 0; d < kNumVoiceDests; ++d)
    {
        const juce::String id = destId (d);
        if (id == "amp_level" || id == "o1_level" || id == "o2_level" || id == "pitch" || id == "o1_pitch" || id == "o2_pitch" || id == "o1_fine" || id == "o2_fine") continue;
        if (auto* p = apvts.getParameter (id))
            p->setValueNotifyingHost (juce::jlimit (0.0f, 1.0f, p->getValue() + (rng.nextFloat() - 0.5f) * 2.0f * amount));
    }
}

void PSXLProcessor::getStateInformation (juce::MemoryBlock& dest)
{
    if (auto xml = exportXml (true)) copyXmlToBinary (*xml, dest);
}

void PSXLProcessor::setStateInformation (const void* data, int size)
{
    if (auto xml = getXmlFromBinary (data, size)) loadPresetXml (*xml, true);
}

// ---------------------------------------------------------------------------------------------
// MIDI learn
// ---------------------------------------------------------------------------------------------
void PSXLProcessor::startMidiLearn (const juce::String& paramId)
{
    for (size_t i = 0; i < paramList.size(); ++i)
        if (auto* pid = dynamic_cast<juce::AudioProcessorParameterWithID*> (paramList[i]))
            if (pid->paramID == paramId) { learnTarget = (int) i; sendChangeMessage(); return; }
}

juce::String PSXLProcessor::learningParamId() const
{
    const int lt = learnTarget.load();
    if (lt >= 0 && lt < (int) paramList.size())
        if (auto* pid = dynamic_cast<juce::AudioProcessorParameterWithID*> (paramList[(size_t) lt])) return pid->paramID;
    return {};
}

juce::String PSXLProcessor::ccForParam (const juce::String& paramId) const
{
    for (int cc = 0; cc < 128; ++cc)
    {
        const int pi = ccMap[cc].load();
        if (pi >= 0)
            if (auto* pid = dynamic_cast<juce::AudioProcessorParameterWithID*> (paramList[(size_t) pi]))
                if (pid->paramID == paramId) return "CC " + juce::String (cc);
    }
    return {};
}

void PSXLProcessor::clearMidiMapping (const juce::String& paramId)
{
    for (int cc = 0; cc < 128; ++cc)
    {
        const int pi = ccMap[cc].load();
        if (pi >= 0)
            if (auto* pid = dynamic_cast<juce::AudioProcessorParameterWithID*> (paramList[(size_t) pi]))
                if (pid->paramID == paramId) ccMap[cc] = -1;
    }
    sendChangeMessage();
}
} // namespace psxl

juce::AudioProcessor* JUCE_CALLTYPE createPluginFilter() { return new psxl::PSXLProcessor(); }
