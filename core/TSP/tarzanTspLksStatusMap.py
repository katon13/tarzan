from __future__ import annotations

"""TARZAN LKS-N5 — mapa kontrolek status_main.

Jeden plik prawdy dla nazw komponentów Dual-state Button na stronie
``status_main`` Nextion 5.

Kontrakt:
- ``component.val=0`` = OFF / brak potwierdzenia / błąd / szary,
- ``component.val=1`` = ON / test OK / zielony.

Ten moduł nie dotyka sprzętu, nie diagnozuje hardware, nie steruje ruchem
ani nie wysyła STEP/DIR/ENABLE. Jest tylko mapą nazw dla warstwy LKS-N5.
"""

from typing import Dict, Iterable, List, Tuple

# Pełna mapa komponentów HMI status_main.
# Klucz logiczny i nazwa komponentu Nextion są na razie takie same, ale mapa
# zostaje celowo jawna, żeby później diagnostyka mogła używać kluczy logicznych
# bez rozrzucania nazw HMI po kodzie.
LKS_STATUS_COMPONENTS: Dict[str, str] = {
    "linux_sys": "linux_sys",
    "snajper_sys": "snajper_sys",
    "pok_play": "pok_play",
    "pok_rec": "pok_rec",
    "rrp": "rrp",
    "sok_poz": "sok_poz",
    "sok_pion": "sok_pion",
    "next_7": "next_7",
    "lcd_1602": "lcd_1602",
    "matrix_led": "matrix_led",
    "keypad": "keypad",
    "f_button": "f_button",
    "f_led": "f_led",
    "shock_alarm": "shock_alarm",
    "level_xyz": "level_xyz",
    "light_laser": "light_laser",
    "light_bh1750": "light_bh1750",
    "kranc": "kranc",
    "kam_poz": "kam_poz",
    "kam_pion": "kam_pion",
    "kam_ostr": "kam_ostr",
    "kam_poch": "kam_poch",
    "ram_poziom": "ram_poziom",
    "ram_pion": "ram_pion",
    "cam_main": "cam_main",
    "cam_track": "cam_track",
    "i2c_bus": "i2c_bus",
    "take_sys": "take_sys",
    "par_sys": "par_sys",
    "ehr_sys": "ehr_sys",
}


# ID komponentów Dual-state Button na stronie status_main z eksportu Nextion 5.
# Używane do obsługi kliknięcia operatora: event 0x65 page_id component_id touch_event.
# touch_event=1 oznacza release i dopiero wtedy uruchamiamy test punktowy.
LKS_STATUS_COMPONENT_IDS: Dict[int, str] = {
    1: "linux_sys",
    2: "snajper_sys",
    3: "pok_play",
    4: "sok_poz",
    5: "pok_rec",
    6: "rrp",
    7: "sok_pion",
    8: "next_7",
    9: "lcd_1602",
    10: "matrix_led",
    11: "keypad",
    12: "f_button",
    13: "shock_alarm",
    14: "level_xyz",
    15: "light_laser",
    16: "light_bh1750",
    17: "kranc",
    18: "f_led",
    19: "kam_poz",
    20: "kam_pion",
    21: "kam_ostr",
    22: "kam_poch",
    23: "ram_poziom",
    24: "ram_pion",
    25: "cam_main",
    26: "cam_track",
    27: "i2c_bus",
    28: "take_sys",
    29: "par_sys",
    30: "ehr_sys",
}

# Grupy logiczne pod diagnostykę ETAPU 5/6.
GROUP_SYSTEM: Tuple[str, ...] = ("linux_sys", "snajper_sys", "take_sys", "par_sys", "ehr_sys")
GROUP_POKEYS: Tuple[str, ...] = ("pok_play", "pok_rec")
GROUP_BUS: Tuple[str, ...] = (
    "i2c_bus",
    "lcd_1602",
    "matrix_led",
    "keypad",
    "light_bh1750",
    "level_xyz",
    "shock_alarm",
    "light_laser",
)
GROUP_IO: Tuple[str, ...] = ("f_button", "f_led", "kranc")
GROUP_CAMERA: Tuple[str, ...] = ("cam_main", "cam_track")
GROUP_AXIS: Tuple[str, ...] = (
    "kam_poz",
    "kam_pion",
    "kam_ostr",
    "kam_poch",
    "ram_poziom",
    "ram_pion",
)
GROUP_SOK: Tuple[str, ...] = ("sok_poz", "sok_pion")

# Elementy wymagane do zbiorczego OK magistrali komunikacji.
# Nazwa komponentu zostaje i2c_bus, ale znaczenie jest szersze: UART / USB / I2C / BUS.
REQUIRED_BUS_DEVICES: Tuple[str, ...] = (
    "lcd_1602",
    "matrix_led",
    "keypad",
    "light_bh1750",
    "level_xyz",
    "shock_alarm",
    "light_laser",
)

ALL_GROUPS: Dict[str, Tuple[str, ...]] = {
    "system": GROUP_SYSTEM,
    "pokeys": GROUP_POKEYS,
    "bus": GROUP_BUS,
    "io": GROUP_IO,
    "camera": GROUP_CAMERA,
    "axis": GROUP_AXIS,
    "sok": GROUP_SOK,
}


def all_components() -> List[str]:
    """Zwraca wszystkie nazwy komponentów Nextion status_main w stałej kolejności."""
    return list(LKS_STATUS_COMPONENTS.values())


def all_keys() -> List[str]:
    """Zwraca wszystkie klucze logiczne statusów LKS-N5."""
    return list(LKS_STATUS_COMPONENTS.keys())


def validate_component(name: str) -> str:
    """Waliduje klucz logiczny albo nazwę komponentu i zwraca nazwę Nextion.

    Akceptuje:
    - klucz z ``LKS_STATUS_COMPONENTS``;
    - bezpośrednią nazwę komponentu, jeżeli znajduje się w wartościach mapy.
    """
    key = str(name or "").strip()
    if not key:
        raise KeyError("Unknown LKS-N5 status component: <empty>")
    if key in LKS_STATUS_COMPONENTS:
        return LKS_STATUS_COMPONENTS[key]
    if key in LKS_STATUS_COMPONENTS.values():
        return key
    raise KeyError(f"Unknown LKS-N5 status component: {key}")


def group_components(group_name: str) -> List[str]:
    """Zwraca komponenty wskazanej grupy logicznej."""
    group = str(group_name or "").strip().lower()
    if group not in ALL_GROUPS:
        raise KeyError(f"Unknown LKS-N5 status group: {group}")
    return [validate_component(name) for name in ALL_GROUPS[group]]


def validate_many(names: Iterable[str]) -> List[str]:
    """Waliduje listę nazw/kluczy i zwraca nazwy komponentów Nextion."""
    return [validate_component(name) for name in names]


def empty_statuses(value: bool = False) -> Dict[str, bool]:
    """Buduje słownik statusów dla wszystkich kontrolek.

    Używane przez reset i testy na sucho.
    """
    return {component: bool(value) for component in all_components()}


def bus_ok_from_statuses(statuses: Dict[str, bool]) -> bool:
    """Wylicza stan kontrolki i2c_bus dla LKS-N5.

    W fizycznym TARZANIE magistrala operatora idzie przez PoKeys BUS/I2C,
    więc nie wolno uzależniać zielonego i2c_bus wyłącznie od /dev/i2c-*
    ani od tego, czy wszystkie peryferia pomocnicze są już podpięte.

    Zielone wystarcza, gdy:
    - punktowy tester i2c_bus potwierdził skan PoKeys BUS/I2C, albo
    - PoSensors / laser-light module dał realny ACK, albo
    - BH1750 potwierdził realną komunikację po tej magistrali.

    Nie uznajemy samego CP2102/USB-UART za OK; to może być tylko szczegół
    diagnostyczny, nie potwierdzenie czujnika.
    """
    return bool(
        statuses.get("i2c_bus", False)
        or statuses.get("light_laser", False)
        or statuses.get("light_bh1750", False)
    )



def component_from_nextion_id(component_id: int) -> str:
    """Zwraca nazwę komponentu status_main po ID z eventu touch Nextiona."""
    cid = int(component_id)
    if cid not in LKS_STATUS_COMPONENT_IDS:
        raise KeyError(f"Unknown LKS-N5 status_main component id: {cid}")
    return validate_component(LKS_STATUS_COMPONENT_IDS[cid])


def nextion_id_from_component(name: str) -> int:
    """Zwraca ID komponentu status_main po nazwie/kluczu logicznym."""
    component = validate_component(name)
    for cid, mapped in LKS_STATUS_COMPONENT_IDS.items():
        if validate_component(mapped) == component:
            return cid
    raise KeyError(f"LKS-N5 component has no Nextion ID: {component}")

def assert_unique_components() -> None:
    """Sprawdza, czy mapa nie ma zdublowanych nazw komponentów."""
    values = all_components()
    duplicates = sorted({name for name in values if values.count(name) > 1})
    if duplicates:
        raise AssertionError(f"Duplicate LKS-N5 components: {', '.join(duplicates)}")


# Szybka walidacja przy imporcie. Jeżeli HMI/mapa zostaną zepsute, błąd ma być
# widoczny od razu w testach, a nie dopiero na fizycznym ekranie.
assert_unique_components()
