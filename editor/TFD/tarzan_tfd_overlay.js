let lastPacketId = -1;
let lastPacketSignature = "";
let lastClapState = 0;
let clapFlashTimer = null;
const elCache = {};

// TARZAN TFD TC MODEL v9:
// b_clap=1 -> RUN / wznowienie
// b_clap=0 -> PAUZA / zatrzymanie na ostatnim czasie
// Overlay nie synchronizuje TC co pakiet. Pakiet jest tylko START/STOP.
// Dzięki temu pakiety 00:00:00:001 albo opóźnione SSE nie cofają sekund/minut/godzin.
let localTcRunning = false;
let localTcBaseMs = 0;
let localTcBasePerf = 0;
let localTcLastText = '00:00:00:000';

function getEl(id) {
    if (!elCache[id]) elCache[id] = document.getElementById(id);
    return elCache[id];
}

function setText(id, value, fallback) {
    const el = getEl(id);
    if (!el) return;
    const nextValue = value ?? fallback;
    const text = String(nextValue);
    if (el.innerText !== text) el.innerText = text;
}

function isTrueLike(value) {
    if (value === true) return true;
    if (value === false || value === null || value === undefined) return false;
    if (typeof value === 'number') return value === 1;
    const text = String(value).trim().toLowerCase();
    return ['1', 'true', 'yes', 'on', 'run', 'start', 'tc run'].includes(text);
}

function isFalseLike(value) {
    if (value === false) return true;
    if (value === true || value === null || value === undefined) return false;
    if (typeof value === 'number') return value === 0;
    const text = String(value).trim().toLowerCase();
    return ['0', 'false', 'no', 'off', 'stop', 'tc stop'].includes(text);
}

function isTcText(value) {
    return /^\d{1,2}:\d{2}:\d{2}:\d{1,4}$/.test(String(value ?? '').trim());
}

function parseTcToMs(value) {
    const text = String(value ?? '').trim();
    const match = text.match(/^(\d{1,2}):(\d{2}):(\d{2}):(\d{1,4})$/);
    if (!match) return null;

    const h = Number(match[1]) || 0;
    const m = Number(match[2]) || 0;
    const s = Number(match[3]) || 0;
    let msText = match[4];

    // TC w TARZAN ma ostatni człon jako milisekundy. Nie dopisujemy zer z prawej
    // dla wartości 1/10/100, bo to robiło błędną interpretację krótkich pól.
    if (msText.length > 3) msText = msText.slice(0, 3);
    const ms = Number(msText.padStart(3, '0')) || 0;
    return (((h * 60 + m) * 60 + s) * 1000) + ms;
}

function formatMsToTc(totalMs) {
    let ms = Math.max(0, Math.floor(Number(totalMs) || 0));
    const h = Math.floor(ms / 3600000);
    ms %= 3600000;
    const m = Math.floor(ms / 60000);
    ms %= 60000;
    const s = Math.floor(ms / 1000);
    const milli = ms % 1000;
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}:${String(milli).padStart(3, '0')}`;
}

function currentLocalTcMs() {
    if (!localTcRunning) return localTcBaseMs;
    return localTcBaseMs + Math.max(0, performance.now() - localTcBasePerf);
}

function paintLocalTc() {
    const text = formatMsToTc(currentLocalTcMs());
    localTcLastText = text;
    setText('t0', text, '00:00:00:000');
}

function pickPacketTcMs(data) {
    const candidates = [data?.t0, data?.tc, data?.take_timecode, data?.par_take_timecode, data?.take_tc, data?.tfd_tc];
    for (const candidate of candidates) {
        if (!isTcText(candidate)) continue;
        const ms = parseTcToMs(candidate);
        if (ms !== null) return ms;
    }
    return null;
}

function packetRunState(data) {
    const eventType = String(data?.last_event?.type ?? '').toUpperCase();
    if (['CLAP_START', 'TC_START'].includes(eventType)) return true;
    if (['CLAP_STOP', 'TC_STOP'].includes(eventType)) return false;

    if (data?.tc_running !== undefined) return isTrueLike(data.tc_running);
    if (data?.take_tc_running !== undefined) return isTrueLike(data.take_tc_running);

    // clap jest stanem b_clap; 1 = run, 0 = pause.
    if (data?.clap !== undefined) return isTrueLike(data.clap);

    return localTcRunning;
}

function syncLocalTcFromPacket(data) {
    const packetRunning = packetRunState(data);
    const packetMsRaw = pickPacketTcMs(data);
    const nowMs = currentLocalTcMs();

    if (packetRunning) {
        if (!localTcRunning) {
            // START / WZNOWIENIE:
            // Nie zeruj, jeśli overlay ma już większy zatrzymany czas.
            // Pakiet 000/001 przy starcie traktujemy jako artefakt techniczny.
            let startMs = localTcBaseMs;
            if (packetMsRaw !== null && packetMsRaw > 5) {
                startMs = Math.max(localTcBaseMs, packetMsRaw);
            }
            localTcBaseMs = startMs;
            localTcBasePerf = performance.now();
            localTcRunning = true;
        }
        paintLocalTc();
        return;
    }

    if (localTcRunning) {
        // STOP / PAUZA: zatrzymaj na aktualnym lokalnym czasie.
        // Jeżeli pakiet niesie większy prawidłowy czas, użyj większego.
        let stopMs = nowMs;
        if (packetMsRaw !== null && packetMsRaw > 5) {
            stopMs = Math.max(stopMs, packetMsRaw);
        }
        localTcBaseMs = stopMs;
        localTcBasePerf = performance.now();
        localTcRunning = false;
        paintLocalTc();
        return;
    }

    // Już stoi: nie wolno cofać do 000/001 ani nadpisywać większego czasu.
    if (packetMsRaw !== null && packetMsRaw > 5 && packetMsRaw > localTcBaseMs) {
        localTcBaseMs = packetMsRaw;
        localTcBasePerf = performance.now();
        paintLocalTc();
    } else {
        paintLocalTc();
    }
}

function showClapFlash() {
    const flash = getEl('clap-flash');
    if (!flash) return;

    flash.classList.add('clap-flash-on');

    if (clapFlashTimer) clearTimeout(clapFlashTimer);
    clapFlashTimer = setTimeout(() => {
        flash.classList.remove('clap-flash-on');
        clapFlashTimer = null;
    }, 1000);
}

function updateUI(data) {
    if (!data) return;

    const signature = [data.packet_id, data.t0, data.tc, data.tc_running, data.take_tc_running, data.clap, data.last_event?.type].join('|');
    if (signature === lastPacketSignature && data.packet_id === lastPacketId) return;
    lastPacketSignature = signature;
    lastPacketId = data.packet_id;

    setText('t_status', data.status, 'LIVE');
    setText('t_take', data.take, '001');
    syncLocalTcFromPacket(data);

    if (data.axes) {
        for (let i = 0; i < 6; i++) {
            const ax = data.axes['axis' + i];
            let value = (ax && typeof ax === 'object') ? (ax.pos ?? '00000') : (ax ?? '00000');
            value = String(value).replace(/^[+-]/, '');
            setText('t_axis' + i, value, '00000');

            const axisText = getEl('t_axis' + i);
            if (axisText && ax && typeof ax === 'object') {
                axisText.classList.remove('dir-positive', 'dir-negative');
                axisText.classList.add(Number(ax.dir || 0) === 1 ? 'dir-positive' : 'dir-negative');
            }

            const iconEl = document.getElementById('t_axis' + i)?.previousElementSibling;
            if (iconEl && iconEl.tagName === 'IMG') {
                if (ax && ax.moving) iconEl.classList.add('axis-active');
                else iconEl.classList.remove('axis-active');
            }
        }
    }

    if (data.sensors) {
        setText('t_laser', data.sensors.laser, 'OFF');
        setText('t_limits', data.sensors.limits, 'OK');
        setText('t_shock', data.sensors.shock, 'OK');
        setText('t_light', data.sensors.light, '00000');

        const sensorIcons = {
            't_laser': data.sensors.laser !== 'OFF' && data.sensors.laser !== '0',
            't_limits': data.sensors.limits !== 'OK',
            't_shock': data.sensors.shock !== 'OK' && data.sensors.shock !== 'OFF' && data.sensors.shock !== '0',
        };

        for (const [id, active] of Object.entries(sensorIcons)) {
            const iconEl = document.getElementById(id)?.previousElementSibling;
            if (iconEl && iconEl.tagName === 'IMG') {
                if (active) iconEl.classList.add('sensor-active');
                else iconEl.classList.remove('sensor-active');
            }
        }

        const tempVal = data.sensors.temp ?? '22C';
        const tempText = String(tempVal).toUpperCase().includes('C') ? String(tempVal) : String(tempVal) + 'C';
        setText('t_temp', tempText, '22C');
        setText('t_xyz', data.sensors.xyz, '+00 +00 +00');
    }

    setText('t1', data.title, 'TYTUŁ FILMU');
    setText('t2', data.director, 'REŻYSER');

    const takeIcon = document.querySelector('.take-icon');
    const clapState = packetRunState(data) ? 1 : 0;
    if (takeIcon) {
        if (clapState === 1) takeIcon.src = "/img/take/take_open_128.png";
        else takeIcon.src = "/img/take/take_closed_128.png";
    }

    const clap = getEl('clap-indicator');
    if (clap) {
        if (clapState === 1) {
            clap.classList.add('clap-on');
            clap.classList.remove('clap-off');
        } else {
            clap.classList.add('clap-off');
            clap.classList.remove('clap-on');
        }
    }

    if (clapState === 1 && lastClapState !== 1) showClapFlash();
    lastClapState = clapState;
}

function startStream() {
    const evtSource = new EventSource('/tfd_stream');

    evtSource.onmessage = function(event) {
        try {
            updateUI(JSON.parse(event.data));
        } catch (e) {
            console.error('TFD SSE Parse Error:', e);
        }
    };

    evtSource.onerror = function() {
        evtSource.close();
        setTimeout(startStream, 2000);
    };
}

function pollTfdDataFallback() {
    fetch('/tfd_data', { cache: 'no-store' })
        .then(response => response.ok ? response.json() : null)
        .then(data => { if (data) updateUI(data); })
        .catch(() => {});
}

document.addEventListener('DOMContentLoaded', () => {
    startStream();
    setInterval(() => {
        if (localTcRunning) paintLocalTc();
    }, 33);
    setInterval(pollTfdDataFallback, 250);
});
