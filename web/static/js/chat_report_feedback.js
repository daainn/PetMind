document.addEventListener('DOMContentLoaded', () => {
  const reportBtn = document.getElementById('reportDownloadBtn');
  const calendarPopup = document.getElementById('chatCalendar');
  const confirmBtn = document.getElementById('calendarConfirmBtn');
  const dateInput = document.getElementById('reportDate');
  const feedbackModal = document.getElementById('feedbackModal');
  const modalClose = document.getElementById('modalCloseBtn');
  const progressBar = document.querySelector('.progress-bar');
  const downloadBtn = document.getElementById('downloadBtn');
  const submitBtn = document.querySelector('.submit-btn');
  const feedbackInput = document.querySelector('.feedback-input-wrapper textarea');
  

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
    onChange: function(selectedDates, dateStr, instance) {
      if (selectedDates.length === 2) {
        const diffInTime = Math.abs(selectedDates[1] - selectedDates[0]);
        const diffInDays = diffInTime / (1000 * 3600 * 24);

        if (diffInDays > 6) {
          alert("최대 7일까지만 선택 가능합니다.");
          instance.clear();
        }
      }
    }
  });

  dateInput.value = '';
  fp.clear();

  calendarPopup.style.display = 'none';

  reportBtn.addEventListener('click', () => {
    const isHidden = calendarPopup.style.display === 'none';
    calendarPopup.style.display = isHidden ? 'block' : 'none';

    if (isHidden) {
      fp.open();
    }
  });

  confirmBtn.addEventListener('click', () => {
    const selectedDate = dateInput.value;
    if (!selectedDate) {
      alert("날짜를 선택해주세요.");
      return;
    }

    fp.close();
    calendarPopup.style.display = 'none';

    dateInput.value = '';
    fp.clear();

    feedbackModal.style.display = 'block';
    });


  modalClose?.addEventListener('click', () => {
    feedbackModal.style.display = 'none';

    ratingValue.value = 0;
    document.querySelectorAll('.star').forEach(s => {
      s.src = starContainer.dataset.gray;
    });

    feedbackInput.value = '';
    pollModelStatus();
  });

  const starContainer = document.querySelector('.star-rating-img');
  const stars = document.querySelectorAll('.star-rating-img .star');
  const ratingValue = document.getElementById('ratingValue');

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

  function pollModelStatus() {
    const interval = setInterval(async () => {
      const res = await fetch('/api/report/status/');
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
    const chatId = parseInt(document.getElementById('chatId').value);

    if (!score || !feedback) {
      alert("별점과 피드백을 모두 입력해주세요.");
      return;
    }

    const response = await fetch('/api/review/submit/', {
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
      document.querySelectorAll('.star').forEach(s => s.src = starContainer.dataset.gray);
    } else {
      const errorText = await response.text();
      alert("피드백 저장 실패: " + errorText);
    }
  });

  document.getElementById('downloadBtn').addEventListener('click', () => {
  const chatId = document.getElementById('chatId').value;
  window.location.href = `/chat/report/pdf/${chatId}/`;
  });

  function getCSRFToken() {
    return document.cookie.split('; ')
      .find(row => row.startsWith('csrftoken='))
      ?.split('=')[1];
  }
});
