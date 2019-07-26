jQuery(function ($) {
  function addAutocompleteBehavior() {
    var filters = $('#filters');
    var contains = $.contains // jQuery 1.4+
      || function (container, contained) {
      while (contained !== null) {
        if (container === contained)
          return true;
        contained = contained.parentNode;
      }
      return false;
    };
    var listener = function (event) {
      var target = event.target || event.srcElement;
      filters.each(function () {
        if (contains(this, target)) {
          var input = $(this).find('input:text').filter(function () {
            return target === this;
          });
          var field_names = 'owner|reporter|cc';
          if (autocomplete_fields.length > 0) {
            field_names = field_names + '|' + autocomplete_fields.join('|');
          }
          var name = input.attr('name');
          var re = new RegExp('^(?:[0-9]+_)?(?:' + field_names + ')$');
          if (input.attr('autocomplete') !== 'off' && re.test(name)) {
            input.autocomplete('subjects', {formatItem: formatItem,
              multiple: /cc$/.test(name)});
            input.focus(); // XXX Workaround for Trac 0.12.2 and jQuery 1.4.2
          }
        }
      });
    };
    if ($.fn.on) {
      // delegate method is available in jQuery 1.7+
      filters.on('focusin', 'input:text', listener);
    }
    else if ($.fn.delegate) {
      // delegate method is available in jQuery 1.4.2+
      filters.delegate('input:text', 'focus', listener);
    }
    else if (window.addEventListener) {
      // use capture=true cause focus event doesn't bubble in the default
      filters.each(function () {
        this.addEventListener('focus', listener, true);
      });
    }
    else {
      // focusin event bubbles, the event is avialable for IE only
      filters.each(function () {
        this.attachEvent('onfocusin', listener);
      });
    }
  }
  addAutocompleteBehavior();
});
