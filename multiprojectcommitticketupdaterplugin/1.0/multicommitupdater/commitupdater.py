# -*- coding: utf-8 -*-
#
# Copyright (C) 2003-2016 Edgewall Software
# Copyright (C) 2012 Ruth Trevor-Allen <fleeblewidget@gmail.com>
# Copyright (C) 2016 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import os
import re

from trac.config import BoolOption, Option
from tracopt.ticket.commit_updater import CommitTicketUpdater


class MultiProjectCommitTicketUpdater(CommitTicketUpdater):
    """Update tickets based on commit messages.

    Extending the functionality of CommitTicketUpdater, this component hooks
    into changeset notifications and searches commit messages for text in the
    form of:
    {{{
    command my-project:#1
    command my-project:#1, #2
    command my-project:#1 & #2
    command my-project:#1 and #2
    }}}

    You can have more than one command in a message. The following commands
    are supported. There is more than one spelling for each command, to make
    this as user-friendly as possible.

      close, closed, closes, fix, fixed, fixes::
        The specified tickets are closed, and the commit message is added to
        them as a comment.

      references, refs, addresses, re, see::
        The specified tickets are left in their current status, and the commit
        message is added to them as a comment.

    A fairly complicated example of what you can do is with a commit message
    of:

        Changed blah and foo to do this or that. Fixes my-project:#10 and
        #12, and refs my-other-project:#12.

    This will close #10 and #12 in my-project, and add a note to #12 in
    my-other-project.

    Note that project names must not contain any whitespace characters.
    Project name matching is case insensitive.
    """

    envelope = Option('ticket', 'commit_ticket_update_envelope', '',
        """Require commands to be enclosed in an envelope.

        Must be empty or contain two characters. For example, if set to "[]",
        then commands must be in the form of [closes #4].""")

    commands_close = Option('ticket', 'commit_ticket_update_commands.close',
        'close closed closes fix fixed fixes',
        """Commands that close tickets, as a space-separated list.""")

    commands_refs = Option('ticket', 'commit_ticket_update_commands.refs',
        'addresses re references refs see',
        """Commands that add a reference, as a space-separated list.

        If set to the special value <ALL>, all tickets referenced by the
        message will get a reference to the changeset.""")

    check_perms = BoolOption('ticket', 'commit_ticket_update_check_perms',
        'true',
        """Check that the committer has permission to perform the requested
        operations on the referenced tickets.

        This requires that the user names be the same for Trac and repository
        operations.""")

    notify = BoolOption('ticket', 'commit_ticket_update_notify', 'true',
        """Send ticket change notification when updating a ticket.""")

    short_name = Option('ticket', 'commit_ticket_update_short_name', '',
        """The name to use when referencing tickets using the
        !MultiProjectCommitTicketUpdater. The name should not contain
        whitespace.
        """)

    project_reference = '\S+:'
    whole_reference = ' ' + project_reference + CommitTicketUpdater.ticket_reference
    ticket_command = (r'(?P<action>[A-Za-z]*)\s*.?\s*'
                      r'(?P<ticket>%s(?:(?:[, &]*|[ ]?and[ ]?)%s)*)' %
                      (whole_reference, CommitTicketUpdater.ticket_reference))
    project_re = re.compile('(\S+):')

    def __init__(self):
        super(self, MultiProjectCommitTicketUpdater).__init__()
        if not hasattr(self.env, 'name'):
            self.env.name = os.path.basename(self.env.path)

    @property
    def project_name(self):
        return self.short_name or self.env.name

    def _parse_message(self, message):
        """Parse the commit message and return the ticket references."""
        cmd_groups = self.command_re.findall(message)
        functions = self._get_functions()
        tickets = {}
        for cmd, projects in cmd_groups:
            project_groups = self.project_re.split(projects)
            # Deal with blanks - should be one at the start
            while project_groups.count(' ') > 0:
                project_groups.remove(' ')
            # Project name is the first thing in the list, then tickets.
            name = project_groups.pop(0)
            if name.lower() == self.project_name.lower():
                func = functions.get(cmd.lower())
                if not func and self.commands_refs.strip() == '<ALL>':
                    func = self.cmd_refs
                if func:
                    tkts = project_groups.pop(0)
                    for tkt_id in self.ticket_re.findall(tkts):
                        tickets.setdefault(int(tkt_id), []).append(func)
        return tickets
