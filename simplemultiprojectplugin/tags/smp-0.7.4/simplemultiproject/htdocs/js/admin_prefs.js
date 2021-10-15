/* Copyright (C) 2020 Cinc */
jQuery(document).ready(function($) {

    /* Set the title of each project permission to the project name */
    for(perm in smp_permissions){
        $('#action option:contains(' + perm + ')').prop('title', smp_permissions[perm]);
        $("span[title='" + perm + "']").each(function(){
            $(this).prop('title', smp_permissions[perm]);
        });
    };
});