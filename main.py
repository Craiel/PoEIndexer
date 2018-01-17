# coding=utf-8

import time
import requests
import re
import os
import json
import ui
import data
import ctypes
from pathlib import Path

from colorama import init
from colorama import Fore, Back, Style
init()

league = "Abyss"
initial_change_id = ""
ignore_list = ["Atziri", "Sadima", "Drillneck", "Vinktar", "Yriel's Fostering", "The Signal Fire", "Ventor's Gamble", "Watcher's Eye"]
enabled = 1

dataLookup = data.IndexerData()


def notify_important():
    ctypes.windll.user32.FlashWindow(ctypes.windll.kernel32.GetConsoleWindow(), True)

def process_item(stash, item):

    name = re.sub(r'<<.*>>', '', item.get('name', None))

    price_raw = item.get('note', None)
    if price_raw is None or not price_raw.startswith('~'):
        return

    if not price_raw or not name:
        return

    if 'chaos' in price_raw or 'Chaos' in price_raw or 'caos' in price_raw:
        currency = None
        currency_title = "chaos"
        pass
    elif 'exa' in price_raw or 'Erhaben' in price_raw:
        currency = "Exalted Orb"
        currency_title = "exalted"
    elif 'alch' in price_raw or 'Alchemie' in price_raw or 'alq' in price_raw:
        currency = "Orb of Alchemy"
        currency_title = "alchemy"
    elif 'vaal' in price_raw:
        currency = "Vaal Orb"
        currency_title = "vaal"
    elif 'chisel' in price_raw or 'Meißel' in price_raw:
        currency = "Cartographer's Chisel"
        currency_title = "chisel"
    elif 'chrom' in price_raw or 'crom' in price_raw:
        currency = "Chromatic Orb"
        currency_title = "chromatic"
    elif 'fuse' in price_raw or 'Verbindung' in price_raw or 'fus' in price_raw or 'fusión' in price_raw:
        currency = "Orb of Fusing"
        currency_title = "fusing"
    elif 'chance' in price_raw:
        currency = "Orb of Chance"
        currency_title = "chance"
    elif 'alt' in price_raw or 'Veränderung' in price_raw:
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
    elif 'silver' in price_raw:
        currency = "Silver Coin"
        currency_title = "silver"
    else:
        print("Unsupported Currency: " + price_raw)
        return

    for ignoreEntry in ignore_list:
        if ignoreEntry in name:
            return

    item_value = dataLookup.get_value(item)
    if item_value is None:
        #print("No Value for " + name)
        return

    try:
        if not re.findall(r'\d+', price_raw)[0]:
            return

        price = float(re.findall(r'\d+', price_raw)[0])

    except:
        return

    currency_price = price
    if currency is not None:
        conversion_rate = dataLookup.get_currency_conversion(currency)
        if conversion_rate is None:
            return

        # Calculate the price in chaos, deduct 5% of the conversion rate since it's changing fast
        price = currency_price * (conversion_rate * 0.95)

    if price is None or price < 1:
        return

    rating = 0
    optimistic_value = item_value * 0.9
    gain = optimistic_value - price
    if gain < 2:
        # Need to make at least 2c for this to be worth
        return

    perc_decrease = (gain / optimistic_value) * 100

    # set the main rating based on the percentage gain
    if perc_decrease >= 85:
        rating += 8
    elif perc_decrease >= 70:
        rating += 6
    elif perc_decrease >= 50:
        rating += 4
    elif perc_decrease >= 30:
        rating += 2
    else:
        return

    # bump up the rating by one since the profit margin is great
    if gain > 25:
        rating += 2

    header = "[{}] [{} - {}c/{}c/{}c - {}%] ".format(
        time.strftime("%H:%M:%S"),
        rating,
        price,
        round(item_value, 0),
        round(optimistic_value, 0),
        round(perc_decrease)
    )

    msg = "@{} Hi, I would like to buy your {} listed for {} {} in {} (stash tab \"{}\"; position: left {}, top {})".format(
        stash['lastCharacterName'],
        name,
        currency_price,
        currency_title,
        league,
        stash.get('stash'),
        item.get('x'),
        item.get('y')
    )

    if rating >= 8:
        notify_important()
        print(Fore.RED + header + msg)
    elif rating >= 6:
        print(Fore.YELLOW + header + msg)
    elif rating >= 4:
        print(Fore.GREEN + header + msg)
    elif rating >= 2:
        print(Fore.WHITE + header + msg)
    else:
        return


def find_items(changeId, stashes):
    # scan stashes available...
    for stash in stashes:
        items = stash['items']

        if len(items) == 0:
            continue

        # scan items
        for item in items:
            itemLeague = item.get('league')
            if itemLeague == "Standard" or itemLeague == "SSF Standard" or itemLeague == "Hardcore" or itemLeague == "Hardcore " + league or itemLeague == "SSF " + league or itemLeague == "SSF " + league + " HC":
                break

            if itemLeague != league:
                print("Warning, Item League was non-standard but mismatch: " + itemLeague + " != " + league)

            process_item(stash, item)

def main():

    dataLookup.set_league(league)
    dataLookup.reload()

    print(Fore.GREEN + "Searching for mispriced items...")
    url_api = "http://www.pathofexile.com/api/public-stash-tabs?id="

    # get the next change id
    r = requests.get("http://api.poe.ninja/api/Data/GetStats")
    next_change_id = initial_change_id
    if next_change_id == "":
        next_change_id = r.json().get('next_change_id')

    if enabled == 0:
        return

    while True:
        params = {'id': next_change_id}
        r = requests.get(url_api, params=params)

        ## parsing structure
        data = r.json()

        ## setting next change id
        next_change_id = data['next_change_id']

        ## attempt to find items...
        find_items(next_change_id, data['stashes'])

        ## wait 5 seconds until parsing next structure
        time.sleep(1)

if __name__ == "__main__":
    #ui.UIApp().run()
    main()
