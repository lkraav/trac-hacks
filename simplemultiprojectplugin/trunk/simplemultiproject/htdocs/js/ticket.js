/* Copyright (C) 2020 Cinc */
jQuery(document).ready(function($) {

    function comp_list(prj_id){
        $('#field-component').html(smp_component_map[prj_id]);
        if(smp_component_sel){
            $('#field-component').val(smp_component_sel)
        };
        var cur_sel = $('#field-component :selected').val();
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
        var cur_sel = $('#field-version :selected').val();
        if(cur_sel !== undefined){
            $('#smp-version-warn').hide();
        }
        else{
            $('#smp-version-warn').show();
        }
    };

    function ms_list(prj_id){
        $('#field-milestone').html(smp_milestone_map[prj_id]);
        if(smp_milestone_sel){
            $('#field-milestone').val(smp_milestone_sel)
        };
        var cur_sel = $('#field-milestone :selected').val();
        if(cur_sel !== undefined){
            $('#smp-milestone-warn').hide();
        }
        else{
            $('#smp-milestone-warn').show();
        }
    };

    function get_cur_prj_id(){
        var cur_prj = smp_project_map[$('#field-project').val()]
        if(cur_prj === undefined){
            cur_prj = '0';
        };
        return cur_prj;
    };

    $('#field-project').change(function() {
        var cur_prj = get_cur_prj_id();
        comp_list(cur_prj);
        ver_list(cur_prj);
        ms_list(cur_prj);
    });

    var cur_prj = get_cur_prj_id();
    /* Save initial selection so we remember ist after project changes */
    smp_component_sel = $('#field-component :selected').val();
    smp_version_sel = $('#field-version :selected').val();
    smp_milestone_sel = $('#field-milestone :selected').val();
    comp_list(cur_prj);
    ver_list(cur_prj);
    ms_list(cur_prj);

    $('#properties').after(smp_component_warning)
    $('#properties').after(smp_version_warning)
    $('#properties').after(smp_milestone_warning)
});
