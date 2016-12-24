<%inherit file="_base.html.mako"/>

<%block name="ogdescription">
  <meta property="og:description" content="${exverse if exverse else appsubtitle}" />
</%block>

This is the reading page :)

starting in ${start}

ending at ${end}
