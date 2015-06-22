from trac.core import *

class Contact(object):
    def __init__(self, env, id=None):
        self.env = env
        if id:
            self.load_by_id(id)
        else:
            self.clear()

    def load_by_id(self, id):
        id = int(id)
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT first, last, position, email, phone FROM contact WHERE id = %s", (id,))
        row = cursor.fetchone()
        if not row:
            raise TracError('Contact with id %s does not exist.' % id)
        self.id = id
        self.first = row[0]
        self.last = row[1]
        self.position = row[2]
        self.email = row[3]
        self.phone = row[4]

    def clear(self):
        self.id = None
        self.first = None
        self.last = None
        self.position = None
        self.email = None
        self.phone = None

    def save(self):
        self.clean()
        if self.id:
            self.update()
        else:
            self.insert()

    def clean(self):
        import re
        p = re.compile(r'<.*?>')
        self.first = p.sub('', self.first)
        self.last = p.sub('', self.last)
        self.position = p.sub('', self.position)
        self.email = p.sub('', self.email)
        self.phone = p.sub('', self.phone)

    def update(self):
        if not self.id:
            raise TracError('Trying to update when there is no id!')
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("UPDATE contact SET first=%s, last=%s, position=%s, email=%s, phone=%s WHERE id=%s",
            (self.first, self.last, self.position, self.email, self.phone, self.id))
        db.commit()

    def insert(self):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("INSERT INTO contact (first, last, position, email, phone) VALUES (%s,%s,%s,%s,%s)",
            (self.first, self.last, self.position, self.email, self.phone))
        self.id = db.get_last_id(cursor, 'contact')
        db.commit()

    def last_first(self):
        return "%s, %s" % (self.last, self.first)

    def update_from_req(self, req):
        self.first = req.args.get('first')
        self.last = req.args.get('last')
        self.position = req.args.get('position')
        self.email = req.args.get('email')
        self.phone = req.args.get('phone')


_COLS = set(('id', 'first', 'last', 'position', 'email', 'phone'))


def ContactIterator(env, order_by = None):
    if not order_by:
        order_by = ('last', 'first')
    for name in order_by:
        if name not in _COLS:
            raise ValueError("Must be one of %r: %r" % (_COLS, name))

    db = env.get_db_cnx()
    if hasattr(db, 'quote'):
        quote = db.quote
    else:
        quote = lambda name: name
    cursor = db.cursor()

    cursor.execute("""
        SELECT id, first, last, position, email, phone
        FROM contact ORDER BY %s
        """ % ','.join(quote(v) for v in order_by))

    for id, first, last, position, email, phone in cursor:
        contact = Contact(env)
        contact.id = id
        contact.first = first
        contact.last = last
        contact.position = position
        contact.email = email
        contact.phone = phone
        yield contact
