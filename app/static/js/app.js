// Dynamic segments handler for Multi-Leg Itinerary (US-07)
function addItinerarySegment() {
  const container = document.getElementById('itinerary-segments-container');
  if (!container) return;

  const count = container.querySelectorAll('.segment-row').length + 1;
  const template = document.getElementById('segment-template');
  if (!template) return;

  const clone = template.content.cloneNode(true);
  const row = clone.querySelector('.segment-row');
  row.querySelector('.segment-number').textContent = `Segmen ${count}`;
  container.appendChild(clone);
}

function removeItinerarySegment(btn) {
  const container = document.getElementById('itinerary-segments-container');
  if (!container) return;
  const rows = container.querySelectorAll('.segment-row');
  if (rows.length <= 2) {
    alert("Itinerary multi-destinasi membutuhkan minimal 2 segmen.");
    return;
  }
  btn.closest('.segment-row').remove();

  // Re-number remaining segments
  const remaining = container.querySelectorAll('.segment-row');
  remaining.forEach((r, idx) => {
    r.querySelector('.segment-number').textContent = `Segmen ${idx + 1}`;
  });
}

// Confirmation modal helper for cancellation (US-05)
function confirmCancellation(event, bookingCode) {
  if (!confirm(`Apakah Anda yakin ingin membatalkan pemesanan tiket dengan kode ${bookingCode}? Tindakan ini tidak dapat dibatalkan.`)) {
    event.preventDefault();
    return false;
  }
  return true;
}
