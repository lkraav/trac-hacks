$( document ).ready(function() {

const closebtn = document.querySelector("#closebtn");

closebtn.addEventListener("click", (event) => {
  document.getElementById("sidebar").style.left = "-220px";
  if(document.getElementById("content").offsetLeft < 215){
    document.getElementById("content").style.marginLeft = "0";
    document.getElementById("footer").style.marginLeft = "0";
  }
  document.getElementById("opensidebar").style.left= "20px";
  event.preventDefault();
});

opensblink = document.getElementById("opensblink")
opensblink.addEventListener("click", (event) => {

  document.getElementById("sidebar").style.left = "0.75em";

  if(document.getElementById("content").offsetLeft < 15){
      document.getElementById("content").style.marginLeft = "200px";
      document.getElementById("footer").style.marginLeft = "200px";
  }
  document.getElementById("opensidebar").style.left= "-60px";

  event.preventDefault();
});

});
