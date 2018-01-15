"""
    Bot that collect and tweet the top Overwatch streamers from Twitch.tv

    @matnesis 2018/01/10
"""

import argparse
import json
import os
import shutil
import sys
import threading
import time
from urllib.request import urlopen

from twitchscrapper import get_directory_data, get_user_data, uniquelist

# Paths

HOME = os.path.normpath(  # The script directory + cxfreeze compatibility
    os.path.dirname(
        sys.executable if getattr(sys, 'frozen', False) else __file__))

IMAGESPATH = os.path.join(HOME, "images")
if not os.path.exists(IMAGESPATH):
    os.makedirs(IMAGESPATH)

DATAPATH = os.path.join(HOME, "data")
if not os.path.exists(DATAPATH):
    os.makedirs(DATAPATH)

# Files

CONFIGJSON = os.path.join(HOME, "config-owbot.json")
try:
    CONFIG = json.load(open(CONFIGJSON, "r"))
except (IOError, ValueError):
    CONFIG = {"promoted": {}}
    with open(CONFIGJSON, 'w') as f:
        json.dump(CONFIG, f)

QBOTJSON = os.path.join(HOME, "qbot.json")
try:
    QBOT = json.load(open(QBOTJSON, "r"))
except (IOError, ValueError):
    QBOT = {
        'options': {
            'refresh_schedule': True
        },
        'schedule': {
            'name':
            'overwatchbest',
            'days': [
                'monday', 'tuesday', 'wednesday', 'thursday', 'friday',
                'saturday', 'sunday'
            ],
            'hours': []
        },
        'twitter_tokens': {
            'consumer_key': 'find',
            'consumer_secret': 'them',
            'oauth_token': 'on',
            'oauth_secret': 'apps.twitter.com'
        },
        'messages': []
    }

    # All day, every 15 minutes
    QBOT['schedule']['hours'] = [
        f"{h:02}:{m:02}" for h in range(0, 24) for m in range(0, 60, 15)
    ]


def strseconds(strtime):
    """
        Return a int with the seconds from particular literals.

        e.g
            "1h" -> 3600
            "20m" -> 1200
            "10s" | "10" -> 10
            "10sm" -> None
            "1d" -> 86400s (1 day)
    """

    result = None

    strtime = strtime.lower()  # Case insensitive
    strdigits = "".join([i for i in strtime if i.isdigit()])

    if len(strtime) == len(strdigits):  # Without simbol is seconds
        result = int(strdigits)
    elif len(strtime) > len(strdigits) + 1:  # Only one symbol allowed
        result = None
    elif 'd' in strtime:  # Days
        result = 86400 * int(strdigits)
    elif 'h' in strtime:  # Hours
        result = 3600 * int(strdigits)
    elif 'm' in strtime:  # Minutes
        result = 60 * int(strdigits)
    elif 's' in strtime:  # Seconds
        result = int(strdigits)

    return result


if __name__ == "__main__":

    DELTA = time.time()
    print("OWbot v0.1")

    # Command line args

    PARSER = argparse.ArgumentParser(
        description=
        "Bot that tweets and collects the top streamers from Twitch.tv")
    PARSER.add_argument(
        "-s",
        "--start",
        help="start the cycle, find the top streamer and queue it in Qbot",
        action="store_true")
    PARSER.add_argument(
        "-d",
        "--delay",
        help="delay between complete cycles, '3h' hours default",
        default="3h",
        type=str)
    PARSER.add_argument(
        "-b",
        "--ban",
        help="delay between republishing an account again, '7d' days default",
        default="7d",
        type=str)
    ARGS = PARSER.parse_args()

    # TODO DANGEROUS code: All new options need to be here or they will be ignored
    if not ARGS.start:
        PARSER.print_usage()
        PARSER.exit()

    # Thread to detect input commands and stop the repeat cycle

    REPEAT = True

    def bot_commands():
        """
            Input detection thread.
        """
        global REPEAT
        while REPEAT:
            text = input()
            if text.strip().lower() == "q":  # Quit
                REPEAT = False

    THREAD = threading.Thread(target=bot_commands)
    THREAD.daemon = True
    THREAD.start()

    # Repeat cycle

    DELAY = strseconds(ARGS.delay)
    BAN = strseconds(ARGS.ban)

    WAIT = 0
    COUNT = 1
    while REPEAT:

        # Prepare a tweet for the top Twitch.tv streamer

        print("\nScrapping data...")

        DIRURL = "https://www.twitch.tv/directory/game/Overwatch"
        DIRECTORY = get_directory_data(
            DIRURL, language="en", increase_image=200)
        print(f"Scrapped: {DIRURL}")

        if not DIRECTORY:
            input(f"\nError scraping: {DIRURL}")
            sys.exit(1)

        with open(
                os.path.join(DATAPATH,
                             f"directory({round(time.time())}).json"),
                'w') as f:
            json.dump(DIRECTORY, f)

        for user, dirdata in DIRECTORY.items():

            # Registry setup

            CONFIG['promoted'] = CONFIG.get('promoted', {})
            CONFIG['promoted'][user] = CONFIG['promoted'].get(
                user, {
                    'count': 0,
                    'found': time.time(),
                    'last_promo': 0
                })

            # Avoid spamming users

            if time.time() - CONFIG['promoted'][user]['last_promo'] < BAN:
                continue

            # Data

            url = f"https://www.twitch.tv/{user}"
            userdata = get_user_data(url)
            print(f"Scrapped: {url}")

            if not userdata:
                input(f"\nError scraping: {url}")
                sys.exit(1)

            with open(
                    os.path.join(DATAPATH,
                                 f"{user}({round(time.time())}).json"),
                    'w') as f:
                json.dump(userdata, f)

            print("\nExtracting data...\n")

            status = userdata[user]['status'].replace('@', '')  # No replies
            status = " ".join(status.split())
            status = status if len(status) < 200 else status[:200] + "[...]"

            # Tags from Twitter and Twitch usernames

            twitter_accounts = userdata[user]['twitter']
            tags = uniquelist(twitter_accounts + [user])
            tags = " ".join([f"#{i}" for i in tags])

            # Images

            imageurl = dirdata['image']
            print(f"Image url: {imageurl}")
            imagefile = os.path.join(IMAGESPATH, os.path.basename(imageurl))
            with urlopen(imageurl) as r, open(imagefile, 'wb') as f:
                shutil.copyfileobj(r, f)
                print(f"Downloaded: {imagefile}")

            # Queue tweet in Qbot

            tweet = {'text': f"{status} {tags}", 'image': imagefile}
            QBOT['messages'].append(tweet)
            with open(QBOTJSON, 'w') as f:
                json.dump(QBOT, f)
                print(f"Tweet: {tweet['text']}")
                print(f"Queued on Qbot: {QBOTJSON}")

            # Register

            CONFIG['promoted'][user]['count'] += 1
            CONFIG['promoted'][user]['last_promo'] = time.time()
            with open(CONFIGJSON, 'w') as f:
                json.dump(CONFIG, f)

            # Just once
            break

        # Repeat

        REPEAT = False if DELAY <= 0 else REPEAT
        if REPEAT:
            print()

        while REPEAT and WAIT < DELAY:
            sys.stdout.write(f"\r'q' + enter to quit ({DELAY - WAIT}s): ")
            sys.stdout.flush()
            WAIT += 1
            time.sleep(1)

        if REPEAT:
            WAIT = 0
            COUNT += 1
            print(f"\n\n#{COUNT}")

    # The end
    print(f"\nDone! ({round(time.time() - DELTA)}s)")
    time.sleep(2)
