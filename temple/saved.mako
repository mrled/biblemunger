<%page args="pairs" />

%if pairs:
  <ul class='noBullets'>
  %for pair in pairs:
    <li><a href="#search=${pair['search']}&replace=${pair['replace']}">${pair['search']} ⇒ ${pair['replace']}</a></li>
  %endfor
  </ul>
%else:
  <p>Sorry, nothing to show :(</p>
%endif
