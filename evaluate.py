import os
import re
import hashlib
import json
import time

from pathlib import Path


class ItemEvaluation:
    league = "Standard"
    cache_directory = "cache_evaluate"
    data = None
    stat_stashes_processed = 0
    stat_items_processed = 0
    ignore_list = []
    character_ignore_list = []
    md5 = hashlib.md5()
    min_value = 1
    min_gain = 2
    min_percent_decrease = 30
    optimistic_multiplier = 0.9
    enable_cache = False
    enable_debug = True
    number_regex = r"[-+]?\d*\.\d+|\d+"

    def __init__(self, indexer_data):

        print("Initializing Item Evaluation")
        print(" -> Cache: " + str(self.enable_cache))

        if indexer_data is None:
            raise ValueError('Indexer Data is None!')

        self.data = indexer_data

        if not os.path.exists(self.cache_directory):
            os.makedirs(self.cache_directory)

        pass

    def set_league(self, league_value):
        print(" -> Setting League to " + league_value)
        self.league = league_value

    def process(self, stashes):
        results = []
        for stash in stashes:
            stash_results = self._process_stash(stash)
            if stash_results is None:
                continue

            for result in stash_results:
                results.append(result)

        return results

    def add_ignore(self, name):
        self.ignore_list.append(name)

    def add_character_ignore(self, name):
        self.character_ignore_list.append(name)

    def _process_stash(self, stash):
        if stash is None:
            return None

        self.stat_stashes_processed += 1

        items = stash['items']
        if items is None or len(items) == 0:
            return None

        # scan items
        results = []
        for item in items:
            item_league = item.get('league')
            if item_league != self.league:
                return None

            entry = self._process_item(stash, item)
            if entry is not None:
                results.append(entry)

        return results

    def _process_item(self, stash, item):
        if stash is None or item is None:
            return None

        self.stat_items_processed += 1

        context = {
            'raw_data': item,
            'id': item.get('id', None),
            'type': item.get('frameType', None),
            'category': item.get('category', None),
            'character': stash.get('lastCharacterName'),
            'note': item.get('note', None),
            'name_raw': item.get('name', None),
            'pos': [item.get('x'), item.get('y')],
            'stash': stash.get('stash'),
            'corrupted': item.get('corrupted') is not None,
        }

        if context['note'] is None \
                or context['note'] == '' \
                or not context['note'].startswith('~'):
            # Ignore this item, won't find any valid price info anyway
            return None

        if context['name_raw'] is None or context['name_raw'] == '' or context['category'] == 'maps':
            context['name'] = item.get('typeLine')
        else:
            context['name'] = re.sub(r'<<.*>>', '', context['name_raw'])

        for ignoreEntry in self.ignore_list:
            if ignoreEntry in context['name']:
                # item is ignored
                return None

        for characterIgnoreEntry in self.character_ignore_list:
            if characterIgnoreEntry in context['character']:
                return None

        context['value'] = self.data.get_value(item)
        if context['value'] is None or context['value'] < self.min_value:
            # print("No Value for " + name)
            return None

        # compute a unique hash based on the id and the note field (which changes with price changes)
        hash_data = (str(context['id']) + context['note']).encode('utf-8')
        self.md5.update(hash_data)
        context['hash'] = self.md5.hexdigest()

        cached_result = self._load_result_from_cache(context['hash'])
        if cached_result is not None:
            age = time.time() - cached_result['time']
            print('Cache_Age: ' + str(age))

            return cached_result

        context['time'] = time.time()

        self._update_item_currency(context)
        self._update_item_price(context)

        if 'price' not in context or context['price'] is None or context['price'] < self.min_value:
            return None

        context['optimistic_value'] = context['value'] * self.optimistic_multiplier
        context['gain'] = context['optimistic_value'] - context['price']
        if context['gain'] < self.min_gain:
            # Need to make at least min gain for this to be worth
            return None

        context['percent_decrease'] = (context['gain'] / context['optimistic_value']) * 100
        if context['percent_decrease'] < self.min_percent_decrease:
            return None

        self._rate_result(context)
        if context['rating'] <= 0:
            return None

        self._save_debug(context)
        self._save_result_to_cache(context)

        return context

    def _load_result_from_cache(self, hash):
        if not self.enable_cache:
            return None

        cache_file = self.cache_directory + "/" + hash
        my_file = Path(cache_file)
        if my_file.is_file():
            with open(cache_file) as json_data:
                return json.load(json_data)

        return None

    def _save_debug(self, result):
        if not self.enable_debug:
            return

        debug_file = self.cache_directory + "/" + str(result['time']) + "_" + str(result['id']) + "_" + result['name']
        with open(debug_file, 'w') as outfile:
            json.dump(result, outfile)

    def _save_result_to_cache(self, result):
        if not self.enable_cache:
            return

        cache_file = self.cache_directory + "/" + result['hash']
        with open(cache_file, 'w') as outfile:
            json.dump(result, outfile)

    @staticmethod
    def _update_item_currency(context):
        price_raw = context['note'].lower()
        if 'chaos' in price_raw or 'caos' in price_raw:
            currency = None
            currency_title = "chaos"
            pass
        elif 'exa' in price_raw or 'erhaben' in price_raw:
            currency = "Exalted Orb"
            currency_title = "exalted"
        elif 'alch' in price_raw or 'alchemie' in price_raw or 'alq' in price_raw:
            currency = "Orb of Alchemy"
            currency_title = "alchemy"
        elif 'vaal' in price_raw:
            currency = "Vaal Orb"
            currency_title = "vaal"
        elif 'chisel' in price_raw or 'meißel' in price_raw:
            currency = "Cartographer's Chisel"
            currency_title = "chisel"
        elif 'chrom' in price_raw or 'crom' in price_raw or 'färbung' in price_raw:
            currency = "Chromatic Orb"
            currency_title = "chromatic"
        elif 'fuse' in price_raw or 'verbindung' in price_raw or 'fus' in price_raw or 'fusión' in price_raw:
            currency = "Orb of Fusing"
            currency_title = "fusing"
        elif 'chance' in price_raw or 'möglichkeiten' in price_raw:
            currency = "Orb of Chance"
            currency_title = "chance"
        elif 'alt' in price_raw or 'veränderung' in price_raw:
            currency = "Orb of Alteration"
            currency_title = "alteration"
        elif 'mirror' in price_raw or 'mir' in price_raw:
            currency = "Mirror of Kalandra"
            currency_title = "mirror"
        elif 'jew' in price_raw:
            currency = "Jeweller's Orb"
            currency_title = "jeweler"
        elif 'regal' in price_raw:
            currency = "Regal Orb"
            currency_title = "regal"
        elif 'scour' in price_raw:
            currency = "Orb of Scouring"
            currency_title = "scouring"
        elif 'gcp' in price_raw:
            currency = "Gemcutter's Prism"
            currency_title = "gemcutter"
        elif 'divine' in price_raw:
            currency = "Divine Orb"
            currency_title = "divine"
        elif 'blessed' in price_raw:
            currency = "Blessed Orb"
            currency_title = "blessed"
        elif 'regret' in price_raw:
            currency = "Orb of Regret"
            currency_title = "regret"
        elif 'silver' in price_raw or 'silver coin' in price_raw:
            currency = "Silver Coin"
            currency_title = "silver"
        elif 'wisdom' in price_raw or 'wis' in price_raw:
            currency = "Scroll of Wisdom"
            currency_title = "wisdom"
        else:
            print("Unsupported Currency: " + price_raw)
            return False

        context['price_raw'] = context['note']
        context['currency'] = currency
        context['currency_title'] = currency_title

    def _update_item_price(self, context):

        try:
            if not re.findall(self.number_regex, context['price_raw'])[0]:
                return

            parsed_price = float(re.findall(self.number_regex, context['price_raw'])[0])
            if parsed_price.is_integer():
                parsed_price = int(parsed_price)

            context['price_raw'] = parsed_price

        except:
            return False

        if context['currency'] is not None:
            conversion_rate = self.data.get_currency_conversion(context['currency'])
            if conversion_rate is None:
                return False

            # Calculate the price in chaos, deduct 5% of the conversion rate since it's changing fast
            context['price'] = int(context['price_raw'] * (conversion_rate * 0.95))
        else:
            context['price'] = int(context['price_raw'])

        if context['price'] is None or context['price'] < 1:
            return False

        return True

    @staticmethod
    def _rate_result(context):

        context['rating'] = 0

        # set the main rating based on the percentage gain
        if context['percent_decrease'] >= 90:
            if context['value'] <= 5:
                # anything less or equal to 5c worth is always at rating 2
                context['rating'] = 2
            else:
                context['rating'] = 4
        elif context['percent_decrease'] >= 60:
            if context['value'] <= 5:
                # anything less or equal to 5c worth is always at rating 2
                context['rating'] = 2
            else:
                context['rating'] = 3
        elif context['percent_decrease'] >= 40:
            context['rating'] = 2
        elif context['percent_decrease'] >= 20:

            # Ignore certain categories in low percentages
            if context['category'] == 'maps':
                return

            context['rating'] = 1
