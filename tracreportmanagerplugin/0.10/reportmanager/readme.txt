= Trac������� =

== ���� ==
 * ���汨��
 * ����ʷ�лָ�����
 * ɾ��������ʷ��¼

== ��װ ==
 ����ͨ�õ�Trac�����װ����.

 1. ������Ѿ���װ���˲���Ĳ�ͬ�汾, ������ж��.

 2. �ҵ������setup.py.

 3. ����������ȫ�ְ�װ, �ò������װ��python��·����:
 {{{
python setup.py install
}}}

 4. �����ֻ��װ��trac��ʵ����:
 {{{
python setup.py bdist_egg
cp dist/*.egg /srv/trac/env/plugins
}}}

 5. ����trac.ini:
  {{{
[components]
reportmanager.* = enabled
}}}

== ���� ==

 * [/svn/zoomquiettranslation/plugins/KSTracReportManager SVN]

 * [source:zoomquiettranslation/plugins/KSTracReportManager ���]
