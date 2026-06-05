#!/usr/bin/env python3
import os
import shutil
import platform
import sys
from pathlib import Path

def find_and_install_pokeys():
    print("--- TARZAN PoKeys Library Installer ---")
    
    if platform.system() == "Windows":
        print("This script is intended for Linux/miniPC systems.")
        print("On Windows, ensure hardware/pokeys/PoKeysDevice_x64.dll is present.")
        return

    # Docelowa lokalizacja
    repo_root = Path(__file__).resolve().parents[1]
    target_dir = repo_root / "hardware" / "pokeys"
    target_path = target_dir / "libPoKeys.so"
    
    # Tworzenie katalogu jeśli nie istnieje
    if not target_dir.exists():
        print(f"Creating directory: {target_dir}")
        target_dir.mkdir(parents=True, exist_ok=True)

    if target_path.exists():
        print(f"PoKeys library already exists at: {target_path}")
        # Możemy chcieć nadpisać jeśli użytkownik tego chce, ale domyślnie zostawiamy
        # print("Skipping.")
        # return

    # Potencjalne lokalizacje biblioteki
    search_paths = [
        "/usr/lib/libPoKeys.so",
        "/usr/local/lib/libPoKeys.so",
        "/opt/PoKeysLib/libPoKeys.so",
        "/usr/lib/x86_64-linux-gnu/libPoKeys.so",
    ]
    
    # Dodatkowo szukamy za pomocą 'find' jeśli powyższe zawiodą (wolniejsze)
    found_path = None
    for p in search_paths:
        if os.path.exists(p):
            found_path = p
            break
            
    if not found_path:
        print("Standard locations empty. Searching with find (this may take a while)...")
        import subprocess
        try:
            # Szukamy tylko w /usr, /opt, /root, /home dla szybkości
            cmd = "find /usr /opt /root /home -name 'libPoKeys.so' 2>/dev/null | head -n 1"
            result = subprocess.check_output(cmd, shell=True).decode().strip()
            if result:
                found_path = result
        except Exception as e:
            print(f"Search failed: {e}")

    if found_path:
        print(f"Found library at: {found_path}")
        try:
            print(f"Copying to: {target_path}")
            shutil.copy2(found_path, target_path)
            os.chmod(target_path, 0o755)
            print("SUCCESS: PoKeys library installed.")
        except Exception as e:
            print(f"ERROR: Failed to copy library: {e}")
            sys.exit(1)
    else:
        print("CRITICAL: libPoKeys.so not found on this system.")
        print("Please install PoKeys SDK first or provide libPoKeys.so manually.")
        sys.exit(1)

if __name__ == "__main__":
    find_and_install_pokeys()
