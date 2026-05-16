let lastPacketId = -1;
let lastClapState = 0;
let clapFlashTimer = null;
const elCache = {};

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
    if (!data || data.packet_id === lastPacketId) return;
    lastPacketId = data.packet_id;

    setText('t_status', data.status, 'LIVE');
    setText('t_take', data.take, '001');
    setText('t0', data.t0 ?? data.tc, '00:00:00:000');

    if (data.axes) {
        for (let i = 0; i < 6; i++) {
            const ax = data.axes['axis' + i];
            const value = (ax && typeof ax === 'object') ? (ax.pos ?? '00000') : (ax ?? '00000');
            setText('t_axis' + i, value, '00000');
        }
    }

    if (data.sensors) {
        setText('t_laser', data.sensors.laser, 'OFF');
        setText('t_limits', data.sensors.limits, 'OK');
        setText('t_shock', data.sensors.shock, 'OK');
        setText('t_light', data.sensors.light, '00000');

        const tempVal = data.sensors.temp ?? '22C';
        const tempText = String(tempVal).toUpperCase().includes('C') ? String(tempVal) : String(tempVal) + 'C';
        setText('t_temp', tempText, '22C');

        setText('t_xyz', data.sensors.xyz, '+00 +00 +00');
    }

    setText('t1', data.title, 'TYTUŁ FILMU');
    setText('t2', data.director, 'REŻYSER');

    const clap = getEl('clap-indicator');
    const clapState = Number(data.clap || 0);

    if (clap) {
        if (clapState === 1) {
            clap.classList.add('clap-on');
            clap.classList.remove('clap-off');
        } else {
            clap.classList.add('clap-off');
            clap.classList.remove('clap-on');
        }
    }

    if (clapState === 1 && lastClapState !== 1) {
        showClapFlash();
    }
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

document.addEventListener('DOMContentLoaded', startStream);
