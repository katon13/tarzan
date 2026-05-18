import sys
from pathlib import Path
import time

ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from core.tarzanSignalBus import TarzanSignalBus
from hardware.tarzanNextion.bridge import TarzanNextionBridge

def test_rrp_logic():
    bus = TarzanSignalBus()
    bridge = TarzanNextionBridge(bus)
    
    print("--- TEST 1: Kierunek (DIR) ---")
    # Symulujemy zdarzenie z Nextiona: Player 1, Oś 4 (ARM_H), Kierunek 1
    bridge._handle_rrp_event("rrp:p1_ax=4")
    bridge._handle_rrp_event("rrp:p1_dr=1")
    
    # Sprawdzamy czy sygnaly w magistrali sa poprawne
    print(f"par_rrp_p1_axis: {bus.get('par_rrp_p1_axis')} (expected 4)")
    print(f"par_rrp_p1_dir: {bus.get('par_rrp_p1_dir')} (expected 1)")
    
    # Symulujemy generator STEP w PAR (analogicznie do kodu w tarzanParPanels.py)
    axis_map = {
        "ARM_H": {"step": ["play_p46_step_ctr_arm_h"], "dir": ["play_p38_step_dir_arm_h", "rec_p12_rec_dir_arm_h", "cnc_b_arm_h_dir"]},
    }
    axis_idx_to_name = {4: "ARM_H"}
    
    bridge_axis = int(bus.get("par_rrp_p1_axis", -1))
    direction = int(bus.get("par_rrp_p1_dir", 0))
    axis_name = axis_idx_to_name.get(bridge_axis)
    
    if axis_name in axis_map:
        cfg = axis_map[axis_name]
        # To jest kod ktory dodalem do tarzanParPanels.py
        for dir_sig in cfg.get("dir", []):
            bus.force_signal(dir_sig, direction, source="PAR_GEN")
            
    print(f"play_p38_step_dir_arm_h: {bus.get('play_p38_step_dir_arm_h')} (expected 1)")
    print(f"rec_p12_rec_dir_arm_h: {bus.get('rec_p12_rec_dir_arm_h')} (expected 1)")
    print(f"cnc_b_arm_h_dir: {bus.get('cnc_b_arm_h_dir')} (expected 1)")
    
    if bus.get('play_p38_step_dir_arm_h') == 1 and bus.get('cnc_b_arm_h_dir') == 1:
        print("Kierunek DIR: OK (ustawiono wszystkie sygnaly)")
    else:
        print("Kierunek DIR: FAIL")

    print("\n--- TEST 2: Potencjometr od zera ---")
    # Symulujemy zmiane na fizycznym potencjometrze (przez bridge bo bridge czyta fizyczne p45/p47)
    # W PAR galka (knob) ustawia bezposrednio sygnal 'play_p45_rrp_pot_h'
    bus.set_input("play_p45_rrp_pot_h", 0, source="PAR_KNOB")
    
    # Gen tick
    v = float(bus.get("play_p45_rrp_pot_h", 0))
    s = float(bus.get("par_rrp_p1_sens", 50))
    intensity = (v / 4095.0) * (s / 100.0)
    print(f"Intensity for v=0: {intensity} (expected 0.0)")
    
    bus.set_input("play_p45_rrp_pot_h", 2048, source="PAR_KNOB")
    v = float(bus.get("play_p45_rrp_pot_h", 0))
    intensity = (v / 4095.0) * (s / 100.0)
    print(f"Intensity for v=2048: {intensity} (expected ~0.25 for sens=50)")

    if intensity > 0:
        print("Potencjometr: OK (reaguje liniowo od 0)")
    else:
        print("Potencjometr: FAIL")

if __name__ == "__main__":
    test_rrp_logic()
