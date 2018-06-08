import re
from enum import Enum

class ModifierType(Enum):
    ResistCold = 1
    ResistFire = 2
    ResistLightning = 3
    Strength = 4
    Dexterity = 5
    Intelligence = 6
    MovementSpeed = 7
    FlatArmor = 8
    FlatEnergyShield = 9
    FlatEvasion = 10
    FlatLife = 11
    FlatMana = 12
    StunRecovery = 13
    TotemPlaceSpeed = 14
    TotemDamage = 15
    ResistChaos = 16
    Rarity = 17
    Quantity = 18
    EnergyShieldIncrease = 19
    SkillDuration = 20
    EnduranceCharges = 21
    GemLevelCurses = 22
    GemLevelDuration = 23
    GemLevelProjectile = 24
    GemLevelAura = 25
    GemLevelTrap = 26
    GemLevel = 27
    GemLevelAoE = 28
    GemLevelWarCry = 29
    CooldownRecovery = 30


modifier_tier_data = {
    ModifierType.ResistFire: [0, 12, 18, 24, 30, 36, 42, 46],
    ModifierType.ResistCold: [0, 12, 18, 24, 30, 36, 42, 46],
    ModifierType.ResistLightning: [0, 12, 18, 24, 30, 36, 42, 46],
    ModifierType.ResistChaos: [0, 11, 16, 21, 26, 31],
    ModifierType.MovementSpeed: [0, 15, 20, 25, 30, 35],
    ModifierType.FlatLife: [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120],
    ModifierType.FlatMana: [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120]
}


score_data = {
    'boots': {
        ModifierType.MovementSpeed: 10,
        ModifierType.FlatLife: 5,
        ModifierType.ResistFire: 2,
        ModifierType.ResistCold: 2,
        ModifierType.ResistLightning: 2,
        ModifierType.Strength: 0.2,
        ModifierType.Dexterity: 0.2,
        ModifierType.Intelligence: 0.2
    }
}


grade_enable_boots = False


class DataCustomizer:

    def GetCustomArmorValue(self, item_name, context):
        return self._grade_armor(context)

    def GetCustomWeaponValue(self, item_name, context):
        return False

    def GetCustomAccessoryValue(self, item_name, context):
        return False

    def GetCustomJewelValue(self, item_name, context):
        return False

    def _grade_armor(self, context):
        corrupted = context['corrupted']
        if corrupted is True:
            return

        grade_base = context['sub_type']

        implicits = context['raw_data'].get('implicitMods')
        if implicits is None:
            implicits = []

        explicits = context['raw_data'].get('explicitMods')
        if explicits is None:
            explicits = []

        # print("Grading Type " + grade_base + " with " + str(len(implicits)) + " Implicit and " + str(len(explicits)) + " Mod(s)")

        if grade_base == "boots":
            return self._grade_armor_boots(context, implicits, explicits)

        # print("Type not implemented for custom grade: " + grade_base)
        return False


    def _grade_armor_boots(self, context, implicits, explicits):
        if not grade_enable_boots:
            return False

        parsed_modifiers = []
        for implicit in implicits:
            infos = self._get_modifier_info(implicit)
            if infos is None:
                #print("Unhandled Implicit Modifier: " + implicit)
                continue

            for info in infos:
                info['is_implicit'] = True
                parsed_modifiers.append(info)

        for explicit in explicits:
            infos = self._get_modifier_info(explicit)
            if infos is None:
                #print("Unhandled Explicit Modifier: " + explicit)
                continue

            for info in infos:
                info['is_implicit'] = False
                parsed_modifiers.append(info)

        if len(parsed_modifiers) == 0:
            return False

        for modifier in parsed_modifiers:
            self._update_modifier_tier(modifier)

        # now check for some basic things that have to be present:

        #  - Has to have movement speed
        if not self._has_modifier_type(parsed_modifiers, ModifierType.MovementSpeed):
            return False

        #  - Has to have Life/ES
        if not self._has_modifier_type(parsed_modifiers, ModifierType.FlatLife) \
            or not self._has_modifier_type(parsed_modifiers, ModifierType.FlatEnergyShield):
            return False

        #  - Has to have at least 2 Resists
        resist_count = 0
        if self._has_modifier_type(parsed_modifiers, ModifierType.ResistLightning):
            resist_count += 1
        if self._has_modifier_type(parsed_modifiers, ModifierType.ResistCold):
            resist_count += 1
        if self._has_modifier_type(parsed_modifiers, ModifierType.ResistFire):
            resist_count += 1

        if resist_count < 2:
            return False

        stat_score = self._calculate_score(context, parsed_modifiers)
        if resist_count == 3:
            # multiply the score for triple res boots
            stat_score = stat_score * 1.2

        if stat_score < 800:
            return False

        context['grade_score'] = stat_score
        context['grade_mods'] = parsed_modifiers
        return True

    def _has_modifier_type(self, modifiers, target_type):
        for modifier in modifiers:
            if modifier['type'] == target_type:
                return True;

        return False

    def _calculate_score(self, context, modifiers):
        if context['sub_type'] not in score_data:
            return 0

        score = 0
        for modifier in modifiers:
            if modifier['tier'] is None or modifier['type'] not in score_data[context['sub_type']]:
                continue

            base_score_value = score_data[context['sub_type']][modifier['type']]
            amount_score_value = base_score_value * modifier['value']
            score += amount_score_value

        return score

    def _get_modifier_info(self, modifier):
        match = re.match("(\+)?([0-9]+)(%)? (to|increased) (.*)", modifier)
        if match:
            return self._get_modifier_info_default_gain_match(match)

        return None

    def _get_modifier_info_default_gain_match(self, match):
        base_result = {
            'raw': match.group(0),
            'value': float(match.group(2)),
            'percentage': match.group(3),
            'modifier_key': match.group(4),
            'target': match.group(5).strip()
        }

        target = base_result['target']
        modifier_types = []

        if target == "Fire Resistance":
            modifier_types.append(ModifierType.ResistFire)
        elif target == "Cold Resistance":
            modifier_types.append(ModifierType.ResistCold)
        elif target == "Lightning Resistance":
            modifier_types.append(ModifierType.ResistLightning)
        elif target == "Fire and Lightning Resistances":
            modifier_types.append(ModifierType.ResistFire)
            modifier_types.append(ModifierType.ResistLightning)
        elif target == "Fire and Cold Resistances":
            modifier_types.append(ModifierType.ResistFire)
            modifier_types.append(ModifierType.ResistCold)
        elif target == "Cold and Lightning Resistances":
            modifier_types.append(ModifierType.ResistLightning)
            modifier_types.append(ModifierType.ResistCold)
        elif target == "Chaos Resistance":
            modifier_types.append(ModifierType.ResistChaos)
        elif target == "Strength":
            modifier_types.append(ModifierType.Strength)
        elif target == "Dexterity":
            modifier_types.append(ModifierType.Dexterity)
        elif target == "Intelligence":
            modifier_types.append(ModifierType.Intelligence)
        elif target == "Movement Speed":
            modifier_types.append(ModifierType.MovementSpeed)
        elif target == "Armour":
            modifier_types.append(ModifierType.FlatArmor)
        elif target == "maximum Energy Shield":
            modifier_types.append(ModifierType.FlatEnergyShield)
        elif target == "Evasion Rating":
            modifier_types.append(ModifierType.FlatEvasion)
        elif target == "Armour and Evasion":
            modifier_types.append(ModifierType.FlatArmor)
            modifier_types.append(ModifierType.FlatEvasion)
        elif target == "Armour and Energy Shield":
            modifier_types.append(ModifierType.FlatArmor)
            modifier_types.append(ModifierType.FlatEnergyShield)
        elif target == "Evasion and Energy Shield":
            modifier_types.append(ModifierType.FlatEvasion)
            modifier_types.append(ModifierType.FlatEnergyShield)
        elif target == "maximum Life":
            modifier_types.append(ModifierType.FlatLife)
        elif target == "maximum Mana":
            modifier_types.append(ModifierType.FlatMana)
        elif target == "Stun and Block Recovery":
            modifier_types.append(ModifierType.StunRecovery)
        elif target == "Totem Placement speed":
            modifier_types.append(ModifierType.TotemPlaceSpeed)
        elif target == "Totem Damage":
            modifier_types.append(ModifierType.TotemDamage)
        elif target == "Rarity of Items found":
            modifier_types.append(ModifierType.Rarity)
        elif target == "Energy Shield" and base_result['modifier_key'] == "increased":
            modifier_types.append(ModifierType.EnergyShieldIncrease)
        elif target == "Skill Effect Duration":
            modifier_types.append(ModifierType.SkillDuration)
        elif target == "Maximum Endurance Charges":
            modifier_types.append(ModifierType.EnduranceCharges)
        elif target == "Level of Socketed Curse Gems":
            modifier_types.append(ModifierType.GemLevelCurses)
        elif target == "Level of Socketed Projectile Gems":
            modifier_types.append(ModifierType.GemLevelProjectile)
        elif target == "Level of Socketed Duration Gems":
            modifier_types.append(ModifierType.GemLevelDuration)
        elif target == "Level of Socketed Aura Gems":
            modifier_types.append(ModifierType.GemLevelAura)
        elif target == "Level of Socketed Trap or Mine Gems":
            modifier_types.append(ModifierType.GemLevelTrap)
        elif target == "Level of Socketed Gems":
            modifier_types.append(ModifierType.GemLevel)
        elif target == "Level of Socketed AoE Gems":
            modifier_types.append(ModifierType.GemLevelAoE)
        elif target == "Level of Socketed Warcry Gems":
            modifier_types.append(ModifierType.GemLevelWarCry)
        elif target == "Cooldown Recovery Speed":
            modifier_types.append(ModifierType.CooldownRecovery)
        elif target == "Movement Speed if you haven't been Hit Recently"\
                or target == "Global Evasion Rating while moving":

            # Don't care about these
            return None
        else:
            print("Unhandled Modifier Target: " + target)
            print(base_result)
            return None

        results = []
        for modifier_type in modifier_types:
            result = base_result
            result['type'] = modifier_type
            results.append(result)

        return results

    def _update_modifier_tier(self, modifier):
        modifier['tier'] = None

        if modifier['type'] in modifier_tier_data:
            tier_data = modifier_tier_data[modifier['type']]
            for i in range(0, len(tier_data)):
                if tier_data[i] > modifier['value']:
                    modifier['tier'] = i
                    return

            # consider it the highest tier
            modifier['tier'] = len(tier_data)
            return

        # print("Missing Tier Info for: " + modifier['target'])


