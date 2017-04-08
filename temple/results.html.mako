<%page args="search, replace, verses" />
<%
import re
%>

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

