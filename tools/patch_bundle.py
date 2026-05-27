"""
Append axe_dota_axe sprite (#sheet) and anim (#anim) entries to bundle.game_data.

Bundle entry format: \x00\x00 + TYPE[4] + PATH_LEN[4LE] + PATH + DATA_LEN[4LE] + DATA
  - PNG  type bytes: \x00png  (0x00, 0x70, 0x6E, 0x67)
  - anim type bytes: anim     (0x61, 0x6E, 0x69, 0x6D)
"""
import struct, shutil, os

BUNDLE = ("/home/nicoefschneider/snap/steam/common/.local/share/Steam"
          "/steamapps/common/Teamfight Manager2/bundle.game_data")
PNG_SRC   = ("/home/nicoefschneider/snap/steam/common/.local/share/Steam"
             "/steamapps/common/Teamfight Manager2/mods/axe_dota"
             "/aseprite_resources/champions/axe_dota_axe.png")
ANIM_SRC  = ("/home/nicoefschneider/snap/steam/common/.local/share/Steam"
             "/steamapps/common/Teamfight Manager2/mods/axe_dota"
             "/aseprite_resources/champions/axe_dota_axe.ase.json")
BACKUP    = BUNDLE + ".bak_axe"

SHEET_PATH = b"asset/base/aseprite_resources/champions/axe_dota_axe#sheet"
ANIM_PATH  = b"asset/base/aseprite_resources/champions/axe_dota_axe#anim"

def make_entry(type4: bytes, path: bytes, data: bytes) -> bytes:
    assert len(type4) == 4
    hdr = b"\x00\x00" + type4 + struct.pack("<I", len(path))
    tail = struct.pack("<I", len(data))
    return hdr + path + tail + data

# Check not already patched
bundle_data = open(BUNDLE, "rb").read()
if SHEET_PATH in bundle_data:
    print("Already patched — axe_dota_axe#sheet already in bundle")
    exit(0)

# Backup
if not os.path.exists(BACKUP):
    shutil.copy2(BUNDLE, BACKUP)
    print(f"Backup created: {BACKUP}")
else:
    print(f"Backup already exists: {BACKUP}")

png_data  = open(PNG_SRC,  "rb").read()
anim_data = open(ANIM_SRC, "rb").read()

sheet_entry = make_entry(b"\x00png", SHEET_PATH, png_data)
anim_entry  = make_entry(b"anim",   ANIM_PATH,  anim_data)

with open(BUNDLE, "ab") as f:
    f.write(sheet_entry)
    f.write(anim_entry)

print(f"Appended {len(sheet_entry)} bytes (sheet) + {len(anim_entry)} bytes (anim)")
print(f"New bundle size: {os.path.getsize(BUNDLE):,} bytes")
print(f"Sheet path ({len(SHEET_PATH)}b): {SHEET_PATH.decode()}")
print(f"Anim  path ({len(ANIM_PATH)}b):  {ANIM_PATH.decode()}")
