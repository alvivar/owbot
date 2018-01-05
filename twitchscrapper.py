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


def selenium_get_html(url, chrome_driver, language="en"):
    """ Return the html source from the url using Selenium and the Chrome web
    driver. """

    driver = webdriver.Chrome(chrome_driver)
    driver.get(url)

    driver.find_element_by_xpath(
        "//div[@class='language-select-menu ']").click()
    driver.find_element_by_xpath(
        f"//div[@class='tw-checkbox' and @data-language-code='{language}']"
    ).click()
    time.sleep(1)

    html = driver.page_source

    driver.quit()

    return html


def get_directory_data(htmlsource):

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

    # Drivers

    CHROME = os.path.normpath(
        os.path.join(CDIR, CONFIG["config"]["chrome_driver_path"]))

    # Data

    HTMLES = selenium_get_html(
        "https://www.twitch.tv/directory/game/Overwatch",
        CHROME,
        language="es")
    DATAES = get_directory_data(HTMLES)

    HTMLEN = selenium_get_html(
        "https://www.twitch.tv/directory/game/Overwatch",
        CHROME,
        language="en")
    DATAEN = get_directory_data(HTMLEN)

    # Scrap

    with open("overwatch_es.json", "w") as f:
        json.dump(DATAES, f)

    with open("overwatch_en.json", "w") as f:
        json.dump(DATAEN, f)

    # The end

    print(f"\nDone! ({round(time.time() - DELTA)}s)")
