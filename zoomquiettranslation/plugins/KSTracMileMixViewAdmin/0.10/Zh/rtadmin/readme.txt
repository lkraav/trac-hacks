= RelaTicketAdmin��� =

== ���� ==
 * http://trac-hacks.org/wiki/RelaTicketAdmin
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
base_path = /path/to/output/html/files    #/tracs/ctrl/keylist/KSTracRelaTicket/exp
}}}

== �÷� ==
 * Trac����Ա����Ҫ������ͼ����̱�:
  * ��Ϊ����Ա��¼, ��Admin -> Ticket System -> RelaTicket
  * ѡ����Ҫ��Ӧ����̱�

== ���� ==

 * [/svn/zoomquiettranslation/plugins/KSTracRelaTicketAdmin SVB]
 * [source:zoomquiettranslation/plugins/KSTracRelaTicketAdmin ���]
