# -*- coding: utf-8 -*-
#
# Copyright (C) 2010 Roberto Longobardi
#

import calendar

from datetime import *
from calendar import Calendar

from trac.core import *
from trac.util import get_reporter_id
from trac.wiki.api import parse_args
from trac.wiki.macros import WikiMacroBase

from resreservation.api import ResourceReservationSystem
from resreservation.labels import *

# Macros

class ResourceReservationListMacro(WikiMacroBase):
    """Display a list of resource reservations.

    Usage:

    {{{
    [[ResourceReservationList(type=<resource type>, period=<num of months>, override=true|false)]]
    }}}
    
    All parameters are optional, with the following default values:
        type = defaulttype
        period = 3
        override = true, meaning that anyone can take on a resource reserved 
                   by someone else in any day by clicking on it. 
                   A value of false means the current owner must first cancel 
                   the reservation before anyone else can take the resource
    """
    def expand_macro(self, formatter, name, content):
        args, kw = parse_args(content)

        res_type = kw.get('type', 'defaulttype')
        period = int(kw.get('period', 3))
        title = kw.get('title', LABELS['default_resource_title'])
        override = kw.get('override', 'true')
        
        if override != 'true' and override != 'false':
            # Consider a misspelled value as the indication of 
            # willing to set it to false (the non-default value)
            override = 'false'

        req = formatter.req
        return _render_resreservation_list(self.env, req, res_type, period, title, override)
    

# Internal methods

def _render_resreservation_list(env, req, res_type, num_months, title, override):
    calendar.setfirstweekday(calendar.MONDAY)
    cal = calendar.Calendar()
    
    res_calendar = {}
    markup_per_resource = {}

    user = get_reporter_id(req)
    
    text = ''
    text += '<link rel="stylesheet" type="text/css" href="../chrome/resreservation/css/resreservation.css" />'
    text += '<script type="text/javascript">var baseLocation="'+req.href()+'";</script>'
    text += '<script type="text/javascript">var currUser="'+user+'";</script>'
    text += '<script type="text/javascript">var resourceType="'+res_type+'";</script>'
    text += '<script type="text/javascript">var override='+override+';</script>'
    text += '<script type="text/javascript" src="../chrome/resreservation/js/labels.js"></script>'
    text += '<script type="text/javascript" src="../chrome/resreservation/js/resreservation.js"></script>'
    
    text += '<div id="resReservationContainer">'
    
    text += '<table class="listing"><thead><tr>'
    text += '<th>'+title+'</th>'

    first_month = date.today().month
    last_month = first_month + num_months

    curr_year = date.today().year

    resource_reservation_system = ResourceReservationSystem(env)
    resources = resource_reservation_system.list_all_resources(res_type, _on_two_digits(curr_year)+'-'+_on_two_digits(first_month)+'-01', '9999-12-31')
    
    months = range(first_month, last_month)
    for i, month in enumerate(months):
        curr_month = month
    
        if curr_month > 12:
            curr_month -= 12
            curr_year += 1
        
        month_string = str(curr_month) #+'/'+str(curr_year)
        days = cal.itermonthdays(curr_year, curr_month)
        for day in days:
            if day == 0:
                continue

            text += '<th>'+str(day)+'/'+month_string+'</th>'

            for resource in resources:
                name = resource['name']
                
                if not name in markup_per_resource:
                    markup_per_resource[name] = []
                    
                while len(markup_per_resource[name]) <= i:
                    markup_per_resource[name].append([])
                    
                while len(markup_per_resource[name][i]) <= day-1:
                    markup_per_resource[name][i].append([])

                markup_per_resource[name][i][day-1] = '<td '+_get_class_by_weekday(date(curr_year, curr_month, day))+' name="'+_on_two_digits(curr_year)+'-'+_on_two_digits(curr_month)+'-'+_on_two_digits(day)+'"></td>'
            
    text += '</tr></thead><tbody id="resReservationTableBody" onclick="editResourceReservation(event)">'
    
    for resource in resources:
        name = resource['name']
        
        for reservation in resource['reservations']:
            assignee = reservation['assignee']
            date_from = reservation['res_from']
            date_to = reservation['res_to']
            
            curr_date = date_from
            while curr_date <= date_to:
                env.log.debug("   >>> curr_date = %s" % curr_date)
                curr_month = curr_date.month - first_month
                if curr_month < 0:
                    curr_month += 12
                
                className = ('resReserved', 'resOwned')[assignee == user]
                markup_per_resource[name][curr_month][curr_date.day-1] = '<td class="'+className+'" title="'+assignee+' '+_on_two_digits(curr_date.day)+'/'+_on_two_digits(curr_date.month)+' '+name+' '+'" name="'+_on_two_digits(curr_date.year)+'-'+_on_two_digits(curr_date.month)+'-'+_on_two_digits(curr_date.day)+'"></td>'

                curr_date += timedelta(days=1)

    for resource in resources:
        name = resource['name']
        
        markup = markup_per_resource[name]
        
        text += '<tr name="'+name+'"><td name="resourceNameCell">'+name+'</td>'
        
        for i in range(len(markup)):
            for j in range(len(markup[i])):
                text += markup[i][j]
                
        text += '</tr>'
            
    text += '</tbody></table>'

    text += '<div class="field" style="marging-top: 60px;"><br /><br />'

    text += '<label>'+LABELS['new_resource']+'</label>'
    text += '<span id="errorMsgSpan" style="color: red;" /><br />'
    text += '<input id="resName" name="resName" type="text" size="50"></input>'
    text += '<input type="button" value="'+LABELS['add_a_resource']+'" onclick="addResource()"></input>'
    text += '</div>'
    
    text += '</div>'

   
    return text
    

def _on_two_digits(val):
    return (str(val), '0'+str(val))[val<10]

    
def _get_class_by_weekday(date_val):
    if date_val.weekday() == 5 or date_val.weekday() == 6:
        return ' class="resHoliday" '
    else:
        return ' '

