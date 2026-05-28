"""
Patch bundle.game_data: append all required axe_dota_axe assets.

Entry format: TYPE_LEN[4LE] + TYPE + PATH_LEN[4LE] + PATH + DATA_LEN[4LE] + DATA
Header at byte 0: 4-byte entry count (LE), must be incremented.

Types: 'png'(3), 'fanim'(5), 'sound_info'(10)
"""
import struct, shutil, os, json

BUNDLE  = ("/home/nicoefschneider/snap/steam/common/.local/share/Steam"
           "/steamapps/common/Teamfight Manager2/bundle.game_data")
BACKUP  = BUNDLE + ".bak_axe"
MOD_DIR = ("/home/nicoefschneider/snap/steam/common/.local/share/Steam"
           "/steamapps/common/Teamfight Manager2/mods/axe_dota")

SHEET_PATH = b"asset/base/aseprite_resources/champions/axe_dota_axe#sheet"
ANIM_PATH  = b"asset/base/aseprite_resources/champions/axe_dota_axe#anim"

# sound_info entries: game looks up asset/base/sound/sfx/{id}_{action_name}
# Axe actions: attack (action_name="attack"), skill (="skill"), skill2 (="skill2"), ult (="ult")
# Point each to berserker's existing mp3 resources.
SOUND_INFOS = {
    "asset/base/sound/sfx/axe_dota_axe_attack":
        {"plays": [{"delay": 0.0, "clip": "berserker_attack0",          "volume": 1.0}]},
    "asset/base/sound/sfx/axe_dota_axe_skill":
        {"plays": [{"delay": 0.0, "clip": "berserker_skill_resource",   "volume": 1.0}]},
    "asset/base/sound/sfx/axe_dota_axe_skill2":
        {"plays": [{"delay": 0.0, "clip": "berserker_skill2_resource",  "volume": 1.0}]},
    "asset/base/sound/sfx/axe_dota_axe_ult":
        {"plays": [{"delay": 0.0, "clip": "berserker_ult_resource",     "volume": 1.0}]},
}

def make_entry(type_str: bytes, path: bytes, data: bytes) -> bytes:
    return (struct.pack("<I", len(type_str)) + type_str
          + struct.pack("<I", len(path))     + path
          + struct.pack("<I", len(data))     + data)

# Restore from backup
if os.path.exists(BACKUP):
    shutil.copy2(BACKUP, BUNDLE)
    print("Restored from backup")
else:
    shutil.copy2(BUNDLE, BACKUP)
    print(f"Created backup: {BACKUP}")

bundle = bytearray(open(BUNDLE, "rb").read())

if SHEET_PATH in bundle:
    print("ERROR: previous sprite patch still present — backup may be stale")
    exit(1)

entry_count = struct.unpack_from("<I", bundle, 0)[0]
print(f"Current entry count: {entry_count}")

# 1. Sprite sheet + anim
png_data  = open(f"{MOD_DIR}/aseprite_resources/champions/axe_dota_axe.png",      "rb").read()
anim_data = open(f"{MOD_DIR}/aseprite_resources/champions/axe_dota_axe.ase.json", "rb").read()
new_entries = [
    make_entry(b"png",   SHEET_PATH, png_data),
    make_entry(b"fanim", ANIM_PATH,  anim_data),
]
n = 2

# 2. sound_info entries for each action
for path_str, payload in SOUND_INFOS.items():
    data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    new_entries.append(make_entry(b"sound_info", path_str.encode(), data))
    n += 1

# Update header count and append
struct.pack_into("<I", bundle, 0, entry_count + n)
for entry in new_entries:
    bundle += entry

with open(BUNDLE, "wb") as f:
    f.write(bundle)

print(f"Appended {n} entries (sprite, anim, {len(SOUND_INFOS)} sound_info)")
print(f"New entry count: {entry_count + n}")
print(f"New bundle size: {os.path.getsize(BUNDLE):,} bytes")
