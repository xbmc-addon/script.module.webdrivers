# -*- coding: utf-8 -*-

import sys

import xbmcplugin
import xbmcgui


def kinopoisk():
    from webdrivers.kinopoisk import KinoPoisk
    kinopoisk = KinoPoisk()
    #print str(kinopoisk.movies.info(597687))
    print str(kinopoisk.movies.info([251733, 597687]))


if sys.argv[2] == '?kinopoisk':
    kinopoisk()

xbmcplugin.addDirectoryItem(int(sys.argv[1]), sys.argv[0] + '?kinopoisk', xbmcgui.ListItem(label='KinoPoisk'), True)
xbmcplugin.endOfDirectory(int(sys.argv[1]))