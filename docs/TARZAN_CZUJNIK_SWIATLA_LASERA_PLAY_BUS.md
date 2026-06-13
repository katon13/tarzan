# TARZAN — czujnik światła lasera na PLAY BUS/I2C

## Co to jest

Obecnie fizycznie podpięty jest **jeden czujnik światła od lasera**.

Ten czujnik ma być traktowany w systemie jako:

```text
light_laser
```

Nie jest to drugi czujnik światła z zespolonej płytki. Drugi czujnik będzie dopięty później i na razie nie wolno go wymagać w testach.

---

## Gdzie jest podpięty

Czujnik światła lasera jest podpięty do płytki:

```text
PLAY / PLAYER
```

Tor podłączenia:

```text
PLAY → pionowe złącze BUS → BUS/I2C → czujnik światła BH1750 / GY-302
```

W praktyce system ma go szukać na PLAY, nie na REC.

---

## Adres czujnika

Test bezpośredni PoKeysLib potwierdził adres:

```text
0x5C
```

Adres `0x23` nie odpowiedział.

Potwierdzony wynik testu:

```text
BUS SCAN: FOUND 0x5C
BH1750 0x5C:
power: 1
reset: 1
mode: 1
data: [0, 1]
OK raw=1 lux=0.8333333333333334
```

Czyli czujnik fizycznie działa i odpowiada.

---

## Ważna zasada adresowania

Dla tego toru PoKeysLib adres ma być używany jako:

```text
0x5C
```

Nie wolno go przesuwać jako:

```text
0x5C << 1 = 0xB8
```

Stary sandbox czytał ten czujnik bez przesunięcia adresu.

Sekwencja odczytu BH1750 / GY-302:

```text
PK_I2CWrite(0x5C, [0x01])   # power on
PK_I2CWrite(0x5C, [0x07])   # reset
PK_I2CWrite(0x5C, [0x20])   # one-time high resolution mode
PK_I2CRead(0x5C, 2)         # odczyt 2 bajtów
```

Przeliczenie:

```text
raw = (byte0 << 8) | byte1
lux = raw / 1.2
```

---

## Jak ma być widziany w LKS-N5

Docelowo w runtime:

```text
light_laser = PLAY BH1750/GY-302 0x5C real read OK
```

Jeżeli `light_laser` odpowiada realnym odczytem `raw/lux`, wtedy:

```text
i2c_bus = OK
```

---

## Drugi czujnik światła

W systemie będą dwa takie same czujniki światła:

```text
1. light_laser
   - obecnie fizycznie podpięty
   - PLAY / BUS/I2C
   - adres 0x5C
   - ten testujemy teraz

2. light_bh1750 / drugi czujnik światła
   - będzie na zespolonej płytce / PoKSyg
   - teraz NIE jest fizycznie podpięty
   - na razie ma być optional / NOT_CONNECTED
```

Brak drugiego czujnika nie może powodować awarii całej magistrali I2C.

---

## Błędna logika do poprawienia

Aktualny runtime wcześniej mylił `light_laser`, bo testował inny tor:

```text
light_laser → REC / TSL25911 / adres 0x29
```

To nie jest obecny fizyczny czujnik lasera.

Dla obecnego etapu poprawna logika to:

```text
light_laser → PLAY / BH1750-GY302 / adres 0x5C
```

---

## Pliki do patcha runtime

Do poprawienia przy patchu:

```text
core/tarzanPoKeys.py
core/tarzanHardwareBridge.py
```

Zakres poprawki:

```text
- nie przesuwać adresu I2C przez << 1 dla PoKeysLib
- czytać BH1750 na PLAY pod adresem 0x5C
- przypisać ten odczyt do light_laser
- light_bh1750 zostawić optional / NOT_CONNECTED
- i2c_bus uznać za OK, jeśli light_laser ma realny odczyt
```

Nie ruszać przy tym:

```text
PoKeys ABC
F-LED
Matrix LED
Nextion 5
Nextion 7
boot/progress
map pinów REC
```

---

## Status

```text
Sprzęt: potwierdzony
PLAY: potwierdzony
Adres: 0x5C potwierdzony
Odczyt lux: potwierdzony
Patch runtime: do zrobienia
```

Szacunkowy stan etapu:

```text
75%
```
