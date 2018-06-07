import os
import re
import hashlib
import json
import time


class ItemEvaluation:
    league = "Standard"
    cache_directory = "cache_evaluate"
    data = None
    stat_stashes_processed = 0
    stat_items_processed = 0
    stat_items_not_for_sale = 0
    stat_items_ignored = 0
    stat_items_without_value = 0
    stat_items_invalid_price = 0
    stat_items_low_gain = 0
    stat_items_low_rating = 0
    stat_items_with_custom_grade = 0
    stat_items_by_type = {}
    ignore_list = []
    character_ignore_list = []
    md5 = hashlib.md5()
    min_value = 5
    min_gain = 3
    min_percent_decrease = 30
    optimistic_multiplier = 0.9
    enable_cache = False
    enable_debug = True
    number_regex = r"[-+]?\d*\.\d+|\d+"
    jeweler_prophecy_value = 16
    max_currency_to_spend = 999999999999

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

    def reset_stats(self):
        self.stat_stashes_processed = 0
        self.stat_items_processed = 0
        self.stat_items_not_for_sale = 0
        self.stat_items_ignored = 0
        self.stat_items_invalid_price = 0
        self.stat_items_low_gain = 0
        self.stat_items_low_rating = 0
        self.stat_items_without_value = 0
        self.stat_items_with_custom_grade = 0
        self.stat_items_by_type = {}

    def print_stats(self, elapsed):
        print(" - Processed {} items in {} stashes ({}/s)".format(
            self.stat_items_processed,
            self.stat_stashes_processed,
            round(self.stat_items_processed / elapsed, 0)
        ))

        print("   -> NS={} I={} V={} P={}".format(self.stat_items_not_for_sale, self.stat_items_ignored, self.stat_items_without_value, self.stat_items_invalid_price))
        print("   -> G={} R={} CGR={}".format(self.stat_items_low_gain, self.stat_items_low_rating, self.stat_items_with_custom_grade))

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
            # 'raw_stash': stash,
            'raw_data': item,
            'id': item.get('id', None),
            'type': item.get('frameType', None),
            'sub_type': None,  # will be filled out below
            'category': item.get('category', None),
            'character': stash.get('lastCharacterName'),
            'note': item.get('note', None),
            'name_raw': item.get('name', None),
            'pos': [item.get('x'), item.get('y')],
            'stash': stash.get('stash'),
            'corrupted': item.get('corrupted') is not None,
            'typeLine': item.get('typeLine')
        }

        if context['note'] is None or context['note'] == '':
            # Ignore this item, won't find any valid price info anyway
            self.stat_items_not_for_sale += 1
            return None

        if not context['note'].startswith('~'):
            self.stat_items_not_for_sale += 1
            return None

        category_info = item.get('category')
        if category_info is not None:
            sub_type_key = list(category_info.keys())[0]
            sub_type_values = category_info[sub_type_key]
            if sub_type_values is not None and len(sub_type_values) > 0:
                context['sub_type'] = category_info[sub_type_key][0]

        if context['name_raw'] is None or context['name_raw'] == '':
            context['name'] = item.get('typeLine')
        else:
            context['name'] = re.sub(r'<<.*>>', '', context['name_raw'])
            if context['category'] == 'maps':
                context['name'] = context['name'] + ' ' + item.get('typeLine')

        for ignoreEntry in self.ignore_list:
            if ignoreEntry in context['name']:
                # item is ignored
                self.stat_items_ignored += 1
                return None

        for characterIgnoreEntry in self.character_ignore_list:
            if characterIgnoreEntry in context['character']:
                self.stat_items_ignored += 1
                return None

        self.data.update_value(context)
        context['is_graded_item'] = False
        if 'grade_score' in context:
            self.stat_items_with_custom_grade += 1
            context['is_graded_item'] = True
        elif 'value' not in context or context['value'] < self.min_value:
            #print("No Value for " + context['name'])
            self.stat_items_without_value += 1
            return None

        if 'value_source' in context:
            context['value_source_id'] = context['value_source'].get('id', None)

        if 'value_source_id' not in context or context['value_source_id'] is None:
            context['value_source_id'] = -1

        # compute a unique hash based on the id and the note field (which changes with price changes)
        hash_data = (str(context['id']) + context['note']).encode('utf-8')
        self.md5.update(hash_data)
        context['hash'] = self.md5.hexdigest()

        context['time'] = time.time()

        self._update_item_currency(context)
        self._update_item_price(context)

        if 'price' not in context or context['price'] is None or context['price'] < self.min_value:
            self.stat_items_invalid_price += 1
            return None

        if not context['is_graded_item']:
            if context['value'] > self.max_currency_to_spend:
                # this item is too expensive right now
                return None

            context['optimistic_value'] = context['value'] * self.optimistic_multiplier
            context['gain'] = context['optimistic_value'] - context['price']
            if context['gain'] < self.min_gain:
                # Need to make at least min gain for this to be worth
                self.stat_items_low_gain += 1
                return None

            if 'links' in context and context['links'] == 5:
                if context['default_value'] < 5:
                    # With jewelers prophecy 5 links are barely worth anything
                    # ignore if the non-linked price is low to begin with
                    self.stat_items_ignored += 1
                    return None

            context['percent_decrease'] = (context['gain'] / context['optimistic_value']) * 100
            if context['percent_decrease'] < self.min_percent_decrease:
                self.stat_items_low_gain += 1
                return None

            self._rate_result(context)
            if context['rating'] <= 0:
                self.stat_items_low_rating += 1
                return None

        #self._save_debug(context)

        return context

    def _save_debug(self, result):
        if not self.enable_debug:
            return

        debug_file = self.cache_directory + "/" + str(result['time']) + "_" + str(result['id']) + "_" + result['name']
        with open(debug_file, 'w') as outfile:
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
        elif 'port' in price_raw or 'portal' in price_raw:
            currency = "Portal Scroll"
            currency_title = "portal"
        elif 'sextant' in price_raw:
            # ignore sextant trading for now
            return False
        elif 'afilar' in price_raw:
            currency = "Blacksmith's Whetstone"
            currency_title = "whetstones"
        elif 'orb-of-annulment' in price_raw:
            currency = "Orb of Annulment"
            currency_title = "annul"
        elif 'trans' in price_raw:
            currency = "Orb of Transmutation"
            currency_title = "transmute"
        elif 'burin' in price_raw:
            # Unknown translation
            return False
        elif ' Shard' in price_raw or ' Fragment' in price_raw:
            # ignore shards and fragments
            return False
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
            if context['value'] <= 5 and context['category'] != 'maps':
                # anything except maps less or equal to 5c worth is always at rating 1
                context['rating'] = 1
            else:
                context['rating'] = 4
        elif context['percent_decrease'] >= 60:
            if context['value'] <= 5 and context['category'] != 'maps':
                # anything except maps less or equal to 5c worth is always at rating 1
                context['rating'] = 1
            else:
                context['rating'] = 3
        elif context['percent_decrease'] >= 40:
            context['rating'] = 2
        elif context['percent_decrease'] >= 20:

            # Ignore certain categories in low percentages
            if context['category'] == 'maps':
                return

            context['rating'] = 1
