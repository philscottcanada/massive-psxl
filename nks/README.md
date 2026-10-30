# NKS support for Massive PSXL

What is implemented in the plug-in itself, and what still needs Native Instruments' tooling.

## Implemented
* **Parameter exposure.** All 40+ sound parameters, 16 macros, the amp envelope, 8 mod slots and 3 performers are
  regular host-automatable parameters, organised in JUCE parameter groups (VST3 "units").
* **Smart macro naming.** When a macro's crosshair is dropped onto a knob, the macro takes that knob's name
  ("Filter 1 Cutoff"). The plug-in then calls `updateHostDisplay(withParameterInfoChanged)`, which makes the
  VST3 wrapper send `kParamTitlesChanged` so the host - and any controller display driven by it - re-reads the
  macro's name immediately. Names are saved in presets (`<MACRO>` elements) and in the plug-in state.
* **Parameter pages.** `psxl_nks_pages.json` lists the intended 8-parameter controller pages (Macros first).
* **Artwork.** `Resources/art/nks/` has provisional plug-in logos, banners and category tiles.
* **Categories.** Presets are organised as Bass / Leads / Pads / Plucks / Keys / Drums / FX / Sequence.

## NOT possible without Native Instruments
* **The NKS Developer Kit / NKS logo / partner listing** are issued by NI (free, but by application):
  3rd-party-developers@native-instruments.com. Until NI approves the product it cannot carry the official
  "NKS" badge or be listed in Komplete Kontrol's browser.
* **`.nksf` preset files** (the format Komplete Kontrol and Maschine browse) and the exact artwork sizes come
  from that kit. Once you have it: convert `Resources/presets/factory_presets.xml` into `.nksf` using the page
  map above and the artwork in `Resources/art/nks/`.

Until then the plug-in works as a normal VST3/AU in Komplete Kontrol and Maschine in "generic plug-in" mode, where
the 8-parameter pages follow the host's parameter order (macros are first, by design).
