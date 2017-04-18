/*

Copyright 2010-2011, 2014 Stefan Goebel - <tracsecdl -at- subtype -dot- de>

This file is part of TracSecDl.

TracSecDl is free software: you can redistribute it and/or modify it under the
terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

TracSecDl is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
TracSecDl. If not, see <http://www.gnu.org/licenses/>.

*/

// Show or hide the extended information in the download table for ID 'id'.

function toggle_info (id) {
    var new_style = 'none';
    var new_link  = '+';
    if (jQuery ('#ext_info_' + id).css ('display') =='none') {
        new_style = 'table-row';
        new_link  = '-';
    }
    jQuery ('#ext_info_' + id).css  ('display', new_style);
    jQuery ('#ext_link_' + id).html (new_link);
}

// Expand the SHA512 checksum in the download table for ID 'id'.

function toggle_sha (id) {
    jQuery ('#ext_sha_' + id).html (jQuery ('#ext_sha_' + id).attr ('title'));
}

// Add another text input field to the enum formular.

function add_enum_input () {
    jQuery ('#newenums').append (jQuery ('#inputtemplate').html ());
    jQuery ('#newenums > input').focus ();
    submit = jQuery ('#submitenums').attr ('value');
    if (submit.substring (submit.length - 1) != 's') {
        jQuery ('#submitenums').attr ('value', submit + 's');
    }
}

// Remove the input fields added by add_enum_input().

function del_enum_input () {
    jQuery ('#newenums > input').remove ();
    submit = jQuery ('#submitenums').attr ('value');
    if (submit.substring (submit.length - 1) == 's') {
        jQuery ('#submitenums').attr (
            'value', submit.substring (0, submit.length - 1)
        );
    }
}

/* :indentSize=4:tabSize=4:noTabs=true:mode=javascript:maxLineLen=79: */