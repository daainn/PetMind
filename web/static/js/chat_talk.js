document.addEventListener('DOMContentLoaded', () => {
  // 시간 포맷 변환
  document.querySelectorAll(".chat-time").forEach(el => {
    const rawTime = el.getAttribute("data-time");
    if (!rawTime) return;
    const date = new Date(rawTime);
    el.textContent = !isNaN(date)
      ? date.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit', hour12: true })
      : '시간 오류';
  });

  // 게스트 체크: 비로그인 사용자 기능 제한
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

  // 이미지 미리보기 & 채팅 전송 공통 함수
  let imageInput = document.getElementById('imageInput');
  const imagePreviewContainer = document.getElementById('imagePreviewContainer');
  let currentFileURLs = [];
  
  // 최초 등록 + 이후 동적 재등록용 함수로 만듦
  function attachImagePreviewListener(input) {
    if (!input || !imagePreviewContainer) {
      console.log('attachImagePreviewListener: input 또는 imagePreviewContainer가 없음');
      return;
    }
    input.addEventListener('change', () => {
      console.log('미리보기 영역 초기화 전:', imagePreviewContainer.innerHTML);
      imagePreviewContainer.innerHTML = '';
      console.log('미리보기 영역 초기화 후:', imagePreviewContainer.innerHTML);
      currentFileURLs.forEach(url => URL.revokeObjectURL(url));
      currentFileURLs = [];
      [...input.files].forEach(file => {
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
 
  // 채팅 메시지/답변 말풍선 출력
  const chatHistory = document.querySelector('.chat-history');
  const addChatBubble = (message, side = 'user', images = []) => {
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
      html += `
        <div class="chat-message-block">
          <div class="chat-message ${side}-message">
            <div class="message-content">${message}</div>
          </div>
        </div>
      `;
    }

    const wrapper = document.createElement('div');
    wrapper.classList.add('chat-message-wrapper', `${side}-side`);
    wrapper.innerHTML = html;
    chatHistory.appendChild(wrapper);
    chatHistory.scrollTop = chatHistory.scrollHeight;
    return wrapper;
  };



  // 로딩 애니메이션 말풍선
  const addLoadingBubble = () => addChatBubble(
    `<span class="dot-loader">
      <span class="dot"></span><span class="dot"></span><span class="dot"></span>
    </span>`, 'bot'
  );

  // 채팅 전송 함수
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
    .then(data => { loadingElem.querySelector('.message-content').textContent = data.response; })
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
      addChatBubble(userMsg, 'user');

      const loadingElem = addLoadingBubble();

      sendChat(form, userMsg, loadingElem);

      messageInput.value = '';
      console.log("메시지 제거 후:" + messageInput.value)
      if (imagePreviewContainer) imagePreviewContainer.innerHTML = '';
      console.log("이미지 미리보기 제거 후:", imagePreviewContainer.innerHTML);

      // 파일 input을 완전히 리셋 
      if (ImageChatingInput && ImageChatingInput.parentNode) {
        ImageChatingInput.value = '';
        const newInput = ImageChatingInput.cloneNode(true);
        ImageChatingInput.parentNode.replaceChild(newInput, ImageChatingInput);
        imageInput = newInput;
        console.log("파일 input 리셋 후 files:", imageInput.files);
        console.log("파일 input 리셋 후 value:", imageInput.value);
        attachImagePreviewListener(newInput); // 꼭 여기서 미리보기 리스너 재등록!
        console.log("리스너 재 등록후 files:", imageInput.files);
        console.log("리스너 재 등록후 value:", imageInput.value);
      }
      setTimeout(() => {
        fileUrls.forEach(url => URL.revokeObjectURL(url));
      }, 5000);
      // currentFileURLs도 즉시 비워줌 (미리보기용)
      currentFileURLs = [];
  });
  }


  // 첫질문 후 chat_talk.html로 로드되며 응답 처리
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
      .then(data => { loadingElem.querySelector('.message-content').textContent = data.response; })
      .catch(() => { loadingElem.querySelector('.message-content').textContent = "응답을 받을 수 없습니다."; });

    if (window.history.replaceState) {
      const url = new URL(window.location);
      url.searchParams.delete('just_sent');
      url.searchParams.delete('last_msg');
      window.history.replaceState({}, document.title, url.pathname + url.search);
    }
  }
});
