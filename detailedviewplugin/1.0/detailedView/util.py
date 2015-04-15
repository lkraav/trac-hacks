# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Jay Thomas
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from trac.ticket.model import Ticket
import re

#sortFields takes a list of dictionaries containing the ticket fields and returns
#two lists, the first one is field/label/type tuples, the second list is textarea
#name/label tuples

def sortFields(fields):

    # define field order
    field_name_sort = [
    "reporter", "owner",
    "baseline", "priority" ,
    "milestone", "perfective" ,
    "version", "blocking" ,
    "component", "blockedby" ,
    "tpr" , "clonedfrom" ,
    "testsite", "clonedin",
    "problemduplicated", "keywords",
    "csci", "test_event",
    "internal", "verifiedby",
    "uservisible", "versionverified",
    "sp_briefed", "versionfixed",
    "test_passed", "trbdate",
    "billable", "lccbdate",
    "qa_passed", "urgency",
    "usability", "safety",
    "external_pr",
     ]

    text_area_sort = [
    "description",
    "solution",
    "test_procedure",
    "sponsor_briefed",
    "safetycomment",
    "impact",
    "test_comment",
    "qa_comment"
    ]

    exclusion_list = ["id", "cc", "changetime", "time", "summary", "resolution", "status"]

    fieldAndLabel = []
    allTextAreas = []
    textAreas = []
    for name in field_name_sort:
        for item in fields:
            if item['name'] == name:
                fieldAndLabel.append([name,item['label'],item['type']])
                break

    for item in fields:
        if item['name'] not in field_name_sort and item['name'] not in exclusion_list:
            if item['type'] != 'textarea':
                fieldAndLabel.append([item['name'],item['label'],item['type']])
            else:
                allTextAreas.append(item['name'])

    for name in text_area_sort:
        for item in fields:
            if item['name'] == name:
                textAreas.append([name,item['label']])
                break

    for name in allTextAreas:
        if name not in text_area_sort:
            for item in fields:
                if name == item['name']:
                    textAreas.append([name, item['label']])

    return fieldAndLabel, textAreas

def formatTickets(string):
    t = re.sub("[^0-9\s]", "", str(string))
    t.replace(" ","\n")
    return t

def findClones(self,initialId,id,cloneTable,cloneList):

    intId = int(id)
    tkt = Ticket(self.env,intId)

    if intId not in cloneList:
        cloneList.append(intId)
        cloneTable.append( [ initialId,
                             intId,
                             formatTickets(tkt['clonedfrom']),
                             formatTickets(tkt['clonedin']),
                             tkt['summary'],tkt['baseline'],
                             tkt['milestone'],
                             tkt['status'],
                             tkt['resolution'] ] )

        if tkt['clonedin']:
            temp = tkt['clonedin'].split()
            for t in temp:
                newId = t.replace("#",'')
                findClones(self,initialId,newId,cloneTable,cloneList)

        if tkt['clonedfrom']:
            temp = tkt['clonedfrom'].split()
            for t in temp:
                newId = t.replace("#",'')
                findClones(self,initialId,newId,cloneTable,cloneList)
    if len(cloneTable) > 1:
        return cloneTable
    else:
        return None

