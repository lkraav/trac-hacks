# -*- coding: utf-8 -*-
#
# Author: Ruth Trevor-Allen 2012, with a hat-tip to my former
# employers NAG Ltd, Oxford, UK.
#
# Do what you like with this code, however, I ask that you respect
# this one condition:
#
# *  The name of the author may not be used to endorse or promote
#    products derived from this software without specific prior
#    written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR `AS IS'' AND ANY EXPRESS
# OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
# GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Based on the file tracopt.ticket.commit_updater.py in Trac 0.12,
# which was licenced under the following terms:
#-------------------------------------------------------------------
# Copyright (C) 2003-2011 Edgewall Software
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 3. The name of the author may not be used to endorse or promote
#    products derived from this software without specific prior
#    written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR `AS IS'' AND ANY EXPRESS
# OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
# GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.org/wiki/TracLicense.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://trac.edgewall.org/log/.
# The Trac commit_updater plugin was based on the
# contrib/trac-post-commit-hook script, which had the following copyright
# notice:
# ----------------------------------------------------------------------------
# Copyright (c) 2004 Stephen Hansen
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
#   The above copyright notice and this permission notice shall be included in
#   all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
# ----------------------------------------------------------------------------

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

    Note that project names must not contain any whitespace characters. Project
    name matching is case insensitive.
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
