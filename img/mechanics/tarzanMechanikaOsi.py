class TarzanMechanics:
    """
    TARZAN – definicja mechaniki osi

    Klasa opisuje fizyczne parametry napędów systemu TARZAN.
    Zawiera wszystkie stałe wynikające z budowy mechanicznej
    urządzenia oraz funkcje przeliczeniowe ruchu silników
    krokowych na rzeczywisty ruch osi.

    W klasie zdefiniowane są:
    - parametry silników krokowych,
    - przełożenia mechaniczne osi,
    - zakresy maksymalnych cykli ruchu,
    - minimalne czasy wykonania cyklu,
    - przeliczniki impulsów STEP,
    - strefy łagodnego rozruchu osi,
    - limity impulsów dla początkowej fazy ruchu,
    - ramy czasowe rozruchu,
    - ogólne limity prędkości dla ruchu ustalonego.

    Dane zapisane w tej klasie są parametrami konstrukcyjnymi
    urządzenia i stanowią podstawę wszystkich obliczeń ruchu.

    Klasa definiuje robocze granice pracy osi, natomiast
    ostateczną ochronę mechaniczną zapewniają krańcówki
    zamontowane w konstrukcji urządzenia.

    Parametry techniczne przekładni i silników – ile potrzeba
    impulsów na jeden pełny cykl osi:
    - oś pozioma kamery:   28800
    - oś pionowa kamery:   12800
    - oś pochyłu kamery:    3200
    - oś ostrości kamery:  30764
    - oś pionowa ramienia: 28485
    - oś pozioma ramienia: 92273

    W systemie TARZAN szczególnie ważny jest początek ruchu osi.
    Pierwsze milimetry lub pierwsze stopnie ruchu są najbardziej
    obciążające mechanicznie, ponieważ wtedy układ:
    - wychodzi ze stanu równowagi,
    - pokonuje bezwładność początkową,
    - pokonuje napięcia i luzy mechaniczne,
    - przechodzi z bezruchu do pracy kontrolowanej.

    Dlatego każda oś otrzymuje 3 stany rozruchowe:
    1. START_SETTLE – bardzo wolne, delikatne wyprowadzenie osi
       z bezruchu i z równowagi.
    2. START_RAMP – łagodne rozpędzanie po początkowym ruszeniu.
    3. CRUISE – normalna prędkość robocza osi.

    Dodatkowo dla rozruchu określone są ramy czasowe.
    Rozruch nie może działać bez końca – musi zamykać się
    w zdefiniowanym czasie, praktycznie w zakresie około 1–2 s,
    zależnie od rodzaju osi i obciążenia mechanicznego.

    Parametry tych stref są częścią definicji mechanicznej osi
    i nie powinny być traktowane jako swobodne parametry użytkowe.
    """

    # =========================================================
    # KOMPENSACJA LUZÓW PRZEKŁADNI
    # =========================================================

    """
    Sekcja definiuje orientacyjną kompensację luzów przekładni
    zębatych w postaci dodatkowych impulsów STEP.

    Wartości te są wartościami startowymi i powinny zostać
    później skalibrowane empirycznie na gotowym mechanizmie.

    Kompensacja wykonywana jest przy zmianie kierunku ruchu osi.

    Osie kamery oraz oś ostrości posiadają jedną parę zębatek,
    dlatego mają jeden główny luz przekładni.

    Osie ramienia posiadają dwa stopnie zazębienia:
        gear1 -> gear2
        gear3 -> gear4

    przy czym gear2 i gear3 leżą na tej samej osi pośredniej.
    Oznacza to, że całkowity luz osi ramienia jest większy
    i wymaga większej kompensacji.

    """

    CAMERA_HORIZONTAL_BACKLASH_COMPENSATION_PULSES = 12
    CAMERA_VERTICAL_BACKLASH_COMPENSATION_PULSES = 12
    CAMERA_TILT_BACKLASH_COMPENSATION_PULSES = 6
    CAMERA_FOCUS_BACKLASH_COMPENSATION_PULSES = 8

    ARM_VERTICAL_BACKLASH_COMPENSATION_PULSES = 28
    ARM_HORIZONTAL_BACKLASH_COMPENSATION_PULSES = 32

    # =========================================================
    # PARAMETRY SILNIKÓW KROKOWYCH
    # =========================================================

    """
    W systemie TARZAN stosowane są silniki krokowe:

    - typ: 2-fazowe
    - krok podstawowy: 1.8°
    - liczba kroków na obrót: 200
    - mikrokrok sterownika: 1/32

    Na tej podstawie wyliczana jest liczba impulsów STEP
    potrzebnych do wykonania jednego pełnego obrotu silnika.

    Jest to baza dla wszystkich dalszych obliczeń mechaniki osi,
    niezależnie od rodzaju przekładni i typu ruchu.
    """

    MOTOR_STEP_ANGLE_DEG = 1.8
    MOTOR_FULL_STEPS_PER_REV = 200
    DRIVER_MICROSTEP = 32

    MOTOR_PULSES_PER_REV = MOTOR_FULL_STEPS_PER_REV * DRIVER_MICROSTEP
    MOTOR_DEG_PER_PULSE = 360.0 / MOTOR_PULSES_PER_REV

    # =========================================================
    # OSIE KAMERY
    # =========================================================

    """
    Sekcja zawiera parametry mechaniczne osi kamery.

    Dla osi obrotowych definiowane są:
    - liczba zębów zębatki silnika,
    - liczba zębów zębatki osi,
    - maksymalny kąt pełnego cyklu,
    - minimalny czas wykonania cyklu.

    Dla osi pochyłu stosowany jest napęd śrubowy,
    dlatego zamiast kąta definiowany jest skok liniowy.

    Dodatkowo dla każdej osi definiowane są strefy rozruchu:
    - START_SETTLE
    - START_RAMP
    - CRUISE

    Dla faz START_SETTLE i START_RAMP określone są:
    - zakres ruchu tej fazy,
    - maksymalna dopuszczalna prędkość impulsów STEP,
    - maksymalny czas trwania tej fazy.
    """

    # 1. OŚ POZIOMA KAMERY
    #
    # Oś obrotowa kamery z prostą przekładnią zębatą.
    # Oś ta wymaga łagodnego rozruchu, ale może wejść
    # w prędkość roboczą szybciej niż osie ramienia.

    CAMERA_HORIZONTAL_MOTOR_TEETH = 12
    CAMERA_HORIZONTAL_AXIS_TEETH = 72
    CAMERA_HORIZONTAL_MAX_CYCLE_ANGLE_DEG = 270.0
    CAMERA_HORIZONTAL_MIN_CYCLE_TIME_SEC = 3.0

    CAMERA_HORIZONTAL_START_SETTLE_ANGLE_DEG = 0.5
    CAMERA_HORIZONTAL_START_SETTLE_MAX_PULSES_PER_SEC = 300.0
    CAMERA_HORIZONTAL_START_SETTLE_TIME_SEC = 0.30

    CAMERA_HORIZONTAL_START_RAMP_ANGLE_DEG = 4.0
    CAMERA_HORIZONTAL_START_RAMP_MAX_PULSES_PER_SEC = 1500.0
    CAMERA_HORIZONTAL_START_RAMP_TIME_SEC = 0.90

    # 2. OŚ PIONOWA KAMERY
    #
    # Oś pionowa kamery pracuje z mniejszym pełnym zakresem
    # ruchu niż oś pozioma kamery. Rozruch nadal powinien
    # być miękki, ale z nieco mniejszym limitem niż w osi
    # poziomej.

    CAMERA_VERTICAL_MOTOR_TEETH = 12
    CAMERA_VERTICAL_AXIS_TEETH = 72
    CAMERA_VERTICAL_MAX_CYCLE_ANGLE_DEG = 120.0
    CAMERA_VERTICAL_MIN_CYCLE_TIME_SEC = 2.0

    CAMERA_VERTICAL_START_SETTLE_ANGLE_DEG = 0.5
    CAMERA_VERTICAL_START_SETTLE_MAX_PULSES_PER_SEC = 250.0
    CAMERA_VERTICAL_START_SETTLE_TIME_SEC = 0.30

    CAMERA_VERTICAL_START_RAMP_ANGLE_DEG = 4.0
    CAMERA_VERTICAL_START_RAMP_MAX_PULSES_PER_SEC = 1200.0
    CAMERA_VERTICAL_START_RAMP_TIME_SEC = 0.90

    # 3. OŚ POCHYŁU KAMERY – NAPĘD ŚRUBOWY
    #
    # Oś pochyłu kamery nie jest osią obrotową.
    # Silnik napędza śrubę liniową, która wysuwa się
    # i cofa, powodując zmianę pochylenia kamery.
    #
    # Parametry:
    # - skok śruby na jeden obrót silnika
    # - maksymalny dopuszczalny skok śruby
    # - minimalny czas wykonania pełnego skoku
    #
    # Dla tej osi strefy rozruchu są definiowane w mm,
    # a nie w stopniach.

    CAMERA_TILT_SCREW_MM_PER_MOTOR_REV = 30.0
    CAMERA_TILT_MAX_SCREW_STROKE_MM = 15.0
    CAMERA_TILT_MIN_CYCLE_TIME_SEC = 1.0

    CAMERA_TILT_START_SETTLE_STROKE_MM = 0.5
    CAMERA_TILT_START_SETTLE_MAX_PULSES_PER_SEC = 150.0
    CAMERA_TILT_START_SETTLE_TIME_SEC = 0.25

    CAMERA_TILT_START_RAMP_STROKE_MM = 3.0
    CAMERA_TILT_START_RAMP_MAX_PULSES_PER_SEC = 600.0
    CAMERA_TILT_START_RAMP_TIME_SEC = 0.75

    # 4. OŚ OSTROŚCI KAMERY
    #
    # Oś sterująca ostrością obiektywu.
    # Oś ta nie przenosi dużych obciążeń mechanicznych,
    # dlatego dopuszczalny jest znacznie szybszy ruch
    # niż w osiach konstrukcyjnych ramienia.
    #
    # Mimo to nadal stosowany jest miękki start, aby
    # zachować płynność i dokładność.

    CAMERA_FOCUS_MOTOR_TEETH = 22
    CAMERA_FOCUS_AXIS_TEETH = 141
    CAMERA_FOCUS_MAX_CYCLE_ANGLE_DEG = 270.0
    CAMERA_FOCUS_MIN_CYCLE_TIME_SEC = 1.0

    CAMERA_FOCUS_START_SETTLE_ANGLE_DEG = 0.3
    CAMERA_FOCUS_START_SETTLE_MAX_PULSES_PER_SEC = 400.0
    CAMERA_FOCUS_START_SETTLE_TIME_SEC = 0.20

    CAMERA_FOCUS_START_RAMP_ANGLE_DEG = 2.0
    CAMERA_FOCUS_START_RAMP_MAX_PULSES_PER_SEC = 2000.0
    CAMERA_FOCUS_START_RAMP_TIME_SEC = 0.50

    # =========================================================
    # OSIE RAMIENIA
    # =========================================================

    """
    Osie ramienia posiadają przekładnie złożone
    składające się z czterech zębatek.

    Przełożenie jest wyznaczane przez dwa stopnie:
        gear1 -> gear2
        gear3 -> gear4

    Osie ramienia są najbardziej obciążone mechanicznie,
    dlatego ich strefy START_SETTLE i START_RAMP mają
    szczególne znaczenie dla zachowania precyzji oraz
    uniknięcia gwałtownego wyprowadzenia układu z równowagi.

    W osiach ramienia rozruch powinien być wyraźnie spokojniejszy
    niż w osiach kamery i powinien zamykać się w czasie zbliżonym
    do 1.5–2.0 s.
    """

    # 5. OŚ PIONOWA RAMIENIA
    #
    # Oś nośna ramienia. Ruch startowy powinien być
    # wyraźnie łagodny, ponieważ pierwsze stopnie ruchu
    # są silnie obciążone zmianą równowagi układu.

    ARM_VERTICAL_GEAR_1_MOTOR_TEETH = 12
    ARM_VERTICAL_GEAR_2_INTERMEDIATE_TEETH = 25
    ARM_VERTICAL_GEAR_3_INTERMEDIATE_TEETH = 22
    ARM_VERTICAL_GEAR_4_AXIS_TEETH = 141

    ARM_VERTICAL_MAX_CYCLE_ANGLE_DEG = 120.0
    ARM_VERTICAL_MIN_CYCLE_TIME_SEC = 10.0

    ARM_VERTICAL_START_SETTLE_ANGLE_DEG = 1.0
    ARM_VERTICAL_START_SETTLE_MAX_PULSES_PER_SEC = 150.0
    ARM_VERTICAL_START_SETTLE_TIME_SEC = 0.50

    ARM_VERTICAL_START_RAMP_ANGLE_DEG = 6.0
    ARM_VERTICAL_START_RAMP_MAX_PULSES_PER_SEC = 900.0
    ARM_VERTICAL_START_RAMP_TIME_SEC = 1.00

    # 6. OŚ POZIOMA RAMIENIA
    #
    # Oś pozioma ramienia posiada największą przekładnię
    # i największy moment po przełożeniu.
    # Jest to oś szczególnie wrażliwa na gwałtowny start.
    #
    # Pierwszy ruch musi wejść bardzo spokojnie, aby nie
    # wyprowadzić układu z równowagi i nie gubić precyzji.

    ARM_HORIZONTAL_GEAR_1_MOTOR_TEETH = 12
    ARM_HORIZONTAL_GEAR_2_INTERMEDIATE_TEETH = 25
    ARM_HORIZONTAL_GEAR_3_INTERMEDIATE_TEETH = 22
    ARM_HORIZONTAL_GEAR_4_AXIS_TEETH = 203

    ARM_HORIZONTAL_MAX_CYCLE_ANGLE_DEG = 270.0
    ARM_HORIZONTAL_MIN_CYCLE_TIME_SEC = 15.0

    ARM_HORIZONTAL_START_SETTLE_ANGLE_DEG = 1.0
    ARM_HORIZONTAL_START_SETTLE_MAX_PULSES_PER_SEC = 200.0
    ARM_HORIZONTAL_START_SETTLE_TIME_SEC = 0.60

    ARM_HORIZONTAL_START_RAMP_ANGLE_DEG = 8.0
    ARM_HORIZONTAL_START_RAMP_MAX_PULSES_PER_SEC = 1200.0
    ARM_HORIZONTAL_START_RAMP_TIME_SEC = 1.20

    # =========================================================
    # FUNKCJE OGÓLNE PRZEKŁADNI
    # =========================================================

    @classmethod
    def simpleGearRatio(cls, motor_teeth: int, axis_teeth: int) -> float:
        """
        Oblicza przełożenie prostej przekładni zębatej.

        Przełożenie liczone jest jako:
            zębatka osi / zębatka silnika

        Funkcja służy dla osi, w których napęd przechodzi
        bezpośrednio z zębatki silnika na zębatkę osi
        wykonawczej.

        Jeżeli liczba zębów którejkolwiek zębatki jest
        niepoprawna lub równa zero, funkcja zwraca 0.0.
        """
        if motor_teeth <= 0 or axis_teeth <= 0:
            return 0.0
        return axis_teeth / motor_teeth

    @classmethod
    def compoundGearRatio(
        cls,
        gear_1_motor_teeth: int,
        gear_2_intermediate_teeth: int,
        gear_3_intermediate_teeth: int,
        gear_4_axis_teeth: int
    ) -> float:
        """
        Oblicza przełożenie przekładni złożonej 4-zębatkowej.

        Przekładnia liczona jest w dwóch stopniach:
            gear1 -> gear2
            gear3 -> gear4

        gdzie gear2 i gear3 pracują na osi pośredniej.

        Całkowite przełożenie:
            (gear2 / gear1) * (gear4 / gear3)

        Funkcja stosowana jest dla osi ramienia TARZAN.
        Jeżeli którakolwiek liczba zębów jest niepoprawna,
        funkcja zwraca 0.0.
        """
        if (
            gear_1_motor_teeth <= 0
            or gear_2_intermediate_teeth <= 0
            or gear_3_intermediate_teeth <= 0
            or gear_4_axis_teeth <= 0
        ):
            return 0.0

        stage_1 = gear_2_intermediate_teeth / gear_1_motor_teeth
        stage_2 = gear_4_axis_teeth / gear_3_intermediate_teeth
        return stage_1 * stage_2

    # =========================================================
    # FUNKCJE IMPULSÓW STEP
    # =========================================================

    @classmethod
    def pulsesPerAxisRevFromRatio(cls, ratio: float) -> float:
        """
        Oblicza liczbę impulsów STEP potrzebnych
        do wykonania jednego pełnego obrotu osi.

        Wartość ta wynika bezpośrednio z:
        - liczby impulsów na obrót silnika,
        - całkowitego przełożenia mechanicznego osi.

        Dla niepoprawnego przełożenia funkcja zwraca 0.0.
        """
        if ratio <= 0:
            return 0.0
        return cls.MOTOR_PULSES_PER_REV * ratio

    @classmethod
    def pulsesPerCycleFromRatio(cls, ratio: float, cycle_angle_deg: float) -> float:
        """
        Oblicza liczbę impulsów potrzebnych
        do wykonania jednego pełnego cyklu osi obrotowej.

        Pełny cykl liczony jest jako określony kąt roboczy osi,
        a nie jako pełne 360 stopni obrotu.

        Funkcja korzysta z:
        - przełożenia osi,
        - liczby impulsów na jeden obrót osi,
        - maksymalnego kąta pełnego cyklu.

        Dla niepoprawnych danych wejściowych funkcja zwraca 0.0.
        """
        pulses_per_rev = cls.pulsesPerAxisRevFromRatio(ratio)
        if pulses_per_rev <= 0 or cycle_angle_deg <= 0:
            return 0.0
        return (cycle_angle_deg / 360.0) * pulses_per_rev

    @classmethod
    def pulsesPerPhaseFromRatio(cls, ratio: float, phase_angle_deg: float) -> float:
        """
        Oblicza liczbę impulsów potrzebnych
        do wykonania wybranego fragmentu ruchu osi obrotowej.

        Funkcja służy między innymi do obliczenia:
        - START_SETTLE
        - START_RAMP

        gdzie faza ruchu nie obejmuje całego cyklu,
        lecz tylko jego początkową część.
        """
        return cls.pulsesPerCycleFromRatio(ratio, phase_angle_deg)

    @classmethod
    def maxPulsesPerSecondFromRatio(cls, ratio: float, cycle_angle_deg: float, cycle_time_sec: float) -> float:
        """
        Oblicza maksymalną dopuszczalną prędkość
        generowania impulsów STEP dla danej osi.

        Wartość ta określa górną granicę prędkości impulsów
        przy założeniu, że pełny cykl osi ma zostać wykonany
        w minimalnym dopuszczalnym czasie.

        Funkcja wylicza więc ogólny limit roboczy osi
        dla fazy ruchu ustalonego CRUISE.

        Dla niepoprawnych danych wejściowych zwracane jest 0.0.
        """
        pulses_per_cycle = cls.pulsesPerCycleFromRatio(ratio, cycle_angle_deg)
        if pulses_per_cycle <= 0 or cycle_time_sec <= 0:
            return 0.0
        return pulses_per_cycle / cycle_time_sec

    @classmethod
    def phaseAveragePulsesPerSecond(cls, phase_pulses: float, phase_time_sec: float) -> float:
        """
        Oblicza średnią prędkość impulsów STEP dla danej fazy ruchu.

        Funkcja pozwala sprawdzić, czy zadany:
        - zakres fazy,
        - oraz czas trwania fazy

        są spójne z zadanym limitem impulsów STEP.

        Zwracana wartość nie zastępuje twardego limitu fazy,
        lecz pokazuje średnie tempo wynikające z geometrii ruchu.
        """
        if phase_pulses <= 0 or phase_time_sec <= 0:
            return 0.0
        return phase_pulses / phase_time_sec

    @classmethod
    def totalStartTime(cls, settle_time_sec: float, ramp_time_sec: float) -> float:
        """
        Oblicza całkowity czas rozruchu osi.

        Rozruch rozumiany jest jako suma faz:
        - START_SETTLE
        - START_RAMP

        Po zakończeniu tego czasu oś przechodzi
        do normalnej fazy ruchu CRUISE.
        """
        if settle_time_sec < 0 or ramp_time_sec < 0:
            return 0.0
        return settle_time_sec + ramp_time_sec

    # =========================================================
    # NAPĘD ŚRUBOWY – OŚ POCHYŁU
    # =========================================================

    @classmethod
    def cameraTiltPulsesPerMm(cls) -> float:
        """
        Oblicza liczbę impulsów STEP potrzebnych
        do przesunięcia śruby o 1 mm.

        Funkcja dotyczy osi pochyłu kamery, która
        pracuje liniowo, a nie obrotowo.

        Wynik zależy od:
        - liczby impulsów na jeden obrót silnika,
        - skoku śruby przypadającego na jeden obrót silnika.

        Dla niepoprawnego skoku śruby zwracane jest 0.0.
        """
        if cls.CAMERA_TILT_SCREW_MM_PER_MOTOR_REV <= 0:
            return 0.0
        return cls.MOTOR_PULSES_PER_REV / cls.CAMERA_TILT_SCREW_MM_PER_MOTOR_REV

    @classmethod
    def cameraTiltPulsesPerCycle(cls) -> float:
        """
        Oblicza liczbę impulsów potrzebnych
        do wykonania pełnego skoku śruby.

        Pełny cykl osi pochyłu kamery rozumiany jest tutaj
        jako pełny dopuszczalny skok śruby, a nie kąt obrotu.

        Funkcja wykorzystuje:
        - liczbę impulsów na 1 mm,
        - maksymalny dopuszczalny skok śruby.

        Dla niepoprawnych danych zwracane jest 0.0.
        """
        pulses_per_mm = cls.cameraTiltPulsesPerMm()
        if pulses_per_mm <= 0:
            return 0.0
        return pulses_per_mm * cls.CAMERA_TILT_MAX_SCREW_STROKE_MM

    @classmethod
    def cameraTiltPulsesPerPhase(cls, phase_stroke_mm: float) -> float:
        """
        Oblicza liczbę impulsów potrzebnych
        do wykonania wybranego fragmentu skoku śruby.

        Funkcja służy między innymi do obliczania:
        - START_SETTLE
        - START_RAMP

        dla osi pochyłu kamery.
        """
        pulses_per_mm = cls.cameraTiltPulsesPerMm()
        if pulses_per_mm <= 0 or phase_stroke_mm <= 0:
            return 0.0
        return pulses_per_mm * phase_stroke_mm

    @classmethod
    def cameraTiltMaxPulsesPerSecond(cls) -> float:
        """
        Oblicza maksymalną prędkość impulsów
        dla osi pochyłu kamery.

        Jest to ogólny limit prędkości dla pełnego skoku śruby,
        wynikający z:
        - liczby impulsów pełnego cyklu,
        - minimalnego czasu wykonania cyklu.

        Limit ten dotyczy pełnego ruchu osi. Dodatkowo początek
        ruchu powinien respektować osobne ograniczenia
        START_SETTLE i START_RAMP.
        """
        pulses_per_cycle = cls.cameraTiltPulsesPerCycle()
        if cls.CAMERA_TILT_MIN_CYCLE_TIME_SEC <= 0:
            return 0.0
        return pulses_per_cycle / cls.CAMERA_TILT_MIN_CYCLE_TIME_SEC

    # =========================================================
    # OŚ POZIOMA KAMERY
    # =========================================================

    @classmethod
    def cameraHorizontalRatio(cls) -> float:
        """
        Zwraca całkowite przełożenie osi poziomej kamery.
        """
        return cls.simpleGearRatio(
            cls.CAMERA_HORIZONTAL_MOTOR_TEETH,
            cls.CAMERA_HORIZONTAL_AXIS_TEETH
        )

    @classmethod
    def cameraHorizontalPulsesPerCycle(cls) -> float:
        """
        Zwraca liczbę impulsów STEP na pełny cykl osi poziomej kamery.
        """
        return cls.pulsesPerCycleFromRatio(
            cls.cameraHorizontalRatio(),
            cls.CAMERA_HORIZONTAL_MAX_CYCLE_ANGLE_DEG
        )

    @classmethod
    def cameraHorizontalCruiseMaxPulsesPerSecond(cls) -> float:
        """
        Zwraca ogólny limit prędkości impulsów STEP
        dla fazy CRUISE osi poziomej kamery.
        """
        return cls.maxPulsesPerSecondFromRatio(
            cls.cameraHorizontalRatio(),
            cls.CAMERA_HORIZONTAL_MAX_CYCLE_ANGLE_DEG,
            cls.CAMERA_HORIZONTAL_MIN_CYCLE_TIME_SEC
        )

    @classmethod
    def cameraHorizontalStartSettlePulses(cls) -> float:
        """
        Zwraca liczbę impulsów przypisaną do fazy START_SETTLE
        osi poziomej kamery.
        """
        return cls.pulsesPerPhaseFromRatio(
            cls.cameraHorizontalRatio(),
            cls.CAMERA_HORIZONTAL_START_SETTLE_ANGLE_DEG
        )

    @classmethod
    def cameraHorizontalStartSettleAveragePulsesPerSecond(cls) -> float:
        """
        Zwraca średnią prędkość impulsów wynikającą z geometrii
        i czasu fazy START_SETTLE osi poziomej kamery.
        """
        return cls.phaseAveragePulsesPerSecond(
            cls.cameraHorizontalStartSettlePulses(),
            cls.CAMERA_HORIZONTAL_START_SETTLE_TIME_SEC
        )

    @classmethod
    def cameraHorizontalStartRampPulses(cls) -> float:
        """
        Zwraca liczbę impulsów przypisaną do fazy START_RAMP
        osi poziomej kamery.
        """
        return cls.pulsesPerPhaseFromRatio(
            cls.cameraHorizontalRatio(),
            cls.CAMERA_HORIZONTAL_START_RAMP_ANGLE_DEG
        )

    @classmethod
    def cameraHorizontalStartRampAveragePulsesPerSecond(cls) -> float:
        """
        Zwraca średnią prędkość impulsów wynikającą z geometrii
        i czasu fazy START_RAMP osi poziomej kamery.
        """
        return cls.phaseAveragePulsesPerSecond(
            cls.cameraHorizontalStartRampPulses(),
            cls.CAMERA_HORIZONTAL_START_RAMP_TIME_SEC
        )

    @classmethod
    def cameraHorizontalStartTotalTimeSec(cls) -> float:
        """
        Zwraca łączny czas rozruchu osi poziomej kamery.
        """
        return cls.totalStartTime(
            cls.CAMERA_HORIZONTAL_START_SETTLE_TIME_SEC,
            cls.CAMERA_HORIZONTAL_START_RAMP_TIME_SEC
        )

    # =========================================================
    # OŚ PIONOWA KAMERY
    # =========================================================

    @classmethod
    def cameraVerticalRatio(cls) -> float:
        """
        Zwraca całkowite przełożenie osi pionowej kamery.
        """
        return cls.simpleGearRatio(
            cls.CAMERA_VERTICAL_MOTOR_TEETH,
            cls.CAMERA_VERTICAL_AXIS_TEETH
        )

    @classmethod
    def cameraVerticalPulsesPerCycle(cls) -> float:
        """
        Zwraca liczbę impulsów STEP na pełny cykl osi pionowej kamery.
        """
        return cls.pulsesPerCycleFromRatio(
            cls.cameraVerticalRatio(),
            cls.CAMERA_VERTICAL_MAX_CYCLE_ANGLE_DEG
        )

    @classmethod
    def cameraVerticalCruiseMaxPulsesPerSecond(cls) -> float:
        """
        Zwraca ogólny limit prędkości impulsów STEP
        dla fazy CRUISE osi pionowej kamery.
        """
        return cls.maxPulsesPerSecondFromRatio(
            cls.cameraVerticalRatio(),
            cls.CAMERA_VERTICAL_MAX_CYCLE_ANGLE_DEG,
            cls.CAMERA_VERTICAL_MIN_CYCLE_TIME_SEC
        )

    @classmethod
    def cameraVerticalStartSettlePulses(cls) -> float:
        """
        Zwraca liczbę impulsów przypisaną do fazy START_SETTLE
        osi pionowej kamery.
        """
        return cls.pulsesPerPhaseFromRatio(
            cls.cameraVerticalRatio(),
            cls.CAMERA_VERTICAL_START_SETTLE_ANGLE_DEG
        )

    @classmethod
    def cameraVerticalStartSettleAveragePulsesPerSecond(cls) -> float:
        """
        Zwraca średnią prędkość impulsów wynikającą z geometrii
        i czasu fazy START_SETTLE osi pionowej kamery.
        """
        return cls.phaseAveragePulsesPerSecond(
            cls.cameraVerticalStartSettlePulses(),
            cls.CAMERA_VERTICAL_START_SETTLE_TIME_SEC
        )

    @classmethod
    def cameraVerticalStartRampPulses(cls) -> float:
        """
        Zwraca liczbę impulsów przypisaną do fazy START_RAMP
        osi pionowej kamery.
        """
        return cls.pulsesPerPhaseFromRatio(
            cls.cameraVerticalRatio(),
            cls.CAMERA_VERTICAL_START_RAMP_ANGLE_DEG
        )

    @classmethod
    def cameraVerticalStartRampAveragePulsesPerSecond(cls) -> float:
        """
        Zwraca średnią prędkość impulsów wynikającą z geometrii
        i czasu fazy START_RAMP osi pionowej kamery.
        """
        return cls.phaseAveragePulsesPerSecond(
            cls.cameraVerticalStartRampPulses(),
            cls.CAMERA_VERTICAL_START_RAMP_TIME_SEC
        )

    @classmethod
    def cameraVerticalStartTotalTimeSec(cls) -> float:
        """
        Zwraca łączny czas rozruchu osi pionowej kamery.
        """
        return cls.totalStartTime(
            cls.CAMERA_VERTICAL_START_SETTLE_TIME_SEC,
            cls.CAMERA_VERTICAL_START_RAMP_TIME_SEC
        )

    # =========================================================
    # OŚ POCHYŁU KAMERY
    # =========================================================

    @classmethod
    def cameraTiltCruiseMaxPulsesPerSecond(cls) -> float:
        """
        Zwraca ogólny limit prędkości impulsów STEP
        dla fazy CRUISE osi pochyłu kamery.
        """
        return cls.cameraTiltMaxPulsesPerSecond()

    @classmethod
    def cameraTiltStartSettlePulses(cls) -> float:
        """
        Zwraca liczbę impulsów przypisaną do fazy START_SETTLE
        osi pochyłu kamery.
        """
        return cls.cameraTiltPulsesPerPhase(
            cls.CAMERA_TILT_START_SETTLE_STROKE_MM
        )

    @classmethod
    def cameraTiltStartSettleAveragePulsesPerSecond(cls) -> float:
        """
        Zwraca średnią prędkość impulsów wynikającą z geometrii
        i czasu fazy START_SETTLE osi pochyłu kamery.
        """
        return cls.phaseAveragePulsesPerSecond(
            cls.cameraTiltStartSettlePulses(),
            cls.CAMERA_TILT_START_SETTLE_TIME_SEC
        )

    @classmethod
    def cameraTiltStartRampPulses(cls) -> float:
        """
        Zwraca liczbę impulsów przypisaną do fazy START_RAMP
        osi pochyłu kamery.
        """
        return cls.cameraTiltPulsesPerPhase(
            cls.CAMERA_TILT_START_RAMP_STROKE_MM
        )

    @classmethod
    def cameraTiltStartRampAveragePulsesPerSecond(cls) -> float:
        """
        Zwraca średnią prędkość impulsów wynikającą z geometrii
        i czasu fazy START_RAMP osi pochyłu kamery.
        """
        return cls.phaseAveragePulsesPerSecond(
            cls.cameraTiltStartRampPulses(),
            cls.CAMERA_TILT_START_RAMP_TIME_SEC
        )

    @classmethod
    def cameraTiltStartTotalTimeSec(cls) -> float:
        """
        Zwraca łączny czas rozruchu osi pochyłu kamery.
        """
        return cls.totalStartTime(
            cls.CAMERA_TILT_START_SETTLE_TIME_SEC,
            cls.CAMERA_TILT_START_RAMP_TIME_SEC
        )

    # =========================================================
    # OŚ OSTROŚCI KAMERY
    # =========================================================

    @classmethod
    def cameraFocusRatio(cls) -> float:
        """
        Zwraca całkowite przełożenie osi ostrości kamery.
        """
        return cls.simpleGearRatio(
            cls.CAMERA_FOCUS_MOTOR_TEETH,
            cls.CAMERA_FOCUS_AXIS_TEETH
        )

    @classmethod
    def cameraFocusPulsesPerCycle(cls) -> float:
        """
        Zwraca liczbę impulsów STEP na pełny cykl osi ostrości kamery.
        """
        return cls.pulsesPerCycleFromRatio(
            cls.cameraFocusRatio(),
            cls.CAMERA_FOCUS_MAX_CYCLE_ANGLE_DEG
        )

    @classmethod
    def cameraFocusCruiseMaxPulsesPerSecond(cls) -> float:
        """
        Zwraca ogólny limit prędkości impulsów STEP
        dla fazy CRUISE osi ostrości kamery.
        """
        return cls.maxPulsesPerSecondFromRatio(
            cls.cameraFocusRatio(),
            cls.CAMERA_FOCUS_MAX_CYCLE_ANGLE_DEG,
            cls.CAMERA_FOCUS_MIN_CYCLE_TIME_SEC
        )

    @classmethod
    def cameraFocusStartSettlePulses(cls) -> float:
        """
        Zwraca liczbę impulsów przypisaną do fazy START_SETTLE
        osi ostrości kamery.
        """
        return cls.pulsesPerPhaseFromRatio(
            cls.cameraFocusRatio(),
            cls.CAMERA_FOCUS_START_SETTLE_ANGLE_DEG
        )

    @classmethod
    def cameraFocusStartSettleAveragePulsesPerSecond(cls) -> float:
        """
        Zwraca średnią prędkość impulsów wynikającą z geometrii
        i czasu fazy START_SETTLE osi ostrości kamery.
        """
        return cls.phaseAveragePulsesPerSecond(
            cls.cameraFocusStartSettlePulses(),
            cls.CAMERA_FOCUS_START_SETTLE_TIME_SEC
        )

    @classmethod
    def cameraFocusStartRampPulses(cls) -> float:
        """
        Zwraca liczbę impulsów przypisaną do fazy START_RAMP
        osi ostrości kamery.
        """
        return cls.pulsesPerPhaseFromRatio(
            cls.cameraFocusRatio(),
            cls.CAMERA_FOCUS_START_RAMP_ANGLE_DEG
        )

    @classmethod
    def cameraFocusStartRampAveragePulsesPerSecond(cls) -> float:
        """
        Zwraca średnią prędkość impulsów wynikającą z geometrii
        i czasu fazy START_RAMP osi ostrości kamery.
        """
        return cls.phaseAveragePulsesPerSecond(
            cls.cameraFocusStartRampPulses(),
            cls.CAMERA_FOCUS_START_RAMP_TIME_SEC
        )

    @classmethod
    def cameraFocusStartTotalTimeSec(cls) -> float:
        """
        Zwraca łączny czas rozruchu osi ostrości kamery.
        """
        return cls.totalStartTime(
            cls.CAMERA_FOCUS_START_SETTLE_TIME_SEC,
            cls.CAMERA_FOCUS_START_RAMP_TIME_SEC
        )

    # =========================================================
    # OŚ PIONOWA RAMIENIA
    # =========================================================

    @classmethod
    def armVerticalRatio(cls) -> float:
        """
        Zwraca całkowite przełożenie osi pionowej ramienia.
        """
        return cls.compoundGearRatio(
            cls.ARM_VERTICAL_GEAR_1_MOTOR_TEETH,
            cls.ARM_VERTICAL_GEAR_2_INTERMEDIATE_TEETH,
            cls.ARM_VERTICAL_GEAR_3_INTERMEDIATE_TEETH,
            cls.ARM_VERTICAL_GEAR_4_AXIS_TEETH
        )

    @classmethod
    def armVerticalPulsesPerCycle(cls) -> float:
        """
        Zwraca liczbę impulsów STEP na pełny cykl osi pionowej ramienia.
        """
        return cls.pulsesPerCycleFromRatio(
            cls.armVerticalRatio(),
            cls.ARM_VERTICAL_MAX_CYCLE_ANGLE_DEG
        )

    @classmethod
    def armVerticalCruiseMaxPulsesPerSecond(cls) -> float:
        """
        Zwraca ogólny limit prędkości impulsów STEP
        dla fazy CRUISE osi pionowej ramienia.
        """
        return cls.maxPulsesPerSecondFromRatio(
            cls.armVerticalRatio(),
            cls.ARM_VERTICAL_MAX_CYCLE_ANGLE_DEG,
            cls.ARM_VERTICAL_MIN_CYCLE_TIME_SEC
        )

    @classmethod
    def armVerticalStartSettlePulses(cls) -> float:
        """
        Zwraca liczbę impulsów przypisaną do fazy START_SETTLE
        osi pionowej ramienia.
        """
        return cls.pulsesPerPhaseFromRatio(
            cls.armVerticalRatio(),
            cls.ARM_VERTICAL_START_SETTLE_ANGLE_DEG
        )

    @classmethod
    def armVerticalStartSettleAveragePulsesPerSecond(cls) -> float:
        """
        Zwraca średnią prędkość impulsów wynikającą z geometrii
        i czasu fazy START_SETTLE osi pionowej ramienia.
        """
        return cls.phaseAveragePulsesPerSecond(
            cls.armVerticalStartSettlePulses(),
            cls.ARM_VERTICAL_START_SETTLE_TIME_SEC
        )

    @classmethod
    def armVerticalStartRampPulses(cls) -> float:
        """
        Zwraca liczbę impulsów przypisaną do fazy START_RAMP
        osi pionowej ramienia.
        """
        return cls.pulsesPerPhaseFromRatio(
            cls.armVerticalRatio(),
            cls.ARM_VERTICAL_START_RAMP_ANGLE_DEG
        )

    @classmethod
    def armVerticalStartRampAveragePulsesPerSecond(cls) -> float:
        """
        Zwraca średnią prędkość impulsów wynikającą z geometrii
        i czasu fazy START_RAMP osi pionowej ramienia.
        """
        return cls.phaseAveragePulsesPerSecond(
            cls.armVerticalStartRampPulses(),
            cls.ARM_VERTICAL_START_RAMP_TIME_SEC
        )

    @classmethod
    def armVerticalStartTotalTimeSec(cls) -> float:
        """
        Zwraca łączny czas rozruchu osi pionowej ramienia.
        """
        return cls.totalStartTime(
            cls.ARM_VERTICAL_START_SETTLE_TIME_SEC,
            cls.ARM_VERTICAL_START_RAMP_TIME_SEC
        )

    # =========================================================
    # OŚ POZIOMA RAMIENIA
    # =========================================================

    @classmethod
    def armHorizontalRatio(cls) -> float:
        """
        Zwraca całkowite przełożenie osi poziomej ramienia.
        """
        return cls.compoundGearRatio(
            cls.ARM_HORIZONTAL_GEAR_1_MOTOR_TEETH,
            cls.ARM_HORIZONTAL_GEAR_2_INTERMEDIATE_TEETH,
            cls.ARM_HORIZONTAL_GEAR_3_INTERMEDIATE_TEETH,
            cls.ARM_HORIZONTAL_GEAR_4_AXIS_TEETH
        )

    @classmethod
    def armHorizontalPulsesPerCycle(cls) -> float:
        """
        Zwraca liczbę impulsów STEP na pełny cykl osi poziomej ramienia.
        """
        return cls.pulsesPerCycleFromRatio(
            cls.armHorizontalRatio(),
            cls.ARM_HORIZONTAL_MAX_CYCLE_ANGLE_DEG
        )

    @classmethod
    def armHorizontalCruiseMaxPulsesPerSecond(cls) -> float:
        """
        Zwraca ogólny limit prędkości impulsów STEP
        dla fazy CRUISE osi poziomej ramienia.
        """
        return cls.maxPulsesPerSecondFromRatio(
            cls.armHorizontalRatio(),
            cls.ARM_HORIZONTAL_MAX_CYCLE_ANGLE_DEG,
            cls.ARM_HORIZONTAL_MIN_CYCLE_TIME_SEC
        )

    @classmethod
    def armHorizontalStartSettlePulses(cls) -> float:
        """
        Zwraca liczbę impulsów przypisaną do fazy START_SETTLE
        osi poziomej ramienia.
        """
        return cls.pulsesPerPhaseFromRatio(
            cls.armHorizontalRatio(),
            cls.ARM_HORIZONTAL_START_SETTLE_ANGLE_DEG
        )

    @classmethod
    def armHorizontalStartSettleAveragePulsesPerSecond(cls) -> float:
        """
        Zwraca średnią prędkość impulsów wynikającą z geometrii
        i czasu fazy START_SETTLE osi poziomej ramienia.
        """
        return cls.phaseAveragePulsesPerSecond(
            cls.armHorizontalStartSettlePulses(),
            cls.ARM_HORIZONTAL_START_SETTLE_TIME_SEC
        )

    @classmethod
    def armHorizontalStartRampPulses(cls) -> float:
        """
        Zwraca liczbę impulsów przypisaną do fazy START_RAMP
        osi poziomej ramienia.
        """
        return cls.pulsesPerPhaseFromRatio(
            cls.armHorizontalRatio(),
            cls.ARM_HORIZONTAL_START_RAMP_ANGLE_DEG
        )

    @classmethod
    def armHorizontalStartRampAveragePulsesPerSecond(cls) -> float:
        """
        Zwraca średnią prędkość impulsów wynikającą z geometrii
        i czasu fazy START_RAMP osi poziomej ramienia.
        """
        return cls.phaseAveragePulsesPerSecond(
            cls.armHorizontalStartRampPulses(),
            cls.ARM_HORIZONTAL_START_RAMP_TIME_SEC
        )

    @classmethod
    def armHorizontalStartTotalTimeSec(cls) -> float:
        """
        Zwraca łączny czas rozruchu osi poziomej ramienia.
        """
        return cls.totalStartTime(
            cls.ARM_HORIZONTAL_START_SETTLE_TIME_SEC,
            cls.ARM_HORIZONTAL_START_RAMP_TIME_SEC
        )