"""
Podstawowe ustawienia systemowe projektu TARZAN.
"""

# ======================================================================
# CZAS SYSTEMOWY
# ======================================================================

# Główny czas próbkowania timeline systemu TARZAN.
# Wszystkie moduły choreografii ruchu powinny korzystać z tej wartości.
CZAS_PROBKOWANIA_MS = 10

# ======================================================================
# PARAMETRY SILNIKA KRZYWYCH
# ======================================================================

# Gęstość próbkowania interpolowanej krzywej ruchu.
# To nie jest czas protokołu, tylko gęstość obliczeń matematycznych.
GESTOSC_INTERPOLACJI = 400