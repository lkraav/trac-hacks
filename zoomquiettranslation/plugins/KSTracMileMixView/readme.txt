= RelaTicket =

== ���� ==
 * http://trac-hacks.org/wiki/RelaTicket
 * �ýű��� [http://trac-hacks.org/wiki/RelaTicketAdmin RelaTicketAdmin] �ĸ����ű�.
 * ���ڶ������ɹ�����Ʊ��ͼHTML�ļ�.

== ���� ==
 * [http://adodb.sourceforge.net Python Adodb]
 * [http://www.advsofteng.com ChartDirector for Python]

== ���� ==
 1. �޸�ini.py��''Settings''
 {{{
    'rootpath':'/path/to/the/parent/of/trac/environment'
    ,'projname':'TracProjectName'	# trac1
    ,'dbname':'db/trac.db'
    ,'ticketurl':'/url/of/trac/ticket'	# http://trac.abc.com/trac1/ticket
    ,'reporturl':'/url/of/trac/report'	# http://trac.abc.com/trac1/report
}}}

 2. ����: ִ�����������, ��'exp'���Կ���������.
 {{{
python run_burndown.py
}}}

 3. ���ͨ�����ԣ���Ҫ�������������ӵ�crontab��.

== ���� ==

 * [/svn/zoomquiettranslation/plugins/KSTracRelaTicket SVN]

 * [source:zoomquiettranslation/plugins/KSTracRelaTicket ���]
