# TARZAN TSP — TARZAN Signal Protocol

## 1. Czym jest TSP

**TSP — TARZAN Signal Protocol** to lekki protokół komunikacji sieciowej dla TARZANA.

Jego zadaniem jest połączenie:

```text
DUŻY PC / EHR / PAR / klient TARZANA
        ↓ kabel LAN / TCP
MINI PC / TARZAN Signal Node
        ↓
SignalBus / Snajper / Bridge / Nextion / elektronika
```

Mini PC nie ma być głównie komputerem od UI. Ma być **TARZAN Signal Node**, czyli wykonawczym blokiem TARZANA przy elektronice.

Mini PC obsługuje:

```text
SignalBus live
Snajpera
Bridge
Nextiona
czujniki
porty USB/COM
elektronikę
logi
procesy runtime
```

Duży komputer obsługuje:

```text
EHR
PAR jako klient zdalny
konfigurację
wygodny podgląd
edycję
```

---

## 2. Główna zasada

TSP **nie jest drugim systemem odświeżania**.

TSP ma być **sieciowym targetem Snajpera**.

Nie robimy tak:

```text
SignalBus → PAR
SignalBus → Nextion
SignalBus → TSP osobno
```

Robimy tak:

```text
SignalBus
  ↓
Caliber
  ↓
Bullet
  ↓
Target:
   - PAR
   - Nextion preview
   - physical Nextion
   - TSP / LAN
  ↓
Snajper.fire()
```

Czyli TSP jest kolejnym celem Snajpera, tak samo jak PAR albo fizyczny Nextion.

---

## 3. Źródło prawdy

Źródłem prawdy zostaje zawsze:

```text
SignalBus
```

TSP nie tworzy własnej logiki sygnałów.

TSP nie mapuje ręcznie nazw, jeśli można użyć istniejącej logiki TARZANA:

```text
kanoniczna_nazwa
Caliber
Bullet
Target
Snajper
```

TSP ma tylko:

```text
wysłać stan sygnałów po LAN
odebrać komendę z klienta
przekazać ją do SignalBus / właściwej akcji
```

---

## 4. Rola Snajpera

Snajper pozostaje dyrygentem odświeżania.

Przykład:

```text
rrp_p1_value
  ↓
Snajper
  ↓
Target physical_nextion → t_p1_val.val
Target PAR              → panel RRP
Target TSP              → pakiet LAN do dużego PC
```

Dzięki temu nie powstają równoległe tory:

```text
osobny polling TSP
osobne odświeżanie PAR
osobna logika Bridge
```

Wszystko idzie przez jeden model:

```text
SignalBus → Snajper → Target
```

---

## 5. Transport protokołu

Proponowany transport TSP v1:

```text
TCP socket
JSON Lines / NDJSON
jedna wiadomość = jedna linia JSON zakończona \n
```

Dlaczego:

```text
lekki
czytelny
łatwy do debugowania
łatwy do logowania
działa po zwykłym kablu LAN
wystarczająco szybki dla TARZANA
```

Przykład pojedynczej wiadomości:

```json
{"cmd":"get_signal","name":"rrp_p1_value"}
```

Odpowiedź:

```json
{"ok":true,"name":"rrp_p1_value","value":1234,"ts":812340}
```

---

## 6. Kabel LAN i szybkość

Ethernet spokojnie wystarczy dla TARZANA.

Typowe sieci:

```text
100 Mb/s
1 Gb/s
```

Pakiety sygnałów TARZANA są małe. Problemem nie będzie kabel, tylko dobra organizacja sygnałów i brak niepotrzebnego rysowania UI.

---

## 7. Rytm pracy

Wewnętrzny rytm TARZANA zostaje:

```text
SignalBus / core tick: 10 ms
```

TSP może mieć szybkie pasmo również co 10 ms, ale nie dla wszystkiego.

Proponowane pasma:

```text
FAST   — 10 ms
NORMAL — 30–50 ms
SLOW   — 250–1000 ms
```

---

## 8. TSP FAST — 10 ms

Pasmo FAST służy do żywych sygnałów.

Przykłady:

```text
axis pulses
STEP/DIR live preview
RRP P1/P2 value
take_time_ms
take_timecode
transport_state
active_mode
stany bezpieczeństwa
czujniki krytyczne
Nextion live values
```

Przykład pakietu:

```json
{
  "event": "snajper_packet",
  "lane": "fast",
  "ts": 12345670,
  "dt_ms": 10,
  "values": {
    "rrp_p1_value": 401,
    "rrp_p2_value": 388,
    "axis_0_pulses": 1204,
    "take_time_ms": 8840
  }
}
```

---

## 9. TSP URGENT EVENT — natychmiastowy kanał zdarzeń

TSP nie może działać wyłącznie jako cykliczne paczki co 10 ms.

Docelowy model komunikacji ma mieć dwa tory:

```text
FAST FRAME    — rytmiczna paczka live co 10 ms
URGENT EVENT  — natychmiastowy strzał poza rytmem
```

Zasada:

```text
FAST pokazuje płynność.
URGENT daje natychmiastową reakcję.
```

`URGENT EVENT` jest kanałem przerwaniowym / alarmowym. Nie zastępuje FAST i nie służy do zwykłego strumienia wszystkich sygnałów.

### Kiedy używać URGENT

URGENT stosujemy tylko dla zdarzeń, które nie powinny czekać do następnej paczki FAST.

Przykłady:

```text
STOP
E-STOP
LIMIT HIT
utrata połączenia z Nextionem
zmiana PAGE z sendme
zmiana MODE
transport_state STOP / PLAY / REC
awaria Bridge
alarm czujnika
ręczny wybór osi RRP
CLAP / TAKE marker
błąd bezpieczeństwa
zatrzymanie osi
```

### Przykład pakietu URGENT

```json
{
  "event": "urgent",
  "ts": 123456789,
  "priority": "HIGH",
  "name": "transport_state",
  "value": "STOP",
  "reason": "operator_stop"
}
```

Przykład bezpieczeństwa:

```json
{
  "event": "urgent",
  "ts": 123456790,
  "priority": "SAFETY",
  "name": "sensor_arm_h_limit_right",
  "value": 1,
  "reason": "limit_hit"
}
```

Przykład TAKE / CLAP:

```json
{
  "event": "urgent",
  "ts": 123456800,
  "priority": "MARKER",
  "name": "clap_event",
  "value": 1,
  "take": 12,
  "timecode": "00:00:03:14",
  "reason": "operator_clap"
}
```

### Integracja URGENT ze Snajperem

URGENT ma być obsłużony przez ten sam model co reszta TSP:

```text
SignalBus
  ↓
Caliber
  ↓
Bullet
  ↓
Target
  ↓
Snajper
  ↓
TSP
```

Snajper przy strzale decyduje o klasie sygnału:

```text
FAST    → bufor paczki 10 ms
NORMAL  → bufor paczki 30–50 ms
SLOW    → bufor wolnej diagnostyki
URGENT  → natychmiastowa wysyłka poza cyklem
```

Czyli TSP powinien obsługiwać dodatkową klasę:

```text
lane = "urgent"
```

albo:

```text
priority = "urgent"
```

### Zasady URGENT

```text
URGENT idzie natychmiast.
URGENT nie czeka na kolejną ramkę FAST.
URGENT nie loguje całego systemu.
URGENT loguje zdarzenie i powód.
URGENT powinien mieć priorytet SAFETY / HIGH / MARKER / INFO.
URGENT nie może omijać SignalBus ani Snajpera.
```

### Priorytety URGENT

Proponowane priorytety:

```text
SAFETY  — bezpieczeństwo, krańcówki, awaria, E-STOP
HIGH    — STOP, zmiana transportu, utrata Bridge/Nextion
MARKER  — CLAP, TAKE marker, ważny znacznik czasowy
INFO    — ważna zmiana stanu, która ma być pokazana natychmiast
```

### Relacja FAST i URGENT

Nie przyspieszamy całego protokołu poniżej 10 ms tylko dlatego, że chcemy szybkości.

Model zostaje:

```text
FAST    — stała rytmiczna ramka live co 10 ms
URGENT  — natychmiastowy event poza rytmem
PING    — wolny heartbeat 500–1000 ms
```

Ping nie jest narzędziem płynności. Ping służy do wykrycia, czy klient żyje. Płynność daje FAST, a natychmiastową reakcję daje URGENT.

Docelowe czasy:

```text
URGENT  — natychmiast
FAST    — 10 ms
NORMAL  — 30–50 ms
SLOW    — 250–1000 ms
PING    — 500–1000 ms
HEALTH  — 1000 ms
```

---

## 10. TSP NORMAL — 30–50 ms

Pasmo NORMAL służy do stanu operatorskiego i UI.

Przykłady:

```text
wybrana strona Nextiona
wybrana oś
tryb active_mode
transport_state
przyciski
suwaki
normalne statusy PAR
```

Przykład:

```json
{
  "event": "snajper_packet",
  "lane": "normal",
  "ts": 12345670,
  "values": {
    "active_mode": "LIVE",
    "transport_state": "PLAY",
    "nextion_page": "rrp_main"
  }
}
```

---

## 11. TSP SLOW — diagnostyka

Pasmo SLOW służy do wolnych statusów.

Przykłady:

```text
CPU
RAM
dysk
temperatura
stan SSH
stan Bridge
wersja programu
heartbeat
```

Przykład:

```json
{
  "event": "health",
  "ts": 12345670,
  "cpu": 12,
  "ram_mb": 620,
  "bridge": "OK",
  "ssh": "OK"
}
```

---

## 12. Komendy TSP v1

Minimalny zakres komend:

```text
ping
get_signal
set_signal
get_all_signals
subscribe
unsubscribe
call_action
get_state
```

Przykłady:

```json
{"cmd":"ping"}
```

```json
{"cmd":"get_signal","name":"take_timecode"}
```

```json
{"cmd":"set_signal","name":"nextion_ui_cut","value":1}
```

```json
{"cmd":"subscribe","signals":["rrp_p1_value","rrp_p2_value","axis_0_pulses"]}
```

```json
{"cmd":"call_action","name":"nextion_refresh_page"}
```

---

## 13. Czego TSP nie robi

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

TSP ma być tylko bramą sieciową do istniejącej architektury TARZANA.

---

## 14. Integracja z architekturą TARZANA

Obowiązujący model:

```text
SignalBus = źródło prawdy
Caliber   = ujednolica nazwę sygnału
Bullet    = przygotowuje wartość/payload
Target    = wskazuje cel
Snajper   = strzela / odświeża
Bridge    = fizyczny Nextion / sprzęt
TSP       = sieciowy target Snajpera
```

Aktualna decyzja projektowa: **na start TSP zostaje w jednym pliku w `core`**.

```text
core/tarzanTsp.py
```

Nie robimy od razu dużego folderu ani wielu plików. TSP ma najpierw powstać jako jeden czysty moduł, ale logicznie podzielony w środku na:

```text
TSP lanes            — FAST / NORMAL / SLOW / HEALTH
TSP packet builder   — budowanie paczek ze Snajpera / SignalBus
TSP router           — komendy LAN -> SignalBus / akcje
TSP state            — klienci, subskrypcje, kolejki, ring buffer
TSP Snajper adapter  — target LAN dla Snajpera
```

Dopiero jeśli `core/tarzanTsp.py` urośnie i zacznie być niewygodny, można go rozdzielić na folder:

```text
core/TSP/
  tarzanTspProtocol.py
  tarzanTspRouter.py
  tarzanTspPacketBuilder.py
  tarzanTspState.py
```

Na tym etapie najważniejsze jest, żeby TSP nie stworzył drugiego toru odświeżania. Dlatego integracja ze Snajperem powinna być jako:

```text
target_type = "tsp"
```

albo jako lekki adapter używany przez istniejący model Target/Snajper.

---

## 15. Rola mini PC

Mini PC ma docelowo działać jako:

```text
TARZAN Signal Node
```

Czyli:

```text
mały komputer wykonawczy przy elektronice
bez ciężkiego UI
zawsze dostępny przez SSH
z własnym daemonem systemd
z SignalBus live
z Bridge i Nextionem
z TSP po LAN
```

Przykładowe usługi:

```text
ssh.service             — zawsze aktywny dostęp ratunkowy
tarzan-core.service     — główny runtime TARZANA
tarzan-tsp.service      — serwer TSP / Signal Node
tarzan-x.service        — lokalny ekran X tylko gdy potrzebny
tarzan-par.service      — PAR jako diagnostyka, nie serce systemu
```

---

## 16. Rola PAR i EHR

PAR i EHR nie muszą działać fizycznie na mini PC.

Docelowo:

```text
EHR — duży komputer, edycja choreografii
PAR — klient diagnostyczny, może działać na dużym komputerze albo lokalnie
Mini PC — runtime, sygnały, elektronika, Nextion, TSP
```

PAR może pobierać live sygnały przez TSP.

Mini PC może mieć lokalny PAR tylko awaryjnie lub serwisowo.

---

## 17. Najważniejszy wniosek

TSP to nie nowy system obok TARZANA.

TSP to **sieciowe ramię Snajpera**.

Najkrótsza definicja:

```text
TSP — TARZAN Signal Protocol:
lekki protokół TCP/JSONL, który pozwala dużemu komputerowi sterować i obserwować live SignalBus mini PC, ale całe odświeżanie dalej prowadzi Snajper.
```

Fundament:

```text
SignalBus zostaje źródłem prawdy.
Snajper zostaje dyrygentem.
TSP zostaje targetem LAN.
Mini PC zostaje TARZAN Signal Node.
```

---

## 18. Fundament sygnałów TSP

TSP ma być oparty o centralną mapę sygnałów TARZANA:

```text
core/tarzanZmienneSygnalowe.py
```

Ten plik jest katalogiem sygnałów dla TSP. Szczególnie ważne pola:

```text
nazwa              — nazwa programowa / sprzętowa
kanoniczna_nazwa   — nazwa logiczna używana przez wyższe warstwy
plytka             — PLAY / REC / CNC
pin                — fizyczny pin, jeśli istnieje
kanal              — kanał CNC / wirtualny, jeśli nie ma pinu
typ                — LH / CTR / ANALOG / F / RESERVED
kierunek           — IN / OUT / F / RESERVED
grupa              — STEP_DIR, STEP_CTR, RRP, CZUJNIKI, UI itd.
logika_trybow      — DOZWOLONY / TYLKO_ODCZYT / ZABRONIONY
rola_logiki        — INPUT / OUTPUT / SENSOR / STATUS / UI / SYSTEM
```

Zasada:

```text
TSP nie wymyśla nazw.
TSP nie tworzy ręcznych map.
TSP używa kanoniczna_nazwa tam, gdzie ona istnieje.
```

Jeśli `kanoniczna_nazwa` jest pusta, TSP może użyć `nazwa`, ale powinno to być traktowane jako niższy poziom / fallback.

Przykład:

```text
play_p46_step_ctr_arm_h
kanoniczna_nazwa = axis_arm_h_step
```

Dla TSP ważniejsza jest nazwa logiczna:

```text
axis_arm_h_step
```

a nie nazwa sprzętowa pinu.

---

## 19. Walidacja bezpieczeństwa sygnałów

TSP musi respektować klasyfikację sygnałów z mapy.

```text
DOZWOLONY
TYLKO_ODCZYT
ZABRONIONY
```

Zasada dla komendy `set_signal`:

```text
DOZWOLONY     — można ustawić, jeśli SignalBus i tryb pracy na to pozwalają
TYLKO_ODCZYT  — nie wolno pisać, można tylko odczytać
ZABRONIONY    — nie wolno używać jako sygnału sterującego
```

Przykład odmowy:

```json
{
  "ok": false,
  "error": "write_denied",
  "name": "sensor_light_lux",
  "reason": "TYLKO_ODCZYT"
}
```

TSP nie może pozwolić klientowi LAN przypadkowo sterować sygnałami sprzętowymi, które są czujnikami, magistralami, funkcjami systemowymi albo pinami zarezerwowanymi.

---

## 20. PoKeys i TSP

Konfiguracja PoKeys pozostaje osobną warstwą.

TSP nie zapisuje konfiguracji PoKeys do flash i nie zmienia funkcji pinów.

Obowiązuje zasada:

```text
tarzanPoKeysSetting.py
→ konfiguracja / walidacja sprzętu PoKeys

tarzanTsp.py
→ live komunikacja sygnałowa po LAN
```

TSP może zgłaszać stan PoKeys, np.:

```json
{
  "event": "hardware",
  "pokeys_play": "OK",
  "pokeys_rec": "OK"
}
```

ale nie powinien samodzielnie wykonywać trwałych operacji konfiguracyjnych.

Zapis do flash PoKeys musi pozostać operacją jawną i świadomą.

---

## 21. Panel PAR — TSP CONNECT

PAR powinien dostać osobny panel połączenia:

```text
TSP CONNECT
```

Rola panelu:

```text
połączyć PAR z mini PC / TARZAN Signal Node
pokazać status protokołu
pokazać ping
pokazać liczbę sygnałów
pokazać ostatni pakiet FAST / NORMAL / SLOW
umożliwić subskrypcję live
umożliwić diagnostykę błędów i snapshot debug
```

Przykładowy widok:

```text
TSP CONNECT
────────────────────────
HOST: 192.168.1.26
PORT: 7777

STATUS: CONNECTED
NODE: tarzan
PING: 2 ms
SIGNALS: 124

FAST:   ON / last 8 ms
NORMAL: ON / last 42 ms
SLOW:   ON / last 250 ms

RX ERRORS: 0
DROPPED: 0
QUEUE: 2

[CONNECT]
[DISCONNECT]
[TEST PING]
[SUBSCRIBE LIVE]
[SHOW LAST PACKETS]
[DUMP SNAPSHOT]
[TRACE SIGNAL]
```

TSP CONNECT w PAR nie jest źródłem prawdy. To tylko klient i panel diagnostyczny.

Źródło prawdy zostaje na mini PC:

```text
SignalBus / Snajper / Bridge / TSP server
```

---

## 22. Logi TSP

TSP musi mieć logi, ale nie wolno logować każdego pakietu FAST 10 ms do pliku.

Domyślnie logujemy:

```text
CONNECT
DISCONNECT
RECONNECT
HELLO
SUBSCRIBE
UNSUBSCRIBE
PROTOCOL_ERROR
UNKNOWN_SIGNAL
WRITE_DENIED
CLIENT_TIMEOUT
QUEUE_OVERFLOW
SNAJPER_TARGET_ERROR
SIGNALBUS_WRITE_ERROR
```

Nie logujemy domyślnie:

```text
każdego pakietu FAST
każdej zmiany każdego sygnału
pełnego SignalBus co 10 ms
```

Podstawowe logi:

```text
journalctl -u tarzan-tsp -f
/var/log/tarzan/tsp.log
```

---

## 23. Statystyki zamiast zalewu logów

Dla szybkiego pasma FAST TSP powinien logować statystyki, nie każdy pakiet.

Przykład raz na sekundę:

```text
FAST_STATS clients=1 packets=100 signals=4200 avg_size=380B dropped=0 queue=2
NORMAL_STATS packets=20 signals=180 dropped=0
SLOW_STATS packets=4 signals=22 dropped=0
```

Daje to informację:

```text
czy TSP żyje
czy klient odbiera
czy kolejka rośnie
czy pakiety wypadają
czy tempo jest stabilne
```

bez zalewania plików logami.

---

## 24. Ring buffer debug

TSP powinien mieć bufor kołowy w RAM.

Propozycja:

```text
ostatnie 200 pakietów RX
ostatnie 200 pakietów TX
ostatnie 100 błędów
```

Normalnie bufor nie zapisuje wszystkiego na dysk.

Panel PAR TSP CONNECT może mieć przycisk:

```text
DUMP SNAPSHOT
```

Wtedy TSP zapisuje jednorazowy zrzut:

```text
/var/log/tarzan/tsp_debug_snapshot_YYYY-MM-DD_HHMMSS.jsonl
```

To pozwala debugować problem bez ciągłego logowania wszystkich ramek.

---

## 25. Trace wybranego sygnału

Do debugowania potrzebny jest tryb śledzenia konkretnego sygnału.

Przykład:

```text
TRACE SIGNAL: rrp_p1_value
TRACE SIGNAL: nextion_page
TRACE SIGNAL: axis_arm_h_pulses
```

TSP zapisuje wtedy tylko wybrane sygnały przez krótki czas, np. 10–30 sekund.

Przykład wpisu:

```json
{"ts":12345670,"lane":"FAST","signal":"rrp_p1_value","value":401}
{"ts":12345680,"lane":"FAST","signal":"rrp_p1_value","value":402}
```

To jest właściwe do debugowania, bo nie zapisuje całego systemu.

---

## 26. Usługi systemd na mini PC

Docelowy model usług:

```text
ssh.service
  zawsze aktywny kanał ratunkowy

tarzan-core.service
  główny runtime TARZANA / SignalBus / sprzęt

tarzan-tsp.service
  serwer TSP / komunikacja LAN

tarzan-x.service
  lokalny ekran X, tylko gdy potrzebny

tarzan-par.service
  lokalny PAR diagnostyczny, nie serce systemu
```

Najważniejsza zasada:

```text
CORE działa zawsze.
TSP działa zawsze, jeśli mini PC ma być Signal Node.
PAR jest tylko podglądem / diagnostyką.
```

PAR nie może być głównym procesem systemu.

---

## 27. Tryb pracy mini PC

Mini PC powinien docelowo działać jako:

```text
TARZAN Signal Node
```

Czyli:

```text
bez ciężkiego pulpitu
zawsze dostępny po SSH
uruchamia core po restarcie
trzyma SignalBus live
obsługuje PoKeys / Nextion / elektronikę
wystawia TSP po kablu LAN
pozwala PAR/EHR działać jako klienci
```

Lokalna grafika X/Openbox zostaje tylko jako opcja serwisowa:

```text
PAR lokalny
test kamery
proste okna diagnostyczne
```

---

## 28. Minimalny zakres implementacji TSP v1

Etap 1 powinien zawierać:

```text
core/tarzanTsp.py
```

W nim:

```text
stałe protokołu
lane FAST / NORMAL / SLOW / HEALTH
budowanie pakietów JSONL
komendy ping / hello
get_signal
set_signal z walidacją DOZWOLONY / TYLKO_ODCZYT / ZABRONIONY
get_signal_catalog
subscribe / unsubscribe
ring buffer debug
statystyki komunikacji
adapter Snajpera target_type=tsp
```

Etap 1 nie musi jeszcze mieć pełnego UI PAR.

Etap 2:

```text
PAR TSP CONNECT
```

Etap 3:

```text
systemd tarzan-tsp.service
autostart Signal Node
pełne logi i snapshoty
```

---

## 29. Ostateczna zasada projektowa

TSP ma być protokołem live opartym o istniejącą mapę sygnałów TARZANA.

Nie wolno budować go jako nowego świata.

Obowiązuje:

```text
tarzanZmienneSygnalowe.py  — katalog sygnałów
kanoniczna_nazwa           — nazwa logiczna
SignalBus                  — źródło prawdy
Snajper                    — dyrygent odświeżania
TSP                        — target LAN Snajpera
PAR TSP CONNECT            — panel klienta i diagnostyki
```

Najkrócej:

```text
TSP = SignalBus live po LAN, dyrygowany przez Snajpera.
```

