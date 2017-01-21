# -*- coding: utf-8 -*-

import os
import re
import shutil
import unicodedata

from datetime import *
from pkg_resources import resource_filename
from zipfile import *
from PIL import Image
from StringIO import *

from trac.config import ListOption, Option
from trac.core import Component, ExtensionPoint, TracError, implements
from trac.mimeview import Mimeview
from trac.perm import IPermissionRequestor
from trac.util import to_unicode
from trac.util.datefmt import pretty_timedelta, to_datetime, to_timestamp, utc
from trac.util.html import html
from trac.util.translation import domain_functions
from trac.web.chrome import INavigationContributor, ITemplateProvider, \
                            add_script, add_stylesheet, web_context
from trac.web.main import IRequestHandler
from trac.wiki.formatter import format_to_oneliner

from tracscreenshots.api import IScreenshotChangeListener, \
                                IScreenshotsRenderer, ScreenshotsApi

# Bring in dedicated Trac plugin i18n helper.
add_domain, _, tag_ = domain_functions('tracscreenshots', ('add_domain', '_',
  'tag_'))


class ScreenshotsCore(Component):
    """
        The core module implements plugin's main page and mainnav button,
        provides permissions and templates.
    """
    implements(INavigationContributor, IRequestHandler, ITemplateProvider,
      IPermissionRequestor)

    renderers = ExtensionPoint(IScreenshotsRenderer)
    change_listeners = ExtensionPoint(IScreenshotChangeListener)

    # Configuration options.
    mainnav_title = Option('screenshots', 'mainnav_title', _("Screenshots"),
      doc = _("Main navigation bar button title."))
    metanav_title = Option('screenshots', 'metanav_title', '', doc = _("Meta "
      "navigation bar link title."))
    ext = ListOption('screenshots', 'ext', 'jpg,png', doc = _("List of "
      "screenshot file extensions that can be uploaded. Must be supported by "
      "PIL."))
    formats = ListOption('screenshots', 'formats', 'raw,html,jpg,png', doc =
      _("List of allowed formats for screenshot download."))
    default_format = Option('screenshots', 'default_format', 'html', doc =
      _("Default format for screenshot download links."))
    default_components = ListOption('screenshots', 'default_components', 'all',
      doc = _("List of components enabled by default."))
    default_versions = ListOption('screenshots', 'default_versions', 'all',
      doc = _("List of versions enabled by default."))
    default_filter_relation = Option('screenshots', 'default_filter_relation',
      'or', doc = _("Logical relation between component and version part of "
      "screenshots filter."))
    default_orders = ListOption('screenshots', 'default_orders', 'id', doc =
      _("List of names of database fields that are used to sort screenshots."))
    default_order_directions = ListOption('screenshots',
      'default_order_directions', 'asc', doc = _("List of ordering directions "
      "for fields specified in {{{default_orders}}} configuration option."))

    def __init__(self):
        # Path where to store uploaded screenshots, see init.py.
        self.path = self.config.getpath('screenshots', 'path') or \
                    '../screenshots'

        # Items for not specified component and version.
        self.none_component = {'name': 'none', 'description': 'none'}
        self.none_version = {'name': 'none', 'description': 'none'}

        # Bind 'tracscreenshots' catalog to the specified locale directory.
        locale_dir = resource_filename(__name__, 'locale')
        add_domain(self.env.path, locale_dir)

    # IPermissionRequestor methods.

    def get_permission_actions(self):
        view = 'SCREENSHOTS_VIEW'
        filter = 'SCREENSHOTS_FILTER', ['SCREENSHOTS_VIEW']
        order = 'SCREENSHOTS_ORDER', ['SCREENSHOTS_VIEW']
        add = 'SCREENSHOTS_ADD', ['SCREENSHOTS_VIEW']
        edit = 'SCREENSHOTS_EDIT', ['SCREENSHOTS_VIEW']
        delete = 'SCREENSHOTS_DELETE', ['SCREENSHOTS_VIEW']
        admin = ('SCREENSHOTS_ADMIN',
                 ['SCREENSHOTS_ORDER', 'SCREENSHOTS_FILTER',
                  'SCREENSHOTS_ADD', 'SCREENSHOTS_EDIT',
                  'SCREENSHOTS_DELETE', 'SCREENSHOTS_VIEW'])
        return [view, filter, order, add, edit, delete, admin]

    # ITemplateProvider methods.

    def get_htdocs_dirs(self):
        return [('screenshots', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return [resource_filename(__name__, 'templates')]

    # INavigationContributor methods.

    def get_active_navigation_item(self, req):
        return 'screenshots'

    def get_navigation_items(self, req):
        if 'SCREENSHOTS_VIEW' in req.perm:
            if self.mainnav_title:
                yield ('mainnav', 'screenshots',
                       html.a(self.mainnav_title,
                              href=req.href.screenshots()))
            if self.metanav_title:
                yield ('metanav', 'screenshots',
                       html.a(self.metanav_title,
                              href=req.href.screenshots()))

    # IRequestHandler methods.

    def match_request(self, req):
        match = re.match(r'/screenshots(?:/(\d+))?$', req.path_info)
        if match:
            if match.group(1):
                req.args['action'] = 'get-file'
                req.args['id'] = match.group(1)
            return 1

    def process_request(self, req):
        # Create request context.
        context = web_context(req)
        context.realm = 'screenshots-core'

        has_tags = self.env.is_component_enabled('tracscreenshots.tags.'
                                                 'ScreenshotsTags')
        req.data = {
            'title': self.mainnav_title or self.metanav_title,
            'has_tags': has_tags
        }

        # Get action from request and perform them.
        actions = self._get_actions(req)
        template, content_type = self._do_actions(context, actions)

        # Add CSS style and JavaScript scripts.
        add_stylesheet(req, 'screenshots/css/screenshots.css')
        add_script(req, 'screenshots/js/screenshots.js')

        # Return template and its data.
        return template + '.html', {'screenshots': req.data}, content_type

    # Internal functions.

    def _get_actions(self, req):
        action = req.args.get('action')
        if action == 'get-file':
            return ['get-file']
        elif action == 'add':
            return ['add']
        elif action == 'post-add':
            return ['post-add', 'view']
        elif action == 'edit':
            return ['edit', 'add']
        elif action == 'post-edit':
            return ['post-edit', 'view']
        elif action == 'delete':
            return ['delete', 'view']
        elif action == 'filter':
            return ['filter', 'view']
        elif action == 'order':
            return ['order', 'view']
        else:
            return ['view']

    def _do_actions(self, context, actions):
        api = self.env[ScreenshotsApi]
        req = context.req

        for action in actions:
            if action == 'get-file':
                req.perm.require('SCREENSHOTS_VIEW')

                # Get request arguments.
                screenshot_id = req.args.getint('id', 0)
                format = req.args.get('format') or self.default_format
                width = req.args.getint('width', 0)
                height = req.args.getint('height', 0)

                # Check if requested format is allowed.
                if format not in self.formats:
                    raise TracError(_("Requested screenshot format that is "
                                      "not allowed."),
                                    _("Requested format not allowed."))

                # Get screenshot.
                screenshot = api.get_screenshot(screenshot_id)

                # Check if requested screenshot exists.
                if not screenshot:
                    if 'SCREENSHOTS_ADD' in req.perm:
                        req.redirect(req.href.screenshots(action = 'add'))
                    else:
                        raise TracError(_("Screenshot not found."))

                # Set missing dimensions.
                width = width or screenshot['width']
                height = height or screenshot['height']

                if format == 'html':
                    # Format screenshot for presentation.
                    screenshot['author'] = format_to_oneliner(self.env, context,
                      screenshot['author'])
                    screenshot['name'] = format_to_oneliner(self.env, context,
                      screenshot['name'])
                    screenshot['description'] = format_to_oneliner(self.env,
                      context, screenshot['description'])
                    screenshot['time'] = pretty_timedelta(to_datetime(
                      screenshot['time'], utc))

                    # For HTML preview format return template.
                    req.data['screenshot'] = screenshot
                    return 'screenshot', None
                else:
                    # Prepare screenshot filename.
                    name, ext = os.path.splitext(screenshot['file'])
                    format = (format == 'raw') and ext or '.' + format
                    path = os.path.normpath(os.path.join(self.path, to_unicode(
                      screenshot['id'])))
                    filename = os.path.normpath(os.path.join(path, '%s-%sx%s%s'
                      % (name, width, height, format)))
                    orig_name = os.path.normpath(os.path.join(path, '%s-%sx%s%s'
                      % (name, screenshot['width'], screenshot['height'], ext)))
                    base_name = os.path.normpath(os.path.basename(filename))

                    self.log.debug("filename: %s", filename)

                    # Create requested file from original if not exists.
                    if not os.path.isfile(filename.encode('utf-8')):
                        self._create_image(orig_name, path, name, format,
                          width, height)

                    # Guess mime type.
                    with open(filename.encode('utf-8')) as fh:
                        file_data = fh.read(1000)
                    mimeview = Mimeview(self.env)
                    mime_type = mimeview.get_mimetype(filename, file_data)
                    if not mime_type:
                        mime_type = 'application/octet-stream'
                    if 'charset=' not in mime_type:
                        charset = mimeview.get_charset(file_data, mime_type)
                        mime_type = mime_type + '; charset=' + charset

                    # Send file to request.
                    req.send_header('Content-Disposition',
                                    'attachment;filename="%s"' % base_name)
                    req.send_header('Content-Description',
                                    screenshot['description'])
                    req.send_file(filename.encode('utf-8'), mime_type)

            elif action == 'add':
                req.perm.require('SCREENSHOTS_ADD')

                index = req.args.getint('index', 0)

                # Fill data dictionary.
                req.data['index'] = index
                req.data['versions'] = api.get_versions()
                req.data['components'] = api.get_components()

                # Return template with add screenshot form.
                return 'screenshot-add', None

            elif action == 'post-add':
                req.perm.require('SCREENSHOTS_ADD')

                # Get image file from request.
                file, filename = self._get_file_from_req(req)
                name, ext = os.path.splitext(filename)
                ext = ext.lower()
                filename = name + ext

                # Is uploaded file archive or single image?
                if ext == '.zip':
                    # Get global timestamp for all files in archive.
                    timestamp = to_timestamp(datetime.now(utc))

                    # List files in archive.
                    zip_file = ZipFile(file)
                    for filename in zip_file.namelist():
                        # Test file extensions for supported type.
                        name, ext = os.path.splitext(filename)
                        tmp_ext = ext.lower()[1:]
                        if tmp_ext in self.ext and tmp_ext != 'zip':
                            # Decompress image file
                            data = zip_file.read(filename)
                            file = StringIO(data)
                            filename = to_unicode(os.path.basename(filename))

                            # Screenshots must be identified by timestamp.
                            timestamp += 1

                            # Create image object.
                            image = Image.open(file)

                            screenshot = {
                                'name':  req.args.get('name'),
                                'description': req.args.get('description'),
                                'time': timestamp,
                                'author': req.authname,
                                'tags': req.args.get('tags'),
                                'file': filename,
                                'width': image.size[0],
                                'height': image.size[1],
                                'priority': req.args.getint('priority', 0)
                            }
                            self.log.debug("screenshot: %s", screenshot)

                            # Save screenshot file and add DB entry.
                            self._add_screenshot(context, api, screenshot,
                                                 file)

                    zip_file.close()
                else:
                    # Create image object.
                    image = Image.open(file)

                    # Construct screenshot dictionary from form values.
                    screenshot = {
                        'name':  req.args.get('name'),
                        'description': req.args.get('description'),
                        'time': to_timestamp(datetime.now(utc)),
                        'author': req.authname,
                        'tags': req.args.get('tags'),
                        'file': filename,
                        'width': image.size[0],
                        'height': image.size[1],
                        'priority': req.args.getint('priority', 0)
                    }
                    self.log.debug("screenshot: %s", screenshot)

                    # Add single image.
                    self._add_screenshot(context, api, screenshot, file)

                # Close input file.
                file.close()

                # Clear ID to prevent display of edit and delete button.
                req.args['id'] = None

            elif action == 'edit':
                req.perm.require('SCREENSHOTS_EDIT')
                screenshot_id = req.args.get('id')
                req.data['screenshot'] = api.get_screenshot(screenshot_id)

            elif action == 'post-edit':
                req.perm.require('SCREENSHOTS_EDIT')
                screenshot_id = req.args.get('id', 0)
                old_screenshot = api.get_screenshot(screenshot_id)

                if not old_screenshot:
                    raise TracError(_("Edited screenshot not found."),
                      _("Screenshot not found."))

                # Get image file from request.
                image = req.args['image']
                if hasattr(image, 'filename') and image.filename:
                    in_file, filename = self._get_file_from_req(req)
                    name, ext = os.path.splitext(filename)
                    filename = name + ext.lower()
                else:
                    filename = None

                # Construct screenshot dictionary from form values.
                screenshot = {
                    'name':  req.args.get('name'),
                    'description': req.args.get('description'),
                    'author': req.authname,
                    'tags': req.args.get('tags'),
                    'components': req.args.getlist('components'),
                    'versions': req.args.getlist('versions'),
                    'priority': req.args.get('priority', 0)
                }

                # Update dimensions and filename if image file is updated.
                if filename:
                    image = Image.open(in_file)
                    screenshot['file'] = filename
                    screenshot['width'] = image.size[0]
                    screenshot['height'] = image.size[1]

                self.log.debug("screenshot: %s", screenshot)

                # Edit screenshot.
                api.edit_screenshot(screenshot_id, screenshot)

                # Prepare file paths.
                if filename:
                    name, ext = os.path.splitext(screenshot['file'])
                    path = os.path.normpath(os.path.join(self.path, to_unicode(
                      screenshot_id)))
                    filepath = os.path.normpath(os.path.join(path, '%s-%ix%i%s'
                      % (name, screenshot['width'], screenshot['height'], ext)))

                    self.log.debug("path: %s", path)
                    self.log.debug("filepath: %s", filepath)

                    # Delete present images.
                    try:
                        for file in os.listdir(path):
                            file = os.path.normpath(
                                os.path.join(path, to_unicode(file)))
                            os.remove(file.encode('utf-8'))
                    except Exception as error:
                        raise TracError(_("Error deleting screenshot. "
                                          "Original error message was: "
                                          "%(error)s",
                                          error=to_unicode(error)))

                    # Store uploaded image.
                    try:
                        out_file = open(filepath.encode('utf-8'), 'wb+') 
                        in_file.seek(0)
                        shutil.copyfileobj(in_file, out_file)
                        out_file.close()
                    except Exception as error:
                        try:
                            os.remove(filepath.encode('utf-8'))
                        except:
                            pass
                        raise TracError(_("Error storing file. Is directory "
                          "specified in path config option in [screenshots] "
                          "section of trac.ini existing? Original error "
                          "message was: %s") % (to_unicode(error),))

                # Notify change listeners.
                for listener in self.change_listeners:
                    listener.screenshot_changed(req, screenshot,
                      old_screenshot)

                # Clear ID to prevent display of edit and delete button.
                req.args['id'] = None

            elif action == 'delete':
                req.perm.require('SCREENSHOTS_DELETE')

                # Get request arguments.
                screenshot_id = req.args.get('id')

                # Get screenshot.
                screenshot = api.get_screenshot(screenshot_id)

                # Check if requested screenshot exits.
                if not screenshot:
                    raise TracError(_("Deleted screenshot not found."),
                      _("Screenshot not found."))

                # Delete screenshot.
                api.delete_screenshot(screenshot['id'])

                # Delete screenshot files. Don't append any other files there :-).
                path = os.path.normpath(os.path.join(self.path, to_unicode(
                  screenshot['id'])))
                self.log.debug("path: %s", path)
                try:
                    for file in os.listdir(path):
                        file = os.path.normpath(os.path.join(path,
                          to_unicode(file)))
                        os.remove(file.encode('utf-8'))
                    os.rmdir(path.encode('utf-8'))
                except Exception as error:
                    raise TracError(_("Error deleting screenshot. Original "
                                      "error message was: %(error)s",
                                      error=to_unicode(error)))

                # Notify change listeners.
                for listener in self.change_listeners:
                    listener.screenshot_deleted(req, screenshot)

                # Clear id to prevent display of edit and delete button.
                req.args['id'] = None

            elif action == 'filter':
                req.perm.require('SCREENSHOTS_FILTER')

                components = req.args.getlist('components')
                self._set_enabled_components(req, components)

                versions = req.args.getlist('versions')
                self._set_enabled_versions(req, versions)

                # Update filter relation from request.
                relation = req.args.get('filter_relation') or 'or'
                self._set_filter_relation(req, relation)

            elif action == 'order':
                req.perm.require('SCREENSHOTS_ORDER')

                # Get three order fields from request and store them to session.
                orders = []
                I = 0
                while 'order_%s' % (I,) in req.args:
                    orders.append((req.args.get('order_%s' % (I,)) or 'id',
                      req.args.get('order_direction_%s' % (I,)) or 'asc'))
                    I += 1
                self._set_orders(req, orders)

            elif action == 'view':
                req.perm.require('SCREENSHOTS_VIEW')

                # Get request arguments.
                screenshot_id = int(req.args.get('id') or 0)

                # Check that at least one IScreenshotsRenderer is enabled.
                if len(self.renderers) == 0:
                    raise TracError(_("No screenshots renderer enabled. "
                      "Enable at least one."), _("No screenshots renderer "
                      "enabled"))

                # Get all available components and versions.
                components = [self.none_component] + api.get_components()
                versions = [self.none_version] + api.get_versions()

                # Get enabled components, versions and filter relation from
                # request or session.
                enabled_components = self._get_enabled_components(req)
                enabled_versions = self._get_enabled_versions(req)
                relation = self._get_filter_relation(req)
                if 'all' in enabled_components:
                    enabled_components = [component['name'] for component in
                    components]
                if 'all' in enabled_versions:
                    enabled_versions = [version['name'] for version in
                    versions]

                self.log.debug("components: %s", components)
                self.log.debug("versions: %s", versions)
                self.log.debug("enabled_components: %s", enabled_components)
                self.log.debug("enabled_versions: %s", enabled_versions)
                self.log.debug("filter_relation: %s", relation)

                # Get order fields of screenshots.
                orders = self._get_orders(req)

                # Filter screenshots.
                screenshots = api.get_filtered_screenshots(enabled_components,
                                                           enabled_versions,
                                                           relation, orders)
                self.log.debug("screenshots: %s", screenshots)

                # Convert enabled components and versions to dictionary.
                enabled_components = dict(zip(enabled_components, [True] *
                  len(enabled_components)))
                enabled_versions = dict(zip(enabled_versions, [True] *
                  len(enabled_versions)))

                # Fill data dictionary.
                req.data['id'] = screenshot_id
                req.data['components'] = components
                req.data['versions'] = versions
                req.data['screenshots'] = screenshots
                req.data['href'] = req.href.screenshots()
                req.data['enabled_versions'] = enabled_versions
                req.data['enabled_components'] = enabled_components
                req.data['filter_relation'] = relation
                req.data['orders'] = orders

                # Get screenshots content template and data.
                template, content_type = self.renderers[0].\
                                         render_screenshots(req)
                req.data['content_template'] = template

                # Return main template.
                return 'screenshots', content_type

            elif actions == 'screenshot-add':
                req.perm.require('SCREENSHOTS_ADD')

                # Get screenshot
                screenshot = api.get_screenshot(self.id)
                self.log.debug("screenshot: %s", screenshot)

    """ Full implementation of screenshot addition. It creates DB entry for
    screenshot <screenshot> and stores screenshot file <file> to file system.
    """
    def _add_screenshot(self, context, api, screenshot, file):

        # Add new screenshot to DB.
        api.add_screenshot(screenshot)

        # Get inserted screenshot to with new id.
        screenshot = api.get_screenshot_by_time(screenshot['time'])

        # Prepare file paths.
        name, ext = os.path.splitext(screenshot['file'])
        path = os.path.normpath(os.path.join(self.path, to_unicode(
          screenshot['id'])))
        filepath = os.path.normpath(os.path.join(path, '%s-%ix%i%s' % (name,
          screenshot['width'], screenshot['height'], ext)))

        self.log.debug("path: %s", path)
        self.log.debug("filename: %s", filepath)

        # Store uploaded image.
        try:
            os.mkdir(path.encode('utf-8'))
            out_file = open(filepath.encode('utf-8'), "wb+")
            file.seek(0)
            shutil.copyfileobj(file, out_file)
            out_file.close()
        except Exception as error:
            self.log.debug(error)

            # Delete screenshot.
            api.delete_screenshot(screenshot['id'])

            # Remove screenshot image and directory.
            try:
                os.remove(filepath.encode('utf-8'))
            except:
                pass
            try:
                os.rmdir(path.encode('utf-8'))
            except:
                pass
            raise TracError(_("Error storing file. Is directory specified "
                              "in path config option in [screenshots] "
                              "section of trac.ini existing? Original error "
                              "message was: %s") % (to_unicode(error),))

        # Add components to screenshot to DB.
        components = context.req.args.get('components') or []
        if not isinstance(components, list):
            components = [components]
        for component in components:
            component = {'screenshot': screenshot['id'],
                         'component': component}
            api.add_component(component)
        screenshot['components'] = components

        # Add versions to screenshots to DB
        versions = context.req.args.get('versions') or []
        if not isinstance(versions, list):
            versions = [versions]
        for version in versions:
            version = {'screenshot': screenshot['id'],
                       'version': version}
            api.add_version(version)
        screenshot['versions'] = versions

        # Notify change listeners.
        for listener in self.change_listeners:
            listener.screenshot_created(context.req, screenshot)

    def _create_image(self, orig_name, path, name, ext, width, height):
        image = Image.open(orig_name.encode('utf-8'))
        image = image.resize((width, height), Image.ANTIALIAS)
        image_name = os.path.normpath(os.path.join(path, '%s-%sx%s%s' % (name,
          width, height, ext)))
        image.save(image_name.encode('utf-8'))

    def _get_file_from_req(self, req):
        image = req.args['image']

        # Test if file is uploaded.
        if not hasattr(image, 'filename') or not image.filename:
            raise TracError(_("No file uploaded."))

        # Get file size.
        if hasattr(image.file, 'fileno'):
            size = os.fstat(image.file.fileno())[6]
        else:
            image.file.seek(0, 2)
            size = image.file.tell()
            image.file.seek(0)
        if size == 0:
            raise TracError(_("Can't upload empty file."))

        # Try to normalize the filename to unicode NFC if we can.
        # Files uploaded from OS X might be in NFD.
        self.log.debug("input filename: %s", image.filename)
        filename = unicodedata.normalize('NFC', to_unicode(image.filename,
          'utf-8'))
        filename = filename.replace('\\', '/').replace(':', '/')
        filename = os.path.basename(filename)
        self.log.debug("output filename: %s", filename)

        # Check correct file type.
        reg = re.compile(r'^(.*)[.](.*)$')
        result = reg.match(filename)
        if result:
            if not result.group(2).lower() in self.ext:
                raise TracError(_("Unsupported uploaded file type."))
        else:
            raise TracError(_("Unsupported uploaded file type."))

        return image.file, filename

    def _get_enabled_components(self, req):
        if 'SCREENSHOTS_FILTER' in req.perm:
            # Return existing filter from session or create default.
            if 'screenshots_enabled_components' in req.session:
                components = eval(req.session.get('screenshots_enabled_'
                  'components'))
            else:
                components = self.default_components
                req.session['screenshots_enabled_components'] = str(components)
        else:
            # Users without SCREENSHOTS_FILTER permission uses
            # 'default_components' configuration option.
            components = self.default_components
        return components

    def _set_enabled_components(self, req, components):
        req.session['screenshots_enabled_components'] = str(components)

    def _get_enabled_versions(self, req):
        if 'SCREENSHOTS_FILTER' in req.perm:
            # Return existing filter from session or create default.
            if 'screenshots_enabled_versions' in req.session:
                versions = eval(req.session.get('screenshots_enabled_versions'))
            else:
                versions = self.default_versions
                req.session['screenshots_enabled_versions'] = str(versions)
        else:
            # Users without SCREENSHOTS_FILTER permission uses
            # 'default_versions' configuration option.
            versions = self.default_versions
        return versions

    def _set_enabled_versions(self, req, versions):
        req.session['screenshots_enabled_versions'] = str(versions)

    def _get_filter_relation(self, req):
        if 'SCREENSHOTS_FILTER' in req.perm:
            # Return existing filter relation from session or create default.
            if 'screenshots_filter_relation' in req.session:
                relation = req.session.get('screenshots_filter_relation')
            else:
                relation = self.default_filter_relation
                req.session['screenshots_filter_relation'] = relation
        else:
            # Users without SCREENSHOTS_FILTER permission uses
            # 'default_filter_relation' configuration option.
            relation = self.default_filter_relation
        return relation

    def _set_filter_relation(self, req, relation):
        req.session['screenshots_filter_relation'] = relation

    def _get_orders(self, req):
        if 'SCREENSHOTS_ORDER' in req.perm:
            # Get ordering fields from session or default ones.
            if 'screenshots_orders' in req.session:
                orders = eval(req.session.get('screenshots_orders'))
            else:
                orders = tuple(self.default_orders)
                directions = tuple(self.default_order_directions)
                orders = [(orders[I], directions[I]) for I in \
                  xrange(len(orders))]
                req.session['screenshots_orders'] = str(orders)
        else:
            # Users without SCREENSHOTS_ORDER permission uses
            # 'default_orders' configuration option.
            orders = tuple(self.default_orders)
            directions = tuple(self.default_order_directions)
            orders = [(orders[I], directions[I]) for I in xrange(len(orders))]
        return tuple(orders)

    def _set_orders(self, req, orders):
        req.session['screenshots_orders'] = str(orders)
