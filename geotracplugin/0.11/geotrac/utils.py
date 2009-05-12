"""
DB utility functions
"""

from trac.db import DatabaseManager

class SQLHelper(object):

    def actions(self, cur):
        """do actions once you have execute the SQL"""
        return {}

    def return_values(self, **kw):
        """return values from the SQL"""

    def __call__(self, env, sql, *params):
        db = env.get_db_cnx()
        cur = db.cursor()
        try:
            cur.execute(sql, params)
            _data = self.actions(cur)
            db.commit()
        except Exception, e:
            env.log.error("""There was a problem executing sql:%s
with parameters:%s
Exception:%s""" %(sql, params, e))
            db.rollback()
        try:
            db.close()
        except:
            pass
        return self.return_values(**_data)

execute_non_query = SQLHelper()

class SQLGetAll(SQLHelper):
    def actions(self, cur):
        return dict(data=cur.fetchall(), desc=cur.description) 

    def return_values(self, **kw):
        return (kw.get('desc'), kw.get('data'))

get_all = SQLGetAll()


class SQLGetFirstRow(SQLHelper):
    def actions(self, cur):
        return dict(data=cur.fetchone())
    def return_values(self, **kw):
        return kw.get('data')

get_first_row = SQLGetFirstRow()

def get_scalar(env, sql, col=0, *params):
    """
    Gets a single value (in the specified column) 
    from the result set of the query
    """
    data = get_first_row(env, sql, *params)
    if data:
        return data[col]

class SQLGetColumn(SQLHelper):
    def actions(self, cur):
        return dict(data=[datam[0] for datum in cur.fetchall()])
    def return_values(self, **kw):
        return kw.get('data')
    def __call__(self, env, table, column):
        sql = "select %s from %s" % (column, table)
        return SQLHelper.__call__(self, sql)

get_column = SQLGetColumn()

def create_table(comp, table):
    """
    create a table given a component
    """

    db_connector, _ = DatabaseManager(comp.env)._get_connector()    
    stmts = db_connector.to_sql(table)
    for stmt in stmts:
        execute_non_query(comp, stmt)
