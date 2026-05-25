# TARZAN — tarzanMiniPC i TSP

## 1. Nazwa maszyny

W projekcie TARZAN przyjmujemy stałą nazwę mini komputera wykonawczego:

```text
tarzanMiniPC
```

To jest nazwa maszyny znajdującej się przy elektronice TARZANA.

## 2. Rola systemowa

`tarzanMiniPC` pełni rolę:

```text
TARZAN Signal Node
```

Czyli jest wykonawczym węzłem sygnałowym TARZANA. Jego zadaniem jest obsługa warstwy live przy elektronice:

```text
SignalBus
Snajper
Bridge
Nextion
czujniki
PoKeys / USB / COM
elektronika
logi runtime
TSP Server
```

`tarzanMiniPC` nie jest głównym komputerem operatorskim ani głównym komputerem edycji EHR. Ma działać lekko, stabilnie i blisko sprzętu.

## 3. Adres IP

Stały adres IP dla `tarzanMiniPC`:

```text
tarzanMiniPC = 192.168.1.26
```

Domyślnie to na tym komputerze uruchamiany jest serwer TSP.

## 4. Duży komputer operatorski

Duży komputer operatorski nazywamy:

```text
tarzanStacja
```

Adres IP:

```text
tarzanStacja = 192.168.1.12
```

Rola `tarzanStacja`:

```text
PAR
EHR
podgląd
konfiguracja
sterowanie operatorskie
TSP Client
```

## 5. Model TSP

TSP, czyli TARZAN Signal Protocol, działa w tym układzie tak:

```text
tarzanStacja / duży PC / klient
        ↓ TCP / JSONL / LAN
tarzanMiniPC / Signal Node / serwer
        ↓
SignalBus / Snajper / Bridge / Nextion / elektronika
```

Czyli:

```text
tarzanMiniPC  = TSP Server
tarzanStacja  = TSP Client
```

Domyślny port TSP:

```text
TSP_PORT = 7777
```

## 6. Stałe konfiguracyjne TSP

W module TSP należy przyjmować następujące ustawienia domyślne:

```python
TSP_MINI_PC_HOST = "192.168.1.26"   # tarzanMiniPC — TSP Server / Signal Node
TSP_STACJA_HOST = "192.168.1.12"    # tarzanStacja — TSP Client / PAR / EHR
TSP_PORT = 7777

TSP_SERVER_NODE_NAME = "tarzanMiniPC"
TSP_CLIENT_NODE_NAME = "tarzanStacja"
```

## 7. Główna zasada architektury

TSP nie jest osobnym systemem odświeżania.

Obowiązuje zasada:

```text
SignalBus = źródło prawdy
Snajper   = dyrygent odświeżania
TSP       = sieciowy target Snajpera
```

Nie budujemy równoległego toru:

```text
SignalBus → TSP osobno
SignalBus → PAR osobno
SignalBus → Nextion osobno
```

Docelowo ma być:

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
TSP / PAR / Nextion
```

## 8. Rytm komunikacji TSP

Podstawowy rytm TARZANA zostaje zgodny z projektem:

```text
CZAS_PROBKOWANIA_MS = 10 ms
```

Dla TSP przyjmujemy:

```text
FAST    = 10 ms
NORMAL  = 30–50 ms
SLOW    = 250–1000 ms
HEALTH  = 1000 ms
PING    = 500–1000 ms
URGENT  = natychmiast, poza rytmem FAST
```

Ważne:

```text
FAST packet ≠ ping
```

FAST przenosi dane live. Ping służy tylko do sprawdzania, czy druga strona żyje.

## 9. URGENT EVENT

TSP ma mieć kanał natychmiastowych zdarzeń:

```text
URGENT EVENT
```

URGENT nie czeka na najbliższą paczkę FAST 10 ms.

Przykłady zdarzeń URGENT:

```text
STOP
E-STOP
LIMIT HIT
zmiana MODE
zmiana transport_state
PAGE_CHANGED z Nextiona / sendme
RRP_AXIS_CHANGED
CLAP / TAKE marker
BRIDGE_ERROR
NEXTION_DISCONNECT
```

Przykład pakietu:

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

## 10. Logi komunikacji

TSP musi mieć logi, ale nie wolno logować każdego pakietu FAST 10 ms.

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
URGENT EVENT
```

Nie logujemy domyślnie:

```text
każdego pakietu FAST
każdej zmiany każdego sygnału
pełnego SignalBus co 10 ms
```

Dla FAST logujemy statystyki, np. raz na sekundę:

```text
FAST_STATS clients=1 packets=100 signals=4200 avg_size=380B dropped=0 queue=2
```

## 11. Panel PAR TSP CONNECT

W PAR docelowo powinien powstać panel:

```text
TSP CONNECT
```

Rola panelu:

```text
połączenie z tarzanMiniPC
status TSP
ping
ostatni FAST / NORMAL / SLOW / HEALTH
liczba odebranych sygnałów
błędy RX/TX
trace wybranego sygnału
snapshot debug
```

Przykładowy układ:

```text
TSP CONNECT
────────────────────────
HOST: 192.168.1.26
PORT: 7777

STATUS: CONNECTED
NODE: tarzanMiniPC
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

## 12. Podstawowe komendy testowe

Na `tarzanMiniPC`:

```bash
cd /opt/tarzan
source .venv/bin/activate
python -m core.TSP.tarzanTsp server
```

Na `tarzanStacja`:

```powershell
cd X:\tarzan; .\.venv\Scripts\activate; python -m core.TSP.tarzanTsp client --host 192.168.1.26 --port 7777 --smoke --seconds 2
```

Oczekiwany wynik:

```text
TSP CLIENT SMOKE OK
errors=0
```

## 13. Podsumowanie

Stałe ustalenie projektowe:

```text
tarzanMiniPC = 192.168.1.26 = TARZAN Signal Node = TSP Server
tarzanStacja = 192.168.1.12 = komputer operatorski = TSP Client
```

Najkrócej:

```text
TSP łączy tarzanStacja z tarzanMiniPC.
tarzanMiniPC trzyma live SignalBus i elektronikę.
tarzanStacja pokazuje, steruje i konfiguruje.
Snajper dalej pozostaje dyrygentem odświeżania.
```
