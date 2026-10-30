"""Builds docs/video_scripts/*.pdf.   Run:  python tools/docs/build_video_scripts.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import psxl_docs as D
from psxl_docs import *
from reportlab.lib.pagesizes import landscape, letter
from reportlab.graphics.shapes import Drawing, Rect, String
from video_a import VIDEOS_A
from video_b import VIDEOS_B
from video_extra import EXTRA

OUT = os.path.join(D.ROOT, "docs", "video_scripts")
VIDEOS = VIDEOS_A + VIDEOS_B
for _v in VIDEOS:
    _v["scenes"] = [(a, (n + " " + EXTRA[(_v["num"], i)]) if (_v["num"], i) in EXTRA else n, vis) for i, (a, n, vis) in enumerate(_v["scenes"], 1)]
WPM = 150


def words(t):
    return len(t.split())


def scene_seconds(narr):
    # narration at 150 wpm, but never shorter than 8 seconds of screen time per scene
    return max(8.0, words(narr) / WPM * 60.0 + 1.5)


def runtime(v):
    sec = sum(scene_seconds(s[1]) for s in v["scenes"])
    nw = sum(words(s[1]) for s in v["scenes"])
    return sec, nw


def fmt(sec):
    m, s = divmod(int(round(sec)), 60)
    return f"{m}:{s:02d}"


def new_doc(path, title):
    doc = PSDoc(path, title, pagesize=landscape(letter))
    doc.pageTemplates.sort(key=lambda t: t.id != "body")
    return doc


def video_pdf(v):
    path = os.path.join(OUT, f"{v['slug']}.pdf")
    title = f"Video {v['num']:02d}: {v['title']}"
    doc = new_doc(path, title)
    doc.chapter = title
    sec, nw = runtime(v)
    st = []
    big = ParagraphStyle("vt", parent=S["body"], fontName="Helvetica-Bold", fontSize=22, leading=26, textColor=INDIGO, spaceAfter=2)
    st.append(Paragraph(f"Video {v['num']:02d}  |  {v['title']}", big))
    st.append(Paragraph("Massive PSXL instructional series  -  video script", ParagraphStyle("vs", parent=S["body"], textColor=MAG_D, fontName="Helvetica-Bold", fontSize=11)))
    st.append(HRule(CYAN, 1.5, 3))
    meta = tbl([["Runtime estimate", "Narration length", "Scenes", "Format"],
                [f"about {fmt(sec)} minutes", f"{nw} words at {WPM} words per minute", str(len(v["scenes"])),
                 "Screen capture of the plug-in with voice-over; dark theme, interface size 125 percent"]],
               [1, 1.5, 0.5, 3], zebra=False)
    st.append(meta)
    st.append(spacer(6))
    st.append(H3("Learning goals"))
    st += bullets(v["goals"])
    st.append(spacer(4))
    st.append(callout("note", "Accuracy rule for the narrator and any generated video: use the on-screen names exactly as written in the action column. "
                              "After <b>Load Init (Blank)</b> the synth is silent until routing is connected. Do not compare Massive PSXL to other products."))
    st.append(spacer(2))
    st.append(Paragraph("Scene table", ParagraphStyle("h3b", parent=S["h3"], keepWithNext=0)))
    rows = [["Scene", "On-screen action", "Narration (word for word)", "Visual notes and call-outs"]]
    for i, (a, n, vis) in enumerate(v["scenes"], 1):
        rows.append([str(i), a, n, vis])
    t = tbl(rows, [0.45, 2.5, 4.1, 2.1], font="cell", align_center=(0,))
    st.append(t)
    st.append(PageBreak())
    st.append(H3("Narration only (plain script for text-to-speech or NotebookLM)"))
    ns = ParagraphStyle("ns", parent=S["body"], fontSize=10, leading=15, spaceAfter=7)
    for i, (a, n, vis) in enumerate(v["scenes"], 1):
        st.append(Paragraph(f"<b>[Scene {i}]</b> {n}", ns))
    st.append(spacer(6))
    st.append(callout("tip", "Pause for about one second between scenes and let on-screen actions finish before the next sentence starts."))
    doc.build(st)
    return path, sec, nw


def swatch(items, width=700):
    d = Drawing(width, 54)
    w = width / len(items)
    for i, (name, hexv, lab) in enumerate(items):
        col = HC(hexv)
        d.add(Rect(i * w + 3, 14, w - 6, 34, fillColor=col, strokeColor=GRID, strokeWidth=0.5, rx=4, ry=4))
        d.add(String(i * w + w / 2, 3, f"{name} {hexv}", fontName="Helvetica-Bold", fontSize=7.5, fillColor=INK, textAnchor="middle"))
    return d


def overview_pdf(results):
    path = os.path.join(OUT, "00_Series_Overview_for_NotebookLM.pdf")
    doc = new_doc(path, "Series Overview for NotebookLM")
    doc.chapter = "Series overview"
    st = []
    big = ParagraphStyle("ot", parent=S["body"], fontName="Helvetica-Bold", fontSize=26, leading=30, textColor=INDIGO, spaceAfter=2)
    st.append(Paragraph("Massive PSXL Video Series", big))
    st.append(Paragraph("Series overview and production guide for Google NotebookLM / Gemini", ParagraphStyle("os", parent=S["body"], textColor=MAG_D, fontName="Helvetica-Bold", fontSize=12)))
    st.append(HRule(CYAN, 1.5, 3))
    st.append(P("<b>Massive PSXL</b> is a wavetable synthesizer by <b>Phil S Audio</b> (VST3, Audio Unit and Standalone for macOS on Apple Silicon). "
                "This folder contains eleven video scripts. Each script gives the exact on-screen action and word-for-word narration for one instructional video of four to nine minutes. "
                "Together they take a viewer from a blank patch to finished drums, basses, leads and pads."))
    st.append(H3("Series at a glance"))
    rows = [["#", "Video", "Runtime (est.)", "Words", "File"]]
    for (v, (p, sec, nw)) in zip(VIDEOS, results):
        rows.append([f"{v['num']:02d}", v["title"], f"about {fmt(sec)}", str(nw), os.path.basename(p)])
    tot = sum(r[1] for r in results)
    rows.append(["", "<b>Total</b>", f"about {fmt(tot)}", str(sum(r[2] for r in results)), ""])
    st.append(tbl(rows, [0.4, 3.6, 1.2, 0.7, 3.2], align_center=(0,)))
    st.append(spacer(4))
    st.append(H3("Audience"))
    st += bullets([
        "Producers and sound designers who know basic synthesis words (oscillator, filter, envelope) but have not used this synth.",
        "Beginners are welcome: every script defines terms the first time they appear and builds every sound from <b>Load Init (Blank)</b>.",
        "Viewers use a Mac with a DAW or the standalone app, and a mouse; a MIDI keyboard is helpful but not required (the plug-in has an on-screen keyboard).",
    ])
    st.append(H3("Tone and pacing"))
    st += bullets([
        "<b>Tone:</b> friendly, calm and practical, like a studio-mate showing you something. Second person (you), present tense, short sentences. No hype and no comparisons with other products.",
        f"<b>Pace:</b> about {WPM} words per minute. Leave a short pause (about one second) between scenes and let each on-screen action finish before narrating the next step.",
        "<b>Numbers:</b> read parameter values the way they appear (point six six, twelve hundred hertz, minus twelve semitones). Say 'Pos' as 'position' on first mention, then 'Pos'.",
        "<b>Structure:</b> each video opens with what you will learn, shows the result early, then goes step by step and ends with a one-sentence summary and a pointer to the next video.",
        "<b>Honesty:</b> values are 'starting points'. Encourage the viewer to adjust by ear. Do not claim features that are not described in the scripts.",
    ])
    st.append(CondPageBreak(160))
    st.append(H3("Visual style guide (Phil S Audio brand)"))
    st.append(P("The plug-in's own palette is the brand palette. Use dark indigo as the background for title cards, lower-thirds and diagrams, with cyan, magenta and amber as accents. "
                "The splash artwork (glowing wavetable ribbons) is the series' key image."))
    st.append(swatch([("Background", "#0B0D14", ""), ("Panel", "#151925", ""), ("Indigo", "#1E1B5E", ""), ("Cyan", "#35D4FF", ""),
                      ("Magenta", "#D24BFF", ""), ("Amber", "#FFB43A", ""), ("Green", "#4BE08A", ""), ("Text", "#E9EDF9", "")]))
    st.append(spacer(6))
    st += bullets([
        "<b>Plug-in colours mean something:</b> cyan = oscillators and modulation slots, magenta = filters and macros, amber = Performers and the Insert, green = noise and performance sources. Use the same colours for call-outs.",
        "<b>Theme:</b> record in the dark theme at interface size 125 percent (Menu > Settings > Interface size). Show the light theme only in video 11.",
        "<b>Title cards:</b> splash artwork with the video number and title in white, accent bar in cyan, magenta and amber across the bottom.",
        "<b>Lower-thirds:</b> dark indigo rounded rectangle, white text, small cyan left bar. Keep to one short line.",
        "<b>Call-outs:</b> thin cyan rings or arrows for controls being touched, amber for values to set, magenta for warnings or things to avoid.",
        "<b>Parameter readouts:</b> when a value is spoken, show it as a small tag next to the knob (for example 'Cutoff 1200 Hz').",
        "<b>Diagrams:</b> use the routing node style (dark boxes with coloured borders and glowing wires) for any signal-flow illustration.",
        "<b>Typography:</b> a clean sans-serif for all on-screen text; headings bold; avoid ornamental fonts.",
        "<b>Music:</b> optional quiet ambient bed under narration; mute it during sound demonstrations.",
    ])
    st.append(H3("How to use these scripts with NotebookLM or Gemini"))
    st += numbered([
        "Create a notebook (or conversation) and upload this overview plus the video script PDFs you want to turn into videos. One script per video works best.",
        "For narration-only output, ask the model to read the 'Narration (word for word)' column in order and ignore the other columns.",
        "For a video or slide-style overview, ask it to follow the scene table: use the 'On-screen action' column for what to show and the 'Visual notes' column for call-outs.",
        "Keep the exact on-screen names (Load Init (Blank), Routing, Filter 1, Cutoff, Mod 2, Macro 1 and so on). Ask the model not to rename controls or add controls that are not in the script.",
        "If the tool produces illustrations instead of recordings, use them only for title cards and diagrams; capture the actual plug-in for every step that shows knobs and menus.",
    ])
    st.append(H3("A prompt you can paste"))
    prompt = ("You are producing an instructional video about Massive PSXL, a wavetable synthesizer by Phil S Audio. "
              "Use only the uploaded scripts as your source. For each scene, show what the 'On-screen action' column says and speak the 'Narration' column word for word at a calm, friendly pace "
              "of about 150 words per minute. Use the dark indigo look with cyan, magenta and amber accents described in the overview. Do not compare the product to any other synthesizer. "
              "Do not invent features, parameter names or values.")
    st.append(callout("tip", prompt))
    st.append(CondPageBreak(160))
    st.append(H3("Facts every video must get right"))
    st += bullets([
        "<b>Load Init (Blank)</b> (Menu button) resets all parameters and leaves <b>no routing</b>. The synth is silent until something is connected in the <b>Routing</b> tab.",
        "Routing is a node editor. Drag from an <b>output port</b> (right edge of a node) to an <b>input port</b> (left edge). Wires glow with audio. Click a wire and press Delete, or double-click it. Right-click a wire for gain, right-click empty space for quick setups.",
        "Signal flows left to right: Osc 1, Osc 2, Noise, then Filter 1, Filter 2, Insert, Out. A source can feed any later node.",
        "Modulation: drag a macro's crosshair chip (bottom strip) or any modulator chip onto a knob. Right-click a modulated knob to edit amount (-1 to +1) or remove. Default amount is +0.5.",
        "A macro automatically takes the target knob's name and the host-visible parameter name updates; that is what controller displays read. Whether a given host refreshes immediately depends on the host.",
        "Voice modulators (envelopes, LFOs, Performers, Velocity, Key Track, Random) cannot control the master effects; use macros, mod wheel or aftertouch.",
        "Lower tabs: Voice, Routing, Amp Env, Mod 2 to Mod 9 (each an Envelope or LFO), Perf 1 to Perf 3. Mod slot chips are at the top left of each tab.",
        "The <b>Keys</b> button pulls down the keyboard with pitch and mod wheels; keys light when MIDI arrives.",
        "<b>Menu > Settings</b> has dark/light theme, interface size (75 to 200 percent), keyboard size, wavetable import and Scala tuning.",
        "117 factory presets in 8 categories (Bass, Leads, Pads, Plucks, Keys, Drums, FX, Sequence). User presets are saved in the Music folder under Phil S Audio.",
        "Ten built-in wavetables: Morph Basic, Pulse Sweep, Harmonic Tilt, Vowel Choir, Hard Sync, FM Bells, Drawbar Organ, Glass Harmonics, Digital Grit, Fold Sweep.",
        "Filters: Ladder (LP 24, LP 12, BP, HP 24), State Variable (LP, BP, HP, Notch), Comb (Comb +, Comb -, Flange, Pluck), Formant (Male, Female, Child, Alien).",
        "Insert types: TanH, Fold, Bitcrush, Hard Clip, Rectify, Sine. Master effect order: EQ, Distortion, Chorus, Delay, Reverb, then Volume.",
    ])
    st.append(H3("Things not to say"))
    st += bullets([
        "Do not name or compare with other synthesizers or companies.",
        "Do not say the plug-in has been tested on any particular Mac, host or hardware.",
        "Do not describe hardware controller integration as certified or official.",
        "Do not describe features that are not in the scripts (for example sample playback, arpeggiator panels or MPE).",
    ])
    st.append(H3("Recording checklist"))
    st += bullets([
        "Record the standalone app or a DAW at 1080p or higher with the interface at 125 percent so labels are legible.",
        "Show the mouse pointer and enable click highlights.",
        "Load the starting state exactly as the first scene says (usually Menu > Load Init (Blank)).",
        "Capture short sound demonstrations of about five seconds after each major change, and keep levels consistent.",
    ])
    doc.build(st)
    return path


def main():
    os.makedirs(OUT, exist_ok=True)
    results = [video_pdf(v) for v in VIDEOS]
    overview_pdf(results)
    for (p, sec, nw), v in zip(results, VIDEOS):
        print(f"{os.path.basename(p)}  ~{fmt(sec)}  {nw} words")


if __name__ == "__main__":
    main()
