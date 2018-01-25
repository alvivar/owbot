"""
    Bot that collects and tweets the top Overwatch streamers from Twitch.tv

    @matnesis 2018/01/10
"""

import argparse
import datetime
import json
import os
import re
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

DATAPATH = os.path.join(HOME, "data")

# Files

CONFIGJSON = os.path.join(HOME, "config-owbot.json")
try:
    with open(CONFIGJSON, 'r') as f:
        CONFIG = json.load(f)
except (IOError, ValueError):
    CONFIG = {'timer': -1, 'promoted': {}}
    with open(CONFIGJSON, 'w') as f:
        json.dump(CONFIG, f)

QBOTJSON = os.path.join(HOME, "qbot.json")
try:
    QBOT = json.load(open(QBOTJSON, 'r'))
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


def str2seconds(strtime):
    """
        Return the seconds represented in 'strtime' based on the special
        convention. 'default' will be returned if 'strtime' is malformed.

        e.g
            "1h" -> 3600s
            "2m" -> 120s
            "30s" | "30" -> 30s
            "30sm" -> None (Only one symbol)
            "1d" -> 86400s (1 day)
            "5x" -> None (x is not a valid symbol)
            "2h30m10" -> 7200s + 1800s + 10

        TODO
            Years
    """

    result = 0

    for i in re.split(r"([0-9]+[a-z]+)", strtime):

        stri = i.strip().lower()  # Case insensitive
        if not stri:
            continue

        digits = "".join([i for i in stri if i.isdigit()])

        if len(stri) == len(digits):  # Without symbol assume seconds
            result += int(digits)
        elif len(stri) > len(digits) + 1:  # Only one symbol number
            result += 0
        elif 'd' in stri:  # Days
            result += 86400 * int(digits)
        elif 'h' in stri:  # Hours
            result += 3600 * int(digits)
        elif 'm' in stri:  # Minutes
            result += 60 * int(digits)
        elif 's' in stri:  # Seconds
            result += int(digits)

    return result


def seconds2str(seconds):
    """
        Return a str representation of 'seconds' based on the special convention.

        e.g
            100 -> "2m40s"
            1000 -> "17m40s"
            10000 -> "3h47m40s"
            100000 -> "1d3h46m40s"

        TODO
            Years
    """

    seconds = abs(seconds)
    days = hours = minutes = 0

    if seconds >= 86400:
        days = seconds / 86400
        seconds = (days - int(days)) * 86400

    if seconds >= 3600:
        hours = seconds / 3600
        seconds = (hours - int(hours)) * 3600

    if seconds >= 60:
        minutes = seconds / 60
        seconds = (minutes - int(minutes)) * 60

    strtime = ""
    strtime += f"{int(days)}d" if days else ""
    strtime += f"{int(hours)}h" if hours else ""
    strtime += f"{int(minutes)}m" if minutes else ""
    strtime += f"{round(seconds)}s" if seconds else ""

    return strtime if strtime else "0s"


def todaystr():
    """
        Return the year, month and day joined as string.

        e.g. 20180115
    """
    today = datetime.datetime.today()
    return f"{today.year}{today.month:02}{today.day:02}"


if __name__ == "__main__":

    DELTA = time.time()
    print("OWbot v0.1")

    # Command line args

    PARSER = argparse.ArgumentParser(
        description=
        "Bot that collects and tweets the top Overwatch streamers from Twitch.tv"
    )
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
    PARSER.add_argument(
        "-n",
        "--now",
        help="starts immediately, ignoring the saved cycle delay",
        action="store_true")
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

    DELAY = str2seconds(ARGS.delay)
    BAN = str2seconds(ARGS.ban)

    TIMER = CONFIG['timer'] if not ARGS.now else DELAY
    TIMER = DELAY if TIMER < 0 else TIMER  # First time is -1 by default
    TIMER = DELAY if TIMER > DELAY else TIMER  # 2nd while below at least once

    COUNT = 0

    while REPEAT:

        # Repeat timer

        REPEAT = False if DELAY <= 0 else REPEAT
        if REPEAT and TIMER <= DELAY:
            print()

        while REPEAT and TIMER <= DELAY:
            COUNTDOWN = seconds2str(DELAY - TIMER)
            COUNTDOWN = f" ({COUNTDOWN}): "
            sys.stdout.write(f"\r'q' + enter to quit{COUNTDOWN}")
            sys.stdout.flush()

            TIMER += 1
            CONFIG['timer'] = TIMER
            time.sleep(1)

        with open(CONFIGJSON, 'w') as f:
            json.dump(CONFIG, f)

        if REPEAT:
            TIMER = 0
            COUNT += 1
            print(f"\n\n#{COUNT}")
        else:
            sys.exit(0)

        # Prepare a tweet of the top Twitch.tv streamer

        print("\nScrapping data...")

        DIRURL = "https://www.twitch.tv/directory/game/Overwatch"
        DIRECTORY = get_directory_data(
            DIRURL, language="en", increase_image=200)
        print(f"Scrapped: {DIRURL}")

        if not DIRECTORY:
            input(f"\nError scraping: {DIRURL}")
            sys.exit(1)

        # Dump directory

        DIRPATH = os.path.join(DATAPATH, todaystr())
        if not os.path.exists(DIRPATH):
            os.makedirs(DIRPATH)

        with open(
                os.path.join(DIRPATH, f"directory.{round(time.time())}.json"),
                'w') as f:
            json.dump(DIRECTORY, f)

        # Top Overwatch Twitch streamer

        for user, dirdata in DIRECTORY.items():

            # Registry setup

            CONFIG['promoted'] = CONFIG.get('promoted', {})
            CONFIG['promoted'][user] = CONFIG['promoted'].get(
                user, {
                    'count': 0,
                    'max_viewers': 0,
                    'min_viewers': 0,
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

            # Dump user

            USERPATH = os.path.join(DATAPATH, todaystr())
            if not os.path.exists(USERPATH):
                os.makedirs(USERPATH)

            with open(
                    os.path.join(USERPATH,
                                 f"{user}.{round(time.time())}.json"),
                    'w') as f:
                json.dump(userdata, f)

            # Data

            print("\nExtracting data...\n")

            status = userdata[user]['status'].replace('@', '')  # No replies
            status = " ".join(status.split())
            status = status if len(status) < 200 else status[:200] + "[...]"

            # Viewers

            viewers = f"({userdata[user]['viewers']} viewers)"

            # Tags from Twitter accounts

            tags = " ".join([f"#{i}" for i in userdata[user]['twitter']])

            # Images

            imageurl = dirdata['image']
            print(f"Image url: {imageurl}")

            imagepath = os.path.join(IMAGESPATH, todaystr())
            if not os.path.exists(imagepath):
                os.makedirs(imagepath)

            imagefile = os.path.join(imagepath, os.path.basename(imageurl))
            with urlopen(imageurl) as r, open(imagefile, 'wb') as f:
                shutil.copyfileobj(r, f)
                print(f"Downloaded: {imagefile}")

            # Queue tweet in Qbot

            tweet = {
                'text': f"{status} {viewers} {url} {tags}",
                'image': imagefile
            }
            QBOT['messages'].append(tweet)
            with open(QBOTJSON, 'w') as f:
                json.dump(QBOT, f)
                print(f"Tweet: {tweet['text']}")
                print(f"Queued on Qbot: {QBOTJSON}")

            # Register

            CONFIG['promoted'][user]['count'] += 1
            CONFIG['promoted'][user]['last_promo'] = time.time()

            nowviewers = userdata[user]['viewers']

            maxviewers = CONFIG['promoted'][user]['max_viewers']
            CONFIG['promoted'][user]['max_viewers'] = max(
                nowviewers, maxviewers)

            minviewers = CONFIG['promoted'][user]['min_viewers']
            minviewers = nowviewers if minviewers < 1 else minviewers
            CONFIG['promoted'][user]['min_viewers'] = min(
                nowviewers, minviewers)

            with open(CONFIGJSON, 'w') as f:
                json.dump(CONFIG, f)

            # Just once
            break

    # The end
    print(f"\nDone! ({round(time.time() - DELTA)}s)")
    time.sleep(1)
