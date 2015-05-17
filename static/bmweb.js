function emboldenMunged() {
    var mungeds = document.getElementsByClassName("munged");
    unembolden_re = new RegExp(" ?embolden", "g");
    for (var i=0, il = mungeds.length; i<il; ++i) {
        melem = mungeds[i]
        if (document.getElementById("emboldenbox").checked) {
            melem.className += " embolden";
        }
        else {
            melem.className = mungeds[i].className.replace(unembolden_re,"");
        }
    }
}
function toggleHideWtf() {
    wtfElem = document.getElementById("wtfSection");
    if (wtfElem.style.display == "") {
        wtfElem.style.display = "none";
    }
    else {
        wtfElem.style.display = "";
    }
}
window.onload = function() { 
    emboldenMunged();  
    toggleHideWtf();
};

