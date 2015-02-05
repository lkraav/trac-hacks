# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Gefasoft AG
# Copyright (C) 2015 Franz Mayer <franz.mayer@gefasoft.de>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#


import StringIO
from operator import eq
import os.path
import re
from time import localtime

from babel.core import Locale
from genshi.builder import tag
import pkg_resources
from trac.config import ListOption, Option
from trac.core import Component, implements
from trac.versioncontrol.api import RepositoryManager
from trac.web import IRequestHandler
from trac.web.api import RequestDone
from trac.web.chrome import INavigationContributor, ITemplateProvider, add_warning, Chrome,\
    add_notice, add_script

import Permissions
import pysvn


class Translationmanager_Plugin(Component):
    """Main view for translation manager.

Translation manager plugin needs `pysvn` in order to submit changes to
Subversion. Unfortunately `pysvn` cannot be installed using `easy_install`.
Thus you need to install `pysvn` manually; on debian-based systems this
can be done by `apt-get`:

{{{#!sh
sudo apt-get install python-svn
}}}

@author: barbara.streppel
    """
    implements(INavigationContributor, IRequestHandler, ITemplateProvider)

    # Ansehen
    __keys = list()
    __lang_dict = {}
    __propdict = {}
    # {birt: [propdest_birt, checkout_folder_birt, /Legato], webapp: [...]}
    __dest_dict = {}

    # Importieren
    __up = ""
    __upload_content = []
    __dict_all_neu = {}
    __propdict_import = {}
    __error_dict = {}

    __target_folder = ""
    __double = []

    # Configuration options
    # Subversion options
    _repository = Option("translationmanager", "svn_repository", "/Legato")
    _checkout = Option(
        "translationmanager", "svn_url", "http://av-devdata-test/svn")
    _svn_register = Option("translationmanager", "svn_username", "barstr")
    _svn_password = Option("translationmanager", "svn_password", "bar#str")
    _comment = Option("translationmanager", "default_comment",
                      "{function} von Trac Translationmanager")

    # options for translation file destination
    _prop_dest = ListOption("translationmanager", "destination_folders",
                            "/WebApp/trunk/web/uploads/reports/birt, \
                            /WebApp/trunk/src/de/gefasoft/legato/webapp")
    _dest_desc = ListOption("translationmanager", "destination_descriptions",
                            "Birt, Webapp")
    _checkout_folder = ListOption("translationmanager", "checkout_folder",
                                  "/var/local/transman/checkout_birt, \
                                  /var/local/transman/checkout")

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        if Permissions.checkPermissionsView(self, req):
            return "Translationmanager"

    def get_navigation_items(self, req):
        if Permissions.checkPermissionsView(self, req):
            yield ("mainnav", "Translationmanager",
                   tag.a("Translationmanager", href=req.href.transmgr()))

    # IRequestHandler methods
    def match_request(self, req):
        return re.match(r'/transmgr' + '(?:/.*)?$', req.path_info)

    def process_request(self, req):
        add_script(req, 'hw/js/transmgr.js')
        Chrome(self.env).add_jquery_ui(req)

        perm = Permissions.whatPermission(self, req)
        self.log.info("permissions: %s" % perm)

        req.session["comment"] = ""
        if req.args.has_key("comment"):
            req.session["comment"] = req.args["comment"]

        def svn_login(realm, username, may_save):
            # Muss Rechte haben, um auf das SVN zugreifen zu können
            return True, self._svn_register, self._svn_password, False
        client = pysvn.Client()
        client.callback_get_login = svn_login

        self.log.info("path: %s" % req.path_info)
        self.log.info("up: %s" % self.__up)

        # Hintergrund bleibt, Import_dialog wird ausgefuehrt
        if req.args.has_key("Datei")\
                and req.path_info != "/transmgr/import-export.html" \
                and req.path_info != "/transmgr/extra.html":
            upload = req.args["Datei"]
            upload_content = []
            try:
                upload_content = upload.file.readlines()
                help_list = []
                for a in upload_content:
                    b = a.replace("\\", "\\\\")
                    self.log.info("content before coding: %s" % b)
                    help_list.append(b.decode("utf8"))
                self.__upload_content = help_list
                self.log.info("upload_content: %s" % self.__upload_content)
                self.__up = "durchsuchen"
            except Exception, e:
                self.log.error("Es wurde keine Datei ausgewählt: %s" % (e))
                msg = "Es wurde keine Datei ausgewählt oder der Dateityp wird nicht akzeptiert! Wählen Sie eine .txt- oder .csv-Datei"
                add_warning(req, msg.decode("utf-8"))

        elif req.args.has_key("coding") and req.path_info != "/transmgr/import-export.html" and req.path_info != "/transmgr/extra.html":
            self.__dict_all_neu = self.read_csv(self.__upload_content, req.args["coding"], int(
                req.args["start_import"]), req.args["seperator"], req.args["qualifier"])
            self.__up = "import_dialog"
            req.session["show"] = req.args["showing"]
            req.session.save()
            self.log.info("session show vorher: %s" % req.session["show"])
        elif self.__up == "break":
            None
        elif req.path_info != "/transmgr/import-export.html" and req.path_info != "/transmgr/extra.html":
            self.__up = ""

        for a in range(len(self._dest_desc)):
            whole_dest = []
            whole_dest.append(self._prop_dest[a])
            whole_dest.append(self._checkout_folder[a])
            whole_dest.append(self._repository)
            # TODO: refactor, since it is not loaded when changed
            self.__dest_dict[self._dest_desc[a]] = whole_dest

        if req.path_info == "/transmgr":
            self.log.info("up: %s" % self.__up)
            if self.__up == "":
                req.session.clear()
                self.log.info("Session deleted")

            if Permissions.checkPermissionsView(self, req):
                if req.args.has_key("ort"):  # ort = webapp oder birt
                    path = req.args["ort"]
                    req.session["path"] = path
                data = {"dest_dict": self.__dest_dict,
                        "perm": perm}
                return "tm-first.html", data, None

        elif req.path_info == "/transmgr/tm-start.html":

            if Permissions.checkPermissionsView(self, req):
                if req.args.has_key("ort"):  # ort = webapp oder birt
                    path = req.args["ort"]
                    req.session["path"] = path
                else:
                    path = req.session["path"]
                path_to_folder = self.__dest_dict[path][0]
                nodes = self.repository_open(
                    path_to_folder, self.__dest_dict[path][2])  # Funktionsaufruf
                self.__lang_dict = self.languages(nodes)
                data = {"lang_dict": self.__lang_dict,
                        "perm": perm}
                return "tm-start.html", data, None

        elif req.path_info == "/transmgr/tm-main.html":

            if Permissions.checkPermissionsView(self, req):
                double = []
                Herkunft = {}
                fuzzy = []
                readable = []  # liste mit allen keys, die readable sind
#                 req.session["main"] = "main"
                if req.args.has_key("ort"):
                    path = req.args["ort"]
                    req.session["path"] = path
                else:
                    path = req.session["path"]

                if req.args.has_key("exist"):
                    req.session["exist"] = req.args["exist"]

                if req.args.has_key("download"):  # Export
                    buf = StringIO.StringIO()
                    complete_first = []
                    all = []
                    m = len(self.__propdict)

                    for a in self.__propdict:  # 1.Zeile
                        e = re.search(r"_(.*)\.", a)
                        complete_first.append(e.group(1))

                    for i in self.__keys:  # Rest
                        complete = [i]
                        for e in self.__propdict:
                            for u in self.__propdict[e]:
                                if i == u:
                                    complete.append(self.__propdict[e][i])
                            if i not in self.__propdict[e]:
                                complete.append("")
                        all.append(complete)
                    self.log.info("all: %s" % all)
                    for i in range(0, len(self.__keys) + 1):
                        if i == 0:
                            content = "Bundle;Key"
                            for e in range(m):
                                if e < m - 1:
                                    content = content + ";" + complete_first[e]
                                elif e == m - 1:
                                    content = content + ";" + "dups" + \
                                        ";" + complete_first[e] + "\r\n"
                            buf.write(content)
                        else:
                            content = self.__dest_dict[path][0]
                            for e in range(m + 1):
                                if e < m:
                                    content = content + ";" + all[i - 1][e]
                                    self.log.info("content: %s" % content)
                                elif e == m:
                                    if all[i - 1][0] in self.__double:
                                        content = content + ";d;" + \
                                            all[i - 1][e] + "\r\n"
                                    else:
                                        content = content + ";;" + \
                                            all[i - 1][e] + "\r\n"
                                    self.log.info("content: %s" % content)
                            buf.write(content)
                    test_str = buf.getvalue()
                    req.send_header('Content-Type', 'text/plain')
                    req.send_header("Content-Length", len(test_str))
                    req.send_header(
                        "Content-Disposition", 'attachment; filename=export.csv')
                    req.end_headers()
                    req.send(
                        test_str.encode("utf-8"), 'text/comma-separated-values')
                    buf.close()
                    raise RequestDone()

                if req.args.has_key("ready"):  # von import kommend

                    req.session["exist"] = ""
                    req.session["main"] = "import"
                    Sprachen_im = []
                    self.__propdict = {}

                    all = self.__dict_all_neu
                    # zeilen wird listen in liste: [[1.Spalte], [2.Spalte],...]
                    zeilen = []
                    for a in range(0, len(all[0])):  # a ist spalte
                        spalten = []
                        for i in all:  # i ist zeile
                            spalten.append(all[i][a])
                        zeilen.append(spalten)
                    help_list = []
                    self.log.info(
                        "length import dict line 1: %s" % len(all[0]))

                    # zeilenumbrüche werden entfernt:
                    # zeilen[len(all[0])-1] ist letzte Spalte
                    for a in zeilen[len(all[0]) - 1]:
                        clear = re.search(r"(\S*)", a)
                        help_list.append(clear.group(1))
                    del zeilen[len(all[0]) - 1]
                    zeilen.append(help_list)

                    index_key = 0
                    index_im = []

                    if isinstance(req.args["lang"], list):  # dups ist immer da
                        for a in req.args["lang"]:
                            lang = re.search(r"(\S*)", a)
                            Sprachen_im.append(lang.group(1))
                        self.log.info("Sprachen_im: %s" % Sprachen_im)
                        for i in range(1, len(zeilen)):
                            if zeilen[i][0] == "Key":
                                index_key = i
                            # ausgewaehlte Sprachen und dups (dups wird beim
                            # einchecken nicht beachtet)
                            if zeilen[i][0] in Sprachen_im:
                                index_im.append(i)

                        self.__target_folder = self.__dest_dict[path][1]
                        path_to_folder = self.__dest_dict[path][0]
                        for a in Sprachen_im:
                            if a != "dups":
                                if re.search("birt", zeilen[0][1]):
                                    b = "gefasoft_" + a + ".properties"
                                    Sprachen_im[Sprachen_im.index(a)] = b
                                elif re.search("webapp", zeilen[0][1]):
                                    b = "messages_" + a + ".properties"
                                    Sprachen_im[Sprachen_im.index(a)] = b

                        self.__propdict_import = {}
                        for i in range(1, len(zeilen)):
                            if i != index_key and i in index_im:
                                y = zip(zeilen[index_key], zeilen[i])
                                dict_help = dict(y)
                                if dict_help.has_key("Key"):
                                    # da komplett mit erster Zeile eingelesen
                                    # -> erste zeile gelöscht
                                    del dict_help["Key"]
                                # bleibt noch drinnen für double, darf deswegen
                                # nicht umbenannt werden
                                if zeilen[i][0] == "dups":
                                    self.__propdict_import[
                                        zeilen[i][0]] = dict_help
                                else:
                                    if re.search("birt", zeilen[0][1]):
                                        # zeilen[i][0] ist nur de, en,... nicht
                                        # gefasoft_de.prop
                                        self.__propdict_import[
                                            "gefasoft_" + zeilen[i][0] + ".properties"] = dict_help
                                    elif re.search("webapp", zeilen[0][1]):
                                        self.__propdict_import[
                                            "messages_" + zeilen[i][0] + ".properties"] = dict_help
                                try:
                                    # i ist welche spalte, 0 de, 0:2 die ersten
                                    # beiden Buchstaben
                                    loc = Locale.parse(zeilen[i][0][0:2])
                                    if re.search("birt", zeilen[0][1]):
                                        self.__lang_dict[
                                            "gefasoft_" + zeilen[i][0] + ".properties"] = loc.get_display_name("de")
                                    elif re.search("webapp", zeilen[0][1]):
                                        self.__lang_dict[
                                            "messages_" + zeilen[i][0] + ".properties"] = loc.get_display_name("de")
                                    self.log.info(
                                        "lang_dict: %s" % self.__lang_dict)
                                except:
                                    None

                        nodes = self.repository_open(
                            path_to_folder, self.__dest_dict[path][2])
                        if req.session.has_key("show"):
                            self.log.info("session: %s" % req.session["show"])
                        # propdict_import nur neue; propdict abgeglichen mit
                        # svn
                        self.__propdict = self.update_with_svn(
                            self.__propdict_import, nodes, Sprachen_im)
                        keys_exist = []
                        keys_new = []
                        keys_no_value = []

                        for a in self.__propdict_import:
                            for i in self.__propdict_import[a]:
                                if self.__propdict_import[a][i] == "":
                                    if i not in keys_no_value:
                                        keys_no_value.append()

                        if req.session["show"] == "new":
                            keys_import = []
                            for a in zeilen[index_key][1:]:
                                self.log.info("a: %s" % a)
                                if a not in keys_import:
                                    keys_import.append(a)
                                    if a in self.__keys:
                                        keys_exist.append(a)
                                    else:
                                        keys_new.append(a)
                            self.__keys = keys_import
                            self.log.info("self.keys: %s" % self.__keys)
                        elif req.session["show"] == "all":
                            # in self.propdict ist noch dups mit drinnen
                            for a in self.__propdict_import:
                                self.log.info("a: %s" % a)
                                if a != "dups":
                                    for i in self.__propdict[a]:
                                        if i not in self.__keys:
                                            self.__keys.append(i)
                                            keys_new.append(i)
                                        else:
                                            keys_exist.append(i)

                        self.__error_dict["warning_exist"] = keys_exist
                        self.__error_dict["warning_new"] = keys_new
                        self.__error_dict["warning_no_value"] = keys_no_value

                        # Speicherort:
                        for a in range(1, len(zeilen[0])):
                            # origin = re.search("(\w+\..*$)", zeilen[0][a])
                            # Herkunft[zeilen[index_key][a]] = origin.group()
                            help_zeile = zeilen[0][a]
                            Herkunft[zeilen[index_key][a]] = help_zeile

                        msg = "Um die importierten Daten endgültig ins SVN zu übertragen, müssen Sie noch auf 'Einchecken' klicken. \n "
                        add_warning(req, msg.decode("utf-8"))
                    else:
                        msg = "Sie haben keine Spalte ausgewählt!"
                        add_warning(req, msg.decode("utf-8"))

                elif req.args.has_key("warning"):  # von warnung kommend
                    req.session["main"] = "import"
                    msg = "Um die importierten Daten endgültig ins SVN zu übertragen, müssen Sie noch auf 'Einchecken' klicken. \n "
                    add_warning(req, msg.decode("utf-8"))
                    warning = req.args["warning"]
                    self.log.info("error_dict vor aenderung: %s" %
                                  self.__error_dict)
                    for i in self.__error_dict[warning]:
                        if req.args.has_key(warning):
                            # req.args sind die ausgewählten, error_dict alle
                            if i not in req.args[warning]:
                                for u in self.__propdict_import:
                                    del self.__propdict[u][i]
                                    self.__keys.remove(i)
                    if self.__up == "break":
                        req.session["error"] = ""
                        self.__error_dict = {}
                        self.log.info("error_dict geloescht")
                        self.__up == ""

                elif req.args.has_key("main_to_main"):  # nach einchecken
                    self.log.info("target_folder: %s" % self.__target_folder)
                    nodes = self.repository_open(
                        self.__dest_dict[path][0], self.__dest_dict[path][2])

                    if os.path.exists(self.__target_folder):
                        client.update(self.__target_folder)
                        rev = client.info(self.__target_folder).revision.number
                        self.log.info("update to rev: %s" % rev)
                    else:
                        checkout = self._checkout + self._repository
                        # path falsch meiner Meinung!!!!!!!!!!!!!
                        client.checkout(checkout, self.__target_folder)

                    change_dict = {}
                    Sprachen_change = []
                    for key in req.args:
                        # key = key_from_properties bzw auch formtoken,...
                        change_dict[key] = req.args[key]
                        self.log.info("key: %s" % key)
                        if "_from_" in key:
                            x = key.split("_from_")
                            if x[1] not in Sprachen_change:
                                Sprachen_change.append(x[1])
                        self.log.info("Sprachen_change: %s" % Sprachen_change)
                    self.log.info("main: %s" % req.session["main"])
                    if req.session["main"] == "manuell":
                        self.__propdict = self.update_dict(
                            self.__propdict, change_dict)
                        msg = "Die Änderungen wurden erfolgreich eingecheckt"
                        add_notice(req, msg.decode("utf-8"))
                    elif req.session["main"] == "import":
                        helpdict = self.update_dict(
                            self.__propdict, change_dict)
                        # self.__keys werden auch akualisiert
                        self.__propdict = self.update_with_svn(
                            helpdict, nodes, Sprachen_change)
                        add_notice(
                            req, "Der Import wurde erfolgreich eingecheckt")

                    b = ""
                    for a in self.__propdict:
                        self.log.info("einzucheckende Sprache: %s" % a)
                        # kommt es von Import? Brauche ich das noch?
                        if ".properties" not in a:
                            # fr wird zu gefasoft_fr.properties
                            name2 = re.search("(\w*)", a)
                            if "birt" in self.__target_folder:
                                b = "gefasoft_" + \
                                    name2.group(1) + ".properties"
                            else:
                                b = "messages_" + \
                                    name2.group(1) + ".properties"
                        else:
                            # propdict hat einmal als key nur fr, einmal
                            # gefasoft_fr.properties
                            b = a

                        help_var = ""
                        if not os.path.isfile(self.__target_folder + "//" + b):
                            help_var = "no"

                        # file wird geschrieben, ob es vorher existiert hat
                        # oder nicht
                        self.write_prop(
                            self.__propdict[a], b, self.__target_folder)

                        if help_var == "no":
                            client.add(self.__target_folder + "//" + b)
                            self.log.info("File added: %s" % b)
                    if req.session["comment"] != "":
                        client.checkin(
                            [self.__target_folder], req.session["comment"])
                        self.log.info("Eingecheckt!")

                # nicht von Import und nicht einchecken
                elif req.session.has_key("path"):

                    path = req.session["path"]  # path = webapp oder birt
                    req.session.save()
                    path_to_folder = self.__dest_dict[path][0]
                    nodes = self.repository_open(
                        path_to_folder, self.__dest_dict[path][2])

                    # der "Rechtehalter" vom SVN muss auch die Rechte am
                    # Schreiben in dem Zielordner haben..
                    self.__target_folder = self.__dest_dict[path][1]

                    if Permissions.checkPermissionsView(self, req):
                        # von tm-start kommend
                        if req.args.has_key("start_to_main"):
                            # Für CheckIn-Comment
                            req.session["main"] = "manuell"
                            miss = []
                            Sprache = []  # Sprache definieren
                            if isinstance(req.args["Sprache"], basestring):
                                Sprache.append(req.args["Sprache"])
                            else:
                                Sprache = req.args["Sprache"]

                            # keys von allen in nodes, propdict nur für Sprache
                            self.__keys, self.__propdict = self.readout_all_info(
                                nodes, Sprache)
                            double, miss = self.double_miss(
                                Sprache, self.__propdict)

                            if req.args["see"] == "all":
                                None
                            else:
                                self.__keys = []
                                if "no_value" in req.args["see"]:
                                    self.__keys = miss
                                    self.log.info("miss: %s" % self.__keys)
                                if "double" in req.args["see"]:
                                    for a in double:
                                        self.__keys.append(a)
                                    self.log.info("double: %s" % self.__keys)

                        # neue Sprache hinzugefügt
                        elif req.args.has_key("add_lang"):
                            Sprache = []
                            if isinstance(req.args["Sprache"], basestring):
                                Sprache.append(req.args["Sprache"])
                            else:
                                Sprache = req.args["Sprache"]
                            for a in self.__propdict:
                                Sprache.append(a)
                            keys, new_propdict = self.readout_all_info(
                                nodes, Sprache)
                            self.__propdict.update(new_propdict)
                            double, miss = self.double_miss(
                                Sprache, self.__propdict)

                        elif req.args.has_key("del_lang"):  # Sprache löschen
                            Sprache = []
                            if isinstance(req.args["Sprache"], basestring):
                                Sprache.append(req.args["Sprache"])
                            else:
                                for a in req.args["Sprache"]:
                                    Sprache.append(a)
                            for a in Sprache:
                                self.__propdict.pop(a, None)
                            Sprache_new = []
                            for a in self.__propdict:
                                Sprache_new.append(a)
                            double, miss = self.double_miss(
                                Sprache_new, self.__propdict)

                        elif req.args.has_key("filter"):  # Filter setzen
                            Sprache = []
                            for a in self.__propdict:
                                Sprache.append(a)
                            self.__keys, new_propdict = self.readout_all_info(
                                nodes, Sprache)
                            double, miss = self.double_miss(
                                Sprache, new_propdict)
                            if req.args["see"] == "all":

                                self.__propdict.update(new_propdict)
                            else:
                                often = True
                                without = True
                                not_edit = False
                                if req.args["see"] == "own":
                                    if req.args["often"] == "ignore":
                                        often = False
                                    elif req.args["without"] == "ignore":
                                        without = False
                                    elif req.args["not_edit"] == "show":
                                        not_edit = True

                                if often and not without:
                                    self.log.info("nur doppelte")
                                    self.__keys = double
                                elif not often and without:
                                    self.log.info("nur miss")
                                    self.__keys = miss
                                elif often and without:
                                    self.log.info("beides")
                                    self.__keys = double + miss
                                if not not_edit:
                                    for a in self.__keys:
                                        if "$" in a:
                                            self.__keys.remove(a)
                                self.__propdict.update(new_propdict)

                        elif req.args.has_key("search"):  # suchen
                            y = []
                            what = req.args["what"]
                            case_sensitive = False
                            if req.args.has_key("case_sensitive"):
                                case_sensitive = req.args["case_sensitive"]
                            self.log.info("Alles oder Teil: %s" % what)
                            if "Value" in what:
                                self.log.info("Value")
                                x = self.searching(req.args["much"], self.__propdict, req.args[
                                                   "search_field"], "value", case_sensitive)  # Liste
                                for a in x:
                                    y.append(a)
                            if "Key" in what:
                                self.log.info("Key")
                                x = self.searching(req.args["much"], self.__keys, req.args[
                                                   "search_field"], "key", case_sensitive)  # liste
                                for a in x:
                                    y.append(a)
                            self.log.info("gefunden: %s" % y)
                            self.__keys = y

                if "dups" in self.__propdict:
                    for a in self.__propdict["dups"]:
                        if req.args.has_key("lang"):
                            # dups und eine Sprache sind immer dabei
                            if len(req.args["lang"]) > 2:
                                if self.__propdict["dups"][a] != "" and a != "dups":
                                    double.append(a)
                    del self.__propdict["dups"]

                for a in self.__keys:
                    if "$" in a:
                        readable.append(a)

                main = ""
                if req.session["main"] == "import":
                    main = "Import"
                elif req.session["main"] == "manuell":
                    main = "Manuelle Änderung"
                    msg = "Sie müssen auf 'Einchecken' klicken, damit die Änderungen an das SVN übergeben werden"
                    add_notice(req, msg.decode("utf-8"))

                self.__double = double

                percent = 100 / (len(self.__propdict) + 1)
                data = {"double": double,
                        "read": readable,
                        "fuzzy": fuzzy,
                        "key_list": self.__keys,
                        "propdict": self.__propdict,
                        "lang_dict": self.__lang_dict,
                        "main": main.decode("utf8"),
                        "perm": perm,
                        "origin": req.session["path"],
                        "percent": percent}

                return "tm-main.html", data, None

        # beide ohne permission, da sonst wrsl Fehlermeldung zwecks nicht
        # ladbar..
        if req.path_info == "/transmgr/import-export.html":
            dict_short = {}
            for a in self.__dict_all_neu:
                if a <= 2:
                    for u in self.__dict_all_neu[a]:
                        dict_short[a] = self.__dict_all_neu[a]
            data = {"up": self.__up,
                    "upload_content": self.__upload_content,
                    "dict_all_neu": dict_short,
                    "dest_dict": self.__dest_dict}

            return "import-export.html", data, None

        if req.path_info == "/transmgr/extra.html":
            path = ""
            if req.session.has_key("path"):
                path = req.session["path"]

            keys_short = list()
            if len(self.__keys) > 4:
                for i in range(0, 4):
                    keys_short.append(self.__keys[i])

            lt = localtime()
            jahr, monat, tag = lt[0:3]
            datum = str(tag) + "." + str(monat) + "." + str(jahr)

            u = 0
            req.session["error"] = ""
            self.log.info("error_dict: %s" % self.__error_dict)
            if self.__error_dict != {}:
                if self.__error_dict["warning_exist"] != []:
                    self.log.info("warning_exist")
                    req.session["error"] = "keys_exist"
                    u += 1
                    if req.session.has_key("exist"):
                        if req.session["exist"] == "first":
                            if self.__error_dict["warning_new"] != []:
                                req.session["error"] = "keys_new"
                                u += 1
                                if req.session["exist"] == "second":
                                    if self.__error_dict["warning_no_value"] != []:
                                        req.session["error"] = "keys_no_value"
                                        u += 1
                            elif self.__error_dict["warning_no_value"] != []:
                                req.session["error"] = "keys_no_value"
                                u += 1
                elif self.__error_dict["warning_new"] != []:
                    self.log.info("warning_new")
                    req.session["error"] = "keys_new"
                    u += 1
                    if req.session.has_key("exist"):
                        if req.session["exist"] == "second":
                            if self.__error_dict["warning_no_value"] != []:
                                req.session["error"] = "keys_no_value"
                                u += 1
                elif self.__error_dict["warning_no_value"] != []:
                    self.log.info("warning_no_value")
                    req.session["error"] = "keys_no_value"
                    u += 1
                req.session["main"] = "import"

            i = 0
            for a in self.__error_dict:
                if self.__error_dict[a] != []:
                    i += 1

            if i == u and u != 0:
                self.__up = "break"

            Sprachen = ["foo"]
            main = ""
            if req.session.has_key("main"):
                for a in self.__propdict:
                    if "foo" in Sprachen:
                        Sprachen.remove("foo")
                    if a not in Sprachen:
                        Sprachen.append(a)

                if req.session["main"] == "import":
                    main = "Import"
                elif req.session["main"] == "manuell":
                    main = "Manuelle Änderung"
#                 main = main.decode("utf-8")
                comment = self._comment.format(function=main.decode("utf-8"))

            nodes = self.repository_open(
                self.__dest_dict[req.session["path"]][0], self.__dest_dict[req.session["path"]][2])
            rest, propdict_svn = self.readout_all_info(nodes, Sprachen)

            user = req.authname
            data = {"lang_dict": self.__lang_dict,
                    "propdict": self.__propdict,
                    "keys_short": keys_short,
                    "Sprachen": Sprachen,
                    "path": path,
                    "comment": comment,
                    "error_dict": self.__error_dict,
                    "error": req.session["error"],
                    "user": user,
                    "prop_svn": propdict_svn}
            return "extra.html", data, None

    # ITemplateProvider methods
    def get_htdocs_dirs(self):  # for static resource directories
        return [('hw', pkg_resources.resource_filename('transmgr', 'htdocs'))]

    def get_templates_dirs(self):  # for template directories
        return [pkg_resources.resource_filename("transmgr", "templates")]

    # path = "/WebApp/trunk/src/de/gefasoft/legato/webapp"
    def repository_open(self, path, rep):
        rm = RepositoryManager(self.env)
        reponame, repos, path2 = rm.get_repository_by_path(rep)
        display = repos.get_node(path)
        nodes = display.get_entries()
        return nodes

    def languages(self, path):
        self.log.info("Pfad fuer lang: %s" % path)
        help_list = []  # messages_de.properties Liste
        languages = []  # deutsch Liste
        for i in path:
            if re.search(r"_.*\.properties", getattr(i, "name")):
                h = self.prop_to_languages(getattr(i, "name"))
                if h != None:
                    help_list.append(h)
                    languages.append(getattr(i, "name"))

        lang_list = zip(languages, help_list)
        help_dict = dict(lang_list)
        return help_dict

    def prop_to_languages(self, prop):
        self.log.info("prop open: %s" % prop)
        point = prop.find(".")
        uline = prop.find("_")

        if (point - uline) == 6:
            loc = Locale.parse(prop[uline + 1:point])
            lang_name = loc.get_display_name("de")
        elif (point - uline) == 3:
            loc = Locale(prop[uline + 1:point])
            lang_name = loc.get_display_name("de")
        else:
            None
        return lang_name  # String Deutsch

    def readout_all_info(self, nodes, Sprache):
        key_list = []
        key_list_unicode = []
        prop_dict = {}
        self.log.info("Sprache: %s" % Sprache)
        for n in nodes:
            if re.search("\.properties$", getattr(n, "name")) and not re.search(r"_user_", getattr(n, "name")):
                key_list_help, prop_dict_help = self.read_prop(n, Sprache)
                if getattr(n, "name") in Sprache:
                    prop_dict[getattr(n, "name")] = prop_dict_help
                for i in key_list_help:
                    if i not in key_list:
                        key_list.append(i)
        for a in key_list:
            key_list_unicode.append(a.decode("unicode_escape"))
        return key_list_unicode, prop_dict

    # aus messages_de.prop -> dict (key <-> value) aus der Sprache
    def read_prop(self, n, Sprache):
        node = n.get_content().read()
        lines = []
        if "\r\n" in node:
            lines = node.split("\r\n")
        else:
            lines = node.split("\n")
        keys = []
        nach = []
        prop_dict = {}
        for i in lines:
            if i == "\n":
                lines.remove(i)
            elif i == "":
                lines.remove(i)
        for i in lines:
            if not re.match("#", i):
                try:
                    x = re.search(r"([\w\.-]*[^ ]) *= *(.*)", i)
                    keys.append(x.group(1))
                    nach.append(x.group(2))
                except:
                    None
        for a in nach:
            if "\\:" in a or "\\=" in a or "\\ " in a or "\\\"" in a or "\\#" in a:
                b = ""
                if "\\:" in a:
                    # lis[lis.index('one')] = 'replaced!'
                    b = a.replace("\\:", ":")
                elif "\\=" in a:
                    b = a.replace("\\=", "=")
                elif "\\ " in a:
                    b = a.replace("\\ ", " ")
                elif "\\\"" in a:
                    b = a.replace("\\\"", "\"")
                elif "\\#" in a:
                    b = a.replace("\\#", "#")
                nach[nach.index(a)] = b
        if getattr(n, "name") in Sprache:
            y = zip(keys, nach)
            prop_dict_help = dict(y)
            prop_dict = {}
            for a in prop_dict_help:
                prop_dict[a] = prop_dict_help[a].decode("unicode_escape")
        return keys, prop_dict

    def double_miss(self, Sprache, propdict):
        for a in propdict.iterkeys():
            self.log.info("Keys vom propdict: %s" % a)
        double = []
        miss = []
        self.log.info("In double_all mit Sprache: %s" % Sprache)
        for i in range(0, len(Sprache) - 1):
            self.log.info("i: %s" % i)
            for n in range(1, len(Sprache) - i):
                self.log.info("n: %s" % n)
                for a in self.__keys:
                    if a in propdict[Sprache[i]] and a in propdict[Sprache[i + n]]:
                        if eq(propdict[Sprache[i]][a], propdict[Sprache[i + n]][a]):
                            if a not in double:
                                double.append(a)
                    else:
                        if a not in miss:
                            miss.append(a)

        if len(Sprache) == 1:
            for a in self.__keys:
                if a not in propdict[Sprache[0]]:
                    miss.append(a)

        return double, miss

    def update_dict(self, prop_dict, change_dict):
        self.log.info("changedict: %s" % change_dict)
        for a in change_dict:
            if "_from_" in a:
                x = a.split("_from_")
                key = x[0]
                origin = x[1]
                for ur in prop_dict:
                    if ur == origin:
                        prop_dict[ur].update({key: change_dict[a]})
        return prop_dict

    def update_with_svn(self, change_dict, nodes, Sprache):
        self.__keys, propdict_svn = self.readout_all_info(nodes, Sprache)
        for a in propdict_svn:
            self.log.info("propdict_svn: %s" % a)
        for a in change_dict:
            self.log.info("change_dict: %s" % a)
            if a in propdict_svn:
                # ist none -> nicht mit = mit etwas verbinden
                propdict_svn[a].update(change_dict[a])
            elif "_from_" in a:
                propdict_svn.update(change_dict)
        return propdict_svn

    # file ist liste; start_import ist int; seperator ist das entsprechende
    # Zeichen; qualifier ist hochkomma, double, none
    def read_csv(self, file, coding, start_import, seperator, qualifier):
        content = file[start_import - 1:len(file)]
        dict_all = {}
        for a in range(0, len(content)):
            if isinstance(seperator, basestring):
                dict_all[a] = re.split(seperator, content[a])
        dict_all_neu = {}
        for a in dict_all:  # a ist Zahl, value ist liste
            new_list = []
            for i in dict_all[a]:
                if qualifier == "hochkomma":
                    neu = "".join(re.findall("[^']", i))
                    new_list.append(neu)
                elif qualifier == "double":
                    neu = "".join(re.findall("[^\"]", i))
                    new_list.append(neu)
                else:
                    neu = i
                    new_list.append(neu)
                dict_all_neu[a] = new_list
        return dict_all_neu

    def searching(self, was, wo, string, was_genau, case_sensitive):
        y = []
        self.log.info("String: %s" % string)
        self.log.info("was: %s" % was)
        self.log.info("was_genau: %s" % was_genau)
        if was == "part":
            if was_genau == "key":
                for a in wo:
                    if case_sensitive:
                        if re.search(string, a):
                            y.append(a)
                    else:
                        if re.search(string, a, re.IGNORECASE):
                            y.append(a)
            if was_genau == "value":
                for a in wo:
                    for i in wo[a]:
                        if case_sensitive:
                            if re.search(string, wo[a][i]):
                                y.append(i)
                        else:
                            if re.search(string, wo[a][i], re.IGNORECASE):
                                y.append(i)
        if was == "whole":
            regex = r"\b" + re.escape(string) + r"\b"
            if was_genau == "key":
                for a in wo:
                    if case_sensitive:
                        if re.search(regex, a):
                            y.append(a)
                    else:
                        if re.search(regex, a, re.IGNORECASE):
                            y.append(a)
            if was_genau == "value":
                for a in wo:
                    for i in wo[a]:
                        if case_sensitive:
                            if re.search(regex, wo[a][i]):
                                y.append(i)
                        else:
                            if re.search(regex, wo[a][i], re.IGNORECASE):
                                y.append(i)
        return y

    # für checkout/checkin vom svn
    def write_prop(self, propdict_single, name, target_folder):
        words_help = {}
        words = {}

        for a in propdict_single:
            words_help[a] = propdict_single[a].encode("unicode_escape")
            words[a] = words_help[a].replace("\\x", "\\u00")
        prop_neu = open(target_folder + "/" + name, "w+")
        self.log.info("try to write file for %s" % name)
        for a in sorted(words):
            prop_neu.write(a + " = " + words[a] + "\r\n")
        prop_neu.close()
        return True
