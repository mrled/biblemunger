<html>
  <head>

    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <title>${pagetitle}</title>
    <meta name="og:title" content="${pagetitle}" />
    <link rel="image_src" href="${baseurl}static/biblemunger-logo-1-noword.svg" />

    <!--Add important global variables that our script relies on, then load our script-->
    <script>
      window.baseurl = "${baseurl}";
      window.debug = (("${debug}" === "True") || ("${debug}" === "true"));
    </script>
    <script><%include file="munge.js.mako" /></script>
    <style><%include file="ben.css.mako" /></style>

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
      <p id="debug-message">DEBUG: Page generated ${datetime.datetime.now()}</p>
    %endif

    <div id="bodyContent">
      ${self.body()}
    </div>

  </body>
</html>
