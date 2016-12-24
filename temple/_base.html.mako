<html>
  <head>
    <title>${pagetitle}</title>
    <script><%include file="munge.js.mako" /></script>
    <style><%include file="munge.css.mako" /></style>
    <meta name="og:title" content="${pagetitle}" />
    <link rel="image_src" href="${baseurl}static/bible.png" />

    ## NOTE: Facebook will ignore any text that contains markup here :( so we cannot embolden our munged terms :(:(
    <%block name="ogdescription">
      <meta property="og:description" content='${appsubtitle}' />
    </%block>
    
    <%block name="headscript"></%block>

    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=0"/> 
  </head>
  <body>

    %if debug:
      <%!
        import datetime
      %>
      <div class="debuggingOnly">
        <p>Page generated ${datetime.datetime.now()}</p>
      </div>
    %endif

    <div id="bodyContent">

      <h1><a href="${baseurl}">${apptitle}</a></h1>
      <h2 id="subtitleH2">${appsubtitle}</h2>

      <div id="intro">
        <div id="cutesyFuckingIcon" class="sectionGlyphLeft">
          <img alt="The Holy Fucking Scriptures" style="max-width:100%" src="${dataUriFromStaticFile('bible.png', 'image/png')}" />
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

      <div class="clearLeft"></div>

      ${self.body()}

    </div>

  </body>
</html>
