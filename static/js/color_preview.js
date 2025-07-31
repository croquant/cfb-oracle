document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('input[data-color-preview]').forEach(function(input) {
    const previewId = input.dataset.colorPreview;
    const preview = document.getElementById(previewId);
    function update() {
      if (preview) {
        preview.style.backgroundColor = input.value || 'transparent';
      }
    }
    input.addEventListener('input', update);
    update();
  });
});
