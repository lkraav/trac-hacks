#
# Copyright (c) 2007-2008 by nexB, Inc. http://www.nexb.com/ - All rights reserved.
# Author: Francois Granade - fg at nexb dot com
# Licensed under the same license as Trac - http://trac.edgewall.org/wiki/TracLicense
#

from datetime import datetime
import codecs
import csv
try:
    import xlrd
except ImportError:
    xlrd = None
try:
    import openpyxl
except ImportError:
    openpyxl = None

from trac.core import TracError
from trac.util.text import exception_to_unicode, to_unicode


def get_reader(env, filename, sheet_index, datetime_format, encoding='utf-8'):
    errors = {}

    if openpyxl:
        try:
            return XLSXReader(filename, sheet_index, datetime_format)
        except IndexError:
            raise TracError('The sheet index (%s) does not seem to correspond to an existing sheet in the spreadsheet'
                            % sheet_index)
        except Exception, e:
            errors['XLSXReader'] = exception_to_unicode(e, traceback=True)

    if xlrd:
        try:
            return XLSReader(filename, sheet_index, datetime_format)
        except IndexError:
            raise TracError('The sheet index (%s) does not seem to correspond to an existing sheet in the spreadsheet'
                            % sheet_index)
        except xlrd.XLRDError, e:
            errors['XLSReader'] = exception_to_unicode(e)
        except Exception, e:
            errors['XLSReader'] = exception_to_unicode(e, traceback=True)

    try:
        return CSVReader(filename, encoding)
    except UnicodeDecodeError:
        raise TracError('Unable to read the CSV file with "%s"' % encoding)
    except csv.Error, e:
        errors['CSVReader'] = exception_to_unicode(e)
    except Exception, e:
        errors['CSVReader'] = exception_to_unicode(e, traceback=True)

    for name, error in errors.iteritems():
        env.log.warning('Exception caught while reading the file using %s: %s',
                        name, error)
    if xlrd or openpyxl:
        message = 'Unable to read this file, does not seem to be a valid ' \
                  'Excel or CSV file.'
    else:
        message = 'XLS reading is not configured, and this file is not a ' \
                  'valid CSV file: unable to read file.'
    raise TracError(message)

def _to_unicode(val):
    if val is None or isinstance(val, unicode):
        return val
    return val.decode('utf-8')

class UTF8Reader(object):
    def __init__(self, file, encoding):
        self.reader = codecs.getreader(encoding)(file, 'replace')
        self.line_num = 0

    def __iter__(self):
        return self

    def next(self):
        line = self.reader.next()
        self.line_num += 1
        return line.encode("utf-8")

class CSVDialect(csv.excel):
    strict = True

class CSVDictReader(csv.DictReader):
    def __init__(self, reader, fields):
        csv.DictReader.__init__(self, reader, fields, dialect=CSVDialect)
        self.__reader = reader

    def next(self):
        reader = self.__reader
        begin = reader.line_num + 1
        try:
            d = csv.DictReader.next(self)
        except csv.Error, e:
            end = reader.line_num
            if begin == end:
                message = 'Error while reading line %(num)d: %(error)s'
                kwargs = {'num': end, 'error': to_unicode(e)}
            else:
                message = 'Error while reading from line %(begin)d to ' \
                          '%(end)d: %(error)s'
                kwargs = {'begin': begin, 'end': end, 'error': to_unicode(e)}
            raise TracError(message % kwargs)
        return dict((_to_unicode(key), _to_unicode(val))
                    for key, val in d.iteritems()
                    if key is not None)

class CSVReader(object):
    def __init__(self, filename, encoding):
        self.file = open(filename, 'rb')
        self.file_reader = UTF8Reader(self.file, encoding)
        self.csv_reader = csv.reader(self.file_reader)
        fields = [_to_unicode(val) for val in self.csv_reader.next()]
        if fields and fields[0] and fields[0].startswith(u'\uFEFF'):
            # Skip BOM
            fields[0] = fields[0][1:]
        self.csvfields = fields
        
    def get_sheet_count(self):
        return 1
        
    def readers(self):
        return self.csvfields, CSVDictReader(self.file_reader, self.csvfields)
            
    def close(self):
        self.file.close()

class XLSReader(object):
    def __init__(self, filename, sheet_index, datetime_format):
        self.book = xlrd.open_workbook(filename)
        self.sheetcount = self.book.nsheets
        self.sh = self.book.sheet_by_index(sheet_index - 1)
        self._datetime_format = datetime_format

    def get_sheet_count(self):
        return self.sheetcount
        
    def readers(self):
        # TODO: do something with sh.name. Probably add it as a column. 
        # TODO: read the other sheets. What if they don't have the same columns ?

        def to_s(val, cell_type):
            if cell_type == xlrd.XL_CELL_NUMBER:
                return '%g' % val
            if cell_type == xlrd.XL_CELL_DATE:
                val = datetime(*xlrd.xldate_as_tuple(val, self.book.datemode))
                return val.strftime(self._datetime_format)
            if cell_type == xlrd.XL_CELL_BOOLEAN:
                return ('FALSE', 'TRUE')[val]
            if cell_type == xlrd.XL_CELL_ERROR:
                return xlrd.error_text_from_code.get(val) or '#ERR%d' % val
            return val

        sh = self.sh
        header = [to_s(sh.cell_value(0, cx), sh.cell_type(0, cx))
                  for cx in xrange(sh.ncols)]
        data = []
        for rx in xrange(sh.nrows):
            if rx == 0:
                continue
            row = {}
            i = 0
            for cx in xrange(sh.ncols):
                val = sh.cell_value(rx, cx)
                cell_type = sh.cell_type(rx, cx)
                row[header[i]] = to_s(val, cell_type)
                i += 1
            data.append(row)

        return header, data

    def close(self):
        pass


class XLSXReader(object):

    def __init__(self, filename, sheet_index, datetime_format):
        self.fileobj = open(filename, 'rb')
        self.book = openpyxl.load_workbook(filename=self.fileobj,
                                           read_only=True, data_only=True)
        worksheets = self.book.worksheets
        self.sheets_count = len(worksheets)
        self.sheet = worksheets[sheet_index - 1]
        self._datetime_format = datetime_format

    def get_sheet_count(self):
        return self.sheets_count

    def readers(self):
        def to_s(cell):
            val = cell.value
            if isinstance(val, unicode):
                return val
            if val is None:
                return ''
            if val is True:
                return 'TRUE'
            if val is False:
                return 'FALSE'
            if isinstance(val, datetime):
                return val.strftime(self._datetime_format)
            if isinstance(val, (long, int, float)):
                return '%g' % val
            return to_unicode(val)

        def iter_data(iter_row, header):
            for row in iter_row:
                values = {}
                for idx, cell in enumerate(row):
                    if idx >= len(header):
                        break
                    values[header[idx]] = to_s(cell)
                if values:
                    yield values

        iter_row = iter(self.sheet.rows)
        try:
            row = next(iter_row)
        except StopIteration:
            return [], []
        else:
            header = [to_s(cell) for cell in row]
            return header, iter_data(iter_row, header)

    def close(self):
        if self.fileobj:
            self.fileobj.close()
            self.fileobj = None
