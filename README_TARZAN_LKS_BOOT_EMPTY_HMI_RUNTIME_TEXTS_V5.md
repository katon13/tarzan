# TARZAN LKS-N5 BOOT EMPTY HMI RUNTIME TEXTS V5

Zakres V5:

- HMI boot_* może mieć puste pola tekstowe.
- Runtime Python uzupełnia dynamicznie:
  - `t_title`
  - `t_subtitle`
  - `t_line1`
  - `t_line2`
  - `t_line3`
  - `t_status`
  - `t_code`
  - `n_progress.txt`
  - `j_progress.val`
- `n_progress` ma zostać nazwą komponentu, ale typem Text, nie Number.
- `boot_loading` po starcie Pythona dostaje własny runtime update, zanim system przejdzie do `boot_linux`.
- Matrix LED: test operatorski to serce READY, bez widocznej ramki testowej/kreski.

Nie ruszano:

- `core/tarzanPoKeys.py`
- `core/tarzanPokABC.py`
- `core/tarzanZmienneSygnalowe.py`
- ABC / POKSYG
- keypad
- LCD low-level
- F-LED low-level
- Matrix LED low-level
- osie / pulse engine

W Nextion Editor na stronach:

- `boot_loading`
- `boot_linux`
- `boot_services`
- `boot_hardware`
- `boot_test`

zostaw puste pola:

- `t_title.txt = ""`
- `t_subtitle.txt = ""`
- `t_line1.txt = ""`
- `t_line2.txt = ""`
- `t_line3.txt = ""`
- `t_status.txt = ""`
- `t_code.txt = ""`
- `n_progress.txt = ""`

`n_progress` musi być komponentem Text, nie Number.

Na `boot_loading` usuń wszystkie linie `n_progress.val=...`. Timer może aktualizować tylko `j_progress.val`.
