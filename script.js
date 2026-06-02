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
    var navObserver = new IntersectionObserver(
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
    sections.forEach(function (s) { navObserver.observe(s); });
  }

  // 2) Reading progress bar.
  var bar = document.getElementById("progress");
  if (bar) {
    var updateBar = function () {
      var d = document.documentElement;
      var max = d.scrollHeight - d.clientHeight;
      var y = window.pageYOffset || d.scrollTop || 0;
      bar.style.width = (max > 0 ? (y / max) * 100 : 0) + "%";
    };
    var ticking = false;
    window.addEventListener("scroll", function () {
      if (!ticking) {
        ticking = true;
        requestAnimationFrame(function () { updateBar(); ticking = false; });
      }
    }, { passive: true });
    window.addEventListener("resize", updateBar, { passive: true });
    updateBar();
  }

  // 3) Section-heading deep links: click the "#" to copy a direct link.
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

  // 4) Click-to-copy email, with brief "copied" feedback.
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

  // 5) Gentle scroll reveal — only for sections below the fold, and only
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

  // 6) Light / dark toggle — overrides the system setting and remembers it.
  var toggle = document.getElementById("theme-toggle");
  if (toggle) {
    var SUN =
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4.2"/><path d="M12 2.5v2.2M12 19.3v2.2M4.6 4.6l1.6 1.6M17.8 17.8l1.6 1.6M2.5 12h2.2M19.3 12h2.2M4.6 19.4l1.6-1.6M17.8 6.2l1.6-1.6"/></svg>';
    var MOON =
      '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M21 12.8A8.5 8.5 0 1 1 11.2 3a6.8 6.8 0 0 0 9.8 9.8z"/></svg>';
    var effective = function () {
      var f = document.documentElement.getAttribute("data-theme");
      if (f === "light" || f === "dark") return f;
      return window.matchMedia &&
        window.matchMedia("(prefers-color-scheme: dark)").matches
        ? "dark"
        : "light";
    };
    var render = function () {
      var dark = effective() === "dark";
      toggle.innerHTML = dark ? SUN : MOON;
      toggle.setAttribute(
        "aria-label",
        dark ? "Switch to light mode" : "Switch to dark mode"
      );
      toggle.setAttribute("aria-pressed", dark ? "true" : "false");
    };
    toggle.addEventListener("click", function () {
      var next = effective() === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", next);
      try { localStorage.setItem("theme", next); } catch (e) {}
      render();
    });
    if (window.matchMedia) {
      var mq = window.matchMedia("(prefers-color-scheme: dark)");
      if (mq.addEventListener) mq.addEventListener("change", render);
      else if (mq.addListener) mq.addListener(render);
    }
    render();
  }
})();
