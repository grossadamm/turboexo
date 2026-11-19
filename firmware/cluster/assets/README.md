# Dashboard assets

Numeric and text fonts are generated from LVGL 9.5.0's Montserrat-Medium.ttf,
licensed under the SIL Open Font License (MONTSERRAT-OFL.txt). Run
`tools/generate_assets.sh` after installing `lv_font_conv@1.5.3` under
`$TURBOEXO_DEPS/font-converter` and cloning LVGL v9.5.0 under
`$TURBOEXO_DEPS/lvgl-9.5.0` (set `TURBOEXO_DEPS` to the persistent dependency directory).
Fonts are committed so the cross-build does not require Node.

The SVG references are the accepted mock's Lucide 0.468.0 and MDI 7.4.47
icons, with their original notices. `tools/generate_icons.py` rasterizes these exact
SVGs to LVGL ARGB8888 C assets using `rsvg-convert` and Python Pillow.
