# SDK Issue: Native (DLL) mod champions are not credited in stats / kill feed / post-game

**Game version:** base 0.4.4
**Mod type:** native Rust `cdylib` champion built against the shipped `mod-sdk` (`mod_api` rlib)
**Toolchain:** rustc nightly matching `mod-sdk/toolchain_version.txt` (1.98.0-nightly, 2026-05-25)

## Summary

A champion registered via `ModChampionInfo` (`ModRegistration::add_champion`) is **fully functional in the simulation** — it spawns, moves, auto-attacks, casts its abilities, takes damage, and its `GameCtx::deal_damage` calls **do reduce enemy HP**. However, the champion is **never credited in the meta/stats layer**:

- Post-game shows **0 damage dealt** for the mod champion.
- It records **no kills and no assists**, even on clean solo kills.
- The **kill feed shows an empty square** (no champion portrait) for the killer slot.

The damage is real in-match (enemies visibly lose HP and die), but none of it is attributed to the mod champion in any stat/UI surface.

## Reproduction (minimal)

1. Register a trivial champion via `ModChampionInfo` with a basic attack whose effect calls
   `ctx.deal_damage(caster_id, target_id, attack, 0, AttackType::BaseAttack)`.
2. Provide the expected assets so it loads/plays: `champions/{id}#sheet` + `#anim`,
   `sound/sfx/{id}_{action}` (sound_info), a `style/champion_view` entry, and a
   `setting/champion_info` `mod_champions[]` `ModChampionEntry { id, stat, growth, category, tags }`.
3. Play a match with the champion; let it kill an enemy.
4. Observe: enemy HP drops and they die, but post-game = 0 damage, 0 kills, 0 assists, and the
   kill feed killer icon is blank.

## What we verified / ruled out

- `deal_damage` is called with the correct signature `(usize caster, usize target, usize physical, usize magic, AttackType)` — confirmed via the compiler. The damage applies.
- The champion is registered in **both** places we could find: the `champion_info` `mod_champions[]` array as a `ModChampionEntry`, and a `champion_view` entry. Neither changes the result.
- Sprite (`#sheet`), animation (`#anim`), `sound_info`, and `skill_icon` are all present (the champion renders and animates on cast).
- **Confirmed not kit-specific:** a second, dead-simple test champion (vanilla stats, a single plain basic attack, no abilities, no passive) shows the **same** 0-damage / no-kills / empty-portrait result. So this affects *every* native mod champion, not a particular implementation.

## Likely cause (from binary inspection)

- `ResultKillLog { tick, killer_team, killer_position, killer_champion, killed_champion }` — `killer_champion` appears to be a base-roster champion identifier that a DLL-registered champion cannot occupy.
- The kill-feed layout (`asset/base/ui/layout/ingame_component/kill_log`) sets `killer_slot.icon` programmatically; for a mod champion there is no resolvable portrait → empty square.
- `GameCtx` exposes only **read-only** `kill_log_count` / `kill_log_at`; there is no API for a mod to record damage dealt or claim kill/assist credit.

## Request

Please expose a way for native mod champions to participate in the stats/kill-feed/post-game systems — e.g.:
- have `deal_damage` attribute damage to the (mod) caster in the stat tallies, and
- allow a mod champion to be recorded as `killer_champion` with a resolvable kill-feed portrait (the champion's `#sheet` + `champion_view.face` would suffice).

Alternatively, if this is intended/known, documenting the limitation in the SDK would save modders the investigation. Happy to provide a minimal repro mod.
