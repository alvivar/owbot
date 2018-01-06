"""
    Twitch.com data scrapper
    :D
"""

import json
import os
import sys
import time

from bs4 import BeautifulSoup

from selenium import webdriver


def selenium_get_html(url, chrome_driver, language=None):
    """
        Return the html source from the url using Selenium and the Chrome web
        driver. If language is specified (es, en, fr, etc) it will click on the
        language menu and change it (works only on directory pages).
    """

    driver = webdriver.Chrome(chrome_driver)
    driver.get(url)

    if language:  # Change the language by 'clicking' on the menu

        driver.find_element_by_xpath(
            "//div[contains(@class, 'language-select-menu')]").click()
        time.sleep(1)

        driver.find_element_by_xpath(
            f"//div[@class='tw-checkbox' and @data-language-code='{language}']"
        ).click()
        time.sleep(1)

    html = driver.page_source
    driver.quit()

    return html


def get_href_handler(htmlsource, href):
    """
        Return the last part of the first url found with the href parameter in
        any url link of the html.

        'lolirotve' from the url https://twitter.com/lolirotve when href is
        'twitter.com/'
    """

    soup = BeautifulSoup(htmlsource, "html.parser")

    for a in soup.find_all("a", href=True):
        if href in a["href"]:
            return a["href"].replace("/", " ").strip().split(" ")[-1]

    return False


def get_directory_data(htmlsource):
    """
        Return a dictionary with the data for each stream in a Twitch game
        directory page, like https://www.twitch.tv/directory/game/Overwatch
    """

    soup = BeautifulSoup(htmlsource, "html.parser")

    data = {}
    for html in soup.find_all("div", "stream-thumbnail"):

        image = html.find("img", src=True)
        image = image["src"] if image else False

        title = html.find("h3", class_="live-channel-card__title", title=True)
        title = title["title"] if title else False

        viewers = html.find("span", class_="tw-ellipsis")
        viewers = viewers.text.split(" ")[0] if viewers else False

        user = html.find("a", class_="live-channel-card__videos", href=True)
        user = user["href"].replace(
            "/", " ").strip().split(" ")[0] if user else False

        data[user] = {
            "image": image,
            "title": title,
            "viewers": viewers,
            "time": time.time()
        }

    return data


def get_user_data(htmlsource):
    """
        Return a dictionary with the user data on a Twitch.tv streamer page html
        source, like https://www.twitch.tv/chipshajen
    """

    soup = BeautifulSoup(htmlsource, "html.parser")

    data = {}

    user = soup.find("a", class_="channel-header__user").find("h5")
    user = user.text if user else False

    status = soup.find("span", {
        "data-a-target": "stream-title",
        "title": True
    })
    status = status["title"] if status else False

    viewers = soup.find("div", {
        "class": "tw-stat",
        "data-a-target": "channel-viewers-count"
    }).find("span", {
        "data-a-target": "tw-stat-value"
    })
    viewers = viewers.text if viewers else False
    viewers = "".join([c for c in viewers if c.isdigit()])

    total_views = soup.find("div", {
        "class": "tw-stat",
        "data-a-target": "total-views-count"
    }).find("span", {
        "data-a-target": "tw-stat-value"
    })
    total_views = total_views.text if total_views else False
    total_views = "".join([c for c in total_views if c.isdigit()])

    twitter = get_href_handler(htmlsource, "twitter.com/")
    instagram = get_href_handler(htmlsource, "instagram.com/")
    youtube = get_href_handler(htmlsource, "youtube.com/user/")

    data[user] = {
        "status": status,
        "twitter": twitter,
        "instagram": instagram,
        "youtube": youtube,
        "viewers": int(viewers),
        "total_views": int(total_views),
        "followers": "",
        "following": "",
        "videos_count": "",
        "tags": "",
        "time": time.time()
    }

    return data


if __name__ == "__main__":

    DELTA = time.time()

    # The current dir should be the script home, cxfreeze compatibility

    CDIR = os.path.normpath(
        os.path.dirname(
            sys.executable if getattr(sys, 'frozen', False) else __file__))
    os.chdir(CDIR)

    # Config

    CONFIGJSON = "config.json"

    try:
        CONFIG = json.load(open(CONFIGJSON, "r"))
    except (IOError, ValueError):
        CONFIG = {"config": {"chrome_driver_path": "chromedriver.exe"}}
        with open(CONFIGJSON, "w") as f:
            json.dump(CONFIG, f)

    # Driver

    CHROME = os.path.normpath(
        os.path.join(CDIR, CONFIG["config"]["chrome_driver_path"]))

    # Data

    # DATAES = get_directory_data(
    #     selenium_get_html(
    #         "https://www.twitch.tv/directory/game/Overwatch",
    #         CHROME,
    #         language="es"))

    # DATAEN = get_directory_data(
    #     selenium_get_html(
    #         "https://www.twitch.tv/directory/game/Overwatch",
    #         CHROME,
    #         language="en"))

    USERX = get_user_data(
        selenium_get_html("https://www.twitch.tv/gale_adelade", CHROME))

    # Scrap results

    # with open("overwatch_es.json", "w") as f:
    #     json.dump(DATAES, f)

    # with open("overwatch_en.json", "w") as f:
    #     json.dump(DATAEN, f)

    with open("userx.json", "w") as f:
        json.dump(USERX, f)

    # The end

    print(f"\nDone! ({round(time.time() - DELTA)}s)")
