# TARZAN — LKS‑N5 / Nextion 5 jako sprzętowa tablica komunikatów mini PC

Data: 2026-05-25  
Status: dokumentacja projektowa + specyfikacja HMI Nextion + przygotowanie implementacji  
Nazwa przydzielona: **LKS‑N5**  
Pełna nazwa: **Lampka Kontrolna Systemu — Nextion 5**  
Rola: **sprzętowa tablica komunikatów tarzanMiniPC**

---

## 1. Decyzja architektoniczna

**Nextion 5 nie jest panelem PAR.**

Nextion 5 nie jest drugim ekranem operatorskim TARZANA, nie jest kopią Nextion 7 i nie służy do sterowania EHR/PAR/KHR.

Nextion 5 jest wizualną wersją LKS dla `tarzanMiniPC`.

```text
LKS-TTY = tekstowa lampka kontrolna na TTY mini PC
LKS-N5  = wizualna lampka kontrolna na Nextion 5
```

Model pracy:

```text
Linux / systemd / TSP / hardware runtime / LKS
        ↓
LKS-N5 bridge
        ↓
Nextion 5
```

Nie:

```text
PAR → Nextion 5
```

PAR może być tylko jednym ze statusów widocznych na LKS-N5:

```text
PAR: OFFLINE
PAR: CONNECTED
PAR: LOST
```

ale PAR nie steruje bezpośrednio Nextionem 5.

---

## 2. Najważniejsza zasada

```text
mini PC wysyła znaczenie
Nextion 5 robi grafikę
```

Mini PC nie generuje grafiki, nie renderuje UI i nie składa obrazów.

Mini PC wysyła krótkie komendy:

```text
scene=boot
scene=ready
scene=warning
take=001
line1=TSP OK
line2=PLAY OK
```

Nextion 5 ma już wgrane:

```text
strony
tła
ikony
kolory
ramki
grafiki ostrzeżeń
grafiki READY / ERROR / TAKE / CLAP
```

i sam pokazuje ładną planszę.

---

## 3. Oficjalny kierunek protokołu Nextion

Przy implementacji trzymamy się oficjalnego **Nextion Instruction Set**.

W praktyce dla LKS‑N5 używamy wyłącznie prostych, bezpiecznych poleceń:

```text
page <page_name>
t_xxx.txt="tekst"
n_xxx.val=123
vis <component>,0/1
bkcmd=3
sendme
print / prints / printh tylko jeśli potrzebne do debug eventów
```

Każda komenda wysyłana z Linuxa/PC do Nextiona musi być zakończona trzema bajtami:

```text
0xFF 0xFF 0xFF
```

Na każdej stronie Nextiona warto dodać `sendme`, aby mini PC wiedział, jaka strona jest aktualna.

---

## 4. Zakres pierwszego etapu

Pierwszy etap LKS‑N5:

```text
INTRO
↓
ŁADOWANIE LINUXA
↓
START USŁUG
↓
TEST OBECNOŚCI URZĄDZEŃ
↓
TEST BEZPIECZNY HARDWARE
↓
GOTOWE / READY
```

Nie testujemy w tym etapie:

```text
STEP
DIR
ENABLE
ruchu osi
CNC impulse
nieznanych outputów
wyjść wykonawczych poza whitelistą
```

Wolno testować:

```text
obecność systemu
obecność usług
TSP
SSH
PoKeysLib
PoKeys PLAY/REC scan
LCD PLAY/REC
Matrix LED REC
LED F1-F4 tylko whitelistą
przyciski F1-F4 jako odczyt
klawiatura 4x3 jako odczyt
BUS/I2C scan
porty UART/Nextion
```

---

## 5. Proponowana struktura plików w projekcie

Główna logika w `core/TSP`, bo LKS‑N5 jest częścią systemu pracy `tarzanMiniPC`.

```text
core/TSP/
  tarzanTspLks.py                # istniejąca LKS tekstowa / TTY
  tarzanTspLksNextion5.py        # NOWE: wizualna LKS-N5
  tarzanTspLksBootCheck.py       # NOWE: sekwencja boot/check/test
  tarzanTspLksMessages.py        # NOWE: sceny i kody komunikatów
```

Niski poziom portu Nextion:

```text
hardware/tarzanNextion/
  lks_n5_device.py               # NOWE: serial, send_cmd, page, txt, val
```

Opcjonalny serwis systemd:

```text
config/systemd/
  tarzan-lks-n5.service
```

Docelowy przepływ:

```text
systemd
   ↓
core/TSP/tarzanTspLksNextion5.py
   ↓
hardware/tarzanNextion/lks_n5_device.py
   ↓
/dev/ttyUSBx albo /dev/serial/by-id/...
   ↓
Nextion 5
```

---

## 6. Nazwy stron w Nextion Editor

Zakładamy Nextion 5 w układzie 800×480. Jeżeli ekran ma inny rozmiar, układ należy przeskalować, ale nazwy stron i komponentów zostają.

Strony HMI:

```text
boot_intro
boot_loading
boot_linux
boot_services
boot_hardware
boot_test
ready_main
take_main
warn_main
error_main
status_main
```

Minimalny zestaw na pierwszy etap:

```text
boot_intro
boot_loading
boot_hardware
ready_main
warn_main
error_main
```

---

## 7. Wspólne komponenty na stronach

Na większości stron stosujemy ten sam schemat nazw, żeby mini PC wysyłał proste komendy bez zgadywania.

### Komponenty tekstowe

```text
t_title      — duży tytuł strony
t_subtitle   — podtytuł / opis
t_line1      — linia komunikatu 1
t_line2      — linia komunikatu 2
t_line3      — linia komunikatu 3
t_status     — krótki status dolny
t_code       — kod błędu / kod testu
```

### Komponenty numeryczne

```text
n_progress   — procent / etap 0-100
n_level      — poziom komunikatu: 0 OK, 1 INFO, 2 WARN, 3 ERROR
n_test_idx   — numer aktualnego testu
```

### Komponenty graficzne / obrazki

```text
p_bg         — tło strony
p_icon       — główna ikona
p_logo       — logo TARZAN
p_ok         — ikona OK
p_warn       — ikona WARNING
p_err        — ikona ERROR
p_spinner1   — animacja / klatka 1
p_spinner2   — animacja / klatka 2
p_spinner3   — animacja / klatka 3
```

### Progress / paski

```text
j_progress   — progress bar
```

Jeżeli w danym typie Nextiona nie używasz `j_progress`, można zastąpić go prostokątem/paskiem z kilkoma obrazkami albo tylko tekstem.

---

## 8. Strony — szczegóły do wpisania w Nextion Editor

### 8.1 `boot_intro`

Rola: pierwsza plansza po starcie zasilania. Działa nawet zanim Linux zacznie mówić do ekranu.

Elementy:

```text
p_bg
p_logo
t_title
t_subtitle
tm_intro
```

Teksty domyślne:

```text
t_title.txt="TARZAN"
t_subtitle.txt="SIGNAL NODE"
```

Event `PostInitialize` strony:

```text
sendme
tm_intro.en=1
```

Timer `tm_intro`:

```text
tim=1200
en=0
```

Event timera:

```text
page boot_loading
```

Sens: Nextion sam pokazuje intro i po chwili przechodzi do ładowania. Nie potrzebuje jeszcze Linuxa.

---

### 8.2 `boot_loading`

Rola: Linux / system jeszcze wstaje.

Elementy:

```text
p_bg
p_logo
t_title
t_line1
t_line2
t_status
j_progress
tm_load
n_progress
```

Teksty domyślne:

```text
t_title.txt="LOADING"
t_line1.txt="LINUX SYSTEM"
t_line2.txt="PLEASE WAIT"
t_status.txt="waiting for LKS-N5 service..."
n_progress.val=10
j_progress.val=10
```

Event `PostInitialize`:

```text
sendme
tm_load.en=1
```

Timer `tm_load` — prosta animacja oczekiwania:

```text
tim=500
en=0
```

Event timera, wersja prosta:

```text
n_progress.val+=5
if(n_progress.val>90)
{
  n_progress.val=20
}
j_progress.val=n_progress.val
```

Linux po starcie nadpisze tę stronę realnymi komunikatami.

---

### 8.3 `boot_linux`

Rola: LKS-N5 service już działa i potwierdza, że Linux wystartował.

Elementy:

```text
t_title
t_line1
t_line2
t_status
j_progress
```

Domyślne:

```text
t_title.txt="LINUX OK"
t_line1.txt="SYSTEM STARTED"
t_line2.txt="STARTING SERVICES"
t_status.txt="LKS-N5 ONLINE"
j_progress.val=30
```

Event `PostInitialize`:

```text
sendme
```

---

### 8.4 `boot_services`

Rola: sprawdzanie usług systemowych.

Elementy:

```text
t_title
t_line1
t_line2
t_line3
t_status
j_progress
```

Przykłady tekstów ustawianych z mini PC:

```text
t_title.txt="SERVICES"
t_line1.txt="SSH: OK"
t_line2.txt="TSP: STARTING"
t_line3.txt="LKS: OK"
t_status.txt="checking..."
j_progress.val=45
```

Event `PostInitialize`:

```text
sendme
```

---

### 8.5 `boot_hardware`

Rola: skan sprzętu.

Elementy:

```text
t_title
t_line1
t_line2
t_line3
t_status
j_progress
```

Przykłady:

```text
t_title.txt="HARDWARE CHECK"
t_line1.txt="PLAY: OK"
t_line2.txt="REC: OK"
t_line3.txt="PoKeysLib: OK"
t_status.txt="checking bus..."
j_progress.val=65
```

Event `PostInitialize`:

```text
sendme
```

---

### 8.6 `boot_test`

Rola: bezpieczne testy peryferiów.

Elementy:

```text
t_title
t_line1
t_line2
t_line3
t_status
t_code
n_test_idx
j_progress
```

Przykłady:

```text
t_title.txt="DEVICE TEST"
t_line1.txt="LCD PLAY: OK"
t_line2.txt="MATRIX REC: OK"
t_line3.txt="F1 LED: OK"
t_status.txt="running whitelist tests"
t_code.txt="TEST 03/08"
j_progress.val=80
```

Event `PostInitialize`:

```text
sendme
```

---

### 8.7 `ready_main`

Rola: normalny stan gotowości.

Elementy:

```text
p_bg
p_logo
p_ok
t_title
t_line1
t_line2
t_line3
t_status
```

Teksty:

```text
t_title.txt="TARZAN NODE"
t_line1.txt="SYSTEM READY"
t_line2.txt="TSP: OK   PAR: WAIT"
t_line3.txt="PLAY: OK  REC: OK"
t_status.txt="LKS-N5 READY"
```

Event `PostInitialize`:

```text
sendme
```

---

### 8.8 `take_main`

Rola: główne komunikaty TAKE / CLAP / marker, ale tylko informacyjnie. Nie PAR steruje ekranem, tylko LKS/TSP/hardware runtime pokazuje ważny marker.

Elementy:

```text
p_bg
p_icon
t_title
t_take
t_tc
t_line1
t_status
```

Teksty:

```text
t_title.txt="TAKE"
t_take.txt="001"
t_tc.txt="00:00:12:08"
t_line1.txt="CLAP MARKED"
t_status.txt="marker saved"
```

Event `PostInitialize`:

```text
sendme
```

---

### 8.9 `warn_main`

Rola: ostrzeżenie.

Elementy:

```text
p_bg
p_warn
t_title
t_line1
t_line2
t_code
t_status
```

Teksty:

```text
t_title.txt="WARNING"
t_line1.txt="NEXTION 7 LOST"
t_line2.txt="CHECK USB PORT"
t_code.txt="N7_OFFLINE"
t_status.txt="system still running"
```

Event `PostInitialize`:

```text
sendme
```

---

### 8.10 `error_main`

Rola: błąd krytyczny / wymagana reakcja.

Elementy:

```text
p_bg
p_err
t_title
t_line1
t_line2
t_code
t_status
```

Teksty:

```text
t_title.txt="ERROR"
t_line1.txt="POKEYS REC LOST"
t_line2.txt="CHECK HARDWARE"
t_code.txt="REC_OFFLINE"
t_status.txt="operator action required"
```

Event `PostInitialize`:

```text
sendme
```

---

### 8.11 `status_main`

Rola: skrócony status node. Nie pełny log.

Elementy:

```text
t_title
t_line1
t_line2
t_line3
t_status
```

Przykład:

```text
t_title.txt="NODE STATUS"
t_line1.txt="TSP: OK   CLIENTS: 1"
t_line2.txt="PLAY: OK  REC: OK"
t_line3.txt="BUS: OK   N7: WAIT"
t_status.txt="uptime 00:03:21"
```

Event `PostInitialize`:

```text
sendme
```

---

## 9. Komendy, które będzie wysyłał mini PC

### Start po uruchomieniu usługi LKS-N5

```text
bkcmd=3
page boot_linux
t_title.txt="LINUX OK"
t_line1.txt="SYSTEM STARTED"
t_line2.txt="STARTING SERVICES"
t_status.txt="LKS-N5 ONLINE"
j_progress.val=30
```

### Sprawdzenie TSP

```text
page boot_services
t_title.txt="SERVICES"
t_line1.txt="SSH: OK"
t_line2.txt="TSP: STARTING"
t_line3.txt="LKS: OK"
j_progress.val=45
```

Po sukcesie:

```text
t_line2.txt="TSP: OK"
j_progress.val=55
```

### Skan PoKeys

```text
page boot_hardware
t_title.txt="HARDWARE CHECK"
t_line1.txt="PLAY: SCAN..."
t_line2.txt="REC: SCAN..."
t_line3.txt="PoKeysLib: OK"
j_progress.val=60
```

Po sukcesie:

```text
t_line1.txt="PLAY: OK 36102"
t_line2.txt="REC: OK 36084"
j_progress.val=70
```

### Bezpieczny test urządzeń

```text
page boot_test
t_title.txt="DEVICE TEST"
t_line1.txt="LCD PLAY: TEST"
t_line2.txt="MATRIX REC: WAIT"
t_line3.txt="F1 LED: WAIT"
t_code.txt="TEST 01/08"
j_progress.val=75
```

Po zakończeniu:

```text
t_line1.txt="LCD PLAY: OK"
t_line2.txt="MATRIX REC: OK"
t_line3.txt="F1-F4 LED: OK"
t_code.txt="TEST DONE"
j_progress.val=95
```

### Gotowość

```text
page ready_main
t_title.txt="TARZAN NODE"
t_line1.txt="SYSTEM READY"
t_line2.txt="TSP: OK   PAR: WAIT"
t_line3.txt="PLAY: OK  REC: OK"
t_status.txt="LKS-N5 READY"
```

### Ostrzeżenie

```text
page warn_main
t_title.txt="WARNING"
t_line1.txt="NEXTION 7 LOST"
t_line2.txt="CHECK USB PORT"
t_code.txt="N7_OFFLINE"
t_status.txt="system still running"
```

### Błąd

```text
page error_main
t_title.txt="ERROR"
t_line1.txt="POKEYS REC LOST"
t_line2.txt="CHECK USB / POWER"
t_code.txt="REC_OFFLINE"
t_status.txt="operator action required"
```

---

## 10. Zdarzenia z Nextiona do mini PC

Na tym etapie Nextion 5 nie jest panelem sterowania. Nie potrzebujemy wielu przycisków.

Warto jednak dodać 2–3 przyciski serwisowe:

```text
b_status  — pokaż status_main
b_ack     — potwierdź ostrzeżenie
b_test    — uruchom operator hardware test, później
```

Event przycisku `b_status`:

```text
print "lks:n5:status"
printh FF FF FF
```

Event `b_ack`:

```text
print "lks:n5:ack"
printh FF FF FF
```

Event `b_test` — na później, nie musi działać od razu:

```text
print "lks:n5:test"
printh FF FF FF
```

Jeżeli nie chcemy jeszcze żadnych przycisków, można ich nie dodawać. Wtedy Nextion 5 jest czysto wyświetlaczem komunikatów.

---

## 11. Implementacja po stronie Python — szkic

### 11.1 `hardware/tarzanNextion/lks_n5_device.py`

Odpowiedzialność:

```text
otwórz port
wyślij komendę z FF FF FF
page()
txt()
val()
read events
last_tx / last_rx / last_error
```

Szkic API:

```python
class TarzanLksN5Device:
    def __init__(self, port: str, baudrate: int = 9600):
        ...

    def connect(self) -> None:
        ...

    def close(self) -> None:
        ...

    def cmd(self, text: str) -> None:
        # wysyła: text + FF FF FF
        ...

    def page(self, name: str) -> None:
        self.cmd(f"page {name}")

    def txt(self, component: str, value: str) -> None:
        safe = value.replace("\\", "\\\\").replace('"', "'")
        self.cmd(f'{component}.txt="{safe}"')

    def val(self, component: str, value: int) -> None:
        self.cmd(f"{component}.val={int(value)}")
```

### 11.2 `core/TSP/tarzanTspLksMessages.py`

Odpowiedzialność:

```text
nazwy scen
poziomy komunikatów
kody błędów
proste DTO komunikatu
```

Przykład:

```python
SCENE_BOOT = "boot"
SCENE_LOADING = "loading"
SCENE_SERVICES = "services"
SCENE_HARDWARE = "hardware"
SCENE_TEST = "test"
SCENE_READY = "ready"
SCENE_WARN = "warn"
SCENE_ERROR = "error"
SCENE_TAKE = "take"
```

### 11.3 `core/TSP/tarzanTspLksNextion5.py`

Odpowiedzialność:

```text
mapuje scenę LKS na stronę Nextion
ustawia teksty
ustawia progress
nie zna szczegółów PAR
```

Przykład:

```python
class TarzanTspLksNextion5:
    def __init__(self, device):
        self.device = device

    def show_boot_linux(self):
        self.device.page("boot_linux")
        self.device.txt("t_title", "LINUX OK")
        self.device.txt("t_line1", "SYSTEM STARTED")
        self.device.txt("t_line2", "STARTING SERVICES")
        self.device.val("j_progress", 30)

    def show_ready(self):
        self.device.page("ready_main")
        self.device.txt("t_title", "TARZAN NODE")
        self.device.txt("t_line1", "SYSTEM READY")
        self.device.txt("t_line2", "TSP: OK   PAR: WAIT")
        self.device.txt("t_line3", "PLAY: OK  REC: OK")
```

### 11.4 `core/TSP/tarzanTspLksBootCheck.py`

Odpowiedzialność:

```text
sekwencja startowa
sprawdzanie usług
wywołanie bezpiecznych testów
komunikaty do LKS-N5
```

Nie odpala ruchu osi i nie dotyka wyjść wykonawczych.

---

## 12. Systemd — docelowo

Usługa LKS-N5 powinna startować wcześnie po podstawowym starcie systemu.

Przykładowy plik:

```ini
[Unit]
Description=TARZAN LKS-N5 Nextion 5 visual system lamp
After=multi-user.target
Wants=multi-user.target

[Service]
Type=simple
WorkingDirectory=/opt/tarzan
ExecStart=/usr/bin/python3 -m core.TSP.tarzanTspLksNextion5 --port /dev/ttyUSB0 --baudrate 9600 --boot-check
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
```

Docelowo lepiej używać stabilnego portu:

```text
/dev/serial/by-id/usb-...
```

a nie ślepo `/dev/ttyUSB0`.

---

## 13. Bezpieczeństwo testów hardware

### Test automatyczny przy starcie

Automatycznie można wykonać:

```text
PoKeys scan
odczyt statusu
sprawdzenie bibliotek
sprawdzenie portów
sprawdzenie TSP
sprawdzenie I2C scan
```

### Test operatora

Po świadomym uruchomieniu można wykonać:

```text
LCD PLAY / REC
Matrix LED
LED F1-F4 whitelistą
buttons-test
keypad-map
bus sensor test
```

### Zakazane w automacie

```text
STEP/CTR impulsy
ENABLE
ruch osi
nieznane wyjścia
CNC impulse
```

---

## 14. Proponowany przebieg pierwszego testu po zbudowaniu HMI

1. Wgrać HMI do Nextion 5.
2. Podłączyć Nextion 5 do mini PC.
3. Sprawdzić port:

```bash
ls -l /dev/serial/by-id/
```

4. Uruchomić prosty test ręczny z Python/serial:

```text
bkcmd=3
page boot_linux
t_title.txt="LINUX OK"
t_line1.txt="TEST FROM MINI PC"
```

5. Jeżeli ekran reaguje, dopiero dodać `tarzanTspLksNextion5.py`.
6. Dopiero potem dodać boot-check i systemd.

---

## 15. Wniosek

LKS‑N5 jest osobnym, bardzo użytecznym modułem mini PC.

Nie jest PAR-em.

Jego pierwsza implementacja powinna zacząć się od:

```text
INTRO
LOADING LINUX
CHECK SERVICES
CHECK HARDWARE
READY
```

a dopiero potem dostać:

```text
WARNING
ERROR
TAKE
CLAP
STATUS
```

Najważniejsze: mini PC wysyła krótkie stany, a Nextion 5 pokazuje gotową grafikę.
