= TracTweakUI��� =

== ���� ==
 * http://trac-hacks.org/wiki/TracTweakUI
 * Ϊʹ��javascript����Trac��UI�ṩ��������ƽ̨
 * ����Trac��Web���������, ����ÿһ��Trac���ڵĲ���

== ���� ==

 1. ����ж�����а�װ.

 2. ִ��
  {{{
cp dist/*.egg /srv/trac/env/plugins
}}}

 3. ����trac.ini:
  {{{
[components]
tractweakui.* = enabled
}}}

 4. ��Trac�Ļ�����htdocsĿ¼��, ��������Ŀ¼�ṹ:
  {{{
htdocs/tractweakui/
}}}

== ����javascript���editcc ==
 1. ��Trac����Ŀ¼�µ�htdocs/tractweakui/, ����Ŀ¼/�ļ��ṹ����:
   {{{
htdocs/tractweakui/editcc/__template__.js
htdocs/tractweakui/editcc/jquery.editcc.js
htdocs/tractweakui/editcc/jquery.editcc.css
htdocs/tractweakui/editcc/del.png
}}}
 1. ����Trac��Web������� -> TracTweakUI Admin
 1. ���� ·��(������ʽ): ^/newticket
 1. ����·�� ^/newticket, ѡ���г���filter
 1. �༭filter��JS�ű�, ������


== ���� ==

 * [/svn/zoomquiettranslation/plugins/KSTracTweakUI SVN]
 * [source:zoomquiettranslation/plugins/KSTracTweakUI ���]