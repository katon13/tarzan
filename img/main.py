from pathlib import Path
import json

from core.tarzanProtokolRuchu import TarzanProtokolRuchu
from core.tarzanTakeVersioning import TarzanTakeVersioning
from core.tarzanUstawienia import CZAS_PROBKOWANIA_MS

from motion.tarzanGhostMotion import TarzanGhostMotion
from motion.tarzanKrzyweRuchu import TarzanKrzyweRuchu
from motion.tarzanMechanicalValidator import TarzanMechanicalValidator
from motion.tarzanSegmentAnalyzer import TarzanSegmentAnalyzer
from motion.tarzanStepGenerator import TarzanStepGenerator
from motion.tarzanSymulacjaRuchu import TarzanSymulacjaRuchu
from motion.tarzanTakeModel import TarzanTake
from motion.tarzanTimeline import TarzanAxisTimeline, TarzanTimeline


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    take_path = base_dir / "data" / "take" / "TAKE_001_v01.json"

    print("=== TARZAN START ===")
    print(f"Ładowanie TAKE: {take_path}")
    print(f"Czas próbkowania systemu: {CZAS_PROBKOWANIA_MS} ms")

    take = TarzanTake.load_json(take_path)

    print(f"TAKE ID: {take.metadata.take_id}")
    print(f"Wersja: {take.metadata.version}")
    print(f"Tytuł: {take.metadata.title}")
    print(f"Czas TAKE: {take.timeline.take_duration} {take.timeline.time_unit}")

    basic_errors = take.validate_basic()
    if basic_errors:
        print("\nBłędy walidacji TAKE")
        for error in basic_errors:
            print(error)
        return

    validator = TarzanMechanicalValidator()
    mechanical_errors = validator.validate_take(take)

    if mechanical_errors:
        print("\nBłędy walidacji mechanicznej")
        for error in mechanical_errors:
            print(error)
        return

    print("\nWalidacja TAKE: OK")

    krzywe = TarzanKrzyweRuchu()
    ghost = TarzanGhostMotion()

    print("\n=== EDYCJA KRZYWEJ (TEST) ===")

    axis_original = krzywe.clone_axis(take.axes["camera_horizontal"])

    axis_edited = krzywe.apply_amplitude_scale_on_interval(
        axis_original,
        start_time_ms=300,
        end_time_ms=1450,
        scale=1.25,
        normalize_distance=True,
    )

    axis_edited = krzywe.smooth_interval(
        axis_edited,
        start_time_ms=300,
        end_time_ms=1450,
        strength=0.4,
        normalize_distance=True,
    )

    take.axes["camera_horizontal"] = axis_edited

    print("Krzywa została zmodyfikowana.")

    print("\n=== GHOST COMPARE ===")
    comparison = ghost.compare_axes(axis_original, axis_edited)

    print(f"Oś: {comparison.axis_name}")
    print(f"Pole oryginalne: {comparison.original_area:.4f}")
    print(f"Pole edytowane:  {comparison.edited_area:.4f}")
    print(f"Delta pola:      {comparison.area_delta:.4f}")
    print(f"Delta pola %:    {comparison.area_delta_percent:.4f}%")
    print(f"Peak oryginalny: {comparison.original_peak:.4f}")
    print(f"Peak edytowany:  {comparison.edited_peak:.4f}")
    print(f"Delta peak:      {comparison.peak_delta:.4f}")
    print(f"Zero crossings oryginalne: {comparison.original_zero_crossings}")
    print(f"Zero crossings edytowane:  {comparison.edited_zero_crossings}")

    print("\nZapisywanie nowej wersji TAKE...")

    with open(take_path, "r", encoding="utf-8") as file:
        take_dict = json.load(file)

    control_points = []
    for point in axis_edited.curve.control_points:
        control_points.append(
            {
                "time": int(point.time),
                "amplitude": float(point.amplitude),
            }
        )

    take_dict["axes"]["camera_horizontal"]["curve"]["control_points"] = control_points

    versioning = TarzanTakeVersioning()
    new_take_path = versioning.save_new_take(
        original_take_path=take_path,
        take_dict=take_dict,
    )

    print("Nowa wersja TAKE zapisana:")
    print(new_take_path)

    take_v2 = TarzanTake.load_json(new_take_path)

    analyzer = TarzanSegmentAnalyzer()
    timeline_builder = TarzanTimeline()

    axis_timelines = []

    for axis_key, axis in take_v2.axes.items():
        profiles = analyzer.build_axis_segment_profiles(axis)
        axis_frames = []

        for profile in profiles:
            step_generator = TarzanStepGenerator(
                time_ms=profile.times_ms,
                pulse_density=profile.pulse_density,
            )

            step_times = step_generator.generate_step_times()

            frames = timeline_builder.build_axis_frames(
                step_times=step_times,
                segment_start_ms=profile.start_time,
                segment_end_ms=profile.end_time,
                direction=profile.direction,
                enabled=not profile.is_pause,
            )

            axis_frames.extend(frames)

        axis_timeline = TarzanAxisTimeline(
            axis_key=axis_key,
            axis_name=axis.axis_name,
            frames=axis_frames,
        )
        axis_timelines.append(axis_timeline)

    global_timeline = timeline_builder.build_global_timeline(axis_timelines)

    print("\nEksport protokołu ruchu...")
    protokol = TarzanProtokolRuchu()

    protocol_path = (
        base_dir
        / "data"
        / "protokoly"
        / f"{take_v2.metadata.take_id}_{take_v2.metadata.version}_protocol.txt"
    )

    protokol.export_txt(
        take=take_v2,
        global_timeline=global_timeline,
        file_path=protocol_path,
    )

    print("Protokół zapisany:")
    print(protocol_path)

    simulator = TarzanSymulacjaRuchu()
    simulator.plot_take_axes(take_v2)

    print("\n=== KONIEC SYMULACJI ===")


if __name__ == "__main__":
    main()