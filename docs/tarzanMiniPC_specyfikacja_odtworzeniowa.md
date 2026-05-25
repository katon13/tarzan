# TARZAN — specyfikacja odtworzeniowa `tarzanMiniPC`

**Cel dokumentu:** szybkie odtworzenie `tarzanMiniPC`, gdy system się wywali, dysk zostanie wymieniony albo Debian trzeba będzie postawić od zera.

**Rola maszyny:** `tarzanMiniPC` jest lekkim node wykonawczym TARZANA. Nie uruchamia UI. UI/PAR/EHR/operator pracują na `tarzanStacja`.

---

## 1. Stała rola systemowa

```text
Nazwa maszyny:        tarzanMiniPC
Hostname Linux:       tarzan
Rola:                 TARZAN Signal Node
Główne IP LAN:        192.168.1.26
Stacja operatorska:   tarzanStacja / 192.168.1.12
Protokół:             TSP — TARZAN Signal Protocol
Port TSP:             7777
Dostęp serwisowy:     SSH / PuTTY
UI lokalne:           NIE
```

Model pracy:

```text
tarzanStacja
  ├─ PAR
  ├─ EHR
  ├─ UI/operator
  ├─ podglądy
  └─ klient TSP

LAN
  ↓

tarzanMiniPC
  ├─ Debian / systemd
  ├─ SSH
  ├─ TSP server
  ├─ SignalBus runtime
  ├─ Snajper / Target LAN
  ├─ Nextion bridge
  ├─ PoKeys
  ├─ czujniki
  └─ prosta diagnostyka
```

---

## 2. Bazowy stan systemu z raportu

Ostatni dobry raport referencyjny:

```text
Plik: tarzan_system_report.txt
Data: 25 maj 2026, 10:21 CEST
```

Stan bazowy:

```text
OS:                Debian GNU/Linux 13 trixie
Kernel:            Linux 6.12.90+deb13-amd64
Hostname:          tarzan
Architektura:      x86_64
Sprzęt:            NP93
CPU:               Intel Celeron N2930 @ 1.83GHz
CPU:               4 rdzenie / 4 wątki
RAM:               1.8 GiB
Swap:              1.9 GiB
Dysk:              /dev/sda 119.2G
Partycja root:     /dev/sda2 116.4G
Użycie root:       ok. 8%
LAN:               enp2s0
Adres LAN:         192.168.1.26/24
Brama:             192.168.1.1
SSH:               active/running
TSP:               active/running
TSP port:          0.0.0.0:7777 LISTEN
Python:            3.13.5
TSP compile:       OK
Failed services:   0
Wi-Fi:             wyłączone na tym etapie
```

---

## 3. Co ma działać po odtworzeniu

Po starcie systemu automatycznie mają działać:

```text
ssh.service
tarzan-tsp.service
networking.service
systemd-timesyncd.service
```

Minimalny oczekiwany wynik:

```bash
systemctl status ssh --no-pager
systemctl status tarzan-tsp --no-pager
ss -ltnp | grep 7777
```

Powinno być:

```text
ssh.service: active (running)
tarzan-tsp.service: active (running)
0.0.0.0:7777 LISTEN
```

---

## 4. Repozytorium TARZAN

Stałe repozytorium:

```text
https://github.com/katon13/tarzan
```

Docelowa lokalizacja na mini PC:

```text
/opt/tarzan
```

Odtworzenie katalogu:

```bash
cd /opt
git clone https://github.com/katon13/tarzan.git tarzan
cd /opt/tarzan
```

Jeżeli katalog już istnieje i trzeba go wyrównać do GitHub:

```bash
cd /opt/tarzan
git fetch origin
git reset --hard origin/main
```

Wymagany katalog TSP:

```text
/opt/tarzan/core/TSP/
```

Aktualny zestaw plików TSP:

```text
core/TSP/__init__.py
core/TSP/tarzanTsp.py
core/TSP/tarzanTspClient.py
core/TSP/tarzanTspConfig.py
core/TSP/tarzanTspLog.py
core/TSP/tarzanTspProtocol.py
core/TSP/tarzanTspServer.py
core/TSP/tarzanTspSignals.py
```

Kontrola:

```bash
cd /opt/tarzan
ls core/TSP
python3 -m compileall -q core/TSP
echo COMPILE_OK
```

---

## 5. Python / venv

Jeżeli po odtworzeniu nie ma `.venv`, utworzyć:

```bash
cd /opt/tarzan
python3 -m venv .venv
source /opt/tarzan/.venv/bin/activate
python -m pip install --upgrade pip
```

Minimalny test:

```bash
cd /opt/tarzan
source /opt/tarzan/.venv/bin/activate
python -m compileall -q core/TSP
python -m core.TSP.tarzanTsp server
```

Po ręcznym starcie serwer powinien pokazać:

```text
TSP SERVER START host=0.0.0.0 port=7777 node=tarzanMiniPC
TSP_STATS clients=0 tx=0 rx=0 errors=0 dropped=0 lanes={}
```

Zatrzymanie testu:

```text
CTRL+C
```

---

## 6. Plik startowy TSP

Plik:

```text
/opt/tarzan/run_tsp.sh
```

Treść:

```bash
#!/bin/bash
set -e

cd /opt/tarzan
source /opt/tarzan/.venv/bin/activate

exec python -m core.TSP.tarzanTsp server
```

Utworzenie:

```bash
cat > /opt/tarzan/run_tsp.sh <<'EOF'
#!/bin/bash
set -e

cd /opt/tarzan
source /opt/tarzan/.venv/bin/activate

exec python -m core.TSP.tarzanTsp server
EOF

chmod +x /opt/tarzan/run_tsp.sh
```

Kontrola:

```bash
ls -l /opt/tarzan/run_tsp.sh
```

Ma być:

```text
-rwxr-xr-x
```

---

## 7. Usługa systemd `tarzan-tsp.service`

Plik:

```text
/etc/systemd/system/tarzan-tsp.service
```

Aktualna treść dopasowana pod LAN / networking:

```ini
[Unit]
Description=TARZAN TSP Server on tarzanMiniPC
After=networking.service ssh.service
Wants=networking.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/tarzan
Environment=PYTHONUNBUFFERED=1
ExecStart=/opt/tarzan/run_tsp.sh
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Utworzenie:

```bash
cat > /etc/systemd/system/tarzan-tsp.service <<'EOF'
[Unit]
Description=TARZAN TSP Server on tarzanMiniPC
After=networking.service ssh.service
Wants=networking.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/tarzan
Environment=PYTHONUNBUFFERED=1
ExecStart=/opt/tarzan/run_tsp.sh
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
```

Aktywacja:

```bash
systemctl daemon-reload
systemctl enable tarzan-tsp
systemctl start tarzan-tsp
systemctl status tarzan-tsp --no-pager
```

Oczekiwane:

```text
Loaded: loaded (...; enabled; ...)
Active: active (running)
python -m core.TSP.tarzanTsp server
```

Kontrola portu:

```bash
ss -ltnp | grep 7777
```

Oczekiwane:

```text
LISTEN 0 10 0.0.0.0:7777
```

---

## 8. Sieć LAN

Aktualny model: LAN po kablu jest głównym połączeniem roboczym.

Interfejs:

```text
enp2s0
```

Konfiguracja bazowa `/etc/network/interfaces`:

```text
source /etc/network/interfaces.d/*

auto lo
iface lo inet loopback

allow-hotplug enp2s0
iface enp2s0 inet dhcp
```

W aktualnej sieci DHCP nadaje:

```text
192.168.1.26/24
gateway 192.168.1.1
```

Kontrola:

```bash
ip a
ip route
```

Oczekiwane:

```text
enp2s0 UP
inet 192.168.1.26/24
default via 192.168.1.1 dev enp2s0
```

---

## 9. SSH

SSH ma być zawsze aktywne, bo to kanał ratunkowy.

Instalacja / aktywacja:

```bash
apt update
apt install -y openssh-server
systemctl enable ssh
systemctl start ssh
```

Kontrola:

```bash
systemctl status ssh --no-pager
```

Oczekiwane:

```text
Active: active (running)
Server listening on 0.0.0.0 port 22
```

Połączenie ze stacji:

```text
PuTTY
Host: 192.168.1.26
Port: 22
User: root
```

---

## 10. Tryb bez UI

`tarzanMiniPC` nie ma obsługiwać lokalnego UI.

Docelowy target:

```bash
systemctl set-default multi-user.target
systemctl get-default
```

Oczekiwane:

```text
multi-user.target
```

Nie uruchamiać lokalnie:

```text
PAR
EHR
ciężkich podglądów
kamery / AI
grafiki operatora
```

To działa na `tarzanStacja`.

---

## 11. Wi-Fi

Aktualny stan: Wi-Fi celowo wyłączone na tym etapie.

Raport bazowy:

```text
wlp3s0: DOWN
nmcli radio wifi: disabled
rfkill Wireless LAN: Soft blocked: yes
```

To jest akceptowane, bo główne połączenie robocze to LAN.

Później można Wi-Fi przywrócić jako:

```text
opcja serwisowa
zapas
połączenie dodatkowe
```

Nie ruszać LAN podczas naprawy Wi-Fi, żeby nie stracić SSH.

Komendy pomocnicze na przyszłość:

```bash
nmcli radio wifi on
rfkill unblock wifi
nmcli device wifi list
```

---

## 12. PoKeys

PoKeys pozostaje osobną warstwą sprzętową.

Zasada:

```text
tarzanPoKeysSetting.py
→ konfiguracja / walidacja sprzętu PoKeys

TSP
→ live komunikacja sygnałowa po LAN
```

TSP może raportować stan PoKeys, ale nie ma sam wykonywać trwałego zapisu konfiguracji PoKeys do flash.

Zapis konfiguracji PoKeys musi być jawny i świadomy.

Biblioteka PoKeys obsługuje m.in.:

```text
Digital IO
Analog IO
PWM
I2C
1-wire
SPI
PoExtBus
Matrix Keyboard
LCD
Matrix LED
Pulse Engine / PEv2
EasySensors
```

---

## 13. Nextion

Nextion działa przez Bridge/Snajpera jako sprzętowy target.

Zasada architektury:

```text
SignalBus → Snajper → Target physical_nextion → Bridge → Nextion
```

Nie budować osobnego toru odświeżania Nextiona obok Snajpera.

Mini PC może obsługiwać fizyczny Nextion, ale UI operatorskie i PAR/EHR są na `tarzanStacja`.

---

## 14. TSP — zasady architektury

TSP nie jest osobnym systemem obok TARZANA.

TSP to sieciowy target / ramię Snajpera.

Stała zasada:

```text
SignalBus = źródło prawdy
Snajper   = dyrygent odświeżania
TSP       = brama LAN / target sieciowy
Mini PC   = TARZAN Signal Node
```

TSP nie może:

```text
zastępować SignalBus
zastępować Snajpera
budować ręcznych map sygnałów
liczyć wartości RRP
odświeżać Nextiona poza Snajperem
robić własnej mechaniki osi
tworzyć drugiego systemu live
```

---

## 15. Diagnostyka po awarii

Po uruchomieniu nowego / naprawionego systemu wykonać:

```bash
hostnamectl
ip a
ip route
systemctl get-default
systemctl --failed
systemctl status ssh --no-pager
systemctl status tarzan-tsp --no-pager
ss -ltnp | grep 7777
cd /opt/tarzan
python3 -m compileall -q core/TSP
echo TSP_COMPILE_OK
```

Oczekiwany skrót:

```text
hostname: tarzan
OS: Debian 13
LAN: 192.168.1.26
default target: multi-user.target
failed services: 0
ssh: active
tarzan-tsp: active
port 7777: LISTEN
TSP_COMPILE_OK
```

---

## 16. Raport systemowy — skrypt kontrolny

Po odtworzeniu systemu warto wygenerować nowy raport:

```bash
cat > /tmp/tarzan_system_check.sh <<'EOF'
#!/bin/bash

OUT="/tmp/tarzan_system_report.txt"

{
echo "===== TARZAN MINIPC SYSTEM REPORT ====="
date
echo

echo "===== HOSTNAME ====="
hostname
hostnamectl 2>/dev/null
echo

echo "===== KERNEL / OS ====="
uname -a
cat /etc/os-release
echo

echo "===== CPU ====="
lscpu
echo

echo "===== RAM ====="
free -h
echo

echo "===== DISK ====="
df -h
echo

echo "===== BLOCK DEVICES ====="
lsblk
echo

echo "===== NETWORK IP ====="
ip a
echo

echo "===== NETWORK ROUTES ====="
ip route
echo

echo "===== NMCLI DEVICE STATUS ====="
nmcli device status 2>/dev/null
echo

echo "===== WIFI RADIO ====="
nmcli radio wifi 2>/dev/null
echo

echo "===== RFKILL ====="
rfkill list 2>/dev/null
echo

echo "===== ENABLED SERVICES ====="
systemctl list-unit-files --state=enabled
echo

echo "===== FAILED SERVICES ====="
systemctl --failed
echo

echo "===== SSH STATUS ====="
systemctl status ssh --no-pager
echo

echo "===== TSP STATUS ====="
systemctl status tarzan-tsp --no-pager 2>/dev/null || true
echo

echo "===== TSP PORT 7777 ====="
ss -ltnp | grep 7777 || true
echo

echo "===== PYTHON ====="
cd /opt/tarzan 2>/dev/null && python3 --version
cd /opt/tarzan 2>/dev/null && python3 -m compileall -q core/TSP && echo "TSP COMPILE OK" || echo "TSP COMPILE FAIL"
echo

echo "===== TEMPERATURE ====="
sensors 2>/dev/null || echo "sensors not installed"
echo

echo "===== LAST BOOT ERRORS ====="
journalctl -p warning -b --no-pager | tail -80
echo

echo "===== IWLWIFI LAST LOG ====="
dmesg | grep -i iwlwifi | tail -40
echo

echo "===== END REPORT ====="
} > "$OUT" 2>&1

echo "$OUT"
EOF

chmod +x /tmp/tarzan_system_check.sh
/tmp/tarzan_system_check.sh
cat /tmp/tarzan_system_report.txt
```

---

## 17. Znane rzeczy poboczne z aktualnego raportu

Nie blokują pracy TSP:

```text
ACPI BIOS warnings
hpet warning
ASPM warning
smartd_opts warning
IPv6 router warning
```

Do sprzątnięcia później:

```text
drkonqi-coredump-launcher.socket spamuje log
PipeWire / wireplumber zależności user-session
```

To są resztki środowiska graficznego/KDE i nie są potrzebne dla node bez UI.

---

## 18. Szybka procedura po reinstalacji — skrót

```bash
apt update
apt install -y git python3 python3-venv openssh-server rfkill network-manager

systemctl enable ssh
systemctl start ssh
systemctl set-default multi-user.target

cd /opt
git clone https://github.com/katon13/tarzan.git tarzan
cd /opt/tarzan

python3 -m venv .venv
source /opt/tarzan/.venv/bin/activate
python -m pip install --upgrade pip
python -m compileall -q core/TSP

cat > /opt/tarzan/run_tsp.sh <<'EOF'
#!/bin/bash
set -e
cd /opt/tarzan
source /opt/tarzan/.venv/bin/activate
exec python -m core.TSP.tarzanTsp server
EOF
chmod +x /opt/tarzan/run_tsp.sh

cat > /etc/systemd/system/tarzan-tsp.service <<'EOF'
[Unit]
Description=TARZAN TSP Server on tarzanMiniPC
After=networking.service ssh.service
Wants=networking.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/tarzan
Environment=PYTHONUNBUFFERED=1
ExecStart=/opt/tarzan/run_tsp.sh
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable tarzan-tsp
systemctl start tarzan-tsp
systemctl status tarzan-tsp --no-pager
ss -ltnp | grep 7777
```

---

## 19. Ostateczna definicja roli

```text
tarzanMiniPC nie jest komputerem UI.
tarzanMiniPC jest lekkim node wykonawczym TARZANA.

Ma działać stabilnie, startować sam, odbierać połączenie ze stacji,
obsługiwać elektronikę, czujniki, PoKeys, Nextiona i TSP.

tarzanStacja obsługuje operatora, PAR, EHR, grafikę i ciężką pracę.
```
