# -*- coding: utf-8 -*-

try:
    from trac.db.api import with_transaction
    def get_read_db(env):
        return env.get_read_db()
except ImportError:
    try:
        import threading
    except ImportError:
        import dummy_threading as threading
        threading._get_ident = lambda: 0

    from trac.core import Component
    from trac.db.api import DatabaseManager

    class ThreadLocal(threading.local):
        def __init__(self, **kwargs):
            threading.local.__init__(self)
            self.__dict__.update(kwargs)

    class TransactionManager(Component):
        def __init__(self):
            self._transaction_local = ThreadLocal(db=None)

    def with_transaction(env, db=None):
        _transaction_local = TransactionManager(env)._transaction_local
        def transaction_wrapper(fn):
            ldb = _transaction_local.db
            if db is not None:
                if ldb is None:
                    _transaction_local.db = db
                    try:
                        fn(db)
                    finally:
                        _transaction_local.db = None
                else:
                    assert ldb is db, "Invalid transaction nesting"
                    fn(db)
            elif ldb:
                fn(ldb)
            else:
                ldb = _transaction_local.db = env.get_db_cnx()
                try:
                    fn(ldb)
                    ldb.commit()
                    _transaction_local.db = None
                except:
                    _transaction_local.db = None
                    ldb.rollback()
                    ldb = None
                    raise
        return transaction_wrapper

    def get_read_db(env):
        return TransactionManager(env)._transaction_local.db or \
               DatabaseManager(env).get_connection()
