#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""Youtubedlg __main__ file.

__main__ file is a python 'executable' file which calls the youtubedlg
main() function in order to start the app. It can be used to start
the app from the package directory OR it can be used to start the app
from a different directory after you have installed the youtube_dl_gui
package.

Example:
    In order to run the app from the package directory.

        $ cd <package director>
        $ python __main__.py

    In order to run the app from /usr/local/bin etc.. AFTER
    you have installed the package using setup.py.

        $ youtube-dl-gui

"""

from __future__ import unicode_literals

import gettext
import os.path
import sys

import wx
from formats import reload_strings
from logmanager import LogManager
from mainframe import MainFrame
from optionsmanager import OptionsManager
from utils import (
    get_config_path,
    get_locale_file,
    os_path_exists,
)


class youtube_dl_gui():
    __packagename__ = "youtube_dl_gui"
    # Set config path and create options and log managers
    config_path = get_config_path()

    opt_manager = OptionsManager(config_path)
    log_manager = None

    if opt_manager.options['enable_log']:
        log_manager = LogManager(config_path, opt_manager.options['log_time'])

    # Set gettext before MainFrame import
    # because the GUI strings are class level attributes
    locale_dir = get_locale_file()

    try:
        gettext.translation(__packagename__, locale_dir, [opt_manager.options['locale_name']]).install(unicode=True)
    except IOError:
        opt_manager.options['locale_name'] = 'en_US'
        gettext.install(__packagename__)

    reload_strings()


    def main(self):
        """The real main. Creates and calls the main app windows. """
        youtubedl_path = self.opt_manager.options["youtubedl_path"]

        app = wx.App()
        frame = MainFrame(self.opt_manager, self.log_manager)
        frame.Show()

        if self.opt_manager.options["disable_update"] and not os_path_exists(youtubedl_path):
            wx.MessageBox("Failed to locate youtube-dl and updates are disabled", "Error", wx.OK | wx.ICON_ERROR)
            frame.close()

        app.MainLoop()

if __package__ is None and not hasattr(sys, "frozen"):
    # direct call of __main__.py
    PATH = os.path.realpath(os.path.abspath(__file__))
    sys.path.append(os.path.dirname(os.path.dirname(PATH)))

if __name__ == '__main__':
    yt = youtube_dl_gui()
    yt.main()
