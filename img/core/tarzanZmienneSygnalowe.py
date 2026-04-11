"""
tarzanZmienneSygnalowe.py

Centralna mapa sygnałów systemu TARZAN.

Założenia:
- każdy wpis odpowiada konkretnemu, fizycznemu pinowi lub kanałowi,
- znaczenie sygnału wynika z rzeczywistego okablowania i nie może być zmieniane,
- nazwy programowe są krótkie, czytelne i zgodne ze stylem Pythona,
- numer pinu, płytka, typ sygnału, kierunek i opis są zapisane jawnie,
- plik stanowi warstwę zgodności hardware -> software,
- plik uwzględnia funkcje specjalne PoKeys57U,
- plik rozróżnia sygnały dostępne dla logiki trybów od sygnałów tylko do odczytu
  oraz od sygnałów zarezerwowanych sprzętowo.

Typy sygnałów:
- LH       : stan logiczny 0/1
- CTR      : sygnał impulsowy / krokowy
- ANALOG   : wejście analogowe
- F        : funkcja sprzętowa / specjalna
- RESERVED : pin rezerwowy / nieużywany

Kierunki:
- IN
- OUT
- F
- RESERVED

Klasyfikacja logiki trybów:
- DOZWOLONY    : sygnał może brać udział w budowaniu logiki trybu
- TYLKO_ODCZYT : sygnał wolno analizować w warunkach, ale nie wolno nim dowolnie sterować
- ZABRONIONY   : sygnał zarezerwowany sprzętowo, magistralowy lub systemowy; nie trafia do kreatora trybów
"""

from dataclasses import dataclass
from typing import Optional, Dict, List


# ======================================================================
# KONFIGURACJA GLOBALNA
# ======================================================================

POKEYS57U_PLAY_DEVICE_SERIAL = 34238
POKEYS57U_REC_DEVICE_SERIAL = 33410
MIKROKROK_STARTOWY = 32


# ======================================================================
# STAŁE DLA FUNKCJI SPRZĘTOWYCH
# ======================================================================

HW_GPIO = "GPIO"
HW_ANALOG = "ANALOG"
HW_LCD = "LCD"
HW_MATRIX_LED = "MATRIX_LED"
HW_POEXTBUS = "POEXTBUS"
HW_PULSE = "PULSE_ENGINE"
HW_I2C = "I2C"
HW_KEYBOARD = "KEYBOARD"
HW_PWM = "PWM"
HW_SYSTEM = "SYSTEM"
HW_RESERVED = "RESERVED"


# ======================================================================
# STAŁE DLA DOSTĘPNOŚCI W LOGICE TRYBÓW
# ======================================================================

LOGIKA_DOZWOLONY = "DOZWOLONY"
LOGIKA_TYLKO_ODCZYT = "TYLKO_ODCZYT"
LOGIKA_ZABRONIONY = "ZABRONIONY"

ROLA_INPUT = "INPUT"
ROLA_OUTPUT = "OUTPUT"
ROLA_SENSOR = "SENSOR"
ROLA_STATUS = "STATUS"
ROLA_UI = "UI"
ROLA_SYSTEM = "SYSTEM"
ROLA_RESERVED = "RESERVED"


# ======================================================================
# MODEL DANYCH
# ======================================================================

@dataclass(frozen=True)
class TarzanSygnal:
    nazwa: str
    plytka: str
    pin: Optional[int]
    kanal: Optional[str]
    typ: str
    kierunek: str
    default: str
    opis: str
    zrodlo: str

    hardware_function: str
    hardware_label: str
    pin_is_fixed: bool
    is_shared_pin: bool
    conflict_group: Optional[str]

    panel_port: Optional[int]
    grupa: str
    klasa_wykonawcza: str
    status: str

    logika_trybow: str = LOGIKA_DOZWOLONY
    rola_logiki: str = ROLA_INPUT
    uwaga_logiki: str = ""


def _wyznacz_klasyfikacje_logiki(
    *,
    typ: str,
    kierunek: str,
    grupa: str,
    hardware_function: str,
    hardware_label: str,
    opis: str,
) -> tuple[str, str, str]:
    """
    Automatyczna klasyfikacja sygnału do użycia w logice trybów.

    Zasada:
    - sygnały infrastruktury sprzętowej i magistral są ZABRONIONE,
    - sygnały czujnikowe, krańcówki i sygnały kopii / statusu są TYLKO_ODCZYT,
    - sygnały sterujące i wybrane wejścia operatora są DOZWOLONE.
    """
    grupa_u = (grupa or "").upper()
    hw_u = (hardware_function or "").upper()
    label_u = (hardware_label or "").upper()
    opis_u = (opis or "").upper()

    forbidden_hw = {HW_LCD, HW_MATRIX_LED, HW_I2C, HW_KEYBOARD, HW_POEXTBUS, HW_SYSTEM, HW_RESERVED}
    if typ in {"F", "RESERVED"} or hw_u in forbidden_hw:
        return (
            LOGIKA_ZABRONIONY,
            ROLA_SYSTEM if hw_u != HW_RESERVED else ROLA_RESERVED,
            "Pin lub kanał pełni stałą funkcję sprzętową; sygnał informacyjny, nie do swobodnego użycia w kreatorze trybów.",
        )

    if "CHARGE PUMP" in label_u or "EMERGENCY" in label_u or "RECOVERY" in label_u or "1-WIRE" in label_u:
        return (
            LOGIKA_ZABRONIONY,
            ROLA_SYSTEM,
            "Sygnał systemowy lub bezpieczeństwa PoKeys57U; nie wolno przypisywać go dowolnie do logiki trybów.",
        )

    readonly_groups = {
        "KRAŃCÓWKI",
        "CZUJNIKI",
        "COPY_CAMERA",
        "MOSTEK_PLAY_REC",
        "STATUS",
        "AUTO_STATUS",
    }
    if grupa_u in readonly_groups:
        return (
            LOGIKA_TYLKO_ODCZYT,
            ROLA_SENSOR if grupa_u in {"KRAŃCÓWKI", "CZUJNIKI"} else ROLA_STATUS,
            "Sygnał wolno analizować w warunkach i bezpieczeństwie, ale nie wolno używać go jako dowolnego wyjścia sterującego.",
        )

    if hw_u == HW_ANALOG or typ == "ANALOG":
        return (
            LOGIKA_TYLKO_ODCZYT,
            ROLA_SENSOR,
            "Sygnał analogowy wykorzystywany pomiarowo; w kreatorze trybów dostępny tylko do odczytu i warunków.",
        )

    if grupa_u in {"UI", "RRP", "STEROWANIE_OPERATORA"} and kierunek == "IN":
        return (
            LOGIKA_DOZWOLONY,
            ROLA_UI,
            "Wejście operatora dopuszczone do budowania logiki trybu jako warunek lub źródło sterowania.",
        )

    if kierunek == "OUT" and hw_u in {HW_GPIO, HW_PULSE, HW_PWM}:
        return (
            LOGIKA_DOZWOLONY,
            ROLA_OUTPUT,
            "Wyjście wykonawcze dopuszczone do przypisywania w logice trybów zgodnie z dokumentacją i mechaniką systemu.",
        )

    if kierunek == "IN":
        return (
            LOGIKA_TYLKO_ODCZYT,
            ROLA_INPUT,
            "Wejście sprzętowe dostępne głównie do warunków i odczytu; przed użyciem w trybie należy potwierdzić jego funkcję w dokumentacji.",
        )

    return (
        LOGIKA_DOZWOLONY,
        ROLA_INPUT if kierunek == "IN" else ROLA_OUTPUT,
        "Sygnał dopuszczony do logiki trybów.",
    )


def _sygnal(
    *,
    nazwa: str,
    plytka: str,
    pin: Optional[int],
    kanal: Optional[str],
    typ: str,
    kierunek: str,
    default: str,
    opis: str,
    zrodlo: str,
    hardware_function: str,
    hardware_label: str,
    pin_is_fixed: bool,
    is_shared_pin: bool,
    conflict_group: Optional[str],
    panel_port: Optional[int],
    grupa: str,
    klasa_wykonawcza: str,
    status: str = "AKTYWNY",
    logika_trybow: Optional[str] = None,
    rola_logiki: Optional[str] = None,
    uwaga_logiki: Optional[str] = None,
) -> TarzanSygnal:
    auto_logika, auto_rola, auto_uwaga = _wyznacz_klasyfikacje_logiki(
        typ=typ,
        kierunek=kierunek,
        grupa=grupa,
        hardware_function=hardware_function,
        hardware_label=hardware_label,
        opis=opis,
    )

    return TarzanSygnal(
        nazwa=nazwa,
        plytka=plytka,
        pin=pin,
        kanal=kanal,
        typ=typ,
        kierunek=kierunek,
        default=default,
        opis=opis,
        zrodlo=zrodlo,
        hardware_function=hardware_function,
        hardware_label=hardware_label,
        pin_is_fixed=pin_is_fixed,
        is_shared_pin=is_shared_pin,
        conflict_group=conflict_group,
        panel_port=panel_port,
        grupa=grupa,
        klasa_wykonawcza=klasa_wykonawcza,
        status=status,
        logika_trybow=logika_trybow or auto_logika,
        rola_logiki=rola_logiki or auto_rola,
        uwaga_logiki=uwaga_logiki or auto_uwaga,
    )


# ======================================================================
# FUNKCJE POMOCNICZE
# ======================================================================

def pobierz_po_nazwie(nazwa: str) -> TarzanSygnal:
    return WSZYSTKIE_SYGNALY[nazwa]


def pobierz_po_pinie(plytka: str, pin: int) -> Optional[TarzanSygnal]:
    slownik = {
        "PLAY": SYGNALY_PLAY,
        "REC": SYGNALY_REC,
    }.get(plytka.upper())

    if slownik is None:
        return None

    for sygnal in slownik.values():
        if sygnal.pin == pin:
            return sygnal
    return None


def pobierz_grupe_konfliktu(conflict_group: str) -> List[TarzanSygnal]:
    return [
        sygnal
        for sygnal in WSZYSTKIE_SYGNALY.values()
        if sygnal.conflict_group == conflict_group
    ]


def pobierz_dla_logiki_trybow() -> List[TarzanSygnal]:
    return [
        sygnal
        for sygnal in WSZYSTKIE_SYGNALY.values()
        if sygnal.logika_trybow == LOGIKA_DOZWOLONY
    ]


def pobierz_tylko_odczyt() -> List[TarzanSygnal]:
    return [
        sygnal
        for sygnal in WSZYSTKIE_SYGNALY.values()
        if sygnal.logika_trybow == LOGIKA_TYLKO_ODCZYT
    ]


def pobierz_zabronione_dla_trybow() -> List[TarzanSygnal]:
    return [
        sygnal
        for sygnal in WSZYSTKIE_SYGNALY.values()
        if sygnal.logika_trybow == LOGIKA_ZABRONIONY
    ]


# ======================================================================
# PLAY
# ======================================================================

play_p01_arm_h_auto_limit = _sygnal(
    nazwa="play_p01_arm_h_auto_limit",
    plytka="PLAY",
    pin=1,
    kanal=None,
    typ="LH",
    kierunek="IN",
    default="1",
    opis="Krańcówka dźwigni automatyki osi poziomej ramienia.",
    zrodlo="tarzan_PoKeys57U_Play_MolexG_RamiePoziom_Ends_Auto",
    hardware_function=HW_GPIO,
    hardware_label="Counter 1 / Fast encoder A1",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="PLAY_P01_COUNTER",
    panel_port=2,
    grupa="KRAŃCÓWKI",
    klasa_wykonawcza="tarzanArmHorizontal.py",
)

play_p02_arm_h_limit_right = _sygnal(
    nazwa="play_p02_arm_h_limit_right",
    plytka="PLAY",
    pin=2,
    kanal=None,
    typ="LH",
    kierunek="IN",
    default="0",
    opis="Krańcówka osi poziomej ramienia, obrót w prawo.",
    zrodlo="tarzan_PoKeys57U_Play_MolexG_RamiePoziom_End1_Prawo",
    hardware_function=HW_GPIO,
    hardware_label="Counter 2 / Fast encoder B1",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="PLAY_P02_COUNTER",
    panel_port=2,
    grupa="KRAŃCÓWKI",
    klasa_wykonawcza="tarzanArmHorizontal.py",
)

play_p03_arm_h_limit_left = _sygnal(
    nazwa="play_p03_arm_h_limit_left",
    plytka="PLAY",
    pin=3,
    kanal=None,
    typ="LH",
    kierunek="IN",
    default="0",
    opis="Krańcówka osi poziomej ramienia, obrót w lewo.",
    zrodlo="tarzan_PoKeys57U_Play_MolexG_RamiePoziom_End2_lewo",
    hardware_function=HW_GPIO,
    hardware_label="GPIO pin 3",
    pin_is_fixed=True,
    is_shared_pin=False,
    conflict_group=None,
    panel_port=2,
    grupa="KRAŃCÓWKI",
    klasa_wykonawcza="tarzanArmHorizontal.py",
)

play_p04_arm_v_limit_up = _sygnal(
    nazwa="play_p04_arm_v_limit_up",
    plytka="PLAY",
    pin=4,
    kanal=None,
    typ="LH",
    kierunek="IN",
    default="0",
    opis="Krańcówka osi pionowej ramienia, ruch w górę.",
    zrodlo="tarzan_PoKeys57U_Play_MolexH_RamiePion_End1_gora",
    hardware_function=HW_GPIO,
    hardware_label="GPIO pin 4",
    pin_is_fixed=True,
    is_shared_pin=False,
    conflict_group=None,
    panel_port=3,
    grupa="KRAŃCÓWKI",
    klasa_wykonawcza="tarzanArmVertical.py",
)

play_p05_cam_h_limit_right = _sygnal(
    nazwa="play_p05_cam_h_limit_right",
    plytka="PLAY",
    pin=5,
    kanal=None,
    typ="LH",
    kierunek="IN",
    default="0",
    opis="Krańcówka głowicy kamery, ruch w prawo.",
    zrodlo="tarzan_PoKeys57U_Play_MolexD_GlowicaKam_End1_prawo",
    hardware_function=HW_GPIO,
    hardware_label="Counter 5 / Fast encoder A2",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="PLAY_P05_COUNTER",
    panel_port=6,
    grupa="KRAŃCÓWKI",
    klasa_wykonawcza="tarzanCameraHorizontal.py",
)

play_p06_cam_h_limit_left = _sygnal(
    nazwa="play_p06_cam_h_limit_left",
    plytka="PLAY",
    pin=6,
    kanal=None,
    typ="LH",
    kierunek="IN",
    default="0",
    opis="Krańcówka głowicy kamery, ruch w lewo.",
    zrodlo="tarzan_PoKeys57U_Play_MolexD_GlowicaKam_End2_lewo",
    hardware_function=HW_GPIO,
    hardware_label="Counter 6 / Fast encoder B2",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="PLAY_P06_COUNTER",
    panel_port=6,
    grupa="KRAŃCÓWKI",
    klasa_wykonawcza="tarzanCameraHorizontal.py",
)

play_p07_cam_v_limit_up = _sygnal(
    nazwa="play_p07_cam_v_limit_up",
    plytka="PLAY",
    pin=7,
    kanal=None,
    typ="LH",
    kierunek="IN",
    default="0",
    opis="Krańcówka głowicy kamery, ruch w górę.",
    zrodlo="tarzan_PoKeys57U_Play_MolexD_GlowicaKam_End3_gora",
    hardware_function=HW_GPIO,
    hardware_label="GPIO pin 7",
    pin_is_fixed=True,
    is_shared_pin=False,
    conflict_group=None,
    panel_port=7,
    grupa="KRAŃCÓWKI",
    klasa_wykonawcza="tarzanCameraVertical.py",
)

play_p08_cam_v_limit_down = _sygnal(
    nazwa="play_p08_cam_v_limit_down",
    plytka="PLAY",
    pin=8,
    kanal=None,
    typ="LH",
    kierunek="IN",
    default="0",
    opis="Krańcówka głowicy kamery, ruch w dół.",
    zrodlo="tarzan_PoKeys57U_Play_MolexD_GlowicaKam_End4_dol",
    hardware_function=HW_GPIO,
    hardware_label="Ultra fast encoder A",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="PLAY_P08_ULTRA_ENCODER",
    panel_port=7,
    grupa="KRAŃCÓWKI",
    klasa_wykonawcza="tarzanCameraVertical.py",
)

play_p09_arm_v_auto_limit = _sygnal(
    nazwa="play_p09_arm_v_auto_limit",
    plytka="PLAY",
    pin=9,
    kanal=None,
    typ="LH",
    kierunek="IN",
    default="0",
    opis="Krańcówka dźwigni automatyki osi pionowej ramienia.",
    zrodlo="tarzan_PoKeys57U_Play_MolexH_RamiePion_EndS_auto",
    hardware_function=HW_GPIO,
    hardware_label="Matrix LED 1 DATA / Counter 9",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="PLAY_P09_MATRIX_LED_1",
    panel_port=3,
    grupa="KRAŃCÓWKI",
    klasa_wykonawcza="tarzanArmVertical.py",
)

play_p10_cam_tilt_limit = _sygnal(
    nazwa="play_p10_cam_tilt_limit",
    plytka="PLAY",
    pin=10,
    kanal=None,
    typ="LH",
    kierunek="IN",
    default="0",
    opis="Krańcówka osi pochyłu głowicy kamery.",
    zrodlo="tarzan_PoKeys57U_Play_Pochyl_End",
    hardware_function=HW_GPIO,
    hardware_label="Matrix LED 1 LATCH",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="PLAY_P10_MATRIX_LED_1",
    panel_port=7,
    grupa="KRAŃCÓWKI",
    klasa_wykonawcza="tarzanCameraTilt.py",
)

play_p11_cart_limit_end = _sygnal(
    nazwa="play_p11_cart_limit_end",
    plytka="PLAY",
    pin=11,
    kanal=None,
    typ="LH",
    kierunek="IN",
    default="0",
    opis="Krańcówka końca jazdy wózka.",
    zrodlo="tarzan_PoKeys57U_Play_wozek_End",
    hardware_function=HW_GPIO,
    hardware_label="Matrix LED 1 CLOCK / Counter 11",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="PLAY_P11_MATRIX_LED_1",
    panel_port=None,
    grupa="KRAŃCÓWKI",
    klasa_wykonawcza="tarzanWozek.py",
)

play_p12_arm_v_limit_down = _sygnal(
    nazwa="play_p12_arm_v_limit_down",
    plytka="PLAY",
    pin=12,
    kanal=None,
    typ="LH",
    kierunek="IN",
    default="0",
    opis="Krańcówka osi pionowej ramienia, ruch w dół.",
    zrodlo="tarzan_PoKeys57U_Play_MolexH_RamiePion_End2_dol",
    hardware_function=HW_GPIO,
    hardware_label="Ultra fast encoder B",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="PLAY_P12_ULTRA_ENCODER",
    panel_port=3,
    grupa="KRAŃCÓWKI",
    klasa_wykonawcza="tarzanArmVertical.py",
)

play_p13_mass_reg_limit_add = _sygnal(
    nazwa="play_p13_mass_reg_limit_add",
    plytka="PLAY",
    pin=13,
    kanal=None,
    typ="LH",
    kierunek="IN",
    default="0",
    opis="Krańcówka regulatora masy, pozycja masa dodana.",
    zrodlo="tarzan_PoKeys57U_Play_MolexI_regmasy_End1_dodane",
    hardware_function=HW_GPIO,
    hardware_label="Ultra fast encoder I",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="PLAY_P13_ULTRA_ENCODER",
    panel_port=8,
    grupa="REGULATOR_MASY",
    klasa_wykonawcza="tarzanRegulatorMasy.py",
)

play_p14_drone_release = _sygnal(
    nazwa="play_p14_drone_release",
    plytka="PLAY",
    pin=14,
    kanal=None,
    typ="LH",
    kierunek="IN",
    default="0",
    opis="Zwolnienie elektromagnesu drona.",
    zrodlo="tarzan_PoKeys57U_Play_Rrp_Dir_Pion",
    hardware_function=HW_GPIO,
    hardware_label="GPIO pin 14",
    pin_is_fixed=True,
    is_shared_pin=False,
    conflict_group=None,
    panel_port=None,
    grupa="DRON",
    klasa_wykonawcza="tarzanDron.py",
)

play_p15_rrp_dir_h_res = _sygnal(
    nazwa="play_p15_rrp_dir_h_res",
    plytka="PLAY",
    pin=15,
    kanal=None,
    typ="LH",
    kierunek="IN",
    default="0",
    opis="Wolne wejście kierunku ręcznego regulatora pozycji w osi poziomej.",
    zrodlo="tarzan_PoKeys57U_Play_Rrp_Dir_Poziom",
    hardware_function=HW_GPIO,
    hardware_label="Counter 15 / Fast encoder A3",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="PLAY_P15_COUNTER",
    panel_port=1,
    grupa="RRP",
    klasa_wykonawcza="tarzanRRP.py",
    status="REZERWOWY",
)

play_p16_action_led = _sygnal(
    nazwa="play_p16_action_led",
    plytka="PLAY",
    pin=16,
    kanal=None,
    typ="LH",
    kierunek="IN",
    default="0",
    opis="Główna lampa sygnalizacyjna pracy ramienia.",
    zrodlo="tarzan_PoKeys57U_Play_akcja_LED",
    hardware_function=HW_GPIO,
    hardware_label="Counter 16 / Fast encoder B3",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="PLAY_P16_COUNTER",
    panel_port=1,
    grupa="UI",
    klasa_wykonawcza="tarzanMatrixLED8x8.py",
)

play_p17_bridge_rec_dir_x = _sygnal(
    nazwa="play_p17_bridge_rec_dir_x",
    plytka="PLAY",
    pin=17,
    kanal=None,
    typ="LH",
    kierunek="OUT",
    default="0",
    opis="Mostek komunikacyjny do REC, kopia DIR X osi poziomej ramienia.",
    zrodlo="tarzan_PoKeys57U_Play_Mstekrec_DirX_RamiePoziom",
    hardware_function=HW_PWM,
    hardware_label="PWM pin 17",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="PLAY_P17_PWM",
    panel_port=1,
    grupa="MOSTEK_PLAY_REC",
    klasa_wykonawcza="tarzanPoKeysPlay.py",
)

play_p18_bridge_rec_dir_y = _sygnal(
    nazwa="play_p18_bridge_rec_dir_y",
    plytka="PLAY",
    pin=18,
    kanal=None,
    typ="LH",
    kierunek="OUT",
    default="0",
    opis="Mostek komunikacyjny do REC, kopia DIR Y osi pionowej ramienia.",
    zrodlo="tarzan_PoKeys57U_Play_MostekRec_DirY_RamiePion",
    hardware_function=HW_PWM,
    hardware_label="PWM pin 18",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="PLAY_P18_PWM",
    panel_port=1,
    grupa="MOSTEK_PLAY_REC",
    klasa_wykonawcza="tarzanPoKeysPlay.py",
)

play_p19_bridge_rec_dir_z = _sygnal(
    nazwa="play_p19_bridge_rec_dir_z",
    plytka="PLAY",
    pin=19,
    kanal=None,
    typ="LH",
    kierunek="OUT",
    default="0",
    opis="Mostek komunikacyjny do REC, kopia DIR Z osi pochyłu ramienia.",
    zrodlo="tarzan_PoKeys57U_Play_MostekRec_DirZ_RamiePochyl",
    hardware_function=HW_PWM,
    hardware_label="PWM pin 19",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="PLAY_P19_PWM",
    panel_port=1,
    grupa="MOSTEK_PLAY_REC",
    klasa_wykonawcza="tarzanPoKeysPlay.py",
)

play_p20_bridge_rec_ctr_x = _sygnal(
    nazwa="play_p20_bridge_rec_ctr_x",
    plytka="PLAY",
    pin=20,
    kanal=None,
    typ="CTR",
    kierunek="OUT",
    default="1010...",
    opis="Mostek komunikacyjny do REC, kopia CTR X osi poziomej ramienia.",
    zrodlo="tarzan_PoKeys57U_Play_MostekRec_CtrX_RamiePoziom",
    hardware_function=HW_PWM,
    hardware_label="PWM pin 20",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="PLAY_P20_PWM",
    panel_port=1,
    grupa="MOSTEK_PLAY_REC",
    klasa_wykonawcza="tarzanPoKeysPlay.py",
)

play_p21_bridge_rec_ctr_y = _sygnal(
    nazwa="play_p21_bridge_rec_ctr_y",
    plytka="PLAY",
    pin=21,
    kanal=None,
    typ="CTR",
    kierunek="OUT",
    default="1010...",
    opis="Mostek komunikacyjny do REC, kopia CTR Y osi pionowej ramienia.",
    zrodlo="tarzan_PoKeys57U_Play_MostekRec_CtrY_RamiePoziom",
    hardware_function=HW_PWM,
    hardware_label="PWM pin 21",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="PLAY_P21_PWM",
    panel_port=1,
    grupa="MOSTEK_PLAY_REC",
    klasa_wykonawcza="tarzanPoKeysPlay.py",
)

play_p22_bridge_rec_ctr_z = _sygnal(
    nazwa="play_p22_bridge_rec_ctr_z",
    plytka="PLAY",
    pin=22,
    kanal=None,
    typ="CTR",
    kierunek="OUT",
    default="1010...",
    opis="Mostek komunikacyjny do REC, kopia CTR Z osi pochyłu ramienia.",
    zrodlo="tarzan_PoKeys57U_Play_MostekRec_CtrZ_RamiePoziom",
    hardware_function=HW_PWM,
    hardware_label="PWM pin 22",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="PLAY_P22_PWM",
    panel_port=1,
    grupa="MOSTEK_PLAY_REC",
    klasa_wykonawcza="tarzanPoKeysPlay.py",
)

play_p23_mass_reg_limit_remove = _sygnal(
    nazwa="play_p23_mass_reg_limit_remove",
    plytka="PLAY",
    pin=23,
    kanal=None,
    typ="LH",
    kierunek="IN",
    default="1",
    opis="Krańcówka regulatora masy, pozycja masa odjęta.",
    zrodlo="tarzan_PoKeys57U_Play_MolexI_RegMasy_End2_odjete",
    hardware_function=HW_LCD,
    hardware_label="LCD DB7 / Matrix LED 2 DATA",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="PLAY_P23_LCD_MATRIX2",
    panel_port=8,
    grupa="REGULATOR_MASY",
    klasa_wykonawcza="tarzanRegulatorMasy.py",
)

play_p24_kb4 = _sygnal(
    nazwa="play_p24_kb4",
    plytka="PLAY",
    pin=24,
    kanal=None,
    typ="F",
    kierunek="F",
    default="brak",
    opis="Klawiatura matrix, linia 4.",
    zrodlo="trPoPlayKb4",
    hardware_function=HW_KEYBOARD,
    hardware_label="Keyboard / LCD DB6 / Matrix LED 2 LATCH",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="PLAY_P24_LCD_MATRIX2_KEYBOARD",
    panel_port=1,
    grupa="UI",
    klasa_wykonawcza="tarzanKlawiatura4x3.py",
)

play_p25_kb3 = _sygnal(
    nazwa="play_p25_kb3",
    plytka="PLAY",
    pin=25,
    kanal=None,
    typ="F",
    kierunek="F",
    default="brak",
    opis="Klawiatura matrix, linia 3.",
    zrodlo="trPoPlayKb3",
    hardware_function=HW_KEYBOARD,
    hardware_label="Keyboard / LCD DB5 / Matrix LED 2 CLOCK",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="PLAY_P25_LCD_MATRIX2_KEYBOARD",
    panel_port=1,
    grupa="UI",
    klasa_wykonawcza="tarzanKlawiatura4x3.py",
)

play_p26_kb2 = _sygnal(
    nazwa="play_p26_kb2",
    plytka="PLAY",
    pin=26,
    kanal=None,
    typ="F",
    kierunek="F",
    default="brak",
    opis="Klawiatura matrix, linia 2.",
    zrodlo="trPoPlayKb2",
    hardware_function=HW_KEYBOARD,
    hardware_label="Keyboard / LCD DB4",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="PLAY_P26_LCD_KEYBOARD",
    panel_port=1,
    grupa="UI",
    klasa_wykonawcza="tarzanKlawiatura4x3.py",
)

play_p27_kb1 = _sygnal(
    nazwa="play_p27_kb1",
    plytka="PLAY",
    pin=27,
    kanal=None,
    typ="F",
    kierunek="F",
    default="brak",
    opis="Klawiatura matrix, linia 1.",
    zrodlo="trPoPlayKb1",
    hardware_function=HW_KEYBOARD,
    hardware_label="Keyboard pin 27",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="PLAY_P27_KEYBOARD",
    panel_port=1,
    grupa="UI",
    klasa_wykonawcza="tarzanKlawiatura4x3.py",
)

play_p28_lcd_rw = _sygnal(
    nazwa="play_p28_lcd_rw",
    plytka="PLAY",
    pin=28,
    kanal=None,
    typ="F",
    kierunek="F",
    default="brak",
    opis="Wyświetlacz LCD, pin RW.",
    zrodlo="trPoPlayLcdRW",
    hardware_function=HW_LCD,
    hardware_label="LCD RW",
    pin_is_fixed=True,
    is_shared_pin=False,
    conflict_group="PLAY_LCD",
    panel_port=1,
    grupa="UI",
    klasa_wykonawcza="tarzanLCD1602.py",
)

play_p29_lcd_rs = _sygnal(
    nazwa="play_p29_lcd_rs",
    plytka="PLAY",
    pin=29,
    kanal=None,
    typ="F",
    kierunek="F",
    default="brak",
    opis="Wyświetlacz LCD, pin RS.",
    zrodlo="trPoPlayLcdRS",
    hardware_function=HW_LCD,
    hardware_label="LCD RS",
    pin_is_fixed=True,
    is_shared_pin=False,
    conflict_group="PLAY_LCD",
    panel_port=1,
    grupa="UI",
    klasa_wykonawcza="tarzanLCD1602.py",
)

play_p30_lcd_e = _sygnal(
    nazwa="play_p30_lcd_e",
    plytka="PLAY",
    pin=30,
    kanal=None,
    typ="F",
    kierunek="F",
    default="brak",
    opis="Wyświetlacz LCD, pin E.",
    zrodlo="trPoPlayLcdE",
    hardware_function=HW_LCD,
    hardware_label="LCD E",
    pin_is_fixed=True,
    is_shared_pin=False,
    conflict_group="PLAY_LCD",
    panel_port=1,
    grupa="UI",
    klasa_wykonawcza="tarzanLCD1602.py",
)

play_p31_lcd_db7 = _sygnal(
    nazwa="play_p31_lcd_db7",
    plytka="PLAY",
    pin=31,
    kanal=None,
    typ="F",
    kierunek="F",
    default="brak",
    opis="Wyświetlacz LCD, pin DB7.",
    zrodlo="trPoPlayLcdDb7",
    hardware_function=HW_LCD,
    hardware_label="LCD secondary DB7",
    pin_is_fixed=True,
    is_shared_pin=False,
    conflict_group="PLAY_LCD_SECONDARY",
    panel_port=1,
    grupa="UI",
    klasa_wykonawcza="tarzanLCD1602.py",
)

play_p32_lcd_db6 = _sygnal(
    nazwa="play_p32_lcd_db6",
    plytka="PLAY",
    pin=32,
    kanal=None,
    typ="F",
    kierunek="F",
    default="brak",
    opis="Wyświetlacz LCD, pin DB6.",
    zrodlo="trPoPlayLcdDb6",
    hardware_function=HW_LCD,
    hardware_label="LCD secondary DB6",
    pin_is_fixed=True,
    is_shared_pin=False,
    conflict_group="PLAY_LCD_SECONDARY",
    panel_port=1,
    grupa="UI",
    klasa_wykonawcza="tarzanLCD1602.py",
)

play_p33_lcd_db5 = _sygnal(
    nazwa="play_p33_lcd_db5",
    plytka="PLAY",
    pin=33,
    kanal=None,
    typ="F",
    kierunek="F",
    default="brak",
    opis="Wyświetlacz LCD, pin DB5.",
    zrodlo="trPoPlayLcdDb5",
    hardware_function=HW_LCD,
    hardware_label="LCD secondary DB5",
    pin_is_fixed=True,
    is_shared_pin=False,
    conflict_group="PLAY_LCD_SECONDARY",
    panel_port=1,
    grupa="UI",
    klasa_wykonawcza="tarzanLCD1602.py",
)

play_p34_lcd_db4 = _sygnal(
    nazwa="play_p34_lcd_db4",
    plytka="PLAY",
    pin=34,
    kanal=None,
    typ="F",
    kierunek="F",
    default="brak",
    opis="Wyświetlacz LCD, pin DB4.",
    zrodlo="trPoPlayLcdDb4",
    hardware_function=HW_LCD,
    hardware_label="LCD secondary DB4",
    pin_is_fixed=True,
    is_shared_pin=False,
    conflict_group="PLAY_LCD_SECONDARY",
    panel_port=1,
    grupa="UI",
    klasa_wykonawcza="tarzanLCD1602.py",
)

play_p35_i2c_scl = _sygnal(
    nazwa="play_p35_i2c_scl",
    plytka="PLAY",
    pin=35,
    kanal=None,
    typ="F",
    kierunek="F",
    default="brak",
    opis="Magistrala I2C, linia SCL.",
    zrodlo="trPoPlayI2cScl",
    hardware_function=HW_I2C,
    hardware_label="I2C SCL / PoExtBus Clock",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="PLAY_P35_I2C_POEXTBUS",
    panel_port=7,
    grupa="CZUJNIKI",
    klasa_wykonawcza="tarzanPoSensors.py",
)

play_p36_i2c_sda = _sygnal(
    nazwa="play_p36_i2c_sda",
    plytka="PLAY",
    pin=36,
    kanal=None,
    typ="F",
    kierunek="F",
    default="brak",
    opis="Magistrala I2C, linia SDA.",
    zrodlo="trPoPlayI2cSda",
    hardware_function=HW_I2C,
    hardware_label="I2C SDA / PoExtBus Data",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="PLAY_P36_I2C_POEXTBUS",
    panel_port=7,
    grupa="CZUJNIKI",
    klasa_wykonawcza="tarzanPoSensors.py",
)

play_p37_step_disconnect_manual = _sygnal(
    nazwa="play_p37_step_disconnect_manual",
    plytka="PLAY",
    pin=37,
    kanal=None,
    typ="LH",
    kierunek="IN",
    default="0",
    opis="Odłączenie przewodów silników krokowych osi poziomej i pionowej, tryb ręczny.",
    zrodlo="tarzan_PoKeys57U_Play_MostekRec_Pokeys_En",
    hardware_function=HW_POEXTBUS,
    hardware_label="PoExtBus Latch / GPIO",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="PLAY_P37_POEXTBUS",
    panel_port=1,
    grupa="SYSTEM",
    klasa_wykonawcza="tarzanPoKeysPlay.py",
)

play_p38_step_dir_arm_h = _sygnal(
    nazwa="play_p38_step_dir_arm_h",
    plytka="PLAY",
    pin=38,
    kanal=None,
    typ="LH",
    kierunek="OUT",
    default="0",
    opis="Sygnał DIR sterownika krokowego osi poziomej ramienia.",
    zrodlo="tarzan_PoKeys57U_Play_Ssk_DirX_RamiePoziom",
    hardware_function=HW_PULSE,
    hardware_label="Pulse engine DIR X",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="PLAY_PULSE_ENGINE",
    panel_port=2,
    grupa="STEP_DIR",
    klasa_wykonawcza="tarzanPoStep25.py",
)

play_p39_step_dir_arm_v = _sygnal(
    nazwa="play_p39_step_dir_arm_v",
    plytka="PLAY",
    pin=39,
    kanal=None,
    typ="LH",
    kierunek="OUT",
    default="0",
    opis="Sygnał DIR sterownika krokowego osi pionowej ramienia.",
    zrodlo="tarzan_PoKeys57U_Play_Ssk_DirY_RamiePion",
    hardware_function=HW_PULSE,
    hardware_label="Pulse engine DIR Y",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="PLAY_PULSE_ENGINE",
    panel_port=3,
    grupa="STEP_DIR",
    klasa_wykonawcza="tarzanPoStep25.py",
)

play_p40_step_dir_arm_tilt = _sygnal(
    nazwa="play_p40_step_dir_arm_tilt",
    plytka="PLAY",
    pin=40,
    kanal=None,
    typ="LH",
    kierunek="OUT",
    default="0",
    opis="Sygnał DIR sterownika krokowego osi pochyłu ramienia.",
    zrodlo="tarzan_PoKeys57U_Play_Ssk_DirZ_RamiePochyl",
    hardware_function=HW_PULSE,
    hardware_label="Pulse engine DIR Z",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="PLAY_PULSE_ENGINE",
    panel_port=6,
    grupa="STEP_DIR",
    klasa_wykonawcza="tarzanPoStep25.py",
)

play_p41_mass_reg_enable = _sygnal(
    nazwa="play_p41_mass_reg_enable",
    plytka="PLAY",
    pin=41,
    kanal=None,
    typ="LH",
    kierunek="OUT",
    default="0",
    opis="Sygnał włączający regulator masy.",
    zrodlo="tarzan_PoKeys57U_Play_Regmasy_En",
    hardware_function=HW_ANALOG,
    hardware_label="Analog input capable pin 41 / GPIO used as digital out",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="PLAY_P41_ANALOG_GPIO",
    panel_port=8,
    grupa="REGULATOR_MASY",
    klasa_wykonawcza="tarzanRegulatorMasy.py",
)

play_p42_res = _sygnal(
    nazwa="play_p42_res",
    plytka="PLAY",
    pin=42,
    kanal=None,
    typ="RESERVED",
    kierunek="RESERVED",
    default="brak",
    opis="Pin niewykorzystany / brak definicji.",
    zrodlo="brak",
    hardware_function=HW_ANALOG,
    hardware_label="Analog input capable pin 42",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="PLAY_P42_ANALOG_GPIO",
    panel_port=None,
    grupa="REZERWA",
    klasa_wykonawcza="tarzanPoKeysPlay.py",
    status="REZERWOWY",
)

play_p43_res = _sygnal(
    nazwa="play_p43_res",
    plytka="PLAY",
    pin=43,
    kanal=None,
    typ="RESERVED",
    kierunek="RESERVED",
    default="brak",
    opis="Pin niewykorzystany / brak definicji.",
    zrodlo="brak",
    hardware_function=HW_ANALOG,
    hardware_label="Analog input capable pin 43",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="PLAY_P43_ANALOG_GPIO",
    panel_port=None,
    grupa="REZERWA",
    klasa_wykonawcza="tarzanPoKeysPlay.py",
    status="REZERWOWY",
)

play_p44_res = _sygnal(
    nazwa="play_p44_res",
    plytka="PLAY",
    pin=44,
    kanal=None,
    typ="RESERVED",
    kierunek="RESERVED",
    default="brak",
    opis="Pin niewykorzystany / brak definicji.",
    zrodlo="brak",
    hardware_function=HW_ANALOG,
    hardware_label="Analog input capable pin 44",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="PLAY_P44_ANALOG_GPIO",
    panel_port=None,
    grupa="REZERWA",
    klasa_wykonawcza="tarzanPoKeysPlay.py",
    status="REZERWOWY",
)

play_p45_rrp_pot_h = _sygnal(
    nazwa="play_p45_rrp_pot_h",
    plytka="PLAY",
    pin=45,
    kanal=None,
    typ="ANALOG",
    kierunek="IN",
    default="~",
    opis="Potencjometr ręcznego regulatora pozycji osi poziomej.",
    zrodlo="tarzan_PoKeys57U_Play_Pot_Rrp_RamiePoziom",
    hardware_function=HW_ANALOG,
    hardware_label="Analog input pin 45",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="PLAY_P45_ANALOG",
    panel_port=2,
    grupa="RRP",
    klasa_wykonawcza="tarzanRRP.py",
)

play_p46_step_ctr_arm_h = _sygnal(
    nazwa="play_p46_step_ctr_arm_h",
    plytka="PLAY",
    pin=46,
    kanal=None,
    typ="CTR",
    kierunek="OUT",
    default="1010...",
    opis="Sygnał CTR sterownika krokowego osi poziomej ramienia.",
    zrodlo="tarzan_PoKeys57U_Play_Ssk_CtrX_RamiePoziom",
    hardware_function=HW_PULSE,
    hardware_label="Pulse engine STEP X",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="PLAY_PULSE_ENGINE",
    panel_port=2,
    grupa="STEP_CTR",
    klasa_wykonawcza="tarzanPoStep25.py",
)

play_p47_rrp_pot_v = _sygnal(
    nazwa="play_p47_rrp_pot_v",
    plytka="PLAY",
    pin=47,
    kanal=None,
    typ="ANALOG",
    kierunek="IN",
    default="~",
    opis="Potencjometr ręcznego regulatora pozycji osi pionowej.",
    zrodlo="tarzan_PoKeys57U_Play_POT_Rrp_RamiePion",
    hardware_function=HW_ANALOG,
    hardware_label="Analog input pin 47",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="PLAY_P47_ANALOG",
    panel_port=3,
    grupa="RRP",
    klasa_wykonawcza="tarzanRRP.py",
)

play_p48_step_ctr_arm_v = _sygnal(
    nazwa="play_p48_step_ctr_arm_v",
    plytka="PLAY",
    pin=48,
    kanal=None,
    typ="CTR",
    kierunek="OUT",
    default="1010...",
    opis="Sygnał CTR sterownika krokowego osi pionowej ramienia.",
    zrodlo="tarzan_PoKeys57U_Play_Ssk_CtrX_RamiePion",
    hardware_function=HW_PULSE,
    hardware_label="Pulse engine STEP Y",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="PLAY_PULSE_ENGINE_PULLUP",
    panel_port=3,
    grupa="STEP_CTR",
    klasa_wykonawcza="tarzanPoStep25.py",
)

play_p49_step_ctr_arm_tilt = _sygnal(
    nazwa="play_p49_step_ctr_arm_tilt",
    plytka="PLAY",
    pin=49,
    kanal=None,
    typ="CTR",
    kierunek="OUT",
    default="1010...",
    opis="Sygnał CTR sterownika krokowego osi pochyłu ramienia.",
    zrodlo="tarzan_PoKeys57U_Play_Ssk_CtrX_RamiePochyl",
    hardware_function=HW_PULSE,
    hardware_label="Pulse engine STEP Z",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="PLAY_PULSE_ENGINE_PULLUP",
    panel_port=6,
    grupa="STEP_CTR",
    klasa_wykonawcza="tarzanPoStep25.py",
)

play_p50_step_en_arm_h = _sygnal(
    nazwa="play_p50_step_en_arm_h",
    plytka="PLAY",
    pin=50,
    kanal=None,
    typ="LH",
    kierunek="OUT",
    default="1",
    opis="Sygnał ENABLE przekaźnika przełączającego sterowanie osi poziomej między RRP a sterownikiem.",
    zrodlo="tarzan_PoKeys57U_Play_Ssk_Enx_RamiePoziom",
    hardware_function=HW_GPIO,
    hardware_label="GPIO pin 50",
    pin_is_fixed=True,
    is_shared_pin=False,
    conflict_group=None,
    panel_port=2,
    grupa="STEP_ENABLE",
    klasa_wykonawcza="tarzanPoStep25.py",
)

play_p51_step_en_arm_v = _sygnal(
    nazwa="play_p51_step_en_arm_v",
    plytka="PLAY",
    pin=51,
    kanal=None,
    typ="LH",
    kierunek="OUT",
    default="1",
    opis="Sygnał ENABLE przekaźnika przełączającego sterowanie osi pionowej między RRP a sterownikiem.",
    zrodlo="tarzan_PoKeys57U_Play_Ssk_Eny_RamiePion",
    hardware_function=HW_GPIO,
    hardware_label="GPIO pin 51",
    pin_is_fixed=True,
    is_shared_pin=False,
    conflict_group=None,
    panel_port=3,
    grupa="STEP_ENABLE",
    klasa_wykonawcza="tarzanPoStep25.py",
)

play_p52_step_en_arm_tilt = _sygnal(
    nazwa="play_p52_step_en_arm_tilt",
    plytka="PLAY",
    pin=52,
    kanal=None,
    typ="LH",
    kierunek="OUT",
    default="1",
    opis="Sygnał ENABLE przekaźnika przełączającego sterowanie osi pochyłu między RRP a sterownikiem.",
    zrodlo="tarzan_PoKeys57U_Play_Ssk_Enz_RamiePochyl",
    hardware_function=HW_PULSE,
    hardware_label="Emergency input capable pin 52 / GPIO",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="PLAY_P52_EMERGENCY",
    panel_port=6,
    grupa="STEP_ENABLE",
    klasa_wykonawcza="tarzanPoStep25.py",
)

play_p53_rrp_en_res = _sygnal(
    nazwa="play_p53_rrp_en_res",
    plytka="PLAY",
    pin=53,
    kanal=None,
    typ="LH",
    kierunek="IN",
    default="0",
    opis="Wolne wejście włączenia ręcznego regulatora pozycji RRP.",
    zrodlo="tarzan_PoKeys57U_Play_Rrp_En",
    hardware_function=HW_PULSE,
    hardware_label="Charge pump capable pin 53 / GPIO",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="PLAY_P53_CHARGE_PUMP",
    panel_port=1,
    grupa="RRP",
    klasa_wykonawcza="tarzanRRP.py",
    status="REZERWOWY",
)

play_p54_reset_do_not_use = _sygnal(
    nazwa="play_p54_reset_do_not_use",
    plytka="PLAY",
    pin=54,
    kanal=None,
    typ="RESERVED",
    kierunek="RESERVED",
    default="brak",
    opis="Pin reset odłączony, zostawić bez użycia.",
    zrodlo="RST - ODŁĄCZONY ZOSTAWIĆ",
    hardware_function=HW_SYSTEM,
    hardware_label="Recovery / boot special pin 54",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="PLAY_P54_SYSTEM",
    panel_port=None,
    grupa="SYSTEM",
    klasa_wykonawcza="tarzanPoKeysPlay.py",
    status="SPRZETOWY",
)

play_p55_bridge_rec_enable = _sygnal(
    nazwa="play_p55_bridge_rec_enable",
    plytka="PLAY",
    pin=55,
    kanal=None,
    typ="LH",
    kierunek="OUT",
    default="0",
    opis="Komunikacja PLAY-REC, opcja nagrywania włączona.",
    zrodlo="tarzan_PoKeys57U_Play_MostekRec_POKSYG_En",
    hardware_function=HW_GPIO,
    hardware_label="GPIO pin 55",
    pin_is_fixed=True,
    is_shared_pin=False,
    conflict_group=None,
    panel_port=1,
    grupa="MOSTEK_PLAY_REC",
    klasa_wykonawcza="tarzanPoKeysPlay.py",
)


# ======================================================================
# REC
# ======================================================================

rec_p01_copy_ctr_cam_h = _sygnal(
    nazwa="rec_p01_copy_ctr_cam_h",
    plytka="REC",
    pin=1,
    kanal=None,
    typ="CTR",
    kierunek="IN",
    default="1010...",
    opis="Kopia sygnału CTR osi poziomej głowicy kamery.",
    zrodlo="tarzan_PoKeys57U_Rec_SygCopy_KamSok_Ctr1_KamPoziom",
    hardware_function=HW_GPIO,
    hardware_label="Counter 1 / Fast encoder A1",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="REC_P01_COUNTER",
    panel_port=6,
    grupa="COPY_CAMERA",
    klasa_wykonawcza="tarzanPoKeysRec.py",
)

rec_p02_copy_ctr_cam_v = _sygnal(
    nazwa="rec_p02_copy_ctr_cam_v",
    plytka="REC",
    pin=2,
    kanal=None,
    typ="CTR",
    kierunek="IN",
    default="1010...",
    opis="Kopia sygnału CTR osi pionowej głowicy kamery.",
    zrodlo="tarzan_PoKeys57U_Rec_SygCopy_KamSok_Ctr2_KamPion",
    hardware_function=HW_GPIO,
    hardware_label="Counter 2 / Fast encoder B1",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="REC_P02_COUNTER",
    panel_port=6,
    grupa="COPY_CAMERA",
    klasa_wykonawcza="tarzanPoKeysRec.py",
)

rec_p03_copy_dir_cam_h = _sygnal(
    nazwa="rec_p03_copy_dir_cam_h",
    plytka="REC",
    pin=3,
    kanal=None,
    typ="LH",
    kierunek="IN",
    default="0",
    opis="Kopia sygnału DIR osi poziomej głowicy kamery.",
    zrodlo="tarzan_PoKeys57U_Rec_SygCopy_KamSok_Dir_KamPoziom",
    hardware_function=HW_GPIO,
    hardware_label="GPIO pin 3",
    pin_is_fixed=True,
    is_shared_pin=False,
    conflict_group=None,
    panel_port=6,
    grupa="COPY_CAMERA",
    klasa_wykonawcza="tarzanPoKeysRec.py",
)

rec_p04_copy_dir_cam_v = _sygnal(
    nazwa="rec_p04_copy_dir_cam_v",
    plytka="REC",
    pin=4,
    kanal=None,
    typ="LH",
    kierunek="IN",
    default="0",
    opis="Kopia sygnału DIR osi pionowej głowicy kamery.",
    zrodlo="tarzan_PoKeys57U_Rec_SygCopy_KamSok_Dir_KamPion",
    hardware_function=HW_GPIO,
    hardware_label="GPIO pin 4",
    pin_is_fixed=True,
    is_shared_pin=False,
    conflict_group=None,
    panel_port=6,
    grupa="COPY_CAMERA",
    klasa_wykonawcza="tarzanPoKeysRec.py",
)

rec_p05_copy_ctr_focus = _sygnal(
    nazwa="rec_p05_copy_ctr_focus",
    plytka="REC",
    pin=5,
    kanal=None,
    typ="CTR",
    kierunek="IN",
    default="1010...",
    opis="Kopia sygnału CTR osi ostrości kamery.",
    zrodlo="tarzan_PoKeys57U_Rec_SygCopy_KamSok_Ctr3_KamOstrosc",
    hardware_function=HW_GPIO,
    hardware_label="Counter 5 / Fast encoder A2",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="REC_P05_COUNTER",
    panel_port=5,
    grupa="COPY_CAMERA",
    klasa_wykonawcza="tarzanPoKeysRec.py",
)

rec_p06_copy_ctr_tilt = _sygnal(
    nazwa="rec_p06_copy_ctr_tilt",
    plytka="REC",
    pin=6,
    kanal=None,
    typ="CTR",
    kierunek="IN",
    default="1010...",
    opis="Kopia sygnału CTR osi pochyłu głowicy kamery.",
    zrodlo="tarzan_PoKeys57U_Rec_SygCopy_RamSok_Ctr_KamPochyl",
    hardware_function=HW_GPIO,
    hardware_label="Counter 6 / Fast encoder B2",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="REC_P06_COUNTER",
    panel_port=6,
    grupa="COPY_CAMERA",
    klasa_wykonawcza="tarzanPoKeysRec.py",
)

rec_p07_copy_dir_focus = _sygnal(
    nazwa="rec_p07_copy_dir_focus",
    plytka="REC",
    pin=7,
    kanal=None,
    typ="LH",
    kierunek="IN",
    default="0",
    opis="Kopia sygnału DIR osi ostrości kamery.",
    zrodlo="tarzan_PoKeys57U_Rec_SygCopy_KamSok_Dir3_KamOstrosc",
    hardware_function=HW_GPIO,
    hardware_label="GPIO pin 7",
    pin_is_fixed=True,
    is_shared_pin=False,
    conflict_group=None,
    panel_port=5,
    grupa="COPY_CAMERA",
    klasa_wykonawcza="tarzanPoKeysRec.py",
)

rec_p08_copy_dir_tilt = _sygnal(
    nazwa="rec_p08_copy_dir_tilt",
    plytka="REC",
    pin=8,
    kanal=None,
    typ="LH",
    kierunek="IN",
    default="0",
    opis="Kopia sygnału DIR osi pochyłu głowicy kamery.",
    zrodlo="tarzan_PoKeys57U_Rec_SygCopy_RamSok_Dir_kampochyl",
    hardware_function=HW_GPIO,
    hardware_label="Ultra fast encoder A",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="REC_P08_ULTRA_ENCODER",
    panel_port=6,
    grupa="COPY_CAMERA",
    klasa_wykonawcza="tarzanPoKeysRec.py",
)

rec_p09_led_data = _sygnal(
    nazwa="rec_p09_led_data",
    plytka="REC",
    pin=9,
    kanal=None,
    typ="F",
    kierunek="F",
    default="brak",
    opis="Wyświetlacz Matrix LED, linia DATA.",
    zrodlo="trPoRecLedData",
    hardware_function=HW_MATRIX_LED,
    hardware_label="Matrix LED 1 DATA / Counter 9",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="REC_P09_MATRIX_LED_1",
    panel_port=1,
    grupa="UI",
    klasa_wykonawcza="tarzanMatrixLED8x8.py",
)

rec_p10_led_latch = _sygnal(
    nazwa="rec_p10_led_latch",
    plytka="REC",
    pin=10,
    kanal=None,
    typ="F",
    kierunek="F",
    default="brak",
    opis="Wyświetlacz Matrix LED, linia LATCH.",
    zrodlo="trPoRecLedLatach",
    hardware_function=HW_MATRIX_LED,
    hardware_label="Matrix LED 1 LATCH",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="REC_P10_MATRIX_LED_1",
    panel_port=1,
    grupa="UI",
    klasa_wykonawcza="tarzanMatrixLED8x8.py",
)

rec_p11_led_clk = _sygnal(
    nazwa="rec_p11_led_clk",
    plytka="REC",
    pin=11,
    kanal=None,
    typ="F",
    kierunek="F",
    default="brak",
    opis="Wyświetlacz Matrix LED, linia CLOCK.",
    zrodlo="trPoRecLedCL",
    hardware_function=HW_MATRIX_LED,
    hardware_label="Matrix LED 1 CLOCK / Counter 11",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="REC_P11_MATRIX_LED_1",
    panel_port=1,
    grupa="UI",
    klasa_wykonawcza="tarzanMatrixLED8x8.py",
)

rec_p12_rec_dir_arm_h = _sygnal(
    nazwa="rec_p12_rec_dir_arm_h",
    plytka="REC",
    pin=12,
    kanal=None,
    typ="LH",
    kierunek="IN",
    default="0",
    opis="Sygnał DIR z ręcznego sterownika obrotowego osi poziomej ramienia do rejestracji.",
    zrodlo="tarzan_PoKeys57U_Rec_SygIn_RamSok_Dir_RamPoziom",
    hardware_function=HW_GPIO,
    hardware_label="Ultra fast encoder B",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="REC_P12_ULTRA_ENCODER",
    panel_port=2,
    grupa="RECORD",
    klasa_wykonawcza="tarzanTrybRecordMotion.py",
)

rec_p13_rec_dir_arm_v = _sygnal(
    nazwa="rec_p13_rec_dir_arm_v",
    plytka="REC",
    pin=13,
    kanal=None,
    typ="LH",
    kierunek="IN",
    default="0",
    opis="Sygnał DIR z ręcznego sterownika obrotowego osi pionowej ramienia do rejestracji.",
    zrodlo="tarzan_PoKeys57U_Rec_SygIn_RamSok_Dir_RamPion",
    hardware_function=HW_GPIO,
    hardware_label="Ultra fast encoder I",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="REC_P13_ULTRA_ENCODER",
    panel_port=3,
    grupa="RECORD",
    klasa_wykonawcza="tarzanTrybRecordMotion.py",
)

rec_p14_poextbus_motor_en = _sygnal(
    nazwa="rec_p14_poextbus_motor_en",
    plytka="REC",
    pin=14,
    kanal=None,
    typ="F",
    kierunek="F",
    default="brak",
    opis="Sterowanie płytką PoExtBusOC16-CNC, motor enable.",
    zrodlo="PoExtBusOC16CNCEn",
    hardware_function=HW_POEXTBUS,
    hardware_label="PoExtBus motor enable",
    pin_is_fixed=True,
    is_shared_pin=False,
    conflict_group=None,
    panel_port=1,
    grupa="CNC",
    klasa_wykonawcza="tarzanPoExtBus.py",
)

rec_p15_rec_ctr_arm_h = _sygnal(
    nazwa="rec_p15_rec_ctr_arm_h",
    plytka="REC",
    pin=15,
    kanal=None,
    typ="LH",
    kierunek="IN",
    default="0",
    opis="Sygnał CTR z ręcznego sterownika obrotowego osi poziomej ramienia do rejestracji.",
    zrodlo="tarzan_PoKeys57U_Rec_SygIn_RamSok_Ctr_RamPoziom",
    hardware_function=HW_GPIO,
    hardware_label="Counter 15 / Fast encoder A3",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="REC_P15_COUNTER",
    panel_port=2,
    grupa="RECORD",
    klasa_wykonawcza="tarzanTrybRecordMotion.py",
)

rec_p16_rec_ctr_arm_v = _sygnal(
    nazwa="rec_p16_rec_ctr_arm_v",
    plytka="REC",
    pin=16,
    kanal=None,
    typ="LH",
    kierunek="IN",
    default="0",
    opis="Sygnał CTR z ręcznego sterownika obrotowego osi pionowej ramienia do rejestracji.",
    zrodlo="tarzan_PoKeys57U_Rec_SygIn_RamSok_Ctr_RamPion",
    hardware_function=HW_GPIO,
    hardware_label="Counter 16 / Fast encoder B3",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="REC_P16_COUNTER",
    panel_port=3,
    grupa="RECORD",
    klasa_wykonawcza="tarzanTrybRecordMotion.py",
)

rec_p17_bridge_play_dir_x = _sygnal(
    nazwa="rec_p17_bridge_play_dir_x",
    plytka="REC",
    pin=17,
    kanal=None,
    typ="LH",
    kierunek="IN",
    default="0",
    opis="Mostek komunikacyjny z PLAY, kopia DIR X osi poziomej ramienia.",
    zrodlo="tarzan_PoKeys57U_Rec_MostekRec_DirX_RamiePoziom",
    hardware_function=HW_PWM,
    hardware_label="PWM pin 17 / input use",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="REC_P17_PWM",
    panel_port=1,
    grupa="MOSTEK_PLAY_REC",
    klasa_wykonawcza="tarzanPoKeysRec.py",
)

rec_p18_bridge_play_dir_y = _sygnal(
    nazwa="rec_p18_bridge_play_dir_y",
    plytka="REC",
    pin=18,
    kanal=None,
    typ="LH",
    kierunek="IN",
    default="0",
    opis="Mostek komunikacyjny z PLAY, kopia DIR Y osi pionowej ramienia.",
    zrodlo="tarzan_PoKeys57U_Rec_MostekRec_DirY_RamiePion",
    hardware_function=HW_PWM,
    hardware_label="PWM pin 18 / input use",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="REC_P18_PWM",
    panel_port=1,
    grupa="MOSTEK_PLAY_REC",
    klasa_wykonawcza="tarzanPoKeysRec.py",
)

rec_p19_bridge_play_dir_z = _sygnal(
    nazwa="rec_p19_bridge_play_dir_z",
    plytka="REC",
    pin=19,
    kanal=None,
    typ="LH",
    kierunek="IN",
    default="0",
    opis="Mostek komunikacyjny z PLAY, kopia DIR Z osi pochyłu ramienia.",
    zrodlo="tarzan_PoKeys57U_Rec_MostekRec_DirZ_RamiePochyl",
    hardware_function=HW_PWM,
    hardware_label="PWM pin 19 / input use",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="REC_P19_PWM",
    panel_port=1,
    grupa="MOSTEK_PLAY_REC",
    klasa_wykonawcza="tarzanPoKeysRec.py",
)

rec_p20_bridge_play_ctr_x = _sygnal(
    nazwa="rec_p20_bridge_play_ctr_x",
    plytka="REC",
    pin=20,
    kanal=None,
    typ="CTR",
    kierunek="IN",
    default="1010...",
    opis="Mostek komunikacyjny z PLAY, kopia CTR X osi poziomej ramienia.",
    zrodlo="tarzan_PoKeys57U_Rec_MostekRec_CtrX_RamiePoziom",
    hardware_function=HW_PWM,
    hardware_label="PWM pin 20 / input use",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="REC_P20_PWM",
    panel_port=1,
    grupa="MOSTEK_PLAY_REC",
    klasa_wykonawcza="tarzanPoKeysRec.py",
)

rec_p21_bridge_play_ctr_y = _sygnal(
    nazwa="rec_p21_bridge_play_ctr_y",
    plytka="REC",
    pin=21,
    kanal=None,
    typ="CTR",
    kierunek="IN",
    default="1010...",
    opis="Mostek komunikacyjny z PLAY, kopia CTR Y osi pionowej ramienia.",
    zrodlo="tarzan_PoKeys57U_Rec_MostekRec_CtrY_RamiePoziom",
    hardware_function=HW_PWM,
    hardware_label="PWM pin 21 / input use",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="REC_P21_PWM",
    panel_port=1,
    grupa="MOSTEK_PLAY_REC",
    klasa_wykonawcza="tarzanPoKeysRec.py",
)

rec_p22_bridge_play_ctr_z = _sygnal(
    nazwa="rec_p22_bridge_play_ctr_z",
    plytka="REC",
    pin=22,
    kanal=None,
    typ="CTR",
    kierunek="IN",
    default="1010...",
    opis="Mostek komunikacyjny z PLAY, kopia CTR Z osi pochyłu ramienia.",
    zrodlo="tarzan_PoKeys57U_Rec_MostekRec_CtrZ_RamiePoziom",
    hardware_function=HW_PWM,
    hardware_label="PWM pin 22 / input use",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="REC_P22_PWM",
    panel_port=1,
    grupa="MOSTEK_PLAY_REC",
    klasa_wykonawcza="tarzanPoKeysRec.py",
)

rec_p23_poextbus_p23 = _sygnal(
    nazwa="rec_p23_poextbus_p23",
    plytka="REC",
    pin=23,
    kanal=None,
    typ="F",
    kierunek="F",
    default="brak",
    opis="Sterowanie płytką PoExtBusOC16-CNC, pin 23.",
    zrodlo="PoExtBusOC16CNC23",
    hardware_function=HW_LCD,
    hardware_label="LCD DB7 / Matrix LED 2 DATA",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="REC_P23_LCD_MATRIX2",
    panel_port=1,
    grupa="CNC",
    klasa_wykonawcza="tarzanPoExtBus.py",
)

rec_p24_free = _sygnal(
    nazwa="rec_p24_free",
    plytka="REC",
    pin=24,
    kanal=None,
    typ="RESERVED",
    kierunek="RESERVED",
    default="brak",
    opis="Pin wolny.",
    zrodlo="WOLNY",
    hardware_function=HW_LCD,
    hardware_label="LCD DB6 / Matrix LED 2 LATCH",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="REC_P24_LCD_MATRIX2",
    panel_port=None,
    grupa="REZERWA",
    klasa_wykonawcza="tarzanPoKeysRec.py",
    status="REZERWOWY",
)

rec_p25_poextbus_p25 = _sygnal(
    nazwa="rec_p25_poextbus_p25",
    plytka="REC",
    pin=25,
    kanal=None,
    typ="F",
    kierunek="F",
    default="brak",
    opis="Sterowanie płytką PoExtBusOC16-CNC, pin 25.",
    zrodlo="PoExtBusOC16CNC25",
    hardware_function=HW_LCD,
    hardware_label="LCD DB5 / Matrix LED 2 CLOCK",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="REC_P25_LCD_MATRIX2",
    panel_port=1,
    grupa="CNC",
    klasa_wykonawcza="tarzanPoExtBus.py",
)

rec_p26_poextbus_p26 = _sygnal(
    nazwa="rec_p26_poextbus_p26",
    plytka="REC",
    pin=26,
    kanal=None,
    typ="F",
    kierunek="F",
    default="brak",
    opis="Sterowanie płytką PoExtBusOC16-CNC, pin 26.",
    zrodlo="PoExtBusOC16CNC26",
    hardware_function=HW_LCD,
    hardware_label="LCD DB4",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="REC_P26_LCD",
    panel_port=1,
    grupa="CNC",
    klasa_wykonawcza="tarzanPoExtBus.py",
)

rec_p27_free_limit_res = _sygnal(
    nazwa="rec_p27_free_limit_res",
    plytka="REC",
    pin=27,
    kanal=None,
    typ="LH",
    kierunek="IN",
    default="0",
    opis="Pin wolny, możliwe kopie sygnałów z krańcówek.",
    zrodlo="brak",
    hardware_function=HW_KEYBOARD,
    hardware_label="Keyboard / GPIO pin 27",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="REC_P27_KEYBOARD",
    panel_port=None,
    grupa="REZERWA",
    klasa_wykonawcza="tarzanPoKeysRec.py",
    status="REZERWOWY",
)

rec_p28_lcd_rw = _sygnal(
    nazwa="rec_p28_lcd_rw",
    plytka="REC",
    pin=28,
    kanal=None,
    typ="F",
    kierunek="F",
    default="brak",
    opis="Wyświetlacz LCD, pin RW.",
    zrodlo="trPoRecLcdRW",
    hardware_function=HW_LCD,
    hardware_label="LCD RW",
    pin_is_fixed=True,
    is_shared_pin=False,
    conflict_group="REC_LCD",
    panel_port=1,
    grupa="UI",
    klasa_wykonawcza="tarzanLCD1602.py",
)

rec_p29_lcd_rs = _sygnal(
    nazwa="rec_p29_lcd_rs",
    plytka="REC",
    pin=29,
    kanal=None,
    typ="F",
    kierunek="F",
    default="brak",
    opis="Wyświetlacz LCD, pin RS.",
    zrodlo="trPoRecLcdRS",
    hardware_function=HW_LCD,
    hardware_label="LCD RS",
    pin_is_fixed=True,
    is_shared_pin=False,
    conflict_group="REC_LCD",
    panel_port=1,
    grupa="UI",
    klasa_wykonawcza="tarzanLCD1602.py",
)

rec_p30_lcd_e = _sygnal(
    nazwa="rec_p30_lcd_e",
    plytka="REC",
    pin=30,
    kanal=None,
    typ="F",
    kierunek="F",
    default="brak",
    opis="Wyświetlacz LCD, pin E.",
    zrodlo="trPoRecLcdE",
    hardware_function=HW_LCD,
    hardware_label="LCD E",
    pin_is_fixed=True,
    is_shared_pin=False,
    conflict_group="REC_LCD",
    panel_port=1,
    grupa="UI",
    klasa_wykonawcza="tarzanLCD1602.py",
)

rec_p31_lcd_db7 = _sygnal(
    nazwa="rec_p31_lcd_db7",
    plytka="REC",
    pin=31,
    kanal=None,
    typ="F",
    kierunek="F",
    default="brak",
    opis="Wyświetlacz LCD, pin DB7.",
    zrodlo="trPoRecLcdDb7",
    hardware_function=HW_LCD,
    hardware_label="LCD secondary DB7",
    pin_is_fixed=True,
    is_shared_pin=False,
    conflict_group="REC_LCD_SECONDARY",
    panel_port=1,
    grupa="UI",
    klasa_wykonawcza="tarzanLCD1602.py",
)

rec_p32_lcd_db6 = _sygnal(
    nazwa="rec_p32_lcd_db6",
    plytka="REC",
    pin=32,
    kanal=None,
    typ="F",
    kierunek="F",
    default="brak",
    opis="Wyświetlacz LCD, pin DB6.",
    zrodlo="trPoRecLcdDb6",
    hardware_function=HW_LCD,
    hardware_label="LCD secondary DB6",
    pin_is_fixed=True,
    is_shared_pin=False,
    conflict_group="REC_LCD_SECONDARY",
    panel_port=1,
    grupa="UI",
    klasa_wykonawcza="tarzanLCD1602.py",
)

rec_p33_lcd_db5 = _sygnal(
    nazwa="rec_p33_lcd_db5",
    plytka="REC",
    pin=33,
    kanal=None,
    typ="F",
    kierunek="F",
    default="brak",
    opis="Wyświetlacz LCD, pin DB5.",
    zrodlo="trPoRecLcdDb5",
    hardware_function=HW_LCD,
    hardware_label="LCD secondary DB5",
    pin_is_fixed=True,
    is_shared_pin=False,
    conflict_group="REC_LCD_SECONDARY",
    panel_port=1,
    grupa="UI",
    klasa_wykonawcza="tarzanLCD1602.py",
)

rec_p34_lcd_db4 = _sygnal(
    nazwa="rec_p34_lcd_db4",
    plytka="REC",
    pin=34,
    kanal=None,
    typ="F",
    kierunek="F",
    default="brak",
    opis="Wyświetlacz LCD, pin DB4.",
    zrodlo="trPoRecLcdDb4",
    hardware_function=HW_LCD,
    hardware_label="LCD secondary DB4",
    pin_is_fixed=True,
    is_shared_pin=False,
    conflict_group="REC_LCD_SECONDARY",
    panel_port=1,
    grupa="UI",
    klasa_wykonawcza="tarzanLCD1602.py",
)

rec_p35_free_keyboard_old = _sygnal(
    nazwa="rec_p35_free_keyboard_old",
    plytka="REC",
    pin=35,
    kanal=None,
    typ="LH",
    kierunek="IN",
    default="0",
    opis="Pin wolny, byłe złącze keyboard.",
    zrodlo="brak",
    hardware_function=HW_I2C,
    hardware_label="I2C SCL / PoExtBus Clock",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="REC_P35_I2C_POEXTBUS",
    panel_port=None,
    grupa="REZERWA",
    klasa_wykonawcza="tarzanPoKeysRec.py",
    status="REZERWOWY",
)

rec_p36_mass_reg_enable = _sygnal(
    nazwa="rec_p36_mass_reg_enable",
    plytka="REC",
    pin=36,
    kanal=None,
    typ="LH",
    kierunek="OUT",
    default="0",
    opis="Sygnał włączający regulator masy.",
    zrodlo="tarzan_PoKeys57U_Rec_regmasy_En",
    hardware_function=HW_I2C,
    hardware_label="I2C SDA / PoExtBus Data",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="REC_P36_I2C_POEXTBUS",
    panel_port=8,
    grupa="REGULATOR_MASY",
    klasa_wykonawcza="tarzanRegulatorMasy.py",
)

rec_p37_bridge_play_rec_in = _sygnal(
    nazwa="rec_p37_bridge_play_rec_in",
    plytka="REC",
    pin=37,
    kanal=None,
    typ="LH",
    kierunek="IN",
    default="0",
    opis="Komunikacja pomiędzy PLAY i REC, wejście.",
    zrodlo="tarzan_PoKeys57U_Rec_MostekRec_PokRec_En",
    hardware_function=HW_POEXTBUS,
    hardware_label="PoExtBus Latch / GPIO",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="REC_P37_POEXTBUS",
    panel_port=1,
    grupa="MOSTEK_PLAY_REC",
    klasa_wykonawcza="tarzanPoKeysRec.py",
)

rec_p38_auto_enable = _sygnal(
    nazwa="rec_p38_auto_enable",
    plytka="REC",
    pin=38,
    kanal=None,
    typ="LH",
    kierunek="OUT",
    default="0",
    opis="Włączenie przekaźników odcinających sygnały sterowników obrotowych, auto enable.",
    zrodlo="tarzan_PoKeys57U_Rec_Auto_En",
    hardware_function=HW_PULSE,
    hardware_label="Pulse engine DIR X / GPIO",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="REC_PULSE_ENGINE",
    panel_port=1,
    grupa="AUTO",
    klasa_wykonawcza="tarzanTrybAllAuto.py",
)

rec_p39_shock_sensor = _sygnal(
    nazwa="rec_p39_shock_sensor",
    plytka="REC",
    pin=39,
    kanal=None,
    typ="LH",
    kierunek="IN",
    default="0",
    opis="Wejście czujnika wstrząsowego.",
    zrodlo="tarzan_PoKeys57U_Rec_Dcopy_GlowicaKam_End1_prawo",
    hardware_function=HW_PULSE,
    hardware_label="Pulse engine DIR Y / GPIO",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="REC_PULSE_ENGINE",
    panel_port=7,
    grupa="CZUJNIKI",
    klasa_wykonawcza="tarzanPoSensors.py",
)

rec_p40_free_limit_res = _sygnal(
    nazwa="rec_p40_free_limit_res",
    plytka="REC",
    pin=40,
    kanal=None,
    typ="LH",
    kierunek="IN",
    default="0",
    opis="Pin wolny, możliwe kopie sygnałów z krańcówek.",
    zrodlo="brak",
    hardware_function=HW_PULSE,
    hardware_label="Pulse engine DIR Z / GPIO",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="REC_PULSE_ENGINE",
    panel_port=None,
    grupa="REZERWA",
    klasa_wykonawcza="tarzanPoKeysRec.py",
    status="REZERWOWY",
)

rec_p41_free_aux_pot = _sygnal(
    nazwa="rec_p41_free_aux_pot",
    plytka="REC",
    pin=41,
    kanal=None,
    typ="RESERVED",
    kierunek="RESERVED",
    default="brak",
    opis="Pin wolny / potencjometr pomocniczy.",
    zrodlo="trPOReckPotV",
    hardware_function=HW_ANALOG,
    hardware_label="Analog input pin 41",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="REC_P41_ANALOG",
    panel_port=None,
    grupa="REZERWA",
    klasa_wykonawcza="tarzanPoKeysRec.py",
    status="REZERWOWY",
)

rec_p42_free_keyboard_old = _sygnal(
    nazwa="rec_p42_free_keyboard_old",
    plytka="REC",
    pin=42,
    kanal=None,
    typ="LH",
    kierunek="IN",
    default="0",
    opis="Pin wolny, byłe złącze keyboard.",
    zrodlo="brak",
    hardware_function=HW_ANALOG,
    hardware_label="Analog input pin 42",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="REC_P42_ANALOG",
    panel_port=None,
    grupa="REZERWA",
    klasa_wykonawcza="tarzanPoKeysRec.py",
    status="REZERWOWY",
)

rec_p43_free_keyboard_old = _sygnal(
    nazwa="rec_p43_free_keyboard_old",
    plytka="REC",
    pin=43,
    kanal=None,
    typ="LH",
    kierunek="IN",
    default="0",
    opis="Pin wolny, byłe złącze keyboard.",
    zrodlo="brak",
    hardware_function=HW_ANALOG,
    hardware_label="Analog input pin 43",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="REC_P43_ANALOG",
    panel_port=None,
    grupa="REZERWA",
    klasa_wykonawcza="tarzanPoKeysRec.py",
    status="REZERWOWY",
)

rec_p44_free_keyboard_old = _sygnal(
    nazwa="rec_p44_free_keyboard_old",
    plytka="REC",
    pin=44,
    kanal=None,
    typ="LH",
    kierunek="IN",
    default="0",
    opis="Pin wolny, byłe złącze keyboard.",
    zrodlo="brak",
    hardware_function=HW_ANALOG,
    hardware_label="Analog input pin 44",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="REC_P44_ANALOG",
    panel_port=None,
    grupa="REZERWA",
    klasa_wykonawcza="tarzanPoKeysRec.py",
    status="REZERWOWY",
)

rec_p45_sw_f1 = _sygnal(
    nazwa="rec_p45_sw_f1",
    plytka="REC",
    pin=45,
    kanal=None,
    typ="LH",
    kierunek="IN",
    default="0",
    opis="Przycisk funkcyjny F1.",
    zrodlo="tarzan_PoKeys57U_Rec_Sw_F1",
    hardware_function=HW_ANALOG,
    hardware_label="Analog input capable pin 45 / GPIO",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="REC_P45_ANALOG",
    panel_port=1,
    grupa="UI",
    klasa_wykonawcza="tarzanPrzyciskiFunkcyjne.py",
)

rec_p46_led_f1 = _sygnal(
    nazwa="rec_p46_led_f1",
    plytka="REC",
    pin=46,
    kanal=None,
    typ="LH",
    kierunek="IN",
    default="0",
    opis="Dioda sygnalizacyjna przełącznika F1.",
    zrodlo="tarzan_PoKeys57U_Rec_Swled_F1",
    hardware_function=HW_PULSE,
    hardware_label="Pulse engine STEP X / GPIO",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="REC_PULSE_ENGINE",
    panel_port=1,
    grupa="UI",
    klasa_wykonawcza="tarzanPrzyciskiFunkcyjne.py",
)

rec_p47_sw_f2 = _sygnal(
    nazwa="rec_p47_sw_f2",
    plytka="REC",
    pin=47,
    kanal=None,
    typ="LH",
    kierunek="IN",
    default="0",
    opis="Przycisk funkcyjny F2.",
    zrodlo="tarzan_PoKeys57U_Rec_Sw_F2",
    hardware_function=HW_ANALOG,
    hardware_label="Analog input capable pin 47 / GPIO",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="REC_P47_ANALOG",
    panel_port=1,
    grupa="UI",
    klasa_wykonawcza="tarzanPrzyciskiFunkcyjne.py",
)

rec_p48_led_f2 = _sygnal(
    nazwa="rec_p48_led_f2",
    plytka="REC",
    pin=48,
    kanal=None,
    typ="LH",
    kierunek="IN",
    default="0",
    opis="Dioda sygnalizacyjna przełącznika F2.",
    zrodlo="tarzan_PoKeys57U_Rec_SwLed_F2",
    hardware_function=HW_PULSE,
    hardware_label="Pulse engine STEP Y / GPIO",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="REC_PULSE_ENGINE_PULLUP",
    panel_port=1,
    grupa="UI",
    klasa_wykonawcza="tarzanPrzyciskiFunkcyjne.py",
)

rec_p49_sw_f3 = _sygnal(
    nazwa="rec_p49_sw_f3",
    plytka="REC",
    pin=49,
    kanal=None,
    typ="LH",
    kierunek="IN",
    default="0",
    opis="Przycisk funkcyjny F3.",
    zrodlo="tarzan_PoKeys57U_Rec_Sw_F3",
    hardware_function=HW_PULSE,
    hardware_label="Pulse engine STEP Z / GPIO",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="REC_PULSE_ENGINE_PULLUP",
    panel_port=1,
    grupa="UI",
    klasa_wykonawcza="tarzanPrzyciskiFunkcyjne.py",
)

rec_p50_led_f3 = _sygnal(
    nazwa="rec_p50_led_f3",
    plytka="REC",
    pin=50,
    kanal=None,
    typ="LH",
    kierunek="IN",
    default="0",
    opis="Dioda sygnalizacyjna przełącznika F3.",
    zrodlo="tarzan_PoKeys57U_Rec_SwLed_F3",
    hardware_function=HW_GPIO,
    hardware_label="GPIO pin 50",
    pin_is_fixed=True,
    is_shared_pin=False,
    conflict_group=None,
    panel_port=1,
    grupa="UI",
    klasa_wykonawcza="tarzanPrzyciskiFunkcyjne.py",
)

rec_p51_sw_f4 = _sygnal(
    nazwa="rec_p51_sw_f4",
    plytka="REC",
    pin=51,
    kanal=None,
    typ="LH",
    kierunek="IN",
    default="0",
    opis="Przycisk funkcyjny F4.",
    zrodlo="tarzan_PoKeys57U_Rec_SW_F4",
    hardware_function=HW_GPIO,
    hardware_label="GPIO pin 51",
    pin_is_fixed=True,
    is_shared_pin=False,
    conflict_group=None,
    panel_port=1,
    grupa="UI",
    klasa_wykonawcza="tarzanPrzyciskiFunkcyjne.py",
)

rec_p52_led_f4 = _sygnal(
    nazwa="rec_p52_led_f4",
    plytka="REC",
    pin=52,
    kanal=None,
    typ="LH",
    kierunek="IN",
    default="0",
    opis="Dioda sygnalizacyjna przełącznika F4.",
    zrodlo="tarzan_PoKeys57U_Rec_SwLed_F4",
    hardware_function=HW_PULSE,
    hardware_label="Emergency input capable pin 52 / GPIO",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="REC_P52_EMERGENCY",
    panel_port=1,
    grupa="UI",
    klasa_wykonawcza="tarzanPrzyciskiFunkcyjne.py",
)

rec_p53_copy_cam_v_limit_up = _sygnal(
    nazwa="rec_p53_copy_cam_v_limit_up",
    plytka="REC",
    pin=53,
    kanal=None,
    typ="LH",
    kierunek="IN",
    default="0",
    opis="Kopia krańcówki głowicy kamery, ruch w górę.",
    zrodlo="tarzan_PoKeys57U_Rec_MolexDCopy_GlowicaKam_End3_gora",
    hardware_function=HW_PULSE,
    hardware_label="Charge pump capable pin 53 / GPIO",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="REC_P53_CHARGE_PUMP",
    panel_port=7,
    grupa="COPY_CAMERA",
    klasa_wykonawcza="tarzanPoKeysRec.py",
)

rec_p54_bridge_play_rec_out = _sygnal(
    nazwa="rec_p54_bridge_play_rec_out",
    plytka="REC",
    pin=54,
    kanal=None,
    typ="LH",
    kierunek="OUT",
    default="0",
    opis="Komunikacja pomiędzy PLAY i REC, wyjście.",
    zrodlo="tarzan_PoKeys57U_Rec_MostekRec_PokRec_En",
    hardware_function=HW_SYSTEM,
    hardware_label="Recovery / boot special pin 54 / GPIO",
    pin_is_fixed=True,
    is_shared_pin=True,
    conflict_group="REC_P54_SYSTEM",
    panel_port=1,
    grupa="MOSTEK_PLAY_REC",
    klasa_wykonawcza="tarzanPoKeysRec.py",
)

rec_p55_free_cart_spare = _sygnal(
    nazwa="rec_p55_free_cart_spare",
    plytka="REC",
    pin=55,
    kanal=None,
    typ="RESERVED",
    kierunek="RESERVED",
    default="brak",
    opis="Pin wolny, komunikacja z wózkiem lub zapas.",
    zrodlo="WOLNY",
    hardware_function=HW_GPIO,
    hardware_label="GPIO pin 55",
    pin_is_fixed=True,
    is_shared_pin=False,
    conflict_group=None,
    panel_port=None,
    grupa="REZERWA",
    klasa_wykonawcza="tarzanPoKeysRec.py",
    status="REZERWOWY",
)


# ======================================================================
# CNC / AUTOMATYKA
# ======================================================================

cnc_x_cam_h_ctr = _sygnal(
    nazwa="cnc_x_cam_h_ctr",
    plytka="CNC",
    pin=None,
    kanal="X / ID1",
    typ="CTR",
    kierunek="OUT",
    default="1010...",
    opis="Wyjście automatyki CTR osi poziomej kamery.",
    zrodlo="tarzan_PoKeys57U_Cnc_AutoKam_Ctr_Poziom",
    hardware_function=HW_PULSE,
    hardware_label="CNC axis X STEP / ID1",
    pin_is_fixed=True,
    is_shared_pin=False,
    conflict_group=None,
    panel_port=6,
    grupa="CNC_CAMERA",
    klasa_wykonawcza="tarzanTrybAllAuto.py",
)

cnc_x_cam_h_dir = _sygnal(
    nazwa="cnc_x_cam_h_dir",
    plytka="CNC",
    pin=None,
    kanal="X / ID1",
    typ="LH",
    kierunek="OUT",
    default="0",
    opis="Wyjście automatyki DIR osi poziomej kamery.",
    zrodlo="tarzan_PoKeys57U_Cnc_AutoKam_Dir_Poziom",
    hardware_function=HW_PULSE,
    hardware_label="CNC axis X DIR / ID1",
    pin_is_fixed=True,
    is_shared_pin=False,
    conflict_group=None,
    panel_port=6,
    grupa="CNC_CAMERA",
    klasa_wykonawcza="tarzanTrybAllAuto.py",
)

cnc_y_cam_v_ctr = _sygnal(
    nazwa="cnc_y_cam_v_ctr",
    plytka="CNC",
    pin=None,
    kanal="Y / ID2",
    typ="CTR",
    kierunek="OUT",
    default="1010...",
    opis="Wyjście automatyki CTR osi pionowej kamery.",
    zrodlo="tarzan_PoKeys57U_Cnc_AutoKam_Ctr_Pion",
    hardware_function=HW_PULSE,
    hardware_label="CNC axis Y STEP / ID2",
    pin_is_fixed=True,
    is_shared_pin=False,
    conflict_group=None,
    panel_port=6,
    grupa="CNC_CAMERA",
    klasa_wykonawcza="tarzanTrybAllAuto.py",
)

cnc_y_cam_v_dir = _sygnal(
    nazwa="cnc_y_cam_v_dir",
    plytka="CNC",
    pin=None,
    kanal="Y / ID2",
    typ="LH",
    kierunek="OUT",
    default="0",
    opis="Wyjście automatyki DIR osi pionowej kamery.",
    zrodlo="tarzan_PoKeys57U_Cnc_AutoKam_Dir_Pion",
    hardware_function=HW_PULSE,
    hardware_label="CNC axis Y DIR / ID2",
    pin_is_fixed=True,
    is_shared_pin=False,
    conflict_group=None,
    panel_port=6,
    grupa="CNC_CAMERA",
    klasa_wykonawcza="tarzanTrybAllAuto.py",
)

cnc_z_focus_ctr = _sygnal(
    nazwa="cnc_z_focus_ctr",
    plytka="CNC",
    pin=None,
    kanal="Z / ID3",
    typ="CTR",
    kierunek="OUT",
    default="1010...",
    opis="Wyjście automatyki CTR osi ostrości kamery.",
    zrodlo="tarzan_PoKeys57U_Cnc_AutoKam_Ctr_Ostrosc",
    hardware_function=HW_PULSE,
    hardware_label="CNC axis Z STEP / ID3",
    pin_is_fixed=True,
    is_shared_pin=False,
    conflict_group=None,
    panel_port=5,
    grupa="CNC_CAMERA",
    klasa_wykonawcza="tarzanTrybAllAuto.py",
)

cnc_z_focus_dir = _sygnal(
    nazwa="cnc_z_focus_dir",
    plytka="CNC",
    pin=None,
    kanal="Z / ID3",
    typ="LH",
    kierunek="OUT",
    default="0",
    opis="Wyjście automatyki DIR osi ostrości kamery.",
    zrodlo="tarzan_PoKeys57U_Cnc_AutoKam_Dir_Ostrosc",
    hardware_function=HW_PULSE,
    hardware_label="CNC axis Z DIR / ID3",
    pin_is_fixed=True,
    is_shared_pin=False,
    conflict_group=None,
    panel_port=5,
    grupa="CNC_CAMERA",
    klasa_wykonawcza="tarzanTrybAllAuto.py",
)

cnc_a_arm_tilt_ctr = _sygnal(
    nazwa="cnc_a_arm_tilt_ctr",
    plytka="CNC",
    pin=None,
    kanal="A / ID4",
    typ="CTR",
    kierunek="OUT",
    default="1010...",
    opis="Wyjście automatyki CTR osi pochyłu ramienia.",
    zrodlo="tarzan_PoKeys57U_Cnc_AutoRam_Ctr_Pochyl",
    hardware_function=HW_PULSE,
    hardware_label="CNC axis A STEP / ID4",
    pin_is_fixed=True,
    is_shared_pin=False,
    conflict_group=None,
    panel_port=6,
    grupa="CNC_ARM",
    klasa_wykonawcza="tarzanTrybAllAuto.py",
)

cnc_a_arm_tilt_dir = _sygnal(
    nazwa="cnc_a_arm_tilt_dir",
    plytka="CNC",
    pin=None,
    kanal="A / ID4",
    typ="LH",
    kierunek="OUT",
    default="0",
    opis="Wyjście automatyki DIR osi pochyłu ramienia.",
    zrodlo="tarzan_PoKeys57U_Cnc_AutoRam_Dir_Pochyl",
    hardware_function=HW_PULSE,
    hardware_label="CNC axis A DIR / ID4",
    pin_is_fixed=True,
    is_shared_pin=False,
    conflict_group=None,
    panel_port=6,
    grupa="CNC_ARM",
    klasa_wykonawcza="tarzanTrybAllAuto.py",
)

cnc_b_arm_h_ctr = _sygnal(
    nazwa="cnc_b_arm_h_ctr",
    plytka="CNC",
    pin=None,
    kanal="B / ID5",
    typ="CTR",
    kierunek="OUT",
    default="1010...",
    opis="Wyjście automatyki CTR osi poziomej ramienia.",
    zrodlo="tarzan_PoKeys57U_Cnc_AutoRam_Ctr_Poziom",
    hardware_function=HW_PULSE,
    hardware_label="CNC axis B STEP / ID5",
    pin_is_fixed=True,
    is_shared_pin=False,
    conflict_group=None,
    panel_port=2,
    grupa="CNC_ARM",
    klasa_wykonawcza="tarzanTrybAllAuto.py",
)

cnc_b_arm_h_dir = _sygnal(
    nazwa="cnc_b_arm_h_dir",
    plytka="CNC",
    pin=None,
    kanal="B / ID5",
    typ="LH",
    kierunek="OUT",
    default="0",
    opis="Wyjście automatyki DIR osi poziomej ramienia.",
    zrodlo="tarzan_PoKeys57U_Cnc_AutoRam_Dir_Poziom",
    hardware_function=HW_PULSE,
    hardware_label="CNC axis B DIR / ID5",
    pin_is_fixed=True,
    is_shared_pin=False,
    conflict_group=None,
    panel_port=2,
    grupa="CNC_ARM",
    klasa_wykonawcza="tarzanTrybAllAuto.py",
)

cnc_c_arm_v_ctr = _sygnal(
    nazwa="cnc_c_arm_v_ctr",
    plytka="CNC",
    pin=None,
    kanal="C / ID6",
    typ="CTR",
    kierunek="OUT",
    default="1010...",
    opis="Wyjście automatyki CTR osi pionowej ramienia.",
    zrodlo="tarzan_PoKeys57U_Cnc_AutoRam_Ctr_Pion",
    hardware_function=HW_PULSE,
    hardware_label="CNC axis C STEP / ID6",
    pin_is_fixed=True,
    is_shared_pin=False,
    conflict_group=None,
    panel_port=3,
    grupa="CNC_ARM",
    klasa_wykonawcza="tarzanTrybAllAuto.py",
)

cnc_c_arm_v_dir = _sygnal(
    nazwa="cnc_c_arm_v_dir",
    plytka="CNC",
    pin=None,
    kanal="C / ID6",
    typ="LH",
    kierunek="OUT",
    default="0",
    opis="Wyjście automatyki DIR osi pionowej ramienia.",
    zrodlo="tarzan_PoKeys57U_Cnc_AutoRam_Dir_Pion",
    hardware_function=HW_PULSE,
    hardware_label="CNC axis C DIR / ID6",
    pin_is_fixed=True,
    is_shared_pin=False,
    conflict_group=None,
    panel_port=3,
    grupa="CNC_ARM",
    klasa_wykonawcza="tarzanTrybAllAuto.py",
)

cnc_d_cart_ctr = _sygnal(
    nazwa="cnc_d_cart_ctr",
    plytka="CNC",
    pin=None,
    kanal="D",
    typ="CTR",
    kierunek="OUT",
    default="1010...",
    opis="Wyjście automatyki CTR wózka.",
    zrodlo="tarzan_PoKeys57U_Cnc_AutoWozek_Ctr_Pion",
    hardware_function=HW_PULSE,
    hardware_label="CNC axis D STEP",
    pin_is_fixed=True,
    is_shared_pin=False,
    conflict_group=None,
    panel_port=None,
    grupa="CNC_CART",
    klasa_wykonawcza="tarzanTrybAllAuto.py",
)

cnc_d_cart_dir = _sygnal(
    nazwa="cnc_d_cart_dir",
    plytka="CNC",
    pin=None,
    kanal="D",
    typ="LH",
    kierunek="OUT",
    default="0",
    opis="Wyjście automatyki DIR wózka.",
    zrodlo="tarzan_PoKeys57U_Cnc_AutoWozek_Dir_Pion",
    hardware_function=HW_PULSE,
    hardware_label="CNC axis D DIR",
    pin_is_fixed=True,
    is_shared_pin=False,
    conflict_group=None,
    panel_port=None,
    grupa="CNC_CART",
    klasa_wykonawcza="tarzanTrybAllAuto.py",
)


# ======================================================================
# SŁOWNIKI ZBIORCZE
# ======================================================================

SYGNALY_PLAY: Dict[str, TarzanSygnal] = {
    sygnal.nazwa: sygnal
    for sygnal in [
        play_p01_arm_h_auto_limit,
        play_p02_arm_h_limit_right,
        play_p03_arm_h_limit_left,
        play_p04_arm_v_limit_up,
        play_p05_cam_h_limit_right,
        play_p06_cam_h_limit_left,
        play_p07_cam_v_limit_up,
        play_p08_cam_v_limit_down,
        play_p09_arm_v_auto_limit,
        play_p10_cam_tilt_limit,
        play_p11_cart_limit_end,
        play_p12_arm_v_limit_down,
        play_p13_mass_reg_limit_add,
        play_p14_drone_release,
        play_p15_rrp_dir_h_res,
        play_p16_action_led,
        play_p17_bridge_rec_dir_x,
        play_p18_bridge_rec_dir_y,
        play_p19_bridge_rec_dir_z,
        play_p20_bridge_rec_ctr_x,
        play_p21_bridge_rec_ctr_y,
        play_p22_bridge_rec_ctr_z,
        play_p23_mass_reg_limit_remove,
        play_p24_kb4,
        play_p25_kb3,
        play_p26_kb2,
        play_p27_kb1,
        play_p28_lcd_rw,
        play_p29_lcd_rs,
        play_p30_lcd_e,
        play_p31_lcd_db7,
        play_p32_lcd_db6,
        play_p33_lcd_db5,
        play_p34_lcd_db4,
        play_p35_i2c_scl,
        play_p36_i2c_sda,
        play_p37_step_disconnect_manual,
        play_p38_step_dir_arm_h,
        play_p39_step_dir_arm_v,
        play_p40_step_dir_arm_tilt,
        play_p41_mass_reg_enable,
        play_p42_res,
        play_p43_res,
        play_p44_res,
        play_p45_rrp_pot_h,
        play_p46_step_ctr_arm_h,
        play_p47_rrp_pot_v,
        play_p48_step_ctr_arm_v,
        play_p49_step_ctr_arm_tilt,
        play_p50_step_en_arm_h,
        play_p51_step_en_arm_v,
        play_p52_step_en_arm_tilt,
        play_p53_rrp_en_res,
        play_p54_reset_do_not_use,
        play_p55_bridge_rec_enable,
    ]
}

SYGNALY_REC: Dict[str, TarzanSygnal] = {
    sygnal.nazwa: sygnal
    for sygnal in [
        rec_p01_copy_ctr_cam_h,
        rec_p02_copy_ctr_cam_v,
        rec_p03_copy_dir_cam_h,
        rec_p04_copy_dir_cam_v,
        rec_p05_copy_ctr_focus,
        rec_p06_copy_ctr_tilt,
        rec_p07_copy_dir_focus,
        rec_p08_copy_dir_tilt,
        rec_p09_led_data,
        rec_p10_led_latch,
        rec_p11_led_clk,
        rec_p12_rec_dir_arm_h,
        rec_p13_rec_dir_arm_v,
        rec_p14_poextbus_motor_en,
        rec_p15_rec_ctr_arm_h,
        rec_p16_rec_ctr_arm_v,
        rec_p17_bridge_play_dir_x,
        rec_p18_bridge_play_dir_y,
        rec_p19_bridge_play_dir_z,
        rec_p20_bridge_play_ctr_x,
        rec_p21_bridge_play_ctr_y,
        rec_p22_bridge_play_ctr_z,
        rec_p23_poextbus_p23,
        rec_p24_free,
        rec_p25_poextbus_p25,
        rec_p26_poextbus_p26,
        rec_p27_free_limit_res,
        rec_p28_lcd_rw,
        rec_p29_lcd_rs,
        rec_p30_lcd_e,
        rec_p31_lcd_db7,
        rec_p32_lcd_db6,
        rec_p33_lcd_db5,
        rec_p34_lcd_db4,
        rec_p35_free_keyboard_old,
        rec_p36_mass_reg_enable,
        rec_p37_bridge_play_rec_in,
        rec_p38_auto_enable,
        rec_p39_shock_sensor,
        rec_p40_free_limit_res,
        rec_p41_free_aux_pot,
        rec_p42_free_keyboard_old,
        rec_p43_free_keyboard_old,
        rec_p44_free_keyboard_old,
        rec_p45_sw_f1,
        rec_p46_led_f1,
        rec_p47_sw_f2,
        rec_p48_led_f2,
        rec_p49_sw_f3,
        rec_p50_led_f3,
        rec_p51_sw_f4,
        rec_p52_led_f4,
        rec_p53_copy_cam_v_limit_up,
        rec_p54_bridge_play_rec_out,
        rec_p55_free_cart_spare,
    ]
}

SYGNALY_CNC: Dict[str, TarzanSygnal] = {
    sygnal.nazwa: sygnal
    for sygnal in [
        cnc_x_cam_h_ctr,
        cnc_x_cam_h_dir,
        cnc_y_cam_v_ctr,
        cnc_y_cam_v_dir,
        cnc_z_focus_ctr,
        cnc_z_focus_dir,
        cnc_a_arm_tilt_ctr,
        cnc_a_arm_tilt_dir,
        cnc_b_arm_h_ctr,
        cnc_b_arm_h_dir,
        cnc_c_arm_v_ctr,
        cnc_c_arm_v_dir,
        cnc_d_cart_ctr,
        cnc_d_cart_dir,
    ]
}

SYGNALY_UI: Dict[str, TarzanSygnal] = {
    sygnal.nazwa: sygnal
    for sygnal in [
        play_p16_action_led,
        play_p24_kb4,
        play_p25_kb3,
        play_p26_kb2,
        play_p27_kb1,
        play_p28_lcd_rw,
        play_p29_lcd_rs,
        play_p30_lcd_e,
        play_p31_lcd_db7,
        play_p32_lcd_db6,
        play_p33_lcd_db5,
        play_p34_lcd_db4,
        rec_p09_led_data,
        rec_p10_led_latch,
        rec_p11_led_clk,
        rec_p28_lcd_rw,
        rec_p29_lcd_rs,
        rec_p30_lcd_e,
        rec_p31_lcd_db7,
        rec_p32_lcd_db6,
        rec_p33_lcd_db5,
        rec_p34_lcd_db4,
        rec_p45_sw_f1,
        rec_p46_led_f1,
        rec_p47_sw_f2,
        rec_p48_led_f2,
        rec_p49_sw_f3,
        rec_p50_led_f3,
        rec_p51_sw_f4,
        rec_p52_led_f4,
    ]
}

SYGNALY_CZUJNIKI: Dict[str, TarzanSygnal] = {
    sygnal.nazwa: sygnal
    for sygnal in [
        play_p35_i2c_scl,
        play_p36_i2c_sda,
        rec_p39_shock_sensor,
    ]
}

SYGNALY_REZERWOWE: Dict[str, TarzanSygnal] = {
    sygnal.nazwa: sygnal
    for sygnal in [
        play_p15_rrp_dir_h_res,
        play_p42_res,
        play_p43_res,
        play_p44_res,
        play_p53_rrp_en_res,
        rec_p24_free,
        rec_p27_free_limit_res,
        rec_p35_free_keyboard_old,
        rec_p40_free_limit_res,
        rec_p41_free_aux_pot,
        rec_p42_free_keyboard_old,
        rec_p43_free_keyboard_old,
        rec_p44_free_keyboard_old,
        rec_p55_free_cart_spare,
    ]
}

WSZYSTKIE_SYGNALY: Dict[str, TarzanSygnal] = {}
WSZYSTKIE_SYGNALY.update(SYGNALY_PLAY)
WSZYSTKIE_SYGNALY.update(SYGNALY_REC)
WSZYSTKIE_SYGNALY.update(SYGNALY_CNC)