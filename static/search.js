// Suggestions as you type: asks /api/search (a TRIE lookup in Python)
// and shows the matching people under the search box.
(function () {
  var box = document.getElementById("q");
  var list = document.getElementById("suggestions");
  if (!box || !list) return;

  var timer = null;

  function show(users) {
    list.innerHTML = "";
    if (users.length === 0) { list.hidden = true; return; }
    users.forEach(function (u) {
      var li = document.createElement("li");
      var a = document.createElement("a");
      a.href = "/user/" + encodeURIComponent(u.username);
      var av = document.createElement("span");
      av.className = "av";
      av.textContent = u.avatar;                       // textContent = safe, no HTML injection
      var text = document.createElement("span");
      text.textContent = u.name + "  @" + u.username;
      a.appendChild(av);
      a.appendChild(text);
      li.appendChild(a);
      list.appendChild(li);
    });
    list.hidden = false;
  }

  box.addEventListener("input", function () {
    clearTimeout(timer);                               // wait a moment after the last key
    var q = box.value.trim();
    if (!q) { list.hidden = true; return; }
    timer = setTimeout(function () {
      fetch("/api/search?q=" + encodeURIComponent(q))
        .then(function (r) { return r.json(); })
        .then(show)
        .catch(function () { list.hidden = true; });
    }, 150);
  });
})();