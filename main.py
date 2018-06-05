# coding=utf-8

import time
import requests
import data
import evaluate
import ctypes
import ui

from colorama import init
from colorama import Fore
init()

league = "Incursion"
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
itemEvaluation.add_ignore("The Pariah")
itemEvaluation.add_ignore("Kaom's Roots")
itemEvaluation.add_ignore("The Ascetic")
itemEvaluation.add_ignore("Skin of the Loyal")
itemEvaluation.add_ignore("Headhunter")
itemEvaluation.add_ignore("The Saint's Treasure")
itemEvaluation.add_ignore("Umbilicus Immortalis")
itemEvaluation.add_ignore("Hall of Grandmasters")

# Set the maximum currency we are willing to spend
itemEvaluation.max_currency_to_spend = 99999

# Own characters
itemEvaluation.add_character_ignore("Cerkhar")

# Known Spammers / Abusers / Price Fixers
#itemEvaluation.add_character_ignore("Алилет")

#uiApp = ui.UIApp()
#uiApp.run

lastStatisticTime = 0
statisticInterval = 60 * 5


def notify_important():
    ctypes.windll.user32.FlashWindow(ctypes.windll.kernel32.GetConsoleWindow(), True)

def get_formated_value(color, value):
    return color + str(round(value, 0))

def print_result_part(string):
    print(string, end='', flush=True)

def print_result(result):

    if result['rating'] == 4:
        color = Fore.MAGENTA
        # won't notify on these, they are almost always mis-pricing
    elif result['rating'] == 3:
        color = Fore.RED
        notify_important()
    elif result['rating'] == 2:
        color = Fore.YELLOW
    elif result['rating'] == 1:
        color = Fore.GREEN
    else:
        return

    print_result_part(color + " -------------------------------- ")

    print()
    print_result_part(color + "[{}] ".format(time.strftime("%H:%M:%S")))
    print_result_part(" ~{}~ ".format(result['value_source_id']))
    print_result_part(Fore.WHITE + "{}% ({}c) ".format(
        get_formated_value(color, result['percent_decrease']),
        get_formated_value(color, result['gain'])))
    print_result_part("OfferValue={}c, Value={}c ({}c)".format(
        get_formated_value(color, result['price']),
        get_formated_value(color, result['value']),
        get_formated_value(color, result['optimistic_value'])
    ))

    if result['currency'] is not None:
        print_result_part(" Pay={} {}".format(
            get_formated_value(color, result['price_raw']),
            result['currency_title']
        ))

    print()
    print_result_part(Fore.WHITE + " -> @{} Hi, I would like to buy your {} listed for {} {} in {} (stash tab \"{}\"; position: left {}, top {})".format(
        result['character'],
        result['name'],
        result['price_raw'],
        result['currency_title'],
        league,
        result['stash'],
        result['pos'][0],
        result['pos'][1]
    ))

    print()

def main():

    dataLookup.set_league(league)
    dataLookup.enable_gems = False
    dataLookup.reload()

    itemEvaluation.set_league(league)

    print("Searching for mispriced items...")
    url_api = "http://www.pathofexile.com/api/public-stash-tabs?id="

    # get the next change id
    r = requests.get("http://poe.ninja/api/Data/GetStats")
    next_change_id = initial_change_id
    if next_change_id == "":
        next_change_id = r.json().get('next_change_id')

    if enabled == 0:
        return

    lastStatisticTime = time.time()

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

        if time.time() - lastStatisticTime > statisticInterval:
            lastStatisticTime = time.time()

            itemEvaluation.print_stats(statisticInterval)
            itemEvaluation.reset_stats()

if __name__ == "__main__":
    #ui.UIApp().run()
    main()
