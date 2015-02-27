#!/bin/bash
# install python egg SqlAlchemyQuery
TRAC_PATH_REPLACE="trac-currencytrader"
USER="dbo_rsa"
MAX_ROW_COUNT_REPLACE="1000"
TABLE_BORDER_REPLACE="border=\"1\""
cp sorttable.js /home/$USER/$TRAC_PATH_REPLACE/htdocs
mkdir tmp
mkdir dist
cp SqlAlchemyQuery-0.1-py2.7.egg tmp
cd tmp
unzip SqlAlchemyQuery-0.1-py2.7.egg
rm SqlAlchemyQuery-0.1-py2.7.egg
cd sqlalchemyquery
cp ../../macro.py.bkp macro.py
sed -i "s/TRAC_PATH_REPLACE/$TRAC_PATH_REPLACE/g" macro.py
sed -i "s/MAX_ROW_COUNT_REPLACE/$MAX_ROW_COUNT_REPLACE/g" macro.py
sed -i "s/TABLE_BORDER_REPLACE/$TABLE_BORDER_REPLACE/g" macro.py
cd ..
zip -r  SqlAlchemyQuery-0.1-py2.7.zip *
mv SqlAlchemyQuery-0.1-py2.7.zip  SqlAlchemyQuery-0.1-py2.7.egg
cp SqlAlchemyQuery-0.1-py2.7.egg /home/$USER/$TRAC_PATH_REPLACE/plugins
mv SqlAlchemyQuery-0.1-py2.7.egg ../dist
rm -r *
cd ..
rm -r tmp

echo "reboot your trac server: lsof | tracd, kill pid "
