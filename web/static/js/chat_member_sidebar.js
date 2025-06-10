document.addEventListener("DOMContentLoaded", () => {
  const sidebar = document.getElementById("sidebar");
  const appWrapper = document.getElementById("appWrapper");
  const sidebarButtons = document.querySelectorAll(".chat-sidebar-btn");

  sidebarButtons.forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const isOpen = sidebar.classList.toggle("active");
      appWrapper?.classList.toggle("sidebar-open", isOpen);
      if (isOpen) appWrapper?.classList.remove("right-open");
    });
  });

  const userIconBtn = document.getElementById("chatUserIcon");
  const userDropdown = document.getElementById("chatDropdownMenu");

  userIconBtn?.addEventListener("click", (e) => {
    e.stopPropagation();
    userDropdown.classList.toggle("show");
  });

  document.addEventListener("click", () => {
    userDropdown?.classList.remove("show");
    sidebar?.classList.remove("active");
    appWrapper?.classList.remove("sidebar-open");
  });

  sidebar?.addEventListener("click", (e) => e.stopPropagation());

  document.querySelectorAll(".chat-title-input").forEach((input) => {
    const chatId = input.dataset.chatId;
    const dogId = input.dataset.dogId;

    input.addEventListener("click", (e) => {
      if (input.hasAttribute("readonly")) {
        goToChat(chatId, dogId);
      } else {
        e.stopPropagation(); 
      }
    });

    input.addEventListener("mousedown", (e) => {
      if (!input.hasAttribute("readonly")) {
        e.stopPropagation();
      }
    });

    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        saveChatTitle(chatId, dogId, input, true); 
      }
    });

    input.addEventListener("blur", () => {
      saveChatTitle(chatId, dogId, input, false);
    });
  });
});

function editChatTitle(chatId, dogId) {
  const input = document.querySelector(`#chat-title-${chatId}`);
  input.removeAttribute("readonly");
  input.focus();
  input.dataset.originalTitle = input.value; 
}

function saveChatTitle(chatId, dogId, input, shouldRedirect = false) {
  if (input.hasAttribute("readonly")) return;

  const newTitle = input.value.trim();
  const originalTitle = (input.dataset.originalTitle || "").trim();

  if (!newTitle) {
    alert("제목은 비워둘 수 없습니다.");
    input.value = originalTitle || "제목 없음";
    input.setAttribute("readonly", true);
    return;
  }

  if (newTitle === originalTitle) {
    input.setAttribute("readonly", true);
    if (shouldRedirect) goToChat(chatId, dogId);
    return;
  }

  fetch(`/chat/${dogId}/update-title/${chatId}/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCSRFToken(),
    },
    body: JSON.stringify({ title: newTitle }),
  })
    .then((res) => {
      if (res.ok) {
        input.setAttribute("readonly", true);
        input.dataset.originalTitle = newTitle;
        if (shouldRedirect) goToChat(chatId, dogId);
      } else {
        alert("제목 수정 실패");
      }
    })
    .catch((e) => {
      alert("서버 오류: " + e.message);
    });
}

function deleteChat(chatId, dogId) {
  if (!confirm("이 채팅을 삭제하시겠습니까?")) return;

  const currentPath = window.location.pathname;
  const expectedPath = `/chat/${dogId}/talk/${chatId}/`;
  const isCurrentChat = currentPath === expectedPath;

  fetch(`/chat/${dogId}/delete/${chatId}/`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCSRFToken(),
    },
  }).then((res) => {
    if (res.ok) {
      document.querySelector(`#chat-${chatId}`)?.remove();
      if (isCurrentChat) window.location.href = `/chat/${dogId}/`;
    } else {
      alert("삭제 실패");
    }
  });
}

function goToChat(chatId, dogId) {
  const form = document.createElement("form");
  form.method = "GET";
  form.action = `/chat/${dogId}/talk/${chatId}/`;

  const csrfInput = document.createElement("input");
  csrfInput.type = "hidden";
  csrfInput.name = "csrfmiddlewaretoken";
  csrfInput.value = getCSRFToken();
  form.appendChild(csrfInput);

  document.body.appendChild(form);
  form.submit();
}

function getCSRFToken() {
  const name = "csrftoken";
  const cookie = document.cookie
    .split(";")
    .find((c) => c.trim().startsWith(name + "="));
  return cookie ? cookie.trim().split("=")[1] : "";
}
