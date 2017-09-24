# -*- coding: utf-8 -*-

from api import SvnAuthzSystem
from model import AuthModel, Group, Path, PathAcl, User

PARSE_NORMAL = 0
PARSE_GROUPS = 1
PARSE_PATH_ACL = 2


class AuthzFile(object):

    def __init__(self, env, filename):
        self.env = env
        self.filename = filename

    def read(self):
        with open(self.filename, 'r') as fp:
            parser = AuthzFileParser(self.filename, fp)
            return parser.parse()

    def write(self, model):
        with open(self.filename, 'r') as fp:
            orig = fp.read()
        new = model.serialize()
        if orig != new:
            with open(self.filename, 'w') as fp:
                fp.write(new)
            for listener in SvnAuthzSystem(self.env).change_listeners:
                listener.authz_changed(self, orig)


class AuthzFileParser(object):

    def __init__(self, filename, fp):
        self.filename = filename
        self.fp = fp
        self.state = PARSE_NORMAL

    def parse(self):
        try:
            m = AuthModel(self.filename, [], [])
            self.state = PARSE_NORMAL
            self._parse_root(m)
            return m
        finally:
            self.fp.close()

    def _parse_root(self, m):
        while True:
            line = self.fp.readline()
            if line == '':
                break
            line = line.strip()
            if line.startswith('#'):
                # Ignore comments
                continue
            if not line:
                continue
            if line == '[groups]':
                self.state = PARSE_GROUPS
                continue
            else:
                if line.startswith('['):
                    self._parse_path(m, line)
                    self.state = PARSE_PATH_ACL
                    continue
            if self.state == PARSE_GROUPS:
                self._parse_group(m, line)
            else:
                if self.state == PARSE_PATH_ACL:
                    self._parse_path_acl(m, line)

    @staticmethod
    def _parse_group(m, line):
        group_name, member_name = line.split('=', 1)
        group_name = group_name.strip()
        g = m.find_group(group_name)
        if g is None:
            g = Group(group_name, [])
            m.add_group(g)

        member_name = member_name.strip()
        if not member_name:
            return
        if ',' in member_name:
            members = member_name.split(',')
        else:
            members = [member_name]
        for me in members:
            me = me.strip()
            if me.startswith('@'):
                member_group = m.find_group(me.lstrip('@'))
                if member_group is None:
                    member_group = Group(me.lstrip('@'), [])
                    m.add_group(member_group)
                g.append(member_group)
            else:
                g.append(User(me))

    def _parse_path(self, m, line):
        line = line.lstrip('[').rstrip(']')
        if ':' in line:
            repo, path = line.split(':')
            repo = repo.strip()
            path = path.strip()
        else:
            repo = None
            path = line.strip()
        self.current_path = Path(path, [], repo)
        assert(m.find_path(self.current_path) == [])
        m.add_path(self.current_path)

    def _parse_path_acl(self, m, line):
        subjectstr, aclstr = line.split("=")
        acl = [False, False]
        if aclstr is not None:
            if 'r' in aclstr:
                acl[0] = True
            if 'w' in aclstr:
                acl[1] = True
        subjectstr = subjectstr.strip()
        assert subjectstr
        if subjectstr.startswith('@'):
            assert len(subjectstr) > 1
            subject = m.find_group(subjectstr.lstrip('@'), True)
            assert subject is not None
        else:
            subject = User(subjectstr)
        self.current_path.append(PathAcl(subject, *acl))
