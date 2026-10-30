#!/bin/bash
# Installs Massive PSXL for the current user only (no admin password needed).
#   usage: installer/install_local.sh [build-dir]
set -euo pipefail
BUILD="${1:-build}"
ART="$BUILD/MassivePSXL_artefacts/Release"
VST3_DIR="$HOME/Library/Audio/Plug-Ins/VST3/Phil S Audio"
AU_DIR="$HOME/Library/Audio/Plug-Ins/Components"
APP_DIR="$HOME/Applications/Phil S Audio"
mkdir -p "$VST3_DIR" "$AU_DIR" "$APP_DIR"
rm -rf "$VST3_DIR/Massive PSXL.vst3" "$AU_DIR/Massive PSXL.component" "$APP_DIR/Massive PSXL.app"
cp -R "$ART/VST3/Massive PSXL.vst3" "$VST3_DIR/"
cp -R "$ART/AU/Massive PSXL.component" "$AU_DIR/"
cp -R "$ART/Standalone/Massive PSXL.app" "$APP_DIR/"
for b in "$VST3_DIR/Massive PSXL.vst3" "$AU_DIR/Massive PSXL.component" "$APP_DIR/Massive PSXL.app"; do
  codesign --force --deep --sign - "$b"
done
killall -9 AudioComponentRegistrar 2>/dev/null || true
echo "Installed:"; echo "  $VST3_DIR/Massive PSXL.vst3"; echo "  $AU_DIR/Massive PSXL.component"; echo "  $APP_DIR/Massive PSXL.app"
