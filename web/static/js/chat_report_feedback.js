document.addEventListener('DOMContentLoaded', () => {
  const reportBtn = document.getElementById('reportDownloadBtn');
  const calendarPopup = document.getElementById('chatCalendar');
  const confirmBtn = document.getElementById('calendarConfirmBtn');
  const dateInput = document.getElementById('reportDate');
  const feedbackModal = document.getElementById('chat_feedbackModal');
  const modalClose = document.getElementById('chat_modalCloseBtn');
  const progressBar = document.querySelector('.progress-bar');
  const downloadBtn = document.getElementById('chat_downloadBtn');
  const submitBtn = document.getElementById('chat_submitBtn');
  const feedbackInput = document.getElementById('chat_feedbackText');
  const chatId = document.getElementById('chat_chatId')?.value;
  let tempSelectedDates = [];

  const fp = flatpickr(dateInput, {
    mode: "range",
    dateFormat: "Y-m-d",
    maxDate: "today",
    appendTo: calendarPopup,
    positionElement: calendarPopup,
    clickOpens: false,
    closeOnSelect: false,
    locale: {
      firstDayOfWeek: 1,
    },
    onChange: function (selectedDates) {
      tempSelectedDates = [...selectedDates];

      if (tempSelectedDates.length === 2) {
        const diffInDays = Math.abs(tempSelectedDates[1] - tempSelectedDates[0]) / (1000 * 3600 * 24);
        if (diffInDays > 6) {
          alert("최대 7일까지만 선택 가능합니다.");
          fp.clear();
          tempSelectedDates = [];
        }
      }
    },
    onClose: function () {
      setTimeout(() => {
        calendarPopup.style.display = 'none';
        tempSelectedDates = [];
        fp.clear();
        dateInput.value = '';
      }, 150);
    }
  });

  dateInput.value = '';
  fp.clear();
  calendarPopup.style.display = 'none';

  const formatDate = (date) => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  reportBtn.addEventListener('click', () => {
    const isHidden = calendarPopup.style.display === 'none';
    calendarPopup.style.display = isHidden ? 'block' : 'none';
    if (isHidden) fp.open();
  });

  confirmBtn.addEventListener('click', async () => {
    if (!chatId) {
      alert("chatId가 유효하지 않습니다.");
      return;
    }

    if (tempSelectedDates.length === 0) {
      alert("날짜를 선택해주세요.");
      return;
    }

    const finalDates = (tempSelectedDates.length === 1)
      ? [tempSelectedDates[0], tempSelectedDates[0]]
      : [...tempSelectedDates];

    const startDate = formatDate(finalDates[0]);
    const endDate = formatDate(finalDates[1]);

    fp.setDate(finalDates, true);
    calendarPopup.style.display = 'none';
    fp.close();

    feedbackModal.style.display = 'block';
    progressBar.style.width = '0%';
    downloadBtn.disabled = true;
    downloadBtn.classList.remove('active');

    const response = await fetch('/chat/report/generate/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCSRFToken(),
      },
      body: JSON.stringify({
        chat_id: chatId,
        start_date: startDate,
        end_date: endDate,
      }),
    });

    if (!response.ok) {
      alert("해당 날짜에는 상담을 진행하지 않았습니다!");
      feedbackModal.style.display = 'none';  // 실패 시 모달 닫기
    } else {
      pollModelStatus();
    }
  });

  const starContainer = document.querySelector('.star-rating-img');
  const stars = document.querySelectorAll('.star-rating-img .chat-star');
  const ratingValue = document.getElementById('chat_ratingValue');
  const yellowStar = starContainer.dataset.yellow;
  const grayStar = starContainer.dataset.gray;

  stars.forEach((star) => {
    star.addEventListener('click', () => {
      const selectedValue = parseInt(star.getAttribute('data-value'));
      ratingValue.value = selectedValue;
      stars.forEach((s, i) => {
        s.src = (i < selectedValue) ? yellowStar : grayStar;
      });
    });
  });

  modalClose?.addEventListener('click', () => {
    feedbackModal.style.display = 'none';
    ratingValue.value = 0;
    feedbackInput.value = '';
    stars.forEach(s => s.src = grayStar);
    progressBar.style.width = '0%';
    downloadBtn.disabled = true;
    downloadBtn.classList.remove('active');
  });

  function pollModelStatus() {
    const interval = setInterval(async () => {
      const res = await fetch('/chat/report/status/');
      const data = await res.json();
      if (data.status === 'done') {
        progressBar.style.width = '100%';
        downloadBtn.disabled = false;
        downloadBtn.classList.add('active');
        clearInterval(interval);
      } else if (data.progress) {
        progressBar.style.width = data.progress + '%';
      }
    }, 1000);
  }

  submitBtn.addEventListener('click', async () => {
    const score = parseInt(ratingValue.value);
    const feedback = feedbackInput.value.trim();

    if (!score || !feedback) {
      alert("별점과 피드백을 모두 입력해주세요.");
      return;
    }

    const response = await fetch('/chat/api/review/submit/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCSRFToken(),
      },
      body: JSON.stringify({
        chat_id: chatId,
        review_score: score,
        review: feedback
      })
    });

    if (response.ok) {
      alert("소중한 피드백 감사합니다!");
      feedbackInput.value = '';
      ratingValue.value = 0;
      stars.forEach(s => s.src = grayStar);
    } else {
      const errorText = await response.text();
      alert("피드백 저장 실패: " + errorText);
    }
  });

  downloadBtn.addEventListener('click', () => {
    window.location.href = `/chat/report/pdf/${chatId}/`;
  });

  function getCSRFToken() {
    return document.cookie.split('; ')
      .find(row => row.startsWith('csrftoken='))
      ?.split('=')[1];
  }
});
