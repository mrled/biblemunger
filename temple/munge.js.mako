/* Biblemunger JS
 */

/******** Generic utility functions
 * Functions in this section should be generic, divorced from my application
 * (including mako variables like ${baseurl} and ${debug})
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

/******** Mako template stuff
 * These items are passed in by Mako
 */

alert("FUCK EVERYTHING I NEED TO MAKE SURE BASEURL DOES NOT HAVE A TRAILING SLASH NOW PLS")
alert("Wait can I set some HTML property to baseurl, and never have to actually refer to it here (referring instead to the HTML property)?")
var baseurl = "${baseurl}";
if (!baseurl.endsWith("/")) {
    baseurl += "/";
}

var debug;
if ("${debug}" === "True") {
    debug = true;
    console.log("Debugging");
} else {
    debug = false;
}

/******** Application-specific stuff
 * Items in this section are tied tightly to my application, and may not be too useful to anyone else
 */

/* Get the path of a URL relative to baseurl
 */
function appSubpath(url) {
    return url.substring(baseurl.length);
}

var appEndpoints = {};

/* Constructor for AppEndpoint objects, which let me reason about URLs for calling into backend functions.
 * backendFunctionName: the name of the function being called in the backend code
 * endpoint: the endpoint, where / is the base application URL, like "/endpoint" or "/some/k-rad/endpoint"
 * composeFunction: a function which takes 2 arguments and returns a URL:
 *  - baseEndpoint: a string representing the endpoint argument passed to this constructor
 *  - backendParameters: a dictionary representing the arguments to the backend function (in argument name:value pairs)
 *  - returns: a URL to call the backend function using those arguments.
 * extractArgsFunction: a function which takes 1 argument and returns a dictionary:
 *  - urlComponents: an array of application URL components (not including baseurl components)
 *  - returns: a dictionary representing arguments to the backend function where key is arg name and value is its value
 */
function registerAppEndpoint(backendFunctionName, endpoint, composeFunction, extractArgsFunction) {

    var appEndpoint = {
        // The name of the backend function
        backendFunctionName: backendFunctionName,

        // An array of path components for the URL to the backend function call, relative to the baseurl
        endpointComponents: pathComponents(endpoint),

        // Test whether a URL points to this backend function
        // url: a URL to test
        // returns: true or false
        test: function(url) {
            var subUrlComponents = pathComponents(appSubpath(url));
            for (var idx=0; idx<endpointComponents.length; idx++) {
                if (endpointComponents[idx] != subUrlComponents[idx]) {
                    return false;
                }
            }
            return true;
        },

        // Compose a backend function call
        // backendParameters: a dictionary representing arguments to the backend function
        // returns: a URL to call the backend function that way
        compose: function(backendParameters) {
            return composeFunction()
        },

        // Extract arguments to a backend function from a URL
        // url: a URL representing a call to this backend function
        // returns: a dictionary containing arguments to the backend function where key is arg name and value is arg value
        extractArgs: function(url) {
            if (!this.test(url)) {
                return;
            }
            return extractArgsFunction(pathComponents(appSubpath(url)));
        }
    }

    // Is this... a good idea? It seems kind of perverse, but also concise, and I can't think of any legit use that would be harmed by this
    if (appEndpoints[backendFunctionName] !== undefined) {
        debugPrint("Attempting to register an AppEndpoint more than once. Aborting...");
        return false;
    }
    appEndpoints[backendFunctionName] = appEndpoint;
    return true;
}
registerAppEndpoint(
    "Munger.munge()",
    "/munge"
    function(baseEndpoint, backendParameters) {
        return [baseEndpoint, backendParameters.search, backendParameters.replace].join("/");
    },
    function(urlComponents) {
        return {search: urlComponents[0], replace: urlComponents[1]};
    }
);
registerAppEndpoint(
    "Munger.search()",
    "/search"
    function(baseEndpoint, ) {
        return [baseurl, "search", options.search, options.replace].join("/");
    },
    function(urlComponents) {
        return {search: urlComponents[0], replace: urlComponents[1]};
    }
)


/* Constructor for AppEndpoint objects, which let me reason about URLs for calling into backend functions.
 * backendFunctionName: the name of the function being called in the backend code
 * endpoint: the endpoint, where / is the base application URL, like "/endpoint" or "/some/k-rad/endpoint"
 * composeFunction: a function which takes 2 arguments and returns a URL:
 *  - baseEndpoint: a string representing the endpoint argument passed to this constructor
 *  - backendParameters: a dictionary representing the arguments to the backend function (in argument name:value pairs)
 *  - returns: a URL to call the backend function using those arguments.
 * extractArgsFunction: a function which takes 1 argument and returns a dictionary:
 *  - urlComponents: an array of application URL components (not including baseurl components)
 *  - returns: a dictionary representing arguments to the backend function where key is arg name and value is its value
 */
function AppEndpoint(backendFunctionName, endpoint, composeFunction, extractArgsFunction) {

    // The name of the backend function
    this.backendFunctionName = backendFunctionName;

    // An array of path components for the URL to the backend function call, relative to the baseurl
    this.endpointComponents = pathComponents(endpoint);

    // Test whether a URL points to this backend function
    // url: a URL to test
    // returns: true or false
    this.test = function(url) {
        var subUrlComponents = pathComponents(appSubpath(url));
        for (var idx=0; idx<endpointComponents.length; idx++) {
            if (endpointComponents[idx] != subUrlComponents[idx]) {
                return false;
            }
        }
        return true;
    };

    // Compose a backend function call
    // backendParameters: a dictionary representing arguments to the backend function
    // returns: a URL to call the backend function that way
    this.compose = function(backendParameters) {
        return composeFunction()
    };

    // Extract arguments to a backend function from a URL
    // url: a URL representing a call to this backend function
    // returns: a dictionary containing arguments to the backend function where key is arg name and value is arg value
    this.extractArgs = function(url) {
        if (!this.test(url)) {
            return;
        }
        return extractArgsFunction(pathComponents(appSubpath(url)));
    };
}

var appEndpoints = {
    munge: new AppEndpoint(
        "Munger.munge()",
        "/munge"
        function(baseEndpoint, backendParameters) {
            return [baseEndpoint, backendParameters.search, backendParameters.replace].join("/");
        },
        function(urlComponents) {
            return {search: urlComponents[0], replace: urlComponents[1]};
        }
    ),
    search: new AppEndpoint(
        "Munger.search()",
        "/search"
        function(baseEndpoint, ) {
            return [baseurl, "search", options.search, options.replace].join("/");
        },
        function(urlComponents) {
            return {search: urlComponents[0], replace: urlComponents[1]};
        }
    )
};

function debugPrint(message) {
    if (debug) {
        console.log(message);
    }
}

/* Run a search/replace operation, and replace the #results div with the results
 * search: a search term
 * replace: a term to replace it with
 * updateHistory: if truthy, call history.pushState() with a URL that will represent the new search
 */
function searchReplace(search, replace, updateHistory) {
    shittyAjax([appEndpoints['Munger.search'], search, replace].join('/'), function(html) {
    shittyAjax(
        appEndpoints['Munger.search'].compose({search: search, replace: replace}),
        function(html) {
    shittyAjax([baseurl, 'search', search, replace].join('/'), function(html) {
    shittyAjax(baseurl+'search/'+search+'/'+replace+'/', function(html) {

        var resultsAreaList = document.getElementsByClassName("results-area");
        for (var idx=0; idx<resultsAreaList.length; idx++) {
            resultsAreaList[idx].innerHTML = html;
        }

        if (updateHistory) {
            var newUrl = [appEndpoints['Munger.munge'], search, replace].join('/');
            var newUrl = baseurl+'munge/'+search+'/'+replace+'/';
            debugPrint("Pushing new URL to history: "+newUrl);
            history.pushState(null, null, newUrl);
        }
        retargetMungeLinks();
    });
}

function getSearchReplaceFromUrl(url) {
    if (typeof url === 'undefined') {
        url = window.location.href;
    } else {
        url = String(url);
    }
    return appEndpoints['Munger.replace'].extractArgs(url);

    var components = pathComponents(appSubpath(url));
    if (components[0] == 'munge' && components.length === 3) {
        return = {'search': components[1], 'replace': components[2]};
    } else {
        return {};
    }
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
    gss(appEndpoints['Munger.favorites'], 'searchFavoriteResults')
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
