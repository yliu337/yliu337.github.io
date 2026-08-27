// Progressive enhancements — no dependencies, degrades gracefully without JS.
(function () {
  "use strict";

  var prefersReduced =
    window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function copyText(text, done) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done, function () {});
    } else {
      var ta = document.createElement("textarea");
      ta.value = text;
      ta.setAttribute("readonly", "");
      ta.style.position = "absolute";
      ta.style.left = "-9999px";
      document.body.appendChild(ta);
      ta.select();
      try { document.execCommand("copy"); done(); } catch (e) {}
      document.body.removeChild(ta);
    }
  }

  // 1) Section-heading deep links: click the "#" to copy a direct link.
  //    (The old scroll-spy and reading-progress features died with the
  //    single-page design: nav highlighting is stamped at build time via
  //    aria-current, and no page is long enough to need a progress bar.)
  document.querySelectorAll("section[id] > h2").forEach(function (h2) {
    var id = h2.parentElement.id;
    var a = document.createElement("a");
    a.className = "heading-anchor";
    a.href = "#" + id;
    a.textContent = "#";
    a.setAttribute("aria-label", "Copy link to this section");
    h2.appendChild(a);
    a.addEventListener("click", function (e) {
      e.preventDefault();
      var url = location.origin + location.pathname + "#" + id;
      copyText(url, function () {
        a.classList.add("copied");
        a.textContent = "✓"; // ✓
        setTimeout(function () {
          a.classList.remove("copied");
          a.textContent = "#";
        }, 1300);
      });
      if (history.replaceState) history.replaceState(null, "", "#" + id);
    });
  });

  // 2) Click-to-copy email, with brief "copied" feedback.
  document.querySelectorAll(".copy-btn").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var text = btn.getAttribute("data-copy") || "";
      copyText(text, function () {
        var prev = btn.getAttribute("data-label") || btn.textContent;
        btn.setAttribute("data-label", prev);
        btn.textContent = "copied ✓";
        btn.classList.add("copied");
        setTimeout(function () {
          btn.textContent = prev;
          btn.classList.remove("copied");
        }, 1600);
      });
    });
  });

  // 3) Gentle scroll reveal — only for sections below the fold, and only
  //    when motion is allowed. Above-the-fold content is never hidden, and
  //    with JS off nothing is hidden at all.
  if ("IntersectionObserver" in window && !prefersReduced) {
    var revObserver = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (e) {
          if (e.isIntersecting) {
            e.target.classList.add("in");
            revObserver.unobserve(e.target);
          }
        });
      },
      { rootMargin: "0px 0px -8% 0px", threshold: 0.08 }
    );
    document.querySelectorAll("main section").forEach(function (s) {
      if (s.getBoundingClientRect().top > window.innerHeight * 0.9) {
        s.classList.add("reveal");
        revObserver.observe(s);
      }
    });
  }

  // 4) Light / dark toggle — the site is dark by default; this opts into light
  //    and remembers the choice.
  var toggle = document.getElementById("theme-toggle");
  if (toggle) {
    // Sun and moon flank the track and label its two ends; the track itself
    // carries nothing but the knob. Drawn once, so flipping the theme only
    // changes state on the button and the knob can slide.
    var SUN =
      '<svg class="switch-ic switch-ic--sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4.2"/><path d="M12 2.5v2.2M12 19.3v2.2M4.6 4.6l1.6 1.6M17.8 17.8l1.6 1.6M2.5 12h2.2M19.3 12h2.2M4.6 19.4l1.6-1.6M17.8 6.2l1.6-1.6"/></svg>';
    var MOON =
      '<svg class="switch-ic switch-ic--moon" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M21 12.8A8.5 8.5 0 1 1 11.2 3a6.8 6.8 0 0 0 9.8 9.8z"/></svg>';
    toggle.innerHTML =
      SUN + '<span class="switch-track"><span class="switch-knob"></span></span>' + MOON;
    var effective = function () {
      // Dark unless the visitor has explicitly chosen light.
      return document.documentElement.getAttribute("data-theme") === "light"
        ? "light"
        : "dark";
    };
    var render = function () {
      var dark = effective() === "dark";
      toggle.setAttribute(
        "aria-label",
        dark ? "Switch to light mode" : "Switch to dark mode"
      );
      toggle.setAttribute("aria-pressed", dark ? "true" : "false");
      // Keep the browser chrome in step with the page.
      var meta = document.querySelector('meta[name="theme-color"]');
      if (meta) meta.setAttribute("content", dark ? "#15171c" : "#1F3A68");
    };
    toggle.addEventListener("click", function () {
      var next = effective() === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", next);
      try { localStorage.setItem("theme", next); } catch (e) {}
      render();
    });
    render();
  }
})();
