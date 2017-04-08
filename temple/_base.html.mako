<html>
  <head>

    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <title>${pagetitle}</title>
    <script><%include file="munge.js.mako" /></script>
    <style><%include file="ben.css.mako" /></style>
    <meta name="og:title" content="${pagetitle}" />
    <link rel="image_src" href="${baseurl}static/biblemunger-logo-1-noword.svg" />

    <%block name="ogdescription">
      <meta property="og:description" content='${appsubtitle}' />
    </%block>
    
    <%block name="headscript"></%block>
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
      ${self.body()}
    </div>

  </body>
</html>
