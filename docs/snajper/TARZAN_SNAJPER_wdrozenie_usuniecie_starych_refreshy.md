# TARZAN_SNAJPER — miejsca usunięcia starego odświeżania i podłączenia Snajpera

Ten dokument opisuje **co usunąć**, **co zastąpić** i **gdzie podłączyć** nowy model:

```txt
core/tarzanSnajper.py
```

Zasada główna:

```txt
STRUKTURA → pełny render tylko przy zmianie struktury
WARTOŚĆ / POZYCJA / STATUS → TARZAN_SNAJPER
```

Snajper nie robi pętli.  
Snajper nie skanuje celów.  
Snajper jest wywoływany przez akcję, która i tak się dzieje: zmianę sygnału, zmianę wartości, zmianę pozycji, zmianę statusu.

---

# 1. Nowy plik

## Plik

```txt
core/tarzanSnajper.py
```

Ten plik już jest przygotowany jako osobny moduł.

Zawiera:

```txt
TarzanSnajper
TarzanSnajperTarget
TkWidgetSnajperAdapter
TkCanvasSnajperAdapter
NextionPhysicalSnajperAdapter
DEFAULT_TARZAN_SNAJPER_SIGNAL_MAP
DEFAULT_TARZAN_SNAJPER_TARGETS
create_default_tarzan_snajper()
```

Nie zmienia on istniejących plików sam z siebie.  
Trzeba go podłączyć w miejscach opisanych niżej.

---

# 2. editor/PAR/tarzanParApp.py

## Cel zmiany

Usunąć stary model:

```txt
nextion_tick → bridge.poll → bridge.sync → nextion_refresh_previews
```

Zastąpić go:

```txt
nextion_snajper_tick → bridge.poll → bridge.flush_snajper_commands
```

Tick nie odświeża UI.  
Tick tylko wypycha gotowe komendy Snajpera do fizycznego Nextiona.

---

## USUNĄĆ

W pliku:

```txt
editor/PAR/tarzanParApp.py
```

usunąć całą metodę:

```py
@profile_method("PAR_APP.nextion_tick")
def nextion_tick(self):
    try:
        self.bridge.poll()
        self.bridge.sync(force=False)
        if hasattr(self.panels, "nextion_refresh_previews"):
            self.panels.nextion_refresh_previews()
    except Exception as exc:
        if hasattr(self.bus, "log"):
            self.bus.log("PAR_ERROR", f"Nextion Tick Error: {exc}")
    self.after(50, self.nextion_tick)
```

Usunąć też każde odwołanie:

```py
self.after(50, self.nextion_tick)
```

oraz:

```py
self.nextion_tick
```

---

## DODAĆ

W tym samym pliku dodać:

```py
@profile_method("PAR_APP.nextion_snajper_tick")
def nextion_snajper_tick(self):
    try:
        self.bridge.poll()
        if hasattr(self.bridge, "flush_snajper_commands"):
            self.bridge.flush_snajper_commands()
    except Exception as exc:
        if hasattr(self.bus, "log"):
            self.bus.log("PAR_ERROR", f"Nextion Snajper Tick Error: {exc}")

    self.after(50, self.nextion_snajper_tick)
```

Start pętli zmienić na:

```py
self.after(50, self.nextion_snajper_tick)
```

---

## W tej metodzie NIE WOLNO mieć

```py
self.panels.nextion_refresh_previews()
widget.refresh()
canvas.delete("all")
refresh_axis_cards()
_refresh_all()
```

---

# 3. editor/PAR/tarzanParPanels.py

## Cel zmiany

Ten plik ma być miejscem podłączenia:

```txt
SignalBus → TarzanSnajper.fire_from_signal(...)
```

Nie może już robić pełnego refreshu jako reakcji na pojedynczą wartość.

---

## DODAĆ IMPORTY

Na górze pliku dodać:

```py
from core.tarzanSnajper import (
    create_default_tarzan_snajper,
    TkWidgetSnajperAdapter,
    TkCanvasSnajperAdapter,
    NextionPhysicalSnajperAdapter,
)
```

---

## DODAĆ W __init__

W klasie paneli PAR, w `__init__`, dodać:

```py
self.tarzan_snajper = create_default_tarzan_snajper()

self.snajper_tk_adapter = TkWidgetSnajperAdapter()
self.snajper_canvas_adapter = TkCanvasSnajperAdapter()

self.tarzan_snajper.register_adapter("par_tkinter", self.snajper_tk_adapter)
self.tarzan_snajper.register_adapter("canvas_preview", self.snajper_canvas_adapter)

if hasattr(self.app, "bridge"):
    self.tarzan_snajper.register_adapter(
        "physical_nextion",
        NextionPhysicalSnajperAdapter(self.app.bridge),
    )

self.nextion_ui_cut = False
```

Jeżeli `self.app.bridge` nie istnieje jeszcze w momencie `__init__`, rejestrację adaptera `physical_nextion` zrobić po utworzeniu bridge’a.

---

## STARE — USUNĄĆ Z TORU DYNAMICZNEGO

Jeżeli istnieje metoda:

```py
def nextion_refresh_previews(self):
    ...
    widget.refresh()
```

nie może być wywoływana cyklicznie.

Usunąć każde cykliczne wywołanie:

```py
self.nextion_refresh_previews()
```

albo:

```py
self.panels.nextion_refresh_previews()
```

Nie przenosić tego do wolniejszego ticka.

---

## ZASTĄPIĆ OBSŁUGĘ ZMIANY SYGNAŁU

Stary model bywa taki:

```py
def _on_bus_signal_change(self, name, state):
    self.rows.set_value(name, state.value)
    self.refresh_axis_cards()
```

albo:

```py
def _on_bus_signal_change(self, name, state):
    self.rows.set_value(name, state.value)
```

Nowy model:

```py
def _on_bus_signal_change(self, name, state):
    value = state.value

    self.rows.set_value(name, value)

    if name == "nextion_ui_cut":
        self.set_nextion_ui_cut(bool(int(value)))
        return

    self.tarzan_snajper.fire_from_signal(name, value)
```

Jeżeli callback dostaje już samo `value`, a nie `state`, użyć:

```py
def _on_bus_signal_change(self, name, value):
    self.rows.set_value(name, value)

    if name == "nextion_ui_cut":
        self.set_nextion_ui_cut(bool(int(value)))
        return

    self.tarzan_snajper.fire_from_signal(name, value)
```

---

## USUNĄĆ DYNAMICZNE REFRESH_AXIS_CARDS

Nie wolno odpalać przy pojedynczej wartości:

```py
self.refresh_axis_cards()
```

Nie wolno odpalać przy pojedynczej wartości:

```py
self.refresh_axis_card(key)
```

Zamiast tego zarejestrować konkretny widget jako cel Snajpera:

```py
self.snajper_tk_adapter.register_widget(
    "par_rrp",
    "p1_value_label",
    self.p1_value_label,
)
```

i wtedy Snajper zrobi:

```py
self.p1_value_label.configure(text=value)
```

---

## PRZYKŁAD REJESTRACJI CELÓW TKINTER

Tam, gdzie tworzony jest licznik P1:

```py
self.p1_value_label = ttk.Label(parent, text="0")
self.snajper_tk_adapter.register_widget(
    "par_rrp",
    "p1_value_label",
    self.p1_value_label,
)
```

Dla P2:

```py
self.p2_value_label = ttk.Label(parent, text="0")
self.snajper_tk_adapter.register_widget(
    "par_rrp",
    "p2_value_label",
    self.p2_value_label,
)
```

Dla UI CUT statusu:

```py
self.ui_cut_status_label = ttk.Label(parent, text="UI ON")
self.snajper_tk_adapter.register_widget(
    "nextion_panel",
    "ui_cut_status_label",
    self.ui_cut_status_label,
)
```

---

## DODAĆ OBSŁUGĘ UI CUT

```py
def set_nextion_ui_cut(self, enabled: bool) -> None:
    self.nextion_ui_cut = bool(enabled)

    if self.nextion_ui_cut:
        # UI CUT odcina lokalny preview.
        # Logi zostają.
        pass

    for widget in getattr(self, "nextion_preview_widgets", {}).values():
        if hasattr(widget, "set_ui_cut"):
            widget.set_ui_cut(self.nextion_ui_cut)
```

---

# 4. editor/PAR/tarzanNextionPreview.py

## Cel zmiany

Canvas preview nie może robić pełnego repaintu przy zmianie wartości.

Stary tor:

```txt
t_p1_val zmienione → refresh() → canvas.delete("all") → render całej strony
```

Nowy tor:

```txt
t_p1_val zmienione → update_component(...) → canvas.itemconfigure(jeden item)
```

---

## DODAĆ W __init__

```py
self._snajper_canvas_items = {}
self.ui_cut = False
```

---

## DODAĆ update_component

```py
def update_component(self, page: str, component: str, prop: str, value) -> None:
    if self.ui_cut:
        return

    if page != self.current_page_id:
        return

    key = f"{page}.{component}.{prop}"
    item_id = self._snajper_canvas_items.get(key)

    if item_id is None:
        return

    if prop in {"txt", "text", "val", "state"}:
        self.screen_canvas.itemconfigure(item_id, text=str(value))
        return

    if prop == "coords":
        if isinstance(value, (list, tuple)):
            self.screen_canvas.coords(item_id, *value)
        return
```

---

## DODAĆ set_ui_cut

```py
def set_ui_cut(self, enabled: bool) -> None:
    self.ui_cut = bool(enabled)

    self.screen_canvas.delete("all")
    self._snajper_canvas_items.clear()

    if self.ui_cut:
        self.screen_canvas.create_text(
            20,
            20,
            anchor="nw",
            text="NEXTION_UI_CUT — preview OFF, dane działają",
            fill="#00ff66",
            font=("Segoe UI", 14, "bold"),
        )
```

---

## ZMIENIĆ REJESTRACJĘ ITEMÓW CANVAS

Stary kod:

```py
self.screen_canvas.create_text(
    sx + sw // 2,
    sy + sh // 2,
    text=str(int(value)),
    fill="#ffffff",
    font=("Segoe UI", max(12, s(28)), "bold"),
)
```

Nowy kod:

```py
item_id = self.screen_canvas.create_text(
    sx + sw // 2,
    sy + sh // 2,
    text=str(int(value)),
    fill="#ffffff",
    font=("Segoe UI", max(12, s(28)), "bold"),
)

self._snajper_canvas_items[f"rrp_main.{label}.txt"] = item_id
```

Dla RRP powinny powstać klucze:

```txt
rrp_main.t_p1_val.txt
rrp_main.t_p2_val.txt
```

---

## GDZIE WOLNO ZOSTAWIĆ canvas.delete("all")

Wolno zostawić tylko w:

```txt
pierwszy render strony
zmiana strony
zmiana struktury layoutu
pełna przebudowa Canvas po zmianie struktury
UI CUT włączony/wyłączony
```

Nie wolno przy:

```txt
t_p1_val
t_p2_val
DIR
SENS
licznik osi
status
sensor
timecode
```

---

# 5. hardware/tarzanNextion/bridge.py

## Cel zmiany

Bridge nie robi pełnego syncu wartości jako modelu dynamicznego.  
Bridge ma przyjmować kolejkę Snajpera i wysyłać tylko delty.

---

## DODAĆ W __init__

```py
from collections import deque
```

W `__init__`:

```py
self._snajper_queue = deque()
self._snajper_sent_cache = {}
```

---

## DODAĆ queue_snajper_command

```py
def queue_snajper_command(self, scope: str, component: str, prop: str, value) -> None:
    value = str(value)
    key = f"{scope}.{component}.{prop}"

    if self._snajper_sent_cache.get(key) == value:
        return

    self._snajper_sent_cache[key] = value
    self._snajper_queue.append((scope, component, prop, value))
```

---

## DODAĆ flush_snajper_commands

```py
def flush_snajper_commands(self) -> None:
    while self._snajper_queue:
        scope, component, prop, value = self._snajper_queue.popleft()

        # scope odpowiada stronie Nextiona, np. rrp_main / take_main / level_xyz.
        # Wysyłać tylko gdy dana strona jest aktywna.
        if not self._is_scope_active(scope):
            continue

        if prop in {"txt", "text"}:
            payload = cmd_text(component, value)
        elif prop == "val":
            payload = command_bytes(f"{component}.val={value}")
        elif prop == "pic":
            payload = command_bytes(f"{component}.pic={value}")
        else:
            continue

        self.device.send_raw(payload)
```

Jeżeli bridge obsługuje wiele ekranów `nextion_5` / `nextion_7`, zamiast `self.device` użyć aktualnego mechanizmu urządzeń z bridge’a.

---

## DODAĆ pomocnicze sprawdzenie strony

```py
def _is_scope_active(self, scope: str) -> bool:
    active_page = None

    if hasattr(self, "active_pages"):
        active_page = self.active_pages.get("nextion_7")

    if active_page is None:
        return True

    return active_page == scope
```

---

## DODAĆ OBSŁUGĘ sys:ui_cut / set:ui_cut

W `poll()` w pętli wiadomości dodać:

```py
if msg.startswith("sys:ui_cut="):
    enabled = msg.split("=", 1)[1].strip() == "1"
    self.bus.force_signal("nextion_ui_cut", 1 if enabled else 0, source="NEXTION")
    handled_text = True
    continue

if msg.startswith("set:ui_cut="):
    enabled = msg.split("=", 1)[1].strip() == "1"
    self.bus.force_signal("nextion_ui_cut", 1 if enabled else 0, source="NEXTION")
    if tfd_state:
        tfd_state.update_meta(nextion_ui_cut=enabled)
    handled_text = True
    continue
```

---

# 6. editor/TFD/tfd_state.py albo plik metadanych title/director

## Cel zmiany

`nextion_ui_cut` ma być zapisany razem z:

```txt
title
director
```

---

## DODAĆ W __init__

```py
self.nextion_ui_cut = False
```

---

## DODAĆ W load_metadata

```py
self.nextion_ui_cut = bool(data.get("nextion_ui_cut", self.nextion_ui_cut))
```

---

## ZMIENIĆ save_metadata

Stare:

```py
json.dump({"title": self.title, "director": self.director}, f, ensure_ascii=False, indent=2)
```

Nowe:

```py
json.dump(
    {
        "title": self.title,
        "director": self.director,
        "nextion_ui_cut": bool(self.nextion_ui_cut),
    },
    f,
    ensure_ascii=False,
    indent=2,
)
```

---

## ZMIENIĆ update_meta

Stare:

```py
def update_meta(self, title=None, director=None):
```

Nowe:

```py
def update_meta(self, title=None, director=None, nextion_ui_cut=None):
```

W środku:

```py
if nextion_ui_cut is not None:
    new_ui_cut = bool(nextion_ui_cut)
    if new_ui_cut != self.nextion_ui_cut:
        self.nextion_ui_cut = new_ui_cut
        changed = True
```

---

# 7. EHR — editor/EHR/tarzanEhrUi.py

## Cel zmiany

EHR nie może robić `_refresh_all` przy zmianie pojedynczej wartości, osi, punktu, STEP preview.

Snajper ma przejąć dynamiczne elementy:

```txt
krzywa osi N
STEP preview osi N
metryki osi N
slot TAKE
ghost line osi N
```

---

## STARY MODEL DO OGRANICZENIA

Przykładowy stary tor:

```py
self._refresh_all()
```

albo:

```py
self._draw_main_canvas()
self._refresh_axis_info()
self._refresh_protocol_preview()
```

wywoływane po zmianie jednej osi lub punktu.

---

## NOWY MODEL

Po zmianie punktu osi:

```py
self.tarzan_snajper.fire("ehr_axis_3_curve", new_curve_coords)
self.tarzan_snajper.fire("ehr_axis_3_step_preview", new_step_bar_coords)
self.tarzan_snajper.fire("ehr_axis_3_metrics", metrics_text)
```

Dla osi 0..5:

```py
self.tarzan_snajper.fire("ehr_axis_0_curve", coords)
self.tarzan_snajper.fire("ehr_axis_1_curve", coords)
self.tarzan_snajper.fire("ehr_axis_2_curve", coords)
self.tarzan_snajper.fire("ehr_axis_3_curve", coords)
self.tarzan_snajper.fire("ehr_axis_4_curve", coords)
self.tarzan_snajper.fire("ehr_axis_5_curve", coords)
```

---

## CANVAS EHR

Po pierwszym renderze EHR trzeba zarejestrować itemy:

```py
self.ehr_canvas_adapter.register_item(
    "ehr_main",
    "axis_3_curve",
    "coords",
    self.main_canvas,
    axis_3_curve_item_id,
)
```

Dla STEP preview:

```py
self.ehr_canvas_adapter.register_item(
    "ehr_protocol",
    "axis_3_step_bars",
    "coords",
    self.protocol_canvas,
    axis_3_step_item_id,
)
```

---

## ZASADA

`_refresh_all()` zostaje tylko dla:

```txt
pierwszy render EHR
wczytanie TAKE
zmiana liczby osi
zmiana skali czasu
pełna zmiana layoutu
reset widoku
```

Nie dla:

```txt
przeciągnięcie punktu
zmiana jednej osi
zmiana metryk
zmiana STEP preview jednej osi
```

---

# 8. Sandbox osi

## Pliki

```txt
editor/EHR/tarzanAxisSandbox.py
editor/tarzanAxisSandbox.py
```

## Cel

Podczas przeciągania punktu nie robić pełnego `_refresh_all`.

---

## STARY MODEL

```py
self._refresh_all()
```

przy ruchu punktu.

---

## NOWY MODEL

```py
self.tarzan_snajper.fire("sandbox_curve", curve_coords)
self.tarzan_snajper.fire("sandbox_step_preview", step_coords)
self.tarzan_snajper.fire("sandbox_metrics", metrics_text)
```

Po pierwszym renderze:

```py
self.sandbox_canvas_adapter.register_item(
    "sandbox",
    "curve",
    "coords",
    self.canvas,
    curve_item_id,
)
```

---

# 9. Timeline

## Cel

Nie odświeżać całej timeline przy zmianie kursora lub markera.

---

## STARY MODEL

```py
draw_timeline()
_schedule_timeline_redraw()
canvas.delete("all")
```

przy zmianie kursora czasu.

---

## NOWY MODEL

```py
self.tarzan_snajper.fire("timeline_cursor", cursor_coords)
self.tarzan_snajper.fire("timeline_take_marker", take_marker_coords)
self.tarzan_snajper.fire("timeline_clap_marker", clap_marker_coords)
```

Po pełnym renderze timeline:

```py
self.timeline_canvas_adapter.register_item(
    "par_timeline",
    "cursor",
    "coords",
    self.timeline_canvas,
    cursor_item_id,
)
```

---

# 10. Layout Designer

## Cel

Nie przerysowywać całego layout preview przy zmianie zaznaczonej komórki lub statusu panelu.

---

## STARY MODEL

```py
draw_preview()
canvas.delete("all")
refresh_zone_buttons()
```

dla drobnych zmian.

---

## NOWY MODEL

```py
self.tarzan_snajper.fire("layout_selected_cell", selected_cell_coords)
self.tarzan_snajper.fire("layout_panel_status", status_text)
self.tarzan_snajper.fire("layout_zone_label", label_text)
```

Pełny `draw_preview()` zostaje tylko dla:

```txt
zmiana liczby kolumn
zmiana liczby wierszy
zmiana struktury paneli
zmiana stref layoutu
```

---

# 11. KHR

## Plik

```txt
editor/tarzanKHR.py
```

## Cel

Nie przerysowywać markerów i statusów całym canvasem.

---

## STARY MODEL

```py
_draw_input()
_draw_khr()
_draw_output()
canvas.delete("all")
```

dla markerów i statusów.

---

## NOWY MODEL

```py
self.tarzan_snajper.fire("khr_input_marker", input_marker_coords)
self.tarzan_snajper.fire("khr_output_marker", output_marker_coords)
self.tarzan_snajper.fire("khr_status", status_text)
```

Kamera/video zostaje osobną pętlą.  
Snajper nie zastępuje obrazu kamery.

---

# 12. Kontrola po zmianie

Po wdrożeniu wyszukać:

```powershell
Get-ChildItem -Path . -Recurse -Filter *.py | Select-String -Pattern "def nextion_tick"
```

Ma nie znaleźć nic.

```powershell
Get-ChildItem -Path . -Recurse -Filter *.py | Select-String -Pattern "self.nextion_tick"
```

Ma nie znaleźć nic.

Wyszukać dynamiczne refreshy:

```powershell
Get-ChildItem -Path . -Recurse -Filter *.py | Select-String -Pattern "nextion_refresh_previews|refresh_axis_cards|_refresh_all|canvas.delete\(\"all\"\)|widget.refresh"
```

Każdy wynik podzielić na:

```txt
STRUKTURALNY — zostaje
DYNAMICZNY — zastąpić Snajperem
```

---

# 13. Finalny model pracy

```txt
SignalBus / akcja UI / runtime packet
        ↓
TarzanSnajper.fire_from_signal(...) albo fire(...)
        ↓
last_value
        ↓
adapter:
    physical_nextion
    canvas_preview
    par_tkinter
    ehr_canvas
    ehr_tkinter
    sandbox_canvas
    timeline_canvas
    layout_canvas
    khr_canvas
        ↓
konkretny cel
```

Nie ma:

```txt
refresh_all dla wartości
refresh panelu dla licznika
refresh preview dla t_p1_val
canvas.delete("all") dla statusu
tick skanujący cele
```

Jest:

```txt
jedna zmiana → jeden strzał
```
