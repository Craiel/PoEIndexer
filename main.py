# coding=utf-8

import time
import requests
import re
import data
import evaluate
import ctypes

from colorama import init
from colorama import Fore, Back, Style
init()

league = "Abyss"
initial_change_id = ""
enabled = 1

dataLookup = data.IndexerData()
itemEvaluation = evaluate.ItemEvaluation(dataLookup)
itemEvaluation.add_ignore("Atziri")
itemEvaluation.add_ignore("Sadima")
itemEvaluation.add_ignore("Vinktar")
itemEvaluation.add_ignore("Yriel's Fostering")
itemEvaluation.add_ignore("The Signal Fire")
itemEvaluation.add_ignore("Ventor's Gamble")
itemEvaluation.add_ignore("Watcher's Eye")

def notify_important():
    ctypes.windll.user32.FlashWindow(ctypes.windll.kernel32.GetConsoleWindow(), True)

def print_result(result):

    rating = 0

    # set the main rating based on the percentage gain
    if result['percent_decrease'] >= 85:
        rating += 8
    elif result['percent_decrease'] >= 70:
        rating += 6
    elif result['percent_decrease'] >= 50:
        rating += 4
    elif result['percent_decrease'] >= 30:
        rating += 2
    else:
        return

    # bump up the rating by one since the profit margin is great
    if result['gain'] > 25:
        rating += 2

    header = "[{}] [{} - {}c/{}c/{}c - {}%] ".format(
        time.strftime("%H:%M:%S"),
        rating,
        round(result['price'], 0),
        round(result['value'], 0),
        round(result['optimistic_value'], 0),
        round(result['percent_decrease'])
    )

    msg = "@{} Hi, I would like to buy your {} listed for {} {} in {} (stash tab \"{}\"; position: left {}, top {})".format(
        result['character'],
        result['name'],
        result['price_raw'],
        result['currency_title'],
        league,
        result['stash'],
        result['pos'][0],
        result['pos'][1]
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

def main():

    dataLookup.set_league(league)
    dataLookup.reload()

    itemEvaluation.set_league(league)

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
        results = itemEvaluation.process(data['stashes'])
        if results is not None:
            for result in results:
                print_result(result)

        ## wait 5 seconds until parsing next structure
        time.sleep(1)

if __name__ == "__main__":
    #ui.UIApp().run()
    main()
