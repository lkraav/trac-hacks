# -*- coding: utf-8 -*-
from pkg_resources import resource_filename

from genshi.builder import tag
from trac.core import Component, implements
from trac.web.api import IRequestFilter, ITemplateStreamFilter
from trac.web.chrome import ITemplateProvider, add_script, add_stylesheet
from trac.resource import ResourceNotFound
from trac.ticket.model import Ticket
from trac.util.text import shorten_line
from trac.util.translation import domain_functions

from model import TICKETREF as TREF
from utils import cnv_text2list, get_diff_refs

_, add_domain = domain_functions("ticketref", ("_", "add_domain"))

TEMPLATE_FILES = [
    "query.html",
    "query_results.html",
    "report_view.html",
    "ticket.html",
    "ticket_box.html",
    "ticket_preview.html",
]

COPY_TICKET_FIELDS = [
    "cc",
    "component",
    "keywords",
    "milestone",
    "owner",
    "priority",
    "type",
    "version",
]

_dummy_catalog = _("added"), _("removed")


class TicketRefsTemplate(Component):
    """ Extend template for ticket cross-reference """

    implements(IRequestFilter, ITemplateProvider, ITemplateStreamFilter)
    _empty_list = []

    def __init__(self):
        add_domain(self.env.path, resource_filename(__name__, "locale"))

    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        if not (data and filename in TEMPLATE_FILES):
            return stream

        if filename.startswith("ticket"):
            self._filter_fields(req, data)

        if filename.startswith("query"):
            self._filter_groups(req, data)

        if filename == "report_view.html":
            self._filter_row_groups(req, data)

        for changes in data.get("changes", []):
            tref = changes.get("fields", {}).get(TREF)
            if tref:
                old, new = tref.get("old"), tref.get("new")
                msg_key, diff_ids = get_diff_refs(old, new)
                elements = [self._get_hyperlink_from_ticket(req, tkt_id)[0]
                            for tkt_id in diff_ids]
                if elements:
                    comma, f = tag.span(u', '), lambda x, y: x + comma + y
                    tref["rendered"] = reduce(f, elements)
                    tref["rendered"] += tag.span(u' ' + _(msg_key))
                tref["label"] = _("Relationships")

        return stream

    def _filter_fields(self, req, data):
        for field in data.get("fields", self._empty_list):
            if field["name"] == TREF:
                field["label"] = _("Relationships")
                ticket = data["ticket"]
                new = self._link_new(req, ticket, field)
                if ticket[TREF]:
                    field["rendered"] = self._link_refs(req, ticket[TREF],
                                                        verbose_link=True)
                    field["rendered"].append(new)
                else:
                    field["rendered"] = tag([new])

    def _filter_groups(self, req, data):
        fields_tref = data.get("fields", {}).get(TREF)
        if fields_tref:  # column checkbox/select option
            fields_tref["label"] = _("Relationships")
            if fields_tref["type"] == u"textarea":
                if isinstance(data.get("all_columns"), list):
                    data["all_columns"].append(TREF)

        # list view header
        for header in data.get("headers", self._empty_list):
            if header["name"] == TREF:
                header["label"] = _("Relationships")

        for group, tickets in data.get("groups", self._empty_list):
            for ticket in tickets:
                if TREF in ticket:
                    if TREF in data.get("row"):
                        ticket[TREF] = self._link_textarea(req, ticket[TREF])
                    else:  # expect TREF in data["col"]
                        ticket[TREF] = self._link_refs(req, ticket[TREF])

    def _filter_row_groups(self, req, data):
        for headers in data.get("header_groups", self._empty_list):
            for header in headers:
                if header["col"] == TREF:
                    header["title"] = _("Relationships")

        for group, rows in data.get("row_groups", self._empty_list):
            for row in rows:
                _is_list = isinstance(row["cell_groups"], list)
                if "cell_groups" in row and _is_list:
                    for cells in row["cell_groups"]:
                        for cell in cells:
                            if cell.get("header", {}).get("col") == TREF:
                                cell["value"] = self._link_refs(req,
                                                                cell["value"])

    def _get_hyperlink_from_ticket(self, req, ref_id):
        elem = verbose_elem = tag.span("#%s" % ref_id)
        try:
            ticket = Ticket(self.env, ref_id)
            if "TICKET_VIEW" in req.perm(ticket.resource):
                title = shorten_line(ticket["summary"])
                attr = {
                    "class_": ticket["status"],
                    "href": req.href.ticket(ref_id),
                    "title": title,
                }
                elem = tag.a("#%s" % ref_id, **attr)
                verbose_elem = tag.a("#%s %s" % (ref_id, title), **attr)
        except ResourceNotFound:
            self.log.warn("ticket not found: %s" % ref_id)
        return elem, verbose_elem

    def _link_refs(self, req, refs_text, verbose_link=False):
        items_tag = None
        items, verbose_items = [], []
        for ref_id in sorted(cnv_text2list(refs_text)):
            elm, verbose_elm = self._get_hyperlink_from_ticket(req, ref_id)
            items.extend([elm, ", "])
            verbose_items.extend([verbose_elm, tag.br()])
        if items:
            items_tag = [tag.span(items[:-1], id="tref_ticketid")]
            if verbose_link:
                vattr = {"id": "tref_summary", "class_": "tref-display-none"}
                items_tag.append(tag.span(verbose_items[:-1], **vattr))
        return tag(items_tag)

    def _link_textarea(self, req, refs_text):
        items = []
        for ref_id in sorted(cnv_text2list(refs_text)):
            elem = u"#%s" % ref_id
            try:
                ticket = Ticket(self.env, ref_id)
                if "TICKET_VIEW" in req.perm(ticket.resource):
                    title = shorten_line(ticket["summary"])
                    elem = u"#%s %s" % (ref_id, title)
            except ResourceNotFound:
                self.log.warn("ticket not found: %s" % ref_id)
            items.extend([elem, u", "])
        return u"".join(item for item in items[:-1])

    def _link_new(self, req, ticket, field):
        param = {TREF: ticket.id}
        param.update(dict([(i, ticket[i]) for i in COPY_TICKET_FIELDS
                     if ticket[i]]))
        attr = {
            "class_": "tref-link",
            "target": "_blank",
            "href": req.href.newticket(**param),
            "title": _("Open new ticket with relationships"),
        }
        return tag.a(_("New"), **attr)

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if req.path_info.startswith("/ticket/") or \
           req.path_info.startswith("/newticket"):
            add_stylesheet(req, "ticketref/ticket.css")
            add_script(req, "ticketref/ticket.js")
        return template, data, content_type

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        yield ("ticketref", resource_filename(__name__, "htdocs"))

    def get_templates_dirs(self):
        return []
