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
                document.getElementById('t_axis0').innerText = data.axes.axis0 || '00000';
                document.getElementById('t_axis1').innerText = data.axes.axis1 || '00000';
                document.getElementById('t_axis2').innerText = data.axes.axis2 || '00000';
                document.getElementById('t_axis3').innerText = data.axes.axis3 || '00000';
                document.getElementById('t_axis4').innerText = data.axes.axis4 || '00000';
                document.getElementById('t_axis5').innerText = data.axes.axis5 || '00000';
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

setInterval(updateData, 100);
