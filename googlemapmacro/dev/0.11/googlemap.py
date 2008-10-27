""" Copyright (c) 2008 Martin Scharrer <martin@scharrer-online.de>
    v0.1 - Oct 2008
    This is Free Software under the GPL v3!
""" 
from genshi.builder import Element,tag
from StringIO import StringIO
from trac.core import *
from trac.util.html import escape,Markup
from trac.wiki.api import parse_args
from trac.wiki.formatter import extract_link
from trac.wiki.macros import WikiMacroBase
from trac.web.api import IRequestFilter
from trac.web.chrome import add_script
from urllib import urlopen,quote_plus
import md5
import re

_allowed_args = ['center','zoom','size','address']

_reWHITESPACES = re.compile(r'\s+')
_reWHITEENDS   = re.compile(r'(?:^\s+|\s+$)')
_reCOMMA       = re.compile(r',\s*')
_reCOMMA       = re.compile(r',\s*')

class GoogleMapMacro(WikiMacroBase):
    implements(IRequestFilter)
    """ Provides a macro to insert Google Maps(TM) in Wiki pages
    """
    nid = 0


    # IRequestFilter#pre_process_request
    def pre_process_request(self, req, handler):
        return handler


    # IRequestFilter#post_process_request
    def post_process_request(self, req, template, data, content_type):
        key = self.env.config.get('googlemap', 'api_key', None)
        if key:
            #add_script(req, r"http://maps.google.com/maps?file=api&v=2&key=%s" % key )

            # add_script hack to support external script files:
            url = r"http://maps.google.com/maps?file=api&v=2&key=%s" % key
            scriptset = req.chrome.setdefault('scriptset', set())
            if not url in scriptset:
                script = {'href': url, 'type': 'text/javascript'}
                req.chrome.setdefault('scripts', []).append(script)
                scriptset.add(url)
        return (template, data, content_type)

    def _format_address(self, address):
        self.env.log.debug("address before = %s" % address)
        address = address.replace(';',',')
        if ((address.startswith('"') and address.endswith('"')) or
            (address.startswith("'") and address.endswith("'"))):
                address = address[1:-1]
        address = _reWHITEENDS.sub('', address)
        address = _reWHITESPACES.sub(' ', address)
        address = _reCOMMA.sub(', ', address)
        self.env.log.debug("address after  = %s" % address)
        return address

    def _get_coords(self, address):
        m = md5.new()
        m.update(address)
        hash = m.hexdigest()

        db = self.env.get_db_cnx()
        cursor = db.cursor()
        #try:
        cursor.execute("SELECT lon,lat FROM googlemapmacro WHERE id='%s'" % hash)
        #except:
        #    pass
        #else:
        for row in cursor:
            if len(row) == 2:
                self.env.log.debug("Reusing coordinates from database")
                return ( str(row[0]), str(row[1]) )

        response = None
        url = r'http://maps.google.com/maps/geo?output=csv&q=' + quote_plus(address)
        try:
            response = urlopen(url).read()
        except:
            return
        resp = response.split(',')
        if len(resp) != 4 or not resp[0] == "200":
            return
        lon, lat = resp[2:4]

        #try:
        cursor.execute(
            "INSERT INTO googlemapmacro VALUES ('%s', %s, %s)" %
            (hash, lon, lat))
        db.commit()
        self.env.log.debug("Saving coordinates to database")
        #except:
        #    pass

        return (lon, lat)


    def expand_macro(self, formatter, name, content):
        args, kwargs = parse_args(content)
        if len(args) > 0 and not 'address' in kwargs:
            kwargs['address'] = args[0]

        # HTML arguments used in Google Maps URL
        hargs = {
            'zoom'   : "6",
            'size'   : self.env.config.get('googlemap', 'default_size', "300x300"),
           # 'hl'     : self.env.config.get('googlemap', 'default_language', ""),
            }

        key = self.env.config.get('googlemap', 'api_key', None)
        if not key:
            raise TracError("No Google Maps API key given! Tell your web admin to get one at http://code.google.com/apis/maps/signup.html .\n")


        ## Delete default zoom if user provides 'span' argument:
        #if 'span' in kwargs:
        #    del hargs['zoom']

        # Copy given macro arguments to the HTML arguments
        for k,v in kwargs.iteritems():
            if k in _allowed_args:
                hargs[k] = v

        # Get height and width
        (width,height) = hargs['size'].split('x')
        width = int(width)
        height = int(height)
        if height < 1:
            height = 1
        elif height > 640:
            height = 640
        else:
            height = str(height) + "px"
        if width < 1:
            width = 1
        elif width > 640:
            width = 640
        else:
            width = str(width) + "px"

        address = ""
        if 'address' in hargs:
            address = self._format_address(hargs['address'])
            if not 'center' in kwargs:
                coord = self._get_coords(address)
                if not coord or len(coord) != 2:
                    raise TracError("Given address '%s' couldn't be resolved by Google Maps!" % address);
                hargs['center'] = ",".join(coord)
                hargs['address'] = "" # delete address when coordinates are resolved
                address = ""

        # Correct separator for 'center' argument because comma isn't allowed in
        # macro arguments
        hargs['center'] = hargs['center'].replace(':',',')

        # Build URL
        #src = _google_src + ('&'.join([ "%s=%s" % (escape(k),escape(v)) for k,v in hargs.iteritems() ]))

        #title = alt = "Google Static Map at %s" % hargs['center']
        # TODO: provide sane alternative text and image title

        #if 'title' in kwargs:
        #    title = kwargs['title']

        # Produce unique id for div tag
        GoogleMapMacro.nid += 1
        #idhash = hashlib.md5()
        #idhash.update( content )
        #id = "tracgooglemap-%i-%s" % (GoogleMapMacro.nid, idhash.hexdigest())
        id = "tracgooglemap-%i" % GoogleMapMacro.nid


        html = tag.div(
                [
        #        tag.script (
        #            "",
        #            src  = ( r"http://maps.google.com/maps?file=api&v=2&key=%s" % hargs['key'] ),
        #            type = "text/javascript",
        #        ),
                tag.script (
                    """
                    //<![CDATA[
                    $(document).ready( function () {
                      if (GBrowserIsCompatible()) {
                        var map = new GMap2(document.getElementById("%(id)s"));
                        map.addControl(new GLargeMapControl());
                        map.addControl(new GMapTypeControl());
                        map.setCenter(new GLatLng(%(center)s), %(zoom)s);
                    }} );

                    $(window).unload( GUnload );
                    //]]>
                    """ % { 'id':id, 'center':hargs['center'],
                        'zoom':hargs['zoom'], 'address':address },
                    type = "text/javascript"),
                tag.div (
                    "",
                    id=id,
                    style="width: %s; height: %s" % (width,height),
                )
                ],
                class_ = "tracgooglemaps",
                );

        return html;

