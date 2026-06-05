import time
import sys
import os
from pathlib import Path

# Add root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.tarzanSignalBus import get_signal_bus
from core.tarzanHardwareBridge import TarzanHardwareBridge

def test_axis_cam_h():
    # Używamy trybu TEST dla szyny, ale bridge będzie działał jako LIVE_ADAPTER
    bus = get_signal_bus("TEST")
    bridge = TarzanHardwareBridge(bus)
    
    print("=== AXIS TEST (DRY RUN) ===")
    
    # 1. Start bridge (może zgłosić brak PoKeys, ale logika powinna działać)
    bridge.start()
    bus.set_mode("LIVE")
    
    # 2. Lock check
    print(f"Initial safety_axis_unlock: {bridge.safety_axis_unlock} (Expected: False)")
    
    # 3. Enable axis
    print("Enabling axis_cam_h...")
    bus.write_output("axis_cam_h_en", 1)
    
    # 4. Set direction
    print("Setting direction forward...")
    bus.write_output("axis_cam_h_dir", 1)
    
    # 5. Unlock axes
    print("Unlocking axes via cmd_unlock_axes...")
    bus.write_output("cmd_unlock_axes", 1)
    # Mostek reaguje asynchronicznie na subskrypcję, ale tutaj wywołujemy _on_signal_change bezpośrednio dla pewności w teście
    bridge._on_signal_change("cmd_unlock_axes", 1)
    
    print(f"Safety status in bridge: {bridge.safety_axis_unlock} (Expected: True)")
    print(f"Safety status in bus: {bus.read('safety_axis_unlock')} (Expected: 1)")
    
    # 6. Generate step pulse
    print("Generating STEP pulse (1 -> 0)...")
    bus.write_output("axis_cam_h_step", 1)
    bus.write_output("axis_cam_h_step", 0)
    
    # 7. Check position
    pos = bridge._abs_positions.get("axis_cam_h", 0)
    print(f"Axis internal position in bridge: {pos} (Expected: 1)")
    
    # 8. Test direction reverse
    print("Setting direction backward...")
    bus.write_output("axis_cam_h_dir", 0)
    bus.write_output("axis_cam_h_step", 1)
    bus.write_output("axis_cam_h_step", 0)
    pos = bridge._abs_positions.get("axis_cam_h", 0)
    print(f"Axis internal position in bridge: {pos} (Expected: 0)")
    
    # 9. Lock back
    print("Locking axes...")
    bus.write_output("cmd_unlock_axes", 0)
    bridge._on_signal_change("cmd_unlock_axes", 0)
    print(f"Safety status in bridge: {bridge.safety_axis_unlock} (Expected: False)")
    
    bridge.stop()
    print("=== TEST FINISHED ===")

if __name__ == "__main__":
    test_axis_cam_h()
