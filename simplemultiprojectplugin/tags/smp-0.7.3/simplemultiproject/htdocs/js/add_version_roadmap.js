jQuery(document).ready(function($) {
  $('div.milestones').append('<div id="smp-version"></div>')

  $('#smp-version').load('./smpversionroadmap?' + smp_query_string);
});
