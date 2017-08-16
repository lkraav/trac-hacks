from trac.db import Table, Column

name = 'accreditation'
version = 1
tables = [
    Table(name)[
        Column('ticket', type='int'),
        Column('topic'),
        Column('conclusion'),
        Column('comment'),
        Column('author'),
    ],
]