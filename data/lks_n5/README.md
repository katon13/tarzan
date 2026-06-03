# TARZAN LKS-N5 — data/lks_n5

Ten katalog przechowuje dane robocze LKS-N5 generowane na miniPC.

Najważniejszy plik ETAPU 9:

```text
lks_n5_hardware_inventory.json
```

Plik jest generowany komendą:

```bash
python3 -m core.TSP.tarzanTspLksInventory --write data/lks_n5/lks_n5_hardware_inventory.json --print
```

To jest inwentaryzacja read-only. Nie wysyła STEP, DIR, ENABLE i nie rusza osi.
