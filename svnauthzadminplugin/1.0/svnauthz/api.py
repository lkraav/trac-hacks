# -*- coding: utf-8 -*-

from trac.core import Component, ExtensionPoint, Interface


class ISvnAuthzChangeListener(Interface):

    def authz_changed(authz_file, old_authz):
        """Called when the authz file is changed."""


class SvnAuthzSystem(Component):

    change_listeners = ExtensionPoint(ISvnAuthzChangeListener)
