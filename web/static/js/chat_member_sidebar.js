document.addEventListener("DOMContentLoaded", () => {
  const sidebar = document.getElementById("sidebar");
  const appWrapper = document.getElementById("appWrapper");
  const sidebarButtons = document.querySelectorAll(".chat-sidebar-btn");

  // 사이드바 토글
  sidebarButtons.forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      sidebar.classList.toggle("active");
      appWrapper?.classList.toggle("sidebar-open");
    });
  });

  // 유저 드롭다운 토글
  const userIconBtn = document.getElementById("chatUserIcon");
  const userDropdown = document.getElementById("chatDropdownMenu");

  userIconBtn?.addEventListener("click", (e) => {
    e.stopPropagation();
    userDropdown.classList.toggle("show");
  });

  // 외부 클릭 시 닫기
  document.addEventListener("click", () => {
    userDropdown?.classList.remove("show");
    sidebar?.classList.remove("active");
    appWrapper?.classList.remove("sidebar-open");
  });

  // 사이드바 내부 클릭 시 닫히지 않도록
  sidebar?.addEventListener("click", (e) => e.stopPropagation());
});

// 제목 클릭 시 이동
function handleTitleClick(event, chatId) {
  const input = document.querySelector(`#chat-title-${chatId}`);
  if (!input.hasAttribute("readonly")) {
    event.stopPropagation(); // 수정 중이면 이동 막기
    return;
  }
  goToChat(chatId);
}

// 제목 수정
function editChatTitle(chatId) {
  const input = document.querySelector(`#chat-title-${chatId}`);
  input.removeAttribute("readonly");
  input.focus();

  input.addEventListener("mousedown", (e) => e.stopPropagation(), { once: true });

  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      saveChatTitle(chatId, input);
    }
  }, { once: true });

  input.addEventListener("blur", () => {
    saveChatTitle(chatId, input);
  }, { once: true });
}

// 제목 저장
function saveChatTitle(chatId, input) {
  const newTitle = input.value.trim();
  if (!newTitle) {
    alert("제목은 비워둘 수 없습니다.");
    input.focus();
    return;
  }

  fetch(`/chat/member/update-title/${chatId}/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCSRFToken(),
    },
    body: JSON.stringify({ title: newTitle }),
  }).then((res) => {
    if (res.ok) {
      input.setAttribute("readonly", true);
    } else {
      alert("제목 수정 실패");
    }
  }).catch((e) => {
    alert("서버 오류: " + e.message);
  });
}

// 채팅 삭제
function deleteChat(chatId) {
  if (!confirm("이 채팅을 삭제하시겠습니까?")) return;

  const currentPath = window.location.pathname;
  const isCurrentChat = currentPath.includes(`/member/chat/${chatId}/`);

  fetch(`/chat/member/delete/${chatId}/`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCSRFToken(),
    },
  }).then((res) => {
    if (res.ok) {
      document.querySelector(`#chat-${chatId}`)?.remove();

      if (isCurrentChat) {
        const firstRemainingChat = document.querySelector(".question-item");
        if (firstRemainingChat) {
          const firstInput = firstRemainingChat.querySelector("input");
          if (firstInput) {
            const id = firstInput.id.replace("chat-title-", "");
            goToChat(id);
          }
        } else {
          window.location.href = "/chat/main/";
        }
      }
    } else {
      alert("삭제 실패");
    }
  });
}

// 이동 함수
function goToChat(chatId) {
  const form = document.createElement("form");
  form.method = "POST";
  form.action = `/chat/member/chat/${chatId}/`;

  const csrfToken = getCSRFToken();
  const csrfInput = document.createElement("input");
  csrfInput.type = "hidden";
  csrfInput.name = "csrfmiddlewaretoken";
  csrfInput.value = csrfToken;
  form.appendChild(csrfInput);

  document.body.appendChild(form);
  form.submit();
}

// CSRF 토큰 추출
function getCSRFToken() {
  const name = "csrftoken";
  const cookie = document.cookie.split(";").find((c) => c.trim().startsWith(name + "="));
  return cookie ? cookie.trim().split("=")[1] : "";
}
