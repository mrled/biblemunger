<h2>Suggestions</h2>
<p>Can't think of anything to search for?</p>
<p>
  <input type="button" value="Show Favorite Searches" onclick="toggleHideFavorites();" />
</p>

<div id="searchFavorites">
  <script>toggleHideFavorites()</script>
  <p>These are some of my favorites:</p>
  <div id="searchFavoriteResults">
    <%include file="saved.html.mako" args="pairs=favorites" />
  </div>
</div>
