(() => {
    // ── State ──
    let hospitals = [];
    let leafletMap = null;
    let drawnItems = null;
    let pendingMeasure = null;
    let currentIdx = null;

    // ── DOM ──
    const cityInput      = document.getElementById('cityInput');
    const searchBtn      = document.getElementById('searchBtn');
    const searchBtnLabel = document.getElementById('searchBtnLabel');
    const searchStatus   = document.getElementById('searchStatus');
    const statsBar       = document.getElementById('statsBar');
    const resultsSection = document.getElementById('resultsSection');
    const hospitalsBody  = document.getElementById('hospitalsBody');
    const tableTitle     = document.getElementById('tableTitle');
    const statTotal      = document.getElementById('statTotal');
    const statContacts   = document.getElementById('statContacts');
    const statMeasured   = document.getElementById('statMeasured');
    const exportBtn      = document.getElementById('exportBtn');
    const mapModal       = document.getElementById('mapModal');
    const modalTitle     = document.getElementById('modalTitle');
    const closeModalBtn  = document.getElementById('closeModalBtn');
    const measLength     = document.getElementById('measLength');
    const measBreadth    = document.getElementById('measBreadth');
    const measArea       = document.getElementById('measArea');
    const clearDrawBtn   = document.getElementById('clearDrawBtn');
    const saveMeasureBtn = document.getElementById('saveMeasureBtn');

    // ── Geocode city via Nominatim ──
    async function geocodeCity(city) {
        const url = `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(city)}&format=json&limit=1&addressdetails=0`;
        const res = await fetch(url, { headers: { 'Accept-Language': 'en-US,en' } });
        if (!res.ok) throw new Error('Geocoding service unavailable');
        const data = await res.json();
        if (!data.length) throw new Error(`City "${city}" not found. Try a different spelling.`);
        const { boundingbox, lat, lon, display_name } = data[0];
        return {
            bbox: {
                south: parseFloat(boundingbox[0]),
                north: parseFloat(boundingbox[1]),
                west:  parseFloat(boundingbox[2]),
                east:  parseFloat(boundingbox[3]),
            },
            center: { lat: parseFloat(lat), lon: parseFloat(lon) },
            label: display_name.split(',').slice(0, 2).join(',').trim(),
        };
    }

    // ── Search hospitals via Overpass ──
    async function fetchHospitals(bbox) {
        const { south, west, north, east } = bbox;
        const query = `[out:json][timeout:40];
(
  node["amenity"="hospital"](${south},${west},${north},${east});
  way["amenity"="hospital"](${south},${west},${north},${east});
  relation["amenity"="hospital"](${south},${west},${north},${east});
);
out center tags;`;
        const res = await fetch('https://overpass-api.de/api/interpreter', {
            method: 'POST',
            body: query,
        });
        if (!res.ok) throw new Error('Hospital data service unavailable. Try again.');
        const data = await res.json();
        return data.elements || [];
    }

    // ── Parse OSM element → hospital object ──
    function parseElement(el, idx) {
        const t = el.tags || {};
        const lat = el.lat ?? el.center?.lat ?? null;
        const lon = el.lon ?? el.center?.lon ?? null;

        const name = t.name || t['name:en'] || 'Unnamed Hospital';

        const addrParts = [
            t['addr:housenumber'],
            t['addr:street'],
            t['addr:suburb'],
            t['addr:city'],
        ].filter(Boolean);
        const address = addrParts.length ? addrParts.join(', ') : (t['addr:full'] || t['addr:place'] || '');

        const phone   = t.phone || t['contact:phone'] || t.telephone || '';
        const email   = t.email || t['contact:email'] || '';
        const website = t.website || t['contact:website'] || t.url || '';

        return { idx, name, address, phone, email, website, lat, lon, length: null, breadth: null, area: null };
    }

    // ── Render table ──
    function renderTable() {
        hospitalsBody.innerHTML = hospitals.map((h, i) => {
            const hasMeas = h.area != null;
            const webCell = h.website
                ? `<a href="${esc(h.website)}" target="_blank" rel="noopener" class="web-link">Visit &#x2197;</a>`
                : '<span style="color:var(--text-muted)">—</span>';
            const mapsUrl = h.lat && h.lon
                ? `https://www.google.com/maps/@${h.lat},${h.lon},80m/data=!3m1!1e3`
                : null;

            return `<tr id="row-${i}" class="${hasMeas ? 'measured' : ''}">
                <td class="col-num">${i + 1}</td>
                <td class="col-name" title="${esc(h.name)}">${esc(h.name)}</td>
                <td class="col-addr" title="${esc(h.address)}">${esc(h.address) || '<span style="color:var(--text-muted)">—</span>'}</td>
                <td><input class="cell-input" type="tel" data-field="phone" data-idx="${i}" value="${esc(h.phone)}" placeholder="Add phone" /></td>
                <td><input class="cell-input" type="email" data-field="email" data-idx="${i}" value="${esc(h.email)}" placeholder="Add email" /></td>
                <td>${webCell}</td>
                <td class="col-meas${hasMeas ? ' measured-val' : ''}" id="len-${i}">${hasMeas ? h.length.toFixed(1) : '—'}</td>
                <td class="col-meas${hasMeas ? ' measured-val' : ''}" id="bre-${i}">${hasMeas ? h.breadth.toFixed(1) : '—'}</td>
                <td class="col-meas${hasMeas ? ' measured-val' : ''}" id="area-${i}">${hasMeas ? h.area.toFixed(0) : '—'}</td>
                <td class="col-actions">
                    <button class="btn-measure ${hasMeas ? 'done' : ''}" onclick="window._openMeasure(${i})">
                        ${hasMeas ? 'Re-measure' : 'Measure Roof'}
                    </button>
                    ${mapsUrl ? `<a href="${mapsUrl}" target="_blank" rel="noopener" class="btn-gmaps" title="Open in Google Maps Satellite">Maps</a>` : ''}
                </td>
            </tr>`;
        }).join('');

        // Bind inline input changes to state
        hospitalsBody.querySelectorAll('.cell-input').forEach(input => {
            input.addEventListener('change', e => {
                hospitals[+e.target.dataset.idx][e.target.dataset.field] = e.target.value;
                updateStats();
            });
        });
    }

    function updateStats() {
        statTotal.textContent    = hospitals.length;
        statContacts.textContent = hospitals.filter(h => h.phone || h.email).length;
        statMeasured.textContent = hospitals.filter(h => h.area != null).length;
    }

    function esc(str) {
        const d = document.createElement('div');
        d.textContent = str || '';
        return d.innerHTML;
    }

    function setStatus(msg, type) {
        searchStatus.textContent = msg;
        searchStatus.className = `status-msg status-${type}`;
    }

    // ── Search flow ──
    searchBtn.addEventListener('click', runSearch);
    cityInput.addEventListener('keydown', e => { if (e.key === 'Enter') runSearch(); });

    async function runSearch() {
        const city = cityInput.value.trim();
        if (!city) { setStatus('Please enter a city name.', 'error'); return; }

        searchBtn.disabled = true;
        searchBtnLabel.innerHTML = '<span class="spinner"></span> Searching...';
        setStatus('Geocoding city…', 'loading');

        try {
            const cityData = await geocodeCity(city);
            setStatus(`Located: ${cityData.label}. Fetching hospitals…`, 'loading');

            const elements = await fetchHospitals(cityData.bbox);
            const parsed = elements
                .filter(el => el.tags?.name && (el.lat || el.center?.lat))
                .map((el, i) => parseElement(el, i));

            if (parsed.length === 0) {
                setStatus('No named hospitals found. Try a larger city or check spelling.', 'error');
                return;
            }

            hospitals = parsed;
            tableTitle.textContent = `Hospitals in ${cityData.label} (${hospitals.length})`;
            renderTable();
            updateStats();
            statsBar.classList.remove('hidden');
            resultsSection.classList.remove('hidden');
            setStatus(`Found ${hospitals.length} hospital(s) in ${cityData.label}`, 'success');
            statsBar.scrollIntoView({ behavior: 'smooth', block: 'start' });

        } catch (err) {
            setStatus(`Error: ${err.message}`, 'error');
        } finally {
            searchBtn.disabled = false;
            searchBtnLabel.textContent = 'Search Hospitals';
        }
    }

    // ── Map measure modal ──
    window._openMeasure = function (idx) {
        currentIdx = idx;
        const h = hospitals[idx];
        if (!h.lat || !h.lon) {
            alert('No coordinates available for this hospital. Cannot open map.');
            return;
        }

        modalTitle.textContent = h.name;
        pendingMeasure = null;
        resetMeasureDisplay();
        mapModal.classList.remove('hidden');

        // Destroy previous map instance
        if (leafletMap) { leafletMap.remove(); leafletMap = null; }

        // Wait for modal to paint, then init map
        requestAnimationFrame(() => requestAnimationFrame(() => initLeafletMap(h.lat, h.lon)));
    };

    function initLeafletMap(lat, lon) {
        leafletMap = L.map('mapContainer', { zoomControl: true }).setView([lat, lon], 19);

        // Satellite layer (Esri World Imagery – no API key required)
        L.tileLayer(
            'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            { attribution: 'Imagery &copy; Esri', maxZoom: 21 }
        ).addTo(leafletMap);

        // Labels overlay
        L.tileLayer(
            'https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',
            { attribution: '', maxZoom: 21, opacity: 0.7 }
        ).addTo(leafletMap);

        // Draw layer
        drawnItems = new L.FeatureGroup();
        leafletMap.addLayer(drawnItems);

        const drawControl = new L.Control.Draw({
            draw: {
                rectangle: { shapeOptions: { color: '#f59e0b', weight: 2.5, fillOpacity: 0.15 } },
                polygon: false, polyline: false, circle: false, circlemarker: false, marker: false,
            },
            edit: { featureGroup: drawnItems },
        });
        leafletMap.addControl(drawControl);

        leafletMap.on(L.Draw.Event.CREATED, e => {
            drawnItems.clearLayers();
            drawnItems.addLayer(e.layer);
            applyMeasurement(e.layer);
        });

        leafletMap.on(L.Draw.Event.EDITED, e => {
            e.layers.eachLayer(layer => applyMeasurement(layer));
        });

        leafletMap.on(L.Draw.Event.DELETED, () => resetMeasureDisplay());
    }

    function applyMeasurement(layer) {
        const bounds = layer.getBounds();
        const ne = bounds.getNorthEast();
        const nw = bounds.getNorthWest();
        const sw = bounds.getSouthWest();

        const w = ne.distanceTo(nw);   // width in metres
        const h2 = nw.distanceTo(sw);  // height in metres

        const length  = Math.max(w, h2);
        const breadth = Math.min(w, h2);
        const area    = w * h2;

        measLength.textContent  = length.toFixed(1);
        measBreadth.textContent = breadth.toFixed(1);
        measArea.textContent    = area.toFixed(0);
        pendingMeasure = { length, breadth, area };
    }

    function resetMeasureDisplay() {
        measLength.textContent  = '—';
        measBreadth.textContent = '—';
        measArea.textContent    = '—';
        pendingMeasure = null;
    }

    clearDrawBtn.addEventListener('click', () => {
        if (drawnItems) drawnItems.clearLayers();
        resetMeasureDisplay();
    });

    saveMeasureBtn.addEventListener('click', () => {
        if (!pendingMeasure) {
            alert('Draw a rectangle on the rooftop first, then save.');
            return;
        }
        const { length, breadth, area } = pendingMeasure;
        hospitals[currentIdx].length  = length;
        hospitals[currentIdx].breadth = breadth;
        hospitals[currentIdx].area    = area;

        // Update row in table
        const row = document.getElementById(`row-${currentIdx}`);
        if (row) {
            row.classList.add('measured');
            document.getElementById(`len-${currentIdx}`).textContent  = length.toFixed(1);
            document.getElementById(`len-${currentIdx}`).className    = 'col-meas measured-val';
            document.getElementById(`bre-${currentIdx}`).textContent  = breadth.toFixed(1);
            document.getElementById(`bre-${currentIdx}`).className    = 'col-meas measured-val';
            document.getElementById(`area-${currentIdx}`).textContent = area.toFixed(0);
            document.getElementById(`area-${currentIdx}`).className   = 'col-meas measured-val';
            const btn = row.querySelector('.btn-measure');
            if (btn) { btn.textContent = 'Re-measure'; btn.classList.add('done'); }
        }

        updateStats();
        closeMap();
    });

    function closeMap() {
        mapModal.classList.add('hidden');
        if (leafletMap) { leafletMap.remove(); leafletMap = null; }
    }

    closeModalBtn.addEventListener('click', closeMap);
    document.querySelector('.modal-backdrop').addEventListener('click', closeMap);
    document.addEventListener('keydown', e => { if (e.key === 'Escape') closeMap(); });

    // ── Excel Export ──
    exportBtn.addEventListener('click', () => {
        if (!hospitals.length) return;
        const city = cityInput.value.trim() || 'city';

        const rows = hospitals.map((h, i) => ({
            '#':               i + 1,
            'Hospital Name':   h.name,
            'Address':         h.address || '',
            'Phone':           h.phone   || '',
            'Email':           h.email   || '',
            'Website':         h.website || '',
            'Roof Length (m)': h.length  != null ? +h.length.toFixed(2)  : '',
            'Roof Breadth (m)':h.breadth != null ? +h.breadth.toFixed(2) : '',
            'Roof Area (m²)':  h.area    != null ? +h.area.toFixed(2)    : '',
        }));

        const ws = XLSX.utils.json_to_sheet(rows);
        ws['!cols'] = [
            { wch: 4 }, { wch: 38 }, { wch: 32 }, { wch: 18 },
            { wch: 30 }, { wch: 32 }, { wch: 14 }, { wch: 14 }, { wch: 14 },
        ];

        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, 'Hospital Leads');

        const slug = city.toLowerCase().replace(/\s+/g, '-');
        XLSX.writeFile(wb, `solar-outreach-${slug}.xlsx`);
    });
})();
