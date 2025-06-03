document.addEventListener('DOMContentLoaded', function () {
  const appWrapper = document.getElementById('appWrapper');
  const userIcon = document.getElementById('chatUserIcon');
  const closeBtn = document.getElementById('closeRightSidebar');

  if (userIcon && appWrapper) {
    userIcon.addEventListener('click', () => {
      appWrapper.classList.toggle('right-open');
    });
  }

  if (closeBtn && appWrapper) {
    closeBtn.addEventListener('click', () => {
      appWrapper.classList.remove('right-open');
    });
  }
});