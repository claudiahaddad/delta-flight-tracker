const API = '';

async function api(path, options = {}) {
    const res = await fetch(`${API}${path}`, {
        headers: { 'Content-Type': 'application/json' },
        ...options,
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || 'Request failed');
    }
    return res.json();
}

// Dashboard
async function loadDashboard() {
    try {
        const stats = await api('/api/dashboard');
        document.getElementById('stat-active').textContent = stats.active_flights;
        document.getElementById('stat-total').textContent = stats.total_flights_tracked;
        document.getElementById('stat-savings').textContent = `$${stats.total_savings.toFixed(0)}`;
        document.getElementById('stat-notifications').textContent = stats.total_notifications;
    } catch (e) {
        console.error('Failed to load dashboard:', e);
    }
}

// Flights
async function loadFlights() {
    try {
        const flights = await api('/api/flights');
        const container = document.getElementById('flights-list');

        if (flights.length === 0) {
            container.innerHTML = '<p class="empty-state">No flights tracked yet. Add one above!</p>';
            return;
        }

        container.innerHTML = flights.map(f => {
            const priceDiff = f.current_price - f.booked_price;
            const priceClass = priceDiff < 0 ? 'price-drop' : priceDiff > 0 ? 'price-up' : '';
            const priceSign = priceDiff < 0 ? '' : priceDiff > 0 ? '+' : '';

            return `
                <div class="flight-card">
                    <div class="flight-header">
                        <span class="flight-route">${f.origin} → ${f.destination}</span>
                        <span class="flight-status ${f.status}">${f.status}</span>
                    </div>
                    <div class="flight-details">
                        <div>
                            <div class="flight-detail-label">Departure</div>
                            <div class="flight-detail-value">${formatDate(f.departure_date)}</div>
                        </div>
                        <div>
                            <div class="flight-detail-label">Booked At</div>
                            <div class="flight-detail-value">$${f.booked_price.toFixed(2)}</div>
                        </div>
                        <div>
                            <div class="flight-detail-label">Current</div>
                            <div class="flight-detail-value ${priceClass}">$${f.current_price.toFixed(2)}</div>
                        </div>
                        <div>
                            <div class="flight-detail-label">Lowest</div>
                            <div class="flight-detail-value price-drop">$${f.lowest_price.toFixed(2)}</div>
                        </div>
                        <div>
                            <div class="flight-detail-label">Savings</div>
                            <div class="flight-detail-value ${f.total_savings > 0 ? 'price-drop' : ''}">$${f.total_savings.toFixed(2)}</div>
                        </div>
                        ${f.confirmation_number ? `
                        <div>
                            <div class="flight-detail-label">Confirmation</div>
                            <div class="flight-detail-value">${f.confirmation_number}</div>
                        </div>` : ''}
                    </div>
                    <div class="flight-actions">
                        <button class="btn-sm update-price" onclick="openPriceModal(${f.id}, '${f.origin}', '${f.destination}', ${f.current_price})">Update Price</button>
                        <button class="btn-sm" onclick="toggleStatus(${f.id}, '${f.status}')">${f.status === 'tracking' ? 'Pause' : 'Resume'}</button>
                        <button class="btn-sm delete" onclick="deleteFlight(${f.id})">Delete</button>
                    </div>
                </div>
            `;
        }).join('');
    } catch (e) {
        console.error('Failed to load flights:', e);
    }
}

// Notifications
async function loadNotifications() {
    try {
        const notifications = await api('/api/notifications');
        const container = document.getElementById('notifications-list');

        if (notifications.length === 0) {
            container.innerHTML = '<p class="empty-state">No price drops detected yet.</p>';
            return;
        }

        // Fetch flight details for notifications
        const flights = await api('/api/flights');
        const flightMap = {};
        flights.forEach(f => { flightMap[f.id] = f; });

        container.innerHTML = notifications.map(n => {
            const flight = flightMap[n.flight_id];
            const route = flight ? `${flight.origin} → ${flight.destination}` : `Flight #${n.flight_id}`;
            return `
                <div class="notification-item">
                    <div>
                        <span class="notification-route">${route}</span>
                        <span class="notification-date">${formatDateTime(n.sent_at)}</span>
                    </div>
                    <div>
                        <span style="text-decoration: line-through; color: #999;">$${n.old_price.toFixed(0)}</span>
                        → $${n.new_price.toFixed(0)}
                    </div>
                    <span class="notification-savings">-$${n.savings.toFixed(0)}</span>
                </div>
            `;
        }).join('');
    } catch (e) {
        console.error('Failed to load notifications:', e);
    }
}

// Add Flight
document.getElementById('add-flight-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const data = {
        origin: document.getElementById('origin').value.toUpperCase(),
        destination: document.getElementById('destination').value.toUpperCase(),
        departure_date: document.getElementById('departure_date').value,
        return_date: document.getElementById('return_date').value || null,
        original_price: parseFloat(document.getElementById('original_price').value),
        confirmation_number: document.getElementById('confirmation_number').value || null,
        cabin_class: document.getElementById('cabin_class').value,
        passengers: parseInt(document.getElementById('passengers').value),
    };

    try {
        await api('/api/flights', {
            method: 'POST',
            body: JSON.stringify(data),
        });
        e.target.reset();
        document.getElementById('passengers').value = '1';
        refreshAll();
    } catch (err) {
        alert('Failed to add flight: ' + err.message);
    }
});

// Price Modal
function openPriceModal(flightId, origin, dest, currentPrice) {
    document.getElementById('update-flight-id').value = flightId;
    document.getElementById('modal-flight-info').textContent = `${origin} → ${dest} (currently $${currentPrice.toFixed(2)})`;
    document.getElementById('new-price').value = '';
    document.getElementById('price-modal').style.display = 'flex';
}

function closeModal() {
    document.getElementById('price-modal').style.display = 'none';
}

document.getElementById('price-update-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const flightId = document.getElementById('update-flight-id').value;
    const price = parseFloat(document.getElementById('new-price').value);

    try {
        await api(`/api/flights/${flightId}/price`, {
            method: 'POST',
            body: JSON.stringify({ price, source: 'manual' }),
        });
        closeModal();
        refreshAll();
    } catch (err) {
        alert('Failed to update price: ' + err.message);
    }
});

// Close modal on overlay click
document.getElementById('price-modal').addEventListener('click', (e) => {
    if (e.target === document.getElementById('price-modal')) {
        closeModal();
    }
});

// Toggle Status
async function toggleStatus(flightId, currentStatus) {
    const newStatus = currentStatus === 'tracking' ? 'paused' : 'tracking';
    try {
        await api(`/api/flights/${flightId}/status?status=${newStatus}`, { method: 'PATCH' });
        refreshAll();
    } catch (err) {
        alert('Failed to update status: ' + err.message);
    }
}

// Delete Flight
async function deleteFlight(flightId) {
    if (!confirm('Delete this flight? This cannot be undone.')) return;
    try {
        await api(`/api/flights/${flightId}`, { method: 'DELETE' });
        refreshAll();
    } catch (err) {
        alert('Failed to delete flight: ' + err.message);
    }
}

// Helpers
function formatDate(dateStr) {
    const d = new Date(dateStr + 'T00:00:00');
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function formatDateTime(dateStr) {
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' });
}

function refreshAll() {
    loadDashboard();
    loadFlights();
    loadNotifications();
}

// Initial load
refreshAll();
