#!/bin/bash
# install python egg SqlAlchemyQuery
TRAC_PATH_REPLACE="/absolute/path/to/your-trac-environment"
TRAC_REPLACE="your_trac_environment"
MAX_ROW_COUNT_REPLACE="1000"
TABLE_BORDER_REPLACE="border=\"1\""

if [ -d /$TRAC_PATH_REPLACE ]; then
	echo "Path exists continuing"
else
	echo "Path:\" " $TRAC_PATH_REPLACE " \" does not exists. Please edit this file and retry."
	exit
fi

if [ -d /$TRAC_PATH_REPLACE/htdocs ]; then
	echo "Path exists continuing"
else
	echo "Path:\" " $TRAC_PATH_REPLACE/htdocs " \" does not exists. Please check your trac installation, edit this file and retry."
	exit
fi

cp sorttable.js /$TRAC_PATH_REPLACE/htdocs
mkdir tmp
mkdir dist
cp SqlAlchemyQuery-0.1-py2.7.egg tmp
cd tmp
unzip SqlAlchemyQuery-0.1-py2.7.egg
rm SqlAlchemyQuery-0.1-py2.7.egg
cd sqlalchemyquery
cp ../../macro.py.bkp macro.py
sed -i "s#TRAC_PATH_REPLACE#$TRAC_PATH_REPLACE#g" macro.py
sed -i "s/TRAC_REPLACE/$TRAC_REPLACE/g" macro.py
sed -i "s/MAX_ROW_COUNT_REPLACE/$MAX_ROW_COUNT_REPLACE/g" macro.py
sed -i "s/TABLE_BORDER_REPLACE/$TABLE_BORDER_REPLACE/g" macro.py
cd ..
zip -r  SqlAlchemyQuery-0.1-py2.7.zip *
mv SqlAlchemyQuery-0.1-py2.7.zip  SqlAlchemyQuery-0.1-py2.7.egg
cp SqlAlchemyQuery-0.1-py2.7.egg /$TRAC_PATH_REPLACE/plugins
mv SqlAlchemyQuery-0.1-py2.7.egg ../dist
rm -r *
cd ..
rm -r tmp

echo "reboot your trac server: lsof | tracd, kill pid "
