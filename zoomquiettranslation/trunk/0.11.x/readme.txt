= ���ڱ���� =
�������ΪTrac 0.11.xĬ��wikiҳ����������İ汾, ����ҳ���ļ���λ��default-pagesĿ¼��.

����Trac 0.12��ʼ֧�ֹ��ʻ�, ������ǽ��ص������Trac 0.12�汾��i18n֧����.

Trac 0.11�Ƚ��ṩĬ��wikiҳ����������İ汾.

= ����/���� =
��trac-hacks.org����/���±������:
  {{{
svn co http://trac-hacks.org/svn/zoomquiettranslation/trunk/0.11.x
}}}

= ��װ =

 1. ��װĬ��wikiҳ�浽��Ŀ������, ִ������:
  {{{
trac-admin /path/to/your/env wiki load default-pages/
}}}

 2. ����trac.ini, ������������:
  {{{
[mainnav]
wiki.href = /wiki/ZhWikiStart

[metanav]
help.href = /wiki/ZhTracGuide
}}}

 * Ҳ���Բ���mainnav����, ʹ��Ĭ�ϵ�/wiki/WikiStart��Ϊ��ʵҳ.

 3. ����ZhTracGuideToc.py����Ŀ������pluginsĿ¼��.
