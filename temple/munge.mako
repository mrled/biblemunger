<%!
    import markupsafe
    import random
    import re
%>
<html>
<head>
  <title>${pagetitle}</title>
  <script type="text/javascript" src="./static/bmweb.js"></script>
  <link type="text/css" rel="stylesheet" href="./static/bmweb.css"></link>
  <meta name="og:title" content="${pagetitle}" />
  <link rel="image_src" href="./static/bible.png" />
  %if results:
    ## NOTE: Facebook will ignore any text that contains markup here :(
    ##       so we cannot embolden our munged terms :(:(
    <meta property="og:description" content="${str(results[random.randrange(len(results))])}" />
  %else:
    <meta property="og:description" content="${appsubtitle}" />
  %endif
  <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=0"/> 
</head>
<body><div id="bodyContent">

<h1><a href="./">${apptitle}</a></h1>
<h2 id="subtitleH2">${appsubtitle}</h2>

<div id="intro">
  <div id="cutesyFuckingIcon" class="sectionGlyphLeft">
    <img src="static/bible.png" alt="The Holy Fucking Scriptures" style="max-width:100%"/>
  </div>
  <div id="introText" class="sectionContentRight">
    <p>Find some text in the Bible and replace it with other text.</p>
    <input type="button" value="About" onclick="toggleHideId('wtfSection');" />
    <input type="button" value="Help" onclick="toggleHideId('helpSection');" />
  </div>
</div>

<div id="wtfSection">
  <script>toggleHideId('wtfSection')</script> 
  <h2>What the fuck is this?</h2>
  ## We aren't setting sectionGlyphLeft here because I can't fucking make it look right
  <div id="wtfSectionListContainer" class="sectionContentCenter">
    <ul id="wtfSectionList" class="noBullets">
      <li class="halfSpacedList">${apptitle} is a stupid thing that will replace arbitrary text in the Bible with other arbitrary text</li>
      <li class="halfSpacedList">It was inspired by <a href="http://the-toast.net/series/bible-verses/">some excellence</a> by Mallory Ortberg (<a href="http://the-toast.net/2014/12/29/bible-verses-thou-shalt-not-replaced-can-u-not/">this one</a> is my personal favorite)</li>
      <li class="halfSpacedList">It uses an XML KJV from <a href="http://sourceforge.net/projects/zefania-sharp/">the Zefania project</a>, which probably would not appreciate this at all</li>
      <li class="halfSpacedList"><a href="http://younix.us">mrled</a> is responsible for this bullshit</li>
      <li class="halfSpacedList"><a href="https://github.com/mrled/biblemunger">Contributions are welcome</a></li>
    </ul>
  </div>
</div>

<div id="helpSection">
  <script>toggleHideId('helpSection')</script> 
  <h2>How the fuck do I use this?</h2>
  <div id="helpSectionListContainer" class="sectionContentCenter">
    <ul id="helpSectionList" class="noBullets">
      <li class="halfSpacedList">Note that it will even search/replace just a <em>part</em> of a word. For instance, in the <a href="./?search=servant&replace=uber%20driver">"servant" &rArr; "uber driver"</a> search, note that some verses now refer to "<strong>menuber drivers and maiduber drivers</strong>" (from <strong>menservants and maidservants</strong>)</li>
      <li class="halfSpacedList">However, it does search/replace numbers and punctuation, not just letters, so if the above behavior is undesirable, surround your search and your replacement with spaces. For example, <a href="./?search=servant&replace=uber%20driver">" servant " &rArr; " uber driver "</a> will only find instances of "servant" when it's surrounded by spaces. (This also means that it will not find results of "servant" when followed by punctuation.)</li>
      <li class="halfSpacedList">One final thing to note: because it's so strict, it currently is case sensitive, such that <a href="./?search=LORD&replace=kickstarter+backer">LORD &rArr; kickstarter backer</a> will find completely different results than <a href="./?search=lord&replace=kickstarter+backer">lord &rArr; kickstarter backer</a>, which will find completely different results than <a href="./?search=Lord&replace=kickstarter+backer">Lord &rArr; kickstarter backer</a>. This means that, currently, an uncapitalized search term will never match a word that begins a sentence.</li>
    %if filterinuse:
      <li>(Note that there is a rather aggressive <a href="https://github.com/dariusk/wordfilter">word filter</a> in place. It's designed to prevent racist bullshit from polluting this list because some of ya'll fucking suck, but it sometimes triggers on innocuous words as well. If you are replacing something and don't see it appear here, you may have tripped over this edge case.)</li>
    %endif
    </ul>
  </div>
</div>

<div class="clearLeft">

%if favorites or recents:
  <h2>Suggestions</h2>
  <p>Can't think of anything to search for?</p>
  <p>
    <input type="button" value="Show Favorite Searches" onclick="toggleHideId('searchFavorites');" />
    <input type="button" value="Show Recent Searches" onclick="toggleHideId('searchRecents');" />
  </p>

  <div id="searchFavorites">
    <script>toggleHideId('searchFavorites')</script> 
    %if favorites:
      <p>These are some of my favorites:</p>
      <ul class="noBullets"> 
        %for fav in favorites:
          <% s = fav['search']; r = fav['replace'] %>
          <li><a href="./munge?search=${s}&replace=${r}">${s} &rArr; ${r}</a></li>
        %endfor
      </ul>
    %else:
      <p>Sorry, no favorite searches to show you :(</p>
    %endif
  </div>
  <div id="searchRecents">    
    <script>toggleHideId('searchRecents')</script> 
    %if recents:
      <p>Here are some recent searches by users:</p>
      <ul class="noBullets"> 
        %for rec in recents:
            ##%if loop.index >= 10:
            ##    <% break %> 
            ##%endif
            <% s = rec['search']; r = rec['replace'] %>
            <li><a href="./munge?search=${s}&replace=${r}">${s} &rArr; ${r}</a></li>
        %endfor
      </ul></p>
    %else:
      <p>Sorry, no recent searches to show you :(</p>
    %endif
  </div>
%endif

<div id="searchSubsection">
<h2>Search and <span class="strikeThru">destroy</span> replace</h2>
<form id="mungerForm" method=GET action="./munge">
  <span class="labelAndBox" id="searchBox">Search:
    <input type=text name="search" size=20 autofocus="true" autocapitalize="off"
      value="${search if search else ''}" /></span>
  <span class="labelAndBox" id="replaceBox">Replace:
    <input type=text name="replace" size=20 autocapitalize="off"
      value="${replace if replace else ''}" /></span>
  <span id="mungeButton"><input type=submit value="Munge" /></span>
</form>
</div>

%if queried:
  <h2>${resultstitle}</h2>
  <p>Embolden replacement text 
    <input name="embolden" id="emboldenbox" type="checkbox" checked="checked" onclick="emboldenMunged()"></p>
  <div id="mungedResults">
    %if results:
      <table border=0 cellspacing=5 cellpadding=5 align="CENTER">
      %for verse in results:
        <tr><td><strong>${verse.book} ${verse.chapter}:${verse.verse}</strong></td>
        <%
            escaped = markupsafe.escape(verse.markedup)
            slashspanned = re.sub('\*\*\*\*\*\*', '</span>', escaped)
            spanned = re.sub('\*\*\*\*\*', '<span class="munged">', slashspanned)
        %>
        <td>${spanned}</td></tr>
      %endfor
      </table>
    %else:
      <p>None</p>
    %endif
  </div>
%endif

<a href="https://github.com/mrled/biblemunger"><img style="position: absolute; top: 0; right: 0; border: 0;" src="https://camo.githubusercontent.com/a6677b08c955af8400f44c6298f40e7d19cc5b2d/68747470733a2f2f73332e616d617a6f6e6177732e636f6d2f6769746875622f726962626f6e732f666f726b6d655f72696768745f677261795f3664366436642e706e67" alt="Fork me on GitHub" data-canonical-src="https://s3.amazonaws.com/github/ribbons/forkme_right_gray_6d6d6d.png"></a>

</div>

</div></body>
<!--${deploymentinfo}-->
</html>
