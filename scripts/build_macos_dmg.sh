#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

VERSION="${CASEFLOW_VERSION:-1.1.1}"
BUILD_PYTHON="${BUILD_PYTHON:-python3}"

if [ "$(uname -s)" != "Darwin" ]; then
  echo "macOS DMG 只能在 macOS 上构建。"
  exit 1
fi

"$BUILD_PYTHON" -m venv .venv-build
.venv-build/bin/python -m pip install --upgrade pip
.venv-build/bin/pip install -r requirements.txt pyinstaller==6.16.0 pillow==11.3.0
.venv-build/bin/python scripts/generate_icons.py
iconutil -c icns build_assets/CaseFlow.iconset -o build_assets/CaseFlow.icns

PYINSTALLER_CONFIG_DIR="$ROOT/build/pyinstaller-config" \
  .venv-build/bin/pyinstaller caseflow-macos.spec --clean --noconfirm

STAGING="$(mktemp -d /tmp/caseflow-dmg-staging.XXXXXX)"
trap 'rm -rf "$STAGING"' EXIT
COPYFILE_DISABLE=1 ditto --norsrc --noextattr dist/CaseFlow.app "$STAGING/CaseFlow.app"
ln -s /Applications "$STAGING/Applications"
xattr -cr "$STAGING/CaseFlow.app"
codesign --force --deep --sign - "$STAGING/CaseFlow.app"
codesign --verify --deep --strict "$STAGING/CaseFlow.app"

DMG="$ROOT/dist/CaseFlow-macOS-Apple-Silicon-v${VERSION}.dmg"
hdiutil create -volname "CaseFlow" -srcfolder "$STAGING" -ov -format UDZO "$DMG"
echo "$DMG"
