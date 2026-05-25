# TARZAN — tarzanMiniPC: krótkie włączenie Wi‑Fi

## Stan bazowy

`tarzanMiniPC` pracuje obecnie po kablu LAN.

```text
LAN / enp2s0      = główne połączenie serwisowe
SSH / PuTTY       = główny dostęp
Wi‑Fi / wlp3s0    = wyłączone programowo, zostawione na później
Bluetooth         = zostawiony na później
```

Nie wyłączać LAN, dopóki Wi‑Fi nie będzie pewnie połączone.

---

## 1. Włączenie Wi‑Fi

Na `tarzanMiniPC` przez PuTTY:

```bash
nmcli radio wifi on
```

Sprawdzenie:

```bash
nmcli radio wifi
```

Oczekiwany wynik:

```text
enabled
```

---

## 2. Skanowanie sieci

```bash
nmcli device wifi rescan ifname wlp3s0
nmcli device wifi list
```

Jeśli Wi‑Fi działa poprawnie, lista pokaże dostępne sieci, np.:

```text
SSID      SIGNAL  SECURITY
FLIZAKA   90      WPA2
```

---

## 3. Połączenie z siecią Wi‑Fi

```bash
nmcli device wifi connect "NAZWA_SIECI" password "HASLO_WIFI" ifname wlp3s0
```

Przykład:

```bash
nmcli device wifi connect "FLIZAKA" password "HASLO_WIFI" ifname wlp3s0
```

Sprawdzenie:

```bash
nmcli device status
ip a
```

---

## 4. Jeśli Wi‑Fi znowu nie skanuje

Sprawdzenie błędów:

```bash
dmesg | grep -i iwlwifi | tail -40
```

Ręczne przeładowanie sterownika:

```bash
modprobe -r iwldvm iwlwifi
sleep 2
modprobe iwlwifi
sleep 3
nmcli device wifi rescan ifname wlp3s0
nmcli device wifi list
```

---

## 5. Wyłączenie Wi‑Fi, jeśli przeszkadza przy starcie

```bash
nmcli radio wifi off
```

Sprawdzenie:

```bash
nmcli radio wifi
```

Oczekiwany wynik:

```text
disabled
```

---

## 6. Obecna poprawka sterownika

Na `tarzanMiniPC` zapisano plik:

```text
/etc/modprobe.d/tarzan-iwlwifi.conf
```

Zawartość:

```text
options iwlwifi 11n_disable=1 power_save=0
options iwldvm force_cam=1
```

Ta poprawka pomaga karcie:

```text
Intel Centrino Advanced-N 6235
sterownik: iwlwifi / iwldvm
```

---

## 7. Zasada bezpieczeństwa

Nie ruszać `enp2s0`, dopóki PuTTY działa po LAN.

```text
enp2s0 = kabel LAN / SSH / dostęp ratunkowy
wlp3s0 = Wi‑Fi / opcjonalnie później
```

Najpierw połączyć Wi‑Fi, sprawdzić IP i dopiero wtedy rozważać pracę bez kabla.
