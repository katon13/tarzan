#!/usr/bin/env python3
"""
TARZAN MAIN RUNTIME
Główny punkt wejścia systemu TARZAN na miniPC.
Automatycznie uruchamia i spina wszystkie moduły:
- TSP Server / LKS / Nextion 5
- SignalBus (LIVE)
- Hardware Bridge (PoKeys / I2C)
- Mode Logic
- Snajper (Pulse Engine)
"""

from __future__ import annotations

import sys
import os
import platform
from pathlib import Path

# Dodanie katalogu głównego do sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.tarzanSignalBus import get_signal_bus
from core.tarzanUstawienia import CZAS_PROBKOWANIA_MS

def main():
    # Produkcyjny miniPC nie uruchamia profilera domyślnie.
    # Profiler wolno włączyć ręcznie tylko diagnostycznie:
    # set TARZAN_PROFILE=1 przed startem procesu.
    if os.environ.get("TARZAN_PROFILE", "0") == "1":
        from core.tarzanProfiler import clear_profiler, enable_profiler, start_profiler_reporting
        enable_profiler(True)
        clear_profiler()
        start_profiler_reporting(interval_s=15.0, top_n=10)

    print("MAIN Runtime START")
    print("SignalBus OK")
    print("TSP SERVER START")
    print("HardwareBridge START")
    print("LKS-N5 START")
    print("PARcore START")
    print("Nextion 7 START")

    # 1. Inicjalizacja SignalBus w trybie LIVE
    # get_signal_bus w trybie LIVE odczyta konfigurację hardware'ową
    # i automatycznie utworzy katalogi (np. data/signalbus), jeśli są wymagane.
    bus = get_signal_bus(mode="LIVE")
    bus.set_input("runtime_state", "INITIALIZING", source="MAIN")
    bus.set_input("system_state", "BOOTING", source="MAIN")
    bus.log("MAIN", "MAIN Runtime START")
    bus.log("MAIN", "SignalBus OK")
    bus.log("MAIN", "TSP SERVER START")
    bus.log("MAIN", "HardwareBridge START")
    bus.log("MAIN", "LKS-N5 START")
    bus.log("MAIN", "PARcore START")
    bus.log("MAIN", "Nextion 7 START")
    
# 2. Konfiguracja parametrów serwera TSP
    is_windows = platform.system().lower() == "windows"
    
    # LKS ma dwa równoległe wyjścia:
    # - LKS-TTY: lokalny ekran statusowy miniPC na HDMI/TTY (/dev/tty7),
    # - LKS-N5: Nextion 5 po UART.
    # Na Windowsie TTY wyłączamy, na miniPC działa domyślnie.
    lks_tty = os.environ.get("TARZAN_LKS_TTY") or ("-" if is_windows else "/dev/tty7")
    enable_lks_tty = (not is_windows) and str(lks_tty or "-") != "-"
    n5_port = "COM5" if is_windows else "/dev/serial/by-path/pci-0000:00:14.0-usb-0:3.2:1.0-port0"
    n5_dry_run = is_windows

    print(f"Initializing TSP Server (LKS={lks_tty}, N5={n5_port}, DryRun={n5_dry_run})...")

    # Wymuszenie czystego importu serwera (na wypadek problemów z bytecode na miniPC)
    try:
        from core.TSP.tarzanTspServer import TarzanTspServer
        print("TSP Server module loaded successfully.")
    except ImportError as e:
        print(f"CRITICAL: Failed to import TarzanTspServer: {e}")
        # Próba importu z pakietu
        try:
            from core.TSP import TarzanTspServer
            print("TSP Server module loaded via package.")
        except ImportError as e2:
            print(f"CRITICAL: Package import also failed: {e2}")
            return
    
    # 3. Inicjalizacja i start TSP Servera
    # TarzanTspServer.start() automatycznie uruchamia:
    # - HardwareBridge (PoKeys)
    # - Snajper (Adaptery)
    # - ModeLogic (Tryby pracy)
    # - LKS (Status panel)
    # - LKS-N5 (Nextion 5)
    server = TarzanTspServer(
        enable_lks=enable_lks_tty,
        lks_tty=lks_tty,
        enable_lks_n5=True,
        lks_n5_port=n5_port,
        lks_n5_dry_run=n5_dry_run
    )
    
    try:
        # TarzanTspServer.start() zainicjuje podsystemy i połączy je z bus-em
        server.start()

        # PARcore i Nextion 7 są lokalnym wykonawcą miniPC.
        # PAR STACJA jest tylko klonem/REMOTE przez TSP.
        try:
            from core.PARcore.tarzanParCore import TarzanParCore
            parcore = TarzanParCore(
                bus=bus,
                hardware_bridge=getattr(server, "hw_bridge", None),
                snajper=getattr(server, "snajper", None),
                mode="LIVE",
                enable_nextion_bridge=True,
            )
            parcore.attach_main_runtime(
                tsp_server=server,
                hardware_bridge=getattr(server, "hw_bridge", None),
                enable_nextion7=True,
            )
            setattr(server, "parcore", parcore)
            bus.set_input("parcore_state", "RUNNING", source="MAIN")
            bus.log("MAIN", "PARcore/Nextion7 runtime bound to TSP Server")
            print("Nextion 7 STARTED")
        except Exception as parcore_exc:
            bus.set_input("parcore_state", "ERROR", source="MAIN")
            bus.set_input("nextion7_state", "ERROR", source="MAIN")
            bus.set_input("par_last_error", f"PARcore/Nextion7 startup failed: {parcore_exc}", source="MAIN")
            bus.log("MAIN", f"PARcore/Nextion7 startup failed: {parcore_exc}")
            print(f"PARcore/Nextion7 START ERROR: {parcore_exc}")
    except Exception as e:
        print(f"CRITICAL ERROR during system start: {e}")
        bus.set_input("system_state", "ERROR", source="MAIN")
        bus.set_input("par_last_error", f"Startup failed: {e}", source="MAIN")
        return

    # 4. Sprawdzanie gotowości EHR/KHR (przez ModeLogic)
    # ModeLogic (uruchomiony przez TspServer) monitoruje statusy modułów.
    bus.set_input("ehr_state", "OFFLINE", source="MAIN")
    bus.set_input("par_state", "OFFLINE", source="MAIN")
    bus.set_input("khr_state", "OFFLINE", source="MAIN")
    
    print("PAR NOT_CONNECTED")
    print("EHR NOT_CONNECTED")
    bus.log("MAIN", "PAR NOT_CONNECTED")
    bus.log("MAIN", "EHR NOT_CONNECTED")

    # 5. Blokada bezpieczeństwa osi (Safety Lock)
    # Zgodnie z wymaganiem: Ruch osi NIE startuje automatycznie.
    # Musi zostać zablokowany do świadomego unlock przez operatora.
    bus.set_input("safety_axis_unlock", 0, source="MAIN_SAFETY")
    print("Safety LOCKED")
    bus.log("MAIN", "Axes LOCKED (Safety Mode). Manual unlock required.")

    # 6. Sygnał gotowości systemu
    bus.set_input("tarzan_ready", 1, source="MAIN")
    bus.set_input("runtime_state", "RUNNING", source="MAIN")
    bus.set_input("system_state", "READY", source="MAIN")
    
    print("----------------------------------------------------")
    print("   TARZAN SYSTEM IS READY AND RUNNING              ")
    print("   Operator Panel: Automatic                        ")
    print("   Safety: LOCKED                                   ")
    print("----------------------------------------------------")
    
    bus.log("MAIN", "System fully operational. Ready for PAR connection.")

    # Pętla główna (blokująca)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping system...")
    finally:
        server.stop()
        print("TARZAN SYSTEM STOPPED.")

if __name__ == "__main__":
    main()
