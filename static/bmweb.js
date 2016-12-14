/* Biblemunger JS
 */

/* This function is DEPRECATED, but still might be useful when working on the site design
 */
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

function toggleHideFavorites() {
    toggleHideId('searchFavorites');
    getSavedSearch('favorites', 'searchFavoriteResults');
}

function toggleHideRecents() {
    toggleHideId('searchRecents');
    getSavedSearch('recents', 'searchRecentResults');
}

function searchReplace(search, replace) {
    // Check if there have been any updates to the favorites list whenver we search
    // (We check for recents later)
    getSavedSearch('favorites', 'searchFavoriteResults');

    var wrappedReplace = "<span class='munged'>"+replace+"</span>";
    $.ajax({url: "search/" + search}).done(function(verses) {
        var newResults = ""
        newResults += "<div id='results'>";
        newResults += "<h2>"+search+" ⇒ "+replace+"</h2>";
        newResults += "<table border=0 cellspacing=5 cellpadding=5 align='CENTER'>";
        var foundVerse = false;
        verses.forEach(function(verse) {
            foundVerse = true;
            mungedText = verse.text.replace(search, wrappedReplace);
            newResults += "<tr><td>"+verse.book+" "+verse.chapter+":"+verse.verse+"</td><td>"+mungedText+"</td></tr>";
        });

        if (foundVerse) {
            // Only add a search to the recents list if it had results, & check for a new recent afterwards
            $.ajax({url: "/recents/"+search+"/"+replace+"/", method: "PUT"}).done(function(data) {
                getSavedSearch('recents', 'searchRecentResults');
            });
        }
        else {
            getSavedSearch('recents', 'searchRecentResults');
        }

        newResults += "</table>";
        newResults += "</div>";
        document.getElementById("results").innerHTML = newResults;
    })
}

/* Assemble a query string
 * Use a prefix of '?' for a normal query string that is passed to the server, or '#' for a hash/fragment/anchor query string
 * Expects an array of objects with 'name' and 'value' properties
 * Will take an array like this:
 *     [{'name': 'foo', 'value': 'bar'}, {'name': 'baz', 'value': 'quux'}]
 * And turn it into a query string like this:
 *     foo=bar&baz=quux
 */
function buildQueryString(argArray, prefix) {
    if (typeof prefix === 'undefined') {
        prefix = "?"
    }
    var result = prefix;
    argArray.forEach(function(argument) {
        lastchar = result.charAt(result.length -1);
        if (lastchar != '?' && lastchar != '#' && lastchar != '&') { result += "&"; }
        result += encodeURIComponent(argument.name) + "=" + encodeURIComponent(argument.value)
    });
    return result;
}

function submitSearchReplace() {
    var search = $('input[name=search]').val();
    var replace = $('input[name=replace]').val();
    searchReplace(search, replace);

    var hashParams = [];
    if (search.length  > 0) { hashParams.push({'name': 'search',  'value': search }); }
    if (replace.length > 0) { hashParams.push({'name': 'replace', 'value': replace}); }
    window.location = buildQueryString(hashParams, "#")
}

/* Pull key=value pairs out of the URL anchor
 */
function getHashParams() {
    var hashParams = {};
    var kvpair_regex = /([^&;=]+)=?([^&;]*)/g;
    var anchor = window.location.hash.substring(1);

    // Replace '+' with ' ' and decode any escape sequences (like %20 for ' ' etc)
    var decode = function(string) {
        return decodeURIComponent(string.replace(/\+/g, " "));
    };

    var kvpair;
    while (kvpair = kvpair_regex.exec(anchor)) {
        key = decode(kvpair[1]);
        val = decode(kvpair[2]);
        hashParams[key] = val;
    }
    return hashParams;
}

function applyHashParams() {
    hashParams = getHashParams();
    if (hashParams.search) {
        document.getElementById("searchBox").value = hashParams.search;
    }
    if (hashParams.replace) {
        document.getElementById("replaceBox").value = hashParams.replace;
    }
    if (hashParams.search && hashParams.replace) {
        submitSearchReplace();
    }
}

/* Get a SavedSearches result
 * uri: a URI (relative is fine) that the SavedSearches object is mounted to
 * elemtnId: the ID of an element which we will replace with the search results
 */
function getSavedSearch(uri, elementId) {
    $.ajax({url: uri}).done(function(html) {
        document.getElementById(elementId).innerHTML = html;
    });
}

window.onload = function() {
    applyHashParams();
    getSavedSearch('recents', 'searchRecentResults');
    getSavedSearch('favorites', 'searchFavoriteResults');
};
window.onhashchange = function() {
    applyHashParams();
}
