/* Biblemunger JS
 */

/******** Mako template stuff
 * These variables come in from Mako. (We then assign them to JavaScript variables so all the code after this is pure valid JS)
 */
// Please ensure that this always ends in a '/' character
var baseurl = "${baseurl}";
var debug;
if ("${debug}" === "True") {
    debug = true;
    console.log("Debugging");
} else {
    debug = false;
}

/******** Generic utility functions
 * Functions in this section should be generic, divorced from my application
 */

function debugPrint(message) {
    if (debug) {
        console.log(message);
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
    request.onload = function() {
        if (request.status >= 200 && request.status < 400) {
            debugPrint(logmsgprefix + "and it succeeded with a status of "+request.status+" and a response of length " + request.responseText.length);
            if (typeof success === 'function') {
                success(request.responseText);
            }
        } else {
            debugPrint(logmsgprefix + "but the server returned an error");
            if (typeof failure === 'function') {
                failure(request);
            }
        }
    };
    request.onerror = function() {
        debugPrint(logmsgprefix + "but the connection failed");
        if (typeof failure === 'function') {
            failure(request);
        }
    }
    request.send();
}


/* String.startsWith polyfill:
 */
if (!String.prototype.startsWith) {
    String.prototype.startsWith = function(searchString, position){
        position = position || 0;
        return this.substr(position, searchString.length) === searchString;
    };
}

/* Test for, add, and remove CSS classes from HTML elements
 */
function hasClass(element, className) {
    if (typeof element === 'undefined' || typeof className === 'undefined') {
        return;
    }
    if (element.className.indexOf(className) !== -1) {
        return true;
    } else {
        return false;
    }
}
function addClass(element, className) {
    if (typeof element === 'undefined' || typeof className === 'undefined') {
        return;
    }
    if (! hasClass(element, className)) {
        element.className += " "+className;
    }
}
function removeClass(element, className) {
    if (typeof element === 'undefined' || typeof className === 'undefined') {
        return;
    }
    if (hasClass(element, className)) {
        element.className = element.className.replace(className, "");
    }
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

/* Run a search/replace operation, and replace the #results div with the results
 * search: a search term
 * replace: a term to replace it with
 * updateHistory: if truthy, call history.pushState() with a URL that will represent the new search
 */
function searchReplace(search, replace, updateHistory) {
    shittyAjax(baseurl+'search/'+search+'/'+replace+'/', function(html) {
        document.getElementById("results").innerHTML = html;
        if (updateHistory) {
            var newUrl = baseurl+'munge/'+search+'/'+replace+'/';
            debugPrint("Pushing new URL to history: "+newUrl);
            history.pushState(null, null, newUrl);
        }
        getSavedSearches();
        retargetMungeLinks();
    });
}

function getSearchReplaceFromUrl(url) {
    if (typeof url === 'undefined') {
        url = window.location.href;
    } else {
        url = String(url);
    }
    var suburl = url.substring(baseurl.length);

    // Create an array of components separated by a slash, and eliminate any empty components
    // (Empty components might crop up if the pathname begins or ends with a slash, or has erroneous double slashes in the middle)
    var components = suburl.split('/').filter(Boolean); // Just a list of non-empty strings making up path components

    var ret = {};
    if (components[0] == 'munge' && components.length == 3) {
        ret = {'search': components[1], 'replace': components[2]};
    }
    return ret;
}

/* Get a SavedSearches result
 * uri: a URI (relative is fine) that the SavedSearches object is mounted to
 * elementId: the ID of an element which we will replace with the search results
 */
function getSavedSearches() {
    function gss(url, id) {
        shittyAjax(url, function(html) {
            document.getElementById(id).innerHTML = html;
            retargetMungeLinks();
        })
    }
    gss(baseurl+'favorites', 'searchFavoriteResults');
}

/* The search form will get retargeted to this function if JS is enabled
 */
function submitSearchForm() {
    var search  = document.getElementById("searchBox").value,
        replace = document.getElementById("replaceBox").value;
    searchReplace(search, replace, true);
}

/* Retarget munge links, change to replace results section via AJAX
 * Downside: requires JS
 * Upside: can do a partial page reload of just the new results, asynchronously
 */
function retargetMungeLinks() {
    Array.prototype.forEach.call(document.getElementsByClassName('mungeLink'), function(element) {
        if (! hasClass(element, 'retargetedMungeLink')) {
            addClass(element, 'retargetedMungeLink');
            var pair = getSearchReplaceFromUrl(element.href);
            element.addEventListener('click', function(event) {
                event.preventDefault();
                searchReplace(pair.search, pair.replace, true);
            });
        }
    });
}

/* Retarget the search form to submit via a JS function
 * Downside: requires JS
 * Upside: can do a partial page reload of just the new results, asynchronously
 */
function retargetSearchForm() {
    document.getElementById('mungerForm').setAttribute('action', 'javascript:submitSearchForm()');
}
