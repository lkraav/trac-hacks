= MileMixViewAdmin��� =

== ���� ==
 * http://trac-hacks.org/wiki/MileMixViewAdmin
 * Trac������Ʊ��ͼͳ����̱������״��,������ʾ���ӹ�ϵ�Ĵ�Ʊ��ϵ 

== ���� ==
 * [http://trac-hacks.org/wiki/WebAdminPlugin WebAdminPlugin]

== ���� ==

 1. ����ж�����а�װ.

 2. ִ��
  {{{
cp dist/*.egg /srv/trac/env/plugins
}}}

 3. ����trac.ini:
  {{{
[components]
rtadmin.* = enabled

[rtadmin]
base_path = /path/to/output/html/files    #/tracs/ctrl/keylist/KSTracMileMixView
exp_path = exp
}}}

== �÷� ==
 * Trac����Ա����Ҫ������ͼ����̱�:
  * ��Ϊ����Ա��¼, ��Admin -> Ticket System -> MileMixView
  * ѡ����Ҫ��Ӧ����̱�

== ���� ==

 * [/svn/zoomquiettranslation/plugins/KSTracMileMixViewAdmin SVB]
 * [source:zoomquiettranslation/plugins/KSTracMileMixViewAdmin ���]
