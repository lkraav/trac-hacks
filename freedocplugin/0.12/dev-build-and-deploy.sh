#!/bin/sh
#
# License: BSDLike
# Rick van der Zwet <info@rickvanderzwet.nl>

TARGET=${1:-/usr/local/www/rickvanderzwet.nl/trac/tracs/personal/plugins/}
WEBSERVER_USER=${2:-www}

rm dist/*
python setup.py bdist_egg

NAME=`basename *.egg-info .egg-info`
sudo rm -v $TARGET/$NAME-*
sudo -u www cp dist/* $TARGET 

