#!/bin/bash

echo - hack svn problem 
mv .svn ignoredir

echo - install
python setup.py install

echo - hack svn problem 
mv ignoredir .svn

echo - change permission
chmod -R o+r /usr/lib/python2.5/site-packages/*

echo - restart webserver
apache2ctl restart

