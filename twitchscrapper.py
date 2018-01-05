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
    """ Return the html source from the url using Selenium and the Chrome web
    driver. If language is specified (es, en, fr, etc) it will click on the
    language menu and change it (works only on directory pages). """

    driver = webdriver.Chrome(chrome_driver)
    driver.get(url)

    # Change the menu language by 'clicking'
    if language:
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


def get_directory_data(htmlsource):
    """ Return a dictionary with the data for each stream in a Twitch game
    directory page, like https://www.twitch.tv/directory/game/Overwatch """

    soup = BeautifulSoup(htmlsource, "html.parser")

    data = {}
    for html in soup.find_all("div", "stream-thumbnail"):

        image = html.find("img", src=True)
        image = image["src"] if image else None

        title = html.find("h3", class_="live-channel-card__title", title=True)
        title = title["title"] if title else None

        viewers = html.find("span", class_="tw-ellipsis")
        viewers = viewers.text.split(" ")[0] if viewers else None

        user = html.find("a", class_="live-channel-card__videos", href=True)
        user = user["href"].replace(
            "/", " ").strip().split(" ")[0] if user else None

        data[user] = {
            "image": image,
            "title": title,
            "viewers": viewers,
            "time": time.time()
        }

    return data


def get_user_data(htmlsource):
    """ Return a dictionary with the user data on a Twitch.tv streamer page html
    source, like https://www.twitch.tv/chipshajen """

    soup = BeautifulSoup(htmlsource, "html.parser")

    data = {}

    status = soup.find("span", {
        "data-a-target": "stream-title",
        "title": True
    })
    status = status["title"] if status else None

    viewers = soup.find("div", {
        "class": "tw-stat",
        "data-a-target": "channel-viewers-count"
    }).find("span", {
        "data-a-target": "tw-stat-value"
    })
    viewers = viewers.text if viewers else None

    total_views = soup.find("div", {
        "class": "tw-stat",
        "data-a-target": "total-views-count"
    }).find("span", {
        "data-a-target": "tw-stat-value"
    })
    total_views = total_views.text if total_views else None

    data["userx"] = {
        "status": status,
        "twitter": "",
        "instagram": "",
        "viewers": viewers,
        "total_views": total_views,
        "followers": "",
        "following": "",
        "videos_count": "",
        "tags": "",
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
        selenium_get_html("https://www.twitch.tv/dafran", CHROME))

    # Scrap results

    # with open("overwatch_es.json", "w") as f:
    #     json.dump(DATAES, f)

    # with open("overwatch_en.json", "w") as f:
    #     json.dump(DATAEN, f)

    with open("userx.json", "w") as f:
        json.dump(USERX, f)

    # The end

    print(f"\nDone! ({round(time.time() - DELTA)}s)")
