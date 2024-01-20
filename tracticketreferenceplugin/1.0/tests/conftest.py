# -*- coding: utf-8 -*-
import pytest

from trac.test import EnvironmentStub

from ticketref.api import TicketRefsPlugin
from ticketref.web_ui import TicketRefsTemplate

def make_trac_environment_with_plugin():
    env = EnvironmentStub(
        enable=["trac.*", "ticketref.*", TicketRefsPlugin, TicketRefsTemplate])
    with env.db_transaction as db:
        TicketRefsPlugin(env).upgrade_environment(db)
    tref = TicketRefsPlugin(env)
    tmpl = TicketRefsTemplate(env)
    return env, tref, tmpl

@pytest.fixture(scope="module")
def env(request):
    env, tref, tmpl = make_trac_environment_with_plugin()
    return env

@pytest.fixture(scope="module")
def tref(request):
    env, tref, tmpl = make_trac_environment_with_plugin()
    return tref

@pytest.fixture(scope="module")
def tmpl(request):
    env, tref, tmpl = make_trac_environment_with_plugin()
    return tmpl
