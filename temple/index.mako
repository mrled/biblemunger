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
  %elif queried:
    <meta property="og:description" content="No results for ${search} :(" />
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
    <input type="button" value="About" onclick="toggleHideWtf();" />
  </div>
</div>

<div id="wtfSection">
  <h2>What the fuck is this?</h2>
  ## We aren't setting sectionGlyphLeft here because I can't fucking make it look right
  <div id="wtfSectionListContainer" class="sectionContentRight">
    <ul id="wtfSectionList" class="noBullets">
      <li class="halfSpacedList">${apptitle} is a stupid thing that will replace arbitrary text in the Bible with other arbitrary text</li>
      <li class="halfSpacedList">It was inspired by <a href="http://the-toast.net/tag/bible-verses/">some excellence</a> by Mallory Ortberg</li>
      <li class="halfSpacedList">It uses an XML KJV from <a href="http://sourceforge.net/projects/zefania-sharp/">the Zefania project</a>, which probably would not appreciate this at all</li>
      <li class="halfSpacedList"><a href="http://younix.us">mrled</a> is responsible for this bullshit</li>
      <li class="halfSpacedList"><a href="https://github.com/mrled/biblemunger">Contributions are welcome</a></li>
    </ul>
  </div>
</div>

<div class="clearLeft">

<div id="searchSubsection">
<h2>Search and <span class="strikeThru">destroy</span> replace</h2>
<form id="mungerForm" method=GET action="./">
  <span class="labelAndBox" id="searchBox">Search:
    <input type=text name="search" size=20 autofocus="true" autocapitalize="off"
      value="${search if search else ""}" /></span>
  <span class="labelAndBox" id="replaceBox">Replace:
    <input type=text name="replace" size=20 autocapitalize="off"
      value="${replace if replace else ""}" /></span>
  <span id="mungeButton"><input type=submit value="Munge" /></span>
</form>
</div>

%if favorites:
  <p>Can't think of anything to search for? Try these:
  <ul id="searchFaves" class="noBullets"> 
    %for fav in favorites:
      <li><a href="./?search=${fav['search']}&replace=${fav['replace']}">${fav['search']} &rArr; ${fav['replace']}</a></li>
    %endfor
  </ul></p>
%endif

%if queried:
  <h2>${resultstitle}</h2>
  <p>Embolden replacement text 
    <input name="embolden" id="emboldenbox" type="checkbox" checked="checked" onclick="emboldenMunged()"></p>
  <div id="mungedResults">
    %if results:
      <table border=0 cellspacing=5 cellpadding=5 align="CENTER">
      %for verse in results:
        <tr><td><strong>${verse.book} ${verse.chapter}:${verse.verse}</strong></td>
        <td>${verse.text_markedup}</td></tr>
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
</html>
