<%inherit file="_base.html.mako"/>

<%block name="ogdescription">
  <meta property="og:description" content="${vrangelabel}" />
</%block>

<h2>${vrangelabel}</h2>

<div class="passage">
  %if verses and len(verses) > 0:
    <table border=0 cellspacing=5 cellpadding=5 align='CENTER'>
    %for verse in verses:
      <tr><td>${verse.book} ${verse.chapter}:${verse.verse}</td><td>${verse.text}</td></tr>
    %endfor
    </table>
  %else:
    <p>Sorry, nothing to show :(</p>
  %endif
</div>
