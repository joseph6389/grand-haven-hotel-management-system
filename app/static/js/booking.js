// Grand Haven Hotel — Booking & Pricing Calculator

function escapeBookingText(value) {
  return String(value ?? '').replace(/[&<>"']/g, character => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  })[character]);
}

document.addEventListener('DOMContentLoaded', function () {
  const checkInEl = document.getElementById('wizard_check_in');
  const checkOutEl = document.getElementById('wizard_check_out');
  const searchRoomsBtn = document.getElementById('searchAvailableRoomsBtn');
  const roomResultsContainer = document.getElementById('roomResultsContainer');
  const pricingQuoteBox = document.getElementById('pricingQuoteBox');

  if (searchRoomsBtn && checkInEl && checkOutEl) {
    searchRoomsBtn.addEventListener('click', function () {
      const inDate = checkInEl.value;
      const outDate = checkOutEl.value;

      if (!inDate || !outDate) {
        alert('Please specify both check-in and check-out dates.');
        return;
      }

      if (outDate <= inDate) {
        alert('Check-out date must be strictly after check-in date.');
        return;
      }

      roomResultsContainer.innerHTML = '<div class="text-center py-4"><div class="spinner-border text-warning" role="status"></div><p class="mt-2 text-muted">Checking real-time room availability...</p></div>';

      fetch(`/api/available-rooms?check_in=${inDate}&check_out=${outDate}`)
        .then(res => res.json())
        .then(data => {
          if (data.error) {
            roomResultsContainer.innerHTML = `<div class="alert alert-danger">${escapeBookingText(data.error)}</div>`;
            return;
          }

          if (data.rooms.length === 0) {
            roomResultsContainer.innerHTML = `
              <div class="alert alert-warning text-center py-4">
                <i class="bi bi-calendar-x fs-2 d-block mb-2"></i>
                <h5>No Rooms Available For Selected Dates</h5>
                <p class="mb-0 text-muted">All operational rooms are occupied or reserved. Please try an alternative date range.</p>
              </div>`;
            return;
          }

          let html = '<div class="row g-3">';
          data.rooms.forEach(rm => {
            html += `
              <div class="col-md-6">
                <div class="card p-3 border h-100 room-select-card" id="card_room_${rm.id}">
                  <div class="form-check">
                    <input class="form-check-input room-checkbox" type="checkbox" name="room_ids" value="${rm.id}" id="room_${rm.id}" data-price="${rm.price_per_night}">
                    <label class="form-check-label w-100 cursor-pointer" for="room_${rm.id}">
                      <div class="d-flex justify-content-between align-items-center">
                        <strong class="fs-5 text-dark">Room ${escapeBookingText(rm.room_number)}</strong>
                       <span class="badge bg-gold">₹${Number(rm.price_per_night).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}/night</span>
                      </div>
                      <div class="text-muted small mt-1">
                        <span class="me-2"><i class="bi bi-tag"></i> ${escapeBookingText(rm.room_type_name)}</span>
                       <span class="me-2"><i class="bi bi-people"></i> Cap: ${rm.capacity}</span>
                        <span><i class="bi bi-layers"></i> Floor ${rm.floor}</span>
                      </div>
                    </label>
                  </div>
                </div>
              </div>`;
          });
          html += '</div>';

          roomResultsContainer.innerHTML = html;

          // Attach listeners to newly generated checkboxes
          document.querySelectorAll('.room-checkbox').forEach(cb => {
            cb.addEventListener('change', updatePricingQuote);
          });
        })
        .catch(err => {
          roomResultsContainer.innerHTML = `<div class="alert alert-danger">Error querying room availability: ${escapeBookingText(err?.message || err)}</div>`;
        });
    });
  }

  function updatePricingQuote() {
    const selectedCheckboxes = document.querySelectorAll('.room-checkbox:checked');
    const selectedIds = Array.from(selectedCheckboxes).map(cb => cb.value);

    if (selectedIds.length === 0) {
      if (pricingQuoteBox) pricingQuoteBox.classList.add('d-none');
      return;
    }

    const inDate = checkInEl.value;
    const outDate = checkOutEl.value;
    const params = new URLSearchParams();
    params.append('check_in', inDate);
    params.append('check_out', outDate);
    selectedIds.forEach(id => params.append('room_ids', id));

    fetch(`/api/pricing-quote?${params.toString()}`)
      .then(res => {
        if (!res.ok) {
          throw new Error(`Server returned status ${res.status}`);
        }
        return res.json();
      })
      .then(data => {
        if (data.error) {
          console.error('Pricing quote error:', data.error);
          return;
        }

        if (
          !Number.isFinite(Number(data.nights)) ||
          !Number.isFinite(Number(data.room_charges)) ||
          !Number.isFinite(Number(data.tax_amount)) ||
          !Number.isFinite(Number(data.total_amount))
        ) {
          throw new Error('Invalid pricing data received from the server.');
        }

        if (pricingQuoteBox) {
          pricingQuoteBox.classList.remove('d-none');
          document.getElementById('quoteNights').innerText = data.nights;
          document.getElementById('quoteRoomCharges').innerText =
            `₹${Number(data.room_charges).toFixed(2)}`;
          document.getElementById('quoteTaxes').innerText =
            `₹${Number(data.tax_amount).toFixed(2)}`;
          document.getElementById('quoteTotal').innerText =
            `₹${Number(data.total_amount).toFixed(2)}`;
        }
      })
      .catch(err => console.error('Error fetching quote:', err));
  }
});
