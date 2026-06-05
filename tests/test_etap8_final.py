import time
import threading
import json
import os
from typing import Dict, Any, Optional

from core.tarzanSignalBus import get_signal_bus
from core.TSP.tarzanTspServer import TarzanTspServer
from editor.PAR.tarzanParBridge import TarzanParBridge
from core.TSP.tarzanTspConfig import TSP_BIND_HOST, TSP_PORT

def run_server():
    print('[SERVER] Starting TSP Server for test...')
    server = TarzanTspServer(host='127.0.0.1', port=7777, enable_lks=True, lks_n5_dry_run=True)
    server.start()
    return server

def test_etap8_logic():
    bus_server = get_signal_bus('TEST')
    bus_server.set_input('tarzan_ready', 1, source='TEST_INIT')
    
    server = run_server()
    time.sleep(1)
    
    print('[CLIENT] Creating TarzanParBridge...')
    bridge = TarzanParBridge(bus=get_signal_bus('TEST_CLIENT'))
    
    print('[CLIENT] Switching to LIVE mode...')
    bridge.set_mode('LIVE')
    
    max_wait = 50
    connected = False
    for _ in range(max_wait):
        if bridge.tsp_client and bridge.tsp_client.is_connected:
            connected = True
            break
        time.sleep(0.1)
    
    if not connected:
        print('[FAIL] Client failed to connect to local TSP server.')
        server.stop()
        return

    print('[SUCCESS] Client connected and handshake completed.')
    time.sleep(0.5)
    
    par_state = bus_server.read('par_state')
    print(f'[STATUS] par_state on server: {par_state}')
    
    print('[ACTION] Requesting Diagnostics...')
    bridge.call_action('run_diagnostics')
    
    diag_requested = False
    for _ in range(30):
        if bus_server.read('cmd_run_diagnostics') == 1:
            diag_requested = True
            break
        time.sleep(0.1)
    
    if diag_requested:
        print('[SUCCESS] cmd_run_diagnostics was set on server.')
    else:
        print('[FAIL] cmd_run_diagnostics NOT set on server.')

    print('[CLIENT] Requesting Take Control (SET_OWNER)...')
    bridge.call_action('set_owner', {'owner': 'PAR_LIVE_TEST'})
    
    owner_changed = False
    for _ in range(30):
        if bus_server.read('control_owner') == 'PAR_LIVE_TEST':
            owner_changed = True
            break
        time.sleep(0.1)
        
    if owner_changed:
        print('[SUCCESS] control_owner changed on server.')
    else:
        print(f'[FAIL] control_owner is {bus_server.read("control_owner")}')

    print('[CLIENT] Sending EHR START command...')
    bridge.write_output('cmd_ehr_start', 1)
    
    ehr_cmd_received = False
    for _ in range(30):
        if bus_server.read('cmd_ehr_start') == 1:
            ehr_cmd_received = True
            break
        time.sleep(0.1)
        
    if ehr_cmd_received:
        print('[SUCCESS] cmd_ehr_start received on server.')
    else:
        print('[FAIL] cmd_ehr_start NOT received on server.')

    print('[CLEANUP] Stopping client and server...')
    bridge.set_mode('TEST')
    server.stop()
    print('[FINISHED] Stage 8 logical test completed.')

if __name__ == '__main__':
    test_etap8_logic()

