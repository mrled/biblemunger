function emboldenMunged() {
  var mungeds = document.getElementsByClassName("munged");
  unembolden_re = new RegExp(" ?embolden", "g");
  for (var i=0, il = mungeds.length; i<il; ++i) {
    if (document.getElementById("emboldenbox").checked) {
      mungeds[i].className += " embolden";
    }
    else {
      mungeds[i].className = mungeds[i].className.replace(unembolden_re,"");
   }
  }
}
window.onload = emboldenMunged;

