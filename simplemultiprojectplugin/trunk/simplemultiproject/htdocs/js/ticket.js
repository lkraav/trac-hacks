/* Copyright (C) 2020 Cinc */
jQuery(document).ready(function($) {

    function comp_list(prj_id){
        $('#field-component').html(smp_component_map[prj_id]);
        if(smp_component_sel){
            $('#field-component').val(smp_component_sel)
        };
        var cur_sel = $('#field-component').children("option:selected").val();
        if(cur_sel !== undefined){
            $('#smp-comp-warn').hide();
        }
        else{
            $('#smp-comp-warn').show();
        }
    };

    function ver_list(prj_id){
        $('#field-version').html(smp_version_map[prj_id]);
        if(smp_version_sel){
            $('#field-version').val(smp_version_sel)
        };
        var cur_sel = $('#field-version').children("option:selected").val();
        if(cur_sel !== undefined){
            $('#smp-version-warn').hide();
        }
        else{
            $('#smp-version-warn').show();
        }
    };

    $('#field-project').change(function() {
        var cur_prj = smp_project_map[$('#field-project').val()]
        comp_list(cur_prj);
        ver_list(cur_prj);
    });

    var cur_prj = smp_project_map[$('#field-project').val()]
    /* Save initial selection so we remember ist after project changes */
    smp_component_sel = $('#field-component').children("option:selected").val();
    smp_version_sel = $('#field-version').children("option:selected").val();

    comp_list(cur_prj);
    ver_list(cur_prj);

    $('#properties').after(smp_component_warning)
    $('#properties').after(smp_version_warning)
});
