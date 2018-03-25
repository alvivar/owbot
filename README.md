# owbot

## Bot that collects and tweets the top Overwatch streamers from Twitch.tv

### Details

* **twitchscrapper.py** scraps data from a game directory and a user page
* **owbot.py** handles the scrap cycle, **#1** the **Overwatch** directory data, **#2** the top streamer data, **#3** queue a tweet about it using **[Qbot](https://github.com/alvivar/qbot)**, then waits before repeating again
* **[ChomeDriver](https://sites.google.com/a/chromium.org/chromedriver/)** is used through Selenium to obtain the html source because **Twitch.tv** is a **JavaScript** app
* You can use **'pyinstaller owbot.py --onefile'** to create a executable with **[pyinstaller](https://www.pyinstaller.org/)**
* Check it out! **[@overwatchbest](https://twitter.com/overwatchbest)**

### More details

```
owbot v0.1
usage: owbot.py [-h] [-s] [-w WAIT] [-b BAN] [-n]

Bot that collects and tweets the top Overwatch streamers from Twitch.tv

optional arguments:
  -h, --help            show this help message and exit
  -s, --start           start the cycle, find the top streamer and queue it in
                        Qbot
  -w WAIT, --wait WAIT  wait time between complete cycles, '1h' hours default,
                        0 or less to avoid repeating
  -b BAN, --ban BAN     wait time between republishing an account again, '7d'
                        days default
  -n, --now             starts immediately, ignoring the saved cycle delay
```
