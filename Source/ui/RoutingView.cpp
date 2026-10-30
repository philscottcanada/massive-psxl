#include "Views.h"

namespace psxl
{
using juce::Graphics;
using juce::Point;
using juce::Rectangle;
using juce::String;

RoutingView::RoutingView (PSXLProcessor& p) : proc (p)
{
    setWantsKeyboardFocus (true);
    proc.addChangeListener (this);
    startTimerHz (30);
}

RoutingView::~RoutingView() { proc.removeChangeListener (this); }

Rectangle<float> RoutingView::nodeRect (int node) const
{
    const float W = (float) getWidth(), H = (float) getHeight();
    const float w = juce::jlimit (96.0f, 150.0f, W * 0.13f), h = 54.0f;
    static const float cx[N_Count] = { 0.10f, 0.10f, 0.10f, 0.32f, 0.54f, 0.74f, 0.91f };
    static const float cy[N_Count] = { 0.22f, 0.50f, 0.78f, 0.34f, 0.66f, 0.50f, 0.50f };
    return Rectangle<float> (w, h).withCentre ({ cx[node] * W, cy[node] * H });
}

juce::Path RoutingView::wirePath (Point<float> a, Point<float> b) const
{
    juce::Path p;
    const float dx = juce::jmax (40.0f, std::abs (b.x - a.x) * 0.5f);
    p.startNewSubPath (a);
    p.cubicTo (a.translated (dx, 0), b.translated (-dx, 0), b);
    return p;
}

String RoutingView::subtitle (int node) const
{
    auto raw = [this] (const String& id) { return proc.apvts.getRawParameterValue (id)->load(); };
    switch (node)
    {
        case N_Osc1: return proc.getTableName ((int) raw ("o1_wt"));
        case N_Osc2: return proc.getTableName ((int) raw ("o2_wt"));
        case N_Noise: return noiseTypeNames()[(int) raw ("n_type")];
        case N_Filt1: { const int m = (int) raw ("f1_model"); return filterModelNames()[m] + " / " + filterModeNames (m)[(int) raw ("f1_mode")]; }
        case N_Filt2: { const int m = (int) raw ("f2_model"); return filterModelNames()[m] + " / " + filterModeNames (m)[(int) raw ("f2_mode")]; }
        case N_Insert: return insertTypeNames()[(int) raw ("ins_type")];
        default: return "Stereo amp";
    }
}

bool RoutingView::hitWire (Point<float> pt, int& src, int& dst) const
{
    for (int s = 0; s < kRouteSrc; ++s)
        for (int d = 0; d < kRouteDst; ++d)
        {
            if (proc.getRoute (s, d) <= 0.0f) continue;
            const auto a = outPort (s), b = inPort (N_Filt1 + d);
            const float dx = juce::jmax (40.0f, std::abs (b.x - a.x) * 0.5f);
            const Point<float> c1 = a.translated (dx, 0), c2 = b.translated (-dx, 0);
            Point<float> prev = a;
            for (int i = 1; i <= 28; ++i)
            {
                const float t = (float) i / 28.0f, u = 1.0f - t;
                const Point<float> q = a * (u * u * u) + c1 * (3 * u * u * t) + c2 * (3 * u * t * t) + b * (t * t * t);
                juce::Line<float> seg (prev, q);
                Point<float> nearest;
                if (seg.getDistanceFromPoint (pt, nearest) < 7.0f) { src = s; dst = d; return true; }
                prev = q;
            }
        }
    return false;
}

int RoutingView::portAt (Point<float> p, bool output) const
{
    for (int n = 0; n < N_Count; ++n)
    {
        if (output && n == N_Out) continue;
        if (! output && n < N_Filt1) continue;
        if ((output ? outPort (n) : inPort (n)).getDistanceFrom (p) < 14.0f) return n;
    }
    return -1;
}

void RoutingView::paint (Graphics& g)
{
    const auto& pal = Theme::p();
    auto bounds = getLocalBounds().toFloat();
    g.setColour (pal.panel);
    g.fillRoundedRectangle (bounds, 8.0f);
    g.setColour (pal.outline);
    g.drawRoundedRectangle (bounds.reduced (0.5f), 8.0f, 1.0f);

    // faint grid
    g.setColour (pal.outline.withAlpha (0.25f));
    for (float x = 20.0f; x < bounds.getWidth(); x += 40.0f) g.drawVerticalLine ((int) x, 4.0f, bounds.getHeight() - 4.0f);
    for (float y = 20.0f; y < bounds.getHeight(); y += 40.0f) g.drawHorizontalLine ((int) y, 4.0f, bounds.getWidth() - 4.0f);

    const double now = juce::Time::getMillisecondCounterHiRes() * 0.001;
    bool any = false;

    // wires
    for (int s = 0; s < kRouteSrc; ++s)
        for (int d = 0; d < kRouteDst; ++d)
        {
            const float gain = proc.getRoute (s, d);
            if (gain <= 0.0f) continue;
            any = true;
            const auto path = wirePath (outPort (s), inPort (N_Filt1 + d));
            const float activity = juce::jlimit (0.0f, 1.0f, proc.shared.nodePeak[s].load() * gain * 3.0f);
            const bool selected = s == selSrc && d == selDst;
            const juce::Colour col = pal.accent.interpolatedWith (pal.accent2, (float) s / 5.0f);
            g.setColour (col.withAlpha (0.28f));
            g.strokePath (path, juce::PathStrokeType (2.0f + gain * 1.5f));
            if (activity > 0.01f)
            {
                g.setColour (col.withAlpha (0.10f + 0.20f * activity));
                g.strokePath (path, juce::PathStrokeType (11.0f, juce::PathStrokeType::curved, juce::PathStrokeType::rounded));
                g.setColour (col.withAlpha (0.35f + 0.5f * activity));
                g.strokePath (path, juce::PathStrokeType (3.0f + activity * 2.0f, juce::PathStrokeType::curved, juce::PathStrokeType::rounded));
                const float len = path.getLength();   // flowing energy dots
                for (int k = 0; k < 5; ++k)
                {
                    const float t = std::fmod ((float) now * (0.25f + activity * 0.6f) + (float) k * 0.2f, 1.0f);
                    const auto pt = path.getPointAlongPath (t * len);
                    g.setColour (juce::Colours::white.withAlpha (0.5f * activity));
                    g.fillEllipse (pt.x - 2.5f, pt.y - 2.5f, 5.0f, 5.0f);
                }
            }
            if (selected)
            {
                g.setColour (pal.text);
                g.strokePath (path, juce::PathStrokeType (1.5f));
            }
            if (std::abs (gain - 1.0f) > 0.01f)
            {
                const auto mid = path.getPointAlongPath (path.getLength() * 0.5f);
                g.setColour (pal.panel); g.fillRoundedRectangle (mid.x - 18, mid.y - 8, 36, 16, 4.0f);
                g.setColour (pal.text); g.setFont (Theme::font (10.5f));
                g.drawText (String (juce::roundToInt (gain * 100.0f)) + "%", Rectangle<float> (mid.x - 18, mid.y - 8, 36, 16), juce::Justification::centred);
            }
        }

    // wire being dragged
    if (dragSrc >= 0)
    {
        g.setColour (pal.accent3);
        g.strokePath (wirePath (outPort (dragSrc), dragPos), juce::PathStrokeType (2.5f));
    }

    // nodes
    for (int n = 0; n < N_Count; ++n)
    {
        const auto r = nodeRect (n);
        juce::Colour col = n <= N_Osc2 ? pal.accent : (n == N_Noise ? pal.good : (n <= N_Filt2 ? pal.accent2 : (n == N_Insert ? pal.accent3 : pal.text)));
        g.setColour (pal.panelHi);
        g.fillRoundedRectangle (r, 8.0f);
        g.setColour (col.withAlpha (0.85f));
        g.drawRoundedRectangle (r.reduced (0.5f), 8.0f, 1.5f);
        g.setColour (pal.text);
        g.setFont (Theme::font (13.0f, true));
        g.drawText (nodeName (n), r.reduced (8.0f, 4.0f).removeFromTop (18.0f), juce::Justification::centredLeft);
        g.setColour (pal.textDim);
        g.setFont (Theme::font (10.0f));
        g.drawFittedText (subtitle (n), r.reduced (8.0f, 0.0f).withTrimmedTop (21.0f).withTrimmedBottom (10.0f).toNearestInt(), juce::Justification::centredLeft, 1);
        const float level = juce::jlimit (0.0f, 1.0f, proc.shared.nodePeak[n].load());   // activity meter
        g.setColour (col.withAlpha (0.8f));
        g.fillRoundedRectangle (r.getX() + 8.0f, r.getBottom() - 8.0f, (r.getWidth() - 16.0f) * level, 3.0f, 1.5f);

        auto port = [&] (Point<float> c, bool compatible)
        {
            g.setColour (pal.panel); g.fillEllipse (c.x - 7, c.y - 7, 14, 14);
            g.setColour (compatible ? pal.accent3 : col); g.drawEllipse (c.x - 6, c.y - 6, 12, 12, compatible ? 2.5f : 1.5f);
            g.fillEllipse (c.x - 2.5f, c.y - 2.5f, 5, 5);
        };
        if (n != N_Out) port (outPort (n), false);
        if (n >= N_Filt1) port (inPort (n), dragSrc >= 0 && routeAllowed (dragSrc, n - N_Filt1));
    }

    if (! any)
    {
        g.setColour (pal.text.withAlpha (0.85f));
        g.setFont (Theme::font (15.0f, true));
        g.drawText ("No routing connections - the synth is silent.", getLocalBounds().withTrimmedTop (getHeight() / 2 - 62).withHeight (22), juce::Justification::centred);
        g.setColour (pal.textDim);
        g.setFont (Theme::font (12.0f));
        g.drawText ("Drag from an output port (right edge of a node) to an input port to connect, or right-click for quick setups.",
                    getLocalBounds().withTrimmedTop (getHeight() / 2 - 38).withHeight (20), juce::Justification::centred);
    }
}

void RoutingView::mouseDown (const juce::MouseEvent& e)
{
    grabKeyboardFocus();
    const auto pt = e.position;
    int s = -1, d = -1;
    const bool onWire = hitWire (pt, s, d);

    if (e.mods.isPopupMenu())
    {
        juce::PopupMenu m;
        if (onWire)
        {
            selSrc = s; selDst = d;
            m.addItem (1, "Remove connection");
            m.addSeparator();
            for (int i = 1; i <= 5; ++i) m.addItem (10 + i, "Gain " + String (i == 5 ? 150 : i * 25) + "%");
        }
        else
        {
            m.addSectionHeader ("Quick setups");
            m.addItem (101, "Osc 1 > Filter 1 > Out");
            m.addItem (102, "Osc 1 + Osc 2 > Filter 1 > Out");
            m.addItem (103, "Serial: Osc 1 + 2 > Filter 1 > Filter 2 > Out");
            m.addItem (104, "Parallel: Osc 1 > Filter 1, Osc 2 > Filter 2 > Out");
            m.addItem (105, "Osc 1 + 2 + Noise > Insert > Out");
            m.addItem (106, "Noise > Filter 1 > Insert > Out (drums / FX)");
            m.addSeparator();
            m.addItem (199, "Clear all connections");
        }
        juce::Component::SafePointer<RoutingView> safe (this);
        m.showMenuAsync ({}, [safe, s, d] (int id)
        {
            if (safe == nullptr || id == 0) return;
            if (id == 1) { safe->proc.setRoute (s, d, 0.0f); safe->selSrc = safe->selDst = -1; }
            else if (id >= 11 && id <= 15) safe->proc.setRoute (s, d, id == 15 ? 1.5f : (float) (id - 10) * 0.25f);
            else safe->applyTemplate (id);
            safe->repaint();
        });
        return;
    }

    dragSrc = portAt (pt, true);
    dragPos = pt;
    if (dragSrc < 0) { selSrc = onWire ? s : -1; selDst = onWire ? d : -1; }
    repaint();
}

void RoutingView::mouseDrag (const juce::MouseEvent& e)
{
    if (dragSrc >= 0) { dragPos = e.position; repaint(); }
}

void RoutingView::mouseUp (const juce::MouseEvent& e)
{
    if (dragSrc < 0) return;
    const int dstNode = portAt (e.position, false);
    if (dstNode >= 0 && routeAllowed (dragSrc, dstNode - N_Filt1))
    {
        const int d = dstNode - N_Filt1;
        if (proc.getRoute (dragSrc, d) <= 0.0f) proc.setRoute (dragSrc, d, 1.0f);
        selSrc = dragSrc; selDst = d;
    }
    else if (dstNode >= 0) toast (String ("Signal flows left to right: ") + nodeName (dragSrc) + " can't feed " + nodeName (dstNode));
    dragSrc = -1;
    repaint();
}

void RoutingView::mouseDoubleClick (const juce::MouseEvent& e)
{
    int s, d;
    if (hitWire (e.position, s, d)) { proc.setRoute (s, d, 0.0f); selSrc = selDst = -1; }
}

bool RoutingView::keyPressed (const juce::KeyPress& k)
{
    if ((k == juce::KeyPress::deleteKey || k == juce::KeyPress::backspaceKey) && selSrc >= 0)
    {
        proc.setRoute (selSrc, selDst, 0.0f); selSrc = selDst = -1; repaint();
        return true;
    }
    return false;
}

void RoutingView::applyTemplate (int id)
{
    proc.clearRouting();
    auto c = [this] (int s, int dstNode) { proc.setRoute (s, dstNode - N_Filt1, 1.0f); };
    switch (id)
    {
        case 101: c (N_Osc1, N_Filt1); c (N_Filt1, N_Out); break;
        case 102: c (N_Osc1, N_Filt1); c (N_Osc2, N_Filt1); c (N_Filt1, N_Out); break;
        case 103: c (N_Osc1, N_Filt1); c (N_Osc2, N_Filt1); c (N_Filt1, N_Filt2); c (N_Filt2, N_Out); break;
        case 104: c (N_Osc1, N_Filt1); c (N_Osc2, N_Filt2); c (N_Filt1, N_Out); c (N_Filt2, N_Out); break;
        case 105: c (N_Osc1, N_Insert); c (N_Osc2, N_Insert); c (N_Noise, N_Insert); c (N_Insert, N_Out); break;
        case 106: c (N_Noise, N_Filt1); c (N_Filt1, N_Insert); c (N_Insert, N_Out); break;
        default: break;   // 199: clear only
    }
}
} // namespace psxl
