# -*- coding: utf-8 -*-
"""
API for administrating custom ticket fields in Trac.
Supports creating, getting, updating and deleting custom fields.

License: BSD

(c) 2005-2008 ::: www.CodeResort.com - BV Network AS (simon-code@bvnetwork.no)
"""

import re

from trac.core import *
from trac.ticket.model import TicketSystem

__all__ = ['CustomFields']

class CustomFields(Component):
    """ These methods should be part of TicketSystem API/Data Model.
    Adds update_custom_field and delete_custom_field methods.
    (The get_custom_fields is already part of the API - just redirect here,
     and add option to only get one named field back.)
    
    Input to methods is a 'customfield' dict supporting these keys:
        name = name of field (alphanumeric only)
        type = text|checkbox|select|radio|textarea
        label = label description
        value = default value for field content
        options = options for select and radio types (list, leave first empty for optional)
        cols = number of columns for text area
        rows = number of rows for text area
        order = specify sort order for field
    """
    
    def get_custom_fields(self, env, customfield={}):
        """ Returns the custom fields from TicketSystem component.
        Use a cfdict with 'name' key set to find a specific custom field only
        """
        if not customfield:    # return full list
            return TicketSystem(env.compmgr).get_custom_fields()
        else:                  # only return specific item with cfname
            all = TicketSystem(env.compmgr).get_custom_fields()
            for item in all:
                if item['name'] == customfield['name']:
                    return item
            return None        # item not found
    
    def verify_custom_field(self, env, customfield, create=True):
        """ Basic validation of the input for modifying or creating
        custom fields. """
        # Name, Type and Label is required
        if not (customfield.get('name') and customfield.get('type') \
                and customfield.get('label')):
            raise TracError("Custom field needs at least a name, type and label.")
        # Use lowercase custom fieldnames only
        customfield['name'] = customfield['name'].lower()
        # Only alphanumeric characters (and [-_]) allowed for custom fieldname
        if re.search('^[a-z0-9-_]+$', customfield['name']) == None:
           raise TracError("Only alphanumeric characters allowed for custom field name (a-z or 0-9 or -_).")
        # Check that it is a valid field type
        if not customfield['type'] in ['text', 'checkbox', 'select', 'radio', 'textarea']:
            raise TracError("%s is not a valid field type" % customfield['type'])
        # Check that field does not already exist (if modify it should already be deleted)
        if create and env.config.get('ticket-custom', customfield['name']):
            raise TracError("Can not create as field already exists.")
    
    def create_custom_field(self, env, customfield):
        """ Create the new custom fields (that may just have been deleted as part
        of 'modify'). Note: Caller is responsible for verifying input before create."""
        # Set the mandatory items
        env.config.set('ticket-custom', customfield['name'], customfield['type'])
        env.config.set('ticket-custom', customfield['name'] + '.label', customfield['label'])
        # Optional items
        if 'value' in customfield:
            env.config.set('ticket-custom', customfield['name'] + '.value', customfield['value'])
        if 'options' in customfield:
            env.config.set('ticket-custom', customfield['name'] + '.options', '|'.join(customfield['options']))
        # Textarea
        if customfield['type'] == 'textarea':
            cols = customfield.get('cols') and int(customfield.get('cols', 0)) > 0 \
                                                and customfield.get('cols') or 60
            rows = customfield.get('rows', 0) and int(customfield.get('rows', 0)) > 0 \
                                                and customfield.get('rows') or 5
            env.config.set('ticket-custom', customfield['name'] + '.cols', cols)
            env.config.set('ticket-custom', customfield['name'] + '.rows', rows)
        # Order
        order = customfield.get('order', "")
        if order == "":
            order = len(self.get_custom_fields(env))
        env.config.set('ticket-custom', customfield['name'] + '.order', order)
        env.config.save()

    def update_custom_field(self, env, customfield, create=False):
        """ Updates a custom. Option to 'create' is kept in order to keep
        the API backwards compatible. """
        if create:
            self.verify_custom_field(env, customfield)
            self.create_custom_field(env, customfield)
            return
        # Check input, then delete and save new
        self.verify_custom_field(env, customfield, create=False)
        self.delete_custom_field(env, customfield, modify=True)
        self.create_custom_field(env, customfield)
    
    def delete_custom_field(self, env, customfield, modify=False):
        """ Deletes a custom field.
        Input is a dictionary (see update_custom_field), but only ['name'] is required.
        """
        if not env.config.get('ticket-custom', customfield['name']):
            return # Nothing to do here - cannot find field
        if not modify:
            # Permanent delete - reorder later fields to lower order
            order_to_delete = env.config.getint('ticket-custom', customfield['name']+'.order')
            cfs = self.get_custom_fields(env)
            for field in cfs:
                if field['order'] > order_to_delete:
                    env.config.set('ticket-custom', field['name']+'.order', field['order'] -1 )
        # Remove any data for the custom field (covering all bases)
        env.config.remove('ticket-custom', customfield['name'])
        env.config.remove('ticket-custom', customfield['name'] + '.label')
        env.config.remove('ticket-custom', customfield['name'] + '.value')
        env.config.remove('ticket-custom', customfield['name'] + '.options')
        env.config.remove('ticket-custom', customfield['name'] + '.cols')
        env.config.remove('ticket-custom', customfield['name'] + '.rows')
        env.config.remove('ticket-custom', customfield['name'] + '.order')
        # Persist permanent deletes
        if not modify:
            env.config.save()
