/* Add an 'Add new Version' button to the roadmap page */
jQuery(document).ready(function($) {
    if(smp_add_version !== undefined){
        $('div.buttons:nth-of-type(2)').append(smp_add_version);
    }
});
