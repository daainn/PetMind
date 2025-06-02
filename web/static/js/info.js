function skipSection(input) {
  const fieldset = input.closest(".info-title").nextElementSibling.querySelector("fieldset");
  if (!fieldset) return;

  if (input.checked) {
    fieldset.disabled = true;
    fieldset.classList.add("dimmed");
  } else {
    fieldset.disabled = false;
    fieldset.classList.remove("dimmed");
  }
}

document.querySelector("form").addEventListener("submit", function(e) {
  if (!confirm("입력한 정보를 제출하시겠습니까?")) {
    e.preventDefault();
  }
});

function handleCancel() {
  if (confirm("입력을 취소하고 이전 페이지로 돌아가시겠습니까?")) {
    window.location.href = "/info/cancel";
  }
}
