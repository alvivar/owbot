"""
    Twitch.tv + Overwatch data scrapper

    @matnesis
    2018/01/04
"""

import json
import os
import random
import re
import sys
import time
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

HOME = os.path.normpath(  # The script directory + cxfreeze compatibility
    os.path.dirname(
        sys.executable if getattr(sys, 'frozen', False) else __file__))

CONFIG = {}
CONFIGJSON = os.path.join(HOME, 'config-twitchscrapper.json')
try:
    CONFIG = json.load(open(CONFIGJSON, 'r'))
except (IOError, ValueError):
    CONFIG = {'config': {'chrome_driver_path': 'chromedriver.exe'}}
    with open(CONFIGJSON, 'w') as f:
        json.dump(CONFIG, f)


def get_twitch_html(url, language=None, closechat=False):
    """
        Return the html source from the Twitch.tv url using Selenium and Chrome
        web driver.

        If language is specified (es, en, fr, etc) it will click on the language
        menu and change it (works only on directory pages).

        If close chat is true, it will click the close chat toggle.
    """

    driver = webdriver.Chrome(
        os.path.join(HOME, CONFIG['config']['chrome_driver_path']))

    driver.maximize_window()
    driver.get(url)
    time.sleep(random.uniform(1, 4))

    try:
        if language:  # 'Click' the menu
            langmenu = "//div[contains(@class, 'language-select-menu')]"
            driver.find_element_by_xpath(langmenu).click()
            time.sleep(random.uniform(1, 4))

            langcheck = f"//div[contains(@class, 'tw-checkbox') and contains(@data-language-code, '{language}')]/label"
            WebDriverWait(driver, 10).until(
                ec.presence_of_element_located((By.XPATH, langcheck))).click()
            time.sleep(random.uniform(1, 4))

        if closechat:  # Click the collapse chat button
            togglecol = "//button[contains(@data-a-target, 'right-column__toggle-collapse-btn')]"
            driver.find_element_by_xpath(togglecol).click()
            time.sleep(random.uniform(1, 4))

    except NoSuchElementException:
        print(f"Clicking doesn't work on '{url}'")
        driver.quit()
        return False

    html = driver.page_source
    driver.quit()

    return html


def uniquelist(l):
    """
        Return the list without repeated elements and their original order.
    """
    unique = []
    for i in l:
        if i not in unique:
            unique.append(i)

    return unique


def get_href_handler(htmlsource, href, fullhref=False):
    """
        Return a list of the social handlers from all urls in the 'htmlsource'
        that contains 'href' in them, assuming that the social handler is the
        first keyword after the domain.

        https://twitter.com/lolirotve -> lolirotve
        https://www.youtube.com/JJoNaKLove -> JJoNaKLove

        If 'fullhref' is True, the complete url will be returned instead.
    """

    soup = BeautifulSoup(htmlsource, 'html.parser')

    found = []
    for a in soup.find_all('a', href=True):
        if href in a['href']:
            if fullhref:
                handler = a['href']
            else:
                url = urlparse(a['href'])
                handler = url.path.replace('/', ' ').strip().split()[0]
            found.append(handler.lower())

    return uniquelist(found)


def increase_image_resolution(url, sizeinc=200):
    """
        Return the same url with the hardcoded resolution increased.

        https://live_user_overwatchleague-320x180.jpg ->
        https://live_user_overwatchleague-520x380.jpg
    """
    resolution = re.split("-|\.", url)[-2]

    w, h = resolution.split('x')
    w = int(w) + sizeinc
    h = int(h) + sizeinc

    return url.replace(resolution, f"{w}x{h}")


def get_directory_data(url, language="en", increase_image=0):
    """
        Return a dictionary with the data for each stream in a Twitch.tv game
        directory page like https://www.twitch.tv/directory/game/Overwatch

        'increase_image' will force the hardcoded image to increase by the size.
    """

    htmlsource = get_twitch_html(url, language=language)
    if not htmlsource:
        return False

    soup = BeautifulSoup(htmlsource, 'html.parser')
    data = {}

    try:
        for html in soup.find_all('div', 'stream-thumbnail'):

            image = html.find('img', src=True)
            image = image['src'] if image else False
            if increase_image:
                image = increase_image_resolution(image, increase_image)

            status = html.find(
                'h3', class_='live-channel-card__title', title=True)
            status = status['title'] if status else False

            viewers = html.find('span', class_='tw-ellipsis')
            viewers = viewers.text.split(' ')[0] if viewers else False

            user = html.find(
                'a', class_='live-channel-card__videos', href=True)
            user = user['href'].replace(
                '/', ' ').strip().split(' ')[0] if user else False

            data[user] = {
                'image': image,
                'status': status,
                'viewers': viewers,
                'time': time.time()
            }
    except AttributeError:
        print(
            f"AttributeError: get_directory_data({url}, language='{language}')"
        )

    return data


def get_user_data(url):
    """
        Return a dictionary with the user data on a Twitch.tv streamer page like
        https://www.twitch.tv/chipshajen
    """

    htmlsource = get_twitch_html(url, closechat=True)
    if not htmlsource:
        return False

    soup = BeautifulSoup(htmlsource, 'html.parser')
    data = {}

    user = url.replace('/', ' ').strip().split(' ')[-1]

    status = soup.find('span', {
        'data-a-target': 'stream-title',
        'title': True
    })
    status = status['title'] if status else False

    try:
        viewers = soup.find('div', {
            'class': 'tw-stat',
            'data-a-target': 'channel-viewers-count'
        }).find('span', {
            'data-a-target': 'tw-stat-value'
        })
        viewers = viewers.text if viewers else False
        viewers = "".join([c for c in viewers if c.isdigit()])
    except AttributeError:
        viewers = -1

    try:
        total_views = soup.find('div', {
            'class': 'tw-stat',
            'data-a-target': 'total-views-count'
        }).find('span', {
            'data-a-target': 'tw-stat-value'
        })
        total_views = total_views.text if total_views else False
        total_views = "".join([c for c in total_views if c.isdigit()])
    except AttributeError:
        total_views = -1

    twitter = get_href_handler(htmlsource, "twitter.com/")
    instagram = get_href_handler(htmlsource, "instagram.com/")
    facebook = get_href_handler(htmlsource, "facebook.com/")
    youtube = get_href_handler(htmlsource, "youtube.com/", fullhref=True)
    discord = get_href_handler(htmlsource, "discord.gg/")

    try:
        followers = soup.find('a', {
            'data-a-target': 'followers-channel-header-item'
        }).find('div', {
            'class': 'channel-header__item-count'
        }).find('span')
        followers = followers.text if followers else False
        followers = "".join([c for c in followers if c.isdigit()])
    except AttributeError:
        followers = -1

    try:
        following = soup.find('a', {
            'data-a-target': 'following-channel-header-item'
        }).find('div', {
            'class': 'channel-header__item-count'
        }).find('span')
        following = following.text if following else False
        following = "".join([c for c in following if c.isdigit()])
    except AttributeError:
        following = -1

    try:
        videos = soup.find('a', {
            'data-a-target': 'videos-channel-header-item'
        }).find('div', {
            'class': 'channel-header__item-count'
        }).find('span')
        videos = videos.text if videos else False
        videos = "".join([c for c in videos if c.isdigit()])
    except AttributeError:
        videos = -1

    try:
        tags = soup.find('div', {
            'class': 'tw-card-body'
        }).find('div', {
            'class': 'tw-flex'
        }).find_all("p")
        tags = [i.text for i in tags]
    except AttributeError:
        tags = []

    data[user] = {
        'status': status,
        'twitter': twitter,
        'instagram': instagram,
        'facebook': facebook,
        'youtube': youtube,
        'discord': discord,
        'viewers': int(viewers),
        'total_views': int(total_views),
        'followers': int(followers),
        'following': int(following),
        'videos_count': int(videos),
        'tags': tags,
        'time': time.time()
    }

    return data


if __name__ == "__main__":

    # Testing

    DELTA = time.time()

    with open(os.path.join(HOME, "sample-directory-en.json"), "w") as f:
        json.dump(
            get_directory_data(
                "https://www.twitch.tv/directory/game/Overwatch",
                language="en",
                increase_image=200), f)

    with open(os.path.join(HOME, "sample-directory-es.json"), "w") as f:
        json.dump(
            get_directory_data(
                "https://www.twitch.tv/directory/game/Overwatch",
                language="es",
                increase_image=200), f)

    with open(os.path.join(HOME, "sample-user.json"), "w") as f:
        json.dump(get_user_data("https://www.twitch.tv/aimbotcalvin"), f)

    print(f"\nDone! ({round(time.time() - DELTA)}s)")
