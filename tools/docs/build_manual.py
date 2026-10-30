"""Builds docs/Massive_PSXL_Manual.pdf.   Run:  python tools/docs/build_manual.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import psxl_docs as D
from psxl_docs import *
import manual_a, manual_b, manual_c, manual_d, manual_tut

OUT = os.path.join(D.ROOT, "docs", "Massive_PSXL_Manual.pdf")


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    cover = make_cover("Massive PSXL", "User Manual and Tutorials", "A wavetable synthesizer by Phil S Audio",
                       extra=["Reference manual  |  28 step-by-step tutorials  |  117 factory presets"])
    doc = PSDoc(OUT, "User Manual and Tutorials", cover=cover)
    st = [NextPageTemplate("body"), PageBreak()]
    st.append(P("Contents", ParagraphStyle("ct", parent=S["h2"], fontSize=22, leading=26, textColor=INDIGO, spaceBefore=0, spaceAfter=10)))
    st.append(make_toc(1))
    front, a_chapters = manual_a.build()
    st.append(PageBreak())
    st += front
    part_title(st, "I", "Reference Manual", "Installation, the interface, sound generation, modulation, presets, MIDI and a complete parameter reference.")
    first = True
    for ch in a_chapters + manual_b.build() + manual_c.build():
        if not first:
            st.append(CondPageBreak(330))
        first = False
        st += ch
    d_chapters, appendix = manual_d.build()
    st.append(CondPageBreak(330))
    for ch in d_chapters:
        st.append(CondPageBreak(330))
        st += ch
    st += manual_tut.build()
    st.append(CondPageBreak(330))
    st += appendix
    doc.multiBuild(st)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
