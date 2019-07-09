jQuery(document).ready(function($) {
  $('#info').before('<div id="peer-status"></div>');

  var data = 'peer_path=' + peer_path + '&peer_repo=' + peer_repo + '&peer_is_head=' + peer_is_head + '&peer_rev=' + peer_rev
  data += '&peer_is_dir=' + peer_is_dir
  $('#peer-status').load(peer_status_url, data, function(){


  });
});