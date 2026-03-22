from pathlib import Path

from core.tarzanUstawienia import CZAS_PROBKOWANIA_MS
from motion.tarzanMechanicalValidator import TarzanMechanicalValidator
from motion.tarzanSegmentAnalyzer import TarzanSegmentAnalyzer
from motion.tarzanStepGenerator import TarzanStepGenerator
from motion.tarzanSymulacjaRuchu import TarzanSymulacjaRuchu
from motion.tarzanTakeModel import TarzanTake
from motion.tarzanTimeline import TarzanTimeline


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    take_file = base_dir / "data" / "take" / "TAKE_001_v01.json"

    print("=== TARZAN START ===")
    print(f"Ładowanie TAKE: {take_file}")
    print(f"Czas próbkowania systemu: {CZAS_PROBKOWANIA_MS} ms")

    take = TarzanTake.load_json(take_file)

    print(f"TAKE ID: {take.metadata.take_id}")
    print(f"Wersja: {take.metadata.version}")
    print(f"Tytuł: {take.metadata.title}")
    print(f"Czas TAKE: {take.timeline.take_duration} {take.timeline.time_unit}")

    basic_errors = take.validate_basic()
    if basic_errors:
        print("\nBłędy podstawowej walidacji TAKE:")
        for err in basic_errors:
            print(f"- {err}")
        return

    print("\nWalidacja podstawowa TAKE: OK")

    validator = TarzanMechanicalValidator()
    mechanical_errors = validator.validate_take(take)

    if mechanical_errors:
        print("\nBłędy walidacji mechanicznej:")
        for err in mechanical_errors:
            print(f"- {err}")
        return

    print("Walidacja mechaniczna: OK")

    analyzer = TarzanSegmentAnalyzer()

    print("\nAnaliza segmentów:")
    first_profile = None

    for axis_key, axis in take.axes.items():
        profiles = analyzer.build_axis_segment_profiles(axis)

        print(f"\nOś: {axis.axis_name} ({axis_key})")
        for profile in profiles:
            print(
                f"  {profile.segment_id}: "
                f"time={profile.start_time}-{profile.end_time} ms | "
                f"dir={profile.direction} | "
                f"pulses={profile.pulse_count} | "
                f"reconstructed={profile.reconstructed_pulses:.2f}"
            )

            if first_profile is None and not profile.is_pause:
                first_profile = profile

    if first_profile is not None:
        print("\nGenerowanie timeline STEP...")

        step_generator = TarzanStepGenerator(
            time_ms=first_profile.times_ms,
            pulse_density=first_profile.pulse_density,
        )

        step_times = step_generator.generate_step_times()

        print("Pierwsze impulsy STEP:")
        for s in step_times[:20]:
            print(f"  {s:.3f} ms")

        print(f"\nŁączna liczba impulsów STEP: {len(step_times)}")

        print("\nBudowa roboczego timeline protokołu...")
        timeline = TarzanTimeline()

        frames = timeline.build_frames(
            step_times=step_times,
            segment_start_ms=first_profile.start_time,
            segment_end_ms=first_profile.end_time,
            direction=first_profile.direction,
            enabled=not first_profile.is_pause,
        )

        print("Pierwsze ramki timeline:")
        for frame in frames[:20]:
            print(
                f"  t={frame.time_ms:4d} ms | "
                f"STEP_COUNT={frame.step_count:3d} | "
                f"STEP={frame.step_state} | "
                f"DIR={frame.dir_state} | "
                f"ENABLE={frame.enable_state}"
            )

    simulator = TarzanSymulacjaRuchu()
    simulator.plot_take_axes(take)

    print("\nSymulacja zakończona.")


if __name__ == "__main__":
    main()