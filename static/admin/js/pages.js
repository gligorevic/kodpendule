/* In-page selection preserves hidden checked inputs when searching or paging. */
(function () {
  "use strict";
  var picker = document.querySelector('[data-product-picker]');
  if (picker) {
    var search = picker.querySelector('[data-picker-search]');
    if (search) {
      var selectedOnly = picker.querySelector('[data-picker-selected]');
      var rows = Array.from(picker.querySelectorAll('tbody tr'));
      var status = picker.querySelector('[data-picker-status]');
      var page = 0, pageSize = 25;
      function fold(s) { return s.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/đ/g, 'dj'); }
      rows.forEach(function (row) { row.dataset.searchText = fold(row.textContent + " " + (row.dataset.pickerCategory || "")); });
      function render() {
        var words = fold(search.value).trim().split(/\s+/).filter(Boolean);
        var matches = rows.filter(function (row) { return words.every(function (word) { return row.dataset.searchText.includes(word); }) && (!selectedOnly.checked || row.querySelector('input[type=checkbox]').checked); });
        var pages = Math.max(1, Math.ceil(matches.length / pageSize)); page = Math.min(page, pages - 1);
        var shown = new Set(matches.slice(page * pageSize, (page + 1) * pageSize));
        rows.forEach(function (row) { row.hidden = !shown.has(row); });
        var count = rows.filter(function (row) { return row.querySelector('input[type=checkbox]').checked; }).length;
        status.textContent = count + ' ' + status.dataset.selectedLabel + ' · ' + matches.length + ' ' + status.dataset.resultsLabel;
        picker.querySelector('[data-picker-empty]').hidden = matches.length > 0;
        picker.querySelector('[data-picker-pagination]').hidden = pages <= 1;
        picker.querySelector('[data-picker-page]').textContent = (page + 1) + ' / ' + pages;
        picker.querySelector('[data-picker-prev]').disabled = page === 0;
        picker.querySelector('[data-picker-next]').disabled = page >= pages - 1;
      }
      search.addEventListener('input', function () { page = 0; render(); });
      selectedOnly.addEventListener('change', function () { page = 0; render(); });
      picker.addEventListener('change', function (e) { if (e.target.matches('tbody input[type=checkbox]')) render(); });
      picker.querySelector('[data-picker-prev]').addEventListener('click', function () { page--; render(); search.focus(); });
      picker.querySelector('[data-picker-next]').addEventListener('click', function () { page++; render(); search.focus(); });
      [['#kp-recommended-select-all, #kp-promo-select-all',true],['#kp-recommended-select-none, #kp-promo-select-none',false]].forEach(function (entry) {
        var button = picker.querySelector(entry[0]); if (button) button.addEventListener('click', function () { rows.filter(function (row) { return !row.hidden; }).forEach(function (row) { row.querySelector('input[type=checkbox]').checked = entry[1]; }); render(); });
      });
      var onPromo = picker.querySelector('#kp-promo-select-on-promo');
      if (onPromo) onPromo.addEventListener('click', function () { rows.forEach(function (row) { row.querySelector('input[type=checkbox]').checked = row.classList.contains('kp-promo-admin__row--active'); }); render(); });
      render();
    }
  }
  document.querySelectorAll('input[type=file][accept*="image"], input[type=file][name="main_image"], input[type=file][name="image"]').forEach(function (input) {
    var preview, objectUrl;
    input.addEventListener('change', function () {
      if (objectUrl) URL.revokeObjectURL(objectUrl);
      if (preview) preview.remove();
      var file = input.files[0]; if (!file || !file.type.startsWith('image/')) return;
      preview = document.createElement('img'); preview.className = 'kp-upload-preview'; preview.alt = '';
      objectUrl = URL.createObjectURL(file); preview.src = objectUrl; input.after(preview);
    });
  });
})();
