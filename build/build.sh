#!/bin/sh
cd `dirname $0`/../src
cp -r ./* $HOME/Library/Application\ Support/XBMC/addons/script.module.webdrivers/

cp -r ../test/* $HOME/Library/Application\ Support/XBMC/addons/plugin.video.webdrivers.test/

#rm -f $HOME/.xbmc/temp/xbmcup/plugin.video.visionette/visionette.sql
