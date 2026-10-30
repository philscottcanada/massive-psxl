#!/bin/bash
# Builds the macOS installer package for Massive PSXL.
#   usage: installer/build_installer.sh [build-dir]
# The package installs:
#   /Library/Audio/Plug-Ins/VST3/Phil S Audio/Massive PSXL.vst3   (VST3 - appears in the "Phil S Audio" folder)
#   /Library/Audio/Plug-Ins/Components/Massive PSXL.component     (Audio Unit - grouped under "Phil S Audio" by manufacturer name)
#   /Applications/Phil S Audio/Massive PSXL.app                   (standalone)
# Optional env vars for distribution outside your own Mac:
#   DEVELOPER_ID_APP        "Developer ID Application: Name (TEAMID)"  -> signs the binaries
#   DEVELOPER_ID_INSTALLER  "Developer ID Installer: Name (TEAMID)"   -> signs the .pkg
#   NOTARY_PROFILE          notarytool keychain profile                -> notarises + staples
set -euo pipefail

BUILD="${1:-build}"
VERSION="1.0.0"
ART="$BUILD/MassivePSXL_artefacts/Release"
VST3="$ART/VST3/Massive PSXL.vst3"
AU="$ART/AU/Massive PSXL.component"
APP="$ART/Standalone/Massive PSXL.app"
OUT="dist"
STAGE="$OUT/payload"

for f in "$VST3" "$AU" "$APP"; do
  [ -e "$f" ] || { echo "Missing build output: $f"; exit 1; }
done

rm -rf "$OUT"; mkdir -p "$STAGE/Library/Audio/Plug-Ins/VST3/Phil S Audio" "$STAGE/Library/Audio/Plug-Ins/Components" "$STAGE/Applications/Phil S Audio"
cp -R "$VST3" "$STAGE/Library/Audio/Plug-Ins/VST3/Phil S Audio/"
cp -R "$AU"   "$STAGE/Library/Audio/Plug-Ins/Components/"
cp -R "$APP"  "$STAGE/Applications/Phil S Audio/"

SIGN_ID="${DEVELOPER_ID_APP:--}"       # "-" = ad-hoc signature (required for arm64 binaries to load locally)
for b in "$STAGE/Library/Audio/Plug-Ins/VST3/Phil S Audio/Massive PSXL.vst3" \
         "$STAGE/Library/Audio/Plug-Ins/Components/Massive PSXL.component" \
         "$STAGE/Applications/Phil S Audio/Massive PSXL.app"; do
  codesign --force --deep --options runtime --timestamp=none --sign "$SIGN_ID" "$b" 2>/dev/null || codesign --force --deep --sign "$SIGN_ID" "$b"
done

PKG_ARGS=(--root "$STAGE" --identifier com.philsaudio.massivepsxl --version "$VERSION" --install-location /)
[ -n "${DEVELOPER_ID_INSTALLER:-}" ] && PKG_ARGS+=(--sign "$DEVELOPER_ID_INSTALLER")
pkgbuild "${PKG_ARGS[@]}" "$OUT/Massive-PSXL-$VERSION.pkg"

if [ -n "${NOTARY_PROFILE:-}" ] && [ -n "${DEVELOPER_ID_INSTALLER:-}" ]; then
  xcrun notarytool submit "$OUT/Massive-PSXL-$VERSION.pkg" --keychain-profile "$NOTARY_PROFILE" --wait
  xcrun stapler staple "$OUT/Massive-PSXL-$VERSION.pkg"
fi

# also a plain zip of the three bundles for manual installs
(cd "$STAGE" && ditto -c -k --sequesterRsrc --keepParent Library "../Massive-PSXL-$VERSION-plugins.zip")
echo "Done: $OUT/Massive-PSXL-$VERSION.pkg"
