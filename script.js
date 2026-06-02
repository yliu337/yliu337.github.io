// Progressive enhancements — no dependencies, degrades gracefully without JS.
(function () {
  "use strict";

  // 1) Highlight the top-nav link for the section currently in view.
  var links = Array.prototype.slice.call(
    document.querySelectorAll('.topnav a[href^="#"]')
  );
  var map = {};
  links.forEach(function (a) {
    var sec = document.getElementById(a.getAttribute("href").slice(1));
    if (sec) map[sec.id] = a;
  });
  var sections = Object.keys(map).map(function (id) {
    return document.getElementById(id);
  });

  if (sections.length && "IntersectionObserver" in window) {
    var current = null;
    var setActive = function (id) {
      if (id === current) return;
      current = id;
      links.forEach(function (a) { a.classList.remove("active"); });
      if (map[id]) map[id].classList.add("active");
    };
    var observer = new IntersectionObserver(
      function (entries) {
        var visible = entries.filter(function (e) { return e.isIntersecting; });
        if (visible.length) {
          visible.sort(function (a, b) {
            return a.boundingClientRect.top - b.boundingClientRect.top;
          });
          setActive(visible[0].target.id);
        }
      },
      { rootMargin: "-45% 0px -50% 0px", threshold: 0 }
    );
    sections.forEach(function (s) { observer.observe(s); });
  }

  // 2) Click-to-copy email, with brief "copied" feedback.
  document.querySelectorAll(".copy-btn").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var text = btn.getAttribute("data-copy") || "";
      var confirm = function () {
        var prev = btn.getAttribute("data-label") || btn.textContent;
        btn.setAttribute("data-label", prev);
        btn.textContent = "copied ✓";
        btn.classList.add("copied");
        setTimeout(function () {
          btn.textContent = prev;
          btn.classList.remove("copied");
        }, 1600);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(confirm, function () {});
      } else {
        var ta = document.createElement("textarea");
        ta.value = text;
        ta.setAttribute("readonly", "");
        ta.style.position = "absolute";
        ta.style.left = "-9999px";
        document.body.appendChild(ta);
        ta.select();
        try { document.execCommand("copy"); confirm(); } catch (e) {}
        document.body.removeChild(ta);
      }
    });
  });
})();
