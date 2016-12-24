<%inherit file="_base.html.mako"/>

<%block name="ogdescription">
  <meta property="og:description" content="${exreplacement if exreplacement else appsubtitle}" />
</%block>

<%block name="headscript">
  <script>

    window.onload = function() {
        getSavedSearches();
        retargetSearchForm();
        retargetMungeLinks();
    };

    window.addEventListener('popstate', function(event) {
        var logmsg = "popstate event: ";
        var pair = getSearchReplaceFromUrl(window.location);
        if (pair) {
            logmsg += "loading "+pair.search+"/"+pair.replace+" results";
            document.getElementById('searchBox').value = pair.search;
            document.getElementById('replaceBox').value = pair.replace;
            searchReplace(pair.search, pair.replace);
            retargetMungeLinks();
        } else {
            logmsg += "no pair to load? doing nothing";
        }
        debugPrint(logmsg);
        getSavedSearches()
    });

  </script>
</%block>

<h2>Suggestions</h2>
<p>Can't think of anything to search for?</p>
<p>
  <input type="button" value="Show Favorite Searches" onclick="toggleHideFavorites();" />
  <input type="button" value="Show Recent Searches" onclick="toggleHideRecents();" />
</p>

<div id="searchFavorites">
  <script>toggleHideFavorites()</script>
  <p>These are some of my favorites:</p>
  <div id="searchFavoriteResults">
    <%include file="saved.html.mako" args="pairs=favorites" />
  </div>
</div>
<div id="searchRecents">
  <script>toggleHideRecents()</script>
  <p>Here are some recent searches by users:</p>
  <div id="searchRecentResults">
    <%include file="saved.html.mako" args="pairs=recents" />
  </div>
</div>

<div id="searchSubsection">
  <h2>Search and <span class="strikeThru">destroy</span> replace</h2>
  <form id="mungerForm" method=GET action="${baseurl}searchForm">
    <span class="labelAndBox" id="searchField">Search: <input type=text name="search" id="searchBox" size=20 autofocus="true" autocapitalize="off" value="" /></span>
    <span class="labelAndBox" id="replaceField">Replace: <input type=text name="replace" id="replaceBox" size=20 autocapitalize="off" value="" /></span>
    <span id="mungeButton"><input type=submit value="Munge" /></span>
  </form>
  <script>retargetSearchForm()</script>
</div>

<div id="results">
  <%include file="results.html.mako" args="search=search,replace=replace,verses=results" />
</div>
