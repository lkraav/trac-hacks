from pkg_resources import resource_filename

from trac.core import *
from trac.util.text import unicode_quote_plus
from trac.web.api import IRequestFilter
from trac.web.chrome import ITemplateProvider, add_script
from trac.ticket.roadmap import TicketGroupStats

class SubComponentsModule(Component):
    """Implements subcomponents in Trac's interface."""
    
    implements(IRequestFilter, ITemplateProvider)
 
    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler
    
    def post_process_request(self, req, template, data, content_type):
        if req.path_info.startswith('/ticket/') or \
           req.path_info.startswith('/newticket') or \
           req.path_info.startswith('/query'):
            add_script(req, 'subcomponents/componentselect.js')
                                 
        if template == "query.html":
            # Allow users to query for parent components and include all subs
            data['modes']['select'].insert(0, {'name': "begins with", 'value': "^"})

        if template == "milestone_view.html":
            if data['grouped_by'] == "component":
                componentname = ''
                newgroups = []
                newcomponents = []
                for component in data['groups']:
                    componentname = component['name'].split('/')[0]
                    if componentname not in newcomponents:
                        # This component is not yet in the new list of components, add it.
                        newcomponents.append(componentname)
                        # Fix URLs to the querys (we use unicode_quote_plus to replace the '/'
                        # with something URL safe (like the hrefs are)
                        new_hrefs = []
                        for interval_href in component['interval_hrefs']:
                            new_hrefs.append(interval_href.replace(unicode_quote_plus(component['name']), '^' + componentname))
                        component['stats_href'] = component['stats_href'].replace(unicode_quote_plus(component['name']), '^' + componentname)
                        component['interval_hrefs'] = new_hrefs
                        # Set the name to the base name (in case this originally
                        # is a subcomponent.
                        component['name'] = componentname
                        
                        newgroups.append(component)
                    else:
                        # This is a subcomponent. Add the stats to the main component.
                        # Note that above two lists are created. Whenever an
                        # item is added to one, an analogous one is added to
                        # the other. This code uses that logic.
                        corecomponent = newgroups[newcomponents.index(componentname)]
                        mergedstats = corecomponent['stats'] #TicketGroupStats from trac.ticket.roadmap
                        newstats = component['stats']
                        
                        # Bear with me as we go to this mess that is the group stats
                        # (or of course this hack, depending on who's viewpoint).
                        # First merge the totals
                        mergedstats.count += newstats.count 
                        
                        # The stats are divided in intervals, merge these.
                        i = 0
                        for interval in mergedstats.intervals:
                            newinterval = newstats.intervals[i]
                            interval['count'] += newinterval['count']
                            i += 1
                        mergedstats.refresh_calcs()
                
                # Now store the new milestone component groups
                data['groups'] = newgroups
        return template, data, content_type        
 
  
    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        """Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc).
        """
        return [('subcomponents', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        """Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        return [resource_filename(__name__, 'templates')]


