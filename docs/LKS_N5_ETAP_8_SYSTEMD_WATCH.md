# TARZAN LKS-N5 — ETAP 8 — systemd i praca ciągła

## Cel

ETAP 8 uruchamia TSP razem z LKS-N5 jako usługę systemd na miniPC.

Kontrakt zostaje bez zmian:

- LKS-TTY zostaje.
- LKS-N5 działa równolegle.
- Nextion 5 pokazuje stan systemu.
- miniPC diagnozuje.
- Nextion 5 nie steruje ruchem.
- Brak STEP, DIR, ENABLE i ruchu osi.

## Dodane pliki

- `config/systemd/tarzan-tsp-lks-n5.service`
- `docs/LKS_N5_ETAP_8_SYSTEMD_WATCH.md`

## Poprawka shutdown

W `core/TSP/tarzanTspServer.py` poprawiono kolejność zamykania LKS-N5:

1. ustawienie flagi `_stopping`,
2. zatrzymanie pętli serwera,
3. wyczyszczenie dirty flag LKS-N5,
4. join wątków `accept` i `lane`,
5. dopiero potem zamknięcie portu serial LKS-N5.

To usuwa fałszywy warning przy `CTRL+C`/systemd stop:

```text
Bad file descriptor
```

## Instalacja usługi na miniPC

```bash
cd /opt/tarzan
sudo cp config/systemd/tarzan-tsp-lks-n5.service /etc/systemd/system/tarzan-tsp-lks-n5.service
sudo systemctl daemon-reload
sudo systemctl enable tarzan-tsp-lks-n5.service
sudo systemctl start tarzan-tsp-lks-n5.service
```

## Kontrola

```bash
sudo systemctl status tarzan-tsp-lks-n5.service --no-pager
journalctl -u tarzan-tsp-lks-n5.service -n 80 --no-pager
```

## Stop / restart

```bash
sudo systemctl stop tarzan-tsp-lks-n5.service
sudo systemctl restart tarzan-tsp-lks-n5.service
```

## Oczekiwany efekt

- TSP startuje na `0.0.0.0:7777`.
- LKS-TTY działa.
- LKS-N5 startuje na porcie CP2102.
- Nextion 5 przechodzi na status systemowy.
- Serwis wstaje po restarcie miniPC.
- Zatrzymanie usługi nie generuje ostrzeżenia `Bad file descriptor`.
