// Grand Haven Hotel — Dashboard Chart.js Visualizations

document.addEventListener('DOMContentLoaded', function () {
  const livePanel = document.getElementById('liveOperations');
  if (livePanel) {
    const feed = document.getElementById('liveOperationsFeed');
    let cursor = Number(livePanel.dataset.lastId || 0);
    const poll = async () => {
      try {
        const response = await fetch(`${livePanel.dataset.url}?after=${cursor}`, {
          credentials: 'same-origin',
          headers: { 'Accept': 'application/json' }
        });
        if (!response.ok) throw new Error(`Activity request failed (${response.status})`);
        const payload = await response.json();
        if (payload.events.length) {
          if (feed.firstElementChild?.classList.contains('text-muted')) feed.replaceChildren();
          for (const event of payload.events) {
            const item = document.createElement('li');
            item.className = 'py-1 border-top';
            const label = document.createElement('span');
            label.textContent = event.label;
            const time = document.createElement('time');
            time.className = 'text-muted ms-2';
            time.textContent = event.timestamp;
            item.append(label, time);
            feed.prepend(item);
            cursor = Math.max(cursor, Number(event.id));
          }
          while (feed.children.length > 8) feed.lastElementChild.remove();
        }
        cursor = Math.max(cursor, Number(payload.cursor || 0));
      } catch (error) {
        console.warn('Live activity update unavailable:', error);
      }
    };
    window.setInterval(poll, 10000);
  }

  // 1. Revenue Trend Chart
  const revenueCanvas = document.getElementById('revenueTrendChart');
  if (revenueCanvas) {
    fetch('/api/dashboard/revenue-trend')
      .then(res => res.json())
      .then(data => {
        new Chart(revenueCanvas, {
          type: 'line',
          data: {
            labels: data.labels,
            datasets: [{
              label: 'Monthly Revenue (₹)',
              data: data.data,
              borderColor: '#C5A880',
              backgroundColor: 'rgba(197, 168, 128, 0.15)',
              fill: true,
              tension: 0.35,
              pointBackgroundColor: '#1A2238',
              pointBorderColor: '#C5A880',
              pointHoverRadius: 6,
              pointRadius: 4,
              borderWidth: 2.5
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { display: false },
              tooltip: {
                callbacks: {
                  label: function (context) {
                    return ` Revenue: ₹${Number(context.raw).toLocaleString('en-IN', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
                  }
                }
              }
            },
            scales: {
              y: {
                beginAtZero: true,
                grid: { color: '#E8E2D9', borderDash: [4, 4] },
                ticks: {
                  callback: function (val) {
                    return '₹' + Number(val).toLocaleString('en-IN');
                  }
                }
              },
              x: {
                grid: { display: false }
              }
            }
          }
        });
      })
      .catch(err => console.error('Error loading revenue chart:', err));
  }

  // 2. Reservation Status Distribution Chart
  const statusCanvas = document.getElementById('statusDistributionChart');
  if (statusCanvas) {
    fetch('/api/dashboard/status-distribution')
      .then(res => res.json())
      .then(data => {
        new Chart(statusCanvas, {
          type: 'doughnut',
          data: {
            labels: data.labels,
            datasets: [{
              data: data.data,
              backgroundColor: [
                '#2E7D32', // Confirmed - green
                '#1A2238', // Checked-In - navy
                '#6C7A89', // Checked-Out - gray
                '#C62828', // Cancelled - red
                '#EF6C00'  // Pending - orange
              ],
              borderWidth: 2,
              borderColor: '#FFFFFF'
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                position: 'bottom',
                labels: { boxWidth: 12, padding: 12, font: { size: 12 } }
              }
            },
            cutout: '68%'
          }
        });
      })
      .catch(err => console.error('Error loading status chart:', err));
  }
});
