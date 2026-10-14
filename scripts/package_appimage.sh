#!/bin/sh
# Wrap a Linux PyInstaller binary in an AppImage when appimagetool is installed.
# The native binary is still produced when appimagetool is absent.
set -eu

ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
VARIANT=lite
if [ "${1:-}" = "--rag" ]; then
  VARIANT=full
fi

if [ "$VARIANT" = "full" ]; then
  SPEC=build_rag.spec
  NAME=wx-assist
else
  SPEC=build.spec
  NAME=wx-assist_no_rag
fi

if [ "$VARIANT" = "full" ]; then
  python3 "$ROOT/scripts/build.py" --rag
else
  python3 "$ROOT/scripts/build.py"
fi
BIN="$ROOT/dist/$NAME"
if [ ! -f "$BIN" ]; then
  echo "expected binary at $BIN" >&2
  exit 1
fi

if ! command -v appimagetool >/dev/null 2>&1; then
  echo "appimagetool not found. Linux artifact is the binary:"
  echo "  $BIN"
  echo "Install appimagetool to also produce an AppImage."
  exit 0
fi

APPDIR="$ROOT/dist/${NAME}.AppDir"
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin"
cp "$BIN" "$APPDIR/usr/bin/$NAME"
chmod +x "$APPDIR/usr/bin/$NAME"

if [ -f "$ROOT/ui/public/favicon.png" ]; then
  cp "$ROOT/ui/public/favicon.png" "$APPDIR/${NAME}.png"
  cp "$ROOT/ui/public/favicon.png" "$APPDIR/wx-assist.png"
fi

cat > "$APPDIR/wx-assist.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=摘星
Comment=Local WeChat assistant
Exec=$NAME
Icon=wx-assist
Categories=Utility;
Terminal=false
EOF

cat > "$APPDIR/AppRun" <<EOF
#!/bin/sh
HERE=\$(dirname "\$(readlink -f "\$0")")
exec "\$HERE/usr/bin/$NAME" "\$@"
EOF
chmod +x "$APPDIR/AppRun"

(
  cd "$ROOT/dist"
  ARCH="${ARCH:-$(uname -m)}" appimagetool "$APPDIR" "${NAME}-${ARCH}.AppImage"
)
echo "AppImage: $ROOT/dist/${NAME}-$(uname -m).AppImage"
