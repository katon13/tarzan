# TARZAN LKS-N5 — ETAP 12B: sprzątanie po testach widocznych

## Cel

Testy widoczne uruchamiane po kliknięciu kontrolki `status_main` mają być czytelne dla operatora, ale po zakończeniu nie mogą zostawiać przypadkowo zapalonych wyjść ani śmieci na wyświetlaczach.

Zasada operatorska:

```text
klik w element -> ten element jest testowany
w czasie testu może mrugać / pokazywać TEST
po teście wszystko wraca do spokojnego stanu
OK   -> kontrolka LKS-N5 zielona
FAIL -> kontrolka LKS-N5 szara
```

## Zmiany

### LCD 1602

Kontrolka `lcd_1602` oznacza zbiorczy test dwóch LCD:

```text
LCD PLAY
LCD REC
```

Podczas testu widocznego LCD pokazuje:

```text
LKS-N5 PLAY / TEST LCD
LKS-N5 REC  / TEST LCD
```

Po poprawnym teście oba LCD zostają w stanie końcowym:

```text
BEZ BLEDOW
GOTOWE
```

Jeżeli test któregoś LCD nie przejdzie, kontrolka `lcd_1602` wraca na szaro.

### Matrix LED

Podczas testu matrix pokazuje krótko:

```text
TEST
OK
wzór kontrolny
```

Po teście matrix jest czyszczony i gaśnie.

### F1-F4 LED

Podczas testu LED-y F1-F4 mrugają po kolei.

Po teście wszystkie LED-y są gaszone także wtedy, gdy test przerwie się błędem w połowie.

## Czego nie zmieniamy

```text
zero STEP
zero DIR
zero ENABLE
zero ruchu osi
zero pełnej diagnostyki w pętli
zero runtime zależności od tarzanMiniPcSandbox.py
```

Sandbox nadal jest tylko źródłem wiedzy historycznej. Testery LKS-N5 są suwerenne.

## Testy ręczne

```bash
cd /opt/tarzan
python3 -m core.TSP.tarzanTspLksHardwareTests --component lcd_1602 --visible
python3 -m core.TSP.tarzanTspLksHardwareTests --component matrix_led --visible
python3 -m core.TSP.tarzanTspLksHardwareTests --component f_led --visible
```

Oczekiwane:

```text
LCD PLAY i LCD REC: TEST -> BEZ BLEDOW / GOTOWE
Matrix LED: TEST/OK/wzór -> gaśnie
LED F1-F4: mrugają -> gasną
```
