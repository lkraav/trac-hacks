jQuery(function($) {
  function smp_updateSelect(id, newOptions, selectedOption)
  {
    var field_id = '#field-' + id;
    var select = $(field_id);
    var options;
    if (select.prop) {
      options = select.prop('options');
    }
    else {
      options = select.attr('options');
    }
    select.empty();

    var addedOptions = [];
    if (options && newOptions) {
      $.each(newOptions, function(val, text) {
        var isSelected = (selectedOption && text == selectedOption);
        options[options.length] = new Option(text, text, isSelected, isSelected);
        addedOptions.push(text);
      });
    }

    if (options && selectedOption && $.inArray(selectedOption, addedOptions) == -1) {
      options[options.length] = new Option(selectedOption, selectedOption, true, true);
    }

    // call custom event trigger to allow other plugins to notify the change
    $(field_id).trigger("onUpdate");
  }

  function smp_onProjectChange(project)
  {
    // milestones
    var milestones = smp_milestonesForProject[project];
    var selectedMilestone = "";

    if (project == smp_initialProjectMilestone[0]) {
      selectedMilestone = smp_initialProjectMilestone[1];
    }
    smp_updateSelect('milestone', milestones, selectedMilestone);

    // components
    var components = smp_all_components;
    var cur_comp = $('#field-component option:selected').text();
    var filtered_components = [];
    var cur_comp_valid = false;

    for (var i = 0; i < components.length; i++) {
      var comp = components[i];
      if (!smp_component_projects[comp] || $.inArray(project, smp_component_projects[comp]) != -1) {
        filtered_components.push(comp);
        cur_comp_valid = cur_comp_valid || (comp == cur_comp);
      }
    }

    if (!cur_comp || cur_comp == "" || !cur_comp_valid) {
      cur_comp = smp_default_component;
    }

    smp_updateSelect('component', filtered_components, cur_comp);

    // versions
    smp_updateSelect('version', smp_project_versions[project], smp_default_version);
  }

  var $project = $('#field-project');
  var project_name = $project.val();
  smp_onProjectChange(project_name);
  $project.change(function() {
    // TracDynamicField triggers the change event during preview,
    // so only trigger if the project is actually changed.
    if (this.value !== project_name) {
      smp_onProjectChange(this.value)
      project_name = this.value;
    }
  });

});
