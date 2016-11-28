# -*- coding: utf-8 -*-

import re

from trac.core import Component, implements
from trac.resource import Resource
from trac.util import to_list
from trac.util.html import html
from trac.util.text import pretty_size, to_unicode
from trac.web.chrome import Chrome
from trac.wiki import IWikiMacroProvider, IWikiSyntaxProvider

from tracdownloads.api import DownloadsApi


class DownloadsWiki(Component):
    """
        The wiki module implements macro for downloads referencing.
    """
    implements(IWikiSyntaxProvider, IWikiMacroProvider)

    # Macros documentation.
    downloads_count_macro_doc = """ """
    list_downloads_macro_doc = """ """

    # IWikiSyntaxProvider
    def get_link_resolvers(self):
        yield 'download', self._download_link

    def get_wiki_syntax(self):
        return []

    # IWikiMacroProvider

    def get_macros(self):
        yield 'DownloadsCount'
        yield 'ListDownloads'

    def get_macro_description(self, name):
        if name == 'DownloadsCount':
            return self.downloads_count_macro_doc
        if name == 'ListDownloads':
            return self.list_downloads_macro_doc

    def expand_macro(self, formatter, name, content):
        if name == 'DownloadsCount':
            api = self.env[DownloadsApi]

            # Check empty macro content.
            download_ids = []
            if content and content.strip() != '':
                # Get download IDs or filenames from content.
                items = to_list(content)

                # Resolve filenames to IDs.
                for item in items:
                    try:
                        # Try if it's download ID first.
                        download_id = int(item)
                        if download_id:
                            download_ids.append(download_id)
                        else:
                            # Any zero ID means all downloads.
                            download_ids = []
                            break
                    except ValueError:
                        # If it wasn't ID resolve filename.
                        download_id = api.get_download_id_from_file(item)
                        if download_id:
                            download_ids.append(download_id)
                        else:
                            self.log.debug("Could not resolve download "
                                           "filename to ID.")

            # Empty list mean all.
            if len(download_ids) == 0:
                download_ids = None

            # Ask for aggregated downloads count.
            self.log.debug(download_ids)
            count = api.get_number_of_downloads(download_ids)

            # Return simple <span> with result.
            return html.span(to_unicode(count), class_="downloads_count")

        elif name == 'ListDownloads':
            # Determine wiki page name.
            page_name = formatter.req.path_info[6:] or 'WikiStart'

            api = self.env[DownloadsApi]

            # Get form values.
            req = formatter.req
            order = req.args.get('order') or 'id'
            desc = req.args.get('desc')
            has_tags = self.env.is_component_enabled('tractags.api.TagEngine')
            visible_fields = self.config.getlist('downloads',
                                                 'visible_fields')

            # Prepare template data.
            data = {
                'order': order,
                'desc': desc,
                'has_tags': has_tags,
                'downloads': api.get_downloads(order, desc),
                'visible_fields': visible_fields,
                'page_name': page_name
            }

            # Return rendered template.
            return to_unicode(Chrome(self.env)
                              .render_template(formatter.req,
                                               'wiki-downloads-list.html', {
                                                    'downloads': data
                                               }, 'text/html', True))

    # Internal functions

    def _download_link(self, formatter, ns, params, label):
        if ns == 'download':
            if 'DOWNLOADS_VIEW' in formatter.req.perm:
                api = self.env[DownloadsApi]

                # Get download.
                if re.match(r'\d+', params):
                    download = api.get_download(params)
                else:
                    download = api.get_download_by_file(params)

                if download:
                    resource = Resource('downloads', download['id'])
                    if 'DOWNLOADS_VIEW' in formatter.req.perm(resource):
                        # Return link to existing file.
                        return html.a(label,
                                      href=formatter.href.downloads(params),
                                      title='%s (%s)'
                                            % (download['file'],
                                               pretty_size(download['size'])))
                    else:
                        # File exists but no permission to download it.
                        html.a(label, href='#', title='%s (%s)' % (
                            download['file'], pretty_size(download['size'])),
                               class_='missing')
                else:
                    # Return link to non-existing file.
                    return html.a(label, href='#', title='File not found.',
                                  class_='missing')
            else:
                # Return link to file to which is no permission. 
                return html.a(label, href='#', title='No permission to file.',
                              class_='missing')
