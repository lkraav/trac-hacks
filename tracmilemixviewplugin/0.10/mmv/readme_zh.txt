= MMV��� =

== ���� ==
 * http://trac-hacks.org/wiki/MMV
 * Trac����ۺ���ͼ, ͳ����̱������״��,������ʾ���ӹ�ϵ�Ĵ�Ʊ��ϵ 

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
mmv.* = enabled

[mmv]
unplanned = [�ƻ���]
ticket_custom_due = duetime
show_burndown_done = false
enable_unplanned = true
enable_relaticket = true
mmv_title = MMV
}}}

== �÷� ==
 * Trac����Ա����Ҫ������ͼ����̱�:
  * ��Ϊ����Ա��¼, ��Admin -> Ticket System -> MMVTicket
  * ѡ����Ҫ��Ӧ����̱�

== ���� ==

 * [/svn/zoomquiettranslation/plugins/KSTracMMV SVN]
 * [source:zoomquiettranslation/plugins/KSTracMMV ���]
