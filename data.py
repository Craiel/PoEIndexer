import time
import requests
import os
import json
import re

from pathlib import Path

data_key_armor = "Armor"
data_key_weapons = "Weapons"
data_key_accessory = "Accessory"
data_key_fragments = "Fragments"
data_key_essence = "Essence"
data_key_prophecy = "Prophecy"
data_key_skill_gem = "SkillGem"
data_key_cards = "DivinationCards"
data_key_flasks = "Flasks"
data_key_jewels = "Jewels"
data_key_unique_maps = "UniqueMaps"
data_key_maps = "Maps"
data_key_currency = "Currency"

class IndexerData:
    _ninja_api = "http://poe.ninja/api/Data/"
    _ninja_item_overview_func = "itemoverview"
    _ninja_currency_overview_func = "currencyoverview"
    league = "Standard"
    cache_directory = "cache_data"
    index = {}
    customizer = None

    # some data got mixed up at some point and non-unique items made it into the result of unique lists, so we hard-ignore those for now
    ignored_data_ids = []

    def __init__(self, customizer):

        self.customizer = customizer
        if not os.path.exists(self.cache_directory):
            os.makedirs(self.cache_directory)

        pass

    def set_league(self, league_value):
        print("Setting League to " + league_value)
        self.league = league_value

    def reload(self):
        self.index = {}

        self._reload_armor()
        self._reload_weapons()
        self._reload_accessories()
        self._reload_fragments()
        self._reload_essences()
        self._reload_skill_gems()
        self._reload_prophecies()
        self._reload_divination_cards()
        self._reload_flasks()
        self._reload_jewels()
        self._reload_maps()
        self._reload_currency()
        pass

    @staticmethod
    def _update_link_count(context):
        sockets = context['raw_data'].get('sockets')
        if sockets is None:
            context['links'] = 0
            return

        count = 0
        for socket in sockets:
            grp = socket.get('group')
            if grp == 0:
                count += 1

        context['links'] = count

    @staticmethod
    def _get_item_property(context, property_name):
        properties = context['raw_data'].get('properties')
        if properties is None:
            return None

        for prop in properties:
            if prop['name'] == property_name:
                return prop['values']

        return None

    def _update_item_map_tier(self, context):
        map_tier_values = self._get_item_property(context, 'Map Tier')
        if map_tier_values is not None:
            context['map_tier'] = int(map_tier_values[0][0])

    def _update_gem_properties(self, context):
        level_values = self._get_item_property(context, 'Level')
        if level_values is None:
            context['gem_level'] = 1
        else:
            context['gem_level'] = int(level_values[0][0].replace(' (Max)', ''))

        quality_values = self._get_item_property(context, 'Quality')
        if quality_values is None:
            context['gem_quality'] = 0
        else:
            context['gem_quality'] = int(quality_values[0][0].replace('+', '').replace('%', ''))

    def _update_item_variant(self, context):
        explicit = context['raw_data'].get('explicitMods')
        if explicit is None or len(explicit) == 0:
            context['variant'] = None
            return

        if context['name'] == "Lightpoacher" \
                or context['name'] == "Bubonic Trail"\
                or context['name'] == "Tombfist"\
                or context['name'] == "Shroud of the Lightless":
            if explicit[0] == 'Has 2 Abyssal Sockets':
                context['variant'] = '2 Jewels'
                return

            if explicit[0] == 'Has 1 Abyssal Socket':
                context['variant'] = '1 Jewel'
                return

        if context['name'] == "Volkuur's Guidance":
            if ' Lightning Damage to Spells and Attacks' in explicit[0]:
                context['variant'] = 'Lightning'
                return

            if ' Fire Damage to Spells and Attacks' in explicit[0]:
                context['variant'] = 'Fire'
                return

            if ' Cold Damage to Spells and Attacks' in explicit[0]:
                context['variant'] = 'Cold'
                return

        if context['name'] == "Impresence"\
                or context['name'] == "Doryani's Invitation":
            if ' Damage over Time' in explicit[0]:
                context['variant'] = 'Chaos'
                return

            if ' Lightning Damage' in explicit[0]:
                context['variant'] = 'Lightning'
                return

            if ' Fire Damage' in explicit[0]:
                context['variant'] = 'Fire'
                return

            if ' Cold Damage' in explicit[0]:
                context['variant'] = 'Cold'
                return

            if ' Physical Damage' in explicit[0]:
                context['variant'] = 'Physical'
                return

        if context['name'] == "Yriel's Fostering":
            if ' Bestial Rhoa Skill' in explicit[0]:
                context['variant'] = 'Maim'
                return

            if ' Bestial Snake Skill' in explicit[0]:
                context['variant'] = 'Poison'
                return

            if ' Bestial Ursa Skill' in explicit[0]:
                context['variant'] = 'Bleeding'
                return

        if context['name'] == "Combat Focus":
            if 'Strength and Intelligence in Radius' in explicit[1]:
                context['variant'] = 'StrInt'
                return

            if 'Dexterity and Strength in Radius' in explicit[1]:
                context['variant'] = 'DexStr'
                return

            if 'Intelligence and Dexterity in Radius' in explicit[1]:
                context['variant'] = 'IntDex'
                return

        if context['name'] == "The Beachhead":
            self._update_item_map_tier(context)
            context['variant'] = "T" + str(context['map_tier'])
            return

        context['variant'] = None

    def get_currency_conversion(self, currency_name):
        for currency in self.index[data_key_currency]:
            if currency == currency_name:
                entry = self.index[data_key_currency][currency][0]
                return entry.get('chaosEquivalent')

        return None

    def update_value(self, context):
        item_name = context['name']
        category = context['category']

        if 'weapons' in category:
            if self._update_weapon_value(item_name, context):
                return

            # print("Unhandled Weapon: " + item_name)

        elif 'armour' in category:
            if self._update_armor_value(item_name, context):
                return

            # print("Unhandled Armor: " + item_name)

        elif 'accessories' in category:
            if self._update_accessory_value(item_name, context):
                return

            # print("Unhandled Accessory: " + item_name)

        elif 'maps' in category:
            if self._update_map_value(item_name, context):
                return

            if self._update_fragment_value(item_name, context):
                return

            print("Unhandled Map: " + item_name + " -> " + context['typeLine'])

        elif 'jewels' in category:
            if self._update_jewel_value(item_name, context):
                return

            # print("Unhandled Jewel: " + item_name)

        elif 'cards' in category:
            if self._update_card_value(context):
                return

            print("Unhandled Card: " + context['typeLine'])

        elif 'flasks' in category:
            if self._update_flask_value(item_name, context):
                return

            # print("Unhandled Flask: " + item_name)

        elif 'gems' in category:
            if context['typeLine'] == 'Vaal Breach':
                # Invalid gems
                return

            if self._update_gem_value(context):
                return

            print("Unhandled Gem: " + context['typeLine'])

        elif 'currency' in category:
            if 'Chaos Orb' in item_name or \
                    "Cartographer's Seal" in item_name or \
                    'Unshaping Orb' in item_name or \
                    'Albino Rhoa Feather' in item_name or \
                    'Stacked Deck' in item_name or \
                    'Scroll of Wisdom' in item_name or \
                    'Harbinger\'s Shard' in item_name or \
                    'Alchemy Shard' in item_name or \
                    'Alteration Shard' in item_name or \
                    'Scroll Fragment' in item_name or \
                    'Horizon Shard' in item_name or \
                    'Engineer\'s Shard' in item_name or \
                    'Binding Shard' in item_name or \
                    'Ancient Shard' in item_name or \
                    'Chaos Shard' in item_name or \
                    'Piece of' in item_name or \
                    'Vial of' in item_name or \
                    'Fossil' in item_name or \
                    'Resonator' in item_name:
                return

            if 'Stacked Deck' in item_name:
                if self._update_card_value(context):
                    return

            if 'Essence' in item_name or 'Remnant' in item_name:
                if self._update_essence_value(item_name, context):
                    return

            if self._update_currency_value(item_name, context):
                return

            if self._update_fragment_value(item_name, context):
                return

            if self._update_prophecy_value(item_name, context):
                return

            if ' Net' in item_name:
                # ignore nets
                return

            print("Unhandled Currency: " + item_name)

        else:
            print("Unhandled Item Category: " + category)

        return None

    def _update_weapon_value(self, item_name, context):
        for weapon in self.index[data_key_weapons]:
            if weapon == item_name:
                self._update_value_for_frame_and_link_match(context, self.index[data_key_weapons][weapon])
                return True

        return self.customizer.GetCustomWeaponValue(item_name, context)

    def _update_armor_value(self, item_name, context):
        for armor in self.index[data_key_armor]:
            if armor == item_name:
                self._update_value_for_frame_and_link_match(context, self.index[data_key_armor][armor])
                return True

        return self.customizer.GetCustomArmorValue(item_name, context)

    def _update_accessory_value(self, item_name, context):
        for accessory in self.index[data_key_accessory]:
            if accessory == item_name:
                self._update_value_generic_non_corrupt(context, self.index[data_key_accessory][accessory])
                return True

        return self.customizer.GetCustomAccessoryValue(item_name, context)

    def _update_map_value(self, item_name, context):
        candidates = []
        for map in self.index[data_key_unique_maps]:
            map_name = item_name.replace("Superior ", "")
            if map == map_name:
                self._update_value_map(context, self.index[data_key_unique_maps][map])
                return True

        if len(candidates) > 0:
            print(candidates)

        type_line = context['typeLine']
        for map in self.index[data_key_maps]:
            map_name = type_line.replace("Superior ", "")
            if map == map_name:
                self._update_value_map(context, self.index[data_key_maps][map])
                return True

            if map in item_name:
                candidates.append(map)

        # lets see of any map matched our item (i.e ### <> Map of ###)
        if len(candidates) == 1:
            self._update_value_generic(context, self.index[data_key_maps][candidates[0]])
            return True
        elif len(candidates) > 1:
            # More than one map matched, (i.e Port Map, Shaped Port Map)
            # pick the longer one (better match)
            best_match = None
            best_match_length = 0
            for match in candidates:
                if best_match is None or len(match) > best_match_length:
                    best_match = match
                    best_match_length = len(match)

            self._update_value_generic(context, self.index[data_key_maps][best_match])
            return True

        return False

    def _update_fragment_value(self, item_name, context):
        for fragment in self.index[data_key_fragments]:
            if fragment == item_name:
                self._update_value_generic(context, self.index[data_key_fragments][fragment])
                return True

        return False

    def _update_jewel_value(self, item_name, context):
        for jewel in self.index[data_key_jewels]:
            if jewel == item_name:
                self._update_value_generic(context, self.index[data_key_jewels][jewel])
                return True

        return self.customizer.GetCustomJewelValue(item_name, context)

    def _update_card_value(self, context):
        type_line = context['typeLine']
        for card in self.index[data_key_cards]:
            if card == type_line:
                self._update_value_generic(context, self.index[data_key_cards][card])
                return True

        return False

    def _update_flask_value(self, item_name, context):
        for flask in self.index[data_key_flasks]:
            if flask == item_name:
                self._update_value_generic(context, self.index[data_key_flasks][flask])
                return True

        return False

    def _update_gem_value(self, context):
        type_line = context['typeLine']
        for gem in self.index[data_key_skill_gem]:
            if gem == type_line:
                self._update_value_gem(context, self.index[data_key_skill_gem][gem])
                return True

        return False

    def _update_essence_value(self, item_name, context):
        for essence in self.index[data_key_essence]:
            if essence == item_name:
                self._update_value_generic(context, self.index[data_key_essence][essence])
                return True

        return False

    def _update_currency_value(self, item_name, context):
        for currency in self.index[data_key_currency]:
            if currency == item_name:
                self._update_value_generic(context, self.index[data_key_currency][currency])
                return True

        return False

    def _update_prophecy_value(self, item_name, context):
        for prophecy in self.index[data_key_prophecy]:
            if prophecy == item_name:
                self._update_value_generic(context, self.index[data_key_prophecy][prophecy])
                return True

        return False

    def _entry_matches_candidate(self, context, candidate, check_links=False):
        item_variant = context['variant']
        item_class = context['type']
        item_base_type = context['typeLine']
        if check_links:
            item_links = context['links']

        entry_class = candidate.get('itemClass')
        entry_links = candidate.get('links')
        entry_variant = candidate.get('variant')
        entry_base_type = candidate.get('baseType')

        if item_variant is not None and entry_variant is None:
            # The entry has a variant but data is not set, so we fake a context and perform the same update_variant call
            fake_context = {'raw_data': {'explicitMods': []},
                            'name': context['name']}

            for mod in candidate['explicitModifiers']:
                fake_context['raw_data']['explicitMods'].append(mod['text'])

            self._update_item_variant(fake_context)
            entry_variant = fake_context['variant']

        if entry_variant is not None:
            if entry_variant != item_variant and entry_variant != "Atlas2":
                if item_variant is None:
                    print("Variant Mismatch: " + entry_variant)
                    print(context['raw_data'])
                return False

        if check_links:
            if item_links >= 5:
                if entry_links != item_links:
                    # print("Item Link Requirement mimatch: " + str(item_links))
                    return False
            else:
                if entry_links >= 5:
                    # print("Candidate Link Requirement mismatch " + str(entry_links))
                    return False

        if entry_class != item_class:
            # print("Class Requirement Mismatch: " + str(entry_class) + " != " + str(item_class) + " || " + str(entry_links) + " != " + str(item_links))
            return False

        if entry_base_type is not None and item_base_type is not None:
            if entry_base_type not in item_base_type:
                #print("Base Type Requirement Mismatch: " + entry_base_type + " != " + item_base_type)
                return False

        return True

    def _update_value_for_frame_and_link_match(self, context, data_entry):
        corrupted = context['corrupted']
        if corrupted is True:
            # For now we will ignore corrupted weapons and armor, too much variation in price
            return

        self._update_link_count(context)
        self._update_item_variant(context)

        results = 0
        result = 0

        context['default_value'] = 0
        for candidate in data_entry:
            entry_links = candidate.get('links')
            if entry_links < 5:
                context['default_value'] = candidate.get('internal_value')
            if context['default_value'] is None:
                context['default_value'] = 0
            break

        matches = []
        for candidate in data_entry:
            if not self._entry_matches_candidate(context, candidate, True):
                continue

            value = candidate.get('internal_value')

            results += 1
            result = value

            # for debug
            matches.append(candidate)

        if results == 0:
            # No results
            return 0

        if results != 1:
            # Inconclusive, wont take the risk
            print("Inconclusive (1): " + str(results))
            print(matches)
            return 0

        context['value'] = result
        context['value_source'] = matches[0]

    def _update_value_generic_non_corrupt(self, context, data_entry):
        corrupted = context['corrupted']
        if corrupted is True:
            # For now we will ignore corrupted weapons and armor, too much variation in price
            return

        self._update_item_variant(context)

        matches = []
        results = 0
        result = 0
        for candidate in data_entry:
            if not self._entry_matches_candidate(context, candidate):
                continue

            value = candidate.get('internal_value')

            results += 1
            result = value

            matches.append(candidate)

        if results == 0:
            return 0

        if results != 1:
            # Inconclusive, wont take the risk
            print("Inconclusive (2): " + str(results))
            print(matches)
            return 0

        context['value'] = result
        context['value_source'] = matches[0]

    def _update_value_generic(self, context, data_entry):
        self._update_item_variant(context)

        matches = []
        results = 0
        result = 0
        for candidate in data_entry:
            if not self._entry_matches_candidate(context, candidate):
                continue

            value = candidate.get('internal_value')

            results += 1
            result = value
            matches.append(candidate)

        if results == 0:
            return 0

        if results != 1:
            # Inconclusive, wont take the risk
            print("Inconclusive (3): " + str(results))
            print(matches)
            return 0

        context['value'] = result
        context['value_source'] = matches[0]

    def _update_value_map(self, context, data_entry):
        if len(data_entry):
            return 0

        matches = []
        results = 0
        result = 0

        self._update_item_map_tier(context)
        target_tier = context['map_tier']

        for candidate in data_entry:
            candidate_tier = candidate.get('mapTier')
            if target_tier != candidate_tier:
                print("Tier Mismatch: " + str(target_tier) + " != " + str(candidate_tier))
                continue

            value = candidate.get('internal_value')

            results += 1
            result = value
            matches.append(candidate)

        if results == 0:
            print("No Match for map: ")
            print(context)
            return 0

        if results != 1:
            # Inconclusive, wont take the risk
            print("Inconclusive (4): " + str(results))
            print(matches)
            return 0

        context['value'] = result
        context['value_source'] = matches[0]

    def _update_value_gem(self, context, data_entry):
        self._update_gem_properties(context)

        level = context['gem_level']
        quality = context['gem_quality']

        corrupted = context['corrupted']

        is_special_support_gem = False
        if context['name'] == 'Empower Support' \
                or context['name'] == 'Enlighten Support' \
                or context['name'] == 'Enhance Support':
            is_special_support_gem = True

        if not is_special_support_gem and corrupted and quality < 20:
            # ignore corrupt gems unless the quality is 20% +
            return

        matches = []
        results = 0
        result = 0
        for candidate in data_entry:
            entry_variant = candidate.get('variant')
            if entry_variant is not None:

                match = re.match("([0-9]+)\/?([0-9]*)(c)?", entry_variant)
                if match is None:
                    print("Unknown gem entry variant: " + entry_variant)
                    continue

                target_level = int(match.group(1))
                target_quality = 0
                if match.group(2) != '':
                    target_quality = int(match.group(2))
                target_corrupt = match.group(3) == 'c'

                if target_corrupt != corrupted:
                    continue

                if is_special_support_gem:

                    # special case
                    if target_level != level:
                        continue
                else:
                    if target_level >= 20 and target_level != level:
                        continue

                    if target_quality >= 20 and target_quality != quality:
                        continue

                    if quality >= 20 and target_quality < 20:
                        continue
                    if level >= 20 and target_level < 20:
                        continue

            value = candidate.get('internal_value')

            results += 1
            result = value
            matches.append(candidate)

        if results == 0:
            return 0

        if results != 1:
            # Inconclusive, wont take the risk
            print("Inconclusive (5): " + str(results))
            print(matches)
            return 0

        context['value'] = result
        context['value_source'] = matches[0]

    def _get_data_cache_name(self, path):
        return time.strftime("%Y-%m-%d-%H") + "_" + self.league + "_" + path

    def _get_ninja_link(self, overviewFunc, overviewType):
        return self._ninja_api + overviewFunc + "?league=" + self.league + "&type=" + overviewType + "&date=" + time.strftime("%Y-%m-%d")

    def _index_data(self, data_key, data, entry_key):
        self.index[data_key] = {}

        entry_count = 0
        for entry in data:
            entry_id = entry.get('id')
            if entry_id is not None:
                if entry_id in self.ignored_data_ids:
                    print("Ignoring data entry id " + str(entry_id))
                    continue

            key = entry.get(entry_key)

            value = entry.get('chaosValue')
            if value is None:
                value = entry.get('chaosEquivalent')

            if value is None:
                print("Data Entry has no Value: " + data_key + " -- " + key)
                continue

            entry['internal_value'] = value

            if key is None or key == "":
                print("Invalid Entry in Data for " + data_key)
                continue

            if key not in self.index[data_key]:
                self.index[data_key][key] = []

            self.index[data_key][key].append(entry)
            entry_count += 1

        print(" -> Indexed " + str(entry_count) + " Entries")

    def _load_data(self, link, cache_name):
        print("Loading " + cache_name)
        cache_file = self.cache_directory + "/" + cache_name
        my_file = Path(cache_file)
        if my_file.is_file():
            print(" -> From Cache")
            with open(cache_file) as json_data:
                return json.load(json_data)
        else:
            print(" -> Live")
            print(link)
            result = requests.get(link)
            data = result.json().get('lines')

            print(" -> Storing Cache")
            with open(cache_file, 'w') as outfile:
                json.dump(data, outfile)

            return data

    # itemoverview
    def _reload_armor(self):
        link = self._get_ninja_link(self._ninja_item_overview_func, "UniqueArmour")
        data = self._load_data(link, self._get_data_cache_name(data_key_armor))
        self._index_data(data_key_armor, data, "name")

    def _reload_weapons(self):
        link = self._get_ninja_link(self._ninja_item_overview_func, "UniqueWeapon")
        data = self._load_data(link, self._get_data_cache_name(data_key_weapons))
        self._index_data(data_key_weapons, data, "name")

    def _reload_accessories(self):
        link = self._get_ninja_link(self._ninja_item_overview_func, "UniqueAccessory")
        data = self._load_data(link, self._get_data_cache_name(data_key_accessory))
        self._index_data(data_key_accessory, data, "name")

    def _reload_fragments(self):
        link = self._get_ninja_link(self._ninja_currency_overview_func, "Fragment")
        data = self._load_data(link, self._get_data_cache_name(data_key_fragments))
        self._index_data(data_key_fragments, data, "currencyTypeName")

    def _reload_prophecies(self):
        link = self._get_ninja_link(self._ninja_item_overview_func, "Prophecy")
        data = self._load_data(link, self._get_data_cache_name(data_key_prophecy))
        self._index_data(data_key_prophecy, data, "name")

    def _reload_skill_gems(self):
        link = self._get_ninja_link(self._ninja_item_overview_func, "SkillGem")
        data = self._load_data(link, self._get_data_cache_name(data_key_skill_gem))
        self._index_data(data_key_skill_gem, data, "name")

    def _reload_essences(self):
        link = self._get_ninja_link(self._ninja_item_overview_func, "Essence")
        data = self._load_data(link, self._get_data_cache_name(data_key_essence))
        self._index_data(data_key_essence, data, "name")

    def _reload_divination_cards(self):
        link = self._get_ninja_link(self._ninja_item_overview_func, "DivinationCard")
        data = self._load_data(link, self._get_data_cache_name(data_key_cards))
        self._index_data(data_key_cards, data, "name")

    def _reload_flasks(self):
        link = self._get_ninja_link(self._ninja_item_overview_func, "UniqueFlask")
        data = self._load_data(link, self._get_data_cache_name(data_key_flasks))
        self._index_data(data_key_flasks, data, "name")

    def _reload_jewels(self):
        link = self._get_ninja_link(self._ninja_item_overview_func, "UniqueJewel")
        data = self._load_data(link, self._get_data_cache_name(data_key_jewels))
        self._index_data(data_key_jewels, data, "name")

    def _reload_maps(self):
        link = self._get_ninja_link(self._ninja_item_overview_func, "UniqueMap")
        data = self._load_data(link, self._get_data_cache_name(data_key_unique_maps))
        self._index_data(data_key_unique_maps, data, "name")
        link = self._get_ninja_link(self._ninja_item_overview_func, "Map")
        data = self._load_data(link, self._get_data_cache_name(data_key_maps))
        self._index_data(data_key_maps, data, "name")

    def _reload_currency(self):
        link = self._get_ninja_link(self._ninja_currency_overview_func, "Currency")
        data = self._load_data(link, self._get_data_cache_name(data_key_currency))
        self._index_data(data_key_currency, data, "currencyTypeName")
