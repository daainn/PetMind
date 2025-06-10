document.addEventListener('DOMContentLoaded', () => {
  function formatKoreanTime(isoString) {
    const date = new Date(isoString);
    let hours = date.getHours();
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const isAM = hours < 12;
    let ampm = isAM ? "오전" : "오후";
    if (hours === 0) {
      hours = 12;
    } else if (hours > 12) {
      hours -= 12;
    }
    return `${ampm} ${String(hours).padStart(2, '0')}:${minutes}`;
  }

  document.querySelectorAll(".chat-time").forEach(el => {
    const rawTime = el.getAttribute("data-time");
    if (!rawTime) return;
    el.textContent = formatKoreanTime(rawTime);
  });

  const isGuest = window.isGuest; 
  if (isGuest) {
    [
      ['.image-upload-btn', "이미지 업로드는 로그인 후 이용하실 수 있습니다."],
      ['#recommendTrigger', "추천 콘텐츠는 로그인 후 이용하실 수 있습니다."]
    ].forEach(([selector, msg]) => {
      const btn = document.querySelector(selector);
      if (btn) btn.addEventListener('click', e => { e.preventDefault(); alert(msg); });
    });
  }

  let imageInput = document.getElementById('imageInput');
  const imagePreviewContainer = document.getElementById('imagePreviewContainer');
  let currentFileURLs = [];
  
  function attachImagePreviewListener(input) {
    if (!input || !imagePreviewContainer) {
      console.log('attachImagePreviewListener: input 또는 imagePreviewContainer가 없음');
      return;
    }
    input.addEventListener('change', () => {
      imagePreviewContainer.innerHTML = '';
      currentFileURLs.forEach(url => URL.revokeObjectURL(url));
      currentFileURLs = [];
      let files = [...input.files];
      if (files.length > 3) {
        alert('이미지는 최대 3장까지만 첨부할 수 있습니다.');
        files = files.slice(0, 3);
      }
      files.forEach(file => {
        const url = URL.createObjectURL(file);
        currentFileURLs.push(url);
        imagePreviewContainer.insertAdjacentHTML(
          'beforeend',
          `<img src="${url}" class="preview-image" style="width:80px;height:80px;object-fit:cover;border-radius:8px;margin-right:4px;">`
        );
      });
      console.log('최종 미리보기 영역:', imagePreviewContainer.innerHTML);
    });
  }
  attachImagePreviewListener(imageInput);

  function customMarkdownParse(text) {
    if (!text) return '';

    text = text.replace(/"[^"]*"|'[^']*'|`[^`]*`/g, (match) => {
        return match.replace(/\./g, '[[DOT]]')
                    .replace(/!/g, '[[EXCL]]')
                    .replace(/\?/g, '[[QST]]');
    });

    text = text.replace(/\*\*?분석\*\*?(?::)?\s?/g, '### ✅ 문제 행동 분석\n');
    text = text.replace(/\*\*?해결책 제시\*\*?(?::)?\s?/g, '\n### 🐾 솔루션\n');
    text = text.replace(/\*\*?추가 질문\*\*?(?::)?\s?/g, '\n### 추가 질문\n');
    text = text.replace(/\*\*(.+?)\*\*/g, '<b>$1</b>');

    text = text.replace(/(\d+)\.\s/g, '<br><span style="margin-left:1em; display:inline-block;">$1.</span> ');
    text = text.replace(/([.!?])(?=[^\d<\n])/g, '$1<br>');
    text = text.replace(/(<br>\s*){2,}/g, '<br>');
    text = text.replace(/^### (.+)$/gm, '<h3>$1</h3>');

    let sectionRegex = /<h3>(.*?)<\/h3>(.*?)(?=(<h3>|$))/gs;
    let result = '';
    let lastIndex = 0;
    let match;
    while ((match = sectionRegex.exec(text)) !== null) {
        result += `<div class="answer-section"><h3>${match[1]}</h3>${match[2].trim()}</div>`;
        lastIndex = sectionRegex.lastIndex;
    }

    if (!result) {
        result = `<div class="answer-section">${text.trim()}</div>`;
    }

    result = result.replace(/<hr>/g, '');
    result = result.replace(/\[\[DOT\]\]/g, '.').replace(/\[\[EXCL\]\]/g, '!').replace(/\[\[QST\]\]/g, '?');
    return result;
  }

  const chatHistory = document.querySelector('.chat-history');
  const addChatBubble = (message, side = 'user', images = [], createdAt = null) => {
    let html = '';

    if (images.length) {
      html += `<div class="chat-image-block">`;
      images.forEach(url => {
        if (url.startsWith('blob:') || url.startsWith('/media/')) {
          html += `<img src="${url}" class="preview-image" style="width:80px;height:80px;object-fit:cover;border-radius:8px;margin-right:4px;">`;
        }
      });
      html += `</div>`;
    }

    if (message) {
      const parsed = (side === 'bot') ? customMarkdownParse(message) : message;
      let timeHtml = '';
      if (createdAt) {
        const timeClass = side === 'user' ? 'chat-time side-time left-time' : 'chat-time side-time right-time';
        timeHtml = `<span class="${timeClass}" data-time="${createdAt}">${formatKoreanTime(createdAt)}</span>`;
      }
      if (side === 'user') {
        html += `
          <div class="chat-message-block" style="display: flex; justify-content: flex-end; align-items: center; gap: 6px; width: 100%;">
            ${timeHtml}
            <div class="chat-message ${side}-message">
              <div class="message-content">${parsed}</div>
            </div>
          </div>
        `;
      } else {
        html += `
          <div class="chat-message-block" style="display: flex; justify-content: flex-start; align-items: center; gap: 6px; width: 100%;">
            <div class="chat-message ${side}-message">
              <div class="message-content">${parsed}</div>
            </div>
            ${timeHtml}
          </div>
        `;
      }
    }

    const wrapper = document.createElement('div');
    wrapper.classList.add('chat-message-wrapper', `${side}-side`);
    wrapper.innerHTML = html;
    chatHistory.appendChild(wrapper);
    chatHistory.scrollTop = chatHistory.scrollHeight;
    return wrapper;
  };

  const addLoadingBubble = () => addChatBubble(
    `<span class="dot-loader">
      <span class="dot"></span><span class="dot"></span><span class="dot"></span>
    </span>`, 'bot', [], null
  );

  const sendChat = (form, message, loadingElem, userMsgTime) => {
    const formData = new FormData(form);
    formData.set('message', message); 
    fetch(form.action, {
      method: 'POST',
      body: formData,
      headers: { 'X-CSRFToken': form.querySelector('[name="csrfmiddlewaretoken"]').value },
      credentials: 'same-origin'
    })
    .then(res => res.json())
    .then(data => {
      if (loadingElem && loadingElem.parentNode) loadingElem.parentNode.removeChild(loadingElem);
      const botTime = data.created_at || new Date().toISOString();
      addChatBubble(data.response, 'bot', [], botTime);
    })
    .catch(err => {
      if (loadingElem && loadingElem.querySelector('.message-content')) {
        loadingElem.querySelector('.message-content').textContent = "응답을 받을 수 없습니다.";
      }
      console.error("오류 발생:", err);
    });
  };

  const form = document.querySelector('.chat-input-form');
  if (form && chatHistory) {
    const messageInput = form.querySelector('textarea');
    form.addEventListener('submit', e => {
      e.preventDefault();
      const fd = new FormData(form);
      for (let [k, v] of fd.entries()) {
      console.log("submit 후 폼데이터", k, v);
      }
      const userMsg = messageInput.value;
      let ImageChatingInput = document.getElementById('imageInput');
      let files = ImageChatingInput && ImageChatingInput.files ? [...ImageChatingInput.files] : [];
      let fileUrls = files.length > 0 ? files.map(file => URL.createObjectURL(file)) : [];
      // 현재 시간
      const nowISOString = new Date().toISOString();
      if (fileUrls.length > 0) {
        addChatBubble('', 'user', fileUrls, nowISOString);
      }
      if (userMsg && userMsg.trim() !== '') {
        addChatBubble(userMsg, 'user', [], nowISOString);
      }
      const loadingElem = addLoadingBubble();
      sendChat(form, userMsg, loadingElem, nowISOString);
      messageInput.value = '';
      if (imagePreviewContainer) imagePreviewContainer.innerHTML = '';
      if (ImageChatingInput && ImageChatingInput.parentNode) {
        ImageChatingInput.value = '';
        const newInput = ImageChatingInput.cloneNode(true);
        ImageChatingInput.parentNode.replaceChild(newInput, ImageChatingInput);
        imageInput = newInput;
        attachImagePreviewListener(newInput); 
      }
      setTimeout(() => {
        fileUrls.forEach(url => URL.revokeObjectURL(url));
      }, 5000);
      currentFileURLs = [];
  });
  }

  const params = new URLSearchParams(window.location.search);
  const justSent = params.get('just_sent');
  const lastMsg = params.get('last_msg');
  if (justSent === '1' && lastMsg && chatHistory) {
    const normalize = str => (str || '').replace(/\s+/g, '').trim();
    const userBubbles = chatHistory.querySelectorAll('.chat-message-wrapper.user-side');
    const seen = new Set();
    userBubbles.forEach(wrapper => {
      const msg = wrapper.querySelector('.message-content');
      if (msg) {
        const key = normalize(msg.textContent);
        if (seen.has(key)) {
          wrapper.remove();
        } else {
          seen.add(key);
        }
      }
    });

    const userMsgs = chatHistory.querySelectorAll('.user-side .message-content');
    let alreadyExists = false;
    let createdAt = null;
    Array.from(userMsgs).forEach(el => {
      if (normalize(el.textContent) === normalize(lastMsg)) {
        alreadyExists = true;
        const parentBlock = el.closest('.chat-message-block');
        if (parentBlock) {
          const timeElem = parentBlock.querySelector('.chat-time[data-time]');
          if (timeElem) {
            createdAt = timeElem.getAttribute('data-time');
          }
        }
      }
    });
    if (!alreadyExists) {
      createdAt = createdAt || new Date().toISOString();
      addChatBubble(lastMsg, 'user', [], createdAt);
    }
    const loadingElem = addLoadingBubble();
    fetch(window.location.pathname, {
      method: 'POST',
      headers: {
        'X-CSRFToken': document.querySelector('[name="csrf_token"], [name="csrfmiddlewaretoken"]').value,
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: `message=${encodeURIComponent(lastMsg)}`,
      credentials: 'same-origin'
    })
      .then(res => res.json())
      .then(data => {
        const createdAt = data.created_at || new Date().toISOString();
        if (loadingElem && loadingElem.parentNode) loadingElem.parentNode.removeChild(loadingElem);
        addChatBubble(data.response, 'bot', [], createdAt);
      })
      .catch(() => { loadingElem.querySelector('.message-content').textContent = "응답을 받을 수 없습니다."; });

    if (window.history.replaceState) {
      const url = new URL(window.location);
      url.searchParams.delete('just_sent');
      url.searchParams.delete('last_msg');
      window.history.replaceState({}, document.title, url.pathname + url.search);
    }
  }

  
});
