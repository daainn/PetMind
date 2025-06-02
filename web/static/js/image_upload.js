document.addEventListener('DOMContentLoaded', function () {
  let imageInput = document.getElementById('imageInput');
  const previewContainer = document.getElementById('imagePreviewContainer');
  let fileList = [];

  imageInput?.addEventListener("change", function () {
    const newFiles = Array.from(this.files);
    let added = false;

    for (const file of newFiles) {
      if (fileList.length >= 3) {
        alert("이미지는 최대 3장까지 업로드할 수 있어요.");
        break;
      }

      const isDuplicate = fileList.some(f => f.name === file.name && f.size === file.size);
      if (isDuplicate) continue;

      fileList.push(file);
      added = true;
    }

    if (added) {
      updatePreview();
      updateInputFiles();
    }

    this.value = "";
  });

  function updatePreview() {
    previewContainer.innerHTML = "";
    fileList.forEach((file, index) => {
      const reader = new FileReader();
      reader.onload = function (e) {
        const wrapper = document.createElement("div");
        wrapper.className = "preview-image-wrapper";

        const img = document.createElement("img");
        img.src = e.target.result;
        img.className = "preview-image";

        const del = document.createElement("div");
        del.className = "delete-preview";
        del.textContent = "×";
        del.onclick = () => {
          fileList.splice(index, 1);
          updatePreview();
          updateInputFiles();
        };

        wrapper.appendChild(img);
        wrapper.appendChild(del);
        previewContainer.appendChild(wrapper);
      };
      reader.readAsDataURL(file);
    });
  }

  function updateInputFiles() {
    const newInput = imageInput.cloneNode();
    const dt = new DataTransfer();
    fileList.forEach(file => dt.items.add(file));
    newInput.files = dt.files;
    imageInput.replaceWith(newInput);
    imageInput = newInput;
    imageInput.id = "imageInput";
  }
});
