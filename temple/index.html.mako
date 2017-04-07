<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <title>${pagetitle}</title>
    <script><%include file="munge.js.mako" /></script>
    <style><%include file="munge.css.mako" /></style>
    <style><%include file="ben.css.mako" /></style>
    <link rel="image_src" href="${baseurl}static/biblemunger-logo-1-noword.svg" />

    ## NOTE: Facebook will ignore any text that contains markup here :( so we cannot embolden our munged terms :(:(
    <meta property="og:description" content="${exreplacement if exreplacement else appsubtitle}" />

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
</head>
<body>
    <header>
        <img src="${baseurl}static/biblemunger-logo-1-noword.svg"/>
    </header>
    <div class="content-area munging-page">
        <h2>Search and <strike>destroy</strike> replace</h2>
        <form id="mungerForm" method=GET action="${baseurl}searchForm">
            <input type="text" id="searchBox" placeholder="Search for" autofocus="true" autocapitalize="off">
            <input type="text" id="replaceBox" placeholder="Replace with" autocapitalize="off">
            <input type="submit" value="Munge" class="form-button std-button">
        </form>
        <script>retargetSearchForm()</script>

        <%
        import re
        %>

        <div class="results-area">
            %if search and replace:
                <p class="substitution"><span>This Munge:</span> <em>Smite</em> Fuck Over</p>
                %if verses and len(verses) > 0:
                    <dl>
                        %for verse in verses:
                            <%
                                taggedreplace = '<strong>{}</strong>'.format(replace)
                                munged = re.sub(search, taggedreplace, verse.text)
                            %>
                            <div class="verse-result">
                                <dd>${munged}</dd><dt>${verse.book} ${verse.chapter}:${verse.verse}</dt>
                            </div>
                        %endfor
                    </dl>
                %else:
                    <p>Sorry, nothing to show :(</p>
                %endif
            %else:
            %endif
        </div>
    </div>
</body>
</html>