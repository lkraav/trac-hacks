﻿# -*- coding: utf-8 -*-

# The MIT License
#
# Copyright (c) 2011 ben.12
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import sys
import os
import tempfile
import shutil
import time
import xlwt
from xlwt.Utils import rowcol_to_cell
import xlrd

# ticket #8805 : unavailable for python 2.4 or 2.5
# from io import BytesIO
import cStringIO


from trac import ticket
from trac import util
from trac.attachment import AttachmentModule
from trac.core import *
from trac.perm import IPermissionRequestor
from trac.ticket.admin import IAdminPanelProvider
from trac.ticket.api import TicketSystem
from trac.ticket.query import Query
from trac.ticket import model
from trac.ticket.model import Ticket
from trac.web.chrome import Chrome, ITemplateProvider, add_script

from importexportxls.formats import *


class ImportExportAdminPanel(Component):

    implements(ITemplateProvider, IPermissionRequestor, IAdminPanelProvider)

    _type = 'importexport'
    _label = ('Import/Export XLS', 'Import/Export XLS')

    def __init__(self):
        self.formats = {}
        self.formats['number'] = NumberFormat(self.config)
        self.formats['datetime'] = DateTimeFormat(self.config)
        self.formats['date'] = DateFormat(self.config)
        self.formats['text'] = TextFormat(self.config)
        self.formats['longtext'] = TextFormat(self.config, True)
        self.formats['boolean'] = BooleanFormat(self.config)

        self.exportForced = ['id', 'summary']
        self.importForbidden = ['id', 'summary', 'time', 'changetime']

    # IPermissionRequestor methods

    def get_permission_actions(self):
        return ['TICKET_ADMIN']

    def get_admin_panels(self, req):
        if 'TICKET_ADMIN' in req.perm:
            yield ('ticket', 'Ticket System', 'importexport', 'Import/Export XLS')

    def render_admin_panel(self, req, cat, page, version):
        req.perm.require('TICKET_ADMIN')

        template = 'importexport_webadminui.html'

        allfields = [ {'name':'id', 'label':'id'} ]
        allfields.extend( TicketSystem(self.env).get_ticket_fields() )
        customfields = TicketSystem(self.env).get_custom_fields()

        customfieldnames = [c['name'] for c in customfields]
        defaultfields = [c for c in allfields if c['name'] not in customfieldnames]

        # get configurations:
        fieldsFormat = self._get_fields_format(allfields)
        fieldsExport = self._get_fields_export(allfields)
        fieldsImport = self._get_fields_import(allfields)
        fieldsWeight = self._get_fields_weight(allfields)

        settings = {}

        if req.method == 'POST':
            # change custom fields excel types
            if req.args.get('save'):
                # clear actual config
                for name, value in self.config.options('import-export-xls'):
                    self.config.remove('import-export-xls', name)
                # change custom fields excel types
                for cf in customfields:
                    fmt = req.args.get(cf['name']+'.format', 'text')
                    self.config.set('import-export-xls', cf['name']+'.format', fmt)
                    fieldsFormat[cf['name']] = fmt
                # change fields exported and imported
                for cf in allfields:
                    fexport = bool( req.args.get(cf['name']+'.export', False) )
                    fimport = bool( req.args.get(cf['name']+'.import', False) )
                    fweight = 0
                    try:
                        fweight = int( req.args.get(cf['name']+'.weight', 0) )
                    except:
                        fweight = fieldsWeight[cf['name']]
                    if not fexport:
                        self.config.set('import-export-xls', cf['name']+'.export', fexport )
                    if not fimport:
                        self.config.set('import-export-xls', cf['name']+'.import', fimport )
                    self.config.set('import-export-xls', cf['name']+'.weight', fweight )
                    fieldsExport[cf['name']] = fexport
                    fieldsImport[cf['name']] = fimport
                    fieldsWeight[cf['name']] = fweight
                self.config.save()
            if req.args.get('export'):
                self._send_export(req)
            if req.args.get('import_preview'):
                (settings['tickets'], settings['importedFields'], settings['warnings']) = self._get_import_preview(req)
                template = 'importexport_preview.html'
                add_script(req, "importexportxls/importexport_preview.js")
            if req.args.get('import'):
                settings = self._process_import(req)
                template = 'importexport_done.html'

        if template == 'importexport_webadminui.html' and not req.args.get('export'):
            settings['types'] = [m.name for m in model.Type.select(self.env)]
            settings['versions'] = [m.name for m in model.Version.select(self.env)]
            settings['milestones'] = [m.name for m in model.Milestone.select(self.env, True)]
            settings['components'] = [m.name for m in model.Component.select(self.env)]
            settings['status'] = [m.name for m in model.Status.select(self.env)]
            settings['priorities'] = [m.name for m in model.Priority.select(self.env)]
            settings['severities'] = [m.name for m in model.Severity.select(self.env)]
            settings['resolutions'] = [m.name for m in model.Resolution.select(self.env)]
            settings['fieldsWeight'] = fieldsWeight
        settings['defaultfields'] = defaultfields
        settings['customfields'] = customfields
        settings['formats'] = self.formats
        settings['fieldsFormat'] = fieldsFormat
        settings['fieldsExport'] = fieldsExport
        settings['fieldsImport'] = fieldsImport
        settings['exportForced'] = self.exportForced
        settings['importForbidden'] = self.importForbidden
        settings['req'] = req
        if hasattr(Chrome, 'jenv'):
            return template, settings, None
        else:
            return template, settings

    # ITemplateProvider methods

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('importexportxls', resource_filename(__name__, 'htdocs'))]

    def _get_fields_format(self, fields = None):
        fieldsFormat = {}

        allfields = [ {'name':'id', 'label':'id'} ]
        allfields.extend( TicketSystem(self.env).get_ticket_fields() )
        customfields = TicketSystem(self.env).get_custom_fields()

        customfieldnames = [c['name'] for c in customfields]
        defaultfields = [c for c in allfields if c['name'] not in customfieldnames]

        defaultfieldnames = [c['name'] for c in defaultfields]

        fields = fields or allfields
        fieldnames = [f['name'] for f in fields]

        for cf in customfields:
            if cf['name'] in fieldnames:
                fieldsFormat[cf['name']] = self.config.get('import-export-xls', cf['name']+'.format', 'text')

        for fd in defaultfields:
            if fd['name'] in fieldnames:
                ftype = 'text'
                if fd['name'] in ['id']:
                    ftype = 'number'
                elif fd['name'] in ['time', 'changetime']:
                    ftype = 'datetime'
                elif fd['name'] in ['summary', 'description']:
                    ftype = 'longtext'
                fieldsFormat[fd['name']] = ftype

        return fieldsFormat


    def _get_fields_export(self, fields = None):
        fieldsExport = {}

        fieldnames = [f['name'] for f in fields]

        allfields = [ {'name':'id', 'label':'id'} ]
        allfields.extend( TicketSystem(self.env).get_ticket_fields() )
        customfields = TicketSystem(self.env).get_custom_fields()

        customfieldnames = [c['name'] for c in customfields]
        defaultfields = [c for c in allfields if c['name'] not in customfieldnames]

        defaultfieldnames = [c['name'] for c in defaultfields]

        fields = fields or allfields
        fieldnames = [f['name'] for f in fields]

        for cf in customfields:
            if cf['name'] in fieldnames:
                fieldsExport[cf['name']] = self.config.getbool('import-export-xls', cf['name']+'.export', True)

        for fd in defaultfields:
            if fd['name'] in fieldnames:
                fieldsExport[fd['name']] = self.config.getbool('import-export-xls', fd['name']+'.export', True)

        for fd in self.exportForced:
            fieldsExport[fd] = True

        return fieldsExport

    def _get_fields_import(self, fields = None):
        fieldsImport = {}

        allfields = [ {'name':'id', 'label':'id'} ]
        allfields.extend( TicketSystem(self.env).get_ticket_fields() )
        customfields = TicketSystem(self.env).get_custom_fields()

        customfieldnames = [c['name'] for c in customfields]
        defaultfields = [c for c in allfields if c['name'] not in customfieldnames]

        defaultfieldnames = [c['name'] for c in defaultfields]

        fields = fields or allfields
        fieldnames = [f['name'] for f in fields]

        for cf in customfields:
            if cf['name'] in fieldnames:
                fieldsImport[cf['name']] = self.config.getbool('import-export-xls', cf['name']+'.import', True)

        for fd in defaultfields:
            if fd['name'] in fieldnames:
                fieldsImport[fd['name']] = self.config.getbool('import-export-xls', fd['name']+'.import', True)


        for fd in self.importForbidden:
            fieldsImport[fd] = False

        return fieldsImport

    def _get_fields_weight(self, fields = None):
        fieldsWeight = {}

        allfields = [ {'name':'id', 'label':'id'} ]
        allfields.extend( TicketSystem(self.env).get_ticket_fields() )
        customfields = TicketSystem(self.env).get_custom_fields()

        customfieldnames = [c['name'] for c in customfields]
        defaultfields = [c for c in allfields if c['name'] not in customfieldnames]

        defaultfieldnames = [c['name'] for c in defaultfields]

        fields = fields or allfields
        fieldnames = [f['name'] for f in fields]

        for cf in customfields:
            if cf['name'] in fieldnames:
                fieldsWeight[cf['name']] = self.config.getint('import-export-xls', cf['name']+'.weight', 0)

        for fd in defaultfields:
            if fd['name'] in fieldnames:
                fieldsWeight[fd['name']] = self.config.getint('import-export-xls', fd['name']+'.weight', 0)

        return fieldsWeight

    def _send_export(self, req):
        from trac.web import RequestDone
        content, output_type = self._process_export(req)

        req.send_response(200)
        req.send_header('Content-Type', output_type)
        req.send_header('Content-Length', len(content))
        req.send_header('Content-Disposition', 'filename=tickets.xls')
        req.end_headers()
        req.write(content)
        raise RequestDone

    def _process_export(self, req):
        fields = [ {'name':'id', 'label':'id'} ]
        fields.extend( TicketSystem(self.env).get_ticket_fields() )
        fieldsFormat = self._get_fields_format(fields)
        fieldsExport = self._get_fields_export(fields)
        fieldsWeight = self._get_fields_weight(fields)

        comment_changeset = req.args.get('export.changeset') and req.args.get('export.changeset') == 'True'

        fields = [c for c in fields if fieldsExport[ c['name'] ] ]
        fieldnames = [c['name'] for c in fields]

        fields.sort( lambda a, b : fieldsWeight[a['name']]-fieldsWeight[b['name']] )

        # ticket #8805 : unavailable for python 2.4 or 2.5
        #content = BytesIO()
        content = cStringIO.StringIO()

        headerStyle = xlwt.easyxf('font: bold on; pattern: pattern solid, fore-colour grey25; borders: top thin, bottom thin, left thin, right thin')

        wb = xlwt.Workbook()
        sheetName = ( 'Tickets - %s' % self.config.get('project','name', '') );
        try:
          ws = wb.add_sheet( sheetName )
        except:
          # Project name incompatible with sheet name constraints.
          sheetName = 'Tickets'
          ws = wb.add_sheet( sheetName )

        colIndex = {}
        c = 0
        for f in fields:
            ws.write(0, c, unicode(f['label']),headerStyle)
            colIndex[f['name']] = c
            c += 1
        if comment_changeset:
            ws.write(0, c, unicode('Comments in change log'),headerStyle)

        constraints = {}
        if req.args.get('filter.type') and len(req.args['filter.type']) > 0 :
            if type( req.args['filter.type'] ) == list :
                constraints['type'] = req.args['filter.type']
            else:
                constraints['type'] = [ req.args['filter.type'] ]

        if req.args.get('filter.version') and len(req.args['filter.version']) > 0 :
            if type( req.args['filter.version'] ) == list :
                constraints['version'] = req.args['filter.version']
            else:
                constraints['version'] = [ req.args['filter.version'] ]

        if req.args.get('filter.milestone') and len(req.args['filter.milestone']) > 0 :
            if type( req.args['filter.milestone'] ) == list :
                constraints['milestone'] = req.args['filter.milestone']
            else:
                constraints['milestone'] = [ req.args['filter.milestone'] ]

        if req.args.get('filter.component') and len(req.args['filter.component']) > 0 :
            if type( req.args['filter.component'] ) == list :
                constraints['component'] = req.args['filter.component']
            else:
                constraints['component'] = [ req.args['filter.component'] ]

        if req.args.get('filter.status') and len(req.args['filter.status']) > 0 :
            if type( req.args['filter.status'] ) == list :
                constraints['status'] = req.args['filter.status']
            else:
                constraints['status'] = [ req.args['filter.status'] ]

        if req.args.get('filter.priority') and len(req.args['filter.priority']) > 0 :
            if type( req.args['filter.priority'] ) == list :
                constraints['priority'] = req.args['filter.priority']
            else:
                constraints['priority'] = [ req.args['filter.priority'] ]

        if req.args.get('filter.severity') and len(req.args['filter.severity']) > 0 :
            if type( req.args['filter.severity'] ) == list :
                constraints['severity'] = req.args['filter.severity']
            else:
                constraints['severity'] = [ req.args['filter.severity'] ]

        if req.args.get('filter.resolution') and len(req.args['filter.resolution']) > 0 :
            if type( req.args['filter.resolution'] ) == list :
                constraints['resolution'] = req.args['filter.resolution']
            else:
                constraints['resolution'] = [ req.args['filter.resolution'] ]

        query = Query(self.env, cols=fieldnames, order='id', max=sys.maxint, constraints=constraints)
        results = query.execute(req)
        r = 0
        cols = query.get_columns()
        for result in results:
            r += 1
            for col in cols:
                value = result[col]
                format = self.formats[ fieldsFormat[col] ]
                value = format.convert(value)
                style = format.get_style(value)
                ws.write(r, colIndex[col], value, style)
            if comment_changeset:
                format = self.formats[ 'longtext' ]
                value = format.convert( self._get_changelog_comments(result['id']) )
                style = format.get_style(value)
                ws.write(r, len(cols), value, style)

        if req.args.get('export.statistics') and req.args.get('export.statistics') == 'True':
            wb = self._add_statistics_sheet(req, sheetName, wb, fields, colIndex, constraints)

        wb.save(content)
        return (content.getvalue(), 'application/excel')

    def _get_changelog_comments(self, tid):
        changelog = Ticket(self.env, tkt_id=tid).get_changelog()
        changelog_str = ''

        for date, author, field, old, new, permanent in changelog:
            if field == 'comment' and new != None and new != '' and old != None and old != '' :
                changelog_str = changelog_str + ( 'comment:%s %s %s\n' % ( old, author or '', self.formats['datetime'].restore(date) ) )
                changelog_str = changelog_str + new + '\n\n'

        return changelog_str


    def _add_statistics_sheet(self, req, sheetName, wb, fields, fieldsIndex, constraints):

        neededFields = ['milestone','status','type']
        neededFieldsInfo = [f['name'] for f in fields if f['name'] in neededFields]

        if len(neededFieldsInfo) != 3 :
            return wb

        milestoneLbl = [f['label'] for f in fields if f['name']=='milestone'][0]

        types = [m.name for m in model.Type.select(self.env)]
        milestones = [m.name for m in model.Milestone.select(self.env, True)]

        if 'type' in constraints.keys() :
            types = [t for t in types if t in constraints['type']]
        if 'milestone' in constraints.keys() :
            milestones = [m for m in milestones if m in constraints['milestone']]

        headerStyle = xlwt.easyxf('font: bold on; pattern: pattern solid, fore-colour grey25; borders: top thin, bottom thin, left thin, right thin')

        ws = wb.add_sheet('Statistics')

        r = 0
        c = 0
        ws.write(r, c, milestoneLbl, headerStyle)

        for m in milestones:
            c += 1
            ws.write(r, c, m, headerStyle)

        c = 0
        for t in types:
            r += 1
            ws.write(r, c, t, headerStyle)

        r += 1
        ws.write(r, c, 'closed', headerStyle)

        template = ( "SUMPRODUCT(0+('%s'!%s:%s=%%s);0+('%s'!%s:%s=%%s))" % ( sheetName, rowcol_to_cell(1, fieldsIndex['milestone'], True, True ), rowcol_to_cell( 65364, fieldsIndex['milestone'], True, True ), sheetName, rowcol_to_cell( 1, fieldsIndex['type'], True, True ), rowcol_to_cell( 65364, fieldsIndex['type'], True, True ) ) )

        closedTemplate = ( ( "IF(SUM(%%s:%%s)=0;"+'""'+";SUMPRODUCT(0+('%s'!%s:%s=%%s);0+('%s'!%s:%s="+'"closed"))*100/SUM(%%s:%%s))' ) % \
                         ( sheetName, rowcol_to_cell(1, fieldsIndex['milestone'], True, True), rowcol_to_cell(65364, fieldsIndex['milestone'], True, True), sheetName, rowcol_to_cell(1, fieldsIndex['status'], True, True), rowcol_to_cell( 65364, fieldsIndex['status'], True, True ) ) )

        borders = xlwt.easyxf('borders: top thin, bottom thin, left thin, right thin')
        percent = xlwt.easyxf('borders: top thin, bottom thin, left thin, right thin')
        percent.num_format_str = '0.00 \\%'

        for m in range(1, len(milestones)+1):
            formula = ( closedTemplate % ( rowcol_to_cell( 1, m ), rowcol_to_cell(len(types), m), rowcol_to_cell( 0, m ), rowcol_to_cell( 1, m ), rowcol_to_cell(len(types), m) ) )
            ws.write( len(types)+1, m, xlwt.Formula( formula ), percent )
            for t in range(1, len(types)+1):
                formula = ( template % ( rowcol_to_cell( 0, m ), rowcol_to_cell( t, 0, True, True) ) )
                ws.write( t, m, xlwt.Formula( formula ), borders )
        return wb

    def _get_import_preview(self, req):
        req.perm.assert_permission('TICKET_ADMIN')

        tempfile = self._save_uploaded_file(req)

        if req.session.has_key('importexportxls.tempfile') and os.path.isfile(req.session['importexportxls.tempfile']):
          try:
            # some times tempfile leave opened
            os.remove( req.session['importexportxls.tempfile'] )
          except:
            exc = sys.exc_info()
        req.session['importexportxls.tempfile'] = tempfile

        return self._get_tickets(tempfile)

    def _process_import(self, req):
        req.perm.assert_permission('TICKET_ADMIN')

        added = 0
        modified = 0;

        if req.session.has_key('importexportxls.tempfile'):
          tempfile = req.session['importexportxls.tempfile']
          del req.session['importexportxls.tempfile']

          tickets, importFields, warnings = self._get_tickets(tempfile)
          try:
            # some times tempfile leave opened
            os.remove( tempfile )
          except:
            exc = sys.exc_info()

          for i, t in enumerate(tickets):
            if bool( req.args.get('ticket.'+unicode(i), False) ):
              if t.exists:
                if t.save_changes(author=util.get_reporter_id(req)):
                  modified += 1
              else:
                t.insert()
                added += 1
        return {'added':added,'modified':modified}

    def _get_tickets(self, filename):
        fieldsLabels = TicketSystem(self.env).get_ticket_field_labels()
        fieldsLabels['id'] = 'id'

        invFieldsLabels = {}
        for k in fieldsLabels.keys():
            invFieldsLabels[fieldsLabels[k]] = k

        book = xlrd.open_workbook(filename)
        sh = book.sheet_by_index(0)
        columns = [unicode(sh.cell_value(0, c)) for c in range(sh.ncols)]

        # columns "id" and "summary" are needed
        if 'id' not in columns and fieldsLabels['id'] not in columns:
            raise TracError('Column "id" not found')
        if 'summary' not in columns and fieldsLabels['summary'] not in columns:
            raise TracError('Column "summary" not found')

        fieldsImport = self._get_fields_import()

        importFields = []
        columnsIds = {}
        idx = 0
        idIndex = 0
        summaryIndex = 0
        creationIndex = None
        modificationIndex = None
        for c in columns:
            if c not in fieldsLabels.keys() and c in fieldsLabels.values():
                columnsIds[idx] = invFieldsLabels[c]
                if fieldsImport[invFieldsLabels[c]]:
                    importFields.append({'name':invFieldsLabels[c], 'label':c})
            elif c in fieldsLabels.keys() and c not in fieldsLabels.values():
                columnsIds[idx] = c
                if fieldsImport[c]:
                    importFields.append({'name':c, 'label':fieldsLabels[c]})
            else:
                columnsIds[idx] = None
            if columnsIds[idx] == 'id':
                idIndex = idx
            if columnsIds[idx] == 'summary':
                summaryIndex = idx
            if columnsIds[idx] == 'time':
                creationIndex = idx
            if columnsIds[idx] == 'changetime':
                modificationIndex = idx
            idx += 1

        fieldsFormat = self._get_fields_format( importFields + [{'name':'id', 'label':'id'}, {'name':'summary', 'label':fieldsLabels['summary']}] )

        warnings = []
        preview = []
        for r in range(1, sh.nrows):
            tid = self.formats['number'].restore( sh.cell_value(r, idIndex) )
            summary = self.formats['text'].restore( sh.cell_value(r, summaryIndex) )
            if tid == '' or tid == None:
                ticket = Ticket(self.env)
                for k in fieldsLabels.keys():
                    defaultValue = ticket.get_value_or_default(k)
                    if defaultValue != None:
                        ticket[k] = defaultValue
                ticket['summary'] = summary
            else:
                ticket = Ticket(self.env, tkt_id=tid)
                if ticket['summary'] != summary:
                    warnings.append('You cannot modify the summary for the ticket #'+unicode(tid))

            for idx in columnsIds.keys():
                col = columnsIds[idx]
                if col != None and idx not in [idIndex, summaryIndex, creationIndex, modificationIndex] and col in fieldsFormat.keys():
                    converterId = fieldsFormat[col]
                    converter = self.formats[converterId];
                    value = sh.cell_value(r, idx)
                    value = converter.restore( value )
                    if converter.convert( value ) != converter.convert( ticket[col] ) and converter.convert( value ) != unicode('--'):
                        ticket[col] = value
            preview.append(ticket)

        return (preview, importFields, warnings)

    def _save_uploaded_file(self, req):
        req.perm.assert_permission('TICKET_ADMIN')

        upload = req.args['import-file']
        if not hasattr(upload, 'filename') or not upload.filename:
            raise TracError('No file uploaded')
        if hasattr(upload.file, 'fileno'):
            size = os.fstat(upload.file.fileno())[6]
        else:
            upload.file.seek(0, 2) # seek to end of file
            size = upload.file.tell()
            upload.file.seek(0)
        if size == 0:
            raise TracError("Can't upload empty file")

        # Maximum file size (in bytes)
        max_size = AttachmentModule.max_size
        if max_size >= 0 and size > max_size:
            raise TracError('Maximum file size (same as attachment size, set in trac.ini configuration file): %d bytes' % max_size,
                            'Upload failed')

        # temp folder
        tempuploadedfile = tempfile.mktemp()

        flags = os.O_CREAT + os.O_WRONLY + os.O_EXCL
        if hasattr(os, 'O_BINARY'):
            flags += os.O_BINARY
        targetfile = os.fdopen(os.open(tempuploadedfile, flags), 'w')

        try:
            shutil.copyfileobj(upload.file, targetfile)
        finally:
            targetfile.close()
        return tempuploadedfile
