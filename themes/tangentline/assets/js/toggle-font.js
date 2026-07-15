(function () {
  var STORAGE_KEY = "font";
  var btn = document.getElementById("font-toggle");
  if (!btn) return;

  function currentFont() {
    return document.documentElement.getAttribute("data-font") === "gothic" ? "gothic" : "mincho";
  }

  function syncLabel() {
    btn.textContent = currentFont() === "gothic" ? "明朝体" : "ゴシック";
  }

  syncLabel();

  btn.addEventListener("click", function () {
    var next = currentFont() === "gothic" ? "mincho" : "gothic";
    if (next === "gothic") {
      document.documentElement.setAttribute("data-font", "gothic");
    } else {
      document.documentElement.removeAttribute("data-font");
    }
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch (e) {}
    syncLabel();
  });
})();
