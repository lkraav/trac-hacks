/** Abstract base class for collection plugins v1.0.1.
	Written by Keith Wood (kbwood{at}iinet.com.au) December 2013.
	Licensed under the MIT (https://github.com/jquery/jquery/blob/master/MIT-LICENSE.txt) license. */
(function(){var j=false;window.JQClass=function(){};JQClass.classes={};JQClass.extend=function extender(f){var g=this.prototype;j=true;var h=new this();j=false;for(var i in f){h[i]=typeof f[i]=='function'&&typeof g[i]=='function'?(function(d,e){return function(){var b=this._super;this._super=function(a){return g[d].apply(this,a||[])};var c=e.apply(this,arguments);this._super=b;return c}})(i,f[i]):f[i]}function JQClass(){if(!j&&this._init){this._init.apply(this,arguments)}}JQClass.prototype=h;JQClass.prototype.constructor=JQClass;JQClass.extend=extender;return JQClass}})();(function($){JQClass.classes.JQPlugin=JQClass.extend({name:'plugin',defaultOptions:{},regionalOptions:{},_getters:[],_getMarker:function(){return'is-'+this.name},_init:function(){$.extend(this.defaultOptions,(this.regionalOptions&&this.regionalOptions[''])||{});var c=camelCase(this.name);$[c]=this;$.fn[c]=function(a){var b=Array.prototype.slice.call(arguments,1);if($[c]._isNotChained(a,b)){return $[c][a].apply($[c],[this[0]].concat(b))}return this.each(function(){if(typeof a==='string'){if(a[0]==='_'||!$[c][a]){throw'Unknown method: '+a;}$[c][a].apply($[c],[this].concat(b))}else{$[c]._attach(this,a)}})}},setDefaults:function(a){$.extend(this.defaultOptions,a||{})},_isNotChained:function(a,b){if(a==='option'&&(b.length===0||(b.length===1&&typeof b[0]==='string'))){return true}return $.inArray(a,this._getters)>-1},_attach:function(a,b){a=$(a);if(a.hasClass(this._getMarker())){return}a.addClass(this._getMarker());b=$.extend({},this.defaultOptions,this._getMetadata(a),b||{});var c=$.extend({name:this.name,elem:a,options:b},this._instSettings(a,b));a.data(this.name,c);this._postAttach(a,c);this.option(a,b)},_instSettings:function(a,b){return{}},_postAttach:function(a,b){},_getMetadata:function(d){try{var f=d.data(this.name.toLowerCase())||'';f=f.replace(/'/g,'"');f=f.replace(/([a-zA-Z0-9]+):/g,function(a,b,i){var c=f.substring(0,i).match(/"/g);return(!c||c.length%2===0?'"'+b+'":':b+':')});f=$.parseJSON('{'+f+'}');for(var g in f){var h=f[g];if(typeof h==='string'&&h.match(/^new Date\((.*)\)$/)){f[g]=eval(h)}}return f}catch(e){return{}}},_getInst:function(a){return $(a).data(this.name)||{}},option:function(a,b,c){a=$(a);var d=a.data(this.name);if(!b||(typeof b==='string'&&c==null)){var e=(d||{}).options;return(e&&b?e[b]:e)}if(!a.hasClass(this._getMarker())){return}var e=b||{};if(typeof b==='string'){e={};e[b]=c}this._optionsChanged(a,d,e);$.extend(d.options,e)},_optionsChanged:function(a,b,c){},destroy:function(a){a=$(a);if(!a.hasClass(this._getMarker())){return}this._preDestroy(a,this._getInst(a));a.removeData(this.name).removeClass(this._getMarker())},_preDestroy:function(a,b){}});function camelCase(c){return c.replace(/-([a-z])/g,function(a,b){return b.toUpperCase()})}$.JQPlugin={createPlugin:function(a,b){if(typeof a==='object'){b=a;a='JQPlugin'}a=camelCase(a);var c=camelCase(b.name);JQClass.classes[c]=JQClass.classes[a].extend(b);new JQClass.classes[c]()}}})(jQuery);
/* http://keith-wood.name/timeEntry.html
   Time entry for jQuery v2.0.1.
   Written by Keith Wood (kbwood{at}iinet.com.au) June 2007.
   Available under the MIT (https://github.com/jquery/jquery/blob/master/MIT-LICENSE.txt) license.
   Please attribute the author if you use it. */
(function($){var n='timeEntry';$.JQPlugin.createPlugin({name:n,defaultOptions:{appendText:'',showSeconds:false,unlimitedHours:false,timeSteps:[1,1,1],initialField:null,noSeparatorEntry:false,tabToExit:false,useMouseWheel:true,defaultTime:null,minTime:null,maxTime:null,spinnerImage:'spinnerDefault.png',spinnerSize:[20,20,8],spinnerBigImage:'',spinnerBigSize:[40,40,16],spinnerIncDecOnly:false,spinnerRepeat:[500,250],beforeShow:null,beforeSetTime:null},regionalOptions:{'':{show24Hours:false,separator:':',ampmPrefix:'',ampmNames:['AM','PM'],spinnerTexts:['Now','Previous field','Next field','Increment','Decrement']}},_getters:['getOffset','getTime','isDisabled'],_appendClass:n+'-append',_controlClass:n+'-control',_expandClass:n+'-expand',_disabledInputs:[],_instSettings:function(a,b){return{_field:0,_selectedHour:0,_selectedMinute:0,_selectedSecond:0}},_postAttach:function(b,c){b.on('focus.'+c.name,this._doFocus).on('blur.'+c.name,this._doBlur).on('click.'+c.name,this._doClick).on('keydown.'+c.name,this._doKeyDown).on('keypress.'+c.name,this._doKeyPress).on('paste.'+c.name,function(a){setTimeout(function(){o._parseTime(c)},1)})},_optionsChanged:function(a,b,c){var d=this._extractTime(b);$.extend(b.options,c);b.options.show24Hours=b.options.show24Hours||b.options.unlimitedHours;b._field=0;if(d){this._setTime(b,new Date(0,0,0,d[0],d[1],d[2]))}a.next('span.'+this._appendClass).remove();a.parent().find('span.'+this._controlClass).remove();if($.fn.mousewheel){a.unmousewheel()}var e=(!b.options.spinnerImage?null:$('<span class="'+this._controlClass+'" style="display: inline-block; '+'background: url(\''+b.options.spinnerImage+'\') 0 0 no-repeat; width: '+b.options.spinnerSize[0]+'px; height: '+b.options.spinnerSize[1]+'px;"></span>'));a.after(b.options.appendText?'<span class="'+this._appendClass+'">'+b.options.appendText+'</span>':'').after(e||'');if(b.options.useMouseWheel&&$.fn.mousewheel){a.mousewheel(this._doMouseWheel)}if(e){e.mousedown(this._handleSpinner).mouseup(this._endSpinner).mouseover(this._expandSpinner).mouseout(this._endSpinner).mousemove(this._describeSpinner)}},enable:function(a){this._enableDisable(a,false)},disable:function(a){this._enableDisable(a,true)},_enableDisable:function(b,c){var d=this._getInst(b);if(!d){return}b.disabled=c;if(b.nextSibling&&b.nextSibling.nodeName.toLowerCase()==='span'){this._changeSpinner(d,b.nextSibling,(c?5:-1))}this._disabledInputs=$.map(this._disabledInputs,function(a){return(a===b?null:a)});if(c){this._disabledInputs.push(b)}},isDisabled:function(a){return $.inArray(a,this._disabledInputs)>-1},_preDestroy:function(b,c){b=$(b).off('.'+n);if($.fn.mousewheel){b.unmousewheel()}this._disabledInputs=$.map(this._disabledInputs,function(a){return(a===b[0]?null:a)});b.siblings('.'+this._appendClass+',.'+this._controlClass).remove()},setTime:function(a,b){var c=this._getInst(a);if(c){if(b===null||b===''){$(a).val('')}else{this._setTime(c,b?($.isArray(b)?b:(typeof b==='object'?new Date(b.getTime()):b)):null)}}},getTime:function(a){var b=this._getInst(a);var c=(b?this._extractTime(b):null);return(!c?null:new Date(0,0,0,c[0],c[1],c[2]))},getOffset:function(a){var b=this._getInst(a);var c=(b?this._extractTime(b):null);return(!c?0:(c[0]*3600+c[1]*60+c[2])*1000)},_doFocus:function(a){var b=(a.nodeName&&a.nodeName.toLowerCase()==='input'?a:this);if(o._lastInput===b||o.isDisabled(b)){o._focussed=false;return}var c=o._getInst(b);o._focussed=true;o._lastInput=b;o._blurredInput=null;$.extend(c.options,($.isFunction(c.options.beforeShow)?c.options.beforeShow.apply(b,[b]):{}));o._parseTime(c,a.nodeName?null:a);setTimeout(function(){o._showField(c)},10)},_doBlur:function(a){o._blurredInput=o._lastInput;o._lastInput=null},_doClick:function(a){var b=a.target;var c=o._getInst(b);var d=c._field;if(!o._focussed){c._field=o._getSelection(c,b,a)}if(d!==c._field){c._lastChr=''}o._showField(c);o._focussed=false},_getSelection:function(b,c,d){var e=0;var f=[b.elem.val().split(b.options.separator)[0].length,2,2];if(c.selectionStart!==null){var g=0;for(var h=0;h<=Math.max(1,b._secondField,b._ampmField);h++){g+=(h!==b._ampmField?f[h]+b.options.separator.length:b.options.ampmPrefix.length+b.options.ampmNames[0].length);e=h;if(c.selectionStart<g){break}}}else if(c.createTextRange&&d!=null){var i=$(d.srcElement);var j=c.createTextRange();var k=function(a){return{thin:2,medium:4,thick:6}[a]||a};var l=d.clientX+document.documentElement.scrollLeft-(i.offset().left+parseInt(k(i.css('border-left-width')),10))-j.offsetLeft;for(var h=0;h<=Math.max(1,b._secondField,b._ampmField);h++){var g=(h!==b._ampmField?(h*fieldSize)+2:(b._ampmField*fieldSize)+b.options.ampmPrefix.length+b.options.ampmNames[0].length);j.collapse();j.moveEnd('character',g);e=h;if(l<j.boundingWidth){break}}}return e},_doKeyDown:function(a){if(a.keyCode>=48){return true}var b=o._getInst(a.target);switch(a.keyCode){case 9:return(b.options.tabToExit?true:(a.shiftKey?o._changeField(b,-1,true):o._changeField(b,+1,true)));case 35:if(a.ctrlKey){o._setValue(b,'')}else{b._field=Math.max(1,b._secondField,b._ampmField);o._adjustField(b,0)}break;case 36:if(a.ctrlKey){o._setTime(b)}else{b._field=0;o._adjustField(b,0)}break;case 37:o._changeField(b,-1,false);break;case 38:o._adjustField(b,+1);break;case 39:o._changeField(b,+1,false);break;case 40:o._adjustField(b,-1);break;case 46:o._setValue(b,'');break;case 8:b._lastChr='';default:return true}return false},_doKeyPress:function(a){var b=String.fromCharCode(a.charCode===undefined?a.keyCode:a.charCode);if(b<' '){return true}var c=o._getInst(a.target);o._handleKeyPress(c,b);return false},_handleKeyPress:function(a,b){if(b===a.options.separator){this._changeField(a,+1,false)}else if(b>='0'&&b<='9'){var c=parseInt(b,10);var d=parseInt(a._lastChr+b,10);var e=(a._field!==0?a._selectedHour:(a.options.unlimitedHours?d:(a.options.show24Hours?(d<24?d:c):(d>=1&&d<=12?d:(c>0?c:a._selectedHour))%12+(a._selectedHour>=12?12:0))));var f=(a._field!==1?a._selectedMinute:(d<60?d:c));var g=(a._field!==a._secondField?a._selectedSecond:(d<60?d:c));var h=this._constrainTime(a,[e,f,g]);this._setTime(a,(a.options.unlimitedHours?h:new Date(0,0,0,h[0],h[1],h[2])));if(a.options.noSeparatorEntry&&a._lastChr){this._changeField(a,+1,false)}else{a._lastChr=(a.options.unlimitedHours&&a._field===0?a._lastChr+b:b)}}else if(!a.options.show24Hours){b=b.toLowerCase();if((b===a.options.ampmNames[0].substring(0,1).toLowerCase()&&a._selectedHour>=12)||(b===a.options.ampmNames[1].substring(0,1).toLowerCase()&&a._selectedHour<12)){var i=a._field;a._field=a._ampmField;this._adjustField(a,+1);a._field=i;this._showField(a)}}},_doMouseWheel:function(a,b){if(o.isDisabled(a.target)){return}var c=o._getInst(a.target);c.elem.focus();if(!c.elem.val()){o._parseTime(c)}o._adjustField(c,b);a.preventDefault()},_expandSpinner:function(b){var c=o._getSpinnerTarget(b);var d=o._getInst(o._getInput(c));if(o.isDisabled(d.elem[0])){return}if(d.options.spinnerBigImage){d._expanded=true;var e=$(c).offset();var f=null;$(c).parents().each(function(){var a=$(this);if(a.css('position')==='relative'||a.css('position')==='absolute'){f=a.offset()}return!f});$('<div class="'+o._expandClass+'" style="position: absolute; left: '+(e.left-(d.options.spinnerBigSize[0]-d.options.spinnerSize[0])/2-(f?f.left:0))+'px; top: '+(e.top-(d.options.spinnerBigSize[1]-d.options.spinnerSize[1])/2-(f?f.top:0))+'px; width: '+d.options.spinnerBigSize[0]+'px; height: '+d.options.spinnerBigSize[1]+'px; background: transparent url('+d.options.spinnerBigImage+') no-repeat 0px 0px; z-index: 10;"></div>').mousedown(o._handleSpinner).mouseup(o._endSpinner).mouseout(o._endExpand).mousemove(o._describeSpinner).insertAfter(c)}},_getInput:function(a){return $(a).siblings('.'+this._getMarker())[0]},_describeSpinner:function(a){var b=o._getSpinnerTarget(a);var c=o._getInst(o._getInput(b));b.title=c.options.spinnerTexts[o._getSpinnerRegion(c,a)]},_handleSpinner:function(a){var b=o._getSpinnerTarget(a);var c=o._getInput(b);if(o.isDisabled(c)){return}if(c===o._blurredInput){o._lastInput=c;o._blurredInput=null}var d=o._getInst(c);o._doFocus(c);var e=o._getSpinnerRegion(d,a);o._changeSpinner(d,b,e);o._actionSpinner(d,e);o._timer=null;o._handlingSpinner=true;if(e>=3&&d.options.spinnerRepeat[0]){o._timer=setTimeout(function(){o._repeatSpinner(d,e)},d.options.spinnerRepeat[0]);$(b).one('mouseout',o._releaseSpinner).one('mouseup',o._releaseSpinner)}},_actionSpinner:function(a,b){if(!a.elem.val()){o._parseTime(a)}switch(b){case 0:this._setTime(a);break;case 1:this._changeField(a,-1,false);break;case 2:this._changeField(a,+1,false);break;case 3:this._adjustField(a,+1);break;case 4:this._adjustField(a,-1);break}},_repeatSpinner:function(a,b){if(!o._timer){return}o._lastInput=o._blurredInput;this._actionSpinner(a,b);this._timer=setTimeout(function(){o._repeatSpinner(a,b)},a.options.spinnerRepeat[1])},_releaseSpinner:function(a){clearTimeout(o._timer);o._timer=null},_endExpand:function(a){o._timer=null;var b=o._getSpinnerTarget(a);var c=o._getInput(b);var d=o._getInst(c);$(b).remove();d._expanded=false},_endSpinner:function(a){o._timer=null;var b=o._getSpinnerTarget(a);var c=o._getInput(b);var d=o._getInst(c);if(!o.isDisabled(c)){o._changeSpinner(d,b,-1)}if(o._handlingSpinner){o._lastInput=o._blurredInput}if(o._lastInput&&o._handlingSpinner){o._showField(d)}o._handlingSpinner=false},_getSpinnerTarget:function(a){return a.target||a.srcElement},_getSpinnerRegion:function(a,b){var c=this._getSpinnerTarget(b);var d=$(c).offset();var e=[document.documentElement.scrollLeft||document.body.scrollLeft,document.documentElement.scrollTop||document.body.scrollTop];var f=(a.options.spinnerIncDecOnly?99:b.clientX+e[0]-d.left);var g=b.clientY+e[1]-d.top;var h=a.options[a._expanded?'spinnerBigSize':'spinnerSize'];var i=(a.options.spinnerIncDecOnly?99:h[0]-1-f);var j=h[1]-1-g;if(h[2]>0&&Math.abs(f-i)<=h[2]&&Math.abs(g-j)<=h[2]){return 0}var k=Math.min(f,g,i,j);return(k===f?1:(k===i?2:(k===g?3:4)))},_changeSpinner:function(a,b,c){$(b).css('background-position','-'+((c+1)*a.options[a._expanded?'spinnerBigSize':'spinnerSize'][0])+'px 0px')},_parseTime:function(a,b){var c=this._extractTime(a);if(c){a._selectedHour=c[0];a._selectedMinute=c[1];a._selectedSecond=c[2]}else{var d=this._constrainTime(a);a._selectedHour=d[0];a._selectedMinute=d[1];a._selectedSecond=(a.options.showSeconds?d[2]:0)}a._secondField=(a.options.showSeconds?2:-1);a._ampmField=(a.options.show24Hours?-1:(a.options.showSeconds?3:2));a._lastChr='';var e=function(){if(a.elem.val()!==''){o._showTime(a)}};if(typeof a.options.initialField==='number'){a._field=Math.max(0,Math.min(Math.max(1,a._secondField,a._ampmField),a.options.initialField));e()}else{setTimeout(function(){a._field=o._getSelection(a,a.elem[0],b);e()},0)}},_extractTime:function(a,b){b=b||a.elem.val();var c=b.split(a.options.separator);if(a.options.separator===''&&b!==''){c[0]=b.substring(0,2);c[1]=b.substring(2,4);c[2]=b.substring(4,6)}if(c.length>=2){var d=!a.options.show24Hours&&(b.indexOf(a.options.ampmNames[0])>-1);var e=!a.options.show24Hours&&(b.indexOf(a.options.ampmNames[1])>-1);var f=parseInt(c[0],10);f=(isNaN(f)?0:f);f=((d||e)&&f===12?0:f)+(e?12:0);var g=parseInt(c[1],10);g=(isNaN(g)?0:g);var h=(c.length>=3?parseInt(c[2],10):0);h=(isNaN(h)||!a.options.showSeconds?0:h);return this._constrainTime(a,[f,g,h])}return null},_constrainTime:function(a,b){var c=(b!==null&&b!==undefined);if(!c){var d=this._determineTime(a.options.defaultTime,a)||new Date();b=[d.getHours(),d.getMinutes(),d.getSeconds()]}var e=false;for(var i=0;i<a.options.timeSteps.length;i++){if(e){b[i]=0}else if(a.options.timeSteps[i]>1){b[i]=Math.round(b[i]/a.options.timeSteps[i])*a.options.timeSteps[i];e=true}}return b},_showTime:function(a){var b=(a.options.unlimitedHours?a._selectedHour:this._formatNumber(a.options.show24Hours?a._selectedHour:((a._selectedHour+11)%12)+1))+a.options.separator+this._formatNumber(a._selectedMinute)+(a.options.showSeconds?a.options.separator+this._formatNumber(a._selectedSecond):'')+(a.options.show24Hours?'':a.options.ampmPrefix+a.options.ampmNames[(a._selectedHour<12?0:1)]);this._setValue(a,b);this._showField(a)},_showField:function(a){var b=a.elem[0];if(a.elem.is(':hidden')||o._lastInput!==b){return}var c=[a.elem.val().split(a.options.separator)[0].length,2,2];var d=0;var e=0;while(e<a._field){d+=c[e]+(e===Math.max(1,a._secondField)?0:a.options.separator.length);e++}var f=d+(a._field!==a._ampmField?c[e]:a.options.ampmPrefix.length+a.options.ampmNames[0].length);if(b.setSelectionRange){b.setSelectionRange(d,f)}else if(b.createTextRange){var g=b.createTextRange();g.moveStart('character',d);g.moveEnd('character',f-a.elem.val().length);g.select()}if(!b.disabled){b.focus()}},_formatNumber:function(a){return(a<10?'0':'')+a},_setValue:function(a,b){if(b!==a.elem.val()){a.elem.val(b).trigger('change')}},_changeField:function(a,b,c){var d=(a.elem.val()===''||a._field===(b===-1?0:Math.max(1,a._secondField,a._ampmField)));if(!d){a._field+=b}this._showField(a);a._lastChr='';return(d&&c)},_adjustField:function(a,b){if(a.elem.val()===''){b=0}if(a.options.unlimitedHours){this._setTime(a,[a._selectedHour+(a._field===0?b*a.options.timeSteps[0]:0),a._selectedMinute+(a._field===1?b*a.options.timeSteps[1]:0),a._selectedSecond+(a._field===a._secondField?b*a.options.timeSteps[2]:0)])}else{this._setTime(a,new Date(0,0,0,a._selectedHour+(a._field===0?b*a.options.timeSteps[0]:0)+(a._field===a._ampmField?b*12:0),a._selectedMinute+(a._field===1?b*a.options.timeSteps[1]:0),a._selectedSecond+(a._field===a._secondField?b*a.options.timeSteps[2]:0)))}},_setTime:function(a,b){if(a.options.unlimitedHours&&$.isArray(b)){var c=b}else{b=this._determineTime(b,a);var c=(b?[b.getHours(),b.getMinutes(),b.getSeconds()]:null)}c=this._constrainTime(a,c);b=new Date(0,0,0,c[0],c[1],c[2]);var b=this._normaliseTime(b);var d=this._normaliseTime(this._determineTime(a.options.minTime,a));var e=this._normaliseTime(this._determineTime(a.options.maxTime,a));if(a.options.unlimitedHours){while(c[2]<0){c[2]+=60;c[1]--}while(c[2]>59){c[2]-=60;c[1]++}while(c[1]<0){c[1]+=60;c[0]--}while(c[1]>59){c[1]-=60;c[0]++}d=(a.options.minTime!=null&&$.isArray(a.options.minTime))?a.options.minTime:[0,0,0];if(c[0]<d[0]){c=d.slice(0,3)}else if(c[0]===d[0]){if(c[1]<d[1]){c[1]=d[1];c[2]=d[2]}else if(c[1]===d[1]){if(c[2]<d[2]){c[2]=d[2]}}}if(a.options.maxTime!=null&&$.isArray(a.options.maxTime)){if(c[0]>a.options.maxTime[0]){c=a.options.maxTime.slice(0,3)}else if(c[0]===a.options.maxTime[0]){if(c[1]>a.options.maxTime[1]){c[1]=a.options.maxTime[1];c[2]=a.options.maxTime[2]}else if(c[1]===a.options.maxTime[1]){if(c[2]>a.options.maxTime[2]){c[2]=a.options.maxTime[2]}}}}}else{if(d&&e&&d>e){if(b<d&&b>e){b=(Math.abs(b-d)<Math.abs(b-e)?d:e)}}else{b=(d&&b<d?d:(e&&b>e?e:b))}c[0]=b.getHours();c[1]=b.getMinutes();c[2]=b.getSeconds()}if($.isFunction(a.options.beforeSetTime)){b=a.options.beforeSetTime.apply(a.elem[0],[this.getTime(a.elem[0]),b,d,e]);c[0]=b.getHours();c[1]=b.getMinutes();c[2]=b.getSeconds()}a._selectedHour=c[0];a._selectedMinute=c[1];a._selectedSecond=c[2];this._showTime(a)},_determineTime:function(i,j){var k=function(a){var b=new Date();b.setTime(b.getTime()+a*1000);return b};var l=function(a){var b=o._extractTime(j,a);var c=new Date();var d=(b?b[0]:c.getHours());var e=(b?b[1]:c.getMinutes());var f=(b?b[2]:c.getSeconds());if(!b){var g=/([+-]?[0-9]+)\s*(s|S|m|M|h|H)?/g;var h=g.exec(a);while(h){switch(h[2]||'s'){case's':case'S':f+=parseInt(h[1],10);break;case'm':case'M':e+=parseInt(h[1],10);break;case'h':case'H':d+=parseInt(h[1],10);break}h=g.exec(a)}}c=new Date(0,0,10,d,e,f,0);if(/^!/.test(a)){if(c.getDate()>10){c=new Date(0,0,10,23,59,59)}else if(c.getDate()<10){c=new Date(0,0,10,0,0,0)}}return c};var m=function(a){return new Date(0,0,0,a[0],a[1]||0,a[2]||0,0)};return(i?(typeof i==='string'?l(i):(typeof i==='number'?k(i):($.isArray(i)?m(i):i))):null)},_normaliseTime:function(a){if(!a){return null}a.setFullYear(1900);a.setMonth(0);a.setDate(0);return a}});var o=$.timeEntry})(jQuery);
