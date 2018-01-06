"""
    Twitch.tv Overwatch data scrapper
    2018/01/06 12:02 am
"""

import json
import os
import sys
import time

from bs4 import BeautifulSoup

from selenium import webdriver


def get_twitch_html(url, chrome_driver, language=None, closechat=None):
    """
        Return the html source from the Twitch.tv url using Selenium and the
        Chrome web driver.

        If language is specified (es, en, fr, etc) it will click on the language
        menu and change it (works only on directory pages).

        If close chat, it will click the close chat toggle.
    """

    driver = webdriver.Chrome(chrome_driver)
    driver.maximize_window()
    driver.get(url)

    # Change the language by 'clicking' on the menu
    if language:

        langmenu = "//div[contains(@class, 'language-select-menu')]"
        driver.find_element_by_xpath(langmenu).click()
        time.sleep(1)

        langcheck = f"//div[@class='tw-checkbox' and @data-language-code='{language}']"
        driver.find_element_by_xpath(langcheck).click()
        time.sleep(1)

    if closechat:
        togglecol = "//button[contains(@data-a-target, 'right-column__toggle-collapse-btn')]"
        driver.find_element_by_xpath(togglecol).click()
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
    youtubeuser = get_href_handler(htmlsource, "youtube.com/user/")
    youtubechannel = get_href_handler(htmlsource, "youtube.com/channel/")
    discord = get_href_handler(htmlsource, "discord.gg/")

    followers = soup.find("a", {
        "data-a-target": "followers-channel-header-item"
    }).find("div", {
        "class": "channel-header__item-count"
    }).find("span")
    followers = followers.text if followers else False
    followers = "".join([c for c in followers if c.isdigit()])

    following = soup.find("a", {
        "data-a-target": "following-channel-header-item"
    }).find("div", {
        "class": "channel-header__item-count"
    }).find("span")
    following = following.text if following else False
    following = "".join([c for c in following if c.isdigit()])

    videos = soup.find("a", {
        "data-a-target": "videos-channel-header-item"
    }).find("div", {
        "class": "channel-header__item-count"
    }).find("span")
    videos = videos.text if videos else False
    videos = "".join([c for c in videos if c.isdigit()])

    data[user] = {
        "status": status,
        "twitter": twitter,
        "instagram": instagram,
        "youtube_user": youtubeuser,
        "youtube_channel": youtubechannel,
        "discord": discord,
        "viewers": int(viewers),
        "total_views": int(total_views),
        "followers": int(followers),
        "following": int(following),
        "videos_count": int(videos),
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

    DATAES = get_directory_data(
        get_twitch_html(
            "https://www.twitch.tv/directory/game/Overwatch",
            CHROME,
            language="es"))

    DATAEN = get_directory_data(
        get_twitch_html(
            "https://www.twitch.tv/directory/game/Overwatch",
            CHROME,
            language="en"))

    USERX = get_user_data(
        get_twitch_html(
            "https://www.twitch.tv/tytannia92", CHROME, closechat=True))

    # Scrap results

    with open("overwatch_es.json", "w") as f:
        json.dump(DATAES, f)

    with open("overwatch_en.json", "w") as f:
        json.dump(DATAEN, f)

    with open("userx.json", "w") as f:
        json.dump(USERX, f)

    # The end

    print(f"\nDone! ({round(time.time() - DELTA)}s)")
