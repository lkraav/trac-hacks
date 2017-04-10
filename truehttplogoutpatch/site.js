jQuery(document).ready(function ($) {
  var $form = $("form#logout");
  var page = $form.attr("action");
  $form.find("button").click(function () {
    if (!page)
      page = '.force_logout';
    try {
      var agt=navigator.userAgent.toLowerCase();
      if (agt.indexOf("msie") != -1) {
        // IE clear HTTP Authentication
        document.execCommand("ClearAuthenticationCache");
      } else {
        // Let's create an xmlhttp object
        var xmlhttp = createXMLObject();
        // Let's prepare invalid credentials
        xmlhttp.open("GET", page, true, "logout", "logout");
        // Let's send the request to the server
        xmlhttp.send("");
        // Let's abort the request
        xmlhttp.abort();
      }
    } catch(e) {
      // There was an error
      return;
    }
  });

  function createXMLObject() {
    try {
      if (window.XMLHttpRequest) {
        xmlhttp = new XMLHttpRequest();
      } else if (window.ActiveXObject) {  // code for IE
        xmlhttp=new ActiveXObject("Microsoft.XMLHTTP");
      }
    } catch (e) {
      xmlhttp = false;
    }
    return xmlhttp;
  }
});
