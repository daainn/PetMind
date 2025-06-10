document.addEventListener('DOMContentLoaded', function () {
  const recommendTrigger = document.getElementById('recommendTrigger');
  const recommendText = document.querySelector('.recommend-text');
  const chatHistory = document.querySelector('.chat-history');
  const textarea = document.querySelector('textarea');
  const isGuest = JSON.parse(document.getElementById('isGuestFlag')?.textContent || 'false');

  if (!recommendTrigger) return;

  recommendTrigger.addEventListener('mouseenter', () => {
    if (!recommendTrigger.classList.contains('disabled')) {
      recommendTrigger.style.backgroundColor = "#ffe6b8";
    }
  });

  recommendTrigger.addEventListener('mouseleave', () => {
    recommendTrigger.style.backgroundColor = "white";
  });

  recommendTrigger.addEventListener('click', () => {
    if (isGuest) {
      alert("추천 콘텐츠는 로그인 후 이용하실 수 있습니다.");
      return;
    }

    if (recommendTrigger.classList.contains('disabled')) return;

    const url = recommendTrigger.getAttribute('data-url');
    if (!url) return;

    fetch(url, {
      method: "GET",
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
      .then(response => response.json())
      .then(data => {
        if (data.cards_html && data.has_recommendation) {
          const wrapper = document.createElement('div');
          wrapper.className = 'chat-message-wrapper bot-side';
          wrapper.innerHTML = `
            <div class="chat-message-block">
              <div class="recommend-bubble">
                <div class="message-content">${data.cards_html}</div>
              </div>
              <span class="chat-time side-time" data-time="${new Date().toISOString()}"></span>
            </div>`;
          chatHistory.appendChild(wrapper);
          wrapper.querySelector(".chat-time").textContent = new Date().toLocaleTimeString('ko-KR', {
            hour: '2-digit',
            minute: '2-digit',
            hour12: true
          });
          chatHistory.scrollTop = chatHistory.scrollHeight;
          recommendTrigger.classList.add('disabled');
          recommendText.innerText = "추천 콘텐츠를 확인했어요!";
        } else {
          recommendText.innerText = "아직 추천할 콘텐츠가 없어요 좀 더 대화를 진행해주세요!";
        }
      });
  });

  textarea?.addEventListener('input', () => {
    if (recommendTrigger.classList.contains('disabled')) {
      recommendTrigger.classList.remove('disabled');
      recommendText.innerText = "이런 정보는 어때요? 추천 콘텐츠를 확인해보세요.";
    }
  });
});
