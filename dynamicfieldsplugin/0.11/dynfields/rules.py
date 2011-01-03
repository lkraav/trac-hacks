import re
from trac.core import *

class IRule(Interface):
    """An extension point interface for adding rules.  Rule processing
    is split into two parts: (1) rule specification (python), (2) rule
    implementation (JS).
    
    The python and JS parts are linked by instantiating the JS rule
    implementation with the corresponding python rule's class name.
    For example, the JS rule implementation corresponding with the
    HideRule python class must be instantiated as follows in rules.js:
    
      var hiderule = new Rule('HideRule');
    """
    
    def get_trigger(self, target, key, opts):
        """Return the field name that triggers the rule, or None if not found
        for the given target field and ticket-custom options key and dict.
        For example, if the 'version' field is to be hidden based on the
        ticket type, then the returned trigger field name should be 'type'."""
       
    def update_spec(self, req, key, opts, spec):
        """Update the spec dict with the rule's specifications needed for
        the JS implementation.  The spec dict is defaulted to include the
        rule's name (rule_name), the trigger field's name (trigger), the
        target field's name (target), and the preference or default value
        if applicable (value)."""
    
    def update_pref(self, req, trigger, target, key, opts, pref):
        """Update the pref dict with the data needed for preferences.
        The primary dict keys to change are:
        
          label (of checkbox)
          type ('none' or 'select')
        
        Default values for the above are provided as well as for the
        keys below (which should usually not be changed):
        
          id (based on unique key)
          enabled ('1' or '0')
          options (list of options if type is 'select')
          value (saved preference or default value)
        """


class Rule(object):
    """Abstract class for common rule properties and utilities."""
    
    @property
    def name(self):
        """Returns the rule instance's class name.  The corresponding
        JS rule must be instantiated with this exact name."""
        return self.__class__.__name__
    
    @property
    def title(self):
        """Returns the rule class' title used for display purposes.
        This default implementation returns the rule's name with any
        camel case split into words and the last word made plural.
        This property/method can be overriden as needed."""
        # split CamelCase to Camel Case
        title = self._split_camel_case(self.name)
        if not title.endswith('s'):
            title += 's'
        return title
    
    @property
    def desc(self):
        """Returns the description of the rule.  This default implementation
        returns the first paragraph of the docstring as the desc."""
        return self.__doc__.split('\n')[0]
    
    # private methods
    def _capitalize(self, word):
        if len(word) <= 1:
            return word.upper()
        return word[0].upper() + word[1:]
    
    def _split_camel_case(self, s):
        return re.sub('((?=[A-Z][a-z])|(?<=[a-z])(?=[A-Z]))', ' ', s)
    

class ClearRule(Component, Rule):
    """Clears one field when another changes.
    
    Example trac.ini specs:
    
      [ticket-custom]
      version.clear_on_change_of = milestone
    """
    
    implements(IRule)
    
    def get_trigger(self, target, key, opts):
        if key == '%s.clear_on_change_of' % target:
            return opts[key]
        return None
        
    def update_spec(self, req, key, opts, spec):
        target = spec['target']
        spec['op'] = 'clear'
        spec['clear_on_change'] = opts.get(target+'.clear_on_change','true')

    def update_pref(self, req, trigger, target, key, opts, pref):
        pref['label'] = "Clear %s when %s changes" % (target, trigger)


class CopyRule(Component, Rule):
    """Copies a field (when changed) to another field (if empty and visible).
    
    Example trac.ini specs:
    
      [ticket-custom]
      captain.copy_from = owner
      captain.overwrite = true
      
    In this example, if the owner value changes, then the captain field's
    value gets set to that value if the captain field is empty and visible
    (the default).  If overwrite is true, then the captain field's value
    will get over-written even if it already has a value (and even if it's
    hidden).
    """
    
    implements(IRule)
    
    def get_trigger(self, target, key, opts):
        if key == '%s.copy_from' % target:
            return opts[key]
        return None
        
    def update_spec(self, req, key, opts, spec):
        spec['op'] = 'copy'
        spec['overwrite'] = opts.get(spec['target']+'.overwrite','false')

    def update_pref(self, req, trigger, target, key, opts, pref):
        pref['label'] = "Copy %s to %s" % (trigger, target)


class DefaultValueRule(Component, Rule):
    """Defaults a field to a user-specified value.
    
    Example trac.ini specs:
    
      [ticket-custom]
      type.default_value = (pref)
    """
    
    implements(IRule)
    
    def get_trigger(self, target, key, opts):
        if key == '%s.default_value' % target:
            return target
        return None
        
    def update_spec(self, req, key, opts, spec):
        pass
    
    def update_pref(self, req, trigger, target, key, opts, pref):
        # "Default trigger to <select options>"
        pref['label'] = "Default %s to" % target
        pref['type'] = 'select'


class HideRule(Component, Rule):
    """Hides a field based on another field's value (or always).
    
    Example trac.ini specs:
    
      [ticket-custom]
      version.show_when_type = enhancement
      milestone.hide_when_type = defect
      alwayshide.hide_always = True
      alwayshide.clear_on_hide = False
    """
    
    implements(IRule)
    
    def get_trigger(self, target, key, opts):
        rule_re = re.compile(r"%s.(?P<op>(show|hide))_when_(?P<trigger>.*)" \
                             % target)
        match = rule_re.match(key)
        if match:
            return match.groupdict()['trigger']
            
        # try finding hide_always rule
        if key == "%s.hide_always" % target:
            return 'type' # requires that 'type' field is enabled
        return None
    
    def update_spec(self, req, key, opts, spec):
        target = spec['target']
        trigger = spec['trigger']
        
        spec_re = re.compile(r"%s.(?P<op>(show|hide))_when_%s" \
                             % (target,trigger))
        match = spec_re.match(key)
        if match:
            spec['op'] = match.groupdict()['op']
            spec['trigger_value'] = opts[key]
            spec['hide_always'] = \
                str(self._is_always_hidden(req, key, opts, spec)).lower()
        else: # assume 'hide_always' rule
            spec['op'] = 'show'
            spec['trigger_value'] = 'invalid_value'
            spec['hide_always'] = 'true'
        spec['clear_on_hide'] = opts.get(target+'.clear_on_hide','true')
        spec['link_to_show'] = opts.get(target+'.link_to_show','false')
    
    def update_pref(self, req, trigger, target, key, opts, pref):
        spec = {'trigger':trigger,'target':target}
        self.update_spec(req, key, opts, spec)
        # "Show/Hide target when trigger = value"
        trigval = spec['trigger_value'].replace('|',' or ')
        pref['label'] = "%s %s when %s = %s" % (self._capitalize(spec['op']),
                                                target, trigger, trigval)
        
        # special case when trigger value is not a select option
        _,options = opts.get_value_and_options(req, trigger, key)
        value = spec['trigger_value']
        if options and value and value not in options and '|' not in value:
            # "Always hide/show target"
            if spec['op'] == 'hide':
                opp = 'show'
            else:
                opp = 'hide'
            pref['label'] = "Always %s %s" % (opp, target)
    
    def _is_always_hidden(self, req, key, opts, spec):
        trigger = spec['trigger']
        _, options = opts.get_value_and_options(req, trigger, key)
        value = spec['trigger_value']
        if options and value and value not in options and '|' not in value:
            return spec['op'] == 'show'
        return False
