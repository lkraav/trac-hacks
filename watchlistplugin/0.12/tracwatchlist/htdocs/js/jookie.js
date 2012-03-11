/*
  License:
  Jookie 1.0 jQuery Plugin

  Copyright (c) 2008 Jon Combe (http://joncom.be)

  Permission is hereby granted, free of charge, to any person
  obtaining a copy of this software and associated documentation
  files (the "Software"), to deal in the Software without
  restriction, including without limitation the rights to use,
  copy, modify, merge, publish, distribute, sublicense, and/or sell
  copies of the Software, and to permit persons to whom the
  Software is furnished to do so, subject to the following
  conditions:

  The above copyright notice and this permission notice shall be
  included in all copies or substantial portions of the Software.

  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
  EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
  OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
  NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
  HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
  WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
  OTHER DEALINGS IN THE SOFTWARE.
*/
(function(c){c.Jookie={Data:{},Debug:function(j){f(j)},Delete:function(j){h(j)},Get:function(k,j){return b(k,j)},Initialise:function(k,j){e(k,j)},Set:function(k,j,l){g(k,j,l)},Unset:function(k,j){d(k,j)}};function f(l){var j=/\+/g;var k=unescape(String(a(l)).replace(j," "));alert("Name: "+l+"\nLifespan: "+c.Jookie.Data[l].iLifespan+" minutes\nCookie Existed Prior to Init: "+c.Jookie.Data[l].bMadeEarlier+"\n\n"+k)}function h(j){delete c.Jookie.Data[j];document.cookie=(j+"=; expires="+(new Date(1990,6,3)).toGMTString()+"; path=/")}function a(n){var l=null;var m=document.cookie.split(";");n+="=";for(var j in m){var k=m[j];while(k.charAt(0)==" "){k=k.substring(1,k.length)}if(k.indexOf(n)==0){l=k.substring(n.length,k.length);break}}return l}function b(k,j){return c.Jookie.Data[k].oValues[j]}function e(l,j){if(typeof c.Jookie.Data[l]=="undefined"){var m={};var n=false;var k=a(l);if(k!==null){m=JSON.parse(unescape(String(k).replace(/\+/g," ")));n=true}c.Jookie.Data[l]={iLifespan:j,bMadeEarlier:n,oValues:m};i(l)}}function i(k){var l="";if(c.Jookie.Data[k].iLifespan>0){var j=new Date();j.setMinutes(j.getMinutes()+c.Jookie.Data[k].iLifespan);l=("; expires="+j.toGMTString())}document.cookie=(k+"="+escape(JSON.stringify(c.Jookie.Data[k].oValues))+l+"; path=/")}function g(l,j,k){c.Jookie.Data[l].oValues[j]=k;i(l)}function d(k,j){delete c.Jookie.Data[k].oValues[j];i(k)}})(jQuery);if(!this.JSON){JSON=function(){function f(n){return n<10?"0"+n:n}Date.prototype.toJSON=function(key){return this.getUTCFullYear()+"-"+f(this.getUTCMonth()+1)+"-"+f(this.getUTCDate())+"T"+f(this.getUTCHours())+":"+f(this.getUTCMinutes())+":"+f(this.getUTCSeconds())+"Z"};var cx=/[\u0000\u00ad\u0600-\u0604\u070f\u17b4\u17b5\u200c-\u200f\u2028-\u202f\u2060-\u206f\ufeff\ufff0-\uffff]/g,escapeable=/[\\\"\x00-\x1f\x7f-\x9f\u00ad\u0600-\u0604\u070f\u17b4\u17b5\u200c-\u200f\u2028-\u202f\u2060-\u206f\ufeff\ufff0-\uffff]/g,gap,indent,meta={"\b":"\\b","\t":"\\t","\n":"\\n","\f":"\\f","\r":"\\r",'"':'\\"',"\\":"\\\\"},rep;function quote(string){escapeable.lastIndex=0;return escapeable.test(string)?'"'+string.replace(escapeable,function(a){var c=meta[a];if(typeof c==="string"){return c}return"\\u"+("0000"+(+(a.charCodeAt(0))).toString(16)).slice(-4)})+'"':'"'+string+'"'}function str(key,holder){var i,k,v,length,mind=gap,partial,value=holder[key];if(value&&typeof value==="object"&&typeof value.toJSON==="function"){value=value.toJSON(key)}if(typeof rep==="function"){value=rep.call(holder,key,value)}switch(typeof value){case"string":return quote(value);case"number":return isFinite(value)?String(value):"null";case"boolean":case"null":return String(value);case"object":if(!value){return"null"}gap+=indent;partial=[];if(typeof value.length==="number"&&!(value.propertyIsEnumerable("length"))){length=value.length;for(i=0;i<length;i+=1){partial[i]=str(i,value)||"null"}v=partial.length===0?"[]":gap?"[\n"+gap+partial.join(",\n"+gap)+"\n"+mind+"]":"["+partial.join(",")+"]";gap=mind;return v}if(rep&&typeof rep==="object"){length=rep.length;for(i=0;i<length;i+=1){k=rep[i];if(typeof k==="string"){v=str(k,value,rep);if(v){partial.push(quote(k)+(gap?": ":":")+v)}}}}else{for(k in value){if(Object.hasOwnProperty.call(value,k)){v=str(k,value,rep);if(v){partial.push(quote(k)+(gap?": ":":")+v)}}}}v=partial.length===0?"{}":gap?"{\n"+gap+partial.join(",\n"+gap)+"\n"+mind+"}":"{"+partial.join(",")+"}";gap=mind;return v}}return{stringify:function(value,replacer,space){var i;gap="";indent="";if(typeof space==="number"){for(i=0;i<space;i+=1){indent+=" "}}else{if(typeof space==="string"){indent=space}}rep=replacer;if(replacer&&typeof replacer!=="function"&&(typeof replacer!=="object"||typeof replacer.length!=="number")){throw new Error("JSON.stringify")}return str("",{"":value})},parse:function(text,reviver){var j;function walk(holder,key){var k,v,value=holder[key];if(value&&typeof value==="object"){for(k in value){if(Object.hasOwnProperty.call(value,k)){v=walk(value,k);if(v!==undefined){value[k]=v}else{delete value[k]}}}}return reviver.call(holder,key,value)}cx.lastIndex=0;if(cx.test(text)){text=text.replace(cx,function(a){return"\\u"+("0000"+(+(a.charCodeAt(0))).toString(16)).slice(-4)})}if(/^[\],:{}\s]*$/.test(text.replace(/\\(?:["\\\/bfnrt]|u[0-9a-fA-F]{4})/g,"@").replace(/"[^"\\\n\r]*"|true|false|null|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?/g,"]").replace(/(?:^|:|,)(?:\s*\[)+/g,""))){j=eval("("+text+")");return typeof reviver==="function"?walk({"":j},""):j}throw new SyntaxError("JSON.parse")}}}()};