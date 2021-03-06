import gettext
import __builtin__

__builtin__._ = gettext.gettext

from calcs.rogue import RogueDamageCalculator
from core import exceptions


class InputNotModeledException(exceptions.InvalidInputException):
    # I'll return these when inputs don't make sense to the model.
    pass


class AldrianasRogueDamageCalculator(RogueDamageCalculator):
    ###########################################################################
    # Main DPS comparison function.  Calls the appropriate sub-function based
    # on talent tree.
    ###########################################################################

    def get_dps(self):
        if self.talents.is_assassination_rogue():
            self.init_assassination()
            return self.assassination_dps_estimate()
        elif self.talents.is_combat_rogue():
            return self.combat_dps_estimate()
        elif self.talents.is_subtlety_rogue():
            return self.subtlety_dps_estimate()
        else:
            raise InputNotModeledException(_('You must have 31 points in at least one talent tree.'))

    def get_dps_breakdown(self):
        if self.talents.is_assassination_rogue():
            self.init_assassination()
            return self.assassination_dps_breakdown()
        elif self.talents.is_combat_rogue():
            return self.combat_dps_breakdown()
        elif self.talents.is_subtlety_rogue():
            return self.subtlety_dps_breakdown()
        else:
            raise InputNotModeledException(_('You must have 31 points in at least one talent tree.'))

    ###########################################################################
    # General object manipulation functions that we'll use multiple places.
    ###########################################################################

    PRECISION_REQUIRED = 10 ** -7

    def are_close_enough(self, old_dist, new_dist):
        for item in new_dist.keys():
            if item not in old_dist:
                return False
            elif not hasattr(new_dist[item], '__iter__'):
                if abs(new_dist[item] - old_dist[item]) > self.PRECISION_REQUIRED:
                    return False
            else:
                for index in range(len(new_dist[item])):
                    if abs(new_dist[item][index] - old_dist[item][index]) > self.PRECISION_REQUIRED:
                        return False
        return True

    def get_dps_contribution(self, damage_tuple, crit_rate, frequency):
        (base_damage, crit_damage) = damage_tuple
        average_hit = base_damage * (1 - crit_rate) + crit_damage * crit_rate
        return average_hit * frequency

    ###########################################################################
    # General modeling functions for pulling information useful across all
    # models.
    ###########################################################################

    def heroism_uptime_per_fight(self):
        if not self.buffs.short_term_haste_buff:
            return 0

        total_uptime = 0
        remaining_duration = self.settings.duration
        while remaining_duration > 0:
            total_uptime += min(remaining_duration, 40)
            remaining_duration -= 600

        return total_uptime * 1.0 / self.settings.duration

    def get_heroism_haste_multiplier(self):
        # Just average-casing for now.  Should fix that at some point.
        return 1 + .3 * self.heroism_uptime_per_fight()

    def get_cp_distribution_for_cycle(self, cp_distribution_per_move, target_cp_quantity):
        cur_min_cp = 0
        ruthlessness_chance = self.talents.ruthlessness * .2
        cur_dist = {(0, 0): (1-ruthlessness_chance), (1, 0): ruthlessness_chance}
        while cur_min_cp < target_cp_quantity:
            cur_min_cp += 1

            new_dist = {}
            for (cps, moves), prob in cur_dist.items():
                if cps >= cur_min_cp:
                    if (cps, moves) in new_dist:
                        new_dist[(cps, moves)] += prob
                    else:
                        new_dist[(cps, moves)] = prob
                else:
                    for (move_cp, move_prob) in cp_distribution_per_move.items():
                        total_cps = cps + move_cp
                        if total_cps > 5:
                            total_cps = 5
                        dist_entry = (total_cps, moves + 1)
                        if dist_entry in new_dist:
                            new_dist[dist_entry] += move_prob * prob
                        else:
                            new_dist[dist_entry] = move_prob * prob
            cur_dist = new_dist

        return cur_dist

    def get_snd_length(self, size):
        duration = 6 + 3 * size
        if self.glyphs.slice_and_dice:
            duration += 6
        return duration * (1 + .25 * self.talents.improved_slice_and_dice)

    def set_constants(self):
        # General setup that we'll use in all 3 cycles.
        self.bonus_energy_regen = 0
        if self.settings.tricks_on_cooldown and not self.glyphs.tricks_of_the_trade:
            self.bonus_energy_regen -= 15. / (30 + self.settings.response_time)
        if self.race.arcane_torrent:
            self.bonus_energy_regen += 15. / (120 + self.settings.response_time)

        self.base_stats = {
            'agi': self.stats.agi + self.buffs.buff_agi() + self.race.racial_agi,
            'ap': self.stats.ap + 140,
            'crit': self.stats.crit,
            'haste': self.stats.haste,
            'mastery': self.stats.mastery
        }

        for boost in self.race.get_racial_stat_boosts():
            if boost['stat'] in self.base_stats:
                self.base_stats[boost['stat']] += boost['value'] * boost['duration'] * 1.0 / (boost['cooldown'] + self.settings.response_time)

        for stat in self.base_stats:
            for boost in self.stats.gear_buffs.get_all_activated_boosts_for_stat(stat):
                if boost['cooldown'] is not None:
                    self.base_stats[stat] += (boost['value'] * boost['duration']) * 1.0 / (boost['cooldown'] + self.settings.response_time)
                else:
                    self.base_stats[stat] += (boost['value'] * boost['duration']) * 1.0 / self.settings.duration

        self.agi_multiplier = self.buffs.stat_multiplier() * self.stats.gear_buffs.leather_specialization_multiplier()

        self.base_strength = self.stats.str + self.buffs.buff_str() + self.race.racial_str
        self.base_strength *= self.buffs.stat_multiplier()

        self.relentless_strikes_energy_return_per_cp = [0, 1.75, 3.5, 5][self.talents.relentless_strikes]

        self.base_speed_multiplier = 1.4 * self.buffs.melee_haste_multiplier() * self.get_heroism_haste_multiplier()
        if self.race.berserking:
            self.base_speed_multiplier *= (1 + .2 * 10. / (180 + self.settings.response_time))
        if self.race.time_is_money:
            self.base_speed_multiplier *= 1.01

        self.strike_hit_chance = self.one_hand_melee_hit_chance()
        self.base_rupture_energy_cost = 20 + 5 / self.strike_hit_chance
        self.base_eviscerate_energy_cost = 28 + 7 / self.strike_hit_chance

    def get_proc_damage_contribution(self, proc, proc_count, current_stats):
        base_damage = proc.value

        if proc.stat == 'spell_damage':
            multiplier = self.raid_settings_modifiers(is_spell=True)
            crit_multiplier = self.crit_damage_modifiers(is_spell=True)
            crit_rate = self.spell_crit_rate(crit=current_stats['crit'])
        elif proc.stat == 'physical_damage':
            multiplier = self.raid_settings_modifiers(is_physical=True)
            crit_multiplier = self.crit_damage_modifiers(is_physical=True)
            crit_rate = self.melee_crit_rate(agi=current_stats['agi'], crit=current_stats['crit'])
        else:
            return 0

        return base_damage * multiplier * (1 + crit_rate * (crit_multiplier - 1)) * proc_count

    def get_rocket_barrage_damage(self, ap, current_stats):
        base_damage = self.race.calculate_rocket_barrage(ap, 0, 0) * self.raid_settings_modifiers(is_spell=True)
        crit_multiplier = self.crit_damage_modifiers(is_spell=True)
        crit_rate = self.spell_crit_rate(crit=current_stats['crit'])

        return base_damage * (1 + crit_rate * (crit_multiplier - 1)) / (120 + self.settings.response_time)

    def get_damage_breakdown(self, current_stats, attacks_per_second, crit_rates, damage_procs):
        # Vendetta may want to be handled elsewhere.
        average_ap = current_stats['ap'] + 2 * current_stats['agi'] + self.base_strength
        average_ap *= self.buffs.attack_power_multiplier()
        if self.talents.is_combat_rogue():
            average_ap *= 1.2
        average_ap *= (1 + .01 * self.talents.savage_combat)

        damage_breakdown = {}

        (mh_base_damage, mh_crit_damage) = self.mh_damage(average_ap)
        mh_hit_rate = self.dual_wield_mh_hit_chance() - self.GLANCE_RATE - crit_rates['mh_autoattacks']
        average_mh_hit = self.GLANCE_RATE * self.GLANCE_MULTIPLIER * mh_base_damage + mh_hit_rate * mh_base_damage + crit_rates['mh_autoattacks'] * mh_crit_damage
        mh_dps = average_mh_hit * attacks_per_second['mh_autoattacks']

        (oh_base_damage, oh_crit_damage) = self.oh_damage(average_ap)
        oh_hit_rate = self.dual_wield_oh_hit_chance() - self.GLANCE_RATE - crit_rates['oh_autoattacks']
        average_oh_hit = self.GLANCE_RATE * self.GLANCE_MULTIPLIER * oh_base_damage + oh_hit_rate * oh_base_damage + crit_rates['oh_autoattacks'] * oh_crit_damage
        oh_dps = average_oh_hit * attacks_per_second['oh_autoattacks']

        damage_breakdown['autoattack'] = mh_dps + oh_dps

        for key in attacks_per_second.keys():
            if not attacks_per_second[key]:
                del attacks_per_second[key]

        if 'mutilate' in attacks_per_second:
            mh_mutilate_dps = self.get_dps_contribution(self.mh_mutilate_damage(average_ap), crit_rates['mutilate'], attacks_per_second['mutilate'])
            oh_mutilate_dps = self.get_dps_contribution(self.oh_mutilate_damage(average_ap), crit_rates['mutilate'], attacks_per_second['mutilate'])
            damage_breakdown['mutilate'] = mh_mutilate_dps + oh_mutilate_dps

        if 'hemorrhage' in attacks_per_second:
            damage_breakdown['hemorrhage'] = self.get_dps_contribution(self.hemorrhage_damage(average_ap), crit_rates['hemorrhage'], attacks_per_second['hemorrhage'])

        if 'backstab' in attacks_per_second:
            damage_breakdown['backstab'] = self.get_dps_contribution(self.backstab_damage(average_ap), crit_rates['backstab'], attacks_per_second['backstab'])

        if 'sinister_strike' in attacks_per_second:
            damage_breakdown['sinister_strike'] = self.get_dps_contribution(self.sinister_strike_damage(average_ap), crit_rates['sinister_strike'], attacks_per_second['sinister_strike'])

        if 'revealing_strike' in attacks_per_second:
            damage_breakdown['revealing_strike'] = self.get_dps_contribution(self.revealing_strike_damage(average_ap), crit_rates['revealing_strike'], attacks_per_second['revealing_strike'])

        if 'main_gauche' in attacks_per_second:
            damage_breakdown['main_gauche'] = self.get_dps_contribution(self.main_gauche_damage(average_ap), crit_rates['main_gauche'], attacks_per_second['main_gauche'])

        if 'ambush' in attacks_per_second:
            damage_breakdown['ambush'] = self.get_dps_contribution(self.ambush_damage(average_ap), crit_rates['ambush'], attacks_per_second['ambush'])

        if 'mh_killing_spree' in attacks_per_second:
            damage_breakdown['killing_spree'] = (self.get_dps_contribution(self.mh_killing_spree_damage(average_ap), crit_rates['mh_killing_spree'], attacks_per_second['mh_killing_spree']) +
                                                 self.get_dps_contribution(self.oh_killing_spree_damage(average_ap), crit_rates['oh_killing_spree'], attacks_per_second['oh_killing_spree']))

        if 'rupture_ticks' in attacks_per_second:
            damage_breakdown['rupture'] = 0
            for i in xrange(1, 6):
                damage_breakdown['rupture'] += self.get_dps_contribution(self.rupture_tick_damage(average_ap, i), crit_rates['rupture_ticks'], attacks_per_second['rupture_ticks'][i])

        if 'envenom' in attacks_per_second:
            damage_breakdown['envenom'] = 0
            for i in xrange(1, 6):
                damage_breakdown['envenom'] += self.get_dps_contribution(self.envenom_damage(average_ap, i, current_stats['mastery']), crit_rates['envenom'], attacks_per_second['envenom'][i])

        if 'eviscerate' in attacks_per_second:
            damage_breakdown['eviscerate'] = 0
            for i in xrange(1, 6):
                damage_breakdown['eviscerate'] += self.get_dps_contribution(self.eviscerate_damage(average_ap, i), crit_rates['eviscerate'], attacks_per_second['eviscerate'][i])

        if 'venomous_wounds' in attacks_per_second:
            damage_breakdown['venomous_wounds'] = self.get_dps_contribution(self.venomous_wounds_damage(average_ap, mastery=current_stats['mastery']), crit_rates['venomous_wounds'], attacks_per_second['venomous_wounds'])

        if 'instant_poison' in attacks_per_second:
            damage_breakdown['instant_poison'] = self.get_dps_contribution(self.instant_poison_damage(average_ap, mastery=current_stats['mastery']), crit_rates['instant_poison'], attacks_per_second['instant_poison'])

        if 'deadly_poison' in attacks_per_second:
            damage_breakdown['deadly_poison'] = self.get_dps_contribution(self.deadly_poison_tick_damage(average_ap, mastery=current_stats['mastery']), crit_rates['deadly_poison'], attacks_per_second['deadly_poison'])

        if 'wound_poison' in attacks_per_second:
            damage_breakdown['wound_poison'] = self.get_dps_contribution(self.wound_poison_damage(average_ap, mastery=current_stats['mastery']), crit_rates['wound_poison'], attacks_per_second['wound_poison'])

        for proc in damage_procs:
            damage_breakdown[proc.proc_name] = self.get_proc_damage_contribution(proc, attacks_per_second[proc.proc_name], current_stats)

        if self.race.rocket_barrage:
            damage_breakdown['rocket_barrage'] = self.get_rocket_barrage_damage(average_ap, current_stats)

        return damage_breakdown

    def get_mh_procs_per_second(self, proc, attacks_per_second, crit_rates):
        triggers_per_second = 0
        if proc.procs_off_auto_attacks():
            if proc.procs_off_crit_only():
                triggers_per_second += attacks_per_second['mh_autoattack_hits'] * crit_rates['mh_autoattacks']
            else:
                triggers_per_second += attacks_per_second['mh_autoattack_hits']
        if proc.procs_off_strikes():
            for ability in ('mutilate', 'backstab', 'revealing_strike', 'sinister_strike', 'ambush', 'hemorrhage', 'mh_killing_spree'):
                if ability in attacks_per_second:
                    if proc.procs_off_crit_only():
                        triggers_per_second += attacks_per_second[ability] * crit_rates[ability]
                    else:
                        triggers_per_second += attacks_per_second[ability]
            for ability in ('envenom', 'eviscerate'):
                if ability in attacks_per_second:
                    if proc.procs_off_crit_only():
                        triggers_per_second += sum(attacks_per_second[ability]) * crit_rates[ability]
                    else:
                        triggers_per_second += sum(attacks_per_second[ability])
        if proc.procs_off_apply_debuff():
            if 'rupture' in attacks_per_second:
                if not proc.procs_off_crit_only():
                    triggers_per_second += attacks_per_second['rupture']

        return triggers_per_second * proc.proc_rate(self.stats.mh.speed)

    def get_oh_procs_per_second(self, proc, attacks_per_second, crit_rates):
        triggers_per_second = 0
        if proc.procs_off_auto_attacks():
            if proc.procs_off_crit_only():
                triggers_per_second += attacks_per_second['oh_autoattack_hits'] * crit_rates['oh_autoattacks']
            else:
                triggers_per_second += attacks_per_second['oh_autoattack_hits']
        if proc.procs_off_strikes():
            for ability in ('mutilate', 'main_gauche', 'oh_killing_spree'):
                if ability in attacks_per_second:
                    if proc.procs_off_crit_only():
                        triggers_per_second += attacks_per_second[ability] * crit_rates[ability]
                    else:
                        triggers_per_second += attacks_per_second[ability]

        return triggers_per_second * proc.proc_rate(self.stats.oh.speed)

    def get_other_procs_per_second(self, proc, attacks_per_second, crit_rates):
        triggers_per_second = 0

        if proc.procs_off_harmful_spells():
            for ability in ('instant_poison', 'wound_poison', 'venomous_wounds'):
                if ability in attacks_per_second:
                    if proc.procs_off_crit_only():
                        triggers_per_second += attacks_per_second[ability] * crit_rates[ability]
                    else:
                        triggers_per_second += attacks_per_second[ability]
        if proc.procs_off_periodic_spell_damage():
            if 'deadly_poison' in attacks_per_second:
                if proc.procs_off_crit_only():
                    triggers_per_second += attacks_per_second['deadly_poison'] * crit_rates['deadly_poison']
                else:
                    triggers_per_second += attacks_per_second['deadly_poison']
        if proc.procs_off_bleeds():
            if 'rupture_ticks' in attacks_per_second:
                if proc.procs_off_crit_only():
                    triggers_per_second += sum(attacks_per_second['rupture_ticks']) * crit_rates['rupture']
                else:
                    triggers_per_second += sum(attacks_per_second['rupture_ticks'])

        if proc.is_ppm():
            if triggers_per_second == 0:
                return 0
            else:
                raise InputNotModeledException(_('PPMs that also proc off spells are not yet modeled.'))
        else:
            return triggers_per_second * proc.proc_rate()

    def get_procs_per_second(self, proc, attacks_per_second, crit_rates):
        # TODO: Include damaging proc hits in figuring out how often everything else procs.
        if getattr(proc, 'mh_only', False):
            procs_per_second = self.get_mh_procs_per_second(proc, attacks_per_second, crit_rates)
        elif getattr(proc, 'oh_only', False):
            procs_per_second = self.get_oh_procs_per_second(proc, attacks_per_second, crit_rates)
        else:
            procs_per_second = self.get_mh_procs_per_second(proc, attacks_per_second, crit_rates) + self.get_oh_procs_per_second(proc, attacks_per_second, crit_rates) + self.get_other_procs_per_second(proc, attacks_per_second, crit_rates)

        return procs_per_second

    def set_uptime(self, proc, attacks_per_second, crit_rates):
        procs_per_second = self.get_procs_per_second(proc, attacks_per_second, crit_rates)

        if proc.icd:
            proc.uptime = proc.duration / (proc.icd + 1. / procs_per_second)
        else:
            # See http://elitistjerks.com/f31/t20747-advanced_rogue_mechanics_discussion/#post621369
            # for the derivation of this formula.
            if procs_per_second >= 1 and proc.duration >= 1:
                proc.uptime = proc.max_stacks
            else:
                q = 1 - procs_per_second
                Q = q ** proc.duration
                P = 1 - Q
                proc.uptime = P * (1 - P ** proc.max_stacks) / Q

    def update_with_damaging_proc(self, proc, attacks_per_second, crit_rates):
        if proc.stat == 'spell_damage':
            attacks_per_second[proc.proc_name] = self.get_procs_per_second(proc, attacks_per_second, crit_rates) * self.spell_hit_chance()
        elif proc.stat == 'physical_damage':
            attacks_per_second[proc.proc_name] = self.get_procs_per_second(proc, attacks_per_second, crit_rates) * self.strike_hit_chance

    def unheeded_warning_multiplier(self, attacks_per_second, crit_rates):
        proc = self.stats.procs.unheeded_warning
        if not proc:
            return 1

        self.set_uptime(proc, attacks_per_second, crit_rates)
        return 1 + proc.value * proc.uptime

    def update_crit_rates_for_4pc_t11(self, attacks_per_second, crit_rates):
        t11_4pc_bonus = self.stats.procs.rogue_t11_4pc
        if t11_4pc_bonus:
            direct_damage_finisher = ''
            for key in ('envenom', 'eviscerate'):
                if key in attacks_per_second and sum(attacks_per_second[key]) != 0:
                    if direct_damage_finisher:
                        raise InputNotModeledException(_('Unable to model the 4pc T11 set bonus in a cycle that uses both eviscerate and envenom'))
                    direct_damage_finisher = key

            if direct_damage_finisher:
                procs_per_second = self.get_procs_per_second(t11_4pc_bonus, attacks_per_second, crit_rates)
                finisher_spacing = min(1 / sum(attacks_per_second[direct_damage_finisher]), t11_4pc_bonus.duration)
                p = 1 - (1-procs_per_second) ** finisher_spacing
                crit_rates[direct_damage_finisher] = p + (1 - p) * crit_rates[direct_damage_finisher]

    def get_poison_counts(self, total_mh_hits, total_oh_hits, attacks_per_second):
        if self.settings.mh_poison == 'dp' or self.settings.oh_poison == 'dp':
            attacks_per_second['deadly_poison'] = 1./3

        if self.settings.mh_poison == 'ip':
            mh_proc_rate = self.stats.mh.speed / 7.
        elif self.settings.mh_poison == 'wp':
            mh_proc_rate = self.stats.mh.speed / 2.8
        else: # Deadly Poison
            mh_proc_rate = .3

        if self.settings.oh_poison == 'ip':
            oh_proc_rate = self.stats.oh.speed / 7.
        elif self.settings.oh_poison == 'wp':
            oh_proc_rate = self.stats.oh.speed / 2.8
        else: # Deadly Poison
            oh_proc_rate = .3

        mh_poison_procs = total_mh_hits * mh_proc_rate * self.spell_hit_chance()
        oh_poison_procs = total_oh_hits * oh_proc_rate * self.spell_hit_chance()

        poison_setup = self.settings.mh_poison + self.settings.oh_poison
        if poison_setup in ['ipip', 'ipdp', 'dpip']:
            attacks_per_second['instant_poison'] = mh_poison_procs + oh_poison_procs
        elif poison_setup in ['wpwp', 'wpdp', 'dpwp']:
            attacks_per_second['wound_poison'] = mh_poison_procs + oh_poison_procs
        elif poison_setup == 'ipwp':
            attacks_per_second['instant_poison'] = mh_poison_procs
            attacks_per_second['wound_poison'] = oh_poison_procs
        elif poison_setup == 'wpip':
            attacks_per_second['wound_poison'] = mh_poison_procs
            attacks_per_second['instant_poison'] = oh_poison_procs

    def compute_damage(self, attack_counts_function):
        # TODO: Crit cap
        #
        # TODO: Hit/Exp procs

        current_stats = {
            'agi': self.base_stats['agi'] * self.agi_multiplier,
            'ap': self.base_stats['ap'],
            'crit': self.base_stats['crit'],
            'haste': self.base_stats['haste'],
            'mastery': self.base_stats['mastery']
        }

        active_procs = []
        damage_procs = []

        for proc_info in self.stats.procs.get_all_procs_for_stat():
            if proc_info.stat in current_stats and not proc_info.is_ppm():
                active_procs.append(proc_info)
            if proc_info.stat in ('spell_damage', 'physical_damage'):
                damage_procs.append(proc_info)

        mh_landslide = self.stats.mh.landslide
        if mh_landslide:
            mh_landslide.mh_only = True
            active_procs.append(mh_landslide)

        mh_hurricane = self.stats.mh.hurricane
        if mh_hurricane:
            mh_hurricane.mh_only = True
            active_procs.append(mh_hurricane)

        oh_landslide = self.stats.oh.landslide
        if oh_landslide:
            oh_landslide.oh_only = True
            active_procs.append(oh_landslide)

        oh_hurricane = self.stats.oh.hurricane
        if oh_hurricane:
            oh_hurricane.oh_only = True
            active_procs.append(oh_hurricane)

        attacks_per_second, crit_rates = attack_counts_function(current_stats)

        while True:
            current_stats = {
                'agi': self.base_stats['agi'],
                'ap': self.base_stats['ap'],
                'crit': self.base_stats['crit'],
                'haste': self.base_stats['haste'],
                'mastery': self.base_stats['mastery']
            }

            self.update_crit_rates_for_4pc_t11(attacks_per_second, crit_rates)

            for proc in damage_procs:
                if not proc.icd:
                    self.update_with_damaging_proc(proc, attacks_per_second, crit_rates)

            for proc in active_procs:
                if not proc.icd:
                    self.set_uptime(proc, attacks_per_second, crit_rates)
                    current_stats[proc.stat] += proc.uptime * proc.value

            current_stats['agi'] *= self.agi_multiplier

            old_attacks_per_second = attacks_per_second
            attacks_per_second, crit_rates = attack_counts_function(current_stats)

            if self.are_close_enough(old_attacks_per_second, attacks_per_second):
                break

        for proc in active_procs:
            if proc.icd:
                self.set_uptime(proc, attacks_per_second, crit_rates)
                if proc.stat == 'agi':
                    current_stats[proc.stat] += proc.uptime * proc.value * self.agi_multiplier
                else:
                    current_stats[proc.stat] += proc.uptime * proc.value

        attacks_per_second, crit_rates = attack_counts_function(current_stats)

        self.update_crit_rates_for_4pc_t11(attacks_per_second, crit_rates)

        for proc in damage_procs:
            self.update_with_damaging_proc(proc, attacks_per_second, crit_rates)

        damage_breakdown = self.get_damage_breakdown(current_stats, attacks_per_second, crit_rates ,damage_procs)
        damage_breakdown['autoattack'] *= self.unheeded_warning_multiplier(attacks_per_second, crit_rates)
        return damage_breakdown

    ###########################################################################
    # Assassination DPS functions
    ###########################################################################

    def init_assassination(self):
        # Call this before calling any of the assassination_dps functions
        # directly.  If you're just calling get_dps, you can ignore this as it
        # happens automatically; however, if you're going to pull a damage
        # breakdown or other sub-result, make sure to call this, as it
        # initializes many values that are needed to perform the calculations.

        if self.settings.cycle._cycle_type != 'assassination':
            raise InputNotModeledException(_('You must specify an assassination cycle to match your assassination spec.'))
        if self.stats.mh.type != 'dagger' or self.stats.oh.type != 'dagger':
            raise InputNotModeledException(_('Assassination modeling requires daggers in both hands'))

        if self.settings.mh_poison + self.settings.oh_poison not in ('ipdp', 'dpip'):
            raise InputNotModeledException(_('Assassination modeling requires instant poison on one weapon and deadly on the other'))

        # These talents have huge, hard-to-model implications on cycle and will
        # always be taken in any serious DPS build.  Hence, I'm not going to
        # worry about modeling them for the foreseeable future.
        if self.talents.master_poisoner != 1:
            raise InputNotModeledException(_('Assassination modeling requires one point in Master Poisoner'))
        if self.talents.cut_to_the_chase != 3:
            raise InputNotModeledException(_('Assassination modeling requires three points in Cut to the Chase'))

        self.set_constants()

        self.envenom_energy_cost = 28 + 7 / self.strike_hit_chance

        self.base_energy_regen = 10
        if self.talents.overkill:
            self.base_energy_regen += 60 / (180. + self.settings.response_time)

        if self.talents.cold_blood:
            self.bonus_energy_regen += 25. / (120 + self.settings.response_time)

        if self.talents.vendetta:
            if self.glyphs.vendetta:
                self.vendetta_mult = 1.06
            else:
                self.vendetta_mult = 1.05
        else:
            self.vendetta_mult = 1

    def assassination_dps_estimate(self):
        mutilate_dps = self.assassination_dps_estimate_mutilate() * (1 - self.settings.time_in_execute_range)
        backstab_dps = self.assassination_dps_estimate_backstab() * self.settings.time_in_execute_range
        return backstab_dps + mutilate_dps

    def assassination_dps_estimate_backstab(self):
        return sum(self.assassination_dps_breakdown_backstab().values())

    def assassination_dps_estimate_mutilate(self):
        return sum(self.assassination_dps_breakdown_mutilate().values())

    def assassination_dps_breakdown(self):
        mutilate_dps_breakdown = self.assassination_dps_breakdown_mutilate()
        backstab_dps_breakdown = self.assassination_dps_breakdown_backstab()

        mutilate_weight = 1 - self.settings.time_in_execute_range
        backstab_weight = self.settings.time_in_execute_range

        dps_breakdown = {}
        for source, quantity in mutilate_dps_breakdown.items():
            dps_breakdown[source] = quantity * mutilate_weight

        for source, quantity in backstab_dps_breakdown.items():
            if source in dps_breakdown:
                dps_breakdown[source] += quantity * backstab_weight
            else:
                dps_breakdown[source] = quantity * backstab_weight

        return dps_breakdown

    def assassination_dps_breakdown_mutilate(self):
        self.mutilate_energy_cost = 48 + 12 / self.strike_hit_chance
        if self.glyphs.mutilate:
            self.mutilate_energy_cost -= 5

        damage_breakdown = self.compute_damage(self.assassination_attack_counts_mutilate)

        for key in damage_breakdown:
            damage_breakdown[key] *= self.vendetta_mult

        return damage_breakdown

    def assassination_dps_breakdown_backstab(self):
        damage_breakdown = self.compute_damage(self.assassination_attack_counts_backstab)

        for key in damage_breakdown:
            damage_breakdown[key] *= self.vendetta_mult

        return damage_breakdown

    def assassination_attack_counts_mutilate(self, current_stats):
        base_melee_crit_rate = self.melee_crit_rate(agi=current_stats['agi'], crit=current_stats['crit'])
        base_spell_crit_rate = self.spell_crit_rate(crit=current_stats['crit'])

        haste_multiplier = self.stats.get_haste_multiplier_from_rating(current_stats['haste'])

        energy_regen = self.base_energy_regen * haste_multiplier
        energy_regen += self.bonus_energy_regen
        energy_regen_with_rupture = energy_regen + 1.5 * self.talents.venomous_wounds

        attack_speed_multiplier = self.base_speed_multiplier * haste_multiplier

        mutilate_crit_rate = base_melee_crit_rate + self.stats.gear_buffs.rogue_t11_2pc_crit_bonus() + .05 * self.talents.puncturing_wounds
        if mutilate_crit_rate > 1:
            mutilate_crit_rate = 1.

        crit_rates = {
            'mh_autoattacks': min(base_melee_crit_rate, self.dual_wield_mh_hit_chance() - self.GLANCE_RATE),
            'oh_autoattacks': min(base_melee_crit_rate, self.dual_wield_oh_hit_chance() - self.GLANCE_RATE),
            'mutilate': mutilate_crit_rate,
            'envenom': base_melee_crit_rate,
            'rupture_ticks': base_melee_crit_rate,
            'venomous_wounds': base_spell_crit_rate,
            'instant_poison': base_spell_crit_rate,
            'deadly_poison': base_spell_crit_rate
        }

        seal_fate_proc_rate = 1 - (1 - mutilate_crit_rate * .5 * self.talents.seal_fate) ** 2
        cp_per_mut = {2: 1 - seal_fate_proc_rate, 3: seal_fate_proc_rate}
        cp_distribution = self.get_cp_distribution_for_cycle(cp_per_mut, self.settings.cycle.min_envenom_size_mutilate)

        # This cycle need a *lot* of work, but in the interest of getting some
        # sort of numbers out of this, I'm going to go with ye olde cheap hack
        # for the moment.

        muts_per_finisher = 0
        cp_per_finisher = 0
        finisher_size_breakdown = [0, 0, 0, 0, 0, 0]
        for (cps, muts), probability in cp_distribution.items():
            muts_per_finisher += muts * probability
            cp_per_finisher += cps * probability
            finisher_size_breakdown[cps] += probability

        energy_for_rupture = muts_per_finisher * self.mutilate_energy_cost + self.base_rupture_energy_cost - cp_per_finisher * self.relentless_strikes_energy_return_per_cp
        rupture_downtime = .5 * energy_for_rupture / energy_regen
        average_rupture_length = 2 * (3 + cp_per_finisher + 2 * self.glyphs.rupture)
        average_cycle_length = rupture_downtime + average_rupture_length

        energy_for_envenoms = average_rupture_length * energy_regen_with_rupture - .5 * energy_for_rupture
        envenom_energy_cost = muts_per_finisher * self.mutilate_energy_cost + self.envenom_energy_cost - cp_per_finisher * self.relentless_strikes_energy_return_per_cp
        envenoms_per_cycle = energy_for_envenoms / envenom_energy_cost

        attacks_per_second = {}

        envenoms_per_second = envenoms_per_cycle / average_cycle_length
        attacks_per_second['rupture'] = 1 / average_cycle_length
        attacks_per_second['mutilate'] = (envenoms_per_second + attacks_per_second['rupture']) * muts_per_finisher

        if self.talents.cold_blood:
            envenoms_per_cold_blood = 120 * envenoms_per_second
            crit_rates['envenom'] = ((envenoms_per_cold_blood - 1) * crit_rates['envenom'] + 1) / envenoms_per_cold_blood

        attacks_per_second['envenom'] = [finisher_chance * envenoms_per_second for finisher_chance in finisher_size_breakdown]

        attacks_per_second['rupture_ticks'] = [0, 0, 0, 0, 0, 0]
        for i in xrange(1, 6):
            ticks_per_rupture = 3 + i + 2 * self.glyphs.rupture
            attacks_per_second['rupture_ticks'][i] = ticks_per_rupture * attacks_per_second['rupture'] * finisher_size_breakdown[i]

        total_rupture_ticks = sum(attacks_per_second['rupture_ticks'])
        attacks_per_second['venomous_wounds'] = total_rupture_ticks * .3 * self.talents.venomous_wounds * self.spell_hit_chance()

        attacks_per_second['mh_autoattacks'] = attack_speed_multiplier / self.stats.mh.speed
        attacks_per_second['oh_autoattacks'] = attack_speed_multiplier / self.stats.oh.speed

        attacks_per_second['mh_autoattack_hits'] = attacks_per_second['mh_autoattacks'] * self.dual_wield_mh_hit_chance()
        attacks_per_second['oh_autoattack_hits'] = attacks_per_second['oh_autoattacks'] * self.dual_wield_oh_hit_chance()

        total_mh_hits_per_second = attacks_per_second['mh_autoattack_hits'] + attacks_per_second['mutilate'] + envenoms_per_second + attacks_per_second['rupture']
        total_oh_hits_per_second = attacks_per_second['oh_autoattack_hits'] + attacks_per_second['mutilate']

        if self.settings.mh_poison == 'ip':
            ip_base_proc_rate = .3 * self.stats.mh.speed / 1.4
        else:
            ip_base_proc_rate = .3 * self.stats.oh.speed / 1.4

        ip_envenom_proc_rate = ip_base_proc_rate * 1.5

        dp_base_proc_rate = .5
        dp_envenom_proc_rate = dp_base_proc_rate + .15

        envenom_uptime = min(sum([(1 / self.strike_hit_chance + cps) * attacks_per_second['envenom'][cps] for cps in xrange(1,6)]), 1)
        avg_ip_proc_rate = ip_base_proc_rate * (1 - envenom_uptime) + ip_envenom_proc_rate * envenom_uptime
        avg_dp_proc_rate = dp_base_proc_rate * (1 - envenom_uptime) + dp_envenom_proc_rate * envenom_uptime

        if self.settings.mh_poison == 'ip':
            mh_poison_procs = avg_ip_proc_rate * total_mh_hits_per_second
            oh_poison_procs = avg_dp_proc_rate * total_oh_hits_per_second
        else:
            mh_poison_procs = avg_dp_proc_rate * total_mh_hits_per_second
            oh_poison_procs = avg_ip_proc_rate * total_oh_hits_per_second

        attacks_per_second['instant_poison'] = (mh_poison_procs + oh_poison_procs) * self.spell_hit_chance()
        attacks_per_second['deadly_poison'] = 1. / 3

        return attacks_per_second, crit_rates

    def assassination_attack_counts_backstab(self, current_stats):
        base_melee_crit_rate = self.melee_crit_rate(agi=current_stats['agi'], crit=current_stats['crit'])
        base_spell_crit_rate = self.spell_crit_rate(crit=current_stats['crit'])

        haste_multiplier = self.stats.get_haste_multiplier_from_rating(current_stats['haste'])

        energy_regen = self.base_energy_regen * haste_multiplier
        energy_regen += self.bonus_energy_regen
        energy_regen_with_rupture = energy_regen + 1.5 * self.talents.venomous_wounds

        attack_speed_multiplier = self.base_speed_multiplier * haste_multiplier

        backstab_crit_rate = base_melee_crit_rate + self.stats.gear_buffs.rogue_t11_2pc_crit_bonus() + .1 * self.talents.puncturing_wounds
        if backstab_crit_rate > 1:
            backstab_crit_rate = 1.

        crit_rates = {
            'mh_autoattacks': min(base_melee_crit_rate, self.dual_wield_mh_hit_chance() - self.GLANCE_RATE),
            'oh_autoattacks': min(base_melee_crit_rate, self.dual_wield_oh_hit_chance() - self.GLANCE_RATE),
            'backstab': backstab_crit_rate,
            'envenom': base_melee_crit_rate,
            'rupture_ticks': base_melee_crit_rate,
            'venomous_wounds': base_spell_crit_rate,
            'instant_poison': base_spell_crit_rate,
            'deadly_poison': base_spell_crit_rate
        }

        backstab_energy_cost = 48 + 12 / self.strike_hit_chance
        backstab_energy_cost -= 15 * self.talents.murderous_intent
        if self.glyphs.backstab:
            backstab_energy_cost -= 5 * backstab_crit_rate

        seal_fate_proc_rate = backstab_crit_rate * .5 * self.talents.seal_fate
        cp_per_backstab = {1: 1-seal_fate_proc_rate, 2: seal_fate_proc_rate}
        cp_distribution = self.get_cp_distribution_for_cycle(cp_per_backstab, self.settings.cycle.min_envenom_size_backstab)

        # This cycle need a *lot* of work, but in the interest of getting some
        # sort of numbers out of this, I'm going to go with ye olde cheap hack
        # for the moment.

        bs_per_finisher = 0
        cp_per_finisher = 0
        finisher_size_breakdown = [0, 0, 0, 0, 0, 0]
        for (cps, bs), probability in cp_distribution.items():
            bs_per_finisher += bs * probability
            cp_per_finisher += cps * probability
            finisher_size_breakdown[cps] += probability

        energy_for_rupture = bs_per_finisher * backstab_energy_cost + self.base_rupture_energy_cost - cp_per_finisher * self.relentless_strikes_energy_return_per_cp
        rupture_downtime = .5 * energy_for_rupture / energy_regen
        average_rupture_length = 2 * (3 + cp_per_finisher + 2 * self.glyphs.rupture)
        average_cycle_length = rupture_downtime + average_rupture_length

        energy_for_envenoms = average_rupture_length * energy_regen_with_rupture - .5 * energy_for_rupture
        envenom_energy_cost = bs_per_finisher * backstab_energy_cost + self.envenom_energy_cost - cp_per_finisher * self.relentless_strikes_energy_return_per_cp
        envenoms_per_cycle = energy_for_envenoms / envenom_energy_cost

        attacks_per_second = {}

        envenoms_per_second = envenoms_per_cycle / average_cycle_length
        attacks_per_second['rupture'] = 1 / average_cycle_length
        attacks_per_second['backstab'] = (envenoms_per_second + attacks_per_second['rupture']) * bs_per_finisher

        if self.talents.cold_blood:
            envenoms_per_cold_blood = 120 * envenoms_per_second
            crit_rates['envenom'] = ((envenoms_per_cold_blood - 1) * crit_rates['envenom'] + 1) / envenoms_per_cold_blood

        attacks_per_second['envenom'] = [finisher_chance * envenoms_per_second for finisher_chance in finisher_size_breakdown]

        attacks_per_second['rupture_ticks'] = [0, 0, 0, 0, 0, 0]
        for i in xrange(1, 6):
            ticks_per_rupture = 3 + i + 2 * self.glyphs.rupture
            attacks_per_second['rupture_ticks'][i] = ticks_per_rupture * attacks_per_second['rupture'] * finisher_size_breakdown[i]

        total_rupture_ticks = sum(attacks_per_second['rupture_ticks'])
        attacks_per_second['venomous_wounds'] = total_rupture_ticks * .3 * self.talents.venomous_wounds * self.spell_hit_chance()

        attacks_per_second['mh_autoattacks'] = attack_speed_multiplier / self.stats.mh.speed
        attacks_per_second['oh_autoattacks'] = attack_speed_multiplier / self.stats.oh.speed

        attacks_per_second['mh_autoattack_hits'] = attacks_per_second['mh_autoattacks'] * self.dual_wield_mh_hit_chance()
        attacks_per_second['oh_autoattack_hits'] = attacks_per_second['oh_autoattacks'] * self.dual_wield_oh_hit_chance()

        total_mh_hits_per_second = attacks_per_second['mh_autoattack_hits'] + attacks_per_second['backstab'] + envenoms_per_second + attacks_per_second['rupture']
        total_oh_hits_per_second = attacks_per_second['oh_autoattack_hits']

        if self.settings.mh_poison == 'ip':
            ip_base_proc_rate = .3 * self.stats.mh.speed / 1.4
        else:
            ip_base_proc_rate = .3 * self.stats.oh.speed / 1.4

        ip_envenom_proc_rate = ip_base_proc_rate * 1.5

        dp_base_proc_rate = .5
        dp_envenom_proc_rate = dp_base_proc_rate + .15

        envenom_uptime = min(sum([(1 / self.strike_hit_chance + cps) * attacks_per_second['envenom'][cps] for cps in xrange(1,6)]), 1)
        avg_ip_proc_rate = ip_base_proc_rate * (1 - envenom_uptime) + ip_envenom_proc_rate * envenom_uptime
        avg_dp_proc_rate = dp_base_proc_rate * (1 - envenom_uptime) + dp_envenom_proc_rate * envenom_uptime

        if self.settings.mh_poison == 'ip':
            mh_poison_procs = avg_ip_proc_rate * total_mh_hits_per_second
            oh_poison_procs = avg_dp_proc_rate * total_oh_hits_per_second
        else:
            mh_poison_procs = avg_dp_proc_rate * total_mh_hits_per_second
            oh_poison_procs = avg_ip_proc_rate * total_oh_hits_per_second

        attacks_per_second['instant_poison'] = (mh_poison_procs + oh_poison_procs) * self.spell_hit_chance()
        attacks_per_second['deadly_poison'] = 1. / 3

        return attacks_per_second, crit_rates

    ###########################################################################
    # Combat DPS functions
    ###########################################################################

    def combat_dps_estimate(self):
        return sum(self.combat_dps_breakdown().values())

    def combat_dps_breakdown(self):
        if self.settings.cycle._cycle_type != 'combat':
            raise InputNotModeledException(_('You must specify a combat cycle to match your combat spec.'))

        if self.settings.cycle.use_revealing_strike not in ('sometimes', 'always', 'never'):
            raise InputNotModeledException(_('Revealing strike usage must be set to always, sometimes, or never'))

        if not self.talents.revealing_strike and self.settings.cycle.use_revealing_strike != 'never':
            raise InputNotModeledException(_('Cannot specify revealing strike usage in cycle without taking the talent.'))

        self.set_constants()

        if self.talents.bandits_guile:
            self.max_bandits_guile_buff = 1.3
        else:
            self.max_bandits_guile_buff = 1

        self.base_revealing_strike_energy_cost = 32 + 8 / self.strike_hit_chance
        self.base_sinister_strike_energy_cost = 36 + 9 / self.strike_hit_chance - 2 * self.talents.improved_sinister_strike

        self.base_energy_regen = 12.5

        damage_breakdown = self.compute_damage(self.combat_attack_counts)
        for key in damage_breakdown:
            if key == 'killing_spree':
                if self.settings.cycle.ksp_immediately:
                    damage_breakdown[key] *= self.bandits_guile_multiplier * (1.2 + .1 * self.glyphs.killing_spree)
                else:
                    damage_breakdown[key] *= self.max_bandits_guile_buff * (1.2 + .1 * self.glyphs.killing_spree)
            elif key in ('sinister_strike', 'revealing_strike'):
                damage_breakdown[key] *= self.bandits_guile_multiplier
            elif key == 'eviscerate':
                damage_breakdown[key] *= self.bandits_guile_multiplier * self.revealing_strike_multiplier
            elif key == 'rupture':
                damage_breakdown[key] *= self.bandits_guile_multiplier * self.ksp_multiplier * self.revealing_strike_multiplier
            else:
                damage_breakdown[key] *= self.bandits_guile_multiplier * self.ksp_multiplier

        return damage_breakdown

    def combat_attack_counts(self, current_stats):
        attacks_per_second = {}

        base_melee_crit_rate = self.melee_crit_rate(agi=current_stats['agi'], crit=current_stats['crit'])
        base_spell_crit_rate = self.spell_crit_rate(crit=current_stats['crit'])

        haste_multiplier = self.stats.get_haste_multiplier_from_rating(current_stats['haste'])

        attack_speed_multiplier = self.base_speed_multiplier * haste_multiplier * (1 + .02 * self.talents.lightning_reflexes)

        attacks_per_second['mh_autoattacks'] = attack_speed_multiplier / self.stats.mh.speed
        attacks_per_second['oh_autoattacks'] = attack_speed_multiplier / self.stats.oh.speed

        attacks_per_second['mh_autoattack_hits'] = attacks_per_second['mh_autoattacks'] * self.dual_wield_mh_hit_chance()
        attacks_per_second['oh_autoattack_hits'] = attacks_per_second['oh_autoattacks'] * self.dual_wield_oh_hit_chance()

        main_gauche_proc_rate = .02 * self.stats.get_mastery_from_rating(current_stats['mastery']) * self.off_hand_melee_hit_chance()
        attacks_per_second['main_gauche'] = main_gauche_proc_rate * attacks_per_second['mh_autoattacks']

        autoattack_cp_regen = self.talents.combat_potency * (attacks_per_second['oh_autoattack_hits'] + attacks_per_second['main_gauche'])
        energy_regen = self.base_energy_regen * haste_multiplier + self.bonus_energy_regen + autoattack_cp_regen

        rupture_energy_cost = self.base_rupture_energy_cost - main_gauche_proc_rate * self.talents.combat_potency
        eviscerate_energy_cost = self.base_eviscerate_energy_cost - main_gauche_proc_rate * self.talents.combat_potency
        revealing_strike_energy_cost = self.base_revealing_strike_energy_cost - main_gauche_proc_rate * self.talents.combat_potency
        sinister_strike_energy_cost = self.base_sinister_strike_energy_cost - main_gauche_proc_rate * self.talents.combat_potency

        crit_rates = {
            'mh_autoattacks': min(base_melee_crit_rate, self.dual_wield_mh_hit_chance() - self.GLANCE_RATE),
            'oh_autoattacks': min(base_melee_crit_rate, self.dual_wield_oh_hit_chance() - self.GLANCE_RATE),
            'main_gauche': base_melee_crit_rate,
            'sinister_strike': base_melee_crit_rate + self.stats.gear_buffs.rogue_t11_2pc_crit_bonus(),
            'revealing_strike': base_melee_crit_rate,
            'eviscerate': base_melee_crit_rate + .1 * self.glyphs.eviscerate,
            'mh_killing_spree': base_melee_crit_rate,
            'oh_killing_spree': base_melee_crit_rate,
            'rupture_ticks': base_melee_crit_rate,
            'instant_poison': base_spell_crit_rate,
            'deadly_poison': base_spell_crit_rate,
            'wound_poison': base_spell_crit_rate
        }

        extra_cp_chance = 0
        if self.glyphs.sinister_strike:
            extra_cp_chance = .2

        cp_per_ss = {1: 1 - extra_cp_chance, 2: extra_cp_chance}
        FINISHER_SIZE = 5

        if self.settings.cycle.use_revealing_strike == 'never':
            cp_distribution = self.get_cp_distribution_for_cycle(cp_per_ss, FINISHER_SIZE)

            rvs_per_finisher = 0
            ss_per_finisher = 0
            cp_per_finisher = 0
            finisher_size_breakdown = [0, 0, 0, 0, 0, 0]
            for (cps, ss), probability in cp_distribution.items():
                ss_per_finisher += ss * probability
                cp_per_finisher += cps * probability
                finisher_size_breakdown[cps] += probability
        elif self.settings.cycle.use_revealing_strike == 'sometimes':
            cp_distribution = self.get_cp_distribution_for_cycle(cp_per_ss, FINISHER_SIZE - 1)

            rvs_per_finisher = 0
            ss_per_finisher = 0
            cp_per_finisher = 0
            finisher_size_breakdown = [0, 0, 0, 0, 0, 0]
            for (cps, ss), probability in cp_distribution.items():
                ss_per_finisher += ss * probability
                if cps < FINISHER_SIZE:
                    actual_cps = cps + 1
                    rvs_per_finisher += probability
                else:
                    actual_cps = cps
                cp_per_finisher += actual_cps * probability
                finisher_size_breakdown[actual_cps] += probability
        else:
            cp_distribution = self.get_cp_distribution_for_cycle(cp_per_ss, FINISHER_SIZE - 1)
            
            rvs_per_finisher = 1
            ss_per_finisher = 0
            cp_per_finisher = 0
            finisher_size_breakdown = [0, 0, 0, 0, 0, 0]
            for (cps, ss), probability in cp_distribution.items():
                ss_per_finisher += ss * probability
                actual_cps = min(cps + 1, 5)
                cp_per_finisher += actual_cps * probability
                finisher_size_breakdown[actual_cps] += probability

        self.revealing_strike_multiplier = (1 + (.2 + .1 * self.glyphs.revealing_strike) * rvs_per_finisher)

        energy_cost_to_generate_cps = rvs_per_finisher * revealing_strike_energy_cost + ss_per_finisher * sinister_strike_energy_cost
        total_eviscerate_cost = energy_cost_to_generate_cps + eviscerate_energy_cost - cp_per_finisher * self.relentless_strikes_energy_return_per_cp
        total_rupture_cost = energy_cost_to_generate_cps + rupture_energy_cost - cp_per_finisher * self.relentless_strikes_energy_return_per_cp

        ss_per_snd = (total_eviscerate_cost - cp_per_finisher * self.relentless_strikes_energy_return_per_cp + 25) / sinister_strike_energy_cost
        snd_size = ss_per_snd * (1 + extra_cp_chance) + .2 * self.talents.ruthlessness
        snd_cost = ss_per_snd * sinister_strike_energy_cost + 25 - snd_size * self.relentless_strikes_energy_return_per_cp

        snd_duration = self.get_snd_length(snd_size)

        energy_spent_on_snd = snd_cost / (snd_duration - self.settings.response_time)

        avg_rupture_gap = (total_rupture_cost - .5 * total_eviscerate_cost) / energy_regen
        avg_rupture_duration = 2 * (3 + 2 * self.glyphs.rupture + cp_per_finisher)
        if self.settings.cycle.use_rupture:
            attacks_per_second['rupture'] = 1 / (avg_rupture_duration + avg_rupture_gap)
        else:
            attacks_per_second['rupture'] = 0
        energy_spent_on_rupture = total_rupture_cost * attacks_per_second['rupture']

        energy_available_for_evis = energy_regen - energy_spent_on_snd - energy_spent_on_rupture
        evis_per_second = energy_available_for_evis / total_eviscerate_cost

        cp_spent_on_damage_finishers_per_second = (attacks_per_second['rupture'] + evis_per_second) * cp_per_finisher

        if self.talents.adrenaline_rush:
            ar_duration = 15 + 5 * self.glyphs.adrenaline_rush
        else:
            ar_duration = 0

        ar_bonus_cp_regen = autoattack_cp_regen * .2
        ar_bonus_energy = ar_duration * (ar_bonus_cp_regen + 10 * haste_multiplier)
        ar_bonus_evis = ar_bonus_energy / total_eviscerate_cost
        ar_cooldown_self_reduction = ar_bonus_evis * cp_per_finisher * self.talents.restless_blades

        ar_actual_cooldown = (180 - ar_cooldown_self_reduction) / (1 + cp_spent_on_damage_finishers_per_second * self.talents.restless_blades) + self.settings.response_time
        total_evis_per_second = evis_per_second + ar_bonus_evis / ar_actual_cooldown

        ar_uptime = ar_duration / ar_actual_cooldown
        ar_autoattack_multiplier = 1 + .2 * ar_uptime

        for attack in ('mh_autoattacks', 'mh_autoattack_hits', 'oh_autoattacks', 'oh_autoattack_hits', 'main_gauche'):
            attacks_per_second[attack] *= ar_autoattack_multiplier

        total_restless_blades_benefit = (total_evis_per_second + attacks_per_second['rupture']) * cp_per_finisher * self.talents.restless_blades
        ksp_cooldown = 120 / total_restless_blades_benefit + self.settings.response_time

        attacks_per_second['sinister_strike'] = (total_evis_per_second + attacks_per_second['rupture']) * ss_per_finisher + ss_per_snd / (snd_duration - self.settings.response_time)
        attacks_per_second['revealing_strike'] = (total_evis_per_second + attacks_per_second['rupture']) * rvs_per_finisher
        attacks_per_second['main_gauche'] += (attacks_per_second['sinister_strike'] + attacks_per_second['revealing_strike'] + total_evis_per_second + attacks_per_second['rupture']) * main_gauche_proc_rate

        if self.talents.bandits_guile:
            time_at_level = 9 / ((attacks_per_second['sinister_strike'] + attacks_per_second['revealing_strike']) * self.talents.bandits_guile)
            cycle_duration = 3 * time_at_level + 15
            if not self.settings.cycle.ksp_immediately:
                avg_wait_till_full_stack = 1.5 * time_at_level / cycle_duration
                ksp_cooldown += avg_wait_till_full_stack
            avg_stacks = (3 * time_at_level + 45) / cycle_duration
            self.bandits_guile_multiplier = 1 + .1 * avg_stacks
        else:
            self.bandits_guile_multiplier = 1

        if self.talents.killing_spree:
            attacks_per_second['mh_killing_spree'] = 5 * self.strike_hit_chance / ksp_cooldown
            attacks_per_second['oh_killing_spree'] = 5 * self.off_hand_melee_hit_chance() / ksp_cooldown
            ksp_uptime = 2. / ksp_cooldown

            ksp_buff = .2 + .1 * self.glyphs.killing_spree
            if self.settings.cycle.ksp_immediately:
                self.ksp_multiplier = 1 + ksp_uptime * ksp_buff
            else:
                self.ksp_multiplier = 1 + ksp_uptime * ksp_buff * self.max_bandits_guile_buff / self.bandits_guile_multiplier
        else:
            attacks_per_second['mh_killing_spree'] = 0
            attacks_per_second['oh_killing_spree'] = 0
            self.ksp_multiplier = 1

        attacks_per_second['eviscerate'] = [finisher_chance * total_evis_per_second for finisher_chance in finisher_size_breakdown]

        attacks_per_second['rupture_ticks'] = [0, 0, 0, 0, 0, 0]
        for i in xrange(1, 6):
            ticks_per_rupture = 3 + i + 2 * self.glyphs.rupture
            attacks_per_second['rupture_ticks'][i] = ticks_per_rupture * attacks_per_second['rupture'] * finisher_size_breakdown[i]

        total_mh_hits = attacks_per_second['mh_autoattack_hits'] + attacks_per_second['sinister_strike'] + attacks_per_second['revealing_strike'] + attacks_per_second['mh_killing_spree'] + attacks_per_second['rupture'] + total_evis_per_second
        total_oh_hits = attacks_per_second['oh_autoattack_hits'] + attacks_per_second['main_gauche'] + attacks_per_second['oh_killing_spree']

        self.get_poison_counts(total_mh_hits, total_oh_hits, attacks_per_second)

        return attacks_per_second, crit_rates

    ###########################################################################
    # Subtlety DPS functions
    ###########################################################################

    def subtlety_dps_estimate(self):
        return sum(self.subtlety_dps_breakdown().values())

    def subtlety_dps_breakdown(self):
        if self.settings.cycle._cycle_type != 'subtlety':
            raise InputNotModeledException(_('You must specify a subtlety cycle to match your subtlety spec.'))

        if self.stats.mh.type != 'dagger':
            raise InputNotModeledException(_('Subtlety modeling currently requires a MH dagger'))

        if self.talents.serrated_blades != 2:
            raise InputNotModeledException(_('Subtlety modeling currently requires 2 points in Serrated Blades'))

        self.set_constants()

        self.base_hemo_cost = 28 + 7 / self.strike_hit_chance - 2 * self.talents.slaughter_from_the_shadows

        cost_reduction = (0, 7, 14, 20)[self.talents.slaughter_from_the_shadows]
        self.base_backstab_energy_cost = 48 + 12 / self.strike_hit_chance - cost_reduction
        self.base_ambush_energy_cost = 48 + 12 / self.strike_hit_chance - cost_reduction

        self.base_energy_regen = 10

        self.agi_multiplier *= 1.25

        damage_breakdown = self.compute_damage(self.subtlety_attack_counts_backstab)
        if self.talents.find_weakness:
            armor_value = self.target_armor()
            armor_reduction = (1 - .25 * self.talents.find_weakness)
            find_weakness_damage_boost = self.armor_mitigation_multiplier(armor_reduction * armor_value) / self.armor_mitigation_multiplier(armor_value)
            find_weakness_multiplier = 1 + (find_weakness_damage_boost - 1) * self.find_weakness_uptime
        else:
            find_weakness_multiplier = 1

        for key in damage_breakdown:
            if key in ('autoattack', 'backstab', 'eviscerate', 'hemorrhage'):
                damage_breakdown[key] *= find_weakness_multiplier
            if key == 'ambush':
                damage_breakdown[key] *= ((1.3 * self.ambush_shadowstep_rate) + (1-self.ambush_shadowstep_rate) * find_weakness_damage_boost)

        return damage_breakdown

    def subtlety_attack_counts_backstab(self, current_stats):
        attacks_per_second = {}

        base_melee_crit_rate = self.melee_crit_rate(agi=current_stats['agi'], crit=current_stats['crit'])
        base_spell_crit_rate = self.spell_crit_rate(crit=current_stats['crit'])

        haste_multiplier = self.stats.get_haste_multiplier_from_rating(current_stats['haste'])

        mastery_snd_speed = 1 + .4 * (1 + .02 * self.stats.get_mastery_from_rating(current_stats['mastery']))

        attack_speed_multiplier = self.base_speed_multiplier * haste_multiplier * mastery_snd_speed / 1.4

        attacks_per_second['mh_autoattacks'] = attack_speed_multiplier / self.stats.mh.speed
        attacks_per_second['oh_autoattacks'] = attack_speed_multiplier / self.stats.oh.speed

        attacks_per_second['mh_autoattack_hits'] = attacks_per_second['mh_autoattacks'] * self.dual_wield_mh_hit_chance()
        attacks_per_second['oh_autoattack_hits'] = attacks_per_second['oh_autoattacks'] * self.dual_wield_oh_hit_chance()

        backstab_crit_rate = base_melee_crit_rate + self.stats.gear_buffs.rogue_t11_2pc_crit_bonus() + .1 * self.talents.puncturing_wounds
        if backstab_crit_rate > 1:
            backstab_crit_rate = 1.

        ambush_crit_rate = base_melee_crit_rate + .2 * self.talents.improved_ambush
        if ambush_crit_rate > 1:
            ambush_crit_rate = 1

        crit_rates = {
            'mh_autoattacks': min(base_melee_crit_rate, self.dual_wield_mh_hit_chance() - self.GLANCE_RATE),
            'oh_autoattacks': min(base_melee_crit_rate, self.dual_wield_oh_hit_chance() - self.GLANCE_RATE),
            'eviscerate': base_melee_crit_rate + .1 * self.glyphs.eviscerate,
            'backstab': backstab_crit_rate,
            'ambush': ambush_crit_rate,
            'hemorrhage': base_melee_crit_rate,
            'rupture_ticks': base_melee_crit_rate,
            'instant_poison': base_spell_crit_rate,
            'deadly_poison': base_spell_crit_rate,
            'wound_poison': base_spell_crit_rate
        }

        if self.glyphs.backstab:
            backstab_energy_cost = self.base_backstab_energy_cost - 5 * backstab_crit_rate
        else:
            backstab_energy_cost = self.base_backstab_energy_cost

        if self.talents.honor_among_thieves:
            hat_triggers_per_second = self.settings.cycle.raid_crits_per_second * self.talents.honor_among_thieves / 3.
            hat_cp_gen = 1 / (5 - self.talents.honor_among_thieves + 1 / hat_triggers_per_second)
        else:
            hat_cp_gen = 0

        energy_regen = self.base_energy_regen * haste_multiplier + self.bonus_energy_regen
        energy_regen_with_recuperate = energy_regen + self.talents.energetic_recovery * 4. / 3

        base_backstab_time = backstab_energy_cost / energy_regen
        base_cp_per_backstab = 1 + base_backstab_time * hat_cp_gen

        backstab_time_during_recuperate = backstab_energy_cost / energy_regen_with_recuperate
        cp_per_backstab_during_recuperate = 1 + backstab_time_during_recuperate * hat_cp_gen

        eviscerate_net_energy_cost = self.base_eviscerate_energy_cost - 5 * self.relentless_strikes_energy_return_per_cp
        eviscerate_net_cp_cost = 5 - .2 * self.talents.ruthlessness - eviscerate_net_energy_cost * hat_cp_gen / energy_regen_with_recuperate

        backstabs_per_eviscerate = eviscerate_net_cp_cost / cp_per_backstab_during_recuperate
        total_eviscerate_cost = eviscerate_net_energy_cost + backstabs_per_eviscerate * backstab_energy_cost
        total_eviscerate_duration = total_eviscerate_cost / energy_regen_with_recuperate

        recuperate_duration = 30
        if self.settings.cycle.clip_recuperate:
            cycle_length = recuperate_duration - .5 * total_eviscerate_duration
            total_cycle_regen = cycle_length * energy_regen_with_recuperate
        else:
            recuperate_net_energy_cost = 30 - 5 * self.relentless_strikes_energy_return_per_cp
            recuperate_net_cp_cost = recuperate_net_energy_cost * hat_cp_gen / energy_regen
            backstabs_under_previous_recuperate = .5 * total_eviscerate_duration / backstab_energy_cost
            cp_gained_under_previous_recuperate = backstabs_under_previous_recuperate * cp_per_backstab_during_recuperate
            cp_needed_outside_recuperate = recuperate_net_cp_cost - cp_gained_under_previous_recuperate
            backstabs_after_recuperate = cp_needed_outside_recuperate / cp_per_backstab_during_recuperate
            energy_spent_after_recuperate = backstabs_after_recuperate * backstab_energy_cost + recuperate_net_energy_cost

            cycle_length = 30 + energy_spent_after_recuperate / energy_regen
            total_cycle_regen = 30 * energy_regen_with_recuperate + energy_spent_after_recuperate

        snd_build_time = total_eviscerate_duration / 2
        snd_build_energy_for_backstabs = 5 * self.relentless_strikes_energy_return_per_cp + energy_regen_with_recuperate * snd_build_time - 25
        backstabs_per_snd = snd_build_energy_for_backstabs / backstab_energy_cost
        hat_cp_per_snd = snd_build_time * hat_cp_gen

        snd_size = .2 * self.talents.ruthlessness + hat_cp_per_snd + backstabs_per_snd
        snd_duration = self.get_snd_length(snd_size)
        snd_per_second = 1./(snd_duration-self.settings.response_time)
        snd_net_energy_cost = 25 - snd_size * self.relentless_strikes_energy_return_per_cp
        snd_per_cycle = cycle_length / snd_duration

        vanish_cooldown = 180 - 30 * self.talents.elusiveness
        ambushes_from_vanish = 1. / (vanish_cooldown + self.settings.response_time) + self.talents.preparation / (300. + self.settings.response_time)
        if self.talents.find_weakness:
            self.find_weakness_uptime = 10 * ambushes_from_vanish
        else:
            self.find_weakness_uptime = 0

        cp_per_ambush = 2 + .5 * self.talents.initiative

        bonus_cp_per_cycle = (hat_cp_gen + ambushes_from_vanish * (cp_per_ambush + 2 * self.talents.premeditation)) * cycle_length
        cp_used_on_buffs = 5 + snd_size * snd_per_cycle - (1 + snd_per_cycle) * .2 * self.talents.ruthlessness
        bonus_eviscerates = (bonus_cp_per_cycle - cp_used_on_buffs) / (5 - .2 * self.talents.ruthlessness)
        energy_spent_on_bonus_finishers = 30 + 25 * snd_per_cycle + 35 * bonus_eviscerates - (5 + snd_size * snd_per_cycle + 5 * bonus_eviscerates) * self.relentless_strikes_energy_return_per_cp + cycle_length * ambushes_from_vanish * self.base_ambush_energy_cost
        energy_for_evis_spam = total_cycle_regen - energy_spent_on_bonus_finishers
        total_cost_of_extra_eviscerate = (5 - .2 * self.talents.ruthlessness) * backstab_energy_cost + self.base_eviscerate_energy_cost - 5 * self.relentless_strikes_energy_return_per_cp
        extra_eviscerates_per_cycle = energy_for_evis_spam / total_cost_of_extra_eviscerate

        attacks_per_second['backstab'] = (5 - .2 * self.talents.ruthlessness) * extra_eviscerates_per_cycle / cycle_length
        attacks_per_second['eviscerate'] = [0, 0, 0, 0, 0, (bonus_eviscerates + extra_eviscerates_per_cycle) / cycle_length]
        attacks_per_second['ambush'] = ambushes_from_vanish

        if self.talents.shadow_dance:
            shadow_dance_duration = 6 + 2 * self.glyphs.shadow_dance
            shadow_dance_frequency = 1. / (60 + self.settings.response_time)

            shadow_dance_bonus_cp_regen = shadow_dance_duration * hat_cp_gen + 2 * self.talents.premeditation
            shadow_dance_bonus_eviscerates = shadow_dance_bonus_cp_regen / (5 - .2 * self.talents.ruthlessness)
            shadow_dance_bonus_eviscerate_cost = shadow_dance_bonus_eviscerates * (35 - 5 * self.relentless_strikes_energy_return_per_cp)
            shadow_dance_available_energy = shadow_dance_duration * energy_regen_with_recuperate - shadow_dance_bonus_eviscerate_cost

            shadow_dance_eviscerate_cost = (5 - .2 * self.talents.ruthlessness) / cp_per_ambush * self.base_ambush_energy_cost + (35 - 5 * self.relentless_strikes_energy_return_per_cp)
            shadow_dance_eviscerates_for_period = shadow_dance_available_energy / shadow_dance_eviscerate_cost

            base_bonus_cp_regen = shadow_dance_duration * hat_cp_gen
            base_bonus_eviscerates = base_bonus_cp_regen / (5 - .2 * self.talents.ruthlessness)
            base_bonus_eviscerate_cost = base_bonus_eviscerates * (35 - 5 * self.relentless_strikes_energy_return_per_cp)
            base_available_energy = shadow_dance_duration * energy_regen_with_recuperate - base_bonus_eviscerate_cost

            base_eviscerates_for_period = base_available_energy / total_cost_of_extra_eviscerate

            shadow_dance_extra_eviscerates = shadow_dance_eviscerates_for_period + shadow_dance_bonus_eviscerates - base_eviscerates_for_period - base_bonus_eviscerates
            shadow_dance_extra_ambushes = (5 - .2 * self.talents.ruthlessness) / cp_per_ambush * shadow_dance_eviscerates_for_period
            shadow_dance_replaced_backstabs = (5 - .2 * self.talents.ruthlessness) * base_eviscerates_for_period

            self.ambush_shadowstep_rate = (shadow_dance_frequency + ambushes_from_vanish) / (shadow_dance_extra_ambushes + ambushes_from_vanish)

            attacks_per_second['backstab'] -= shadow_dance_replaced_backstabs * shadow_dance_frequency
            attacks_per_second['ambush'] += shadow_dance_extra_ambushes * shadow_dance_frequency
            attacks_per_second['eviscerate'][5] += shadow_dance_extra_eviscerates * shadow_dance_frequency

            self.find_weakness_uptime += (10 + shadow_dance_duration - self.settings.response_time) * shadow_dance_frequency
        else:
            self.ambush_shadowstep_rate = 1

        attacks_per_second['rupture_ticks'] = (0, 0, 0, 0, 0, .5)

        total_mh_hits = attacks_per_second['mh_autoattack_hits'] + attacks_per_second['backstab'] + sum(attacks_per_second['eviscerate']) + attacks_per_second['ambush']
        total_oh_hits = attacks_per_second['oh_autoattack_hits']

        self.get_poison_counts(total_mh_hits, total_oh_hits, attacks_per_second)

        return attacks_per_second, crit_rates
