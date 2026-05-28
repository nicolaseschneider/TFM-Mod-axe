"""
Patch bundle.game_data (0.4.4) with axe_dota_axe assets.

Restores from the clean 0.4.4 backup first, then appends:
  - #sheet  (png)        recolored Axe sprite
  - #anim   (fanim)      Axe animation (berserker layout + skill alias + spin)
  - 4x sound_info        attack / skill / skill2 / ult -> berserker mp3 clips

Entry format: TYPE_LEN[4LE] + TYPE + PATH_LEN[4LE] + PATH + DATA_LEN[4LE] + DATA
Header at byte 0: 4-byte little-endian entry count (incremented by 6).

If Steam updates the game again, delete bundle.game_data.bak_044, run
Steam "Verify integrity of game files", then re-create the backup and re-run.
"""
import struct, shutil, os, json

GAMEDIR = "/home/nicoefschneider/snap/steam/common/.local/share/Steam/steamapps/common/Teamfight Manager2"
BUNDLE  = f"{GAMEDIR}/bundle.game_data"
BACKUP  = f"{BUNDLE}.bak_044"           # clean verified 0.4.4 bundle
MOD_DIR = f"{GAMEDIR}/mods/axe_dota"

SHEET_PATH = b"asset/base/aseprite_resources/champions/axe_dota_axe#sheet"
ANIM_PATH  = b"asset/base/aseprite_resources/champions/axe_dota_axe#anim"

SOUND_INFOS = {
    "asset/base/sound/sfx/axe_dota_axe_attack":
        {"plays": [{"delay": 0.0, "clip": "berserker_attack0",         "volume": 1.0}]},
    "asset/base/sound/sfx/axe_dota_axe_skill":
        {"plays": [{"delay": 0.0, "clip": "berserker_skill_resource",  "volume": 1.0}]},
    "asset/base/sound/sfx/axe_dota_axe_skill2":
        {"plays": [{"delay": 0.0, "clip": "berserker_skill2_resource", "volume": 1.0}]},
    "asset/base/sound/sfx/axe_dota_axe_ult":
        {"plays": [{"delay": 0.0, "clip": "berserker_ult_resource",    "volume": 1.0}]},
}

def make_entry(type_str: bytes, path: bytes, data: bytes) -> bytes:
    return (struct.pack("<I", len(type_str)) + type_str
          + struct.pack("<I", len(path))     + path
          + struct.pack("<I", len(data))     + data)

if not os.path.exists(BACKUP):
    raise SystemExit(f"ERROR: clean 0.4.4 backup missing: {BACKUP}\n"
                     "Run Steam 'Verify integrity', then: cp bundle.game_data bundle.game_data.bak_044")

# Always start from the clean 0.4.4 backup
shutil.copy2(BACKUP, BUNDLE)
print("Restored clean 0.4.4 bundle from backup")

bundle = bytearray(open(BUNDLE, "rb").read())
entry_count = struct.unpack_from("<I", bundle, 0)[0]
print(f"Base entry count: {entry_count}")

png_data  = open(f"{MOD_DIR}/aseprite_resources/champions/axe_dota_axe.png",      "rb").read()
anim_data = open(f"{MOD_DIR}/aseprite_resources/champions/axe_dota_axe.ase.json", "rb").read()

new_entries = [
    make_entry(b"png",   SHEET_PATH, png_data),
    make_entry(b"fanim", ANIM_PATH,  anim_data),
]
for path_str, payload in SOUND_INFOS.items():
    data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    new_entries.append(make_entry(b"sound_info", path_str.encode(), data))

# Test Dummy champion — reuses Axe's sprite/anim, plain berserker sounds.
new_entries.append(make_entry(b"png",   b"asset/base/aseprite_resources/champions/axe_dota_dummy#sheet", png_data))
new_entries.append(make_entry(b"fanim", b"asset/base/aseprite_resources/champions/axe_dota_dummy#anim",  anim_data))
for action, clip in [("attack","berserker_attack0"), ("skill","berserker_skill_resource"), ("skill2","berserker_skill2_resource")]:
    payload = {"plays": [{"delay": 0.0, "clip": clip, "volume": 1.0}]}
    data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    new_entries.append(make_entry(b"sound_info", f"asset/base/sound/sfx/axe_dota_dummy_{action}".encode(), data))

struct.pack_into("<I", bundle, 0, entry_count + len(new_entries))
for e in new_entries:
    bundle += e

with open(BUNDLE, "wb") as f:
    f.write(bundle)

print(f"Appended {len(new_entries)} entries (sprite, anim, {len(SOUND_INFOS)} sound_info)")
print(f"New entry count: {entry_count + len(new_entries)}")
print(f"New bundle size: {os.path.getsize(BUNDLE):,} bytes")
