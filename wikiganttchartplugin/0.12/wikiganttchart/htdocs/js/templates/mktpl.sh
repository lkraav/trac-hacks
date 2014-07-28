#!/bin/bash
# Easy script for generate template variables.

TEMPLATES_DIR=.
OUT=../gantt-templates.js

templates=
for file in `ls $TEMPLATES_DIR/*.html`
do
  tpl=`cat $file | sed -e 's/\"/\\\\\\"/g' | sed -e :loop -e 'N; $!b loop' -e 's/\n/\\\\n/g'`
  name=`echo $file | sed -e "s/^$TEMPLATES_DIR\/\\([^.]*\\)\\..*/\\1/"`
  templates="$templates\$.templates(\"$name\", \"$tpl\");"
done

echo $templates > $OUT
