# TARZAN LKS-N5 — ETAP 13 HOTFIX 7
## intro_status sterowany przez Nextion, bez wymuszania status_main z Pythona

## Cel

Dostosowanie końcówki sekwencji startowej do rzeczywistej struktury HMI Nextion 5.

Poprawna kolejność stron:

```text
boot_intro
boot_loading
boot_linux
boot_services
boot_hardware
boot_test
ready_main
intro_status
status_main
```

## Najważniejsza zasada

`intro_status` jest stroną animowaną lokalnie po stronie Nextiona.
Python ma tylko wejść na stronę:

```text
page intro_status
```

a następnie poczekać. Nie wysyła tam tekstów, progressu ani `page status_main`.

W aktualnym HMI `intro_status` ma:

```text
p_anim
va_anim
tm_anim
```

Timer `tm_anim` przełącza obrazki i na końcu sam wykonuje:

```text
page status_main
```

## Co zmienia patch

Przed patchem Python robił za dużo:

```text
page ready_main
page intro_status
page status_main
set statuses
```

Po patchu:

```text
page ready_main
page intro_status
czekanie na animację Nextiona
set statuses
```

Czyli `status_main` jest uruchamiany przez Nextion, nie przez Python.
Python tylko ustawia 30 kontrolek, gdy animacja już powinna być zakończona.

## Bezpieczeństwo

Patch nie zmienia diagnostyki urządzeń.
Patch nie dotyka STEP/DIR/ENABLE.
Patch nie uruchamia osi.
Patch dotyczy tylko kolejności i sposobu wejścia na strony HMI.

## Test

```bash
cd /opt/tarzan
sudo systemctl stop tarzan-tsp-lks-n5.service
git pull origin main
python3 -m py_compile core/TSP/tarzanTspLksBootProgress.py
python3 -m core.TSP.tarzanTspLksNextion5 --dry-run --boot-check
sudo systemctl start tarzan-tsp-lks-n5.service
```

W dry-run oczekiwane jest:

```text
page ready_main
page intro_status
linux_sys.val=...
...
```

Nie powinno być wymuszonego `page status_main` po `intro_status`.
Na fizycznym Nextionie `intro_status` sam przejdzie do `status_main` swoim timerem.
