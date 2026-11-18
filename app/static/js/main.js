// Grand Haven Hotel — Main Client Script

document.addEventListener('DOMContentLoaded', function () {
  // 1. Auto-dismiss flash alerts after 5 seconds
  const alerts = document.querySelectorAll('.alert-dismissible');
  alerts.forEach(function (alert) {
    setTimeout(function () {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      if (bsAlert) {
        bsAlert.close();
      }
    }, 6000);
  });

  // 2. Synchronize check-in and check-out date inputs
  const checkInInput = document.getElementById('check_in') || document.querySelector('input[name="check_in"]');
  const checkOutInput = document.getElementById('check_out') || document.querySelector('input[name="check_out"]');

  if (checkInInput && checkOutInput) {
    checkInInput.addEventListener('change', function () {
      if (checkInInput.value) {
        const inDate = new Date(checkInInput.value);
        const minOut = new Date(inDate);
        minOut.setDate(minOut.getDate() + 1);

        const yyyy = minOut.getFullYear();
        const mm = String(minOut.getMonth() + 1).padStart(2, '0');
        const dd = String(minOut.getDate()).padStart(2, '0');
        const minOutStr = `${yyyy}-${mm}-${dd}`;

        checkOutInput.min = minOutStr;
        if (checkOutInput.value && checkOutInput.value <= checkInInput.value) {
          checkOutInput.value = minOutStr;
        }
      }
    });
  }

  // 3. Password Show/Hide Toggle
  const togglePassBtns = document.querySelectorAll('.toggle-password-btn');
  togglePassBtns.forEach(btn => {
    btn.addEventListener('click', function () {
      const targetInput = document.querySelector(this.getAttribute('data-target'));
      if (targetInput) {
        const isPassword = targetInput.type === 'password';
        targetInput.type = isPassword ? 'text' : 'password';
        const icon = this.querySelector('i');
        if (icon) {
          icon.classList.toggle('bi-eye', !isPassword);
          icon.classList.toggle('bi-eye-slash', isPassword);
        }
      }
    });
  });

  // 4. Initialize Tooltips
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });
});
