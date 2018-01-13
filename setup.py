""" Create an .exe with cx_Freeze, by calling 'python setup.py build'. """

from cx_Freeze import Executable, setup

OPTIONS = {
    'build_exe': {
        'includes': ['Queue.multiprocessing', 'idna.idnadata']
    }
}

EXECUTABLES = [Executable('owbot.py', targetName='owbot.exe')]

setup(
    name='owbot',
    version='0.1',
    description="Bot that tweets the best streamers from Twitch.tv",
    executables=EXECUTABLES,
    options=OPTIONS)
