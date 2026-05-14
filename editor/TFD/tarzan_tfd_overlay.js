function updateData() {
    fetch('/tfd_data')
        .then(response => response.json())
        .then(data => {
            // Top Panel
            document.getElementById('t_tc').innerText = data.tc || '00:00:00:00';
            document.getElementById('t_status').innerText = data.status || 'LIVE';
            document.getElementById('t_take').innerText = (data.take || 0).toString().padStart(3, '0');
            document.getElementById('t0').innerText = data.t0 || data.tc || '00:00:00:00';

            // Axes
            if (data.axes) {
                for (let i = 0; i < 6; i++) {
                    const key = 'axis' + i;
                    const ax = data.axes[key];
                    const val = (typeof ax === 'object') ? ax.pos : ax;
                    const el = document.getElementById('t_axis' + i);
                    if (el) {
                        el.innerText = val || '00000';
                        // Opcjonalnie można pokazać status EN/DIR
                        if (typeof ax === 'object' && !ax.en) {
                            el.style.color = '#555'; // Szary jeśli wyłączona
                        } else {
                            el.style.color = '';
                        }
                    }
                }
            }

            // Sensors
            if (data.sensors) {
                document.getElementById('t_laser').innerText = data.sensors.laser || 'OK';
                document.getElementById('t_limits').innerText = data.sensors.limits || 'OK';
                document.getElementById('t_shock').innerText = data.sensors.shock || 'OFF';
                document.getElementById('t_light').innerText = data.sensors.light || '00000';
                document.getElementById('t_temp').innerText = data.sensors.temp || '22C';
                document.getElementById('t_xyz').innerText = data.sensors.xyz || 'X+0 Y+0 Z+0';
            }

            // Bottom Panel
            document.getElementById('t1').innerText = data.title || 'TYTUŁ FILMU';
            document.getElementById('t2').innerText = (data.director ? 'reż. ' + data.director : 'REŻYSER');

            // Clap Indicator
            const clap = document.getElementById('clap-indicator');
            if (data.clap === 1) {
                clap.classList.remove('clap-off');
                clap.classList.add('clap-on');
            } else {
                clap.classList.remove('clap-on');
                clap.classList.add('clap-off');
            }
        })
        .catch(err => console.error('TFD Fetch Error:', err));
}

setInterval(updateData, 50); // 50ms = 20 FPS telemetrii
