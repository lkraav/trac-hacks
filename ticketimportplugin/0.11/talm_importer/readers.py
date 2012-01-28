#
# Copyright (c) 2007-2008 by nexB, Inc. http://www.nexb.com/ - All rights reserved.
# Author: Francois Granade - fg at nexb dot com
# Licensed under the same license as Trac - http://trac.edgewall.org/wiki/TracLicense
#

import codecs
import csv
import datetime
try:
    import xlrd
except ImportError:
    xlrd = None

from trac.core import TracError
from trac.util.text import to_unicode


def get_reader(filename, sheet_index, datetime_format, encoding='utf-8'):
    # NOTE THAT the sheet index is 1-based !
    # KISS - keep it simple: if it can be opened as XLS, do, otherwise try as CSV.
    if xlrd:
        try:
            return XLSReader(filename, sheet_index, datetime_format)
        except IndexError:
            raise TracError('The sheet index (%s) does not seem to correspond to an existing sheet in the spreadsheet'
                            % sheet_index)
        except Exception:
            pass

    try:
        return CSVReader(filename, encoding)
    except UnicodeDecodeError:
        raise TracError('Unable to read the CSV file with "%s"' % encoding)
    except:
        if xlrd:
            message = 'Unable to read this file, does not seem to be a valid Excel or CSV file.'
        else:
            message = 'XLS reading is not configured, and this file is not a valid CSV file: unable to read file.'
        raise TracError(message)

def _to_unicode(val):
    if val is None or isinstance(val, unicode):
        return val
    return val.decode('utf-8')

class UTF8Reader(object):
    def __init__(self, file, encoding):
        self.reader = codecs.getreader(encoding)(file, 'replace')

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode("utf-8")

class CSVDictReader(csv.DictReader):
    def next(self):
        d = csv.DictReader.next(self)
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
        header = [to_unicode(self.sh.cell_value(rowx=0, colx=cx))
                  for cx in xrange(self.sh.ncols)]

        data = []
        for rx in xrange(self.sh.nrows):
            if rx == 0:
                continue
            row = {}
            i = 0
            for cx in xrange(self.sh.ncols):
                val = self.sh.cell_value(rx, cx)
                cell_type = self.sh.cell_type(rx, cx)
                if cell_type == xlrd.XL_CELL_NUMBER:
                    val = '%g' % val
                elif cell_type == xlrd.XL_CELL_DATE:
                    val = datetime.datetime(*xlrd.xldate_as_tuple(val, self.book.datemode))
                    val = val.strftime(self._datetime_format)
                elif cell_type == xlrd.XL_CELL_BOOLEAN:
                    val = ('FALSE', 'TRUE')[val]
                elif cell_type == xlrd.XL_CELL_ERROR:
                    val = xlrd.error_text_from_code.get(val) or '#ERR%d' % val
                row[header[i]] = val

                i += 1
            data.append(row)

        return header, data

    def close(self):
        pass
