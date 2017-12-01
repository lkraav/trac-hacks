
//var linkify =
//(function(){
String.prototype.trim =
  (function () {return this.replace(/^\s+/, "").replace(/\s+$/, "");});

var invalidDate = new Date("invalid").toString();
var billingfields= {};
var statusfields = [];

var decoder = document.createElement('textarea');
function decodeHtml(s){
  decoder.innerHTML = s;
  return decoder.value;
}

function dateToUnixEpoch(date){ return  (Math.round(1000*date.getTime())); }
function makeDate(val) {
  var d = null;
  if (val && val.length && val.length>0){
    try{
      d = Date.parse(val);
    }
    catch(e){
      d = invalidDate;
    }
    if(!d || d.toString == invalidDate){
      alert("You entered an invalid date: "+val);
      return null;
    }
  }
  return d;
}
function getSetDate(ctl, val){
  if(arguments.length == 1){
    var d = makeDate(jQuery(ctl).val());
    if (d) return dateToUnixEpoch(d);
    else return null;
  }
  else{
    var val = makeDate(val);
    jQuery(ctl).val(val);
    return val;
  }
}
function getSetCheck(ctl, val){
  if (arguments.length==1){
    return jQuery(ctl).checked();
  }else {
    jQuery(ctl).checked(val);
    return val;
  }
}
function getSetInp(ctl, val, name){
  if (arguments.length==1){
    var it = jQuery(ctl).val();
    if(it) return it.trim();
    return null;
  }else {
    jQuery(ctl).val(val);
    return val;
  }
}
function addBillingField( name, type, status ){
  var name = decodeHtml(name);
  var type = type || "textbox";
  var status = status || false;
  var fn = getSetInp;
  if (type == 'checkbox') fn = getSetCheck;
  if (type == 'date' ) fn = getSetDate;
  //console.log('addBillingField', name, type, status, fn);
  var ctl = name;
  var get = function(){ return fn(jQuery(document.getElementById(name)));};
  var o = { name: name, ctl: ctl, getval: get };
  billingfields[name] = o;
  if (status){
    statusfields.push(o);
  }
}

addBillingField("billable", "checkbox");
addBillingField("unbillable", "checkbox");
addBillingField("startdate", "date");
addBillingField("startbilling", "dateselect");
addBillingField("enddate", "date");
addBillingField("endbilling", "dateselect");


var linkify = function ( atag, basehref ){
  var query = "";
  var haveAdded = false;
  function addToQuery(str){
    query += haveAdded ? "&" : "?";
    query += str;
    haveAdded = true;
  }
  //billable logic
  addToQuery(billingfields["billable"].getval() || !(billingfields["unbillable"].getval())
	     ? "BILLABLE=1" : "BILLABLE=0");
  addToQuery(billingfields["unbillable"].getval() || !(billingfields["billable"].getval())
	     ? "UNBILLABLE=0" : "UNBILLABLE=1");
  var val;
  jQuery.each(statusfields, function(k, f){
    var val = f.name.toUpperCase().replace(/\W|_|\s/gi,"")+"=";
    if(f.getval()){ val += f.name; }
    addToQuery(val);
  });
  //startdate the date in the text box or the date in the dropdown or the first time
  var startdate = billingfields["startdate"].getval() || billingfields["startbilling"].getval() || 0;
  addToQuery("STARTDATE="+startdate);
  //the date in the enddate text box or the date in the enddate billing box or real close to the end of integer unix epoch time
  // this will need a patch to continue working  past this point
  var enddate = billingfields["enddate"].getval() || billingfields["endbilling"].getval() ||
        2000000000000000;
  addToQuery("ENDDATE="+enddate);

  atag.href = basehref+query;
};
//})()
