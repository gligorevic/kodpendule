/* Navigation helpers only: all changes still go through Django's validated forms. */
(function () {
  "use strict";
  document.querySelectorAll('[data-admin-filter]').forEach(function (select) {
    select.addEventListener('change', function () { window.location.search = select.value; });
  });
  var nav = document.getElementById('kp-form-sections');
  if (nav) {
    document.querySelectorAll('fieldset.module').forEach(function (fieldset, index) {
      var heading = fieldset.querySelector('h2');
      if (!heading) return;
      var id = 'kp-form-section-' + index;
      fieldset.id = fieldset.id || id;
      var link = document.createElement('a');
      link.href = '#' + fieldset.id;
      link.textContent = heading.textContent.trim();
      link.addEventListener('click', function () {
        var details = fieldset.querySelector('details');
        if (details) details.open = true;
      });
      nav.appendChild(link);
    });
    nav.hidden = !nav.children.length;
  }
})();
