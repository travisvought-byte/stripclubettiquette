(function () {
  "use strict";

  // Quick exit: leave for a neutral site and keep this page out of the back button.
  document.querySelectorAll("[data-exit]").forEach(function (a) {
    a.addEventListener("click", function (ev) {
      ev.preventDefault();
      try { sessionStorage.clear(); } catch (err) { /* storage blocked */ }
      window.location.replace(a.href);
    });
  });

  // Collapsible menu on small screens. Without JavaScript the menu stays open.
  var btn = document.querySelector(".navtoggle");
  var nav = document.getElementById("site-nav");
  if (btn && nav) {
    btn.hidden = false;
    nav.classList.add("collapsible");
    btn.addEventListener("click", function () {
      var open = btn.getAttribute("aria-expanded") === "true";
      btn.setAttribute("aria-expanded", String(!open));
      nav.classList.toggle("open", !open);
    });
  }

  // Directory filters. The full table shows without JavaScript.
  var form = document.getElementById("filters");
  if (form) {
    var rows = Array.prototype.slice.call(document.querySelectorAll("#clubs tbody tr"));
    var out = document.getElementById("shown");
    var timer;
    var run = function () {
      var st = form.elements.state.value;
      var status = form.elements.status.value;
      var q = form.elements.q.value.trim().toLowerCase();
      var n = 0;
      rows.forEach(function (r) {
        var ok = (!st || r.dataset.state === st) &&
                 (!status || r.dataset.status === status) &&
                 (!q || r.dataset.text.indexOf(q) !== -1);
        r.hidden = !ok;
        if (ok) { n += 1; }
      });
      out.textContent = n === rows.length
        ? "Showing all " + n + " clubs."
        : "Showing " + n + " of " + rows.length + " clubs.";
    };
    form.hidden = false;
    form.addEventListener("change", run);
    form.addEventListener("input", function () { clearTimeout(timer); timer = setTimeout(run, 250); });
    form.addEventListener("submit", function (ev) { ev.preventDefault(); run(); });
  }
  // Claim form: pick the club named in the address (?club=OH-0001), and, when
  // claims go by email, open the visitor's email app with the details filled in.
  var claim = document.getElementById("claim");
  if (claim) {
    var m = /[?&]club=([A-Z]{2}-\d{4})/.exec(window.location.search);
    if (m && claim.elements.club) { claim.elements.club.value = m[1]; }
    var to = claim.getAttribute("data-mailto");
    if (to) {
      claim.addEventListener("submit", function (ev) {
        if (!claim.checkValidity()) { return; }
        ev.preventDefault();
        var lines = [];
        Array.prototype.forEach.call(claim.elements, function (el) {
          if (!el.name || !el.value) { return; }
          var label = claim.querySelector('label[for="' + el.id + '"]');
          var text = el.tagName === "SELECT" ? el.options[el.selectedIndex].text : el.value;
          lines.push((label ? label.textContent : el.name) + ": " + text);
        });
        window.location.href = "mailto:" + to + "?subject=" + encodeURIComponent("Club listing claim") +
          "&body=" + encodeURIComponent(lines.join("\n"));
      });
    }
  }
})();
