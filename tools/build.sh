#!/bin/bash
# Build axe_dota.dll via Wine-hosted Windows rustc (cross-compile won't work:
# the SDK proc-macros engine_macro/game_macro/core_macro are Windows-only DLLs).
set -o pipefail

WINE="/home/nicoefschneider/snap/steam/common/.local/share/Steam/steamapps/common/Proton 10.0/files/bin/wine64"
export WINEPREFIX=/home/nicoefschneider/.wineprefix_axe
export WINEDEBUG=-all

RUSTC_WIN=/tmp/rustc_win/rustc-nightly-x86_64-pc-windows-msvc/rustc
RUSTLLD="$RUSTC_WIN/lib/rustlib/x86_64-pc-windows-msvc/bin/rust-lld.exe"
SDK=/tmp/tfm2_sdk_link
CRT_STUBS=/tmp/crt_stubs.o
XWIN=/home/nicoefschneider/.cache/cargo-xwin/xwin
SRC=/home/nicoefschneider/Desktop/axe_dota/src/lib.rs
OUT=/home/nicoefschneider/Desktop/axe_dota/axe_dota.dll

to_wine() { echo "Z:$1" | sed 's|/|\\\\|g'; }

echo "=== Building axe_dota.dll ==="
"$WINE" "$RUSTC_WIN/bin/rustc.exe" \
    --edition 2021 \
    --crate-type cdylib \
    --crate-name axe_dota \
    --target x86_64-pc-windows-msvc \
    --sysroot "$(to_wine $RUSTC_WIN)" \
    -C "linker=$(to_wine $RUSTLLD)" \
    -C "link-arg=/LIBPATH:$(to_wine $XWIN/crt/lib/x86_64)" \
    -C "link-arg=/LIBPATH:$(to_wine $XWIN/sdk/lib/ucrt/x86_64)" \
    -C "link-arg=/LIBPATH:$(to_wine $XWIN/sdk/lib/um/x86_64)" \
    -C "link-arg=vcruntime.lib" \
    -C "link-arg=ucrt.lib" \
    -C "link-arg=$(to_wine $CRT_STUBS)" \
    -L "dependency=$(to_wine $SDK/deps)" \
    --extern "mod_api=$(to_wine $SDK/deps/libmod_api-0a24296d2b45e79d.rlib)" \
    -L "native=$(to_wine $SDK/native)" \
    "$(to_wine $SRC)" \
    -o "$(to_wine $OUT)" \
    2>&1 | grep -ivE 'fixme:|wineserver|FreeType|ole3|equal to 2.0.5|^$' || true

STATUS=${PIPESTATUS[0]}
echo "=== Build exit: $STATUS ==="
[ $STATUS -eq 0 ] && ls -lh "$OUT"
exit $STATUS
