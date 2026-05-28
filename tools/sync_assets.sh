#!/bin/bash
# Re-embed the sprite sheet + animation into the game bundle after editing them.
# Usage: edit aseprite_resources/champions/axe_dota_axe.png (or .ase.json) in the
# repo, then run this script, then restart the game.
set -e

REPO=/home/nicoefschneider/Desktop/axe_dota
MOD_DIR="/home/nicoefschneider/snap/steam/common/.local/share/Steam/steamapps/common/Teamfight Manager2/mods/axe_dota"

cp "$REPO/aseprite_resources/champions/axe_dota_axe.png"      "$MOD_DIR/aseprite_resources/champions/axe_dota_axe.png"
cp "$REPO/aseprite_resources/champions/axe_dota_axe.ase.json" "$MOD_DIR/aseprite_resources/champions/axe_dota_axe.ase.json"
echo "Copied sprite + anim into mod folder."

python3 "$REPO/tools/patch_bundle.py"
echo "Done. Restart the game to see the updated sprite."
