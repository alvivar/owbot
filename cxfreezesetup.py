"""
    Run 'python cxfreezesetup.py build' to create a executable with cx_Freeze.
"""

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
    description=
    "Bot that collects and tweets the top Overwatch streamers from Twitch.tv",
    executables=EXECUTABLES,
    options=OPTIONS)
