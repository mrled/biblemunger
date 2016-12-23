<%page args="search, replace, verses" />
<%
import re
%>

%if search and replace:
  <h2>${search} ⇒ ${replace}</h2>
  %if verses and len(verses) > 0:
    <table border=0 cellspacing=5 cellpadding=5 align='CENTER'>
    %for verse in verses:
      <%
        taggedreplace = '<span class="munged">{}</span>'.format(replace)
        munged = re.sub(search, taggedreplace, verse.text)
      %>
      <tr><td>${verse.book} ${verse.chapter}:${verse.verse}</td><td>${munged}</td></tr>
    %endfor
    </table>
  %else:
    <p>Sorry, nothing to show :(</p>
  %endif
%else:
%endif

