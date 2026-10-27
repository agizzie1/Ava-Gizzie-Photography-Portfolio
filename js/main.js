(function () {
  // lightbox: open the clicked photo at full size with its caption
  var lb = document.getElementById("lb"), lbImg = document.getElementById("lbImg"), lbCap = document.getElementById("lbCap");
  document.addEventListener("click", function (e) {
    var f = e.target.closest("button.frame");
    if (!f || !lb.showModal) return;
    var img = f.querySelector("img");
    if (!img) return;
    lbImg.src = img.currentSrc || img.src;
    lbImg.alt = img.alt;
    var cap = f.parentElement.querySelector("figcaption");
    lbCap.innerHTML = cap ? cap.innerHTML : "";
    lb.showModal();
  });
  document.getElementById("lbClose").addEventListener("click", function () { lb.close(); });
  lb.addEventListener("click", function (e) { if (e.target === lb) lb.close(); });

  // underline the section in view
  var bar = document.getElementById("links");
  var links = bar.querySelectorAll("a");
  var map = {};
  links.forEach(function (a) { map[a.getAttribute("href").slice(1)] = a; });
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        links.forEach(function (a) { a.classList.remove("on"); });
        var a = map[en.target.id];
        if (!a) return;
        a.classList.add("on");
        // keep the link visible in the nav strip; scrollIntoView would also scroll the page and fight the user's scroll
        if (a.offsetLeft < bar.scrollLeft) bar.scrollLeft = a.offsetLeft;
        else if (a.offsetLeft + a.offsetWidth > bar.scrollLeft + bar.clientWidth) bar.scrollLeft = a.offsetLeft + a.offsetWidth - bar.clientWidth;
      });
    }, { rootMargin: "-45% 0px -50% 0px" });
    document.querySelectorAll("main section").forEach(function (s) { io.observe(s); });
  }
})();
