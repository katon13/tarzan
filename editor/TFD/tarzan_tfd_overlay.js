let lastPacketId = -1;
const elCache = {};

/**
 * Szybki dostęp do elementów DOM z cache'owaniem referencji.
 */
function getEl(id) {
    if (!elCache[id]) elCache[id] = document.getElementById(id);
    return elCache[id];
}

/**
 * Aktualizacja interfejsu - dotyczy tylko danych liczbowych i CLAP.
 * Statyczne elementy (tytuły, status, opisy) nie są dotykane w tym strumieniu.
 */
function updateUI(data) {
    if (!data || data.packet_id === lastPacketId) return;
    lastPacketId = data.packet_id;

    // 1. Status i Numer Ujęcia (Take)
    if (getEl('t_status')) getEl('t_status').innerText = data.status || 'LIVE';
    if (getEl('t_take')) getEl('t_take').innerText = data.take || '001';

    // 2. Czas Główny / TC
    if (getEl('t0')) getEl('t0').innerText = data.t0 || data.tc || '00:00:00:000';

    // 3. Osie (t_axis0 do t_axis5)
    if (data.axes) {
        for (let i = 0; i < 6; i++) {
            const el = getEl('t_axis' + i);
            if (el) {
                const ax = data.axes['axis' + i];
                // Obsługa formatu obiektowego (z .pos) lub prostego ciągu znaków
                el.innerText = (typeof ax === 'object') ? (ax.pos || '00000') : (ax || '00000');
            }
        }
    }

    // 4. Czujniki
    if (data.sensors) {
        if (getEl('t_laser')) getEl('t_laser').innerText = data.sensors.laser || 'OFF';
        if (getEl('t_limits')) getEl('t_limits').innerText = data.sensors.limits || 'OK';
        if (getEl('t_shock')) getEl('t_shock').innerText = data.sensors.shock || 'OK';
        if (getEl('t_light')) getEl('t_light').innerText = data.sensors.light || '00000';
        if (getEl('t_temp')) getEl('t_temp').innerText = (data.sensors.temp || '22.0') + 'C';
        if (getEl('t_xyz')) getEl('t_xyz').innerText = data.sensors.xyz || '+00 +00 +00';
    }

    // 5. Metadane Filmu (Tytuł i Reżyser)
    if (getEl('t1')) getEl('t1').innerText = data.title || 'TYTUŁ FILMU';
    if (getEl('t2')) getEl('t2').innerText = data.director || 'REŻYSER';

    // 6. Wskaźnik CLAP (Indicator)
    const clap = getEl('clap-indicator');
    if (clap) {
        if (data.clap === 1) {
            clap.classList.add('clap-on');
            clap.classList.remove('clap-off');
        } else {
            clap.classList.add('clap-off');
            clap.classList.remove('clap-on');
        }
    }
}

/**
 * Inicjalizacja strumienia danych SSE.
 */
function startStream() {
    console.log("TFD: Łączenie ze strumieniem SSE (/tfd_stream)...");
    const evtSource = new EventSource("/tfd_stream");

    evtSource.onmessage = function(event) {
        try {
            const data = JSON.parse(event.data);
            updateUI(data);
        } catch (e) {
            console.error("TFD SSE Parse Error:", e);
        }
    };

    evtSource.onerror = function() {
        console.warn("TFD: Połączenie SSE utracone. Próba wznowienia za 2s...");
        // Nie czyścimy widoku - zostają ostatnie poprawne wartości
        evtSource.close();
        setTimeout(startStream, 2000);
    };
}

// Uruchomienie po załadowaniu strony
document.addEventListener('DOMContentLoaded', startStream);
