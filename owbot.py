"""
    Overwatch + Twitch.tv + Twitter Bot

    Look for the most viewed Overwatch player on Twitch.tv and publish his stuff
    on Twitter.

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

from twitchscrapper import get_directory_data, get_user_data

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
    with open(CONFIGJSON, "w") as f:
        json.dump(CONFIG, f)

QBOTJSON = os.path.join(HOME, "qbot.json")
try:
    QBOT = json.load(open(QBOTJSON, "r"))
except (IOError, ValueError):
    QBOT = {
        "options": {
            "refresh_schedule": True
        },
        "schedule": {
            "name":
            "overwatchbest",
            "days": [
                "monday", "tuesday", "wednesday", "thursday", "friday",
                "saturday", "sunday"
            ],
            "hours": []
        },
        "twitter_tokens": {
            "consumer_key": "find",
            "consumer_secret": "them",
            "oauth_token": "on",
            "oauth_secret": "apps.twitter.com"
        },
        "messages": []
    }

    # All day, every 15 minutes
    QBOT['schedule']['hours'] = [
        f"{h:02}:{m:02}" for h in range(0, 24) for m in range(0, 60, 15)
    ]

if __name__ == "__main__":

    DELTA = time.time()
    print("OWbot v0.1")

    # Command line args

    PARSER = argparse.ArgumentParser(
        description='Bot that tweets the best streamers from Twitch.tv')
    PARSER.add_argument(
        "-s",
        "--start",
        help="start the scrapping + Qbot queue process",
        action="store_true")
    PARSER.add_argument(
        "-d",
        "--delay",
        help=
        "seconds to wait between complete cycles, 900s (15m) default, use 0 or less to not repeat at all",
        default=15 * 60,
        type=int)
    PARSER.add_argument(
        "-b",
        "--ban",
        help=
        "seconds to wait before republishing an account again, 43200s (12h) default",
        default=12 * 3600,
        type=int)
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
                "w") as f:
            json.dump(DIRECTORY, f)

        for user, dirdata in DIRECTORY.items():

            # Registry setup

            CONFIG['promoted'] = CONFIG.get('promoted', {})
            CONFIG['promoted'][user] = CONFIG['promoted'].get(
                user, {
                    'count': 0,
                    'first_time': time.time(),
                    'last_time': 0
                })

            # Avoid spamming users

            if time.time() - CONFIG['promoted'][user]['last_time'] < ARGS.ban:
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
                    "w") as f:
                json.dump(userdata, f)

            print("\nExtracting data...\n")

            status = userdata[user]['status']
            status = status if len(status) < 200 else status[:200] + "[...]"
            status = " ".join(status.split())

            twitter = " ".join([f"@{i}" for i in userdata[user]['twitter']])
            twitter = f" ({twitter}) " if twitter else " "

            imageurl = dirdata['image']
            print(f"Image url: {imageurl}")
            imagefile = os.path.join(IMAGESPATH, os.path.basename(imageurl))
            with urlopen(imageurl) as r, open(imagefile, 'wb') as f:
                shutil.copyfileobj(r, f)
                print(f"Downloaded: {imagefile}")

            # Queue tweet in Qbot

            tweet = {'text': f"{status}{twitter}{url}", 'image': imagefile}
            QBOT['messages'].append(tweet)
            with open(QBOTJSON, "w") as f:
                json.dump(QBOT, f)
                print(f"Tweet: {tweet['text']}")
                print(f"Queued on Qbot: {QBOTJSON}")

            # Register

            CONFIG['promoted'][user]['count'] += 1
            CONFIG['promoted'][user]['last_time'] += time.time()
            with open(CONFIGJSON, "w") as f:
                json.dump(CONFIG, f)

            # Just once
            break

        # Repeat

        REPEAT = False if ARGS.delay <= 0 else REPEAT
        if REPEAT:
            print()

        while REPEAT and WAIT < ARGS.delay:
            sys.stdout.write(f"\r'q' + enter to quit ({ARGS.delay - WAIT}s): ")
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
