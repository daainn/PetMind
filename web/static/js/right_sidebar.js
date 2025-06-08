document.addEventListener('DOMContentLoaded', function () {
  const appWrapper = document.getElementById('appWrapper');
  const userIcon = document.getElementById('chatUserIcon');
  const closeBtn = document.getElementById('closeRightSidebar');

  if (userIcon && appWrapper) {
    userIcon.addEventListener('click', () => {
      const isOpen = appWrapper.classList.toggle('right-open');

      if (isOpen) {
        appWrapper.classList.remove('sidebar-open');

        const sidebar = document.getElementById("sidebar") || document.querySelector(".sidebar");
        if (sidebar?.classList.contains("active")) {
          sidebar.classList.remove("active");
        }
      }
    });
  }

  if (closeBtn && appWrapper) {
    closeBtn.addEventListener('click', () => {
      appWrapper.classList.remove('right-open');
    });
  }
});
