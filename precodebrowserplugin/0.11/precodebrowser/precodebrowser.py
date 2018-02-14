# $Id$

from genshi.filters.transform import Transformer
from trac.core import Component, implements
from trac.web.chrome import ITemplateStreamFilter


class PreCodeBrowserPlugin(Component):
    implements(ITemplateStreamFilter)

    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        filter1 = Transformer('//div[@id = "preview"]')
        filter2 = Transformer('//table[@class = "code"]')
        return stream | filter1.attr('class', 'searchable code') | \
            filter2.rename('pre') \
            .select('//pre[@class = "code"]/thead').remove().end() \
            .select('//pre[@class = "code"]/tbody/tr/th').remove().end() \
            .select('//pre[@class = "code"]/tbody/tr/td').append('\n').unwrap()
