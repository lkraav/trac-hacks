# -*- coding: utf-8 -*-

from model import AuthModel, Group, Path, PathAcl, User

PARSE_NORMAL = 0
PARSE_GROUPS = 1
PARSE_PATH_ACL = 2


class AuthzFileReader:

    def __init__(self):
        pass

    @staticmethod
    def read(filename):
        fp = open(filename, 'r')
        parser = AuthzFileParser(filename, fp)
        return parser.parse()


class AuthzFileWriter:

    def __init__(self):
        pass

    @staticmethod
    def write(filename, model):
        fp = open(filename, 'r')
        orig = fp.read()
        fp.close()
        new = model.serialize()
        if orig != new:
            fp = open(filename, 'w')
            fp.write(new)
            fp.close()


class AuthzFileParser:

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
        group_name, member_name = line.split('=')
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
        subject, acl = line.split('=')
        acl = [False, False]
        if acl is not None:
            if 'r' in acl:
                acl[0] = True
            if 'w' in acl:
                acl[1] = True
        subject = subject.strip()
        assert subject
        if subject.startswith('@'):
            assert subject
            subject = m.find_group(subject.lstrip('@'), True)
            assert subject is not None
        else:
            subject = User(subject)
        self.current_path.append(PathAcl(subject, *acl))
