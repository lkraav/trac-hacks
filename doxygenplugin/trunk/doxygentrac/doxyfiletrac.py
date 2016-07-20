# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Emmanuel Saint-James <esj@rezo.net>
#

import os
import re

from collections import OrderedDict
from subprocess import Popen
from trac.util.text import to_unicode
from trac.core import TracError

def post_doxyfile(req, doxygen, doxygen_args, doxyfile, input, base_path, log):
    """
    Build a Doxyfile from POST data and execute Doxygen,
    whose path and arguments are issued from trac.ini.
    If exec succeed, redirect to the main page of the generated documentation.
    """
    path_trac = req.args.get('OUTPUT_DIRECTORY')
    if  path_trac and path_trac[-1] !='/':
        path_trac += '/'
    if not doxyfile:
        doxyfile = os.path.join(path_trac, 'Doxyfile')
    if not os.path.isdir(path_trac):
        try:
            os.mkdir(path_trac)
        except (IOError, OSError), e:
            raise TracError("Can't create directory: %s" % path_trac)

    if not os.path.isdir(path_trac) or not os.access(path_trac, os.W_OK):
        return {'msg': 'Error:' + path_trac + ' not W_OK', 'trace': ''}
    else:
        log.debug('calling ' + doxygen + ' ' + doxygen_args)
        env = apply_doxyfile(req.args, doxygen, doxygen_args, doxyfile, input, path_trac)
        log.debug('write %d options in %s', env['options'], doxyfile);
        if env['msg'] != '':
            return env
        else:
            log.debug(env['trace'])
            doc = path_trac[len(base_path):].strip('/')
            if not doc:
                url = req.href.doxygen('/')
            else:
                url = req.href.doxygen('/', doc=doc)
            req.redirect(url)


def init_doxyfile(env, doxygen, doxyfile, input, base_path, default_doc, log):
    """
    Build the standard Doxyfile, and merge it with the current if any.
    Return a dict with the list of Doxygen options with their values,
    along with an error message if any,
    and the trace for warnings and the like.
    """
    path_trac = os.path.join(base_path, default_doc)
    if not env and not os.path.isdir(path_trac) or not os.access(path_trac, os.W_OK):
        env = {'msg': 'Error: ' + path_trac + ' not W_OK', 'trace': ''}
        path_trac = '/tmp'
    elif not env:
        env = {'msg': '', 'trace': ''}
    if not doxyfile:
        doxyfile = os.path.join(path_trac, 'Doxyfile')
    else:
        doxyfile = ''
    # Read old choices if they exists
    if os.path.exists(doxyfile):
        old = analyze_doxyfile(base_path, default_doc, input, doxyfile, {}, log)
    else:
        old = {}
    # Generate the std Doxyfile
    # (newer after a doxygen command update, who knows)
    fi = os.path.join(path_trac, 'doxygen.tmp')
    fo = os.path.join(path_trac, 'doxygen.out')
    o = open(fo, 'w');
    fr = os.path.join(path_trac, 'doxygen.err')
    e = open(fr, 'w');
    if o and e:
        p = Popen([doxygen, '-g', fi],  bufsize=-1, stdout=o, stderr=e)
        p.communicate()
        n = p.returncode
    else:
        n = -1
    if not os.path.exists(fi) or n !=0:
        env['fieldsets'] = {};
        env['msg'] += (" Doxygen -g Error %s\n" %(n))
        env['trace'] = file(fr).read()
    else:
        # Read std Doxyfile and report old choices in it
        # split in fieldsets
        fieldsets = OrderedDict()
        sets = OrderedDict()
        prev = first = ''
        inputs = analyze_doxyfile(base_path, default_doc, input, fi, old, log)
        for k,s in inputs.iteritems():
            if s['explain']:
                if prev and sets:
                    log.debug("fieldset %s first '%s'", prev, first)
                    fieldsets[prev] = display_doxyfile(prev, first, sets)
                sets = OrderedDict()
                prev = s['explain']
                first = s['value'].strip()
            sets[k] = s
        if prev and sets:
            fieldsets[prev] = display_doxyfile(prev, first, sets)
        env['fieldsets'] = fieldsets

    # try, don't cry
    try:
        os.unlink(fi)
        os.unlink(fr)
        os.unlink(fo)
    except (IOError, OSError), e:
        log.debug("forget temporary files")

    return env


def apply_doxyfile(req_args, doxygen, doxygen_args, doxyfile, input, path_trac):
    """
    Save the POST data in the Doxyfile, and execute doxygen from the INPUT dir,
    since the EXCLUDE option is computed relative to the execution path.
    Return a dict with an empty "msg" field if ok, an error message otherwise.
    Warning: Doxygen does not check if the Dot utility exit on error,
    so an empty message doest not always mean the execution is ok.
    The "trace" field mention the possible Dot errors.
    It also contains the Doxygen warnings.
    """

    f = open(doxyfile, 'w')
    i = 0;
    for k in req_args:
        if not re.match(r'''^[A-Z]''', k):
            continue
        if req_args.get(k):
            s = req_args.get(k)
        else:
            s = '';
        o = "#\n" + k + '=' + s + "\n"
        f.write(o.encode('utf8'))
        i+=1

    f.close()
    fo = os.path.join(path_trac, 'doxygen.out')
    o = open(fo, 'w');
    fr = os.path.join(path_trac, 'doxygen.err')
    e = open(fr, 'w');
    if doxygen_args:
        arg = doxygen_args
    else:
        arg = doxyfile

    dir = req_args.get('INPUT') if req_args.get('INPUT') else input;
    if not os.path.isdir(dir) or not os.access(dir, os.R_OK):
        return {'msg': 'Error: ' + dir + ' not R_OK', 'trace': '', 'options': i}
    p = Popen([doxygen, arg], bufsize=-1, stdout=o, stderr=e, cwd=dir if dir else None)
    p.communicate();
    n = p.returncode;
    o.close()
    e.close()
    if n == 0:
        p = Popen(['chmod', '-R', 'g+w', path_trac])
        msg = "";
        trace = file(fo).read() + file(fr).read()
    else:
        msg = ("Doxygen Error %s\n" %(n))
        trace = file(fr).read()
    os.unlink(fo)
    os.unlink(fr)
    return {'msg': msg, 'trace': trace, 'options': i}


def analyze_doxyfile(base_path, default_doc, input, path, old, log):
    """
    Read a Doxyfile and build a Web form allowing to change its default values.
    Text blocs between '#----' introduce new section.
    Other text blocs are treated as the "label" tag of the "input" tag
    described by the line matching NAME=VALUE that follows.
    Values different form default value for a field have a different CSS class.
    For some NAMES, value cannot be choosen freely.
    """

    try:
        content = file(path).read()
    except (IOError, OSError), e:
        raise TracError("Can't read doxygen content: %s" % e)

    content = to_unicode(content, 'utf-8')
    # Initial text is about file, not form
    c = re.match(r'''^.*?(#-----.*)''', content, re.S)
    if c:
        log.debug('taking "%s" last characters out of %s in %s', len(c.group(1)), len(content), path);
        content = c.group(1)

    m = re.compile(r'''\s*(#-+\s+#(.*?)\s+#-+)?(.*?)$\s*([A-Z][A-Z0-9_-]+)\s*=([^#]*?)$''', re.S|re.M)
    s = m.findall(content)
    log.debug('Found "%s" options in Doxyfile', len(s));
    options = OrderedDict()
    for o in s:
        u, explain, label, id, value = o
        atclass = default = ''
        if id in old and value != old[id]['value']:
            value = old[id]['value']
            atclass = 'changed'
        # required for plugin to work
        if id == 'SERVER_BASED_SEARCH' or id == 'EXTERNAL_SEARCH':
            value = 'YES'
            atclass = 'changed'
        if id == 'OUTPUT_DIRECTORY' and base_path:
            default = base_path + ('' if base_path[-1] =='/' else '/')
            value = value[len(default):]
            if value:
                atclass = 'changed'
            else:
                value = default_doc
        elif id == 'INPUT' and input:
            default = input + ('' if input[-1] =='/' else '/')
            value = value[len(default):]
            if value:
                atclass = 'changed'
        elif id == 'STRIP_FROM_PATH' and input and not value:
            value = input
            atclass = 'changed'
        elif id == 'PROJECT_NAME' and re.match('\s*"My Project"', value):
            value = os.path.basename(input)
            if not value:
                value = os.path.basename(base_path)
            atclass = 'changed'
                
        # prepare longer input tag for long default value
        l = 20 if len(value) < 20 else len(value) + 3
        options[id] = {
            'explain': explain,
            'label': label,
            'value': value,
            'default': default,
            'size': l,
            'atclass': atclass
        }
    return options

def display_doxyfile(prev, first, sets):
    """
    Prepare the fieldset corresponding to a section in the Doxyfile.
    If the name of the section matches "output", 
    and the first option in it is set to 'NO',
    the fieldset will not be displayed.
    """
    if re.match(r'''.*output$''', prev) and first == 'NO':
        display = 'none'
    else:
        display = 'block'
    return {'display': display, 'opt': sets}

