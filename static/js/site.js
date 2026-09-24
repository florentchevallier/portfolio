/* Small, dependency-free enhancements. The site works without JavaScript. */
(function () {
  'use strict';

  // 1. Assemble e-mail addresses in the browser (keeps them out of the raw HTML).
  document.querySelectorAll('a.mail').forEach(function (a) {
    var address = a.dataset.u + '@' + a.dataset.d;
    a.href = 'mailto:' + address;
    a.textContent = address;
  });

  // 2. Interactive embeds load only when the visitor asks for them, so no third-party
  //    request (map tiles, etc.) is made just by opening a page.
  document.querySelectorAll('.embed-stage[data-embed]').forEach(function (stage) {
    var button = stage.querySelector('[data-play]');
    if (!button) return;
    button.hidden = false; // without JavaScript the "open in a new tab" link remains
    button.addEventListener('click', function () {
      var frame = document.createElement('iframe');
      frame.src = stage.dataset.embed;
      frame.title = stage.dataset.title || 'Interactive embed';
      frame.allow = 'fullscreen';
      stage.replaceChildren(frame);
      stage.classList.add('is-live');
      frame.focus();
    });
  });
})();
