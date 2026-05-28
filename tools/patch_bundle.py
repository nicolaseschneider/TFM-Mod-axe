"""
Patch bundle.game_data: append axe_dota_axe #sheet (png) and #anim (fanim) entries.

Correct bundle entry format (NO \x00\x00 marker):
  TYPE_LEN[4LE] + TYPE[type_len] + PATH_LEN[4LE] + PATH[path_len] + DATA_LEN[4LE] + DATA[data_len]

Header at byte 0: 4-byte entry count (little-endian). Must be incremented by 2.

Types:
  "png"   (3 bytes) for sprite sheets
  "fanim" (5 bytes) for animation JSON
"""
import struct, shutil, os

BUNDLE = ("/home/nicoefschneider/snap/steam/common/.local/share/Steam"
          "/steamapps/common/Teamfight Manager2/bundle.game_data")
BACKUP = BUNDLE + ".bak_axe"
PNG_SRC  = ("/home/nicoefschneider/snap/steam/common/.local/share/Steam"
            "/steamapps/common/Teamfight Manager2/mods/axe_dota"
            "/aseprite_resources/champions/axe_dota_axe.png")
ANIM_SRC = ("/home/nicoefschneider/snap/steam/common/.local/share/Steam"
            "/steamapps/common/Teamfight Manager2/mods/axe_dota"
            "/aseprite_resources/champions/axe_dota_axe.ase.json")

SHEET_PATH = b"asset/base/aseprite_resources/champions/axe_dota_axe#sheet"
ANIM_PATH  = b"asset/base/aseprite_resources/champions/axe_dota_axe#anim"

def make_entry(type_str: bytes, path: bytes, data: bytes) -> bytes:
    return (struct.pack("<I", len(type_str)) + type_str
          + struct.pack("<I", len(path))     + path
          + struct.pack("<I", len(data))     + data)

# --- Restore from backup first if backup exists ---
if os.path.exists(BACKUP):
    shutil.copy2(BACKUP, BUNDLE)
    print("Restored from backup")
else:
    shutil.copy2(BUNDLE, BACKUP)
    print(f"Created backup: {BACKUP}")

bundle = bytearray(open(BUNDLE, "rb").read())

if SHEET_PATH in bundle:
    print("Already patched!")
    exit(0)

# Read and increment header count
entry_count = struct.unpack_from("<I", bundle, 0)[0]
print(f"Current entry count: {entry_count}")

png_data  = open(PNG_SRC,  "rb").read()
anim_data = open(ANIM_SRC, "rb").read()

sheet_entry = make_entry(b"png",   SHEET_PATH, png_data)
anim_entry  = make_entry(b"fanim", ANIM_PATH,  anim_data)

# Update header count
struct.pack_into("<I", bundle, 0, entry_count + 2)
print(f"Updated entry count: {entry_count + 2}")

# Append entries
bundle += sheet_entry
bundle += anim_entry

with open(BUNDLE, "wb") as f:
    f.write(bundle)

size = os.path.getsize(BUNDLE)
print(f"Appended {len(sheet_entry)} (sheet) + {len(anim_entry)} (anim) bytes")
print(f"New bundle size: {size:,} bytes")
print(f"New entry count header: {struct.unpack_from('<I', bundle, 0)[0]}")
