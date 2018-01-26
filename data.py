import time
import requests
import os
import json

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
    _ninja_cdn = "http://cdn.poe.ninja/api/Data/"
    _ninja_api = "http://api.poe.ninja/api/Data/"
    league = "Standard"
    cache_directory = "cache_data"
    index = {}

    # some data got mixed up at some point and non-unique items made it into the result of unique lists, so we hard-ignore those for now
    ignored_data_ids = [4809, 4810, 4813, 4814, 4815, 4816, 4817, 4818]

    def __init__(self):

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
            for weapon in self.index[data_key_weapons]:
                if weapon == item_name:
                    self._update_value_for_frame_and_link_match(context, self.index[data_key_weapons][weapon])
                    return

        elif 'armour' in category:
            for armor in self.index[data_key_armor]:
                if armor == item_name:
                    self._update_value_for_frame_and_link_match(context, self.index[data_key_armor][armor])
                    return

        elif 'accessories' in category:
            for accessory in self.index[data_key_accessory]:
                if accessory == item_name:
                    self._update_value_generic_non_corrupt(context, self.index[data_key_accessory][accessory])
                    return

        elif 'maps' in category:
            for map in self.index[data_key_unique_maps]:
                if map == item_name:
                    self._update_value_generic(context, self.index[data_key_unique_maps][map])
                    return

            type_line = context['typeLine']
            for map in self.index[data_key_maps]:
                if map == type_line:
                    self._update_value_generic(context, self.index[data_key_maps][map])
                    return

        elif 'jewels' in category:
            for jewel in self.index[data_key_jewels]:
                if jewel == item_name:
                    self._update_value_generic(context, self.index[data_key_jewels][jewel])
                    return

        elif 'cards' in category:
            type_line = context['typeLine']
            for card in self.index[data_key_cards]:
                if card == type_line:
                    self._update_value_generic(context, self.index[data_key_cards][card])
                    return

        elif 'flasks' in category:
            for flask in self.index[data_key_flasks]:
                if flask == item_name:
                    self._update_value_generic(context, self.index[data_key_flasks][flask])
                    return

        elif 'gems' in category:
            type_line = context['typeLine']
            for gem in self.index[data_key_skill_gem]:
                if gem == type_line:
                    self._update_value_generic(context, self.index[data_key_skill_gem][gem])
                    return

        elif 'currency' in category:
            for currency in self.index[data_key_currency]:
                if currency == item_name:
                    self._update_value_generic(context, self.index[data_key_currency][currency])
                    return
        else:
            print("Unhandled Item Category: " + category)

        return None

    def _update_value_for_frame_and_link_match(self, context, data_entry):
        self._update_link_count(context)
        item_class = context['type']
        item_links = context['links']
        corrupted = context['corrupted']
        if corrupted is True:
            # For now we will ignore corrupted weapons and armor, too much variation in price
            return

        results = 0
        result = 0

        context['default_value'] = 0
        for candidate in data_entry:
            entry_links = candidate.get('links')
            if entry_links < 5:
                context['default_value'] = candidate.get('chaosValue')
            if context['default_value'] is None:
                context['default_value'] = 0
            break

        lastCandidate = None
        for candidate in data_entry:
            entry_class = candidate.get('itemClass')
            entry_links = candidate.get('links')
            if entry_class != item_class or entry_links != item_links:
                continue

            value = candidate.get('chaosValue')
            if value is None:
                continue

            results += 1
            result = value

            # for debug
            lastCandidate = candidate

        if results != 1:
            # Inconclusive, wont take the risk
            return 0

        context['value'] = result
        context['value_source'] = lastCandidate

    @staticmethod
    def _update_value_generic_non_corrupt(context, data_entry):
        corrupted = context['corrupted']
        if corrupted is True:
            # For now we will ignore corrupted weapons and armor, too much variation in price
            return

        lastCandidate = None
        results = 0
        result = 0
        for candidate in data_entry:
            value = candidate.get('chaosValue')
            if value is None:
                continue

            results += 1
            result = value

            lastCandidate = candidate

        if results != 1:
            # Inconclusive, wont take the risk
            return 0

        context['value'] = result
        context['value_source'] = lastCandidate

    @staticmethod
    def _update_value_generic(context, data_entry):
        lastCandidate = None
        results = 0
        result = 0
        for candidate in data_entry:
            value = candidate.get('chaosValue')
            if value is None:
                continue

            results += 1
            result = value
            lastCandidate = candidate

        if results != 1:
            # Inconclusive, wont take the risk
            return 0

        context['value'] = result
        context['value_source'] = lastCandidate

    def _get_data_cache_name(self, path):
        return time.strftime("%Y-%m-%d-%H") + "_" + self.league + "_" + path

    def _get_ninja_link(self, is_cdn, path):
        if is_cdn == 1:
            link = self._ninja_cdn
        else:
            link = self._ninja_api
        link += path + "?league=" + self.league + "&date=" + time.strftime("%Y-%m-%d")
        return link

    def _index_data(self, data_key, data, entry_key):
        self.index[data_key] = {}

        entry_count = 0
        for entry in data:
            id = entry.get('id')
            if id is not None:
                if id in self.ignored_data_ids:
                    print("Ignoring data entry id " + str(id))
                    continue

            key = entry.get(entry_key)
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

    def _reload_armor(self):
        link = self._get_ninja_link(1, "GetUniqueArmourOverview")
        data = self._load_data(link, self._get_data_cache_name(data_key_armor))
        self._index_data(data_key_armor, data, "name")

    def _reload_weapons(self):
        link = self._get_ninja_link(1, "GetUniqueWeaponOverview")
        data = self._load_data(link, self._get_data_cache_name(data_key_weapons))
        self._index_data(data_key_weapons, data, "name")

    def _reload_accessories(self):
        link = self._get_ninja_link(1, "GetUniqueAccessoryOverview")
        data = self._load_data(link, self._get_data_cache_name(data_key_accessory))
        self._index_data(data_key_accessory, data, "name")

    def _reload_fragments(self):
        link = self._get_ninja_link(1, "GetFragmentOverview")
        data = self._load_data(link, self._get_data_cache_name(data_key_fragments))
        self._index_data(data_key_fragments, data, "currencyTypeName")

    def _reload_prophecies(self):
        link = self._get_ninja_link(1, "GetProphecyOverview")
        data = self._load_data(link, self._get_data_cache_name(data_key_prophecy))
        self._index_data(data_key_prophecy, data, "name")

    def _reload_essences(self):
        link = self._get_ninja_link(1, "GetSkillGemOverview")
        data = self._load_data(link, self._get_data_cache_name(data_key_skill_gem))
        self._index_data(data_key_skill_gem, data, "name")

    def _reload_skill_gems(self):
        link = self._get_ninja_link(1, "GetEssenceOverview")
        data = self._load_data(link, self._get_data_cache_name(data_key_essence))
        self._index_data(data_key_essence, data, "name")

    def _reload_divination_cards(self):
        link = self._get_ninja_link(0, "GetDivinationCardsOverview")
        data = self._load_data(link, self._get_data_cache_name(data_key_cards))
        self._index_data(data_key_cards, data, "name")

    def _reload_flasks(self):
        link = self._get_ninja_link(0, "GetUniqueFlaskOverview")
        data = self._load_data(link, self._get_data_cache_name(data_key_flasks))
        self._index_data(data_key_flasks, data, "name")

    def _reload_jewels(self):
        link = self._get_ninja_link(0, "GetUniqueJewelOverview")
        data = self._load_data(link, self._get_data_cache_name(data_key_jewels))
        self._index_data(data_key_jewels, data, "name")

    def _reload_maps(self):
        link = self._get_ninja_link(1, "GetUniqueMapOverview")
        data = self._load_data(link, self._get_data_cache_name(data_key_unique_maps))
        self._index_data(data_key_unique_maps, data, "name")
        link = self._get_ninja_link(1, "GetMapOverview")
        data = self._load_data(link, self._get_data_cache_name(data_key_maps))
        self._index_data(data_key_maps, data, "name")

    def _reload_currency(self):
        link = self._get_ninja_link(1, "GetCurrencyOverview")
        data = self._load_data(link, self._get_data_cache_name(data_key_currency))
        self._index_data(data_key_currency, data, "currencyTypeName")