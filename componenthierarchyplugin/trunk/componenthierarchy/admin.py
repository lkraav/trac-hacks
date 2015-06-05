# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Thomas Doering, falkb
#
from genshi.builder import tag
from genshi.filters.transform import Transformer, InjectorTransformation
from genshi.input import HTML
from trac.util.text import to_unicode
from trac.core import *
from trac.web.api import ITemplateStreamFilter, IRequestFilter
from trac.web.chrome import add_script_data, add_script, add_notice
from trac.ticket import model
from trac.util.translation import _
from operator import itemgetter
import re

from componenthierarchy.model import *

class InsertParentTd(InjectorTransformation):
    """Transformation to insert the parent column into the component table"""
    _value = None
    _td = 0

    def __init__(self, content, all_comp):
        self._all_comp = all_comp
        super(InsertParentTd, self).__init__(content)

    def __call__(self, stream):

        for event in stream:
            mark, (kind, data, pos) = event
            if self._value:
                yield event  # Yield the event so the column is closed
                # Depending on the stream data may be '{http://www.w3.org/1999/xhtml}td' or just 'td'
                if mark == 'INSIDE' and kind == 'END' and data.endswith('td'):
                    # The end of a table column, tag: </td>
                    self._td += 1
                    if self._td ==3:
                        try:
                            self.content = tag.td(self._all_comp[self._value], class_="parent")
                        except KeyError:
                            self.content = tag.td(class_="parent")
                        self._value = None
                        self._td = 0
                        for n, ev in self._inject():
                            yield 'INSIDE', ev
            else:
                if mark == 'INSIDE' and kind == 'START' and data[0].localname == 'input':
                    if data[1].get('type') == u"checkbox":
                        self._value = data[1].get('value') or data[1].get('name')
                        self._td = 0
                yield event


class ComponentHierarchyAdminPanelFilter(Component):
    """Provides a selection box for a parent component on the component admin panel."""
    
    implements(ITemplateStreamFilter, IRequestFilter)

    def __init__(self):
        self._ChModel = ComponentHierarchyModel(self.env)

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        component_id = None
        match = re.match(r'/admin/ticket/components(?:/(.+))?$', req.path_info)
        if match:
            if match.group(1):
                component_id = match.group(1)

        if component_id and req.method == 'POST':
            parent = req.args.get('parent_component')
            name = req.args.get('name')

            if name != component_id:
                self._ChModel.rename_component(component_id, name)

            if parent == None or parent == "":
                 self._ChModel.remove_parent_component(name)
            else:
                 self._ChModel.set_parent_component(name, parent)
                
        return handler

    def post_process_request(self, req, template, data, content_type):
        return template, data, content_type

    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):

        if req.path_info.startswith('/admin/ticket/components/'):
            trans = Transformer('//form[@id="modcomp"]/fieldset/div[1]')
            stream = stream | trans.after(self._parent_component_select(req, data)) 

        elif req.path_info.startswith('/admin/ticket/components'):
            # add a "parent component" column to the components table
            stream = stream | Transformer('//table[@id="complist"]/thead/tr/th[3]').after(tag.th("Parent"))

            all_comp = {}
            for comp in [comp.name for comp in model.Component.select(self.env)]:
                parent_component = self._ChModel.get_parent_component(comp)
                if parent_component == None:
                    parent_component = ""
                all_comp[comp] = parent_component
            stream = stream | Transformer('//table[@id="complist"]//tr').apply(InsertParentTd("", all_comp))

        return stream

    def _parent_component_select(self, req, data):
        match = re.match(r'/admin/ticket/components/(.+)$', req.path_info)
        if match:
            component = match.group(1)
            all_components = [comp.name for comp in model.Component.select(self.env)]
            
            if component:
                cur_parent = self._ChModel.get_parent_component(component)
            else:
                cur_parent = None
    
            div = tag.div(class_='field')
            label = tag.label('%s:' % _('Parent Component'))
            label.append(tag.br())
            
            select = tag.select(id="parent_component", name="parent_component");
            for comp in sorted(all_components):
                if comp != component and not self._ChModel.is_child(component, comp):
                    # only show components that aren't children of the current one
                    if cur_parent and comp == cur_parent:
                        select.append(tag.option(comp, value=comp, selected="selected"))
                    else:
                        select.append(tag.option(comp, value=comp))
                
            label.append(select)
            div.append(label)
        
        return div
        
        