
class TarzanStepGenerator:
    """
    Generates STEP signal density based on curve amplitudes.
    STEP toggles only when accumulator crosses 1.
    Sampling time is fixed (default 10 ms).
    """

    def __init__(self, sample_ms=10):
        self.sample_ms = sample_ms

    def generate(self, amplitudes, max_steps):
        step_state = 0
        accumulator = 0.0
        steps_done = 0

        protocol = []

        for i, amp in enumerate(amplitudes):

            # density proportional to amplitude
            density = abs(amp) * max_steps / len(amplitudes)
            accumulator += density

            step_out = 0

            if accumulator >= 1 and steps_done < max_steps:
                step_state = 1 - step_state
                step_out = step_state
                accumulator -= 1
                steps_done += 1

            dir_val = 1 if amp >= 0 else 0

            protocol.append({
                "COUNT": i,
                "TIME_MS": i * self.sample_ms,
                "DIR": dir_val,
                "STEP": step_out
            })

        return protocol
