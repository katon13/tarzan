from __future__ import annotations

import matplotlib.pyplot as plt

from motion.tarzanKrzyweRuchu import TarzanKrzyweRuchu
from motion.tarzanSegmentAnalyzer import TarzanSegmentAnalyzer
from motion.tarzanTakeModel import TarzanTake


class TarzanSymulacjaRuchu:
    """
    Podstawowa symulacja ruchu TARZANA w dark mode.
    """

    def __init__(self) -> None:
        self.krzywe = TarzanKrzyweRuchu()
        self.segment_analyzer = TarzanSegmentAnalyzer()
        self._setup_dark_style()

    def plot_take_axes(self, take: TarzanTake) -> None:
        if not take.axes:
            print("Brak osi do symulacji.")
            return

        for axis_key, axis in take.axes.items():
            self._plot_single_axis(axis_key, axis)

        plt.show()

    def _plot_single_axis(self, axis_key: str, axis) -> None:
        try:
            dense_times, dense_amplitudes = self.krzywe.build_curve_samples(axis)
            gradient_times, gradients = self.krzywe.build_gradient_samples(axis)
            accel_times, accelerations = self.krzywe.build_acceleration_samples(axis)
            control_times, control_amplitudes = self.krzywe.get_control_points(axis)
            profiles = self.segment_analyzer.build_axis_segment_profiles(axis)
        except ValueError as exc:
            print(f"{axis_key}: {exc}")
            return

        fig, axes = plt.subplots(4, 1, figsize=(14, 11), sharex=True)
        fig.patch.set_facecolor("#1e1e1e")

        axes[0].plot(dense_times, dense_amplitudes, linewidth=2.2, color="#4FC3F7")
        axes[0].plot(
            control_times,
            control_amplitudes,
            "o",
            markersize=8,
            color="#FFB74D",
        )
        axes[0].axhline(0.0, linewidth=1.2, color="#607D8B")
        axes[0].set_title(
            f"{axis.axis_name} ({axis_key})",
            fontsize=16,
            color="#ECEFF1",
            pad=10,
        )
        axes[0].set_ylabel("Natężenie ruchu", color="#ECEFF1")
        axes[0].grid(True, alpha=0.35, color="#78909C")

        axes[1].plot(gradient_times, gradients, linewidth=2.0, color="#81C784")
        axes[1].axhline(0.0, linewidth=1.2, color="#607D8B")
        axes[1].set_ylabel("Gradient krzywej", color="#ECEFF1")
        axes[1].grid(True, alpha=0.35, color="#78909C")

        axes[2].plot(accel_times, accelerations, linewidth=2.0, color="#E57373")
        axes[2].axhline(0.0, linewidth=1.2, color="#607D8B")
        axes[2].set_ylabel("Przyspieszenie", color="#ECEFF1")
        axes[2].grid(True, alpha=0.35, color="#78909C")

        has_profile = False
        for profile in profiles:
            if len(profile.times_ms) < 2:
                continue

            color = "#BA68C8" if profile.direction >= 0 else "#F06292"
            axes[3].plot(
                profile.times_ms,
                profile.pulse_density,
                linewidth=2.2,
                color=color,
            )
            has_profile = True

        axes[3].axhline(0.0, linewidth=1.2, color="#607D8B")
        axes[3].set_xlabel("Czas [ms]", color="#ECEFF1")
        axes[3].set_ylabel("Gęstość impulsów", color="#ECEFF1")
        axes[3].grid(True, alpha=0.35, color="#78909C")

        if not has_profile:
            axes[3].text(
                0.5,
                0.5,
                "Brak aktywnych segmentów",
                transform=axes[3].transAxes,
                ha="center",
                va="center",
                color="#CFD8DC",
                fontsize=12,
            )

        for ax in axes:
            ax.set_facecolor("#263238")
            ax.tick_params(colors="#CFD8DC", labelsize=11)
            for spine in ax.spines.values():
                spine.set_color("#90A4AE")

        plt.tight_layout()

    def _setup_dark_style(self) -> None:
        plt.rcParams["figure.facecolor"] = "#1e1e1e"
        plt.rcParams["axes.facecolor"] = "#263238"
        plt.rcParams["savefig.facecolor"] = "#1e1e1e"
        plt.rcParams["text.color"] = "#ECEFF1"
        plt.rcParams["axes.labelcolor"] = "#ECEFF1"
        plt.rcParams["xtick.color"] = "#CFD8DC"
        plt.rcParams["ytick.color"] = "#CFD8DC"
        plt.rcParams["axes.edgecolor"] = "#90A4AE"
        plt.rcParams["grid.color"] = "#78909C"
        plt.rcParams["font.size"] = 11