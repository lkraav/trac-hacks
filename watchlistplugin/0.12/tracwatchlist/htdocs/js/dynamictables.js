/* Javascript code for Trac Watchlist Plugin
 * $Id$
 * */
/*
 *  TypeWatch 2.0 - Original by Denny Ferrassoli / Refactored by Charles Christolini
 *
 *  Examples/Docs: www.dennydotnet.com
 *
 *  Copyright(c) 2007 Denny Ferrassoli - DennyDotNet.com
 *  Coprright(c) 2008 Charles Christolini - BinaryPie.com
 *
 *  Dual licensed under the MIT and GPL licenses:
 *  http://www.opensource.org/licenses/mit-license.php
 *  http://www.gnu.org/licenses/gpl.html
 *
 *  Modified by Martin Scharrer Sep 2010 to suit the Trac WatchlistPlugin.
 *  Changes:
 *      o Default values
 *      o Removed 'captureLength' code
 *      o Changed arguments to callback function.
 *      o Changed argument to typeWatch function from hash to callback function
 *        only
*/
(function(a){a.fn.typeWatch=function(d){var b={wait:555,callback:d,highlight:true,};function c(h,g){var f=a(h.el).val();if(f!=h.text||g){h.text=f;h.cb(h.el,f)}}function e(g){if(g.type.toUpperCase()=="TEXT"||g.nodeName.toUpperCase()=="TEXTAREA"){var h={timer:null,text:a(g).val().toUpperCase(),cb:b.callback,el:g,wait:b.wait};if(b.highlight){a(g).focus(function(){this.select()})}var f=function(i){var l=h.wait;var k=false;if(i.keyCode==13&&this.type.toUpperCase()=="TEXT"){l=1;k=true}var j=function(){c(h,k)};clearTimeout(h.timer);h.timer=setTimeout(j,l)};a(g).keydown(f)}}return this.each(function(f){e(this)})}})(jQuery);function wldeleterow(b,a){$(a).dataTable().fnDeleteRow(b)}function fnResetAllFilters(a){var b=a.fnSettings();if(b){for(iCol=0;iCol<b.aoPreSearchCols.length;iCol++){b.aoPreSearchCols[iCol].sSearch=""}b.oPreviousSearch.sSearch="";a.fnDraw()}}var TRACWATCHLIST_COOKIE_VERSION=1;var maincookie="TracWatchlistPlugin";$.Jookie.Initialise(maincookie,90*24*60);if(!($.Jookie.Get(maincookie,"version")==TRACWATCHLIST_COOKIE_VERSION)){var cookies=$.Jookie.Get(maincookie,"cookies");if(typeof(cookies)=="Object"){for(cookie in cookies){$.Jookie.Delete(cookie)}}$.Jookie.Delete(maincookie);$.Jookie.Initialise(maincookie,90*24*60);$.Jookie.Set(maincookie,"version",TRACWATCHLIST_COOKIE_VERSION);$.Jookie.Set(maincookie,"cookies",new Object())}jQuery.fn.dataTableExt.oSort["html-numeric-asc"]=function(d,f){var e=parseFloat(d.replace(/<[^>]+>/g,"").replace(/^\s*#/,""));var c=parseFloat(f.replace(/<[^>]+>/g,"").replace(/^\s*#/,""));return((e<c)?-1:((e>c)?1:0))};jQuery.fn.dataTableExt.oSort["html-numeric-desc"]=function(d,f){var e=parseFloat(d.replace(/<[^>]+>/g,"").replace(/^\s*#/,""));var c=parseFloat(f.replace(/<[^>]+>/g,"").replace(/^\s*#/,""));return((e<c)?1:((e>c)?-1:0))};$.fn.dataTableExt.afnFiltering.push(function(e,c,b){var d=$("#"+e.sTableId);var a=true;$(d).find("span.datetimefilter").each(function(){if(!a){return}var g=$(this).data("index");var i=$(this).find("input[name=sincelastvisit]").is(":checked");if(i&&c[g-1]!="1"){a=false}else{timestamp=c[g+1]*1;if(!timestamp){return true}var h=$(this).find("input[name=from-datetime-ts]").val()*1;var f=$(this).find("input[name=to-datetime-ts]").val()*1;if(!h&&!f){}else{if(!h&&timestamp<=f){}else{if(h<=timestamp&&!f){}else{if(h<=timestamp&&timestamp<=f){}else{a=false}}}}}});if(!a){return false}$(d).find("input.numericfilter").each(function(){if(!a){return}var f=$(this).data("index");var h=c[f].replace(/<[^>]+>/g,"").replace("#","");var g=$(this).data("filterfunction");if(g&&!g(h)){a=false}});return a});jQuery(document).ready(function(){try{var b=$("#resetfilters").detach().removeAttr("Id").removeAttr("style")}catch(g){var b=$("#resetfilters").clone().removeAttr("Id").removeAttr("style");$("#resetfilters").remove()}$("#preferences form #deletecookies").click(function(){wldeletecookies();wldisablecookies();window.location.href=window.location.protocol+"//"+window.location.host+window.location.pathname});var f=$.Jookie.Get(maincookie,"cookies");if(typeof(f)!="Object"){f=new Object()}$("table.watchlist").each(function(){var l=this;var n=$(l).attr("id");var k="TracWatchlistPlugin-table#"+n;$.Jookie.Initialise(k,90*24*60);f[k]=1;var m=[];var j=[];$(this).find("thead th").each(function(o){m.push(String($(this).text()).replace(/^\s+|\s+$/g,""));var p=new Object();if($(this).hasClass("hidden")){p.bVisible=false;p.bSortable=false;p.bSearchable=false}if($(this).hasClass("sorting_disabled")){p.bSortable=false;p.bSearchable=false}if($(this).hasClass("filtering_disabled")){p.bSearchable=false;p.sType="html-numeric"}if($(this).hasClass("sort_next")){p.iDataSort=o+1}j.push(p)});if(JSON.stringify(m)!=JSON.stringify($.Jookie.Get(k,"asColumnNames",m))){wldeletecookies("table#"+n);$.Jookie.Initialise(k,90*24*60)}$.Jookie.Set(k,"asColumnNames",m);$(this).find("tfoot th").each(function(o){$(this).data("index",o)});$(this).find("span.datetimefilter").each(function(){var o=$(this).parents("tfoot").find("th").index($(this).parent("th"));$(this).data("index",o)});$(this).find("tfoot input.filter,tfoot input.numericfilter").each(function(){var o=$(l).find("tfoot th").index($(this).parent("th"));$(this).data("index",o)});$(this).dataTable({bStateSave:true,sCookiePrefix:"tracwatchlist_",aoColumns:j,sPaginationType:"full_numbers",bPaginate:true,sDom:'ilp<"resetfilters">frt',sPagePrevious:"&lt;",aLengthMenu:[[10,25,50,100,-1],[10,25,50,100,"&#8734;"]],fnHeaderCallback:function(r,t,q,p,o){if(t.length==0){wlremoveempty(r)}},oLanguage:{sLengthMenu:"_MENU_",sZeroRecords:"./.",sInfo:"_START_-_END_ / _TOTAL_",sInfoEmpty:"./.",sInfoFiltered:"(_MAX_)",sProcessing:"...",sInfoPostFix:"",sSearch:"",sUrl:"",oPaginate:{sFirst:"|&lt;",sPrevious:"&lt;",sNext:"&gt;",sLast:"&gt;|"},fnInfoCallback:null},});var i=$(b).clone();$(i).click(function(){wldelfilters(l);return false});$(l).parent().find("div.resetfilters").append(i)});$.Jookie.Set(maincookie,"cookies",f);$(b).remove();var a=false;if($("#datetime_format").length!=0){a=true;var h=$("#datetime_format").val();var c={format:h,formatUtcOffset:"%: (%@)",labelHour:$("#labelHour").val(),labelMinute:$("#labelMinute").val(),labelSecond:$("#labelSecond").val(),labelYear:$("#labelYear").val(),labelMonth:$("#labelMonth").val(),labelDayOfMonth:$("#labelDayOfMonth").val(),labelTimeZone:$("#labelTimeZone").val(),labelTitle:$("#labelTitle").val(),monthAbbreviations:$("#monthAbbreviations").val().split(","),dayAbbreviations:$("#dayAbbreviations").val().split(","),};var d=$("#tzoffset").val()*1;var e={format:h,utcFormatOffsetImposed:d,utcParseOffsetAssumed:d,}}$("table.watchlist").each(function(){var k=this;var i=$(this).dataTable();var m=$(k).attr("id");var j="TracWatchlistPlugin-table#"+m;$(this).find("tfoot input.filter").keyup(function(){i.fnFilter(this.value,$(this).data("index"))});$(this).find("tfoot input.numericfilter").typeWatch(function(n,o){$(n).data("filterfunction",wlgetfilterfunctions(o));i.fnDraw()});var l=i.fnSettings();$(this).find("tfoot th").each(function(){var n=$(this).data("index");$(this).find("input.filter").val(l.aoPreSearchCols[n].sSearch)});$(k).find("tfoot input.numericfilter").each(function(){var n=m+"/"+$(this).attr("name");var o=$.Jookie.Get(j,n);if(o){$(this).val(o);$(this).data("filterfunction",wlgetfilterfunctions(o))}});$(this).find("span.datetimefilter").each(function(){var n=this;$(this).find("input[name=sincelastvisit]").change(function(){if($(this).is(":checked")){$(n).find("input[type=text]").attr("disabled","disabled")}else{$(n).find("input[type=text]").removeAttr("disabled")}i.fnDraw()});if(a){$(this).find("input[type=text]").each(function(){$(this).AnyTime_picker(c);$(this).data("converter",new AnyTime.Converter(e));$(this).change(function(){wlupdatedatetime(this);i.fnDraw()})})}else{$(this).find("input[type=text]").typeWatch(function(o,q){var p=Date.parse(q);$(o).next("input[type=hidden]").val(p/1000);i.fnDraw()})}dtid=$(this).attr("id");$(this).find("input[type=text]").each(function(){var o=dtid+"/"+$(this).attr("name");var p=$.Jookie.Get(j,o);if(p){$(this).val(p);$(this).change()}});$(this).find("input[type=checkbox]").each(function(){var o=dtid+"/"+$(this).attr("name");var p=$.Jookie.Get(j,o);if(p){$(this).attr("checked",p=="checked");$(this).change()}})});i.fnDraw();jQuery(window).bind("unload.watchlist.table#"+m,function(){wlstorespecialfilters("table#"+m)})})});function wlupdatedatetime(a){var b=$(a).data("converter");$(a).next("input[type=hidden]").val(b.parse($(a).val()).getTime()/1000)}function wldelfilters(b){var a=$(b).dataTable();$(b).find("tfoot .datetimefilter input[type=text]").each(function(){$(this).removeAttr("disabled");$(this).val($(this).prev().val());wlupdatedatetime(this)});$(b).find("tfoot input.filter,tfoot input.numericfilter").removeAttr("disabled").val("");$(b).find("tfoot input.numericfilter").data("filterfunction","");$(b).parent().find(".dataTables_filter input").val("");$(b).find("tfoot input[type=checkbox]").removeAttr("checked");fnResetAllFilters(a);return true}function wlprefsubmit(a){$("fieldset.orderadd").each(function(){if(a||$(this).data("modified")){realm=$(this).data("realm");table="table#"+realm+"list";wldeletecookies(table);wldisablecookies(table)}})}function wlstorespecialfilters(a){if(!a){a="table.watchlist"}$(a).each(function(){table=this;var c=$(table).attr("id");var b="TracWatchlistPlugin-table#"+c;$(table).find("tfoot input.numericfilter").each(function(){var e=$(this).val();var d=c+"/"+$(this).attr("name");$.Jookie.Set(b,d,e)});$(table).find(".datetimefilter").each(function(){var d=$(this).attr("id");$(this).find("input[type=text]").each(function(){var e=d+"/"+$(this).attr("name");var g=$(this).val();var f=$(this).prev().val();if(g==f){$.Jookie.Unset(b,e)}else{$.Jookie.Set(b,e,g)}});$(this).find("input[type=checkbox]").each(function(){var e=d+"/"+$(this).attr("name");var f=$(this).is(":checked")?"checked":"";$.Jookie.Set(b,e,f)})})})}function wldeletecookies(a){if(!a){a="table.watchlist"}$(a).each(function(){var e=$(this).attr("id");var c="TracWatchlistPlugin-table#"+e;$.Jookie.Delete(c);var d=window.location.pathname.split("/");var b="tracwatchlist_"+e+"_"+d.pop().replace(/[\/:]/g,"").toLowerCase();document.cookie=b+"=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path="+d.join("/")+"/"})}function wldisablecookies(a){if(!a){a="table.watchlist";namespace=".watchlist"}else{namespace="."+a}jQuery(window).unbind("unload"+namespace);$(a).each(function(){var b=$(this).dataTable();var c=b.fnSettings();c.oFeatures.bStateSave=false})}function wlresettodefault(){wlprefsubmit(1)}function wlgetfilterfunction(f){var e=f.indexOf("-");var d;var c;if(e==-1){d=parseFloat(f);c=d}else{d=parseFloat(f.substring(0,e));c=parseFloat(f.substring(e+1))}if(isNaN(d)){d=0}if(isNaN(c)){c=Number.MAX_VALUE}if(d==c){return function(a){return(a==d)}}else{return function(a){return((a>=d)&&(c>=a))}}}function wlgetfilterfunctions(c){var a=new Array();if(!c){c=""}var b=c.split(",");for(s in b){a.push(wlgetfilterfunction(b[s]))}if(a.length==1){return a[0]}return function(d){var e;for(e in a){if(a[e](d)){return true}}return false}};