<%inherit file="_base.html.mako"/>

<%block name="ogdescription">
  <meta property="og:description" content="${exreplacement if exreplacement else appsubtitle}" />
</%block>

<%block name="headscript">
  <script>
    window.onload = function() {
        setSearchReplaceBoxValues(getSearchReplaceFromUrl(window.location));
        // getSavedSearches();
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
        // getSavedSearches()
    });
  </script>
</%block>

  <header>
    <img src="${baseurl}static/biblemunger-logo-1-noword.svg"/>
  </header>
  <div class="content-area munging-page">
    <form id="mungerForm" method=GET action="${baseurl}searchForm">
      <input type="text" id="searchBox"  placeholder="Search for"   autocapitalize="off" autofocus="true" >
      <input type="text" id="replaceBox" placeholder="Replace with" autocapitalize="off">
      <input type="submit" value="Munge" class="form-button std-button">
    </form>
    <script>retargetSearchForm()</script>
  </div>

<div class="results-area">
  <%include file="results.html.mako" args="search=search,replace=replace,verses=results" />
</div>
