/* Biblemunger JS
 */

/******** Generic utility functions
 * Functions in this section should be generic, divorced from my application
 */

function toggleHideId(Id) {
    elem = document.getElementById(Id);
    if (elem.style.display == "") {
        elem.style.display = "none";
    }
    else {
        elem.style.display = "";
    }
}

/* Get an anchor element with the URL assigned
 * This is useful for its properties like 'pathname', 'port', etc.
 * ... especially because the pathname property normalizes the path and eliminates like "../" automatically
 * These elements can be used as a standin for a Location object that comes from document.location / window.location
 * https://developer.mozilla.org/en-US/docs/Web/API/Location
 */
function getAnchorElement(url) {
    if (typeof url === 'undefined') {
        url = window.location;
    }
    var elem = document.createElement('a');
    elem.href = url;
    return elem;
}

/* Get an array of path components separated by a slash
 */
function getUrlPathComponents(url) {
    var elem = getAnchorElement(url);

    // Create an array of components separated by a slash, and eliminate any empty components
    // (Empty components might crop up if the pathname begins or ends with a slash, or has erroneous double slashes in the middle)
    var components = elem.pathname.split('/').filter(Boolean); // Just a list of non-empty strings making up path components

    return components;
}

/* This is my own shitty function for making an HTTP request. It probably suxxx really hard. Sorry ¯\_(ツ)_/¯
 * thanx 2 http://youmightnotneedjquery.com for the confidence I need to make this bad decision
 * NOTE: it doesn't even work at all in IE versions < 9
 * url: the url to request
 * success: a function that takes one argument; if the request is successful, call this function with the server's response as its argument
 * failure: a function that takes one argument; if the request is unsuccessful, call this function with the request object as its argument
 */
function shittyAjax(url, success, failure) {
    var logmsgprefix = "Requested URL at " + url + " ";
    var request = new XMLHttpRequest();
    request.open('GET', url, true);
    request.onreadystatechange = function() {
        if (this.status >= 200 && this.status < 400) {
            console.log(logmsgprefix + "and it succeeded with a response of length " + this.responseText.length);
            if (typeof success === 'function') {
                success(this.responseText);
            }
        } else {
            console.log(logmsgprefix + "but the server returned an error");
            if (typeof failure === 'function') {
                failure(this);
            }
        }
    };
    request.onerror = function() {
        console.log(logmsgprefix + "but the connection failed")
    }
    request.send();
    request = null;
}

/******** Application-specific functions
 * Functions in this section are tied tightly to my application, and may not be too useful to anyone else
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

function toggleHideFavorites() {
    toggleHideId('searchFavorites');
    getSavedSearches();
}

function toggleHideRecents() {
    toggleHideId('searchRecents');
    getSavedSearches();
}

function searchReplace(search, replace) {
    shittyAjax('/search/'+search+'/'+replace+'/', function(html) {
        document.getElementById("results").innerHTML = html;
        getSavedSearches();
    });
}

/* Get a SavedSearches result
 * uri: a URI (relative is fine) that the SavedSearches object is mounted to
 * elementId: the ID of an element which we will replace with the search results
 */
function getSavedSearches() {
    shittyAjax('/recents',   function(html) { document.getElementById('searchRecentResults').innerHTML = html; });
    shittyAjax('/favorites', function(html) { document.getElementById('searchFavoriteResults').innerHTML = html; });
}

/* The search form will get retargetted to this function if JS is enabled
 * Note that we call history.pushState here; do not call this function during the popstate event or history will break!
 */
function submitSearchForm() {
    var search  = document.getElementById("searchBox").value,
        replace = document.getElementById("replaceBox").value;
    history.pushState(null, null, '/'+search+'/'+replace+'/');
    searchReplace(search, replace);
}

/* Retarget the search form
 * Change the search form to submit via a JS function
 * Downside: requires JS
 * Upside: can do a partial page reload of just the new results, asynchronously
 */
function retargetSearchForm() {
    document.getElementById('mungerForm').setAttribute('action', 'javascript:submitSearchForm()');
}

window.onload = function() {
    getSavedSearches();
    // We have to do this weird syntax with Array.prototype.forEach() because document.getElementsByClassName() doesn't have a forEach() method of its own
    // https://developer.mozilla.org/en-US/docs/Web/API/Document/getElementsByClassName
    Array.prototype.forEach.call(document.getElementsByClassName('mungeLink'), function(element) {
        element.addEventListener("click", function(element) {
            var components = getUrlPathComponents(element.href)
            submitSearchForm(components[0], components[1]);
        })
    });
};

window.addEventListener('popstate', function(event) {
    var components = getUrlPathComponents();
    getSavedSearches()
    if (components.length == 2) {
        document.getElementById('searchBox').value = components[0];
        document.getElementById('replaceBox').value = components[1];
        searchReplace(components[0], components[1]);
    }
});
