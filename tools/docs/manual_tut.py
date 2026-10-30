"""Manual part E: the tutorials (rendered from tutorials_data.py)."""
import psxl_docs as D
from psxl_docs import *
import tutorials_data as TD


def intro():
    st = [Banner("", "How to Use the Tutorials", "Recipes that start from Load Init (Blank)", level=0)]
    st += [
        P("Each tutorial builds one sound from scratch, so you learn the controls by using them. They all start the same way:"),
    ]
    st += numbered([
        "<b>Menu > Load Init (Blank)</b>: every parameter returns to its default, and there is <b>no routing</b>.",
        "<b>Routing</b> tab: connect the nodes the recipe lists. Either right-click empty space and choose a quick setup, or drag from an output port (right edge) to an input port (left edge).",
        "Set the oscillator, noise, filter, insert and envelope values from the steps and the settings table.",
        "Assign modulation by dragging a chip onto a knob, then right-click the knob > <b>Edit amount</b> and type or drag to the amount given.",
        "Add the effects, play, and adjust by ear.",
    ])
    st += [
        H3("Reading the recipe tables"),
        tbl([["Column", "Meaning"],
             ["Where", "The panel or tab: Osc 1, Osc 2, Noise, Filter 1, Insert, Amp, Amp Env, Mod 2 and so on. 'Mod 2 (LFO)' means the Mod 2 tab with Type set to LFO."],
             ["Parameter", "The labels on screen, in the order listed. A slash separates several parameters in one row."],
             ["Value", "The setting in the same order. 'Pos 0.66' means turn Pos to 0.66; you can hover over a knob while dragging to see the exact value."]],
            [0.8, 4.8], first_bold=True),
        callout("start", "Every number in these tutorials is a <b>starting point</b>, not a rule. Real patches are found by ear: change Cutoff, Decay and amounts until it sounds right for your track."),
        callout("tip", "To compare with a ready-made version, load the factory preset named at the top of each tutorial. Use <b>Menu > Load Init (Blank)</b> afterwards to start again."),
        callout("note", "Quick tab reminders: oscillator knobs belong to whichever of <b>Osc 1 | Osc 2</b> is selected, the filter knobs to <b>Filter 1 | Filter 2</b>, and the effects to the <b>EQ / Delay / Verb / Chor / Dist</b> tabs. "
                        "Make the destination knob visible before dropping a chip on it."),
        H3("The tutorials"),
    ]
    groups = {}
    for t in TD.TUTORIALS:
        groups.setdefault(t["group"], []).append(t)
    rows = [["Group", "Tutorials"]]
    for g, ts in groups.items():
        rows.append([g, ", ".join(f"{t['n']}. {t['title']}" for t in ts)])
    st.append(tbl(rows, [1.2, 4.6], first_bold=True))
    return st


def render(t):
    story = []
    title = f"Tutorial {t['n']}: {t['title']}"
    head = Heading(title, S["h2"], 1, title)
    tag = P(f"{t['group']}  |  Factory preset to compare: <b>{t['preset']}</b>", "tag")
    goal = P(t["goal"], "goal")
    wires = t["wires"]
    diag = node_diagram(D.FW, 96, wires, compact=True, subs=False, title="Routing for this recipe")
    story.append(CondPageBreak(290))
    story.append(KeepTogether([head, tag, goal, P("<b>Routing:</b> " + t["routing"]), diag]))
    story.append(spacer(3))
    story.append(H4("Steps"))
    story += numbered(t["steps"])
    story.append(H4("Settings"))
    rows = [["Where", "Parameter", "Value (starting point)"]]
    for w, p, v in t["settings"]:
        rows.append([w, p, v])
    story.append(tbl(rows, [1.2, 2.2, 2.6], first_bold=True))
    if t["mods"]:
        story.append(spacer(4))
        story.append(H4("Modulation assignments"))
        rows = [["Source", "Target", "Amount", "Why"]]
        for m in t["mods"]:
            rows.append(list(m))
        story.append(tbl(rows, [1.1, 1.3, 1.1, 2.6], first_bold=True))
    if t["tips"]:
        story.append(H4("Playing tips and variations"))
        story += bullets(t["tips"])
    story.append(spacer(10))
    return story


def build():
    st = []
    D.part_title(st, "II", "Tutorials", "Twenty-eight recipes that start from Load Init (Blank): drums, bass, leads, keys, pads, effects, sequenced sounds, macros and wavetable import.")
    st += intro()
    for t in TD.TUTORIALS:
        st += render(t)
    return st
