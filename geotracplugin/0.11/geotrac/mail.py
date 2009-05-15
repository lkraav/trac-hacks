"""
mail2trac handler for email with a location.  
the location is denoted with a '@' in the subject line:

Subject: loud music @ 349 W. 12 St., New York, NY
"""

from geotrac.ticket import GeolocationException
from geotrac.ticket import GeoTrac
from trac.config import BoolOption

try:
    from mail2trac.email2trac import EmailException
    from mail2trac.email2ticket import EmailToTicket

    class GeoMailToTicket(EmailToTicket):
        """create a ticket from an email with a location"""

	def order(self):
	   """Force this handler to run first."""
	   return True
        
        def order(self):
	    """Make ourselves show up first"""
	    return True

        def fields(self, message, **fields):

            # if you don't have GeoTrac enabled, why are you using this plugin?
            assert GeoTrac in self.env.components 
            geotrac = self.env.components[GeoTrac]

            subject = message['subject']
            location = ''

            # get the location from the email subject
            if '@' in subject:
                subject, location = [i.strip() for i in subject.rsplit('@', 1)]

                # from help(email.Message.Message) on __setitem__:
                # Note: this does not overwrite an existing header 
                # with the same field name.
                # Use __delitem__() first to delete any existing headers.
                del message['subject']

                # set the message subject, sans location
                message['subject'] = subject

                # geolocate the issue
                try:
                    fields['location'] = geotrac.geolocate(location)[0]
                except GeolocationException, e:
                    # handle multiple and unfound locations
                    if geotrac.mandatory_location:
                        raise EmailException(str(e))
                    else:
                        fields['location'] = location

            else:
                if geotrac.mandatory_location:
                    raise EmailException('Location required. Please email with "%s @ <location>" in your subject.' % subject)

            return EmailToTicket.fields(self, message, **fields)


except ImportError:
    pass
