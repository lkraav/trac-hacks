# -*- coding: utf-8 -*-

from trac.test import EnvironmentStub

from ticketref.api import TicketRefsPlugin
from ticketref.web_ui import TicketRefsTemplate

def pytest_addoption(parser):
    group = parser.getgroup("general")
    group.addoption('--envscope',
                    action="store", dest="envscope", default="module",
                    type="choice", choices=["module", "function"],
                    help=("set environment scope, default: module."))

def make_trac_environment_with_plugin():
    env = EnvironmentStub(
        enable=["trac.*", "ticketref.*", TicketRefsPlugin, TicketRefsTemplate])
    with env.db_transaction as db:
        TicketRefsPlugin(env).upgrade_environment(db)
    tref = TicketRefsPlugin(env)
    tmpl = TicketRefsTemplate(env)
    return env, tref, tmpl

def pytest_funcarg__env(request):
    setup = make_trac_environment_with_plugin
    scope = request.config.option.envscope
    env, tref, tmpl = request.cached_setup(setup=setup, scope=scope)
    return env

def pytest_funcarg__tref(request):
    setup = make_trac_environment_with_plugin
    scope = request.config.option.envscope
    env, tref, tmpl = request.cached_setup(setup=setup, scope=scope)
    return tref

def pytest_funcarg__tmpl(request):
    setup = make_trac_environment_with_plugin
    scope = request.config.option.envscope
    env, tref, tmpl = request.cached_setup(setup=setup, scope=scope)
    return tmpl
