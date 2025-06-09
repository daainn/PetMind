document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll(".chat-time").forEach(el => {
    const rawTime = el.getAttribute("data-time");
    if (!rawTime) return;
    const date = new Date(rawTime);
    el.textContent = !isNaN(date)
      ? date.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit', hour12: true })
      : '시간 오류';
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
  const addChatBubble = (message, side = 'user', images = []) => {
    console.log('[addChatBubble] message:', message, 'side:', side, 'images:', images);
    let html = '';

    if (images.length) {
      html += `<div class="chat-image-block" style="margin-top:8px;">`;
      images.forEach(url => {
        if (url.startsWith('blob:') || url.startsWith('/media/')) {
          html += `<img src="${url}" class="preview-image" style="width:80px;height:80px;object-fit:cover;border-radius:8px;margin-right:4px;">`;
        }
      });
      html += `</div>`;
    }

    if (message) {
      const parsed = (side === 'bot') ? customMarkdownParse(message) : message;
      html += `
        <div class="chat-message-block">
          <div class="chat-message ${side}-message">
            <div class="message-content">${parsed}</div>
          </div>
        </div>
      `;
    }

    const wrapper = document.createElement('div');
    wrapper.classList.add('chat-message-wrapper', `${side}-side`);
    wrapper.innerHTML = html;
    console.log('[addChatBubble] wrapper.innerHTML:', wrapper.innerHTML);
    chatHistory.appendChild(wrapper);
    chatHistory.scrollTop = chatHistory.scrollHeight;
    return wrapper;
  };


  const addLoadingBubble = () => addChatBubble(
    `<span class="dot-loader">
      <span class="dot"></span><span class="dot"></span><span class="dot"></span>
    </span>`, 'bot'
  );

  const sendChat = (form, message, loadingElem) => {
    const formData = new FormData(form);
    formData.set('message', message); 
    fetch(form.action, {
      method: 'POST',
      body: formData,
      headers: { 'X-CSRFToken': form.querySelector('[name="csrfmiddlewaretoken"]').value },
      credentials: 'same-origin'
    })
    .then(res => res.json())
    .then(data => { loadingElem.querySelector('.message-content').innerHTML = customMarkdownParse(data.response); })
    .catch(err => {
      loadingElem.querySelector('.message-content').textContent = "응답을 받을 수 없습니다.";
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
      console.log("유저 메시지:" + userMsg)
      console.log("입력한 image files:", imageInput.files);
      console.log("입력한 image value:", imageInput.value);
      let ImageChatingInput = document.getElementById('imageInput');
      let files = ImageChatingInput && ImageChatingInput.files ? [...ImageChatingInput.files] : [];
      let fileUrls = files.length > 0 ? files.map(file => URL.createObjectURL(file)) : [];
      fileUrls.forEach(url => console.log("채팅에 보일 이미지 url:", url));
        
      if (fileUrls.length > 0) {
        addChatBubble('', 'user', fileUrls);
      }
      if (userMsg && userMsg.trim() !== '') {
        addChatBubble(userMsg, 'user');
      }

      const loadingElem = addLoadingBubble();

      sendChat(form, userMsg, loadingElem);

      messageInput.value = '';
      console.log("메시지 제거 후:" + messageInput.value)
      if (imagePreviewContainer) imagePreviewContainer.innerHTML = '';
      console.log("이미지 미리보기 제거 후:", imagePreviewContainer.innerHTML);

      if (ImageChatingInput && ImageChatingInput.parentNode) {
        ImageChatingInput.value = '';
        const newInput = ImageChatingInput.cloneNode(true);
        ImageChatingInput.parentNode.replaceChild(newInput, ImageChatingInput);
        imageInput = newInput;
        console.log("파일 input 리셋 후 files:", imageInput.files);
        console.log("파일 input 리셋 후 value:", imageInput.value);
        attachImagePreviewListener(newInput); 
        console.log("리스너 재 등록후 files:", imageInput.files);
        console.log("리스너 재 등록후 value:", imageInput.value);
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
    Array.from(userMsgs).forEach(el => {
      if (normalize(el.textContent) === normalize(lastMsg)) {
        alreadyExists = true;
      }
    });
    if (!alreadyExists) {
      addChatBubble(lastMsg, 'user');
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
      .then(data => { loadingElem.querySelector('.message-content').innerHTML = customMarkdownParse(data.response); })
      .catch(() => { loadingElem.querySelector('.message-content').textContent = "응답을 받을 수 없습니다."; });

    if (window.history.replaceState) {
      const url = new URL(window.location);
      url.searchParams.delete('just_sent');
      url.searchParams.delete('last_msg');
      window.history.replaceState({}, document.title, url.pathname + url.search);
    }
  }

  
});
