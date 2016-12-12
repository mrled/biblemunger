function emboldenMunged() {
    var mungeds = document.getElementsByClassName("munged");
    unembolden_re = new RegExp(" ?embolden", "g");
    for (var i=0, il = mungeds.length; i<il; ++i) {
        melem = mungeds[i];
        if (document.getElementById("emboldenbox").checked) {
            melem.className += " embolden";
        }
        else {
            melem.className = mungeds[i].className.replace(unembolden_re,"");
        }
    }
}

function toggleHideId(Id) {
    elem = document.getElementById(Id);
    if (elem.style.display == "") {
        elem.style.display = "none";
    }
    else {
        elem.style.display = "";
    }
}

function searchReplace(search, replace) {
    $.ajax({url: "api/search/" + search}).done(function(verses) {
        var newResults = ""
        newResults += "<div id='results'>";
        newResults += "<h2>"+search+" ⇒ "+replace+"</h2>";
        newResults += "<table border=0 cellspacing=5 cellpadding=5 align='CENTER'>"
        verses.forEach(function(verse) {
            mungedText = verse.text.replace(search, replace)
            newResults += "<tr><td>"+verse.book+" "+verse.chapter+":"+verse.verse+"</td><td>"+mungedText+"</td></tr>"
        });
        alert(mungedText)
        newResults += "</table>"
        newResults += "</div>";
        document.getElementById("results").innerHTML = newResults;
    })
}

function submitSearchReplace() {
    var search = $('input[name=search]').val();
    var replace = $('input[name=replace]').val();
    searchReplace(search, replace);
}

window.onload = function() { 
    emboldenMunged();  
};

