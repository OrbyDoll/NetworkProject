let map;
let polyline;
let markers = [];

function initMap() {
    if (!document.getElementById('map')) return;
    map = L.map('map').setView([20, 0], 2);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        className: 'map-tiles'
    }).addTo(map);
}

function renderMap(hops) {
    if (!map) initMap();
    
    // Clear old data
    if (polyline) map.removeLayer(polyline);
    markers.forEach(m => map.removeLayer(m));
    markers = [];

    const coords = [];
    hops.forEach(hop => {
        if (hop.lat && hop.lon) {
            coords.push([hop.lat, hop.lon]);
            const marker = L.marker([hop.lat, hop.lon]).addTo(map)
                .bindPopup(`Hop ${hop.hop_number}: ${hop.ip} (${hop.city}, ${hop.country})`);
            markers.push(marker);
        }
    });

    if (coords.length > 0) {
        polyline = L.polyline(coords, {color: '#bb86fc'}).addTo(map);
        map.fitBounds(polyline.getBounds(), {padding: [50, 50]});
    }
}

document.addEventListener('DOMContentLoaded', () => {
    initMap();

    const form = document.getElementById('traceroute-form');
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const target = document.getElementById('target').value;
            const loading = document.getElementById('loading');
            const errorDiv = document.getElementById('error');
            const resultContainer = document.getElementById('result-container');
            const submitBtn = document.getElementById('submit-btn');

            loading.classList.remove('hidden');
            resultContainer.classList.add('hidden');
            errorDiv.classList.add('hidden');
            submitBtn.disabled = true;

            try {
                const response = await fetch('/api/traceroute', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({target})
                });
                
                const data = await response.json();
                
                if (!response.ok) {
                    throw new Error(data.detail || 'Traceroute failed');
                }

                document.getElementById('res-target').textContent = data.target;
                document.getElementById('res-ip').textContent = data.ip_address;

                const tbody = document.querySelector('#hops-table tbody');
                tbody.innerHTML = '';
                
                data.hops.forEach(hop => {
                    const tr = document.createElement('tr');
                    const loc = hop.country && hop.country !== '-' ? `${hop.country}, ${hop.city}` : '-';
                    tr.innerHTML = `
                        <td>${hop.hop_number}</td>
                        <td>${hop.ip || '-'}</td>
                        <td>${hop.hostname || '-'}</td>
                        <td>${hop.delay === null ? '*' : hop.delay}</td>
                        <td>${loc}</td>
                    `;
                    tbody.appendChild(tr);
                });

                renderMap(data.hops);
                setTimeout(() => map.invalidateSize(), 100);
                resultContainer.classList.remove('hidden');
            } catch (err) {
                errorDiv.textContent = err.message;
                errorDiv.classList.remove('hidden');
            } finally {
                loading.classList.add('hidden');
                submitBtn.disabled = false;
            }
        });
    }

    // Modal close
    const modal = document.getElementById('history-detail-modal');
    if (modal) {
        modal.querySelector('.close-btn').addEventListener('click', () => {
            modal.classList.add('hidden');
        });
        window.addEventListener('click', (e) => {
            if (e.target === modal) modal.classList.add('hidden');
        });
    }
});

async function loadHistory() {
    try {
        const response = await fetch('/api/history');
        const data = await response.json();
        const tbody = document.querySelector('#history-table tbody');
        
        data.forEach(item => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${item.id}</td>
                <td>${item.target}</td>
                <td>${item.ip_address}</td>
                <td>${new Date(item.created_at).toLocaleString()}</td>
                <td>${item.hops.length}</td>
                <td><button class="btn" onclick="openHistoryDetail(${item.id})">View</button></td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        console.error(e);
    }
}

async function openHistoryDetail(id) {
    try {
        const response = await fetch(`/api/history/${id}`);
        const data = await response.json();
        
        const tbody = document.querySelector('#detail-table tbody');
        tbody.innerHTML = '';
        
        data.hops.forEach(hop => {
            const tr = document.createElement('tr');
            const loc = hop.country && hop.country !== '-' ? `${hop.country}, ${hop.city}` : '-';
            tr.innerHTML = `
                <td>${hop.hop_number}</td>
                <td>${hop.ip || '-'}</td>
                <td>${hop.hostname || '-'}</td>
                <td>${hop.delay === null ? '*' : hop.delay}</td>
                <td>${loc}</td>
            `;
            tbody.appendChild(tr);
        });
        
        document.getElementById('history-detail-modal').classList.remove('hidden');
    } catch(e) {
        console.error(e);
    }
}

async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        
        const container = document.getElementById('stats-container');
        container.innerHTML = `
            <div class="stat-card">
                <h3>${data.total_traces}</h3>
                <p>Total Traces</p>
            </div>
            <div class="stat-card">
                <h3>${data.avg_hops}</h3>
                <p>Average Hops</p>
            </div>
            <div class="stat-card">
                <h3>${data.requests_last_24h}</h3>
                <p>Requests (24h)</p>
            </div>
        `;
        
        const popList = document.getElementById('popular-targets');
        data.popular_targets.forEach(t => {
            const li = document.createElement('li');
            li.innerHTML = `<span>${t.target}</span> <span>${t.count} requests</span>`;
            popList.appendChild(li);
        });
    } catch(e) {
        console.error(e);
    }
}