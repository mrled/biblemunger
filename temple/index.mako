<html>
<head>
  <title>${pagetitle}</title>
  <style type="text/css" src="/static/bmweb.css"></style>
  <script src="/static/bmweb.js"></script>
</head>

<body><center>
<h2><a href="/">${apptitle}</a></h2>
<p>${appsubtitle}</p>
<p>Find some text in the Bible and replace it with other text.</p>
<p>(Based on <a href="http://the-toast.net/tag/bible-verses/">some excellence</a> by Mallory Ortberg. XML KJV from <a href="http://sourceforge.net/projects/zefania-sharp/files/Bibles/ENG/King%20James/King%20James%20Version/SF_2009-01-23_ENG_KJV_%28KING%20JAMES%20VERSION%29.zip/download">the Zefania project</a>, which probably doesn't appreciate this use of it.)</p>
%if favorites:
  <p>Can't think of anything to search for? Try these:
  <ul style="list-style:none;">
    %for fav in favorites:
      <li><a href="/?search=${fav['search']}&replace=${fav['replace']}">${fav['search']} &rArr; ${fav['replace']}</a></li>
    %endfor
  </ul></p>
%endif
<form method=GET action="/">
<table border=0 cellpadding=5 cellspacing=5><tr>
%if search:
  <td valign="TOP">Search:  <input type=text name="search"  value="${search}"  size=20 autofocus="true"></td>
%else: 
  <td valign="TOP">Search:  <input type=text name="search" size=20 autofocus="true"></td>
%endif
%if replace:
  <td valign="TOP">Replace: <input type=text name="replace" value="${replace}" size=20></td>
%else: 
  <td valign="TOP">Replace: <input type=text name="replace" size=20></td>
%endif
<td valign="TOP"><input type=submit value="Munge"></td>
</tr>
</table>
</form>
%if queried:
  <h2>${resultstitle}</h2>
  <p>Embolden replacement text 
    <input name="embolden" id="emboldenbox" type="checkbox" checked="checked" onclick="emboldenMunged()"></p>
  <div id="results">
    %if results:
      <table border=0 cellspacing=5 cellpadding=5 width="540" align="CENTER">
      %for verse in results:
        ${verse.htmltr()}
      %endfor
      </table>
    %else:
      <p>None</p>
  </div>
  %endif
%endif     

</center></body>
</html>
