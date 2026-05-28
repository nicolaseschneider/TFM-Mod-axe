use mod_api::*;

const MOD_ID: &str = "axe_dota";

const CALL_JUMP_RANGE: u64 = 42_000;
const CALL_TAUNT_RADIUS: i64 = 35_000;
const CALL_TAUNT_RADIUS_SQ: i64 = CALL_TAUNT_RADIUS * CALL_TAUNT_RADIUS;
const CALL_TAUNT_TICKS: usize = 360; // 6 seconds at 60 ticks/sec
const HELIX_RADIUS_SQ: i64 = 30_000 * 30_000;

fn init(_ctx: &GameCtx) -> ModRegistration {
    let mut reg = ModRegistration::new(MOD_ID);
    reg.add_champion(Axe);
    reg
}

declare_mod!(init);

// ─── Champion definition ──────────────────────────────────────────────────────

#[derive(Clone, Debug)]
struct Axe;

impl ModChampionInfo for Axe {
    fn id(&self) -> &str { "axe_dota_axe" }
    fn name(&self) -> &str { "axe_dota_axe" }
    fn category(&self) -> ChampionCategory { ChampionCategory::Melee }
    fn tags(&self) -> Vec<ChampionTag> {
        vec![ChampionTag::AD, ChampionTag::Tank, ChampionTag::CC]
    }

    fn stat(&self) -> EntityStat {
        EntityStat {
            attack: 58,
            magic_power: 10,
            hp: 950,
            defence: 45,
            magic_resistance: 22,
            move_speed: 1100,
            hp_regen: 5,
            stack: 0,
            crit_chance: 0,
        }
    }

    fn growth(&self) -> EntityStat {
        EntityStat {
            attack: 5,
            magic_power: 1,
            hp: 100,
            defence: 5,
            magic_resistance: 3,
            move_speed: 0,
            hp_regen: 1,
            stack: 0,
            crit_chance: 0,
        }
    }

    fn skill_icon(&self, skill_index: usize) -> (String, String) {
        let sheet = "asset/base/aseprite_resources/UI_aseprite/skill_icon".to_string();
        let tag = match skill_index {
            0 => "berserker_0",   // attack
            1 => "berserker_2",   // Counter Helix (spin)
            2 => "fighter_1",     // Berserker's Call (taunt)
            3 => "executioner_3", // Culling Blade (execute)
            _ => "berserker_0",
        };
        (sheet, tag.to_string())
    }

    fn attack(&self) -> Box<dyn ModAction> { Box::new(AxeAttack) }
    fn skill(&self) -> Box<dyn ModAction> { Box::new(CounterHelixActive) }
    fn skill2(&self) -> Box<dyn ModAction> { Box::new(BerserkerCall) }
    fn ult(&self) -> Option<Box<dyn ModAction>> { Some(Box::new(CullingBlade)) }
    fn passive(&self) -> Option<Box<dyn ModPassive>> { Some(Box::new(CounterHelixPassive)) }
}

// ─── Basic attack ─────────────────────────────────────────────────────────────

#[derive(Clone, Debug)]
struct AxeAttack;

impl ModAction for AxeAttack {
    fn clone_box(&self) -> Box<dyn ModAction> { Box::new(self.clone()) }
    fn action_name(&self) -> &str { "attack" }
    fn duration(&self) -> usize { 50 }
    fn cooltime(&self, _stat: &EntityStat, _level: usize) -> usize { 0 }
    fn casting_target(&self) -> CastingTarget { CastingTarget::Enemy }

    fn effect(&self) -> Option<ModEffect> {
        Some(ModEffect {
            range: 18_000,
            growth_range: 0,
            start_timing: 20,
            casting: CastingType::Targeting,
            target: CastingTarget::Enemy,
            attack_type: AttackType::BaseAttack,
            effect_type: Box::new(AxeAttackEffect),
        })
    }
}

#[derive(Debug)]
struct AxeAttackEffect;

impl ModEffectType for AxeAttackEffect {
    fn apply(&self, ctx: &mut GameCtx, _rng: u64, caster_id: usize, input: InputTarget) {
        let InputTarget::Target { target_id } = input else { return };
        let dmg = ctx.get_entity(caster_id).map(|e| e.stat().attack).unwrap_or(0);
        ctx.deal_damage(caster_id, target_id, dmg, 0, AttackType::BaseAttack);
    }

    fn expected_damage(&self, stat: &EntityStat) -> (usize, usize) {
        (stat.attack, 0)
    }
}

// ─── Berserker's Call (AoE taunt, knight-style) ───────────────────────────────

#[derive(Clone, Debug)]
struct BerserkerCall;

impl ModAction for BerserkerCall {
    fn clone_box(&self) -> Box<dyn ModAction> { Box::new(self.clone()) }
    fn action_name(&self) -> &str { "skill2" }
    fn duration(&self) -> usize { 50 }
    fn cooltime(&self, _stat: &EntityStat, _level: usize) -> usize { 420 }
    fn casting_target(&self) -> CastingTarget { CastingTarget::Enemy }

    fn effect(&self) -> Option<ModEffect> {
        Some(ModEffect {
            range: CALL_JUMP_RANGE,
            growth_range: 0,
            start_timing: 10,
            casting: CastingType::Targeting,
            target: CastingTarget::Enemy,
            attack_type: AttackType::Skill,
            effect_type: Box::new(BerserkerCallEffect),
        })
    }
}

#[derive(Debug)]
struct BerserkerCallEffect;

impl ModEffectType for BerserkerCallEffect {
    fn apply(&self, ctx: &mut GameCtx, _rng: u64, caster_id: usize, input: InputTarget) {
        let InputTarget::Target { target_id } = input else { return };

        let target_pos = ctx.get_entity(target_id).map(|e| { let p = e.pos(); (p.x, p.y) });
        let caster_pos = ctx.get_entity(caster_id).map(|e| { let p = e.pos(); (p.x, p.y) });
        let (Some((tx, ty)), Some((cx, cy))) = (target_pos, caster_pos) else { return };

        // Jump TO the target.
        ctx.apply_cc(caster_id, CCState::ForceMove {
            tick: 20,
            dx: tx as i64 - cx as i64,
            dy: ty as i64 - cy as i64,
            speed: 5_000,
        });

        let caster_team = ctx.get_entity(caster_id).map(|e| e.team()).unwrap_or(usize::MAX);

        // Taunt enemy champions near the landing spot (the target's position).
        let mut targets: Vec<usize> = Vec::new();
        for i in 0..ctx.entity_count() {
            if let Some(e) = ctx.entity_at(i) {
                if e.team() != caster_team && e.is_champion() {
                    let p = e.pos();
                    let edx = p.x as i64 - tx as i64;
                    let edy = p.y as i64 - ty as i64;
                    if edx * edx + edy * edy <= CALL_TAUNT_RADIUS_SQ {
                        targets.push(e.id());
                    }
                }
            }
        }
        for tid in targets {
            ctx.apply_cc(tid, CCState::Taunt { tick: CALL_TAUNT_TICKS as u64, target: caster_id });
        }

        // Dota flavor: Axe gains heavy bonus armor for the taunt's duration.
        ctx.add_buff(caster_id, BuffState {
            duration: BuffType::Time { tick: CALL_TAUNT_TICKS },
            defence: 400,
            ..Default::default()
        });
    }

    fn expected_damage(&self, _stat: &EntityStat) -> (usize, usize) { (0, 0) }
    fn expected_cc_time(&self) -> Option<usize> { Some(CALL_TAUNT_TICKS) }
}

// ─── Counter Helix ────────────────────────────────────────────────────────────

#[derive(Clone, Debug)]
struct CounterHelixActive;

// Counter Helix is passive-only (like Ogre's Q): no active cast, 0 cooldown.
// The skill1 slot is inert; the spin is driven entirely by CounterHelixPassive.
impl ModAction for CounterHelixActive {
    fn clone_box(&self) -> Box<dyn ModAction> { Box::new(self.clone()) }
    fn action_name(&self) -> &str { "skill" }
    fn duration(&self) -> usize { 0 }
    fn cooltime(&self, _stat: &EntityStat, _level: usize) -> usize { 0 }
    fn casting_target(&self) -> CastingTarget { CastingTarget::Enemy }

    fn effect(&self) -> Option<ModEffect> { None }
}

#[derive(Clone, Debug)]
struct CounterHelixPassive;

impl ModPassive for CounterHelixPassive {
    fn clone_box(&self) -> Box<dyn ModPassive> { Box::new(self.clone()) }

    fn on_damaged(&mut self, ctx: &mut GameCtx, rng_seed: usize, entity_id: usize, _attacker_id: usize, _damage: usize) {
        if rng_seed % 100 < 20 {
            spin_attack(ctx, entity_id);
        }
    }
}

fn spin_attack(ctx: &mut GameCtx, caster_id: usize) {
    let (cx, cy) = match ctx.get_entity(caster_id) {
        Some(e) => { let p = e.pos(); (p.x, p.y) }
        None => return,
    };
    let team = ctx.get_entity(caster_id).map(|e| e.team()).unwrap_or(usize::MAX);
    let dmg = ctx.get_entity(caster_id)
        .map(|e| e.stat().attack * 70 / 100)
        .unwrap_or(0);

    // Hit all nearby enemies (champions + creeps/minions); skip towers to avoid
    // their missing death animation.
    let mut targets: Vec<usize> = Vec::new();
    for i in 0..ctx.entity_count() {
        if let Some(e) = ctx.entity_at(i) {
            if e.team() != team && e.id() != caster_id && !e.is_tower() {
                let p = e.pos();
                let dx = p.x as i64 - cx as i64;
                let dy = p.y as i64 - cy as i64;
                if dx * dx + dy * dy <= HELIX_RADIUS_SQ {
                    targets.push(e.id());
                }
            }
        }
    }
    for tid in targets {
        ctx.deal_damage(caster_id, tid, dmg, 0, AttackType::Skill);
    }
}

// ─── Culling Blade ────────────────────────────────────────────────────────────

#[derive(Clone, Debug)]
struct CullingBlade;

impl ModAction for CullingBlade {
    fn clone_box(&self) -> Box<dyn ModAction> { Box::new(self.clone()) }
    fn action_name(&self) -> &str { "ult" }
    fn duration(&self) -> usize { 80 }
    fn cooltime(&self, _stat: &EntityStat, _level: usize) -> usize { 1800 }
    fn casting_target(&self) -> CastingTarget { CastingTarget::Enemy }

    fn effect(&self) -> Option<ModEffect> {
        Some(ModEffect {
            range: 40_000,
            growth_range: 0,
            start_timing: 25,
            casting: CastingType::Targeting,
            target: CastingTarget::Enemy,
            attack_type: AttackType::Skill,
            effect_type: Box::new(CullingBladeEffect),
        })
    }
}

#[derive(Debug)]
struct CullingBladeEffect;

impl ModEffectType for CullingBladeEffect {
    fn apply(&self, ctx: &mut GameCtx, _rng: u64, caster_id: usize, input: InputTarget) {
        let InputTarget::Target { target_id } = input else { return };

        let target_pos = ctx.get_entity(target_id).map(|e| { let p = e.pos(); (p.x, p.y) });
        let caster_pos = ctx.get_entity(caster_id).map(|e| { let p = e.pos(); (p.x, p.y) });
        if let (Some((tx, ty)), Some((cx, cy))) = (target_pos, caster_pos) {
            ctx.apply_cc(caster_id, CCState::ForceMove {
                tick: 20,
                dx: tx as i64 - cx as i64,
                dy: ty as i64 - cy as i64,
                speed: 5_500,
            });
        }

        // Execute: instant kill if the target is at/below 25% max HP or <= 600 HP.
        // Otherwise just a moderate hit with no execute bonus.
        let (cur, max) = ctx.get_entity(target_id)
            .map(|e| { let h = e.hp(); (h.current, h.max) })
            .unwrap_or((0, 0));
        let execute = cur <= max * 25 / 100 || cur <= 600;
        if execute {
            ctx.deal_damage(caster_id, target_id, 1_000_000, 0, AttackType::Skill);
        } else {
            ctx.deal_damage(caster_id, target_id, 250, 0, AttackType::Skill);
        }

        let killed = ctx.get_entity(target_id)
            .map(|e| e.hp().current == 0)
            .unwrap_or(true);
        if !killed { return; }

        let caster_team = ctx.get_entity(caster_id).map(|e| e.team()).unwrap_or(usize::MAX);
        let speed_buff = BuffState {
            duration: BuffType::Time { tick: 300 },
            move_speed_mult: 25,
            ..Default::default()
        };

        let mut ally_ids: Vec<usize> = Vec::new();
        for i in 0..ctx.entity_count() {
            if let Some(e) = ctx.entity_at(i) {
                if e.team() == caster_team && e.is_champion() {
                    ally_ids.push(e.id());
                }
            }
        }
        for aid in ally_ids {
            ctx.add_buff(aid, speed_buff.clone());
        }

        ctx.add_buff(caster_id, BuffState {
            duration: BuffType::Permanent,
            defence: 5,
            ..Default::default()
        });
    }

    fn expected_damage(&self, _stat: &EntityStat) -> (usize, usize) {
        (600, 0)
    }
}
