/* Biblemunger JS
 */

/******** Generic utility functions
 * Functions in this section should be generic, divorced from my application
 * (including mako variables)
 */

/* The base URL for the application (so we can find endpoints, static assets, etc)
 * We assume this exists; you must inject this variable separately
 * We make sure it always ends with a slash so our code is less fragile
 */
if (window.baseurl[ window.baseurl.length -1 ] !== '/') {
    window.baseurl += '/';
}

/* Print a debug message
 * Checks a global 'debug' variable first; you must inject this variable separately
 */
function debugPrint(message) {
    if (window.debug) {
        console.log(message);
    }
}
debugPrint("If this prints to the console, debugging is enabled");
debugPrint("Detected baseurl as '" + baseurl + "'");

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

/* Polyfills for String.startsWith and String.endsWith
 */
if (!String.prototype.startsWith) {
    String.prototype.startsWith = function(searchString, position){
        position = position || 0;
        return this.substr(position, searchString.length) === searchString;
    };
}
if (!String.prototype.endsWith) {
    String.prototype.endsWith = function(searchString, position) {
        var subjectString = this.toString();
        if (typeof position !== 'number' ||
            !isFinite(position) ||
            Math.floor(position) !== position ||
            position > subjectString.length)
        {
            position = subjectString.length;
        }
        position -= searchString.length;
        var lastIndex = subjectString.lastIndexOf(searchString, position);
        return lastIndex !== -1 && lastIndex === position;
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

/* Given the pathname part of a URL, return an array where each item represents a component of that path
 * The path is normalized by eliminating empty components (which can happen if pathname begins/ends w/ slash, or has erroneous double slashes in it)
 */
function pathComponents(urlpath) {
    return urlpath.split('/').filter(function(component) { return component.length > 0; });
}

/* Assemble a path from path components
 * components: an array of (string) path components
 * startSlash: if true, ensure the path begins with a slash; if false, ensure it does not
 * endSlash: if true, ensure the path ends with a slash; if false, ensure it does not
 * returns: the components, each separated by a single '/'
 *          will search and replace all multi-slashes in a component with a single slash
 *          except that if it notices a protocol like http://, it saves it before replacing
 *          this also means if you want to represent file:/// urls w/ 3 slashes, you can do so
 *          by passing startSlash as true.
 */
function assemblePath(components, startSlash, endSlash) {
    var assembled = components.join('/');
    var match = assembled.match(/^\w+\:\/\//);
    if (match) {
        var protocol = match[0];
        assembled = assembled.substring(match[0].length);
    }
    assembled = assembled.replace(/\/+/g, '/');

    if (startSlash && assembled[0] !== '/') {
        assembled = '/' + assembled;
    } else if (!startSlash && assembled[0] === '/') {
        assembled = assembled.substring(1);
    }

    var finalIdx = assembled.length - 1;
    if (endSlash && assembled[finalIdx] !== '/') {
        assembled = assembled + '/';
    } else if (!endSlash && assembled[finalIdx] === '/') {
        assembled = assembled.substring(0, finalIdx);
    }

    if (protocol) {
        assembled = protocol + assembled;
    }

    return assembled;
}

/******** Application-specific stuff
 * Items in this section are tied tightly to my application, and may not be too useful to anyone else
 */

/* Run a search/replace operation, and replace the #results div with the results
 * search: a search term
 * replace: a term to replace it with
 * updateHistory: if truthy, call history.pushState() with a URL that will represent the new search
 */
function searchReplace(search, replace, updateHistory) {
    shittyAjax(assemblePath([baseurl, 'search', search, replace], false, true), function(html) {

        var resultsAreaList = document.getElementsByClassName("results-area");
        for (var idx=0; idx<resultsAreaList.length; idx++) {
            resultsAreaList[idx].innerHTML = html;
        }

        if (updateHistory) {
            var newUrl = assemblePath([baseurl, 'munge', search, replace], false, true);
            debugPrint("Pushing new URL to history: "+newUrl);
            history.pushState(null, null, newUrl);
        }
        retargetMungeLinks();
    });
}

/* Extract search/replace parameters from a munge URL
 * url: A url to examine, defaults to window.location.href
 * returns: An object with .search and .replace properties, or nothing
 */
function getSearchReplaceFromUrl(url) {
    if (typeof url === 'undefined') {
        url = window.location.href;
    } else {
        url = String(url);
    }
    var urlpath = url.substring(baseurl.length);
    var components = pathComponents(urlpath);
    var ret = {};
    if (components[0] == 'munge' && components.length === 3) {
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
    gss(assemblePath([baseurl, 'favorites'], false, true), 'searchFavoriteResults');
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

function setSearchReplaceBoxValues(pair) {
    var searchBox  = document.getElementById('searchBox'),
        replaceBox = document.getElementById('replaceBox');
    if (pair.search) {
        searchBox.placeholder = "";
        searchBox.value = pair.search;
    }
    if (pair.replace) {
        replaceBox.placeholder = "";
        replaceBox.value = pair.replace;
    }
}
