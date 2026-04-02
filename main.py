from pathlib import Path

from core.tarzanUstawienia import CZAS_PROBKOWANIA_MS
from motion.tarzanMechanicalValidator import TarzanMechanicalValidator
from motion.tarzanSegmentAnalyzer import TarzanSegmentAnalyzer
from motion.tarzanStepGenerator import TarzanStepGenerator
from motion.tarzanSymulacjaRuchu import TarzanSymulacjaRuchu
from motion.tarzanTakeModel import TarzanTake
from motion.tarzanTimeline import TarzanAxisTimeline, TarzanTimeline


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
    timeline_builder = TarzanTimeline()

    print("\nAnaliza segmentów:")

    axis_timelines: list[TarzanAxisTimeline] = []
    first_profile = None

    for axis_key, axis in take.axes.items():
        profiles = analyzer.build_axis_segment_profiles(axis)

        print(f"\nOś: {axis.axis_name} ({axis_key})")

        axis_frames = []

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

            step_generator = TarzanStepGenerator(
                time_ms=profile.times_ms,
                pulse_density=profile.pulse_density,
            )
            step_times = step_generator.generate_step_times()

            segment_frames = timeline_builder.build_axis_frames(
                step_times=step_times,
                segment_start_ms=profile.start_time,
                segment_end_ms=profile.end_time,
                direction=profile.direction,
                enabled=not profile.is_pause,
            )

            axis_frames.extend(segment_frames)

        if not axis_frames:
            axis_frames = timeline_builder.build_empty_axis_frames(
                take_start_ms=take.timeline.take_start,
                take_end_ms=take.timeline.take_end,
                enabled=axis.axis_enabled,
            )

        axis_timeline = TarzanAxisTimeline(
            axis_key=axis_key,
            axis_name=axis.axis_name,
            frames=axis_frames,
        )
        axis_timelines.append(axis_timeline)

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

    print("\nBudowa globalnego timeline systemu...")
    global_timeline = timeline_builder.build_global_timeline(axis_timelines)

    print("Pierwsze ramki globalnego timeline:")
    shown_frames = 0
    for time_ms, axes_state in global_timeline.items():
        print(f"\nt={time_ms:4d} ms")
        for axis_key, signals in axes_state.items():
            print(
                f"  {axis_key}: "
                f"STEP_COUNT={signals['STEP_COUNT']:3d} | "
                f"STEP={signals['STEP']} | "
                f"DIR={signals['DIR']} | "
                f"ENABLE={signals['ENABLE']}"
            )

        shown_frames += 1
        if shown_frames >= 10:
            break

    simulator = TarzanSymulacjaRuchu()
    simulator.plot_take_axes(take)

    print("\nSymulacja zakończona.")


if __name__ == "__main__":
    main()