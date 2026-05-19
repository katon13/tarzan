# TARZAN_SNAJPER_FULL_V3 — pełny rejestr celów z repo

Ten dokument poprawia poprzednią wersję. To nie są przykłady. To jest pełny katalog wygenerowany z aktualnego `tarzan.zip` oraz z przesłanych plików HMI Nextiona.

## Liczby

```txt
Nextion HMI components: 139
Python Tkinter widgets found: 200
Python Canvas targets found: 834
Refresh/repaint/tick sites found: 552
Raw signal aliases: 1488
Logical signals with targets: 1288
Single target rows: 1521
```

## Pliki w paczce

```txt
core/tarzanSnajper.py
docs/TARZAN_SNAJPER_FULL_V3.md
docs/TARZAN_SNAJPER_REFRESH_SCAN_FULL.csv
docs/TARZAN_SNAJPER_TARGETS_FULL.csv
docs/TARZAN_SNAJPER_SIGNALS_FULL.csv
docs/TARZAN_SNAJPER_NEXTION_COMPONENTS_FULL.csv
```

---

# 1. Pełna definicja TarzanSnajperTarget

W `core/tarzanSnajper.py` uzupełniono:

```py
@dataclass(frozen=True)
class TarzanSnajperTarget:
    adapter: str
    scope: str
    target: str
    prop: str
```

## Adaptery

```txt
- physical_nextion
- canvas_preview
- par_tkinter
- ehr_canvas
- ehr_tkinter
- sandbox_canvas
- sandbox_tkinter
- timeline_canvas
- layout_canvas
- khr_canvas
- khr_tkinter
- tfd_adapter
- take_adapter
- log_adapter
- signal_row
```

## Props

```txt
- coords
- en
- pic
- state
- text
- tim
- txt
- val
- value
- visible
```

---

# 2. Pełna fabryka

```py
def create_default_tarzan_snajper() -> TarzanSnajper:
    snajper = TarzanSnajper()
    snajper.register_signals(DEFAULT_TARZAN_SNAJPER_SIGNAL_MAP)
    snajper.register_targets(DEFAULT_TARZAN_SNAJPER_TARGETS)
    return snajper
```

Ta fabryka ładuje pełną mapę z pliku:

```txt
DEFAULT_TARZAN_SNAJPER_SIGNAL_MAP
DEFAULT_TARZAN_SNAJPER_TARGETS
```

---

# 3. Pełna lista celów Snajpera

Pełna tabela jest też w CSV:

```txt
docs/TARZAN_SNAJPER_TARGETS_FULL.csv
```

Poniżej ta sama lista w Markdown.

| logical_signal | adapter | scope | target | prop |
| --- | --- | --- | --- | --- |
| axis_0_value | physical_nextion | take_main | t_axis0 | txt |
| axis_0_value | canvas_preview | take_main | t_axis0 | txt |
| axis_0_value | par_tkinter | axis_panel | axis_0_value_label | text |
| axis_1_value | physical_nextion | take_main | t_axis1 | txt |
| axis_1_value | canvas_preview | take_main | t_axis1 | txt |
| axis_1_value | par_tkinter | axis_panel | axis_1_value_label | text |
| axis_2_value | physical_nextion | take_main | t_axis2 | txt |
| axis_2_value | canvas_preview | take_main | t_axis2 | txt |
| axis_2_value | par_tkinter | axis_panel | axis_2_value_label | text |
| axis_3_value | physical_nextion | take_main | t_axis3 | txt |
| axis_3_value | canvas_preview | take_main | t_axis3 | txt |
| axis_3_value | par_tkinter | axis_panel | axis_3_value_label | text |
| axis_4_value | physical_nextion | take_main | t_axis4 | txt |
| axis_4_value | canvas_preview | take_main | t_axis4 | txt |
| axis_4_value | par_tkinter | axis_panel | axis_4_value_label | text |
| axis_5_value | physical_nextion | take_main | t_axis5 | txt |
| axis_5_value | canvas_preview | take_main | t_axis5 | txt |
| axis_5_value | par_tkinter | axis_panel | axis_5_value_label | text |
| canvas_editor_editor_ehr_tarzanaxissandbox_c_line_line_826_coords | ehr_canvas | editor_editor_ehr_tarzanaxissandbox | c_line_line_826 | coords |
| canvas_editor_editor_ehr_tarzanaxissandbox_c_line_line_833_coords | ehr_canvas | editor_editor_ehr_tarzanaxissandbox | c_line_line_833 | coords |
| canvas_editor_editor_ehr_tarzanaxissandbox_c_line_line_840_coords | ehr_canvas | editor_editor_ehr_tarzanaxissandbox | c_line_line_840 | coords |
| canvas_editor_editor_ehr_tarzanaxissandbox_c_line_line_852_coords | ehr_canvas | editor_editor_ehr_tarzanaxissandbox | c_line_line_852 | coords |
| canvas_editor_editor_ehr_tarzanaxissandbox_c_line_line_853_coords | ehr_canvas | editor_editor_ehr_tarzanaxissandbox | c_line_line_853 | coords |
| canvas_editor_editor_ehr_tarzanaxissandbox_c_line_line_867_coords | ehr_canvas | editor_editor_ehr_tarzanaxissandbox | c_line_line_867 | coords |
| canvas_editor_editor_ehr_tarzanaxissandbox_c_line_line_879_coords | ehr_canvas | editor_editor_ehr_tarzanaxissandbox | c_line_line_879 | coords |
| canvas_editor_editor_ehr_tarzanaxissandbox_c_line_line_881_coords | ehr_canvas | editor_editor_ehr_tarzanaxissandbox | c_line_line_881 | coords |
| canvas_editor_editor_ehr_tarzanaxissandbox_c_oval_line_849_coords | ehr_canvas | editor_editor_ehr_tarzanaxissandbox | c_oval_line_849 | coords |
| canvas_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_812_coords | ehr_canvas | editor_editor_ehr_tarzanaxissandbox | c_rectangle_line_812 | coords |
| canvas_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_819_coords | ehr_canvas | editor_editor_ehr_tarzanaxissandbox | c_rectangle_line_819 | coords |
| canvas_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_820_coords | ehr_canvas | editor_editor_ehr_tarzanaxissandbox | c_rectangle_line_820 | coords |
| canvas_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_821_coords | ehr_canvas | editor_editor_ehr_tarzanaxissandbox | c_rectangle_line_821 | coords |
| canvas_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_861_coords | ehr_canvas | editor_editor_ehr_tarzanaxissandbox | c_rectangle_line_861 | coords |
| canvas_editor_editor_ehr_tarzanaxissandbox_c_text_line_827_text | ehr_canvas | editor_editor_ehr_tarzanaxissandbox | c_text_line_827 | text |
| canvas_editor_editor_ehr_tarzanaxissandbox_c_text_line_834_text | ehr_canvas | editor_editor_ehr_tarzanaxissandbox | c_text_line_834 | text |
| canvas_editor_editor_ehr_tarzanaxissandbox_c_text_line_854_text | ehr_canvas | editor_editor_ehr_tarzanaxissandbox | c_text_line_854 | text |
| canvas_editor_editor_ehr_tarzanaxissandbox_c_text_line_855_text | ehr_canvas | editor_editor_ehr_tarzanaxissandbox | c_text_line_855 | text |
| canvas_editor_editor_ehr_tarzanaxissandbox_c_text_line_882_text | ehr_canvas | editor_editor_ehr_tarzanaxissandbox | c_text_line_882 | text |
| canvas_editor_editor_ehr_tarzanaxissandbox_c_text_line_883_text | ehr_canvas | editor_editor_ehr_tarzanaxissandbox | c_text_line_883 | text |
| canvas_editor_editor_ehr_tarzanehrui_c_image_line_2734_coords | ehr_canvas | editor_editor_ehr_tarzanehrui | c_image_line_2734 | coords |
| canvas_editor_editor_ehr_tarzanehrui_c_line_line_1910_coords | ehr_canvas | editor_editor_ehr_tarzanehrui | c_line_line_1910 | coords |
| canvas_editor_editor_ehr_tarzanehrui_c_line_line_1919_coords | ehr_canvas | editor_editor_ehr_tarzanehrui | c_line_line_1919 | coords |
| canvas_editor_editor_ehr_tarzanehrui_c_line_line_1930_coords | ehr_canvas | editor_editor_ehr_tarzanehrui | c_line_line_1930 | coords |
| canvas_editor_editor_ehr_tarzanehrui_c_line_line_1937_coords | ehr_canvas | editor_editor_ehr_tarzanehrui | c_line_line_1937 | coords |
| canvas_editor_editor_ehr_tarzanehrui_c_line_line_1951_coords | ehr_canvas | editor_editor_ehr_tarzanehrui | c_line_line_1951 | coords |
| canvas_editor_editor_ehr_tarzanehrui_c_line_line_1952_coords | ehr_canvas | editor_editor_ehr_tarzanehrui | c_line_line_1952 | coords |
| canvas_editor_editor_ehr_tarzanehrui_c_line_line_1966_coords | ehr_canvas | editor_editor_ehr_tarzanehrui | c_line_line_1966 | coords |
| canvas_editor_editor_ehr_tarzanehrui_c_line_line_1978_coords | ehr_canvas | editor_editor_ehr_tarzanehrui | c_line_line_1978 | coords |
| canvas_editor_editor_ehr_tarzanehrui_c_line_line_1980_coords | ehr_canvas | editor_editor_ehr_tarzanehrui | c_line_line_1980 | coords |
| canvas_editor_editor_ehr_tarzanehrui_c_line_line_2697_coords | ehr_canvas | editor_editor_ehr_tarzanehrui | c_line_line_2697 | coords |
| canvas_editor_editor_ehr_tarzanehrui_c_line_line_2707_coords | ehr_canvas | editor_editor_ehr_tarzanehrui | c_line_line_2707 | coords |
| canvas_editor_editor_ehr_tarzanehrui_c_line_line_2710_coords | ehr_canvas | editor_editor_ehr_tarzanehrui | c_line_line_2710 | coords |
| canvas_editor_editor_ehr_tarzanehrui_c_line_line_2749_coords | ehr_canvas | editor_editor_ehr_tarzanehrui | c_line_line_2749 | coords |
| canvas_editor_editor_ehr_tarzanehrui_c_line_line_2757_coords | ehr_canvas | editor_editor_ehr_tarzanehrui | c_line_line_2757 | coords |
| canvas_editor_editor_ehr_tarzanehrui_c_line_line_2765_coords | ehr_canvas | editor_editor_ehr_tarzanehrui | c_line_line_2765 | coords |
| canvas_editor_editor_ehr_tarzanehrui_c_line_line_2778_coords | ehr_canvas | editor_editor_ehr_tarzanehrui | c_line_line_2778 | coords |
| canvas_editor_editor_ehr_tarzanehrui_c_line_line_2801_coords | ehr_canvas | editor_editor_ehr_tarzanehrui | c_line_line_2801 | coords |
| canvas_editor_editor_ehr_tarzanehrui_c_oval_line_1947_coords | ehr_canvas | editor_editor_ehr_tarzanehrui | c_oval_line_1947 | coords |
| canvas_editor_editor_ehr_tarzanehrui_c_oval_line_2792_coords | ehr_canvas | editor_editor_ehr_tarzanehrui | c_oval_line_2792 | coords |
| canvas_editor_editor_ehr_tarzanehrui_c_oval_line_2794_coords | ehr_canvas | editor_editor_ehr_tarzanehrui | c_oval_line_2794 | coords |
| canvas_editor_editor_ehr_tarzanehrui_c_polygon_line_2808_coords | ehr_canvas | editor_editor_ehr_tarzanehrui | c_polygon_line_2808 | coords |
| canvas_editor_editor_ehr_tarzanehrui_c_rectangle_line_1893_coords | ehr_canvas | editor_editor_ehr_tarzanehrui | c_rectangle_line_1893 | coords |
| canvas_editor_editor_ehr_tarzanehrui_c_rectangle_line_1901_coords | ehr_canvas | editor_editor_ehr_tarzanehrui | c_rectangle_line_1901 | coords |
| canvas_editor_editor_ehr_tarzanehrui_c_rectangle_line_1902_coords | ehr_canvas | editor_editor_ehr_tarzanehrui | c_rectangle_line_1902 | coords |
| canvas_editor_editor_ehr_tarzanehrui_c_rectangle_line_1903_coords | ehr_canvas | editor_editor_ehr_tarzanehrui | c_rectangle_line_1903 | coords |
| canvas_editor_editor_ehr_tarzanehrui_c_rectangle_line_1960_coords | ehr_canvas | editor_editor_ehr_tarzanehrui | c_rectangle_line_1960 | coords |
| canvas_editor_editor_ehr_tarzanehrui_c_rectangle_line_2688_coords | ehr_canvas | editor_editor_ehr_tarzanehrui | c_rectangle_line_2688 | coords |
| canvas_editor_editor_ehr_tarzanehrui_c_rectangle_line_2705_coords | ehr_canvas | editor_editor_ehr_tarzanehrui | c_rectangle_line_2705 | coords |
| canvas_editor_editor_ehr_tarzanehrui_c_rectangle_line_2790_coords | ehr_canvas | editor_editor_ehr_tarzanehrui | c_rectangle_line_2790 | coords |
| canvas_editor_editor_ehr_tarzanehrui_c_rectangle_line_2800_coords | ehr_canvas | editor_editor_ehr_tarzanehrui | c_rectangle_line_2800 | coords |
| canvas_editor_editor_ehr_tarzanehrui_c_text_line_1911_text | ehr_canvas | editor_editor_ehr_tarzanehrui | c_text_line_1911 | text |
| canvas_editor_editor_ehr_tarzanehrui_c_text_line_1920_text | ehr_canvas | editor_editor_ehr_tarzanehrui | c_text_line_1920 | text |
| canvas_editor_editor_ehr_tarzanehrui_c_text_line_1953_text | ehr_canvas | editor_editor_ehr_tarzanehrui | c_text_line_1953 | text |
| canvas_editor_editor_ehr_tarzanehrui_c_text_line_1954_text | ehr_canvas | editor_editor_ehr_tarzanehrui | c_text_line_1954 | text |
| canvas_editor_editor_ehr_tarzanehrui_c_text_line_1981_text | ehr_canvas | editor_editor_ehr_tarzanehrui | c_text_line_1981 | text |
| canvas_editor_editor_ehr_tarzanehrui_c_text_line_1982_text | ehr_canvas | editor_editor_ehr_tarzanehrui | c_text_line_1982 | text |
| canvas_editor_editor_ehr_tarzanehrui_c_text_line_2720_text | ehr_canvas | editor_editor_ehr_tarzanehrui | c_text_line_2720 | text |
| canvas_editor_editor_ehr_tarzanehrui_c_text_line_2727_text | ehr_canvas | editor_editor_ehr_tarzanehrui | c_text_line_2727 | text |
| canvas_editor_editor_ehr_tarzanehrui_c_text_line_2736_text | ehr_canvas | editor_editor_ehr_tarzanehrui | c_text_line_2736 | text |
| canvas_editor_editor_ehr_tarzanehrui_c_text_line_2809_text | ehr_canvas | editor_editor_ehr_tarzanehrui | c_text_line_2809 | text |
| canvas_editor_editor_ehr_tarzanehrui_c_text_line_2816_text | ehr_canvas | editor_editor_ehr_tarzanehrui | c_text_line_2816 | text |
| canvas_editor_editor_ehr_tarzanehrui_canvas_image_line_712_coords | ehr_canvas | editor_editor_ehr_tarzanehrui | canvas_image_line_712 | coords |
| canvas_editor_editor_ehr_tarzanehrui_canvas_rectangle_line_1244_coords | ehr_canvas | editor_editor_ehr_tarzanehrui | canvas_rectangle_line_1244 | coords |
| canvas_editor_editor_ehr_tarzanehrui_canvas_window_line_1172_coords | ehr_canvas | editor_editor_ehr_tarzanehrui | canvas_window_line_1172 | coords |
| canvas_editor_editor_ehr_tarzanehrui_item_text | ehr_canvas | editor_editor_ehr_tarzanehrui | item | text |
| canvas_editor_editor_ehr_tarzanehrui_protocol_canvas_rectangle_line_962_coords | ehr_canvas | editor_editor_ehr_tarzanehrui | protocol_canvas_rectangle_line_962 | coords |
| canvas_editor_editor_ehr_tarzanehrui_protocol_canvas_rectangle_line_963_coords | ehr_canvas | editor_editor_ehr_tarzanehrui | protocol_canvas_rectangle_line_963 | coords |
| canvas_editor_editor_ehr_tarzanehrui_row_window_coords | ehr_canvas | editor_editor_ehr_tarzanehrui | row_window | coords |
| canvas_editor_editor_ehr_tarzanehrui_save_button_window_coords | ehr_canvas | editor_editor_ehr_tarzanehrui | save_button_window | coords |
| canvas_editor_editor_tarzanaxissandbox_c_line_line_826_coords | sandbox_canvas | editor_editor_tarzanaxissandbox | c_line_line_826 | coords |
| canvas_editor_editor_tarzanaxissandbox_c_line_line_833_coords | sandbox_canvas | editor_editor_tarzanaxissandbox | c_line_line_833 | coords |
| canvas_editor_editor_tarzanaxissandbox_c_line_line_852_coords | sandbox_canvas | editor_editor_tarzanaxissandbox | c_line_line_852 | coords |
| canvas_editor_editor_tarzanaxissandbox_c_line_line_859_coords | sandbox_canvas | editor_editor_tarzanaxissandbox | c_line_line_859 | coords |
| canvas_editor_editor_tarzanaxissandbox_c_line_line_871_coords | sandbox_canvas | editor_editor_tarzanaxissandbox | c_line_line_871 | coords |
| canvas_editor_editor_tarzanaxissandbox_c_line_line_872_coords | sandbox_canvas | editor_editor_tarzanaxissandbox | c_line_line_872 | coords |
| canvas_editor_editor_tarzanaxissandbox_c_line_line_886_coords | sandbox_canvas | editor_editor_tarzanaxissandbox | c_line_line_886 | coords |
| canvas_editor_editor_tarzanaxissandbox_c_line_line_898_coords | sandbox_canvas | editor_editor_tarzanaxissandbox | c_line_line_898 | coords |
| canvas_editor_editor_tarzanaxissandbox_c_line_line_900_coords | sandbox_canvas | editor_editor_tarzanaxissandbox | c_line_line_900 | coords |
| canvas_editor_editor_tarzanaxissandbox_c_oval_line_868_coords | sandbox_canvas | editor_editor_tarzanaxissandbox | c_oval_line_868 | coords |
| canvas_editor_editor_tarzanaxissandbox_c_rectangle_line_812_coords | sandbox_canvas | editor_editor_tarzanaxissandbox | c_rectangle_line_812 | coords |
| canvas_editor_editor_tarzanaxissandbox_c_rectangle_line_819_coords | sandbox_canvas | editor_editor_tarzanaxissandbox | c_rectangle_line_819 | coords |
| canvas_editor_editor_tarzanaxissandbox_c_rectangle_line_820_coords | sandbox_canvas | editor_editor_tarzanaxissandbox | c_rectangle_line_820 | coords |
| canvas_editor_editor_tarzanaxissandbox_c_rectangle_line_821_coords | sandbox_canvas | editor_editor_tarzanaxissandbox | c_rectangle_line_821 | coords |
| canvas_editor_editor_tarzanaxissandbox_c_rectangle_line_880_coords | sandbox_canvas | editor_editor_tarzanaxissandbox | c_rectangle_line_880 | coords |
| canvas_editor_editor_tarzanaxissandbox_c_text_line_827_text | sandbox_canvas | editor_editor_tarzanaxissandbox | c_text_line_827 | text |
| canvas_editor_editor_tarzanaxissandbox_c_text_line_834_text | sandbox_canvas | editor_editor_tarzanaxissandbox | c_text_line_834 | text |
| canvas_editor_editor_tarzanaxissandbox_c_text_line_873_text | sandbox_canvas | editor_editor_tarzanaxissandbox | c_text_line_873 | text |
| canvas_editor_editor_tarzanaxissandbox_c_text_line_874_text | sandbox_canvas | editor_editor_tarzanaxissandbox | c_text_line_874 | text |
| canvas_editor_editor_tarzanaxissandbox_c_text_line_901_text | sandbox_canvas | editor_editor_tarzanaxissandbox | c_text_line_901 | text |
| canvas_editor_editor_tarzanaxissandbox_c_text_line_902_text | sandbox_canvas | editor_editor_tarzanaxissandbox | c_text_line_902 | text |
| canvas_editor_editor_tarzanehrtakesandbox_canvas_image_line_553_coords | ehr_canvas | editor_editor_tarzanehrtakesandbox | canvas_image_line_553 | coords |
| canvas_editor_editor_tarzanehrtakesandbox_item_text | ehr_canvas | editor_editor_tarzanehrtakesandbox | item | text |
| canvas_editor_editor_tarzanehrtakesandbox_protocol_canvas_rectangle_line_1057_coords | ehr_canvas | editor_editor_tarzanehrtakesandbox | protocol_canvas_rectangle_line_1057 | coords |
| canvas_editor_editor_tarzanehrtakesandbox_protocol_canvas_rectangle_line_1058_coords | ehr_canvas | editor_editor_tarzanehrtakesandbox | protocol_canvas_rectangle_line_1058 | coords |
| canvas_editor_editor_tarzanehrtakesandbox_protocol_title_id_text | ehr_canvas | editor_editor_tarzanehrtakesandbox | protocol_title_id | text |
| canvas_editor_editor_tarzanehrtakesandbox_row_window_coords | ehr_canvas | editor_editor_tarzanehrtakesandbox | row_window | coords |
| canvas_editor_editor_tarzanehrtakesandbox_save_button_window_coords | ehr_canvas | editor_editor_tarzanehrtakesandbox | save_button_window | coords |
| canvas_editor_editor_tarzantakeprotocollight_canvas_image_line_860_coords | canvas_preview | editor_editor_tarzantakeprotocollight | canvas_image_line_860 | coords |
| canvas_editor_editor_tarzantakeprotocollight_item_text | canvas_preview | editor_editor_tarzantakeprotocollight | item | text |
| canvas_editor_editor_tarzantakeprotocollight_protocol_canvas_rectangle_line_1215_coords | canvas_preview | editor_editor_tarzantakeprotocollight | protocol_canvas_rectangle_line_1215 | coords |
| canvas_editor_editor_tarzantakeprotocollight_protocol_canvas_rectangle_line_1216_coords | canvas_preview | editor_editor_tarzantakeprotocollight | protocol_canvas_rectangle_line_1216 | coords |
| canvas_editor_editor_tarzantakeprotocollight_protocol_title_id_text | canvas_preview | editor_editor_tarzantakeprotocollight | protocol_title_id | text |
| canvas_editor_editor_tarzantakeprotocollight_row_window_coords | canvas_preview | editor_editor_tarzantakeprotocollight | row_window | coords |
| canvas_editor_editor_tarzantakeprotocollight_save_button_window_coords | canvas_preview | editor_editor_tarzantakeprotocollight | save_button_window | coords |
| canvas_editor_ehr_tarzanaxissandbox_c_line_line_827_coords | ehr_canvas | editor_ehr_tarzanaxissandbox | c_line_line_827 | coords |
| canvas_editor_ehr_tarzanaxissandbox_c_line_line_834_coords | ehr_canvas | editor_ehr_tarzanaxissandbox | c_line_line_834 | coords |
| canvas_editor_ehr_tarzanaxissandbox_c_line_line_841_coords | ehr_canvas | editor_ehr_tarzanaxissandbox | c_line_line_841 | coords |
| canvas_editor_ehr_tarzanaxissandbox_c_line_line_853_coords | ehr_canvas | editor_ehr_tarzanaxissandbox | c_line_line_853 | coords |
| canvas_editor_ehr_tarzanaxissandbox_c_line_line_854_coords | ehr_canvas | editor_ehr_tarzanaxissandbox | c_line_line_854 | coords |
| canvas_editor_ehr_tarzanaxissandbox_c_line_line_868_coords | ehr_canvas | editor_ehr_tarzanaxissandbox | c_line_line_868 | coords |
| canvas_editor_ehr_tarzanaxissandbox_c_line_line_880_coords | ehr_canvas | editor_ehr_tarzanaxissandbox | c_line_line_880 | coords |
| canvas_editor_ehr_tarzanaxissandbox_c_line_line_882_coords | ehr_canvas | editor_ehr_tarzanaxissandbox | c_line_line_882 | coords |
| canvas_editor_ehr_tarzanaxissandbox_c_oval_line_850_coords | ehr_canvas | editor_ehr_tarzanaxissandbox | c_oval_line_850 | coords |
| canvas_editor_ehr_tarzanaxissandbox_c_rectangle_line_813_coords | ehr_canvas | editor_ehr_tarzanaxissandbox | c_rectangle_line_813 | coords |
| canvas_editor_ehr_tarzanaxissandbox_c_rectangle_line_820_coords | ehr_canvas | editor_ehr_tarzanaxissandbox | c_rectangle_line_820 | coords |
| canvas_editor_ehr_tarzanaxissandbox_c_rectangle_line_821_coords | ehr_canvas | editor_ehr_tarzanaxissandbox | c_rectangle_line_821 | coords |
| canvas_editor_ehr_tarzanaxissandbox_c_rectangle_line_822_coords | ehr_canvas | editor_ehr_tarzanaxissandbox | c_rectangle_line_822 | coords |
| canvas_editor_ehr_tarzanaxissandbox_c_rectangle_line_862_coords | ehr_canvas | editor_ehr_tarzanaxissandbox | c_rectangle_line_862 | coords |
| canvas_editor_ehr_tarzanaxissandbox_c_text_line_828_text | ehr_canvas | editor_ehr_tarzanaxissandbox | c_text_line_828 | text |
| canvas_editor_ehr_tarzanaxissandbox_c_text_line_835_text | ehr_canvas | editor_ehr_tarzanaxissandbox | c_text_line_835 | text |
| canvas_editor_ehr_tarzanaxissandbox_c_text_line_855_text | ehr_canvas | editor_ehr_tarzanaxissandbox | c_text_line_855 | text |
| canvas_editor_ehr_tarzanaxissandbox_c_text_line_856_text | ehr_canvas | editor_ehr_tarzanaxissandbox | c_text_line_856 | text |
| canvas_editor_ehr_tarzanaxissandbox_c_text_line_883_text | ehr_canvas | editor_ehr_tarzanaxissandbox | c_text_line_883 | text |
| canvas_editor_ehr_tarzanaxissandbox_c_text_line_884_text | ehr_canvas | editor_ehr_tarzanaxissandbox | c_text_line_884 | text |
| canvas_editor_ehr_tarzanehrui_c_image_line_3130_coords | ehr_canvas | editor_ehr_tarzanehrui | c_image_line_3130 | coords |
| canvas_editor_ehr_tarzanehrui_c_line_line_1993_coords | ehr_canvas | editor_ehr_tarzanehrui | c_line_line_1993 | coords |
| canvas_editor_ehr_tarzanehrui_c_line_line_2002_coords | ehr_canvas | editor_ehr_tarzanehrui | c_line_line_2002 | coords |
| canvas_editor_ehr_tarzanehrui_c_line_line_2013_coords | ehr_canvas | editor_ehr_tarzanehrui | c_line_line_2013 | coords |
| canvas_editor_ehr_tarzanehrui_c_line_line_2020_coords | ehr_canvas | editor_ehr_tarzanehrui | c_line_line_2020 | coords |
| canvas_editor_ehr_tarzanehrui_c_line_line_2048_coords | ehr_canvas | editor_ehr_tarzanehrui | c_line_line_2048 | coords |
| canvas_editor_ehr_tarzanehrui_c_line_line_2049_coords | ehr_canvas | editor_ehr_tarzanehrui | c_line_line_2049 | coords |
| canvas_editor_ehr_tarzanehrui_c_line_line_2068_coords | ehr_canvas | editor_ehr_tarzanehrui | c_line_line_2068 | coords |
| canvas_editor_ehr_tarzanehrui_c_line_line_2080_coords | ehr_canvas | editor_ehr_tarzanehrui | c_line_line_2080 | coords |
| canvas_editor_ehr_tarzanehrui_c_line_line_2082_coords | ehr_canvas | editor_ehr_tarzanehrui | c_line_line_2082 | coords |
| canvas_editor_ehr_tarzanehrui_c_line_line_3081_coords | ehr_canvas | editor_ehr_tarzanehrui | c_line_line_3081 | coords |
| canvas_editor_ehr_tarzanehrui_c_line_line_3102_coords | ehr_canvas | editor_ehr_tarzanehrui | c_line_line_3102 | coords |
| canvas_editor_ehr_tarzanehrui_c_line_line_3105_coords | ehr_canvas | editor_ehr_tarzanehrui | c_line_line_3105 | coords |
| canvas_editor_ehr_tarzanehrui_c_line_line_3145_coords | ehr_canvas | editor_ehr_tarzanehrui | c_line_line_3145 | coords |
| canvas_editor_ehr_tarzanehrui_c_line_line_3153_coords | ehr_canvas | editor_ehr_tarzanehrui | c_line_line_3153 | coords |
| canvas_editor_ehr_tarzanehrui_c_line_line_3161_coords | ehr_canvas | editor_ehr_tarzanehrui | c_line_line_3161 | coords |
| canvas_editor_ehr_tarzanehrui_c_line_line_3176_coords | ehr_canvas | editor_ehr_tarzanehrui | c_line_line_3176 | coords |
| canvas_editor_ehr_tarzanehrui_c_line_line_3217_coords | ehr_canvas | editor_ehr_tarzanehrui | c_line_line_3217 | coords |
| canvas_editor_ehr_tarzanehrui_c_line_line_3231_coords | ehr_canvas | editor_ehr_tarzanehrui | c_line_line_3231 | coords |
| canvas_editor_ehr_tarzanehrui_c_oval_line_2044_coords | ehr_canvas | editor_ehr_tarzanehrui | c_oval_line_2044 | coords |
| canvas_editor_ehr_tarzanehrui_c_oval_line_3194_coords | ehr_canvas | editor_ehr_tarzanehrui | c_oval_line_3194 | coords |
| canvas_editor_ehr_tarzanehrui_c_oval_line_3210_coords | ehr_canvas | editor_ehr_tarzanehrui | c_oval_line_3210 | coords |
| canvas_editor_ehr_tarzanehrui_c_polygon_line_3226_coords | ehr_canvas | editor_ehr_tarzanehrui | c_polygon_line_3226 | coords |
| canvas_editor_ehr_tarzanehrui_c_rectangle_line_1976_coords | ehr_canvas | editor_ehr_tarzanehrui | c_rectangle_line_1976 | coords |
| canvas_editor_ehr_tarzanehrui_c_rectangle_line_1984_coords | ehr_canvas | editor_ehr_tarzanehrui | c_rectangle_line_1984 | coords |
| canvas_editor_ehr_tarzanehrui_c_rectangle_line_1985_coords | ehr_canvas | editor_ehr_tarzanehrui | c_rectangle_line_1985 | coords |
| canvas_editor_ehr_tarzanehrui_c_rectangle_line_1986_coords | ehr_canvas | editor_ehr_tarzanehrui | c_rectangle_line_1986 | coords |
| canvas_editor_ehr_tarzanehrui_c_rectangle_line_2062_coords | ehr_canvas | editor_ehr_tarzanehrui | c_rectangle_line_2062 | coords |
| canvas_editor_ehr_tarzanehrui_c_rectangle_line_3072_coords | ehr_canvas | editor_ehr_tarzanehrui | c_rectangle_line_3072 | coords |
| canvas_editor_ehr_tarzanehrui_c_rectangle_line_3100_coords | ehr_canvas | editor_ehr_tarzanehrui | c_rectangle_line_3100 | coords |
| canvas_editor_ehr_tarzanehrui_c_rectangle_line_3192_coords | ehr_canvas | editor_ehr_tarzanehrui | c_rectangle_line_3192 | coords |
| canvas_editor_ehr_tarzanehrui_c_rectangle_line_3216_coords | ehr_canvas | editor_ehr_tarzanehrui | c_rectangle_line_3216 | coords |
| canvas_editor_ehr_tarzanehrui_c_text_line_1994_text | ehr_canvas | editor_ehr_tarzanehrui | c_text_line_1994 | text |
| canvas_editor_ehr_tarzanehrui_c_text_line_2003_text | ehr_canvas | editor_ehr_tarzanehrui | c_text_line_2003 | text |
| canvas_editor_ehr_tarzanehrui_c_text_line_2050_text | ehr_canvas | editor_ehr_tarzanehrui | c_text_line_2050 | text |
| canvas_editor_ehr_tarzanehrui_c_text_line_2051_text | ehr_canvas | editor_ehr_tarzanehrui | c_text_line_2051 | text |
| canvas_editor_ehr_tarzanehrui_c_text_line_2083_text | ehr_canvas | editor_ehr_tarzanehrui | c_text_line_2083 | text |
| canvas_editor_ehr_tarzanehrui_c_text_line_2084_text | ehr_canvas | editor_ehr_tarzanehrui | c_text_line_2084 | text |
| canvas_editor_ehr_tarzanehrui_c_text_line_3115_text | ehr_canvas | editor_ehr_tarzanehrui | c_text_line_3115 | text |
| canvas_editor_ehr_tarzanehrui_c_text_line_3122_text | ehr_canvas | editor_ehr_tarzanehrui | c_text_line_3122 | text |
| canvas_editor_ehr_tarzanehrui_c_text_line_3132_text | ehr_canvas | editor_ehr_tarzanehrui | c_text_line_3132 | text |
| canvas_editor_ehr_tarzanehrui_c_text_line_3228_text | ehr_canvas | editor_ehr_tarzanehrui | c_text_line_3228 | text |
| canvas_editor_ehr_tarzanehrui_c_text_line_3239_text | ehr_canvas | editor_ehr_tarzanehrui | c_text_line_3239 | text |
| canvas_editor_ehr_tarzanehrui_canvas_image_line_760_coords | ehr_canvas | editor_ehr_tarzanehrui | canvas_image_line_760 | coords |
| canvas_editor_ehr_tarzanehrui_canvas_rectangle_line_1300_coords | ehr_canvas | editor_ehr_tarzanehrui | canvas_rectangle_line_1300 | coords |
| canvas_editor_ehr_tarzanehrui_canvas_window_line_1226_coords | ehr_canvas | editor_ehr_tarzanehrui | canvas_window_line_1226 | coords |
| canvas_editor_ehr_tarzanehrui_item_text | ehr_canvas | editor_ehr_tarzanehrui | item | text |
| canvas_editor_ehr_tarzanehrui_protocol_canvas_rectangle_line_1010_coords | ehr_canvas | editor_ehr_tarzanehrui | protocol_canvas_rectangle_line_1010 | coords |
| canvas_editor_ehr_tarzanehrui_protocol_canvas_rectangle_line_1011_coords | ehr_canvas | editor_ehr_tarzanehrui | protocol_canvas_rectangle_line_1011 | coords |
| canvas_editor_ehr_tarzanehrui_row_window_coords | ehr_canvas | editor_ehr_tarzanehrui | row_window | coords |
| canvas_editor_ehr_tarzanehrui_save_button_window_coords | ehr_canvas | editor_ehr_tarzanehrui | save_button_window | coords |
| canvas_editor_par_tarzannextionpreview_edit_window_coords | canvas_preview | editor_par_tarzannextionpreview | _edit_window | coords |
| canvas_editor_par_tarzannextionpreview_screen_canvas_image_line_591_coords | canvas_preview | editor_par_tarzannextionpreview | screen_canvas_image_line_591 | coords |
| canvas_editor_par_tarzannextionpreview_screen_canvas_image_line_623_coords | canvas_preview | editor_par_tarzannextionpreview | screen_canvas_image_line_623 | coords |
| canvas_editor_par_tarzannextionpreview_screen_canvas_image_line_640_coords | canvas_preview | editor_par_tarzannextionpreview | screen_canvas_image_line_640 | coords |
| canvas_editor_par_tarzannextionpreview_screen_canvas_image_line_692_coords | canvas_preview | editor_par_tarzannextionpreview | screen_canvas_image_line_692 | coords |
| canvas_editor_par_tarzannextionpreview_screen_canvas_image_line_718_coords | canvas_preview | editor_par_tarzannextionpreview | screen_canvas_image_line_718 | coords |
| canvas_editor_par_tarzannextionpreview_screen_canvas_line_line_415_coords | canvas_preview | editor_par_tarzannextionpreview | screen_canvas_line_line_415 | coords |
| canvas_editor_par_tarzannextionpreview_screen_canvas_line_line_432_coords | canvas_preview | editor_par_tarzannextionpreview | screen_canvas_line_line_432 | coords |
| canvas_editor_par_tarzannextionpreview_screen_canvas_line_line_445_coords | canvas_preview | editor_par_tarzannextionpreview | screen_canvas_line_line_445 | coords |
| canvas_editor_par_tarzannextionpreview_screen_canvas_line_line_737_coords | canvas_preview | editor_par_tarzannextionpreview | screen_canvas_line_line_737 | coords |
| canvas_editor_par_tarzannextionpreview_screen_canvas_line_line_738_coords | canvas_preview | editor_par_tarzannextionpreview | screen_canvas_line_line_738 | coords |
| canvas_editor_par_tarzannextionpreview_screen_canvas_line_line_818_coords | canvas_preview | editor_par_tarzannextionpreview | screen_canvas_line_line_818 | coords |
| canvas_editor_par_tarzannextionpreview_screen_canvas_oval_line_740_coords | canvas_preview | editor_par_tarzannextionpreview | screen_canvas_oval_line_740 | coords |
| canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_394_coords | canvas_preview | editor_par_tarzannextionpreview | screen_canvas_rectangle_line_394 | coords |
| canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_512_coords | canvas_preview | editor_par_tarzannextionpreview | screen_canvas_rectangle_line_512 | coords |
| canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_527_coords | canvas_preview | editor_par_tarzannextionpreview | screen_canvas_rectangle_line_527 | coords |
| canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_593_coords | canvas_preview | editor_par_tarzannextionpreview | screen_canvas_rectangle_line_593 | coords |
| canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_625_coords | canvas_preview | editor_par_tarzannextionpreview | screen_canvas_rectangle_line_625 | coords |
| canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_642_coords | canvas_preview | editor_par_tarzannextionpreview | screen_canvas_rectangle_line_642 | coords |
| canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_785_coords | canvas_preview | editor_par_tarzannextionpreview | screen_canvas_rectangle_line_785 | coords |
| canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_787_coords | canvas_preview | editor_par_tarzannextionpreview | screen_canvas_rectangle_line_787 | coords |
| canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_790_coords | canvas_preview | editor_par_tarzannextionpreview | screen_canvas_rectangle_line_790 | coords |
| canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_797_coords | canvas_preview | editor_par_tarzannextionpreview | screen_canvas_rectangle_line_797 | coords |
| canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_815_coords | canvas_preview | editor_par_tarzannextionpreview | screen_canvas_rectangle_line_815 | coords |
| canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_400_text | canvas_preview | editor_par_tarzannextionpreview | screen_canvas_text_line_400 | text |
| canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_414_text | canvas_preview | editor_par_tarzannextionpreview | screen_canvas_text_line_414 | text |
| canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_421_text | canvas_preview | editor_par_tarzannextionpreview | screen_canvas_text_line_421 | text |
| canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_425_text | canvas_preview | editor_par_tarzannextionpreview | screen_canvas_text_line_425 | text |
| canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_466_text | canvas_preview | editor_par_tarzannextionpreview | screen_canvas_text_line_466 | text |
| canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_483_text | canvas_preview | editor_par_tarzannextionpreview | screen_canvas_text_line_483 | text |
| canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_518_text | canvas_preview | editor_par_tarzannextionpreview | screen_canvas_text_line_518 | text |
| canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_529_text | canvas_preview | editor_par_tarzannextionpreview | screen_canvas_text_line_529 | text |
| canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_594_text | canvas_preview | editor_par_tarzannextionpreview | screen_canvas_text_line_594 | text |
| canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_603_text | canvas_preview | editor_par_tarzannextionpreview | screen_canvas_text_line_603 | text |
| canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_626_text | canvas_preview | editor_par_tarzannextionpreview | screen_canvas_text_line_626 | text |
| canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_643_text | canvas_preview | editor_par_tarzannextionpreview | screen_canvas_text_line_643 | text |
| canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_791_text | canvas_preview | editor_par_tarzannextionpreview | screen_canvas_text_line_791 | text |
| canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_798_text | canvas_preview | editor_par_tarzannextionpreview | screen_canvas_text_line_798 | text |
| canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_799_text | canvas_preview | editor_par_tarzannextionpreview | screen_canvas_text_line_799 | text |
| canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_816_text | canvas_preview | editor_par_tarzannextionpreview | screen_canvas_text_line_816 | text |
| canvas_editor_par_tarzanparapp_canvas_oval_line_1309_coords | layout_canvas | editor_par_tarzanparapp | canvas_oval_line_1309 | coords |
| canvas_editor_par_tarzanparapp_canvas_oval_line_1402_coords | layout_canvas | editor_par_tarzanparapp | canvas_oval_line_1402 | coords |
| canvas_editor_par_tarzanparapp_canvas_rectangle_line_1286_coords | layout_canvas | editor_par_tarzanparapp | canvas_rectangle_line_1286 | coords |
| canvas_editor_par_tarzanparapp_canvas_rectangle_line_1303_coords | layout_canvas | editor_par_tarzanparapp | canvas_rectangle_line_1303 | coords |
| canvas_editor_par_tarzanparapp_canvas_rectangle_line_1314_coords | layout_canvas | editor_par_tarzanparapp | canvas_rectangle_line_1314 | coords |
| canvas_editor_par_tarzanparapp_canvas_rectangle_line_1315_coords | layout_canvas | editor_par_tarzanparapp | canvas_rectangle_line_1315 | coords |
| canvas_editor_par_tarzanparapp_canvas_rectangle_line_1316_coords | layout_canvas | editor_par_tarzanparapp | canvas_rectangle_line_1316 | coords |
| canvas_editor_par_tarzanparapp_canvas_rectangle_line_1329_coords | layout_canvas | editor_par_tarzanparapp | canvas_rectangle_line_1329 | coords |
| canvas_editor_par_tarzanparapp_canvas_rectangle_line_1387_coords | layout_canvas | editor_par_tarzanparapp | canvas_rectangle_line_1387 | coords |
| canvas_editor_par_tarzanparapp_canvas_rectangle_line_1414_coords | layout_canvas | editor_par_tarzanparapp | canvas_rectangle_line_1414 | coords |
| canvas_editor_par_tarzanparapp_canvas_rectangle_line_1415_coords | layout_canvas | editor_par_tarzanparapp | canvas_rectangle_line_1415 | coords |
| canvas_editor_par_tarzanparapp_canvas_rectangle_line_1416_coords | layout_canvas | editor_par_tarzanparapp | canvas_rectangle_line_1416 | coords |
| canvas_editor_par_tarzanparapp_canvas_rectangle_line_1431_coords | layout_canvas | editor_par_tarzanparapp | canvas_rectangle_line_1431 | coords |
| canvas_editor_par_tarzanparapp_canvas_text_line_1310_text | layout_canvas | editor_par_tarzanparapp | canvas_text_line_1310 | text |
| canvas_editor_par_tarzanparapp_canvas_text_line_1434_text | layout_canvas | editor_par_tarzanparapp | canvas_text_line_1434 | text |
| canvas_editor_par_tarzanparapp_canvas_text_line_1451_text | layout_canvas | editor_par_tarzanparapp | canvas_text_line_1451 | text |
| canvas_editor_par_tarzanparapp_canvas_text_line_1455_text | layout_canvas | editor_par_tarzanparapp | canvas_text_line_1455 | text |
| canvas_editor_par_tarzanparapp_led_oval_line_485_coords | layout_canvas | editor_par_tarzanparapp | led_oval_line_485 | coords |
| canvas_editor_par_tarzanparapp_panel_canvas_window_line_1076_coords | layout_canvas | editor_par_tarzanparapp | panel_canvas_window_line_1076 | coords |
| canvas_editor_par_tarzanparapp_text_id_text | layout_canvas | editor_par_tarzanparapp | text_id | text |
| canvas_editor_par_tarzanparpanels_can_image_line_1306_coords | canvas_preview | editor_par_tarzanparpanels | can_image_line_1306 | coords |
| canvas_editor_par_tarzanparpanels_can_line_line_1298_coords | canvas_preview | editor_par_tarzanparpanels | can_line_line_1298 | coords |
| canvas_editor_par_tarzanparpanels_can_line_line_1299_coords | canvas_preview | editor_par_tarzanparpanels | can_line_line_1299 | coords |
| canvas_editor_par_tarzanparpanels_can_line_line_1304_coords | canvas_preview | editor_par_tarzanparpanels | can_line_line_1304 | coords |
| canvas_editor_par_tarzanparpanels_can_line_line_1311_coords | canvas_preview | editor_par_tarzanparpanels | can_line_line_1311 | coords |
| canvas_editor_par_tarzanparpanels_can_line_line_1326_coords | canvas_preview | editor_par_tarzanparpanels | can_line_line_1326 | coords |
| canvas_editor_par_tarzanparpanels_can_line_line_1327_coords | canvas_preview | editor_par_tarzanparpanels | can_line_line_1327 | coords |
| canvas_editor_par_tarzanparpanels_can_line_line_510_coords | canvas_preview | editor_par_tarzanparpanels | can_line_line_510 | coords |
| canvas_editor_par_tarzanparpanels_can_line_line_664_coords | canvas_preview | editor_par_tarzanparpanels | can_line_line_664 | coords |
| canvas_editor_par_tarzanparpanels_can_line_line_665_coords | canvas_preview | editor_par_tarzanparpanels | can_line_line_665 | coords |
| canvas_editor_par_tarzanparpanels_can_oval_line_509_coords | canvas_preview | editor_par_tarzanparpanels | can_oval_line_509 | coords |
| canvas_editor_par_tarzanparpanels_can_oval_line_511_coords | canvas_preview | editor_par_tarzanparpanels | can_oval_line_511 | coords |
| canvas_editor_par_tarzanparpanels_can_oval_line_656_coords | canvas_preview | editor_par_tarzanparpanels | can_oval_line_656 | coords |
| canvas_editor_par_tarzanparpanels_can_oval_line_920_coords | canvas_preview | editor_par_tarzanparpanels | can_oval_line_920 | coords |
| canvas_editor_par_tarzanparpanels_can_polygon_line_921_coords | canvas_preview | editor_par_tarzanparpanels | can_polygon_line_921 | coords |
| canvas_editor_par_tarzanparpanels_can_rectangle_line_899_coords | canvas_preview | editor_par_tarzanparpanels | can_rectangle_line_899 | coords |
| canvas_editor_par_tarzanparpanels_can_rectangle_line_901_coords | canvas_preview | editor_par_tarzanparpanels | can_rectangle_line_901 | coords |
| canvas_editor_par_tarzanparpanels_can_text_line_1307_text | canvas_preview | editor_par_tarzanparpanels | can_text_line_1307 | text |
| canvas_editor_par_tarzanparpanels_can_text_line_1309_text | canvas_preview | editor_par_tarzanparpanels | can_text_line_1309 | text |
| canvas_editor_par_tarzanparpanels_can_text_line_1310_text | canvas_preview | editor_par_tarzanparpanels | can_text_line_1310 | text |
| canvas_editor_par_tarzanparpanels_can_text_line_1329_text | canvas_preview | editor_par_tarzanparpanels | can_text_line_1329 | text |
| canvas_editor_par_tarzanparpanels_can_text_line_1331_text | canvas_preview | editor_par_tarzanparpanels | can_text_line_1331 | text |
| canvas_editor_par_tarzanparpanels_canvas_line_line_825_coords | canvas_preview | editor_par_tarzanparpanels | canvas_line_line_825 | coords |
| canvas_editor_par_tarzanparpanels_canvas_line_line_826_coords | canvas_preview | editor_par_tarzanparpanels | canvas_line_line_826 | coords |
| canvas_editor_par_tarzanparpanels_canvas_oval_line_1575_coords | canvas_preview | editor_par_tarzanparpanels | canvas_oval_line_1575 | coords |
| canvas_editor_par_tarzanparpanels_canvas_oval_line_830_coords | canvas_preview | editor_par_tarzanparpanels | canvas_oval_line_830 | coords |
| canvas_editor_par_tarzanparpanels_canvas_polygon_line_828_coords | canvas_preview | editor_par_tarzanparpanels | canvas_polygon_line_828 | coords |
| canvas_editor_par_tarzanparpanels_canvas_rectangle_line_1449_coords | canvas_preview | editor_par_tarzanparpanels | canvas_rectangle_line_1449 | coords |
| canvas_editor_par_tarzanparpanels_canvas_rectangle_line_1450_coords | canvas_preview | editor_par_tarzanparpanels | canvas_rectangle_line_1450 | coords |
| canvas_editor_par_tarzanparpanels_canvas_rectangle_line_1451_coords | canvas_preview | editor_par_tarzanparpanels | canvas_rectangle_line_1451 | coords |
| canvas_editor_par_tarzanparpanels_old_c_line_line_3118_coords | canvas_preview | editor_par_tarzanparpanels_old | c_line_line_3118 | coords |
| canvas_editor_par_tarzanparpanels_old_c_line_line_3119_coords | canvas_preview | editor_par_tarzanparpanels_old | c_line_line_3119 | coords |
| canvas_editor_par_tarzanparpanels_old_c_oval_line_1979_coords | canvas_preview | editor_par_tarzanparpanels_old | c_oval_line_1979 | coords |
| canvas_editor_par_tarzanparpanels_old_c_oval_line_1980_coords | canvas_preview | editor_par_tarzanparpanels_old | c_oval_line_1980 | coords |
| canvas_editor_par_tarzanparpanels_old_c_oval_line_2212_coords | canvas_preview | editor_par_tarzanparpanels_old | c_oval_line_2212 | coords |
| canvas_editor_par_tarzanparpanels_old_c_oval_line_3111_coords | canvas_preview | editor_par_tarzanparpanels_old | c_oval_line_3111 | coords |
| canvas_editor_par_tarzanparpanels_old_c_oval_line_344_coords | canvas_preview | editor_par_tarzanparpanels_old | c_oval_line_344 | coords |
| canvas_editor_par_tarzanparpanels_old_c_polygon_line_2213_coords | canvas_preview | editor_par_tarzanparpanels_old | c_polygon_line_2213 | coords |
| canvas_editor_par_tarzanparpanels_old_canvas_image_line_1549_coords | canvas_preview | editor_par_tarzanparpanels_old | canvas_image_line_1549 | coords |
| canvas_editor_par_tarzanparpanels_old_canvas_line_line_1538_coords | canvas_preview | editor_par_tarzanparpanels_old | canvas_line_line_1538 | coords |
| canvas_editor_par_tarzanparpanels_old_canvas_line_line_1539_coords | canvas_preview | editor_par_tarzanparpanels_old | canvas_line_line_1539 | coords |
| canvas_editor_par_tarzanparpanels_old_canvas_line_line_1545_coords | canvas_preview | editor_par_tarzanparpanels_old | canvas_line_line_1545 | coords |
| canvas_editor_par_tarzanparpanels_old_canvas_line_line_1563_coords | canvas_preview | editor_par_tarzanparpanels_old | canvas_line_line_1563 | coords |
| canvas_editor_par_tarzanparpanels_old_canvas_line_line_1581_coords | canvas_preview | editor_par_tarzanparpanels_old | canvas_line_line_1581 | coords |
| canvas_editor_par_tarzanparpanels_old_canvas_line_line_1582_coords | canvas_preview | editor_par_tarzanparpanels_old | canvas_line_line_1582 | coords |
| canvas_editor_par_tarzanparpanels_old_canvas_line_line_1784_coords | canvas_preview | editor_par_tarzanparpanels_old | canvas_line_line_1784 | coords |
| canvas_editor_par_tarzanparpanels_old_canvas_line_line_1785_coords | canvas_preview | editor_par_tarzanparpanels_old | canvas_line_line_1785 | coords |
| canvas_editor_par_tarzanparpanels_old_canvas_line_line_2481_coords | canvas_preview | editor_par_tarzanparpanels_old | canvas_line_line_2481 | coords |
| canvas_editor_par_tarzanparpanels_old_canvas_line_line_767_coords | canvas_preview | editor_par_tarzanparpanels_old | canvas_line_line_767 | coords |
| canvas_editor_par_tarzanparpanels_old_canvas_line_line_780_coords | canvas_preview | editor_par_tarzanparpanels_old | canvas_line_line_780 | coords |
| canvas_editor_par_tarzanparpanels_old_canvas_line_line_781_coords | canvas_preview | editor_par_tarzanparpanels_old | canvas_line_line_781 | coords |
| canvas_editor_par_tarzanparpanels_old_canvas_line_line_784_coords | canvas_preview | editor_par_tarzanparpanels_old | canvas_line_line_784 | coords |
| canvas_editor_par_tarzanparpanels_old_canvas_oval_line_1216_coords | canvas_preview | editor_par_tarzanparpanels_old | canvas_oval_line_1216 | coords |
| canvas_editor_par_tarzanparpanels_old_canvas_oval_line_1796_coords | canvas_preview | editor_par_tarzanparpanels_old | canvas_oval_line_1796 | coords |
| canvas_editor_par_tarzanparpanels_old_canvas_oval_line_2480_coords | canvas_preview | editor_par_tarzanparpanels_old | canvas_oval_line_2480 | coords |
| canvas_editor_par_tarzanparpanels_old_canvas_oval_line_2482_coords | canvas_preview | editor_par_tarzanparpanels_old | canvas_oval_line_2482 | coords |
| canvas_editor_par_tarzanparpanels_old_canvas_polygon_line_1786_coords | canvas_preview | editor_par_tarzanparpanels_old | canvas_polygon_line_1786 | coords |
| canvas_editor_par_tarzanparpanels_old_canvas_rectangle_line_1113_coords | canvas_preview | editor_par_tarzanparpanels_old | canvas_rectangle_line_1113 | coords |
| canvas_editor_par_tarzanparpanels_old_canvas_rectangle_line_1114_coords | canvas_preview | editor_par_tarzanparpanels_old | canvas_rectangle_line_1114 | coords |
| canvas_editor_par_tarzanparpanels_old_canvas_rectangle_line_1116_coords | canvas_preview | editor_par_tarzanparpanels_old | canvas_rectangle_line_1116 | coords |
| canvas_editor_par_tarzanparpanels_old_canvas_rectangle_line_1117_coords | canvas_preview | editor_par_tarzanparpanels_old | canvas_rectangle_line_1117 | coords |
| canvas_editor_par_tarzanparpanels_old_canvas_rectangle_line_1313_coords | canvas_preview | editor_par_tarzanparpanels_old | canvas_rectangle_line_1313 | coords |
| canvas_editor_par_tarzanparpanels_old_canvas_rectangle_line_1314_coords | canvas_preview | editor_par_tarzanparpanels_old | canvas_rectangle_line_1314 | coords |
| canvas_editor_par_tarzanparpanels_old_canvas_rectangle_line_1315_coords | canvas_preview | editor_par_tarzanparpanels_old | canvas_rectangle_line_1315 | coords |
| canvas_editor_par_tarzanparpanels_old_canvas_text_line_1551_text | canvas_preview | editor_par_tarzanparpanels_old | canvas_text_line_1551 | text |
| canvas_editor_par_tarzanparpanels_old_canvas_text_line_1554_text | canvas_preview | editor_par_tarzanparpanels_old | canvas_text_line_1554 | text |
| canvas_editor_par_tarzanparpanels_old_canvas_text_line_1555_text | canvas_preview | editor_par_tarzanparpanels_old | canvas_text_line_1555 | text |
| canvas_editor_par_tarzanparpanels_old_canvas_text_line_1586_text | canvas_preview | editor_par_tarzanparpanels_old | canvas_text_line_1586 | text |
| canvas_editor_par_tarzanparpanels_old_canvas_text_line_766_text | canvas_preview | editor_par_tarzanparpanels_old | canvas_text_line_766 | text |
| canvas_editor_par_tarzanparpanels_old_canvas_text_line_785_text | canvas_preview | editor_par_tarzanparpanels_old | canvas_text_line_785 | text |
| canvas_editor_par_tarzanparpanels_old_canvas_window_line_119_coords | canvas_preview | editor_par_tarzanparpanels_old | canvas_window_line_119 | coords |
| canvas_editor_par_tarzanparpanels_old_dot_oval_line_378_coords | canvas_preview | editor_par_tarzanparpanels_old | dot_oval_line_378 | coords |
| canvas_editor_par_tarzanparpanels_old_led_oval_line_1049_coords | canvas_preview | editor_par_tarzanparpanels_old | led_oval_line_1049 | coords |
| canvas_editor_par_tarzanparpanels_old_led_oval_line_1050_coords | canvas_preview | editor_par_tarzanparpanels_old | led_oval_line_1050 | coords |
| canvas_editor_par_tarzanparpanels_old_rect_coords | canvas_preview | editor_par_tarzanparpanels_old | rect | coords |
| canvas_editor_par_tarzanparpanels_old_self_rectangle_line_1346_coords | canvas_preview | editor_par_tarzanparpanels_old | self_rectangle_line_1346 | coords |
| canvas_editor_par_tarzanparpanels_old_self_rectangle_line_1347_coords | canvas_preview | editor_par_tarzanparpanels_old | self_rectangle_line_1347 | coords |
| canvas_editor_par_tarzanparpanels_old_window_id_coords | canvas_preview | editor_par_tarzanparpanels_old | window_id | coords |
| canvas_editor_par_tarzanparpanels_self_rectangle_line_185_coords | canvas_preview | editor_par_tarzanparpanels | self_rectangle_line_185 | coords |
| canvas_editor_par_tarzanparpanels_window_id_coords | canvas_preview | editor_par_tarzanparpanels | window_id | coords |
| canvas_editor_par_tarzanparwidgets_c_line_line_304_coords | canvas_preview | editor_par_tarzanparwidgets | c_line_line_304 | coords |
| canvas_editor_par_tarzanparwidgets_c_oval_line_299_coords | canvas_preview | editor_par_tarzanparwidgets | c_oval_line_299 | coords |
| canvas_editor_par_tarzanparwidgets_c_oval_line_300_coords | canvas_preview | editor_par_tarzanparwidgets | c_oval_line_300 | coords |
| canvas_editor_par_tarzanparwidgets_c_oval_line_305_coords | canvas_preview | editor_par_tarzanparwidgets | c_oval_line_305 | coords |
| canvas_editor_par_tarzanparwidgets_self_oval_line_59_coords | canvas_preview | editor_par_tarzanparwidgets | self_oval_line_59 | coords |
| canvas_editor_par_tarzanparwidgets_self_oval_line_60_coords | canvas_preview | editor_par_tarzanparwidgets | self_oval_line_60 | coords |
| canvas_editor_par_tarzanparwidgets_self_oval_line_64_coords | canvas_preview | editor_par_tarzanparwidgets | self_oval_line_64 | coords |
| canvas_editor_par_tarzanparwidgets_self_oval_line_65_coords | canvas_preview | editor_par_tarzanparwidgets | self_oval_line_65 | coords |
| canvas_editor_par_tarzanparwidgets_self_rectangle_line_90_coords | canvas_preview | editor_par_tarzanparwidgets | self_rectangle_line_90 | coords |
| canvas_editor_tarzanaxissandbox_c_line_line_826_coords | sandbox_canvas | editor_tarzanaxissandbox | c_line_line_826 | coords |
| canvas_editor_tarzanaxissandbox_c_line_line_833_coords | sandbox_canvas | editor_tarzanaxissandbox | c_line_line_833 | coords |
| canvas_editor_tarzanaxissandbox_c_line_line_852_coords | sandbox_canvas | editor_tarzanaxissandbox | c_line_line_852 | coords |
| canvas_editor_tarzanaxissandbox_c_line_line_859_coords | sandbox_canvas | editor_tarzanaxissandbox | c_line_line_859 | coords |
| canvas_editor_tarzanaxissandbox_c_line_line_871_coords | sandbox_canvas | editor_tarzanaxissandbox | c_line_line_871 | coords |
| canvas_editor_tarzanaxissandbox_c_line_line_872_coords | sandbox_canvas | editor_tarzanaxissandbox | c_line_line_872 | coords |
| canvas_editor_tarzanaxissandbox_c_line_line_886_coords | sandbox_canvas | editor_tarzanaxissandbox | c_line_line_886 | coords |
| canvas_editor_tarzanaxissandbox_c_line_line_898_coords | sandbox_canvas | editor_tarzanaxissandbox | c_line_line_898 | coords |
| canvas_editor_tarzanaxissandbox_c_line_line_900_coords | sandbox_canvas | editor_tarzanaxissandbox | c_line_line_900 | coords |
| canvas_editor_tarzanaxissandbox_c_oval_line_868_coords | sandbox_canvas | editor_tarzanaxissandbox | c_oval_line_868 | coords |
| canvas_editor_tarzanaxissandbox_c_rectangle_line_812_coords | sandbox_canvas | editor_tarzanaxissandbox | c_rectangle_line_812 | coords |
| canvas_editor_tarzanaxissandbox_c_rectangle_line_819_coords | sandbox_canvas | editor_tarzanaxissandbox | c_rectangle_line_819 | coords |
| canvas_editor_tarzanaxissandbox_c_rectangle_line_820_coords | sandbox_canvas | editor_tarzanaxissandbox | c_rectangle_line_820 | coords |
| canvas_editor_tarzanaxissandbox_c_rectangle_line_821_coords | sandbox_canvas | editor_tarzanaxissandbox | c_rectangle_line_821 | coords |
| canvas_editor_tarzanaxissandbox_c_rectangle_line_880_coords | sandbox_canvas | editor_tarzanaxissandbox | c_rectangle_line_880 | coords |
| canvas_editor_tarzanaxissandbox_c_text_line_827_text | sandbox_canvas | editor_tarzanaxissandbox | c_text_line_827 | text |
| canvas_editor_tarzanaxissandbox_c_text_line_834_text | sandbox_canvas | editor_tarzanaxissandbox | c_text_line_834 | text |
| canvas_editor_tarzanaxissandbox_c_text_line_873_text | sandbox_canvas | editor_tarzanaxissandbox | c_text_line_873 | text |
| canvas_editor_tarzanaxissandbox_c_text_line_874_text | sandbox_canvas | editor_tarzanaxissandbox | c_text_line_874 | text |
| canvas_editor_tarzanaxissandbox_c_text_line_901_text | sandbox_canvas | editor_tarzanaxissandbox | c_text_line_901 | text |
| canvas_editor_tarzanaxissandbox_c_text_line_902_text | sandbox_canvas | editor_tarzanaxissandbox | c_text_line_902 | text |
| canvas_editor_tarzanehrtakesandbox_canvas_image_line_553_coords | ehr_canvas | editor_tarzanehrtakesandbox | canvas_image_line_553 | coords |
| canvas_editor_tarzanehrtakesandbox_item_text | ehr_canvas | editor_tarzanehrtakesandbox | item | text |
| canvas_editor_tarzanehrtakesandbox_protocol_canvas_rectangle_line_1057_coords | ehr_canvas | editor_tarzanehrtakesandbox | protocol_canvas_rectangle_line_1057 | coords |
| canvas_editor_tarzanehrtakesandbox_protocol_canvas_rectangle_line_1058_coords | ehr_canvas | editor_tarzanehrtakesandbox | protocol_canvas_rectangle_line_1058 | coords |
| canvas_editor_tarzanehrtakesandbox_protocol_title_id_text | ehr_canvas | editor_tarzanehrtakesandbox | protocol_title_id | text |
| canvas_editor_tarzanehrtakesandbox_row_window_coords | ehr_canvas | editor_tarzanehrtakesandbox | row_window | coords |
| canvas_editor_tarzanehrtakesandbox_save_button_window_coords | ehr_canvas | editor_tarzanehrtakesandbox | save_button_window | coords |
| canvas_editor_tarzankhr_c_image_line_1518_coords | khr_canvas | editor_tarzankhr | c_image_line_1518 | coords |
| canvas_editor_tarzankhr_c_image_line_1533_coords | khr_canvas | editor_tarzankhr | c_image_line_1533 | coords |
| canvas_editor_tarzankhr_c_image_line_623_coords | khr_canvas | editor_tarzankhr | c_image_line_623 | coords |
| canvas_editor_tarzankhr_c_line_line_1545_coords | khr_canvas | editor_tarzankhr | c_line_line_1545 | coords |
| canvas_editor_tarzankhr_c_line_line_1546_coords | khr_canvas | editor_tarzankhr | c_line_line_1546 | coords |
| canvas_editor_tarzankhr_c_line_line_1555_coords | khr_canvas | editor_tarzankhr | c_line_line_1555 | coords |
| canvas_editor_tarzankhr_c_line_line_1570_coords | khr_canvas | editor_tarzankhr | c_line_line_1570 | coords |
| canvas_editor_tarzankhr_c_line_line_1571_coords | khr_canvas | editor_tarzankhr | c_line_line_1571 | coords |
| canvas_editor_tarzankhr_c_line_line_1593_coords | khr_canvas | editor_tarzankhr | c_line_line_1593 | coords |
| canvas_editor_tarzankhr_c_line_line_1597_coords | khr_canvas | editor_tarzankhr | c_line_line_1597 | coords |
| canvas_editor_tarzankhr_c_oval_line_1589_coords | khr_canvas | editor_tarzankhr | c_oval_line_1589 | coords |
| canvas_editor_tarzankhr_c_oval_line_1590_coords | khr_canvas | editor_tarzankhr | c_oval_line_1590 | coords |
| canvas_editor_tarzankhr_c_polygon_line_1553_coords | khr_canvas | editor_tarzankhr | c_polygon_line_1553 | coords |
| canvas_editor_tarzankhr_c_polygon_line_1602_coords | khr_canvas | editor_tarzankhr | c_polygon_line_1602 | coords |
| canvas_editor_tarzankhr_c_rectangle_line_1548_coords | khr_canvas | editor_tarzankhr | c_rectangle_line_1548 | coords |
| canvas_editor_tarzankhr_c_rectangle_line_1573_coords | khr_canvas | editor_tarzankhr | c_rectangle_line_1573 | coords |
| canvas_editor_tarzankhr_c_text_line_1457_text | khr_canvas | editor_tarzankhr | c_text_line_1457 | text |
| canvas_editor_tarzankhr_c_text_line_1465_text | khr_canvas | editor_tarzankhr | c_text_line_1465 | text |
| canvas_editor_tarzankhr_c_text_line_1472_text | khr_canvas | editor_tarzankhr | c_text_line_1472 | text |
| canvas_editor_tarzankhr_c_text_line_1473_text | khr_canvas | editor_tarzankhr | c_text_line_1473 | text |
| canvas_editor_tarzankhr_c_text_line_1474_text | khr_canvas | editor_tarzankhr | c_text_line_1474 | text |
| canvas_editor_tarzankhr_c_text_line_1481_text | khr_canvas | editor_tarzankhr | c_text_line_1481 | text |
| canvas_editor_tarzankhr_c_text_line_1486_text | khr_canvas | editor_tarzankhr | c_text_line_1486 | text |
| canvas_editor_tarzankhr_c_text_line_1496_text | khr_canvas | editor_tarzankhr | c_text_line_1496 | text |
| canvas_editor_tarzankhr_c_text_line_1503_text | khr_canvas | editor_tarzankhr | c_text_line_1503 | text |
| canvas_editor_tarzankhr_c_text_line_1520_text | khr_canvas | editor_tarzankhr | c_text_line_1520 | text |
| canvas_editor_tarzankhr_c_text_line_1522_text | khr_canvas | editor_tarzankhr | c_text_line_1522 | text |
| canvas_editor_tarzankhr_c_text_line_1525_text | khr_canvas | editor_tarzankhr | c_text_line_1525 | text |
| canvas_editor_tarzankhr_c_text_line_1542_text | khr_canvas | editor_tarzankhr | c_text_line_1542 | text |
| canvas_editor_tarzankhr_c_text_line_1549_text | khr_canvas | editor_tarzankhr | c_text_line_1549 | text |
| canvas_editor_tarzankhr_c_text_line_1554_text | khr_canvas | editor_tarzankhr | c_text_line_1554 | text |
| canvas_editor_tarzankhr_c_text_line_1556_text | khr_canvas | editor_tarzankhr | c_text_line_1556 | text |
| canvas_editor_tarzankhr_c_text_line_1564_text | khr_canvas | editor_tarzankhr | c_text_line_1564 | text |
| canvas_editor_tarzankhr_c_text_line_1569_text | khr_canvas | editor_tarzankhr | c_text_line_1569 | text |
| canvas_editor_tarzankhr_c_text_line_1574_text | khr_canvas | editor_tarzankhr | c_text_line_1574 | text |
| canvas_editor_tarzankhr_c_text_line_1576_text | khr_canvas | editor_tarzankhr | c_text_line_1576 | text |
| canvas_editor_tarzankhr_c_text_line_1578_text | khr_canvas | editor_tarzankhr | c_text_line_1578 | text |
| canvas_editor_tarzankhr_c_text_line_1579_text | khr_canvas | editor_tarzankhr | c_text_line_1579 | text |
| canvas_editor_tarzankhr_c_text_line_1580_text | khr_canvas | editor_tarzankhr | c_text_line_1580 | text |
| canvas_editor_tarzankhr_c_text_line_1603_text | khr_canvas | editor_tarzankhr | c_text_line_1603 | text |
| canvas_editor_tarzankhr_c_text_line_1604_text | khr_canvas | editor_tarzankhr | c_text_line_1604 | text |
| canvas_editor_tarzankhr_c_text_line_1605_text | khr_canvas | editor_tarzankhr | c_text_line_1605 | text |
| canvas_editor_tarzankhr_c_text_line_615_text | khr_canvas | editor_tarzankhr | c_text_line_615 | text |
| canvas_editor_tarzankhr_c_text_line_625_text | khr_canvas | editor_tarzankhr | c_text_line_625 | text |
| canvas_editor_tarzankhr_c_text_line_627_text | khr_canvas | editor_tarzankhr | c_text_line_627 | text |
| canvas_editor_tarzankhr_c_text_line_629_text | khr_canvas | editor_tarzankhr | c_text_line_629 | text |
| canvas_editor_tarzantakeprotocollight_canvas_image_line_860_coords | canvas_preview | editor_tarzantakeprotocollight | canvas_image_line_860 | coords |
| canvas_editor_tarzantakeprotocollight_item_text | canvas_preview | editor_tarzantakeprotocollight | item | text |
| canvas_editor_tarzantakeprotocollight_protocol_canvas_rectangle_line_1215_coords | canvas_preview | editor_tarzantakeprotocollight | protocol_canvas_rectangle_line_1215 | coords |
| canvas_editor_tarzantakeprotocollight_protocol_canvas_rectangle_line_1216_coords | canvas_preview | editor_tarzantakeprotocollight | protocol_canvas_rectangle_line_1216 | coords |
| canvas_editor_tarzantakeprotocollight_protocol_title_id_text | canvas_preview | editor_tarzantakeprotocollight | protocol_title_id | text |
| canvas_editor_tarzantakeprotocollight_row_window_coords | canvas_preview | editor_tarzantakeprotocollight | row_window | coords |
| canvas_editor_tarzantakeprotocollight_save_button_window_coords | canvas_preview | editor_tarzantakeprotocollight | save_button_window | coords |
| canvas_mechanics_tarzanedytorchoreografiiruchu_c_line_line_305_coords | canvas_preview | mechanics_tarzanedytorchoreografiiruchu | c_line_line_305 | coords |
| canvas_mechanics_tarzanedytorchoreografiiruchu_c_line_line_313_coords | canvas_preview | mechanics_tarzanedytorchoreografiiruchu | c_line_line_313 | coords |
| canvas_mechanics_tarzanedytorchoreografiiruchu_c_text_line_314_text | canvas_preview | mechanics_tarzanedytorchoreografiiruchu | c_text_line_314 | text |
| canvas_mechanics_tarzanedytorchoreografiiruchu_scroll_window_coords | canvas_preview | mechanics_tarzanedytorchoreografiiruchu | scroll_window | coords |
| canvas_mechanics_tarzanwykresosi_c_line_line_1011_coords | canvas_preview | mechanics_tarzanwykresosi | c_line_line_1011 | coords |
| canvas_mechanics_tarzanwykresosi_c_line_line_1012_coords | canvas_preview | mechanics_tarzanwykresosi | c_line_line_1012 | coords |
| canvas_mechanics_tarzanwykresosi_c_line_line_754_coords | canvas_preview | mechanics_tarzanwykresosi | c_line_line_754 | coords |
| canvas_mechanics_tarzanwykresosi_c_line_line_756_coords | canvas_preview | mechanics_tarzanwykresosi | c_line_line_756 | coords |
| canvas_mechanics_tarzanwykresosi_c_line_line_757_coords | canvas_preview | mechanics_tarzanwykresosi | c_line_line_757 | coords |
| canvas_mechanics_tarzanwykresosi_c_line_line_770_coords | canvas_preview | mechanics_tarzanwykresosi | c_line_line_770 | coords |
| canvas_mechanics_tarzanwykresosi_c_oval_line_777_coords | canvas_preview | mechanics_tarzanwykresosi | c_oval_line_777 | coords |
| canvas_mechanics_tarzanwykresosi_c_polygon_line_1013_coords | canvas_preview | mechanics_tarzanwykresosi | c_polygon_line_1013 | coords |
| canvas_mechanics_tarzanwykresosi_c_rectangle_line_723_coords | canvas_preview | mechanics_tarzanwykresosi | c_rectangle_line_723 | coords |
| canvas_mechanics_tarzanwykresosi_c_rectangle_line_732_coords | canvas_preview | mechanics_tarzanwykresosi | c_rectangle_line_732 | coords |
| canvas_mechanics_tarzanwykresosi_c_rectangle_line_734_coords | canvas_preview | mechanics_tarzanwykresosi | c_rectangle_line_734 | coords |
| canvas_mechanics_tarzanwykresosi_c_rectangle_line_751_coords | canvas_preview | mechanics_tarzanwykresosi | c_rectangle_line_751 | coords |
| canvas_mechanics_tarzanwykresosi_c_text_line_1014_text | canvas_preview | mechanics_tarzanwykresosi | c_text_line_1014 | text |
| canvas_mechanics_tarzanwykresosi_c_text_line_731_text | canvas_preview | mechanics_tarzanwykresosi | c_text_line_731 | text |
| canvas_mechanics_tarzanwykresosi_c_text_line_735_text | canvas_preview | mechanics_tarzanwykresosi | c_text_line_735 | text |
| canvas_mechanics_tarzanwykresosi_c_text_line_758_text | canvas_preview | mechanics_tarzanwykresosi | c_text_line_758 | text |
| canvas_mechanics_tarzanwykresosi_c_text_line_759_text | canvas_preview | mechanics_tarzanwykresosi | c_text_line_759 | text |
| canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_line_line_826_coords | ehr_canvas | modes_editor_editor_ehr_tarzanaxissandbox | c_line_line_826 | coords |
| canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_line_line_833_coords | ehr_canvas | modes_editor_editor_ehr_tarzanaxissandbox | c_line_line_833 | coords |
| canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_line_line_840_coords | ehr_canvas | modes_editor_editor_ehr_tarzanaxissandbox | c_line_line_840 | coords |
| canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_line_line_852_coords | ehr_canvas | modes_editor_editor_ehr_tarzanaxissandbox | c_line_line_852 | coords |
| canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_line_line_853_coords | ehr_canvas | modes_editor_editor_ehr_tarzanaxissandbox | c_line_line_853 | coords |
| canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_line_line_867_coords | ehr_canvas | modes_editor_editor_ehr_tarzanaxissandbox | c_line_line_867 | coords |
| canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_line_line_879_coords | ehr_canvas | modes_editor_editor_ehr_tarzanaxissandbox | c_line_line_879 | coords |
| canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_line_line_881_coords | ehr_canvas | modes_editor_editor_ehr_tarzanaxissandbox | c_line_line_881 | coords |
| canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_oval_line_849_coords | ehr_canvas | modes_editor_editor_ehr_tarzanaxissandbox | c_oval_line_849 | coords |
| canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_812_coords | ehr_canvas | modes_editor_editor_ehr_tarzanaxissandbox | c_rectangle_line_812 | coords |
| canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_819_coords | ehr_canvas | modes_editor_editor_ehr_tarzanaxissandbox | c_rectangle_line_819 | coords |
| canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_820_coords | ehr_canvas | modes_editor_editor_ehr_tarzanaxissandbox | c_rectangle_line_820 | coords |
| canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_821_coords | ehr_canvas | modes_editor_editor_ehr_tarzanaxissandbox | c_rectangle_line_821 | coords |
| canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_861_coords | ehr_canvas | modes_editor_editor_ehr_tarzanaxissandbox | c_rectangle_line_861 | coords |
| canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_text_line_827_text | ehr_canvas | modes_editor_editor_ehr_tarzanaxissandbox | c_text_line_827 | text |
| canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_text_line_834_text | ehr_canvas | modes_editor_editor_ehr_tarzanaxissandbox | c_text_line_834 | text |
| canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_text_line_854_text | ehr_canvas | modes_editor_editor_ehr_tarzanaxissandbox | c_text_line_854 | text |
| canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_text_line_855_text | ehr_canvas | modes_editor_editor_ehr_tarzanaxissandbox | c_text_line_855 | text |
| canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_text_line_882_text | ehr_canvas | modes_editor_editor_ehr_tarzanaxissandbox | c_text_line_882 | text |
| canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_text_line_883_text | ehr_canvas | modes_editor_editor_ehr_tarzanaxissandbox | c_text_line_883 | text |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_image_line_2734_coords | ehr_canvas | modes_editor_editor_ehr_tarzanehrui | c_image_line_2734 | coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_1910_coords | ehr_canvas | modes_editor_editor_ehr_tarzanehrui | c_line_line_1910 | coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_1919_coords | ehr_canvas | modes_editor_editor_ehr_tarzanehrui | c_line_line_1919 | coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_1930_coords | ehr_canvas | modes_editor_editor_ehr_tarzanehrui | c_line_line_1930 | coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_1937_coords | ehr_canvas | modes_editor_editor_ehr_tarzanehrui | c_line_line_1937 | coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_1951_coords | ehr_canvas | modes_editor_editor_ehr_tarzanehrui | c_line_line_1951 | coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_1952_coords | ehr_canvas | modes_editor_editor_ehr_tarzanehrui | c_line_line_1952 | coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_1966_coords | ehr_canvas | modes_editor_editor_ehr_tarzanehrui | c_line_line_1966 | coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_1978_coords | ehr_canvas | modes_editor_editor_ehr_tarzanehrui | c_line_line_1978 | coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_1980_coords | ehr_canvas | modes_editor_editor_ehr_tarzanehrui | c_line_line_1980 | coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_2697_coords | ehr_canvas | modes_editor_editor_ehr_tarzanehrui | c_line_line_2697 | coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_2707_coords | ehr_canvas | modes_editor_editor_ehr_tarzanehrui | c_line_line_2707 | coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_2710_coords | ehr_canvas | modes_editor_editor_ehr_tarzanehrui | c_line_line_2710 | coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_2749_coords | ehr_canvas | modes_editor_editor_ehr_tarzanehrui | c_line_line_2749 | coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_2757_coords | ehr_canvas | modes_editor_editor_ehr_tarzanehrui | c_line_line_2757 | coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_2765_coords | ehr_canvas | modes_editor_editor_ehr_tarzanehrui | c_line_line_2765 | coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_2778_coords | ehr_canvas | modes_editor_editor_ehr_tarzanehrui | c_line_line_2778 | coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_2801_coords | ehr_canvas | modes_editor_editor_ehr_tarzanehrui | c_line_line_2801 | coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_oval_line_1947_coords | ehr_canvas | modes_editor_editor_ehr_tarzanehrui | c_oval_line_1947 | coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_oval_line_2792_coords | ehr_canvas | modes_editor_editor_ehr_tarzanehrui | c_oval_line_2792 | coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_oval_line_2794_coords | ehr_canvas | modes_editor_editor_ehr_tarzanehrui | c_oval_line_2794 | coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_polygon_line_2808_coords | ehr_canvas | modes_editor_editor_ehr_tarzanehrui | c_polygon_line_2808 | coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_rectangle_line_1893_coords | ehr_canvas | modes_editor_editor_ehr_tarzanehrui | c_rectangle_line_1893 | coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_rectangle_line_1901_coords | ehr_canvas | modes_editor_editor_ehr_tarzanehrui | c_rectangle_line_1901 | coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_rectangle_line_1902_coords | ehr_canvas | modes_editor_editor_ehr_tarzanehrui | c_rectangle_line_1902 | coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_rectangle_line_1903_coords | ehr_canvas | modes_editor_editor_ehr_tarzanehrui | c_rectangle_line_1903 | coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_rectangle_line_1960_coords | ehr_canvas | modes_editor_editor_ehr_tarzanehrui | c_rectangle_line_1960 | coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_rectangle_line_2688_coords | ehr_canvas | modes_editor_editor_ehr_tarzanehrui | c_rectangle_line_2688 | coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_rectangle_line_2705_coords | ehr_canvas | modes_editor_editor_ehr_tarzanehrui | c_rectangle_line_2705 | coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_rectangle_line_2790_coords | ehr_canvas | modes_editor_editor_ehr_tarzanehrui | c_rectangle_line_2790 | coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_rectangle_line_2800_coords | ehr_canvas | modes_editor_editor_ehr_tarzanehrui | c_rectangle_line_2800 | coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_1911_text | ehr_canvas | modes_editor_editor_ehr_tarzanehrui | c_text_line_1911 | text |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_1920_text | ehr_canvas | modes_editor_editor_ehr_tarzanehrui | c_text_line_1920 | text |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_1953_text | ehr_canvas | modes_editor_editor_ehr_tarzanehrui | c_text_line_1953 | text |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_1954_text | ehr_canvas | modes_editor_editor_ehr_tarzanehrui | c_text_line_1954 | text |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_1981_text | ehr_canvas | modes_editor_editor_ehr_tarzanehrui | c_text_line_1981 | text |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_1982_text | ehr_canvas | modes_editor_editor_ehr_tarzanehrui | c_text_line_1982 | text |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_2720_text | ehr_canvas | modes_editor_editor_ehr_tarzanehrui | c_text_line_2720 | text |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_2727_text | ehr_canvas | modes_editor_editor_ehr_tarzanehrui | c_text_line_2727 | text |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_2736_text | ehr_canvas | modes_editor_editor_ehr_tarzanehrui | c_text_line_2736 | text |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_2809_text | ehr_canvas | modes_editor_editor_ehr_tarzanehrui | c_text_line_2809 | text |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_2816_text | ehr_canvas | modes_editor_editor_ehr_tarzanehrui | c_text_line_2816 | text |
| canvas_modes_editor_editor_ehr_tarzanehrui_canvas_image_line_712_coords | ehr_canvas | modes_editor_editor_ehr_tarzanehrui | canvas_image_line_712 | coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_canvas_rectangle_line_1244_coords | ehr_canvas | modes_editor_editor_ehr_tarzanehrui | canvas_rectangle_line_1244 | coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_canvas_window_line_1172_coords | ehr_canvas | modes_editor_editor_ehr_tarzanehrui | canvas_window_line_1172 | coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_item_text | ehr_canvas | modes_editor_editor_ehr_tarzanehrui | item | text |
| canvas_modes_editor_editor_ehr_tarzanehrui_protocol_canvas_rectangle_line_962_coords | ehr_canvas | modes_editor_editor_ehr_tarzanehrui | protocol_canvas_rectangle_line_962 | coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_protocol_canvas_rectangle_line_963_coords | ehr_canvas | modes_editor_editor_ehr_tarzanehrui | protocol_canvas_rectangle_line_963 | coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_row_window_coords | ehr_canvas | modes_editor_editor_ehr_tarzanehrui | row_window | coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_save_button_window_coords | ehr_canvas | modes_editor_editor_ehr_tarzanehrui | save_button_window | coords |
| canvas_modes_editor_editor_tarzanaxissandbox_c_line_line_826_coords | sandbox_canvas | modes_editor_editor_tarzanaxissandbox | c_line_line_826 | coords |
| canvas_modes_editor_editor_tarzanaxissandbox_c_line_line_833_coords | sandbox_canvas | modes_editor_editor_tarzanaxissandbox | c_line_line_833 | coords |
| canvas_modes_editor_editor_tarzanaxissandbox_c_line_line_852_coords | sandbox_canvas | modes_editor_editor_tarzanaxissandbox | c_line_line_852 | coords |
| canvas_modes_editor_editor_tarzanaxissandbox_c_line_line_859_coords | sandbox_canvas | modes_editor_editor_tarzanaxissandbox | c_line_line_859 | coords |
| canvas_modes_editor_editor_tarzanaxissandbox_c_line_line_871_coords | sandbox_canvas | modes_editor_editor_tarzanaxissandbox | c_line_line_871 | coords |
| canvas_modes_editor_editor_tarzanaxissandbox_c_line_line_872_coords | sandbox_canvas | modes_editor_editor_tarzanaxissandbox | c_line_line_872 | coords |
| canvas_modes_editor_editor_tarzanaxissandbox_c_line_line_886_coords | sandbox_canvas | modes_editor_editor_tarzanaxissandbox | c_line_line_886 | coords |
| canvas_modes_editor_editor_tarzanaxissandbox_c_line_line_898_coords | sandbox_canvas | modes_editor_editor_tarzanaxissandbox | c_line_line_898 | coords |
| canvas_modes_editor_editor_tarzanaxissandbox_c_line_line_900_coords | sandbox_canvas | modes_editor_editor_tarzanaxissandbox | c_line_line_900 | coords |
| canvas_modes_editor_editor_tarzanaxissandbox_c_oval_line_868_coords | sandbox_canvas | modes_editor_editor_tarzanaxissandbox | c_oval_line_868 | coords |
| canvas_modes_editor_editor_tarzanaxissandbox_c_rectangle_line_812_coords | sandbox_canvas | modes_editor_editor_tarzanaxissandbox | c_rectangle_line_812 | coords |
| canvas_modes_editor_editor_tarzanaxissandbox_c_rectangle_line_819_coords | sandbox_canvas | modes_editor_editor_tarzanaxissandbox | c_rectangle_line_819 | coords |
| canvas_modes_editor_editor_tarzanaxissandbox_c_rectangle_line_820_coords | sandbox_canvas | modes_editor_editor_tarzanaxissandbox | c_rectangle_line_820 | coords |
| canvas_modes_editor_editor_tarzanaxissandbox_c_rectangle_line_821_coords | sandbox_canvas | modes_editor_editor_tarzanaxissandbox | c_rectangle_line_821 | coords |
| canvas_modes_editor_editor_tarzanaxissandbox_c_rectangle_line_880_coords | sandbox_canvas | modes_editor_editor_tarzanaxissandbox | c_rectangle_line_880 | coords |
| canvas_modes_editor_editor_tarzanaxissandbox_c_text_line_827_text | sandbox_canvas | modes_editor_editor_tarzanaxissandbox | c_text_line_827 | text |
| canvas_modes_editor_editor_tarzanaxissandbox_c_text_line_834_text | sandbox_canvas | modes_editor_editor_tarzanaxissandbox | c_text_line_834 | text |
| canvas_modes_editor_editor_tarzanaxissandbox_c_text_line_873_text | sandbox_canvas | modes_editor_editor_tarzanaxissandbox | c_text_line_873 | text |
| canvas_modes_editor_editor_tarzanaxissandbox_c_text_line_874_text | sandbox_canvas | modes_editor_editor_tarzanaxissandbox | c_text_line_874 | text |
| canvas_modes_editor_editor_tarzanaxissandbox_c_text_line_901_text | sandbox_canvas | modes_editor_editor_tarzanaxissandbox | c_text_line_901 | text |
| canvas_modes_editor_editor_tarzanaxissandbox_c_text_line_902_text | sandbox_canvas | modes_editor_editor_tarzanaxissandbox | c_text_line_902 | text |
| canvas_modes_editor_editor_tarzanehrtakesandbox_canvas_image_line_553_coords | ehr_canvas | modes_editor_editor_tarzanehrtakesandbox | canvas_image_line_553 | coords |
| canvas_modes_editor_editor_tarzanehrtakesandbox_item_text | ehr_canvas | modes_editor_editor_tarzanehrtakesandbox | item | text |
| canvas_modes_editor_editor_tarzanehrtakesandbox_protocol_canvas_rectangle_line_1057_coords | ehr_canvas | modes_editor_editor_tarzanehrtakesandbox | protocol_canvas_rectangle_line_1057 | coords |
| canvas_modes_editor_editor_tarzanehrtakesandbox_protocol_canvas_rectangle_line_1058_coords | ehr_canvas | modes_editor_editor_tarzanehrtakesandbox | protocol_canvas_rectangle_line_1058 | coords |
| canvas_modes_editor_editor_tarzanehrtakesandbox_protocol_title_id_text | ehr_canvas | modes_editor_editor_tarzanehrtakesandbox | protocol_title_id | text |
| canvas_modes_editor_editor_tarzanehrtakesandbox_row_window_coords | ehr_canvas | modes_editor_editor_tarzanehrtakesandbox | row_window | coords |
| canvas_modes_editor_editor_tarzanehrtakesandbox_save_button_window_coords | ehr_canvas | modes_editor_editor_tarzanehrtakesandbox | save_button_window | coords |
| canvas_modes_editor_editor_tarzantakeprotocollight_canvas_image_line_860_coords | canvas_preview | modes_editor_editor_tarzantakeprotocollight | canvas_image_line_860 | coords |
| canvas_modes_editor_editor_tarzantakeprotocollight_item_text | canvas_preview | modes_editor_editor_tarzantakeprotocollight | item | text |
| canvas_modes_editor_editor_tarzantakeprotocollight_protocol_canvas_rectangle_line_1215_coords | canvas_preview | modes_editor_editor_tarzantakeprotocollight | protocol_canvas_rectangle_line_1215 | coords |
| canvas_modes_editor_editor_tarzantakeprotocollight_protocol_canvas_rectangle_line_1216_coords | canvas_preview | modes_editor_editor_tarzantakeprotocollight | protocol_canvas_rectangle_line_1216 | coords |
| canvas_modes_editor_editor_tarzantakeprotocollight_protocol_title_id_text | canvas_preview | modes_editor_editor_tarzantakeprotocollight | protocol_title_id | text |
| canvas_modes_editor_editor_tarzantakeprotocollight_row_window_coords | canvas_preview | modes_editor_editor_tarzantakeprotocollight | row_window | coords |
| canvas_modes_editor_editor_tarzantakeprotocollight_save_button_window_coords | canvas_preview | modes_editor_editor_tarzantakeprotocollight | save_button_window | coords |
| canvas_modes_editor_ehr_tarzanaxissandbox_c_line_line_827_coords | ehr_canvas | modes_editor_ehr_tarzanaxissandbox | c_line_line_827 | coords |
| canvas_modes_editor_ehr_tarzanaxissandbox_c_line_line_834_coords | ehr_canvas | modes_editor_ehr_tarzanaxissandbox | c_line_line_834 | coords |
| canvas_modes_editor_ehr_tarzanaxissandbox_c_line_line_841_coords | ehr_canvas | modes_editor_ehr_tarzanaxissandbox | c_line_line_841 | coords |
| canvas_modes_editor_ehr_tarzanaxissandbox_c_line_line_853_coords | ehr_canvas | modes_editor_ehr_tarzanaxissandbox | c_line_line_853 | coords |
| canvas_modes_editor_ehr_tarzanaxissandbox_c_line_line_854_coords | ehr_canvas | modes_editor_ehr_tarzanaxissandbox | c_line_line_854 | coords |
| canvas_modes_editor_ehr_tarzanaxissandbox_c_line_line_868_coords | ehr_canvas | modes_editor_ehr_tarzanaxissandbox | c_line_line_868 | coords |
| canvas_modes_editor_ehr_tarzanaxissandbox_c_line_line_880_coords | ehr_canvas | modes_editor_ehr_tarzanaxissandbox | c_line_line_880 | coords |
| canvas_modes_editor_ehr_tarzanaxissandbox_c_line_line_882_coords | ehr_canvas | modes_editor_ehr_tarzanaxissandbox | c_line_line_882 | coords |
| canvas_modes_editor_ehr_tarzanaxissandbox_c_oval_line_850_coords | ehr_canvas | modes_editor_ehr_tarzanaxissandbox | c_oval_line_850 | coords |
| canvas_modes_editor_ehr_tarzanaxissandbox_c_rectangle_line_813_coords | ehr_canvas | modes_editor_ehr_tarzanaxissandbox | c_rectangle_line_813 | coords |
| canvas_modes_editor_ehr_tarzanaxissandbox_c_rectangle_line_820_coords | ehr_canvas | modes_editor_ehr_tarzanaxissandbox | c_rectangle_line_820 | coords |
| canvas_modes_editor_ehr_tarzanaxissandbox_c_rectangle_line_821_coords | ehr_canvas | modes_editor_ehr_tarzanaxissandbox | c_rectangle_line_821 | coords |
| canvas_modes_editor_ehr_tarzanaxissandbox_c_rectangle_line_822_coords | ehr_canvas | modes_editor_ehr_tarzanaxissandbox | c_rectangle_line_822 | coords |
| canvas_modes_editor_ehr_tarzanaxissandbox_c_rectangle_line_862_coords | ehr_canvas | modes_editor_ehr_tarzanaxissandbox | c_rectangle_line_862 | coords |
| canvas_modes_editor_ehr_tarzanaxissandbox_c_text_line_828_text | ehr_canvas | modes_editor_ehr_tarzanaxissandbox | c_text_line_828 | text |
| canvas_modes_editor_ehr_tarzanaxissandbox_c_text_line_835_text | ehr_canvas | modes_editor_ehr_tarzanaxissandbox | c_text_line_835 | text |
| canvas_modes_editor_ehr_tarzanaxissandbox_c_text_line_855_text | ehr_canvas | modes_editor_ehr_tarzanaxissandbox | c_text_line_855 | text |
| canvas_modes_editor_ehr_tarzanaxissandbox_c_text_line_856_text | ehr_canvas | modes_editor_ehr_tarzanaxissandbox | c_text_line_856 | text |
| canvas_modes_editor_ehr_tarzanaxissandbox_c_text_line_883_text | ehr_canvas | modes_editor_ehr_tarzanaxissandbox | c_text_line_883 | text |
| canvas_modes_editor_ehr_tarzanaxissandbox_c_text_line_884_text | ehr_canvas | modes_editor_ehr_tarzanaxissandbox | c_text_line_884 | text |
| canvas_modes_editor_ehr_tarzanehrui_c_image_line_3130_coords | ehr_canvas | modes_editor_ehr_tarzanehrui | c_image_line_3130 | coords |
| canvas_modes_editor_ehr_tarzanehrui_c_line_line_1993_coords | ehr_canvas | modes_editor_ehr_tarzanehrui | c_line_line_1993 | coords |
| canvas_modes_editor_ehr_tarzanehrui_c_line_line_2002_coords | ehr_canvas | modes_editor_ehr_tarzanehrui | c_line_line_2002 | coords |
| canvas_modes_editor_ehr_tarzanehrui_c_line_line_2013_coords | ehr_canvas | modes_editor_ehr_tarzanehrui | c_line_line_2013 | coords |
| canvas_modes_editor_ehr_tarzanehrui_c_line_line_2020_coords | ehr_canvas | modes_editor_ehr_tarzanehrui | c_line_line_2020 | coords |
| canvas_modes_editor_ehr_tarzanehrui_c_line_line_2048_coords | ehr_canvas | modes_editor_ehr_tarzanehrui | c_line_line_2048 | coords |
| canvas_modes_editor_ehr_tarzanehrui_c_line_line_2049_coords | ehr_canvas | modes_editor_ehr_tarzanehrui | c_line_line_2049 | coords |
| canvas_modes_editor_ehr_tarzanehrui_c_line_line_2068_coords | ehr_canvas | modes_editor_ehr_tarzanehrui | c_line_line_2068 | coords |
| canvas_modes_editor_ehr_tarzanehrui_c_line_line_2080_coords | ehr_canvas | modes_editor_ehr_tarzanehrui | c_line_line_2080 | coords |
| canvas_modes_editor_ehr_tarzanehrui_c_line_line_2082_coords | ehr_canvas | modes_editor_ehr_tarzanehrui | c_line_line_2082 | coords |
| canvas_modes_editor_ehr_tarzanehrui_c_line_line_3081_coords | ehr_canvas | modes_editor_ehr_tarzanehrui | c_line_line_3081 | coords |
| canvas_modes_editor_ehr_tarzanehrui_c_line_line_3102_coords | ehr_canvas | modes_editor_ehr_tarzanehrui | c_line_line_3102 | coords |
| canvas_modes_editor_ehr_tarzanehrui_c_line_line_3105_coords | ehr_canvas | modes_editor_ehr_tarzanehrui | c_line_line_3105 | coords |
| canvas_modes_editor_ehr_tarzanehrui_c_line_line_3145_coords | ehr_canvas | modes_editor_ehr_tarzanehrui | c_line_line_3145 | coords |
| canvas_modes_editor_ehr_tarzanehrui_c_line_line_3153_coords | ehr_canvas | modes_editor_ehr_tarzanehrui | c_line_line_3153 | coords |
| canvas_modes_editor_ehr_tarzanehrui_c_line_line_3161_coords | ehr_canvas | modes_editor_ehr_tarzanehrui | c_line_line_3161 | coords |
| canvas_modes_editor_ehr_tarzanehrui_c_line_line_3176_coords | ehr_canvas | modes_editor_ehr_tarzanehrui | c_line_line_3176 | coords |
| canvas_modes_editor_ehr_tarzanehrui_c_line_line_3217_coords | ehr_canvas | modes_editor_ehr_tarzanehrui | c_line_line_3217 | coords |
| canvas_modes_editor_ehr_tarzanehrui_c_line_line_3231_coords | ehr_canvas | modes_editor_ehr_tarzanehrui | c_line_line_3231 | coords |
| canvas_modes_editor_ehr_tarzanehrui_c_oval_line_2044_coords | ehr_canvas | modes_editor_ehr_tarzanehrui | c_oval_line_2044 | coords |
| canvas_modes_editor_ehr_tarzanehrui_c_oval_line_3194_coords | ehr_canvas | modes_editor_ehr_tarzanehrui | c_oval_line_3194 | coords |
| canvas_modes_editor_ehr_tarzanehrui_c_oval_line_3210_coords | ehr_canvas | modes_editor_ehr_tarzanehrui | c_oval_line_3210 | coords |
| canvas_modes_editor_ehr_tarzanehrui_c_polygon_line_3226_coords | ehr_canvas | modes_editor_ehr_tarzanehrui | c_polygon_line_3226 | coords |
| canvas_modes_editor_ehr_tarzanehrui_c_rectangle_line_1976_coords | ehr_canvas | modes_editor_ehr_tarzanehrui | c_rectangle_line_1976 | coords |
| canvas_modes_editor_ehr_tarzanehrui_c_rectangle_line_1984_coords | ehr_canvas | modes_editor_ehr_tarzanehrui | c_rectangle_line_1984 | coords |
| canvas_modes_editor_ehr_tarzanehrui_c_rectangle_line_1985_coords | ehr_canvas | modes_editor_ehr_tarzanehrui | c_rectangle_line_1985 | coords |
| canvas_modes_editor_ehr_tarzanehrui_c_rectangle_line_1986_coords | ehr_canvas | modes_editor_ehr_tarzanehrui | c_rectangle_line_1986 | coords |
| canvas_modes_editor_ehr_tarzanehrui_c_rectangle_line_2062_coords | ehr_canvas | modes_editor_ehr_tarzanehrui | c_rectangle_line_2062 | coords |
| canvas_modes_editor_ehr_tarzanehrui_c_rectangle_line_3072_coords | ehr_canvas | modes_editor_ehr_tarzanehrui | c_rectangle_line_3072 | coords |
| canvas_modes_editor_ehr_tarzanehrui_c_rectangle_line_3100_coords | ehr_canvas | modes_editor_ehr_tarzanehrui | c_rectangle_line_3100 | coords |
| canvas_modes_editor_ehr_tarzanehrui_c_rectangle_line_3192_coords | ehr_canvas | modes_editor_ehr_tarzanehrui | c_rectangle_line_3192 | coords |
| canvas_modes_editor_ehr_tarzanehrui_c_rectangle_line_3216_coords | ehr_canvas | modes_editor_ehr_tarzanehrui | c_rectangle_line_3216 | coords |
| canvas_modes_editor_ehr_tarzanehrui_c_text_line_1994_text | ehr_canvas | modes_editor_ehr_tarzanehrui | c_text_line_1994 | text |
| canvas_modes_editor_ehr_tarzanehrui_c_text_line_2003_text | ehr_canvas | modes_editor_ehr_tarzanehrui | c_text_line_2003 | text |
| canvas_modes_editor_ehr_tarzanehrui_c_text_line_2050_text | ehr_canvas | modes_editor_ehr_tarzanehrui | c_text_line_2050 | text |
| canvas_modes_editor_ehr_tarzanehrui_c_text_line_2051_text | ehr_canvas | modes_editor_ehr_tarzanehrui | c_text_line_2051 | text |
| canvas_modes_editor_ehr_tarzanehrui_c_text_line_2083_text | ehr_canvas | modes_editor_ehr_tarzanehrui | c_text_line_2083 | text |
| canvas_modes_editor_ehr_tarzanehrui_c_text_line_2084_text | ehr_canvas | modes_editor_ehr_tarzanehrui | c_text_line_2084 | text |
| canvas_modes_editor_ehr_tarzanehrui_c_text_line_3115_text | ehr_canvas | modes_editor_ehr_tarzanehrui | c_text_line_3115 | text |
| canvas_modes_editor_ehr_tarzanehrui_c_text_line_3122_text | ehr_canvas | modes_editor_ehr_tarzanehrui | c_text_line_3122 | text |
| canvas_modes_editor_ehr_tarzanehrui_c_text_line_3132_text | ehr_canvas | modes_editor_ehr_tarzanehrui | c_text_line_3132 | text |
| canvas_modes_editor_ehr_tarzanehrui_c_text_line_3228_text | ehr_canvas | modes_editor_ehr_tarzanehrui | c_text_line_3228 | text |
| canvas_modes_editor_ehr_tarzanehrui_c_text_line_3239_text | ehr_canvas | modes_editor_ehr_tarzanehrui | c_text_line_3239 | text |
| canvas_modes_editor_ehr_tarzanehrui_canvas_image_line_760_coords | ehr_canvas | modes_editor_ehr_tarzanehrui | canvas_image_line_760 | coords |
| canvas_modes_editor_ehr_tarzanehrui_canvas_rectangle_line_1300_coords | ehr_canvas | modes_editor_ehr_tarzanehrui | canvas_rectangle_line_1300 | coords |
| canvas_modes_editor_ehr_tarzanehrui_canvas_window_line_1226_coords | ehr_canvas | modes_editor_ehr_tarzanehrui | canvas_window_line_1226 | coords |
| canvas_modes_editor_ehr_tarzanehrui_item_text | ehr_canvas | modes_editor_ehr_tarzanehrui | item | text |
| canvas_modes_editor_ehr_tarzanehrui_protocol_canvas_rectangle_line_1010_coords | ehr_canvas | modes_editor_ehr_tarzanehrui | protocol_canvas_rectangle_line_1010 | coords |
| canvas_modes_editor_ehr_tarzanehrui_protocol_canvas_rectangle_line_1011_coords | ehr_canvas | modes_editor_ehr_tarzanehrui | protocol_canvas_rectangle_line_1011 | coords |
| canvas_modes_editor_ehr_tarzanehrui_row_window_coords | ehr_canvas | modes_editor_ehr_tarzanehrui | row_window | coords |
| canvas_modes_editor_ehr_tarzanehrui_save_button_window_coords | ehr_canvas | modes_editor_ehr_tarzanehrui | save_button_window | coords |
| canvas_modes_editor_par_tarzannextionpreview_edit_window_coords | canvas_preview | modes_editor_par_tarzannextionpreview | _edit_window | coords |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_image_line_591_coords | canvas_preview | modes_editor_par_tarzannextionpreview | screen_canvas_image_line_591 | coords |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_image_line_623_coords | canvas_preview | modes_editor_par_tarzannextionpreview | screen_canvas_image_line_623 | coords |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_image_line_640_coords | canvas_preview | modes_editor_par_tarzannextionpreview | screen_canvas_image_line_640 | coords |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_image_line_692_coords | canvas_preview | modes_editor_par_tarzannextionpreview | screen_canvas_image_line_692 | coords |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_image_line_718_coords | canvas_preview | modes_editor_par_tarzannextionpreview | screen_canvas_image_line_718 | coords |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_line_line_415_coords | canvas_preview | modes_editor_par_tarzannextionpreview | screen_canvas_line_line_415 | coords |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_line_line_432_coords | canvas_preview | modes_editor_par_tarzannextionpreview | screen_canvas_line_line_432 | coords |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_line_line_445_coords | canvas_preview | modes_editor_par_tarzannextionpreview | screen_canvas_line_line_445 | coords |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_line_line_737_coords | canvas_preview | modes_editor_par_tarzannextionpreview | screen_canvas_line_line_737 | coords |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_line_line_738_coords | canvas_preview | modes_editor_par_tarzannextionpreview | screen_canvas_line_line_738 | coords |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_line_line_818_coords | canvas_preview | modes_editor_par_tarzannextionpreview | screen_canvas_line_line_818 | coords |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_oval_line_740_coords | canvas_preview | modes_editor_par_tarzannextionpreview | screen_canvas_oval_line_740 | coords |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_394_coords | canvas_preview | modes_editor_par_tarzannextionpreview | screen_canvas_rectangle_line_394 | coords |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_512_coords | canvas_preview | modes_editor_par_tarzannextionpreview | screen_canvas_rectangle_line_512 | coords |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_527_coords | canvas_preview | modes_editor_par_tarzannextionpreview | screen_canvas_rectangle_line_527 | coords |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_593_coords | canvas_preview | modes_editor_par_tarzannextionpreview | screen_canvas_rectangle_line_593 | coords |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_625_coords | canvas_preview | modes_editor_par_tarzannextionpreview | screen_canvas_rectangle_line_625 | coords |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_642_coords | canvas_preview | modes_editor_par_tarzannextionpreview | screen_canvas_rectangle_line_642 | coords |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_785_coords | canvas_preview | modes_editor_par_tarzannextionpreview | screen_canvas_rectangle_line_785 | coords |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_787_coords | canvas_preview | modes_editor_par_tarzannextionpreview | screen_canvas_rectangle_line_787 | coords |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_790_coords | canvas_preview | modes_editor_par_tarzannextionpreview | screen_canvas_rectangle_line_790 | coords |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_797_coords | canvas_preview | modes_editor_par_tarzannextionpreview | screen_canvas_rectangle_line_797 | coords |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_815_coords | canvas_preview | modes_editor_par_tarzannextionpreview | screen_canvas_rectangle_line_815 | coords |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_400_text | canvas_preview | modes_editor_par_tarzannextionpreview | screen_canvas_text_line_400 | text |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_414_text | canvas_preview | modes_editor_par_tarzannextionpreview | screen_canvas_text_line_414 | text |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_421_text | canvas_preview | modes_editor_par_tarzannextionpreview | screen_canvas_text_line_421 | text |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_425_text | canvas_preview | modes_editor_par_tarzannextionpreview | screen_canvas_text_line_425 | text |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_466_text | canvas_preview | modes_editor_par_tarzannextionpreview | screen_canvas_text_line_466 | text |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_483_text | canvas_preview | modes_editor_par_tarzannextionpreview | screen_canvas_text_line_483 | text |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_518_text | canvas_preview | modes_editor_par_tarzannextionpreview | screen_canvas_text_line_518 | text |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_529_text | canvas_preview | modes_editor_par_tarzannextionpreview | screen_canvas_text_line_529 | text |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_594_text | canvas_preview | modes_editor_par_tarzannextionpreview | screen_canvas_text_line_594 | text |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_603_text | canvas_preview | modes_editor_par_tarzannextionpreview | screen_canvas_text_line_603 | text |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_626_text | canvas_preview | modes_editor_par_tarzannextionpreview | screen_canvas_text_line_626 | text |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_643_text | canvas_preview | modes_editor_par_tarzannextionpreview | screen_canvas_text_line_643 | text |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_791_text | canvas_preview | modes_editor_par_tarzannextionpreview | screen_canvas_text_line_791 | text |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_798_text | canvas_preview | modes_editor_par_tarzannextionpreview | screen_canvas_text_line_798 | text |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_799_text | canvas_preview | modes_editor_par_tarzannextionpreview | screen_canvas_text_line_799 | text |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_816_text | canvas_preview | modes_editor_par_tarzannextionpreview | screen_canvas_text_line_816 | text |
| canvas_modes_editor_par_tarzanparapp_canvas_oval_line_1309_coords | layout_canvas | modes_editor_par_tarzanparapp | canvas_oval_line_1309 | coords |
| canvas_modes_editor_par_tarzanparapp_canvas_oval_line_1402_coords | layout_canvas | modes_editor_par_tarzanparapp | canvas_oval_line_1402 | coords |
| canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1286_coords | layout_canvas | modes_editor_par_tarzanparapp | canvas_rectangle_line_1286 | coords |
| canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1303_coords | layout_canvas | modes_editor_par_tarzanparapp | canvas_rectangle_line_1303 | coords |
| canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1314_coords | layout_canvas | modes_editor_par_tarzanparapp | canvas_rectangle_line_1314 | coords |
| canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1315_coords | layout_canvas | modes_editor_par_tarzanparapp | canvas_rectangle_line_1315 | coords |
| canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1316_coords | layout_canvas | modes_editor_par_tarzanparapp | canvas_rectangle_line_1316 | coords |
| canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1329_coords | layout_canvas | modes_editor_par_tarzanparapp | canvas_rectangle_line_1329 | coords |
| canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1387_coords | layout_canvas | modes_editor_par_tarzanparapp | canvas_rectangle_line_1387 | coords |
| canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1414_coords | layout_canvas | modes_editor_par_tarzanparapp | canvas_rectangle_line_1414 | coords |
| canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1415_coords | layout_canvas | modes_editor_par_tarzanparapp | canvas_rectangle_line_1415 | coords |
| canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1416_coords | layout_canvas | modes_editor_par_tarzanparapp | canvas_rectangle_line_1416 | coords |
| canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1431_coords | layout_canvas | modes_editor_par_tarzanparapp | canvas_rectangle_line_1431 | coords |
| canvas_modes_editor_par_tarzanparapp_canvas_text_line_1310_text | layout_canvas | modes_editor_par_tarzanparapp | canvas_text_line_1310 | text |
| canvas_modes_editor_par_tarzanparapp_canvas_text_line_1434_text | layout_canvas | modes_editor_par_tarzanparapp | canvas_text_line_1434 | text |
| canvas_modes_editor_par_tarzanparapp_canvas_text_line_1451_text | layout_canvas | modes_editor_par_tarzanparapp | canvas_text_line_1451 | text |
| canvas_modes_editor_par_tarzanparapp_canvas_text_line_1455_text | layout_canvas | modes_editor_par_tarzanparapp | canvas_text_line_1455 | text |
| canvas_modes_editor_par_tarzanparapp_led_oval_line_485_coords | layout_canvas | modes_editor_par_tarzanparapp | led_oval_line_485 | coords |
| canvas_modes_editor_par_tarzanparapp_panel_canvas_window_line_1076_coords | layout_canvas | modes_editor_par_tarzanparapp | panel_canvas_window_line_1076 | coords |
| canvas_modes_editor_par_tarzanparapp_text_id_text | layout_canvas | modes_editor_par_tarzanparapp | text_id | text |
| canvas_modes_editor_par_tarzanparpanels_can_image_line_1306_coords | canvas_preview | modes_editor_par_tarzanparpanels | can_image_line_1306 | coords |
| canvas_modes_editor_par_tarzanparpanels_can_line_line_1298_coords | canvas_preview | modes_editor_par_tarzanparpanels | can_line_line_1298 | coords |
| canvas_modes_editor_par_tarzanparpanels_can_line_line_1299_coords | canvas_preview | modes_editor_par_tarzanparpanels | can_line_line_1299 | coords |
| canvas_modes_editor_par_tarzanparpanels_can_line_line_1304_coords | canvas_preview | modes_editor_par_tarzanparpanels | can_line_line_1304 | coords |
| canvas_modes_editor_par_tarzanparpanels_can_line_line_1311_coords | canvas_preview | modes_editor_par_tarzanparpanels | can_line_line_1311 | coords |
| canvas_modes_editor_par_tarzanparpanels_can_line_line_1326_coords | canvas_preview | modes_editor_par_tarzanparpanels | can_line_line_1326 | coords |
| canvas_modes_editor_par_tarzanparpanels_can_line_line_1327_coords | canvas_preview | modes_editor_par_tarzanparpanels | can_line_line_1327 | coords |
| canvas_modes_editor_par_tarzanparpanels_can_line_line_510_coords | canvas_preview | modes_editor_par_tarzanparpanels | can_line_line_510 | coords |
| canvas_modes_editor_par_tarzanparpanels_can_line_line_664_coords | canvas_preview | modes_editor_par_tarzanparpanels | can_line_line_664 | coords |
| canvas_modes_editor_par_tarzanparpanels_can_line_line_665_coords | canvas_preview | modes_editor_par_tarzanparpanels | can_line_line_665 | coords |
| canvas_modes_editor_par_tarzanparpanels_can_oval_line_509_coords | canvas_preview | modes_editor_par_tarzanparpanels | can_oval_line_509 | coords |
| canvas_modes_editor_par_tarzanparpanels_can_oval_line_511_coords | canvas_preview | modes_editor_par_tarzanparpanels | can_oval_line_511 | coords |
| canvas_modes_editor_par_tarzanparpanels_can_oval_line_656_coords | canvas_preview | modes_editor_par_tarzanparpanels | can_oval_line_656 | coords |
| canvas_modes_editor_par_tarzanparpanels_can_oval_line_920_coords | canvas_preview | modes_editor_par_tarzanparpanels | can_oval_line_920 | coords |
| canvas_modes_editor_par_tarzanparpanels_can_polygon_line_921_coords | canvas_preview | modes_editor_par_tarzanparpanels | can_polygon_line_921 | coords |
| canvas_modes_editor_par_tarzanparpanels_can_rectangle_line_899_coords | canvas_preview | modes_editor_par_tarzanparpanels | can_rectangle_line_899 | coords |
| canvas_modes_editor_par_tarzanparpanels_can_rectangle_line_901_coords | canvas_preview | modes_editor_par_tarzanparpanels | can_rectangle_line_901 | coords |
| canvas_modes_editor_par_tarzanparpanels_can_text_line_1307_text | canvas_preview | modes_editor_par_tarzanparpanels | can_text_line_1307 | text |
| canvas_modes_editor_par_tarzanparpanels_can_text_line_1309_text | canvas_preview | modes_editor_par_tarzanparpanels | can_text_line_1309 | text |
| canvas_modes_editor_par_tarzanparpanels_can_text_line_1310_text | canvas_preview | modes_editor_par_tarzanparpanels | can_text_line_1310 | text |
| canvas_modes_editor_par_tarzanparpanels_can_text_line_1329_text | canvas_preview | modes_editor_par_tarzanparpanels | can_text_line_1329 | text |
| canvas_modes_editor_par_tarzanparpanels_can_text_line_1331_text | canvas_preview | modes_editor_par_tarzanparpanels | can_text_line_1331 | text |
| canvas_modes_editor_par_tarzanparpanels_canvas_line_line_825_coords | canvas_preview | modes_editor_par_tarzanparpanels | canvas_line_line_825 | coords |
| canvas_modes_editor_par_tarzanparpanels_canvas_line_line_826_coords | canvas_preview | modes_editor_par_tarzanparpanels | canvas_line_line_826 | coords |
| canvas_modes_editor_par_tarzanparpanels_canvas_oval_line_1575_coords | canvas_preview | modes_editor_par_tarzanparpanels | canvas_oval_line_1575 | coords |
| canvas_modes_editor_par_tarzanparpanels_canvas_oval_line_830_coords | canvas_preview | modes_editor_par_tarzanparpanels | canvas_oval_line_830 | coords |
| canvas_modes_editor_par_tarzanparpanels_canvas_polygon_line_828_coords | canvas_preview | modes_editor_par_tarzanparpanels | canvas_polygon_line_828 | coords |
| canvas_modes_editor_par_tarzanparpanels_canvas_rectangle_line_1449_coords | canvas_preview | modes_editor_par_tarzanparpanels | canvas_rectangle_line_1449 | coords |
| canvas_modes_editor_par_tarzanparpanels_canvas_rectangle_line_1450_coords | canvas_preview | modes_editor_par_tarzanparpanels | canvas_rectangle_line_1450 | coords |
| canvas_modes_editor_par_tarzanparpanels_canvas_rectangle_line_1451_coords | canvas_preview | modes_editor_par_tarzanparpanels | canvas_rectangle_line_1451 | coords |
| canvas_modes_editor_par_tarzanparpanels_old_c_line_line_3118_coords | canvas_preview | modes_editor_par_tarzanparpanels_old | c_line_line_3118 | coords |
| canvas_modes_editor_par_tarzanparpanels_old_c_line_line_3119_coords | canvas_preview | modes_editor_par_tarzanparpanels_old | c_line_line_3119 | coords |
| canvas_modes_editor_par_tarzanparpanels_old_c_oval_line_1979_coords | canvas_preview | modes_editor_par_tarzanparpanels_old | c_oval_line_1979 | coords |
| canvas_modes_editor_par_tarzanparpanels_old_c_oval_line_1980_coords | canvas_preview | modes_editor_par_tarzanparpanels_old | c_oval_line_1980 | coords |
| canvas_modes_editor_par_tarzanparpanels_old_c_oval_line_2212_coords | canvas_preview | modes_editor_par_tarzanparpanels_old | c_oval_line_2212 | coords |
| canvas_modes_editor_par_tarzanparpanels_old_c_oval_line_3111_coords | canvas_preview | modes_editor_par_tarzanparpanels_old | c_oval_line_3111 | coords |
| canvas_modes_editor_par_tarzanparpanels_old_c_oval_line_344_coords | canvas_preview | modes_editor_par_tarzanparpanels_old | c_oval_line_344 | coords |
| canvas_modes_editor_par_tarzanparpanels_old_c_polygon_line_2213_coords | canvas_preview | modes_editor_par_tarzanparpanels_old | c_polygon_line_2213 | coords |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_image_line_1549_coords | canvas_preview | modes_editor_par_tarzanparpanels_old | canvas_image_line_1549 | coords |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_1538_coords | canvas_preview | modes_editor_par_tarzanparpanels_old | canvas_line_line_1538 | coords |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_1539_coords | canvas_preview | modes_editor_par_tarzanparpanels_old | canvas_line_line_1539 | coords |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_1545_coords | canvas_preview | modes_editor_par_tarzanparpanels_old | canvas_line_line_1545 | coords |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_1563_coords | canvas_preview | modes_editor_par_tarzanparpanels_old | canvas_line_line_1563 | coords |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_1581_coords | canvas_preview | modes_editor_par_tarzanparpanels_old | canvas_line_line_1581 | coords |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_1582_coords | canvas_preview | modes_editor_par_tarzanparpanels_old | canvas_line_line_1582 | coords |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_1784_coords | canvas_preview | modes_editor_par_tarzanparpanels_old | canvas_line_line_1784 | coords |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_1785_coords | canvas_preview | modes_editor_par_tarzanparpanels_old | canvas_line_line_1785 | coords |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_2481_coords | canvas_preview | modes_editor_par_tarzanparpanels_old | canvas_line_line_2481 | coords |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_767_coords | canvas_preview | modes_editor_par_tarzanparpanels_old | canvas_line_line_767 | coords |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_780_coords | canvas_preview | modes_editor_par_tarzanparpanels_old | canvas_line_line_780 | coords |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_781_coords | canvas_preview | modes_editor_par_tarzanparpanels_old | canvas_line_line_781 | coords |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_784_coords | canvas_preview | modes_editor_par_tarzanparpanels_old | canvas_line_line_784 | coords |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_oval_line_1216_coords | canvas_preview | modes_editor_par_tarzanparpanels_old | canvas_oval_line_1216 | coords |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_oval_line_1796_coords | canvas_preview | modes_editor_par_tarzanparpanels_old | canvas_oval_line_1796 | coords |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_oval_line_2480_coords | canvas_preview | modes_editor_par_tarzanparpanels_old | canvas_oval_line_2480 | coords |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_oval_line_2482_coords | canvas_preview | modes_editor_par_tarzanparpanels_old | canvas_oval_line_2482 | coords |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_polygon_line_1786_coords | canvas_preview | modes_editor_par_tarzanparpanels_old | canvas_polygon_line_1786 | coords |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_rectangle_line_1113_coords | canvas_preview | modes_editor_par_tarzanparpanels_old | canvas_rectangle_line_1113 | coords |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_rectangle_line_1114_coords | canvas_preview | modes_editor_par_tarzanparpanels_old | canvas_rectangle_line_1114 | coords |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_rectangle_line_1116_coords | canvas_preview | modes_editor_par_tarzanparpanels_old | canvas_rectangle_line_1116 | coords |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_rectangle_line_1117_coords | canvas_preview | modes_editor_par_tarzanparpanels_old | canvas_rectangle_line_1117 | coords |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_rectangle_line_1313_coords | canvas_preview | modes_editor_par_tarzanparpanels_old | canvas_rectangle_line_1313 | coords |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_rectangle_line_1314_coords | canvas_preview | modes_editor_par_tarzanparpanels_old | canvas_rectangle_line_1314 | coords |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_rectangle_line_1315_coords | canvas_preview | modes_editor_par_tarzanparpanels_old | canvas_rectangle_line_1315 | coords |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_text_line_1551_text | canvas_preview | modes_editor_par_tarzanparpanels_old | canvas_text_line_1551 | text |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_text_line_1554_text | canvas_preview | modes_editor_par_tarzanparpanels_old | canvas_text_line_1554 | text |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_text_line_1555_text | canvas_preview | modes_editor_par_tarzanparpanels_old | canvas_text_line_1555 | text |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_text_line_1586_text | canvas_preview | modes_editor_par_tarzanparpanels_old | canvas_text_line_1586 | text |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_text_line_766_text | canvas_preview | modes_editor_par_tarzanparpanels_old | canvas_text_line_766 | text |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_text_line_785_text | canvas_preview | modes_editor_par_tarzanparpanels_old | canvas_text_line_785 | text |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_window_line_119_coords | canvas_preview | modes_editor_par_tarzanparpanels_old | canvas_window_line_119 | coords |
| canvas_modes_editor_par_tarzanparpanels_old_dot_oval_line_378_coords | canvas_preview | modes_editor_par_tarzanparpanels_old | dot_oval_line_378 | coords |
| canvas_modes_editor_par_tarzanparpanels_old_led_oval_line_1049_coords | canvas_preview | modes_editor_par_tarzanparpanels_old | led_oval_line_1049 | coords |
| canvas_modes_editor_par_tarzanparpanels_old_led_oval_line_1050_coords | canvas_preview | modes_editor_par_tarzanparpanels_old | led_oval_line_1050 | coords |
| canvas_modes_editor_par_tarzanparpanels_old_rect_coords | canvas_preview | modes_editor_par_tarzanparpanels_old | rect | coords |
| canvas_modes_editor_par_tarzanparpanels_old_self_rectangle_line_1346_coords | canvas_preview | modes_editor_par_tarzanparpanels_old | self_rectangle_line_1346 | coords |
| canvas_modes_editor_par_tarzanparpanels_old_self_rectangle_line_1347_coords | canvas_preview | modes_editor_par_tarzanparpanels_old | self_rectangle_line_1347 | coords |
| canvas_modes_editor_par_tarzanparpanels_old_window_id_coords | canvas_preview | modes_editor_par_tarzanparpanels_old | window_id | coords |
| canvas_modes_editor_par_tarzanparpanels_self_rectangle_line_185_coords | canvas_preview | modes_editor_par_tarzanparpanels | self_rectangle_line_185 | coords |
| canvas_modes_editor_par_tarzanparpanels_window_id_coords | canvas_preview | modes_editor_par_tarzanparpanels | window_id | coords |
| canvas_modes_editor_par_tarzanparwidgets_c_line_line_304_coords | canvas_preview | modes_editor_par_tarzanparwidgets | c_line_line_304 | coords |
| canvas_modes_editor_par_tarzanparwidgets_c_oval_line_299_coords | canvas_preview | modes_editor_par_tarzanparwidgets | c_oval_line_299 | coords |
| canvas_modes_editor_par_tarzanparwidgets_c_oval_line_300_coords | canvas_preview | modes_editor_par_tarzanparwidgets | c_oval_line_300 | coords |
| canvas_modes_editor_par_tarzanparwidgets_c_oval_line_305_coords | canvas_preview | modes_editor_par_tarzanparwidgets | c_oval_line_305 | coords |
| canvas_modes_editor_par_tarzanparwidgets_self_oval_line_59_coords | canvas_preview | modes_editor_par_tarzanparwidgets | self_oval_line_59 | coords |
| canvas_modes_editor_par_tarzanparwidgets_self_oval_line_60_coords | canvas_preview | modes_editor_par_tarzanparwidgets | self_oval_line_60 | coords |
| canvas_modes_editor_par_tarzanparwidgets_self_oval_line_64_coords | canvas_preview | modes_editor_par_tarzanparwidgets | self_oval_line_64 | coords |
| canvas_modes_editor_par_tarzanparwidgets_self_oval_line_65_coords | canvas_preview | modes_editor_par_tarzanparwidgets | self_oval_line_65 | coords |
| canvas_modes_editor_par_tarzanparwidgets_self_rectangle_line_90_coords | canvas_preview | modes_editor_par_tarzanparwidgets | self_rectangle_line_90 | coords |
| canvas_modes_editor_tarzanaxissandbox_c_line_line_826_coords | sandbox_canvas | modes_editor_tarzanaxissandbox | c_line_line_826 | coords |
| canvas_modes_editor_tarzanaxissandbox_c_line_line_833_coords | sandbox_canvas | modes_editor_tarzanaxissandbox | c_line_line_833 | coords |
| canvas_modes_editor_tarzanaxissandbox_c_line_line_852_coords | sandbox_canvas | modes_editor_tarzanaxissandbox | c_line_line_852 | coords |
| canvas_modes_editor_tarzanaxissandbox_c_line_line_859_coords | sandbox_canvas | modes_editor_tarzanaxissandbox | c_line_line_859 | coords |
| canvas_modes_editor_tarzanaxissandbox_c_line_line_871_coords | sandbox_canvas | modes_editor_tarzanaxissandbox | c_line_line_871 | coords |
| canvas_modes_editor_tarzanaxissandbox_c_line_line_872_coords | sandbox_canvas | modes_editor_tarzanaxissandbox | c_line_line_872 | coords |
| canvas_modes_editor_tarzanaxissandbox_c_line_line_886_coords | sandbox_canvas | modes_editor_tarzanaxissandbox | c_line_line_886 | coords |
| canvas_modes_editor_tarzanaxissandbox_c_line_line_898_coords | sandbox_canvas | modes_editor_tarzanaxissandbox | c_line_line_898 | coords |
| canvas_modes_editor_tarzanaxissandbox_c_line_line_900_coords | sandbox_canvas | modes_editor_tarzanaxissandbox | c_line_line_900 | coords |
| canvas_modes_editor_tarzanaxissandbox_c_oval_line_868_coords | sandbox_canvas | modes_editor_tarzanaxissandbox | c_oval_line_868 | coords |
| canvas_modes_editor_tarzanaxissandbox_c_rectangle_line_812_coords | sandbox_canvas | modes_editor_tarzanaxissandbox | c_rectangle_line_812 | coords |
| canvas_modes_editor_tarzanaxissandbox_c_rectangle_line_819_coords | sandbox_canvas | modes_editor_tarzanaxissandbox | c_rectangle_line_819 | coords |
| canvas_modes_editor_tarzanaxissandbox_c_rectangle_line_820_coords | sandbox_canvas | modes_editor_tarzanaxissandbox | c_rectangle_line_820 | coords |
| canvas_modes_editor_tarzanaxissandbox_c_rectangle_line_821_coords | sandbox_canvas | modes_editor_tarzanaxissandbox | c_rectangle_line_821 | coords |
| canvas_modes_editor_tarzanaxissandbox_c_rectangle_line_880_coords | sandbox_canvas | modes_editor_tarzanaxissandbox | c_rectangle_line_880 | coords |
| canvas_modes_editor_tarzanaxissandbox_c_text_line_827_text | sandbox_canvas | modes_editor_tarzanaxissandbox | c_text_line_827 | text |
| canvas_modes_editor_tarzanaxissandbox_c_text_line_834_text | sandbox_canvas | modes_editor_tarzanaxissandbox | c_text_line_834 | text |
| canvas_modes_editor_tarzanaxissandbox_c_text_line_873_text | sandbox_canvas | modes_editor_tarzanaxissandbox | c_text_line_873 | text |
| canvas_modes_editor_tarzanaxissandbox_c_text_line_874_text | sandbox_canvas | modes_editor_tarzanaxissandbox | c_text_line_874 | text |
| canvas_modes_editor_tarzanaxissandbox_c_text_line_901_text | sandbox_canvas | modes_editor_tarzanaxissandbox | c_text_line_901 | text |
| canvas_modes_editor_tarzanaxissandbox_c_text_line_902_text | sandbox_canvas | modes_editor_tarzanaxissandbox | c_text_line_902 | text |
| canvas_modes_editor_tarzanehrtakesandbox_canvas_image_line_553_coords | ehr_canvas | modes_editor_tarzanehrtakesandbox | canvas_image_line_553 | coords |
| canvas_modes_editor_tarzanehrtakesandbox_item_text | ehr_canvas | modes_editor_tarzanehrtakesandbox | item | text |
| canvas_modes_editor_tarzanehrtakesandbox_protocol_canvas_rectangle_line_1057_coords | ehr_canvas | modes_editor_tarzanehrtakesandbox | protocol_canvas_rectangle_line_1057 | coords |
| canvas_modes_editor_tarzanehrtakesandbox_protocol_canvas_rectangle_line_1058_coords | ehr_canvas | modes_editor_tarzanehrtakesandbox | protocol_canvas_rectangle_line_1058 | coords |
| canvas_modes_editor_tarzanehrtakesandbox_protocol_title_id_text | ehr_canvas | modes_editor_tarzanehrtakesandbox | protocol_title_id | text |
| canvas_modes_editor_tarzanehrtakesandbox_row_window_coords | ehr_canvas | modes_editor_tarzanehrtakesandbox | row_window | coords |
| canvas_modes_editor_tarzanehrtakesandbox_save_button_window_coords | ehr_canvas | modes_editor_tarzanehrtakesandbox | save_button_window | coords |
| canvas_modes_editor_tarzankhr_c_image_line_1518_coords | khr_canvas | modes_editor_tarzankhr | c_image_line_1518 | coords |
| canvas_modes_editor_tarzankhr_c_image_line_1533_coords | khr_canvas | modes_editor_tarzankhr | c_image_line_1533 | coords |
| canvas_modes_editor_tarzankhr_c_image_line_623_coords | khr_canvas | modes_editor_tarzankhr | c_image_line_623 | coords |
| canvas_modes_editor_tarzankhr_c_line_line_1545_coords | khr_canvas | modes_editor_tarzankhr | c_line_line_1545 | coords |
| canvas_modes_editor_tarzankhr_c_line_line_1546_coords | khr_canvas | modes_editor_tarzankhr | c_line_line_1546 | coords |
| canvas_modes_editor_tarzankhr_c_line_line_1555_coords | khr_canvas | modes_editor_tarzankhr | c_line_line_1555 | coords |
| canvas_modes_editor_tarzankhr_c_line_line_1570_coords | khr_canvas | modes_editor_tarzankhr | c_line_line_1570 | coords |
| canvas_modes_editor_tarzankhr_c_line_line_1571_coords | khr_canvas | modes_editor_tarzankhr | c_line_line_1571 | coords |
| canvas_modes_editor_tarzankhr_c_line_line_1593_coords | khr_canvas | modes_editor_tarzankhr | c_line_line_1593 | coords |
| canvas_modes_editor_tarzankhr_c_line_line_1597_coords | khr_canvas | modes_editor_tarzankhr | c_line_line_1597 | coords |
| canvas_modes_editor_tarzankhr_c_oval_line_1589_coords | khr_canvas | modes_editor_tarzankhr | c_oval_line_1589 | coords |
| canvas_modes_editor_tarzankhr_c_oval_line_1590_coords | khr_canvas | modes_editor_tarzankhr | c_oval_line_1590 | coords |
| canvas_modes_editor_tarzankhr_c_polygon_line_1553_coords | khr_canvas | modes_editor_tarzankhr | c_polygon_line_1553 | coords |
| canvas_modes_editor_tarzankhr_c_polygon_line_1602_coords | khr_canvas | modes_editor_tarzankhr | c_polygon_line_1602 | coords |
| canvas_modes_editor_tarzankhr_c_rectangle_line_1548_coords | khr_canvas | modes_editor_tarzankhr | c_rectangle_line_1548 | coords |
| canvas_modes_editor_tarzankhr_c_rectangle_line_1573_coords | khr_canvas | modes_editor_tarzankhr | c_rectangle_line_1573 | coords |
| canvas_modes_editor_tarzankhr_c_text_line_1457_text | khr_canvas | modes_editor_tarzankhr | c_text_line_1457 | text |
| canvas_modes_editor_tarzankhr_c_text_line_1465_text | khr_canvas | modes_editor_tarzankhr | c_text_line_1465 | text |
| canvas_modes_editor_tarzankhr_c_text_line_1472_text | khr_canvas | modes_editor_tarzankhr | c_text_line_1472 | text |
| canvas_modes_editor_tarzankhr_c_text_line_1473_text | khr_canvas | modes_editor_tarzankhr | c_text_line_1473 | text |
| canvas_modes_editor_tarzankhr_c_text_line_1474_text | khr_canvas | modes_editor_tarzankhr | c_text_line_1474 | text |
| canvas_modes_editor_tarzankhr_c_text_line_1481_text | khr_canvas | modes_editor_tarzankhr | c_text_line_1481 | text |
| canvas_modes_editor_tarzankhr_c_text_line_1486_text | khr_canvas | modes_editor_tarzankhr | c_text_line_1486 | text |
| canvas_modes_editor_tarzankhr_c_text_line_1496_text | khr_canvas | modes_editor_tarzankhr | c_text_line_1496 | text |
| canvas_modes_editor_tarzankhr_c_text_line_1503_text | khr_canvas | modes_editor_tarzankhr | c_text_line_1503 | text |
| canvas_modes_editor_tarzankhr_c_text_line_1520_text | khr_canvas | modes_editor_tarzankhr | c_text_line_1520 | text |
| canvas_modes_editor_tarzankhr_c_text_line_1522_text | khr_canvas | modes_editor_tarzankhr | c_text_line_1522 | text |
| canvas_modes_editor_tarzankhr_c_text_line_1525_text | khr_canvas | modes_editor_tarzankhr | c_text_line_1525 | text |
| canvas_modes_editor_tarzankhr_c_text_line_1542_text | khr_canvas | modes_editor_tarzankhr | c_text_line_1542 | text |
| canvas_modes_editor_tarzankhr_c_text_line_1549_text | khr_canvas | modes_editor_tarzankhr | c_text_line_1549 | text |
| canvas_modes_editor_tarzankhr_c_text_line_1554_text | khr_canvas | modes_editor_tarzankhr | c_text_line_1554 | text |
| canvas_modes_editor_tarzankhr_c_text_line_1556_text | khr_canvas | modes_editor_tarzankhr | c_text_line_1556 | text |
| canvas_modes_editor_tarzankhr_c_text_line_1564_text | khr_canvas | modes_editor_tarzankhr | c_text_line_1564 | text |
| canvas_modes_editor_tarzankhr_c_text_line_1569_text | khr_canvas | modes_editor_tarzankhr | c_text_line_1569 | text |
| canvas_modes_editor_tarzankhr_c_text_line_1574_text | khr_canvas | modes_editor_tarzankhr | c_text_line_1574 | text |
| canvas_modes_editor_tarzankhr_c_text_line_1576_text | khr_canvas | modes_editor_tarzankhr | c_text_line_1576 | text |
| canvas_modes_editor_tarzankhr_c_text_line_1578_text | khr_canvas | modes_editor_tarzankhr | c_text_line_1578 | text |
| canvas_modes_editor_tarzankhr_c_text_line_1579_text | khr_canvas | modes_editor_tarzankhr | c_text_line_1579 | text |
| canvas_modes_editor_tarzankhr_c_text_line_1580_text | khr_canvas | modes_editor_tarzankhr | c_text_line_1580 | text |
| canvas_modes_editor_tarzankhr_c_text_line_1603_text | khr_canvas | modes_editor_tarzankhr | c_text_line_1603 | text |
| canvas_modes_editor_tarzankhr_c_text_line_1604_text | khr_canvas | modes_editor_tarzankhr | c_text_line_1604 | text |
| canvas_modes_editor_tarzankhr_c_text_line_1605_text | khr_canvas | modes_editor_tarzankhr | c_text_line_1605 | text |
| canvas_modes_editor_tarzankhr_c_text_line_615_text | khr_canvas | modes_editor_tarzankhr | c_text_line_615 | text |
| canvas_modes_editor_tarzankhr_c_text_line_625_text | khr_canvas | modes_editor_tarzankhr | c_text_line_625 | text |
| canvas_modes_editor_tarzankhr_c_text_line_627_text | khr_canvas | modes_editor_tarzankhr | c_text_line_627 | text |
| canvas_modes_editor_tarzankhr_c_text_line_629_text | khr_canvas | modes_editor_tarzankhr | c_text_line_629 | text |
| canvas_modes_editor_tarzantakeprotocollight_canvas_image_line_860_coords | canvas_preview | modes_editor_tarzantakeprotocollight | canvas_image_line_860 | coords |
| canvas_modes_editor_tarzantakeprotocollight_item_text | canvas_preview | modes_editor_tarzantakeprotocollight | item | text |
| canvas_modes_editor_tarzantakeprotocollight_protocol_canvas_rectangle_line_1215_coords | canvas_preview | modes_editor_tarzantakeprotocollight | protocol_canvas_rectangle_line_1215 | coords |
| canvas_modes_editor_tarzantakeprotocollight_protocol_canvas_rectangle_line_1216_coords | canvas_preview | modes_editor_tarzantakeprotocollight | protocol_canvas_rectangle_line_1216 | coords |
| canvas_modes_editor_tarzantakeprotocollight_protocol_title_id_text | canvas_preview | modes_editor_tarzantakeprotocollight | protocol_title_id | text |
| canvas_modes_editor_tarzantakeprotocollight_row_window_coords | canvas_preview | modes_editor_tarzantakeprotocollight | row_window | coords |
| canvas_modes_editor_tarzantakeprotocollight_save_button_window_coords | canvas_preview | modes_editor_tarzantakeprotocollight | save_button_window | coords |
| canvas_vision_tarzanvisionsetup_window_id_coords | canvas_preview | vision_tarzanvisionsetup | window_id | coords |
| ehr_axis_0_curve | ehr_canvas | ehr_main | axis_0_curve | coords |
| ehr_axis_0_metrics | ehr_tkinter | ehr_axis_info | axis_0_metrics | text |
| ehr_axis_0_step_preview | ehr_canvas | ehr_protocol | axis_0_step_bars | coords |
| ehr_axis_1_curve | ehr_canvas | ehr_main | axis_1_curve | coords |
| ehr_axis_1_metrics | ehr_tkinter | ehr_axis_info | axis_1_metrics | text |
| ehr_axis_1_step_preview | ehr_canvas | ehr_protocol | axis_1_step_bars | coords |
| ehr_axis_2_curve | ehr_canvas | ehr_main | axis_2_curve | coords |
| ehr_axis_2_metrics | ehr_tkinter | ehr_axis_info | axis_2_metrics | text |
| ehr_axis_2_step_preview | ehr_canvas | ehr_protocol | axis_2_step_bars | coords |
| ehr_axis_3_curve | ehr_canvas | ehr_main | axis_3_curve | coords |
| ehr_axis_3_metrics | ehr_tkinter | ehr_axis_info | axis_3_metrics | text |
| ehr_axis_3_step_preview | ehr_canvas | ehr_protocol | axis_3_step_bars | coords |
| ehr_axis_4_curve | ehr_canvas | ehr_main | axis_4_curve | coords |
| ehr_axis_4_metrics | ehr_tkinter | ehr_axis_info | axis_4_metrics | text |
| ehr_axis_4_step_preview | ehr_canvas | ehr_protocol | axis_4_step_bars | coords |
| ehr_axis_5_curve | ehr_canvas | ehr_main | axis_5_curve | coords |
| ehr_axis_5_metrics | ehr_tkinter | ehr_axis_info | axis_5_metrics | text |
| ehr_axis_5_step_preview | ehr_canvas | ehr_protocol | axis_5_step_bars | coords |
| ehr_take_slot_0_status | ehr_tkinter | ehr_take_slots | slot_0 | state |
| ehr_take_slot_1_status | ehr_tkinter | ehr_take_slots | slot_1 | state |
| ehr_take_slot_2_status | ehr_tkinter | ehr_take_slots | slot_2 | state |
| ehr_take_slot_3_status | ehr_tkinter | ehr_take_slots | slot_3 | state |
| ehr_take_slot_4_status | ehr_tkinter | ehr_take_slots | slot_4 | state |
| ehr_take_slot_5_status | ehr_tkinter | ehr_take_slots | slot_5 | state |
| ehr_take_slot_6_status | ehr_tkinter | ehr_take_slots | slot_6 | state |
| ehr_take_slot_7_status | ehr_tkinter | ehr_take_slots | slot_7 | state |
| khr_input_marker | khr_canvas | khr_input | marker | coords |
| khr_output_marker | khr_canvas | khr_output | marker | coords |
| khr_status | khr_tkinter | khr | status_label | text |
| layout_panel_status | layout_canvas | par_layout | panel_status | text |
| layout_selected_cell | layout_canvas | par_layout | selected_cell | coords |
| layout_zone_label | layout_canvas | par_layout | zone_label | text |
| level_x | physical_nextion | level_xyz | va0 | val |
| level_x | canvas_preview | level_xyz | va0 | val |
| level_x | par_tkinter | sensors_panel | level_x_label | text |
| level_y | physical_nextion | level_xyz | va1 | val |
| level_y | canvas_preview | level_xyz | va1 | val |
| level_y | par_tkinter | sensors_panel | level_y_label | text |
| nextion_boot_event_en | physical_nextion | boot | Event | en |
| nextion_boot_event_en | canvas_preview | boot | Event | en |
| nextion_boot_event_tim | physical_nextion | boot | Event | tim |
| nextion_boot_event_tim | canvas_preview | boot | Event | tim |
| nextion_boot_p0_pic | physical_nextion | boot | p0 | pic |
| nextion_boot_p0_pic | canvas_preview | boot | p0 | pic |
| nextion_boot_tm0_en | physical_nextion | boot | tm0 | en |
| nextion_boot_tm0_en | canvas_preview | boot | tm0 | en |
| nextion_boot_tm0_tim | physical_nextion | boot | tm0 | tim |
| nextion_boot_tm0_tim | canvas_preview | boot | tm0 | tim |
| nextion_boot_va0_val | physical_nextion | boot | va0 | val |
| nextion_boot_va0_val | canvas_preview | boot | va0 | val |
| nextion_face_rec_b_home_pic | physical_nextion | face_rec | b_home | pic |
| nextion_face_rec_b_home_pic | canvas_preview | face_rec | b_home | pic |
| nextion_face_rec_b_home_val | physical_nextion | face_rec | b_home | val |
| nextion_face_rec_b_home_val | canvas_preview | face_rec | b_home | val |
| nextion_face_rec_t0_txt | physical_nextion | face_rec | t0 | txt |
| nextion_face_rec_t0_txt | canvas_preview | face_rec | t0 | txt |
| nextion_keybda_b0_pic | physical_nextion | keybdA | b0 | pic |
| nextion_keybda_b0_pic | canvas_preview | keybdA | b0 | pic |
| nextion_keybda_b0_val | physical_nextion | keybdA | b0 | val |
| nextion_keybda_b0_val | canvas_preview | keybdA | b0 | val |
| nextion_keybda_b1_pic | physical_nextion | keybdA | b1 | pic |
| nextion_keybda_b1_pic | canvas_preview | keybdA | b1 | pic |
| nextion_keybda_b1_val | physical_nextion | keybdA | b1 | val |
| nextion_keybda_b1_val | canvas_preview | keybdA | b1 | val |
| nextion_keybda_b200_pic | physical_nextion | keybdA | b200 | pic |
| nextion_keybda_b200_pic | canvas_preview | keybdA | b200 | pic |
| nextion_keybda_b200_val | physical_nextion | keybdA | b200 | val |
| nextion_keybda_b200_val | canvas_preview | keybdA | b200 | val |
| nextion_keybda_b201_pic | physical_nextion | keybdA | b201 | pic |
| nextion_keybda_b201_pic | canvas_preview | keybdA | b201 | pic |
| nextion_keybda_b201_val | physical_nextion | keybdA | b201 | val |
| nextion_keybda_b201_val | canvas_preview | keybdA | b201 | val |
| nextion_keybda_b20_pic | physical_nextion | keybdA | b20 | pic |
| nextion_keybda_b20_pic | canvas_preview | keybdA | b20 | pic |
| nextion_keybda_b20_val | physical_nextion | keybdA | b20 | val |
| nextion_keybda_b20_val | canvas_preview | keybdA | b20 | val |
| nextion_keybda_b210_pic | physical_nextion | keybdA | b210 | pic |
| nextion_keybda_b210_pic | canvas_preview | keybdA | b210 | pic |
| nextion_keybda_b210_val | physical_nextion | keybdA | b210 | val |
| nextion_keybda_b210_val | canvas_preview | keybdA | b210 | val |
| nextion_keybda_b21_pic | physical_nextion | keybdA | b21 | pic |
| nextion_keybda_b21_pic | canvas_preview | keybdA | b21 | pic |
| nextion_keybda_b21_val | physical_nextion | keybdA | b21 | val |
| nextion_keybda_b21_val | canvas_preview | keybdA | b21 | val |
| nextion_keybda_b220_pic | physical_nextion | keybdA | b220 | pic |
| nextion_keybda_b220_pic | canvas_preview | keybdA | b220 | pic |
| nextion_keybda_b220_val | physical_nextion | keybdA | b220 | val |
| nextion_keybda_b220_val | canvas_preview | keybdA | b220 | val |
| nextion_keybda_b22_pic | physical_nextion | keybdA | b22 | pic |
| nextion_keybda_b22_pic | canvas_preview | keybdA | b22 | pic |
| nextion_keybda_b22_val | physical_nextion | keybdA | b22 | val |
| nextion_keybda_b22_val | canvas_preview | keybdA | b22 | val |
| nextion_keybda_b230_pic | physical_nextion | keybdA | b230 | pic |
| nextion_keybda_b230_pic | canvas_preview | keybdA | b230 | pic |
| nextion_keybda_b230_val | physical_nextion | keybdA | b230 | val |
| nextion_keybda_b230_val | canvas_preview | keybdA | b230 | val |
| nextion_keybda_b231_pic | physical_nextion | keybdA | b231 | pic |
| nextion_keybda_b231_pic | canvas_preview | keybdA | b231 | pic |
| nextion_keybda_b231_val | physical_nextion | keybdA | b231 | val |
| nextion_keybda_b231_val | canvas_preview | keybdA | b231 | val |
| nextion_keybda_b232_pic | physical_nextion | keybdA | b232 | pic |
| nextion_keybda_b232_pic | canvas_preview | keybdA | b232 | pic |
| nextion_keybda_b232_val | physical_nextion | keybdA | b232 | val |
| nextion_keybda_b232_val | canvas_preview | keybdA | b232 | val |
| nextion_keybda_b23_pic | physical_nextion | keybdA | b23 | pic |
| nextion_keybda_b23_pic | canvas_preview | keybdA | b23 | pic |
| nextion_keybda_b23_val | physical_nextion | keybdA | b23 | val |
| nextion_keybda_b23_val | canvas_preview | keybdA | b23 | val |
| nextion_keybda_b240_pic | physical_nextion | keybdA | b240 | pic |
| nextion_keybda_b240_pic | canvas_preview | keybdA | b240 | pic |
| nextion_keybda_b240_val | physical_nextion | keybdA | b240 | val |
| nextion_keybda_b240_val | canvas_preview | keybdA | b240 | val |
| nextion_keybda_b241_pic | physical_nextion | keybdA | b241 | pic |
| nextion_keybda_b241_pic | canvas_preview | keybdA | b241 | pic |
| nextion_keybda_b241_val | physical_nextion | keybdA | b241 | val |
| nextion_keybda_b241_val | canvas_preview | keybdA | b241 | val |
| nextion_keybda_b242_pic | physical_nextion | keybdA | b242 | pic |
| nextion_keybda_b242_pic | canvas_preview | keybdA | b242 | pic |
| nextion_keybda_b242_val | physical_nextion | keybdA | b242 | val |
| nextion_keybda_b242_val | canvas_preview | keybdA | b242 | val |
| nextion_keybda_b243_pic | physical_nextion | keybdA | b243 | pic |
| nextion_keybda_b243_pic | canvas_preview | keybdA | b243 | pic |
| nextion_keybda_b243_val | physical_nextion | keybdA | b243 | val |
| nextion_keybda_b243_val | canvas_preview | keybdA | b243 | val |
| nextion_keybda_b244_pic | physical_nextion | keybdA | b244 | pic |
| nextion_keybda_b244_pic | canvas_preview | keybdA | b244 | pic |
| nextion_keybda_b244_val | physical_nextion | keybdA | b244 | val |
| nextion_keybda_b244_val | canvas_preview | keybdA | b244 | val |
| nextion_keybda_b249_pic | physical_nextion | keybdA | b249 | pic |
| nextion_keybda_b249_pic | canvas_preview | keybdA | b249 | pic |
| nextion_keybda_b249_val | physical_nextion | keybdA | b249 | val |
| nextion_keybda_b249_val | canvas_preview | keybdA | b249 | val |
| nextion_keybda_b24_pic | physical_nextion | keybdA | b24 | pic |
| nextion_keybda_b24_pic | canvas_preview | keybdA | b24 | pic |
| nextion_keybda_b24_val | physical_nextion | keybdA | b24 | val |
| nextion_keybda_b24_val | canvas_preview | keybdA | b24 | val |
| nextion_keybda_b251_pic | physical_nextion | keybdA | b251 | pic |
| nextion_keybda_b251_pic | canvas_preview | keybdA | b251 | pic |
| nextion_keybda_b251_val | physical_nextion | keybdA | b251 | val |
| nextion_keybda_b251_val | canvas_preview | keybdA | b251 | val |
| nextion_keybda_b25_pic | physical_nextion | keybdA | b25 | pic |
| nextion_keybda_b25_pic | canvas_preview | keybdA | b25 | pic |
| nextion_keybda_b25_val | physical_nextion | keybdA | b25 | val |
| nextion_keybda_b25_val | canvas_preview | keybdA | b25 | val |
| nextion_keybda_b26_pic | physical_nextion | keybdA | b26 | pic |
| nextion_keybda_b26_pic | canvas_preview | keybdA | b26 | pic |
| nextion_keybda_b26_val | physical_nextion | keybdA | b26 | val |
| nextion_keybda_b26_val | canvas_preview | keybdA | b26 | val |
| nextion_keybda_b27_pic | physical_nextion | keybdA | b27 | pic |
| nextion_keybda_b27_pic | canvas_preview | keybdA | b27 | pic |
| nextion_keybda_b27_val | physical_nextion | keybdA | b27 | val |
| nextion_keybda_b27_val | canvas_preview | keybdA | b27 | val |
| nextion_keybda_b28_pic | physical_nextion | keybdA | b28 | pic |
| nextion_keybda_b28_pic | canvas_preview | keybdA | b28 | pic |
| nextion_keybda_b28_val | physical_nextion | keybdA | b28 | val |
| nextion_keybda_b28_val | canvas_preview | keybdA | b28 | val |
| nextion_keybda_b2_pic | physical_nextion | keybdA | b2 | pic |
| nextion_keybda_b2_pic | canvas_preview | keybdA | b2 | pic |
| nextion_keybda_b2_val | physical_nextion | keybdA | b2 | val |
| nextion_keybda_b2_val | canvas_preview | keybdA | b2 | val |
| nextion_keybda_b3_pic | physical_nextion | keybdA | b3 | pic |
| nextion_keybda_b3_pic | canvas_preview | keybdA | b3 | pic |
| nextion_keybda_b3_val | physical_nextion | keybdA | b3 | val |
| nextion_keybda_b3_val | canvas_preview | keybdA | b3 | val |
| nextion_keybda_b40_pic | physical_nextion | keybdA | b40 | pic |
| nextion_keybda_b40_pic | canvas_preview | keybdA | b40 | pic |
| nextion_keybda_b40_val | physical_nextion | keybdA | b40 | val |
| nextion_keybda_b40_val | canvas_preview | keybdA | b40 | val |
| nextion_keybda_b41_pic | physical_nextion | keybdA | b41 | pic |
| nextion_keybda_b41_pic | canvas_preview | keybdA | b41 | pic |
| nextion_keybda_b41_val | physical_nextion | keybdA | b41 | val |
| nextion_keybda_b41_val | canvas_preview | keybdA | b41 | val |
| nextion_keybda_b42_pic | physical_nextion | keybdA | b42 | pic |
| nextion_keybda_b42_pic | canvas_preview | keybdA | b42 | pic |
| nextion_keybda_b42_val | physical_nextion | keybdA | b42 | val |
| nextion_keybda_b42_val | canvas_preview | keybdA | b42 | val |
| nextion_keybda_b43_pic | physical_nextion | keybdA | b43 | pic |
| nextion_keybda_b43_pic | canvas_preview | keybdA | b43 | pic |
| nextion_keybda_b43_val | physical_nextion | keybdA | b43 | val |
| nextion_keybda_b43_val | canvas_preview | keybdA | b43 | val |
| nextion_keybda_b44_pic | physical_nextion | keybdA | b44 | pic |
| nextion_keybda_b44_pic | canvas_preview | keybdA | b44 | pic |
| nextion_keybda_b44_val | physical_nextion | keybdA | b44 | val |
| nextion_keybda_b44_val | canvas_preview | keybdA | b44 | val |
| nextion_keybda_b45_pic | physical_nextion | keybdA | b45 | pic |
| nextion_keybda_b45_pic | canvas_preview | keybdA | b45 | pic |
| nextion_keybda_b45_val | physical_nextion | keybdA | b45 | val |
| nextion_keybda_b45_val | canvas_preview | keybdA | b45 | val |
| nextion_keybda_b46_pic | physical_nextion | keybdA | b46 | pic |
| nextion_keybda_b46_pic | canvas_preview | keybdA | b46 | pic |
| nextion_keybda_b46_val | physical_nextion | keybdA | b46 | val |
| nextion_keybda_b46_val | canvas_preview | keybdA | b46 | val |
| nextion_keybda_b4_pic | physical_nextion | keybdA | b4 | pic |
| nextion_keybda_b4_pic | canvas_preview | keybdA | b4 | pic |
| nextion_keybda_b4_val | physical_nextion | keybdA | b4 | val |
| nextion_keybda_b4_val | canvas_preview | keybdA | b4 | val |
| nextion_keybda_b5_pic | physical_nextion | keybdA | b5 | pic |
| nextion_keybda_b5_pic | canvas_preview | keybdA | b5 | pic |
| nextion_keybda_b5_val | physical_nextion | keybdA | b5 | val |
| nextion_keybda_b5_val | canvas_preview | keybdA | b5 | val |
| nextion_keybda_b6_pic | physical_nextion | keybdA | b6 | pic |
| nextion_keybda_b6_pic | canvas_preview | keybdA | b6 | pic |
| nextion_keybda_b6_val | physical_nextion | keybdA | b6 | val |
| nextion_keybda_b6_val | canvas_preview | keybdA | b6 | val |
| nextion_keybda_b7_pic | physical_nextion | keybdA | b7 | pic |
| nextion_keybda_b7_pic | canvas_preview | keybdA | b7 | pic |
| nextion_keybda_b7_val | physical_nextion | keybdA | b7 | val |
| nextion_keybda_b7_val | canvas_preview | keybdA | b7 | val |
| nextion_keybda_b8_pic | physical_nextion | keybdA | b8 | pic |
| nextion_keybda_b8_pic | canvas_preview | keybdA | b8 | pic |
| nextion_keybda_b8_val | physical_nextion | keybdA | b8 | val |
| nextion_keybda_b8_val | canvas_preview | keybdA | b8 | val |
| nextion_keybda_b9_pic | physical_nextion | keybdA | b9 | pic |
| nextion_keybda_b9_pic | canvas_preview | keybdA | b9 | pic |
| nextion_keybda_b9_val | physical_nextion | keybdA | b9 | val |
| nextion_keybda_b9_val | canvas_preview | keybdA | b9 | val |
| nextion_keybda_event_en | physical_nextion | keybdA | Event | en |
| nextion_keybda_event_en | canvas_preview | keybdA | Event | en |
| nextion_keybda_event_tim | physical_nextion | keybdA | Event | tim |
| nextion_keybda_event_tim | canvas_preview | keybdA | Event | tim |
| nextion_keybda_input_txt | physical_nextion | keybdA | input | txt |
| nextion_keybda_input_txt | canvas_preview | keybdA | input | txt |
| nextion_keybda_inputlenth_val | physical_nextion | keybdA | inputlenth | val |
| nextion_keybda_inputlenth_val | canvas_preview | keybdA | inputlenth | val |
| nextion_keybda_loadcmpid_val | physical_nextion | keybdA | loadcmpid | val |
| nextion_keybda_loadcmpid_val | canvas_preview | keybdA | loadcmpid | val |
| nextion_keybda_loadpageid_val | physical_nextion | keybdA | loadpageid | val |
| nextion_keybda_loadpageid_val | canvas_preview | keybdA | loadpageid | val |
| nextion_keybda_refshow_state | physical_nextion | keybdA | refshow | state |
| nextion_keybda_refshow_state | canvas_preview | keybdA | refshow | state |
| nextion_keybda_show_txt | physical_nextion | keybdA | show | txt |
| nextion_keybda_show_txt | canvas_preview | keybdA | show | txt |
| nextion_keybda_temp2_val | physical_nextion | keybdA | temp2 | val |
| nextion_keybda_temp2_val | canvas_preview | keybdA | temp2 | val |
| nextion_keybda_temp_val | physical_nextion | keybdA | temp | val |
| nextion_keybda_temp_val | canvas_preview | keybdA | temp | val |
| nextion_keybda_tempstr_txt | physical_nextion | keybdA | tempstr | txt |
| nextion_keybda_tempstr_txt | canvas_preview | keybdA | tempstr | txt |
| nextion_keybda_tm0_en | physical_nextion | keybdA | tm0 | en |
| nextion_keybda_tm0_en | canvas_preview | keybdA | tm0 | en |
| nextion_keybda_tm0_tim | physical_nextion | keybdA | tm0 | tim |
| nextion_keybda_tm0_tim | canvas_preview | keybdA | tm0 | tim |
| nextion_level_xyz_b_home_pic | physical_nextion | level_xyz | b_home | pic |
| nextion_level_xyz_b_home_pic | canvas_preview | level_xyz | b_home | pic |
| nextion_level_xyz_b_home_val | physical_nextion | level_xyz | b_home | val |
| nextion_level_xyz_b_home_val | canvas_preview | level_xyz | b_home | val |
| nextion_level_xyz_event_en | physical_nextion | level_xyz | Event | en |
| nextion_level_xyz_event_en | canvas_preview | level_xyz | Event | en |
| nextion_level_xyz_event_tim | physical_nextion | level_xyz | Event | tim |
| nextion_level_xyz_event_tim | canvas_preview | level_xyz | Event | tim |
| nextion_level_xyz_p0_pic | physical_nextion | level_xyz | p0 | pic |
| nextion_level_xyz_p0_pic | canvas_preview | level_xyz | p0 | pic |
| nextion_level_xyz_tm0_en | physical_nextion | level_xyz | tm0 | en |
| nextion_level_xyz_tm0_en | canvas_preview | level_xyz | tm0 | en |
| nextion_level_xyz_tm0_tim | physical_nextion | level_xyz | tm0 | tim |
| nextion_level_xyz_tm0_tim | canvas_preview | level_xyz | tm0 | tim |
| nextion_level_xyz_va0_val | physical_nextion | level_xyz | va0 | val |
| nextion_level_xyz_va0_val | canvas_preview | level_xyz | va0 | val |
| nextion_level_xyz_va1_val | physical_nextion | level_xyz | va1 | val |
| nextion_level_xyz_va1_val | canvas_preview | level_xyz | va1 | val |
| nextion_level_xyz_va2_val | physical_nextion | level_xyz | va2 | val |
| nextion_level_xyz_va2_val | canvas_preview | level_xyz | va2 | val |
| nextion_level_xyz_va3_val | physical_nextion | level_xyz | va3 | val |
| nextion_level_xyz_va3_val | canvas_preview | level_xyz | va3 | val |
| nextion_page1_b_face_pic | physical_nextion | page1 | b_face | pic |
| nextion_page1_b_face_pic | canvas_preview | page1 | b_face | pic |
| nextion_page1_b_face_val | physical_nextion | page1 | b_face | val |
| nextion_page1_b_face_val | canvas_preview | page1 | b_face | val |
| nextion_page1_b_level_pic | physical_nextion | page1 | b_level | pic |
| nextion_page1_b_level_pic | canvas_preview | page1 | b_level | pic |
| nextion_page1_b_level_val | physical_nextion | page1 | b_level | val |
| nextion_page1_b_level_val | canvas_preview | page1 | b_level | val |
| nextion_page1_b_rrp_pic | physical_nextion | page1 | b_rrp | pic |
| nextion_page1_b_rrp_pic | canvas_preview | page1 | b_rrp | pic |
| nextion_page1_b_rrp_val | physical_nextion | page1 | b_rrp | val |
| nextion_page1_b_rrp_val | canvas_preview | page1 | b_rrp | val |
| nextion_page1_b_sensors_pic | physical_nextion | page1 | b_sensors | pic |
| nextion_page1_b_sensors_pic | canvas_preview | page1 | b_sensors | pic |
| nextion_page1_b_sensors_val | physical_nextion | page1 | b_sensors | val |
| nextion_page1_b_sensors_val | canvas_preview | page1 | b_sensors | val |
| nextion_page1_b_settings_pic | physical_nextion | page1 | b_settings | pic |
| nextion_page1_b_settings_pic | canvas_preview | page1 | b_settings | pic |
| nextion_page1_b_settings_val | physical_nextion | page1 | b_settings | val |
| nextion_page1_b_settings_val | canvas_preview | page1 | b_settings | val |
| nextion_page1_b_take_pic | physical_nextion | page1 | b_take | pic |
| nextion_page1_b_take_pic | canvas_preview | page1 | b_take | pic |
| nextion_page1_b_take_val | physical_nextion | page1 | b_take | val |
| nextion_page1_b_take_val | canvas_preview | page1 | b_take | val |
| nextion_rrp_main_b_home_pic | physical_nextion | rrp_main | b_home | pic |
| nextion_rrp_main_b_home_pic | canvas_preview | rrp_main | b_home | pic |
| nextion_rrp_main_b_home_val | physical_nextion | rrp_main | b_home | val |
| nextion_rrp_main_b_home_val | canvas_preview | rrp_main | b_home | val |
| nextion_rrp_main_b_p1_arm_h_val | physical_nextion | rrp_main | b_p1_arm_h | val |
| nextion_rrp_main_b_p1_arm_h_val | canvas_preview | rrp_main | b_p1_arm_h | val |
| nextion_rrp_main_b_p1_arm_v_val | physical_nextion | rrp_main | b_p1_arm_v | val |
| nextion_rrp_main_b_p1_arm_v_val | canvas_preview | rrp_main | b_p1_arm_v | val |
| nextion_rrp_main_b_p1_cam_f_val | physical_nextion | rrp_main | b_p1_cam_f | val |
| nextion_rrp_main_b_p1_cam_f_val | canvas_preview | rrp_main | b_p1_cam_f | val |
| nextion_rrp_main_b_p1_cam_h_val | physical_nextion | rrp_main | b_p1_cam_h | val |
| nextion_rrp_main_b_p1_cam_h_val | canvas_preview | rrp_main | b_p1_cam_h | val |
| nextion_rrp_main_b_p1_cam_t_val | physical_nextion | rrp_main | b_p1_cam_t | val |
| nextion_rrp_main_b_p1_cam_t_val | canvas_preview | rrp_main | b_p1_cam_t | val |
| nextion_rrp_main_b_p1_cam_v_val | physical_nextion | rrp_main | b_p1_cam_v | val |
| nextion_rrp_main_b_p1_cam_v_val | canvas_preview | rrp_main | b_p1_cam_v | val |
| nextion_rrp_main_b_p1_dir_val | physical_nextion | rrp_main | b_p1_dir | val |
| nextion_rrp_main_b_p1_dir_val | canvas_preview | rrp_main | b_p1_dir | val |
| nextion_rrp_main_b_p2_arm_h_val | physical_nextion | rrp_main | b_p2_arm_h | val |
| nextion_rrp_main_b_p2_arm_h_val | canvas_preview | rrp_main | b_p2_arm_h | val |
| nextion_rrp_main_b_p2_arm_v_val | physical_nextion | rrp_main | b_p2_arm_v | val |
| nextion_rrp_main_b_p2_arm_v_val | canvas_preview | rrp_main | b_p2_arm_v | val |
| nextion_rrp_main_b_p2_cam_f_val | physical_nextion | rrp_main | b_p2_cam_f | val |
| nextion_rrp_main_b_p2_cam_f_val | canvas_preview | rrp_main | b_p2_cam_f | val |
| nextion_rrp_main_b_p2_cam_h_val | physical_nextion | rrp_main | b_p2_cam_h | val |
| nextion_rrp_main_b_p2_cam_h_val | canvas_preview | rrp_main | b_p2_cam_h | val |
| nextion_rrp_main_b_p2_cam_t_val | physical_nextion | rrp_main | b_p2_cam_t | val |
| nextion_rrp_main_b_p2_cam_t_val | canvas_preview | rrp_main | b_p2_cam_t | val |
| nextion_rrp_main_b_p2_cam_v_val | physical_nextion | rrp_main | b_p2_cam_v | val |
| nextion_rrp_main_b_p2_cam_v_val | canvas_preview | rrp_main | b_p2_cam_v | val |
| nextion_rrp_main_b_p2_dir_val | physical_nextion | rrp_main | b_p2_dir | val |
| nextion_rrp_main_b_p2_dir_val | canvas_preview | rrp_main | b_p2_dir | val |
| nextion_rrp_main_b_stop_pic | physical_nextion | rrp_main | b_stop | pic |
| nextion_rrp_main_b_stop_pic | canvas_preview | rrp_main | b_stop | pic |
| nextion_rrp_main_b_stop_val | physical_nextion | rrp_main | b_stop | val |
| nextion_rrp_main_b_stop_val | canvas_preview | rrp_main | b_stop | val |
| nextion_rrp_main_h_p1_sens_val | physical_nextion | rrp_main | h_p1_sens | val |
| nextion_rrp_main_h_p1_sens_val | canvas_preview | rrp_main | h_p1_sens | val |
| nextion_rrp_main_h_p2_sens_val | physical_nextion | rrp_main | h_p2_sens | val |
| nextion_rrp_main_h_p2_sens_val | canvas_preview | rrp_main | h_p2_sens | val |
| nextion_rrp_main_t_buf_p1_txt | physical_nextion | rrp_main | t_buf_p1 | txt |
| nextion_rrp_main_t_buf_p1_txt | canvas_preview | rrp_main | t_buf_p1 | txt |
| nextion_rrp_main_t_buf_p2_txt | physical_nextion | rrp_main | t_buf_p2 | txt |
| nextion_rrp_main_t_buf_p2_txt | canvas_preview | rrp_main | t_buf_p2 | txt |
| nextion_rrp_main_t_p1_val_txt | physical_nextion | rrp_main | t_p1_val | txt |
| nextion_rrp_main_t_p1_val_txt | canvas_preview | rrp_main | t_p1_val | txt |
| nextion_rrp_main_t_p2_val_txt | physical_nextion | rrp_main | t_p2_val | txt |
| nextion_rrp_main_t_p2_val_txt | canvas_preview | rrp_main | t_p2_val | txt |
| nextion_rrp_main_va_p1_axis_val | physical_nextion | rrp_main | va_p1_axis | val |
| nextion_rrp_main_va_p1_axis_val | canvas_preview | rrp_main | va_p1_axis | val |
| nextion_rrp_main_va_p1_dir_val | physical_nextion | rrp_main | va_p1_dir | val |
| nextion_rrp_main_va_p1_dir_val | canvas_preview | rrp_main | va_p1_dir | val |
| nextion_rrp_main_va_p1_val_val | physical_nextion | rrp_main | va_p1_val | val |
| nextion_rrp_main_va_p1_val_val | canvas_preview | rrp_main | va_p1_val | val |
| nextion_rrp_main_va_p2_axis_val | physical_nextion | rrp_main | va_p2_axis | val |
| nextion_rrp_main_va_p2_axis_val | canvas_preview | rrp_main | va_p2_axis | val |
| nextion_rrp_main_va_p2_dir_val | physical_nextion | rrp_main | va_p2_dir | val |
| nextion_rrp_main_va_p2_dir_val | canvas_preview | rrp_main | va_p2_dir | val |
| nextion_rrp_main_va_p2_val_val | physical_nextion | rrp_main | va_p2_val | val |
| nextion_rrp_main_va_p2_val_val | canvas_preview | rrp_main | va_p2_val | val |
| nextion_rrp_main_va_tmp_val | physical_nextion | rrp_main | va_tmp | val |
| nextion_rrp_main_va_tmp_val | canvas_preview | rrp_main | va_tmp | val |
| nextion_mode_main_b_home_pic | physical_nextion | mode_main | b_home | pic |
| nextion_mode_main_b_home_pic | canvas_preview | mode_main | b_home | pic |
| nextion_mode_main_b_home_val | physical_nextion | mode_main | b_home | val |
| nextion_mode_main_b_home_val | canvas_preview | mode_main | b_home | val |
| nextion_mode_main_t0_txt | physical_nextion | mode_main | t0 | txt |
| nextion_mode_main_t0_txt | canvas_preview | mode_main | t0 | txt |
| nextion_settings_main_b_home_pic | physical_nextion | settings_main | b_home | pic |
| nextion_settings_main_b_home_pic | canvas_preview | settings_main | b_home | pic |
| nextion_settings_main_b_home_val | physical_nextion | settings_main | b_home | val |
| nextion_settings_main_b_home_val | canvas_preview | settings_main | b_home | val |
| nextion_settings_main_b_save_meta_pic | physical_nextion | settings_main | b_save_meta | pic |
| nextion_settings_main_b_save_meta_pic | canvas_preview | settings_main | b_save_meta | pic |
| nextion_settings_main_b_save_meta_val | physical_nextion | settings_main | b_save_meta | val |
| nextion_settings_main_b_save_meta_val | canvas_preview | settings_main | b_save_meta | val |
| nextion_settings_main_t_director_txt | physical_nextion | settings_main | t_director | txt |
| nextion_settings_main_t_director_txt | canvas_preview | settings_main | t_director | txt |
| nextion_settings_main_t_save_status_txt | physical_nextion | settings_main | t_save_status | txt |
| nextion_settings_main_t_save_status_txt | canvas_preview | settings_main | t_save_status | txt |
| nextion_settings_main_t_title_txt | physical_nextion | settings_main | t_title | txt |
| nextion_settings_main_t_title_txt | canvas_preview | settings_main | t_title | txt |
| nextion_take_main_b_clap_pic | physical_nextion | take_main | b_clap | pic |
| nextion_take_main_b_clap_pic | canvas_preview | take_main | b_clap | pic |
| nextion_take_main_b_clap_val | physical_nextion | take_main | b_clap | val |
| nextion_take_main_b_clap_val | canvas_preview | take_main | b_clap | val |
| nextion_take_main_b_home_pic | physical_nextion | take_main | b_home | pic |
| nextion_take_main_b_home_pic | canvas_preview | take_main | b_home | pic |
| nextion_take_main_b_home_val | physical_nextion | take_main | b_home | val |
| nextion_take_main_b_home_val | canvas_preview | take_main | b_home | val |
| nextion_take_main_p_axis0_pic | physical_nextion | take_main | p_axis0 | pic |
| nextion_take_main_p_axis0_pic | canvas_preview | take_main | p_axis0 | pic |
| nextion_take_main_p_axis1_pic | physical_nextion | take_main | p_axis1 | pic |
| nextion_take_main_p_axis1_pic | canvas_preview | take_main | p_axis1 | pic |
| nextion_take_main_p_axis2_pic | physical_nextion | take_main | p_axis2 | pic |
| nextion_take_main_p_axis2_pic | canvas_preview | take_main | p_axis2 | pic |
| nextion_take_main_p_axis3_pic | physical_nextion | take_main | p_axis3 | pic |
| nextion_take_main_p_axis3_pic | canvas_preview | take_main | p_axis3 | pic |
| nextion_take_main_p_axis4_pic | physical_nextion | take_main | p_axis4 | pic |
| nextion_take_main_p_axis4_pic | canvas_preview | take_main | p_axis4 | pic |
| nextion_take_main_p_axis5_pic | physical_nextion | take_main | p_axis5 | pic |
| nextion_take_main_p_axis5_pic | canvas_preview | take_main | p_axis5 | pic |
| nextion_take_main_p_laser_pic | physical_nextion | take_main | p_laser | pic |
| nextion_take_main_p_laser_pic | canvas_preview | take_main | p_laser | pic |
| nextion_take_main_p_light_pic | physical_nextion | take_main | p_light | pic |
| nextion_take_main_p_light_pic | canvas_preview | take_main | p_light | pic |
| nextion_take_main_p_limits_pic | physical_nextion | take_main | p_limits | pic |
| nextion_take_main_p_limits_pic | canvas_preview | take_main | p_limits | pic |
| nextion_take_main_p_shock_pic | physical_nextion | take_main | p_shock | pic |
| nextion_take_main_p_shock_pic | canvas_preview | take_main | p_shock | pic |
| nextion_take_main_p_temp_pic | physical_nextion | take_main | p_temp | pic |
| nextion_take_main_p_temp_pic | canvas_preview | take_main | p_temp | pic |
| nextion_take_main_p_xyz_pic | physical_nextion | take_main | p_xyz | pic |
| nextion_take_main_p_xyz_pic | canvas_preview | take_main | p_xyz | pic |
| nextion_take_main_t0_txt | physical_nextion | take_main | t0 | txt |
| nextion_take_main_t0_txt | canvas_preview | take_main | t0 | txt |
| nextion_take_main_t1_txt | physical_nextion | take_main | t1 | txt |
| nextion_take_main_t1_txt | canvas_preview | take_main | t1 | txt |
| nextion_take_main_t2_txt | physical_nextion | take_main | t2 | txt |
| nextion_take_main_t2_txt | canvas_preview | take_main | t2 | txt |
| nextion_take_main_t_axis0_txt | physical_nextion | take_main | t_axis0 | txt |
| nextion_take_main_t_axis0_txt | canvas_preview | take_main | t_axis0 | txt |
| nextion_take_main_t_axis1_txt | physical_nextion | take_main | t_axis1 | txt |
| nextion_take_main_t_axis1_txt | canvas_preview | take_main | t_axis1 | txt |
| nextion_take_main_t_axis2_txt | physical_nextion | take_main | t_axis2 | txt |
| nextion_take_main_t_axis2_txt | canvas_preview | take_main | t_axis2 | txt |
| nextion_take_main_t_axis3_txt | physical_nextion | take_main | t_axis3 | txt |
| nextion_take_main_t_axis3_txt | canvas_preview | take_main | t_axis3 | txt |
| nextion_take_main_t_axis4_txt | physical_nextion | take_main | t_axis4 | txt |
| nextion_take_main_t_axis4_txt | canvas_preview | take_main | t_axis4 | txt |
| nextion_take_main_t_axis5_txt | physical_nextion | take_main | t_axis5 | txt |
| nextion_take_main_t_axis5_txt | canvas_preview | take_main | t_axis5 | txt |
| nextion_take_main_t_clap_txt | physical_nextion | take_main | t_clap | txt |
| nextion_take_main_t_clap_txt | canvas_preview | take_main | t_clap | txt |
| nextion_take_main_t_laser_txt | physical_nextion | take_main | t_laser | txt |
| nextion_take_main_t_laser_txt | canvas_preview | take_main | t_laser | txt |
| nextion_take_main_t_light_txt | physical_nextion | take_main | t_light | txt |
| nextion_take_main_t_light_txt | canvas_preview | take_main | t_light | txt |
| nextion_take_main_t_limits_txt | physical_nextion | take_main | t_limits | txt |
| nextion_take_main_t_limits_txt | canvas_preview | take_main | t_limits | txt |
| nextion_take_main_t_shock_txt | physical_nextion | take_main | t_shock | txt |
| nextion_take_main_t_shock_txt | canvas_preview | take_main | t_shock | txt |
| nextion_take_main_t_status_txt | physical_nextion | take_main | t_status | txt |
| nextion_take_main_t_status_txt | canvas_preview | take_main | t_status | txt |
| nextion_take_main_t_take_txt | physical_nextion | take_main | t_take | txt |
| nextion_take_main_t_take_txt | canvas_preview | take_main | t_take | txt |
| nextion_take_main_t_temp_txt | physical_nextion | take_main | t_temp | txt |
| nextion_take_main_t_temp_txt | canvas_preview | take_main | t_temp | txt |
| nextion_take_main_t_xyz_txt | physical_nextion | take_main | t_xyz | txt |
| nextion_take_main_t_xyz_txt | canvas_preview | take_main | t_xyz | txt |
| nextion_ui_cut | physical_nextion | settings_main | b_ui_cut | val |
| nextion_ui_cut | par_tkinter | nextion_panel | ui_cut_status_label | text |
| rrp_p1_dir | physical_nextion | rrp_main | b_p1_dir | val |
| rrp_p1_dir | physical_nextion | rrp_main | va_p1_dir | val |
| rrp_p1_dir | canvas_preview | rrp_main | b_p1_dir | val |
| rrp_p1_dir | par_tkinter | par_rrp | p1_dir_widget | state |
| rrp_p1_sens | physical_nextion | rrp_main | h_p1_sens | val |
| rrp_p1_sens | canvas_preview | rrp_main | h_p1_sens | val |
| rrp_p1_sens | par_tkinter | par_rrp | p1_sens_slider | value |
| rrp_p1_value | physical_nextion | rrp_main | t_p1_val | txt |
| rrp_p1_value | canvas_preview | rrp_main | t_p1_val | txt |
| rrp_p1_value | par_tkinter | par_rrp | p1_value_label | text |
| rrp_p2_dir | physical_nextion | rrp_main | b_p2_dir | val |
| rrp_p2_dir | physical_nextion | rrp_main | va_p2_dir | val |
| rrp_p2_dir | canvas_preview | rrp_main | b_p2_dir | val |
| rrp_p2_dir | par_tkinter | par_rrp | p2_dir_widget | state |
| rrp_p2_sens | physical_nextion | rrp_main | h_p2_sens | val |
| rrp_p2_sens | canvas_preview | rrp_main | h_p2_sens | val |
| rrp_p2_sens | par_tkinter | par_rrp | p2_sens_slider | value |
| rrp_p2_value | physical_nextion | rrp_main | t_p2_val | txt |
| rrp_p2_value | canvas_preview | rrp_main | t_p2_val | txt |
| rrp_p2_value | par_tkinter | par_rrp | p2_value_label | text |
| sandbox_curve | sandbox_canvas | sandbox | curve | coords |
| sandbox_metrics | sandbox_tkinter | sandbox | metrics_label | text |
| sandbox_step_preview | sandbox_canvas | sandbox | step_bars | coords |
| take_timecode | physical_nextion | take_main | t0 | txt |
| take_timecode | canvas_preview | take_main | t0 | txt |
| take_timecode | par_tkinter | take_panel | timecode_label | text |
| timeline_clap_marker | timeline_canvas | par_timeline | clap_marker | coords |
| timeline_cursor | timeline_canvas | par_timeline | cursor | coords |
| timeline_take_marker | timeline_canvas | par_timeline | take_marker | coords |
| tk_editor_editor_ehr_tarzanaxissandbox_curve_canvas_state | ehr_tkinter | editor_editor_ehr_tarzanaxissandbox | curve_canvas | state |
| tk_editor_editor_ehr_tarzanaxissandbox_step_canvas_state | ehr_tkinter | editor_editor_ehr_tarzanaxissandbox | step_canvas | state |
| tk_editor_editor_ehr_tarzanehrui_axis_info_label_text | ehr_tkinter | editor_editor_ehr_tarzanehrui | axis_info_label | text |
| tk_editor_editor_ehr_tarzanehrui_canvas_state | ehr_tkinter | editor_editor_ehr_tarzanehrui | canvas | state |
| tk_editor_editor_ehr_tarzanehrui_curve_canvas_state | ehr_tkinter | editor_editor_ehr_tarzanehrui | curve_canvas | state |
| tk_editor_editor_ehr_tarzanehrui_left_state | ehr_tkinter | editor_editor_ehr_tarzanehrui | left | state |
| tk_editor_editor_ehr_tarzanehrui_protocol_box_state | ehr_tkinter | editor_editor_ehr_tarzanehrui | protocol_box | state |
| tk_editor_editor_ehr_tarzanehrui_protocol_canvas_state | ehr_tkinter | editor_editor_ehr_tarzanehrui | protocol_canvas | state |
| tk_editor_editor_ehr_tarzanehrui_protocol_holder_state | ehr_tkinter | editor_editor_ehr_tarzanehrui | protocol_holder | state |
| tk_editor_editor_ehr_tarzanehrui_protocol_label_text | ehr_tkinter | editor_editor_ehr_tarzanehrui | protocol_label | text |
| tk_editor_editor_ehr_tarzanehrui_protocol_text_text | ehr_tkinter | editor_editor_ehr_tarzanehrui | protocol_text | text |
| tk_editor_editor_ehr_tarzanehrui_row_frame_state | ehr_tkinter | editor_editor_ehr_tarzanehrui | row_frame | state |
| tk_editor_editor_ehr_tarzanehrui_save_button_text | ehr_tkinter | editor_editor_ehr_tarzanehrui | save_button | text |
| tk_editor_editor_ehr_tarzanehrui_status_text | ehr_tkinter | editor_editor_ehr_tarzanehrui | status | text |
| tk_editor_editor_ehr_tarzanehrui_step_canvas_state | ehr_tkinter | editor_editor_ehr_tarzanehrui | step_canvas | state |
| tk_editor_editor_ehr_tarzanehrui_take_panel_state | ehr_tkinter | editor_editor_ehr_tarzanehrui | take_panel | state |
| tk_editor_editor_ehr_tarzanehrui_timeline_canvas_state | ehr_tkinter | editor_editor_ehr_tarzanehrui | timeline_canvas | state |
| tk_editor_editor_tarzanaxissandbox_curve_canvas_state | sandbox_tkinter | editor_editor_tarzanaxissandbox | curve_canvas | state |
| tk_editor_editor_tarzanaxissandbox_step_canvas_state | sandbox_tkinter | editor_editor_tarzanaxissandbox | step_canvas | state |
| tk_editor_editor_tarzanehrtakesandbox_canvas_state | ehr_tkinter | editor_editor_tarzanehrtakesandbox | canvas | state |
| tk_editor_editor_tarzanehrtakesandbox_controls_wrap_state | ehr_tkinter | editor_editor_tarzanehrtakesandbox | controls_wrap | state |
| tk_editor_editor_tarzanehrtakesandbox_protocol_canvas_state | ehr_tkinter | editor_editor_tarzanehrtakesandbox | protocol_canvas | state |
| tk_editor_editor_tarzanehrtakesandbox_protocol_holder_state | ehr_tkinter | editor_editor_tarzanehrtakesandbox | protocol_holder | state |
| tk_editor_editor_tarzanehrtakesandbox_row_frame_state | ehr_tkinter | editor_editor_tarzanehrtakesandbox | row_frame | state |
| tk_editor_editor_tarzanehrtakesandbox_save_button_text | ehr_tkinter | editor_editor_tarzanehrtakesandbox | save_button | text |
| tk_editor_editor_tarzantakeprotocollight_canvas_state | par_tkinter | editor_editor_tarzantakeprotocollight | canvas | state |
| tk_editor_editor_tarzantakeprotocollight_protocol_canvas_state | par_tkinter | editor_editor_tarzantakeprotocollight | protocol_canvas | state |
| tk_editor_editor_tarzantakeprotocollight_protocol_holder_state | par_tkinter | editor_editor_tarzantakeprotocollight | protocol_holder | state |
| tk_editor_editor_tarzantakeprotocollight_row_frame_state | par_tkinter | editor_editor_tarzantakeprotocollight | row_frame | state |
| tk_editor_editor_tarzantakeprotocollight_save_button_text | par_tkinter | editor_editor_tarzantakeprotocollight | save_button | text |
| tk_editor_ehr_tarzanaxissandbox_curve_canvas_state | ehr_tkinter | editor_ehr_tarzanaxissandbox | curve_canvas | state |
| tk_editor_ehr_tarzanaxissandbox_step_canvas_state | ehr_tkinter | editor_ehr_tarzanaxissandbox | step_canvas | state |
| tk_editor_ehr_tarzanehrui_axis_info_label_text | ehr_tkinter | editor_ehr_tarzanehrui | axis_info_label | text |
| tk_editor_ehr_tarzanehrui_canvas_state | ehr_tkinter | editor_ehr_tarzanehrui | canvas | state |
| tk_editor_ehr_tarzanehrui_curve_canvas_state | ehr_tkinter | editor_ehr_tarzanehrui | curve_canvas | state |
| tk_editor_ehr_tarzanehrui_left_state | ehr_tkinter | editor_ehr_tarzanehrui | left | state |
| tk_editor_ehr_tarzanehrui_protocol_box_state | ehr_tkinter | editor_ehr_tarzanehrui | protocol_box | state |
| tk_editor_ehr_tarzanehrui_protocol_canvas_state | ehr_tkinter | editor_ehr_tarzanehrui | protocol_canvas | state |
| tk_editor_ehr_tarzanehrui_protocol_holder_state | ehr_tkinter | editor_ehr_tarzanehrui | protocol_holder | state |
| tk_editor_ehr_tarzanehrui_protocol_label_text | ehr_tkinter | editor_ehr_tarzanehrui | protocol_label | text |
| tk_editor_ehr_tarzanehrui_protocol_text_text | ehr_tkinter | editor_ehr_tarzanehrui | protocol_text | text |
| tk_editor_ehr_tarzanehrui_row_frame_state | ehr_tkinter | editor_ehr_tarzanehrui | row_frame | state |
| tk_editor_ehr_tarzanehrui_save_button_text | ehr_tkinter | editor_ehr_tarzanehrui | save_button | text |
| tk_editor_ehr_tarzanehrui_selected_point_time_label_text | ehr_tkinter | editor_ehr_tarzanehrui | selected_point_time_label | text |
| tk_editor_ehr_tarzanehrui_status_text | ehr_tkinter | editor_ehr_tarzanehrui | status | text |
| tk_editor_ehr_tarzanehrui_step_canvas_state | ehr_tkinter | editor_ehr_tarzanehrui | step_canvas | state |
| tk_editor_ehr_tarzanehrui_take_panel_state | ehr_tkinter | editor_ehr_tarzanehrui | take_panel | state |
| tk_editor_ehr_tarzanehrui_timeline_canvas_state | ehr_tkinter | editor_ehr_tarzanehrui | timeline_canvas | state |
| tk_editor_par_tarzannextionpreview_page_label_text | par_tkinter | editor_par_tarzannextionpreview | page_label | text |
| tk_editor_par_tarzannextionpreview_screen_canvas_state | par_tkinter | editor_par_tarzannextionpreview | screen_canvas | state |
| tk_editor_par_tarzannextionpreview_screen_frame_state | par_tkinter | editor_par_tarzannextionpreview | screen_frame | state |
| tk_editor_par_tarzannextionpreview_status_text | par_tkinter | editor_par_tarzannextionpreview | status | text |
| tk_editor_par_tarzanparapp_body_state | par_tkinter | editor_par_tarzanparapp | body | state |
| tk_editor_par_tarzanparapp_bottom_state | par_tkinter | editor_par_tarzanparapp | bottom | state |
| tk_editor_par_tarzanparapp_clock_text | par_tkinter | editor_par_tarzanparapp | clock | text |
| tk_editor_par_tarzanparapp_footer_state | par_tkinter | editor_par_tarzanparapp | footer | state |
| tk_editor_par_tarzanparapp_header_state | par_tkinter | editor_par_tarzanparapp | header | state |
| tk_editor_par_tarzanparapp_layout_master_state | par_tkinter | editor_par_tarzanparapp | layout_master | state |
| tk_editor_par_tarzanparapp_left_state | par_tkinter | editor_par_tarzanparapp | left | state |
| tk_editor_par_tarzanparapp_middle_bottom_state | par_tkinter | editor_par_tarzanparapp | middle_bottom | state |
| tk_editor_par_tarzanparapp_middle_top_state | par_tkinter | editor_par_tarzanparapp | middle_top | state |
| tk_editor_par_tarzanparapp_mode_label_text | par_tkinter | editor_par_tarzanparapp | mode_label | text |
| tk_editor_par_tarzanparapp_right_state | par_tkinter | editor_par_tarzanparapp | right | state |
| tk_editor_par_tarzanparapp_top_state | par_tkinter | editor_par_tarzanparapp | top | state |
| tk_editor_par_tarzanparpanels_log_text_text | par_tkinter | editor_par_tarzanparpanels | log_text | text |
| tk_editor_par_tarzanparpanels_old_log_text_text | par_tkinter | editor_par_tarzanparpanels_old | log_text | text |
| tk_editor_par_tarzanparpanels_timeline_canvas_state | par_tkinter | editor_par_tarzanparpanels | timeline_canvas | state |
| tk_editor_par_tarzanparwidgets_body_state | par_tkinter | editor_par_tarzanparwidgets | body | state |
| tk_editor_par_tarzanparwidgets_counter_label_text | par_tkinter | editor_par_tarzanparwidgets | counter_label | text |
| tk_editor_par_tarzanparwidgets_motor_canvas_state | par_tkinter | editor_par_tarzanparwidgets | motor_canvas | state |
| tk_editor_tarzanaxissandbox_curve_canvas_state | sandbox_tkinter | editor_tarzanaxissandbox | curve_canvas | state |
| tk_editor_tarzanaxissandbox_step_canvas_state | sandbox_tkinter | editor_tarzanaxissandbox | step_canvas | state |
| tk_editor_tarzanehrtakesandbox_canvas_state | ehr_tkinter | editor_tarzanehrtakesandbox | canvas | state |
| tk_editor_tarzanehrtakesandbox_controls_wrap_state | ehr_tkinter | editor_tarzanehrtakesandbox | controls_wrap | state |
| tk_editor_tarzanehrtakesandbox_protocol_canvas_state | ehr_tkinter | editor_tarzanehrtakesandbox | protocol_canvas | state |
| tk_editor_tarzanehrtakesandbox_protocol_holder_state | ehr_tkinter | editor_tarzanehrtakesandbox | protocol_holder | state |
| tk_editor_tarzanehrtakesandbox_row_frame_state | ehr_tkinter | editor_tarzanehrtakesandbox | row_frame | state |
| tk_editor_tarzanehrtakesandbox_save_button_text | ehr_tkinter | editor_tarzanehrtakesandbox | save_button | text |
| tk_editor_tarzankhr_btn_start_text | khr_tkinter | editor_tarzankhr | btn_start | text |
| tk_editor_tarzankhr_btn_stop_text | khr_tkinter | editor_tarzankhr | btn_stop | text |
| tk_editor_tarzankhr_input_canvas_state | khr_tkinter | editor_tarzankhr | input_canvas | state |
| tk_editor_tarzankhr_khr_canvas_state | khr_tkinter | editor_tarzankhr | khr_canvas | state |
| tk_editor_tarzankhr_output_canvas_state | khr_tkinter | editor_tarzankhr | output_canvas | state |
| tk_editor_tarzankhr_plugin_box_text | khr_tkinter | editor_tarzankhr | plugin_box | text |
| tk_editor_tarzankhr_preview_canvas_state | khr_tkinter | editor_tarzankhr | preview_canvas | state |
| tk_editor_tarzankhr_profile_box_text | khr_tkinter | editor_tarzankhr | profile_box | text |
| tk_editor_tarzankhr_profile_desc_text | khr_tkinter | editor_tarzankhr | profile_desc | text |
| tk_editor_tarzankhr_status_text | khr_tkinter | editor_tarzankhr | status | text |
| tk_editor_tarzantakeprotocollight_canvas_state | par_tkinter | editor_tarzantakeprotocollight | canvas | state |
| tk_editor_tarzantakeprotocollight_protocol_canvas_state | par_tkinter | editor_tarzantakeprotocollight | protocol_canvas | state |
| tk_editor_tarzantakeprotocollight_protocol_holder_state | par_tkinter | editor_tarzantakeprotocollight | protocol_holder | state |
| tk_editor_tarzantakeprotocollight_row_frame_state | par_tkinter | editor_tarzantakeprotocollight | row_frame | state |
| tk_editor_tarzantakeprotocollight_save_button_text | par_tkinter | editor_tarzantakeprotocollight | save_button | text |
| tk_hardware_tarzannextion_tarzannextionsandbox_log_text | sandbox_tkinter | hardware_tarzannextion_tarzannextionsandbox | log | text |
| tk_mechanics_tarzanedytorchoreografiiruchu_global_canvas_state | par_tkinter | mechanics_tarzanedytorchoreografiiruchu | global_canvas | state |
| tk_mechanics_tarzanedytorchoreografiiruchu_scroll_canvas_state | par_tkinter | mechanics_tarzanedytorchoreografiiruchu | scroll_canvas | state |
| tk_mechanics_tarzanedytorchoreografiiruchu_tracks_frame_state | par_tkinter | mechanics_tarzanedytorchoreografiiruchu | tracks_frame | state |
| tk_mechanics_tarzanpanelosi_row1_state | par_tkinter | mechanics_tarzanpanelosi | row1 | state |
| tk_mechanics_tarzanpanelosi_row2_state | par_tkinter | mechanics_tarzanpanelosi | row2 | state |
| tk_mechanics_tarzanpanelosi_row3_state | par_tkinter | mechanics_tarzanpanelosi | row3 | state |
| tk_mechanics_tarzanwykresosi_canvas_state | par_tkinter | mechanics_tarzanwykresosi | canvas | state |
| tk_mechanics_tarzanwykresosi_limit_canvas_state | par_tkinter | mechanics_tarzanwykresosi | limit_canvas | state |
| tk_mechanics_tarzanwykresosi_limit_panel_state | par_tkinter | mechanics_tarzanwykresosi | limit_panel | state |
| tk_mechanics_tarzanwykresosi_meta_label_text | par_tkinter | mechanics_tarzanwykresosi | meta_label | text |
| tk_mechanics_tarzanwykresosi_title_text | par_tkinter | mechanics_tarzanwykresosi | title | text |
| tk_modes_editor_editor_ehr_tarzanaxissandbox_curve_canvas_state | ehr_tkinter | modes_editor_editor_ehr_tarzanaxissandbox | curve_canvas | state |
| tk_modes_editor_editor_ehr_tarzanaxissandbox_step_canvas_state | ehr_tkinter | modes_editor_editor_ehr_tarzanaxissandbox | step_canvas | state |
| tk_modes_editor_editor_ehr_tarzanehrui_axis_info_label_text | ehr_tkinter | modes_editor_editor_ehr_tarzanehrui | axis_info_label | text |
| tk_modes_editor_editor_ehr_tarzanehrui_canvas_state | ehr_tkinter | modes_editor_editor_ehr_tarzanehrui | canvas | state |
| tk_modes_editor_editor_ehr_tarzanehrui_curve_canvas_state | ehr_tkinter | modes_editor_editor_ehr_tarzanehrui | curve_canvas | state |
| tk_modes_editor_editor_ehr_tarzanehrui_left_state | ehr_tkinter | modes_editor_editor_ehr_tarzanehrui | left | state |
| tk_modes_editor_editor_ehr_tarzanehrui_protocol_box_state | ehr_tkinter | modes_editor_editor_ehr_tarzanehrui | protocol_box | state |
| tk_modes_editor_editor_ehr_tarzanehrui_protocol_canvas_state | ehr_tkinter | modes_editor_editor_ehr_tarzanehrui | protocol_canvas | state |
| tk_modes_editor_editor_ehr_tarzanehrui_protocol_holder_state | ehr_tkinter | modes_editor_editor_ehr_tarzanehrui | protocol_holder | state |
| tk_modes_editor_editor_ehr_tarzanehrui_protocol_label_text | ehr_tkinter | modes_editor_editor_ehr_tarzanehrui | protocol_label | text |
| tk_modes_editor_editor_ehr_tarzanehrui_protocol_text_text | ehr_tkinter | modes_editor_editor_ehr_tarzanehrui | protocol_text | text |
| tk_modes_editor_editor_ehr_tarzanehrui_row_frame_state | ehr_tkinter | modes_editor_editor_ehr_tarzanehrui | row_frame | state |
| tk_modes_editor_editor_ehr_tarzanehrui_save_button_text | ehr_tkinter | modes_editor_editor_ehr_tarzanehrui | save_button | text |
| tk_modes_editor_editor_ehr_tarzanehrui_status_text | ehr_tkinter | modes_editor_editor_ehr_tarzanehrui | status | text |
| tk_modes_editor_editor_ehr_tarzanehrui_step_canvas_state | ehr_tkinter | modes_editor_editor_ehr_tarzanehrui | step_canvas | state |
| tk_modes_editor_editor_ehr_tarzanehrui_take_panel_state | ehr_tkinter | modes_editor_editor_ehr_tarzanehrui | take_panel | state |
| tk_modes_editor_editor_ehr_tarzanehrui_timeline_canvas_state | ehr_tkinter | modes_editor_editor_ehr_tarzanehrui | timeline_canvas | state |
| tk_modes_editor_editor_tarzanaxissandbox_curve_canvas_state | sandbox_tkinter | modes_editor_editor_tarzanaxissandbox | curve_canvas | state |
| tk_modes_editor_editor_tarzanaxissandbox_step_canvas_state | sandbox_tkinter | modes_editor_editor_tarzanaxissandbox | step_canvas | state |
| tk_modes_editor_editor_tarzanehrtakesandbox_canvas_state | ehr_tkinter | modes_editor_editor_tarzanehrtakesandbox | canvas | state |
| tk_modes_editor_editor_tarzanehrtakesandbox_controls_wrap_state | ehr_tkinter | modes_editor_editor_tarzanehrtakesandbox | controls_wrap | state |
| tk_modes_editor_editor_tarzanehrtakesandbox_protocol_canvas_state | ehr_tkinter | modes_editor_editor_tarzanehrtakesandbox | protocol_canvas | state |
| tk_modes_editor_editor_tarzanehrtakesandbox_protocol_holder_state | ehr_tkinter | modes_editor_editor_tarzanehrtakesandbox | protocol_holder | state |
| tk_modes_editor_editor_tarzanehrtakesandbox_row_frame_state | ehr_tkinter | modes_editor_editor_tarzanehrtakesandbox | row_frame | state |
| tk_modes_editor_editor_tarzanehrtakesandbox_save_button_text | ehr_tkinter | modes_editor_editor_tarzanehrtakesandbox | save_button | text |
| tk_modes_editor_editor_tarzantakeprotocollight_canvas_state | par_tkinter | modes_editor_editor_tarzantakeprotocollight | canvas | state |
| tk_modes_editor_editor_tarzantakeprotocollight_protocol_canvas_state | par_tkinter | modes_editor_editor_tarzantakeprotocollight | protocol_canvas | state |
| tk_modes_editor_editor_tarzantakeprotocollight_protocol_holder_state | par_tkinter | modes_editor_editor_tarzantakeprotocollight | protocol_holder | state |
| tk_modes_editor_editor_tarzantakeprotocollight_row_frame_state | par_tkinter | modes_editor_editor_tarzantakeprotocollight | row_frame | state |
| tk_modes_editor_editor_tarzantakeprotocollight_save_button_text | par_tkinter | modes_editor_editor_tarzantakeprotocollight | save_button | text |
| tk_modes_editor_ehr_tarzanaxissandbox_curve_canvas_state | ehr_tkinter | modes_editor_ehr_tarzanaxissandbox | curve_canvas | state |
| tk_modes_editor_ehr_tarzanaxissandbox_step_canvas_state | ehr_tkinter | modes_editor_ehr_tarzanaxissandbox | step_canvas | state |
| tk_modes_editor_ehr_tarzanehrui_axis_info_label_text | ehr_tkinter | modes_editor_ehr_tarzanehrui | axis_info_label | text |
| tk_modes_editor_ehr_tarzanehrui_canvas_state | ehr_tkinter | modes_editor_ehr_tarzanehrui | canvas | state |
| tk_modes_editor_ehr_tarzanehrui_curve_canvas_state | ehr_tkinter | modes_editor_ehr_tarzanehrui | curve_canvas | state |
| tk_modes_editor_ehr_tarzanehrui_left_state | ehr_tkinter | modes_editor_ehr_tarzanehrui | left | state |
| tk_modes_editor_ehr_tarzanehrui_protocol_box_state | ehr_tkinter | modes_editor_ehr_tarzanehrui | protocol_box | state |
| tk_modes_editor_ehr_tarzanehrui_protocol_canvas_state | ehr_tkinter | modes_editor_ehr_tarzanehrui | protocol_canvas | state |
| tk_modes_editor_ehr_tarzanehrui_protocol_holder_state | ehr_tkinter | modes_editor_ehr_tarzanehrui | protocol_holder | state |
| tk_modes_editor_ehr_tarzanehrui_protocol_label_text | ehr_tkinter | modes_editor_ehr_tarzanehrui | protocol_label | text |
| tk_modes_editor_ehr_tarzanehrui_protocol_text_text | ehr_tkinter | modes_editor_ehr_tarzanehrui | protocol_text | text |
| tk_modes_editor_ehr_tarzanehrui_row_frame_state | ehr_tkinter | modes_editor_ehr_tarzanehrui | row_frame | state |
| tk_modes_editor_ehr_tarzanehrui_save_button_text | ehr_tkinter | modes_editor_ehr_tarzanehrui | save_button | text |
| tk_modes_editor_ehr_tarzanehrui_selected_point_time_label_text | ehr_tkinter | modes_editor_ehr_tarzanehrui | selected_point_time_label | text |
| tk_modes_editor_ehr_tarzanehrui_status_text | ehr_tkinter | modes_editor_ehr_tarzanehrui | status | text |
| tk_modes_editor_ehr_tarzanehrui_step_canvas_state | ehr_tkinter | modes_editor_ehr_tarzanehrui | step_canvas | state |
| tk_modes_editor_ehr_tarzanehrui_take_panel_state | ehr_tkinter | modes_editor_ehr_tarzanehrui | take_panel | state |
| tk_modes_editor_ehr_tarzanehrui_timeline_canvas_state | ehr_tkinter | modes_editor_ehr_tarzanehrui | timeline_canvas | state |
| tk_modes_editor_par_tarzannextionpreview_page_label_text | par_tkinter | modes_editor_par_tarzannextionpreview | page_label | text |
| tk_modes_editor_par_tarzannextionpreview_screen_canvas_state | par_tkinter | modes_editor_par_tarzannextionpreview | screen_canvas | state |
| tk_modes_editor_par_tarzannextionpreview_screen_frame_state | par_tkinter | modes_editor_par_tarzannextionpreview | screen_frame | state |
| tk_modes_editor_par_tarzannextionpreview_status_text | par_tkinter | modes_editor_par_tarzannextionpreview | status | text |
| tk_modes_editor_par_tarzanparapp_body_state | par_tkinter | modes_editor_par_tarzanparapp | body | state |
| tk_modes_editor_par_tarzanparapp_bottom_state | par_tkinter | modes_editor_par_tarzanparapp | bottom | state |
| tk_modes_editor_par_tarzanparapp_clock_text | par_tkinter | modes_editor_par_tarzanparapp | clock | text |
| tk_modes_editor_par_tarzanparapp_footer_state | par_tkinter | modes_editor_par_tarzanparapp | footer | state |
| tk_modes_editor_par_tarzanparapp_header_state | par_tkinter | modes_editor_par_tarzanparapp | header | state |
| tk_modes_editor_par_tarzanparapp_layout_master_state | par_tkinter | modes_editor_par_tarzanparapp | layout_master | state |
| tk_modes_editor_par_tarzanparapp_left_state | par_tkinter | modes_editor_par_tarzanparapp | left | state |
| tk_modes_editor_par_tarzanparapp_middle_bottom_state | par_tkinter | modes_editor_par_tarzanparapp | middle_bottom | state |
| tk_modes_editor_par_tarzanparapp_middle_top_state | par_tkinter | modes_editor_par_tarzanparapp | middle_top | state |
| tk_modes_editor_par_tarzanparapp_mode_label_text | par_tkinter | modes_editor_par_tarzanparapp | mode_label | text |
| tk_modes_editor_par_tarzanparapp_right_state | par_tkinter | modes_editor_par_tarzanparapp | right | state |
| tk_modes_editor_par_tarzanparapp_top_state | par_tkinter | modes_editor_par_tarzanparapp | top | state |
| tk_modes_editor_par_tarzanparpanels_log_text_text | par_tkinter | modes_editor_par_tarzanparpanels | log_text | text |
| tk_modes_editor_par_tarzanparpanels_old_log_text_text | par_tkinter | modes_editor_par_tarzanparpanels_old | log_text | text |
| tk_modes_editor_par_tarzanparpanels_timeline_canvas_state | par_tkinter | modes_editor_par_tarzanparpanels | timeline_canvas | state |
| tk_modes_editor_par_tarzanparwidgets_body_state | par_tkinter | modes_editor_par_tarzanparwidgets | body | state |
| tk_modes_editor_par_tarzanparwidgets_counter_label_text | par_tkinter | modes_editor_par_tarzanparwidgets | counter_label | text |
| tk_modes_editor_par_tarzanparwidgets_motor_canvas_state | par_tkinter | modes_editor_par_tarzanparwidgets | motor_canvas | state |
| tk_modes_editor_tarzanaxissandbox_curve_canvas_state | sandbox_tkinter | modes_editor_tarzanaxissandbox | curve_canvas | state |
| tk_modes_editor_tarzanaxissandbox_step_canvas_state | sandbox_tkinter | modes_editor_tarzanaxissandbox | step_canvas | state |
| tk_modes_editor_tarzanehrtakesandbox_canvas_state | ehr_tkinter | modes_editor_tarzanehrtakesandbox | canvas | state |
| tk_modes_editor_tarzanehrtakesandbox_controls_wrap_state | ehr_tkinter | modes_editor_tarzanehrtakesandbox | controls_wrap | state |
| tk_modes_editor_tarzanehrtakesandbox_protocol_canvas_state | ehr_tkinter | modes_editor_tarzanehrtakesandbox | protocol_canvas | state |
| tk_modes_editor_tarzanehrtakesandbox_protocol_holder_state | ehr_tkinter | modes_editor_tarzanehrtakesandbox | protocol_holder | state |
| tk_modes_editor_tarzanehrtakesandbox_row_frame_state | ehr_tkinter | modes_editor_tarzanehrtakesandbox | row_frame | state |
| tk_modes_editor_tarzanehrtakesandbox_save_button_text | ehr_tkinter | modes_editor_tarzanehrtakesandbox | save_button | text |
| tk_modes_editor_tarzankhr_btn_start_text | khr_tkinter | modes_editor_tarzankhr | btn_start | text |
| tk_modes_editor_tarzankhr_btn_stop_text | khr_tkinter | modes_editor_tarzankhr | btn_stop | text |
| tk_modes_editor_tarzankhr_input_canvas_state | khr_tkinter | modes_editor_tarzankhr | input_canvas | state |
| tk_modes_editor_tarzankhr_khr_canvas_state | khr_tkinter | modes_editor_tarzankhr | khr_canvas | state |
| tk_modes_editor_tarzankhr_output_canvas_state | khr_tkinter | modes_editor_tarzankhr | output_canvas | state |
| tk_modes_editor_tarzankhr_plugin_box_text | khr_tkinter | modes_editor_tarzankhr | plugin_box | text |
| tk_modes_editor_tarzankhr_preview_canvas_state | khr_tkinter | modes_editor_tarzankhr | preview_canvas | state |
| tk_modes_editor_tarzankhr_profile_box_text | khr_tkinter | modes_editor_tarzankhr | profile_box | text |
| tk_modes_editor_tarzankhr_profile_desc_text | khr_tkinter | modes_editor_tarzankhr | profile_desc | text |
| tk_modes_editor_tarzankhr_status_text | khr_tkinter | modes_editor_tarzankhr | status | text |
| tk_modes_editor_tarzantakeprotocollight_canvas_state | par_tkinter | modes_editor_tarzantakeprotocollight | canvas | state |
| tk_modes_editor_tarzantakeprotocollight_protocol_canvas_state | par_tkinter | modes_editor_tarzantakeprotocollight | protocol_canvas | state |
| tk_modes_editor_tarzantakeprotocollight_protocol_holder_state | par_tkinter | modes_editor_tarzantakeprotocollight | protocol_holder | state |
| tk_modes_editor_tarzantakeprotocollight_row_frame_state | par_tkinter | modes_editor_tarzantakeprotocollight | row_frame | state |
| tk_modes_editor_tarzantakeprotocollight_save_button_text | par_tkinter | modes_editor_tarzantakeprotocollight | save_button | text |
| tk_modes_hardware_tarzannextion_tarzannextionsandbox_log_text | sandbox_tkinter | modes_hardware_tarzannextion_tarzannextionsandbox | log | text |
| tk_vision_tarzanvisionsetup_content_state | par_tkinter | vision_tarzanvisionsetup | content | state |

---

# 4. Pełna lista sygnałów wejściowych

CSV:

```txt
docs/TARZAN_SNAJPER_SIGNALS_FULL.csv
```

| raw_signal | logical_signal |
| --- | --- |
| axis_0_value | axis_0_value |
| axis_1_value | axis_1_value |
| axis_2_value | axis_2_value |
| axis_3_value | axis_3_value |
| axis_4_value | axis_4_value |
| axis_5_value | axis_5_value |
| boot.Event.en | nextion_boot_event_en |
| boot.Event.tim | nextion_boot_event_tim |
| boot.p0.pic | nextion_boot_p0_pic |
| boot.tm0.en | nextion_boot_tm0_en |
| boot.tm0.tim | nextion_boot_tm0_tim |
| boot.va0.val | nextion_boot_va0_val |
| canvas_editor_editor_ehr_tarzanaxissandbox_c_line_line_826_coords | canvas_editor_editor_ehr_tarzanaxissandbox_c_line_line_826_coords |
| canvas_editor_editor_ehr_tarzanaxissandbox_c_line_line_833_coords | canvas_editor_editor_ehr_tarzanaxissandbox_c_line_line_833_coords |
| canvas_editor_editor_ehr_tarzanaxissandbox_c_line_line_840_coords | canvas_editor_editor_ehr_tarzanaxissandbox_c_line_line_840_coords |
| canvas_editor_editor_ehr_tarzanaxissandbox_c_line_line_852_coords | canvas_editor_editor_ehr_tarzanaxissandbox_c_line_line_852_coords |
| canvas_editor_editor_ehr_tarzanaxissandbox_c_line_line_853_coords | canvas_editor_editor_ehr_tarzanaxissandbox_c_line_line_853_coords |
| canvas_editor_editor_ehr_tarzanaxissandbox_c_line_line_867_coords | canvas_editor_editor_ehr_tarzanaxissandbox_c_line_line_867_coords |
| canvas_editor_editor_ehr_tarzanaxissandbox_c_line_line_879_coords | canvas_editor_editor_ehr_tarzanaxissandbox_c_line_line_879_coords |
| canvas_editor_editor_ehr_tarzanaxissandbox_c_line_line_881_coords | canvas_editor_editor_ehr_tarzanaxissandbox_c_line_line_881_coords |
| canvas_editor_editor_ehr_tarzanaxissandbox_c_oval_line_849_coords | canvas_editor_editor_ehr_tarzanaxissandbox_c_oval_line_849_coords |
| canvas_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_812_coords | canvas_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_812_coords |
| canvas_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_819_coords | canvas_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_819_coords |
| canvas_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_820_coords | canvas_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_820_coords |
| canvas_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_821_coords | canvas_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_821_coords |
| canvas_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_861_coords | canvas_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_861_coords |
| canvas_editor_editor_ehr_tarzanaxissandbox_c_text_line_827_text | canvas_editor_editor_ehr_tarzanaxissandbox_c_text_line_827_text |
| canvas_editor_editor_ehr_tarzanaxissandbox_c_text_line_834_text | canvas_editor_editor_ehr_tarzanaxissandbox_c_text_line_834_text |
| canvas_editor_editor_ehr_tarzanaxissandbox_c_text_line_854_text | canvas_editor_editor_ehr_tarzanaxissandbox_c_text_line_854_text |
| canvas_editor_editor_ehr_tarzanaxissandbox_c_text_line_855_text | canvas_editor_editor_ehr_tarzanaxissandbox_c_text_line_855_text |
| canvas_editor_editor_ehr_tarzanaxissandbox_c_text_line_882_text | canvas_editor_editor_ehr_tarzanaxissandbox_c_text_line_882_text |
| canvas_editor_editor_ehr_tarzanaxissandbox_c_text_line_883_text | canvas_editor_editor_ehr_tarzanaxissandbox_c_text_line_883_text |
| canvas_editor_editor_ehr_tarzanehrui_c_image_line_2734_coords | canvas_editor_editor_ehr_tarzanehrui_c_image_line_2734_coords |
| canvas_editor_editor_ehr_tarzanehrui_c_line_line_1910_coords | canvas_editor_editor_ehr_tarzanehrui_c_line_line_1910_coords |
| canvas_editor_editor_ehr_tarzanehrui_c_line_line_1919_coords | canvas_editor_editor_ehr_tarzanehrui_c_line_line_1919_coords |
| canvas_editor_editor_ehr_tarzanehrui_c_line_line_1930_coords | canvas_editor_editor_ehr_tarzanehrui_c_line_line_1930_coords |
| canvas_editor_editor_ehr_tarzanehrui_c_line_line_1937_coords | canvas_editor_editor_ehr_tarzanehrui_c_line_line_1937_coords |
| canvas_editor_editor_ehr_tarzanehrui_c_line_line_1951_coords | canvas_editor_editor_ehr_tarzanehrui_c_line_line_1951_coords |
| canvas_editor_editor_ehr_tarzanehrui_c_line_line_1952_coords | canvas_editor_editor_ehr_tarzanehrui_c_line_line_1952_coords |
| canvas_editor_editor_ehr_tarzanehrui_c_line_line_1966_coords | canvas_editor_editor_ehr_tarzanehrui_c_line_line_1966_coords |
| canvas_editor_editor_ehr_tarzanehrui_c_line_line_1978_coords | canvas_editor_editor_ehr_tarzanehrui_c_line_line_1978_coords |
| canvas_editor_editor_ehr_tarzanehrui_c_line_line_1980_coords | canvas_editor_editor_ehr_tarzanehrui_c_line_line_1980_coords |
| canvas_editor_editor_ehr_tarzanehrui_c_line_line_2697_coords | canvas_editor_editor_ehr_tarzanehrui_c_line_line_2697_coords |
| canvas_editor_editor_ehr_tarzanehrui_c_line_line_2707_coords | canvas_editor_editor_ehr_tarzanehrui_c_line_line_2707_coords |
| canvas_editor_editor_ehr_tarzanehrui_c_line_line_2710_coords | canvas_editor_editor_ehr_tarzanehrui_c_line_line_2710_coords |
| canvas_editor_editor_ehr_tarzanehrui_c_line_line_2749_coords | canvas_editor_editor_ehr_tarzanehrui_c_line_line_2749_coords |
| canvas_editor_editor_ehr_tarzanehrui_c_line_line_2757_coords | canvas_editor_editor_ehr_tarzanehrui_c_line_line_2757_coords |
| canvas_editor_editor_ehr_tarzanehrui_c_line_line_2765_coords | canvas_editor_editor_ehr_tarzanehrui_c_line_line_2765_coords |
| canvas_editor_editor_ehr_tarzanehrui_c_line_line_2778_coords | canvas_editor_editor_ehr_tarzanehrui_c_line_line_2778_coords |
| canvas_editor_editor_ehr_tarzanehrui_c_line_line_2801_coords | canvas_editor_editor_ehr_tarzanehrui_c_line_line_2801_coords |
| canvas_editor_editor_ehr_tarzanehrui_c_oval_line_1947_coords | canvas_editor_editor_ehr_tarzanehrui_c_oval_line_1947_coords |
| canvas_editor_editor_ehr_tarzanehrui_c_oval_line_2792_coords | canvas_editor_editor_ehr_tarzanehrui_c_oval_line_2792_coords |
| canvas_editor_editor_ehr_tarzanehrui_c_oval_line_2794_coords | canvas_editor_editor_ehr_tarzanehrui_c_oval_line_2794_coords |
| canvas_editor_editor_ehr_tarzanehrui_c_polygon_line_2808_coords | canvas_editor_editor_ehr_tarzanehrui_c_polygon_line_2808_coords |
| canvas_editor_editor_ehr_tarzanehrui_c_rectangle_line_1893_coords | canvas_editor_editor_ehr_tarzanehrui_c_rectangle_line_1893_coords |
| canvas_editor_editor_ehr_tarzanehrui_c_rectangle_line_1901_coords | canvas_editor_editor_ehr_tarzanehrui_c_rectangle_line_1901_coords |
| canvas_editor_editor_ehr_tarzanehrui_c_rectangle_line_1902_coords | canvas_editor_editor_ehr_tarzanehrui_c_rectangle_line_1902_coords |
| canvas_editor_editor_ehr_tarzanehrui_c_rectangle_line_1903_coords | canvas_editor_editor_ehr_tarzanehrui_c_rectangle_line_1903_coords |
| canvas_editor_editor_ehr_tarzanehrui_c_rectangle_line_1960_coords | canvas_editor_editor_ehr_tarzanehrui_c_rectangle_line_1960_coords |
| canvas_editor_editor_ehr_tarzanehrui_c_rectangle_line_2688_coords | canvas_editor_editor_ehr_tarzanehrui_c_rectangle_line_2688_coords |
| canvas_editor_editor_ehr_tarzanehrui_c_rectangle_line_2705_coords | canvas_editor_editor_ehr_tarzanehrui_c_rectangle_line_2705_coords |
| canvas_editor_editor_ehr_tarzanehrui_c_rectangle_line_2790_coords | canvas_editor_editor_ehr_tarzanehrui_c_rectangle_line_2790_coords |
| canvas_editor_editor_ehr_tarzanehrui_c_rectangle_line_2800_coords | canvas_editor_editor_ehr_tarzanehrui_c_rectangle_line_2800_coords |
| canvas_editor_editor_ehr_tarzanehrui_c_text_line_1911_text | canvas_editor_editor_ehr_tarzanehrui_c_text_line_1911_text |
| canvas_editor_editor_ehr_tarzanehrui_c_text_line_1920_text | canvas_editor_editor_ehr_tarzanehrui_c_text_line_1920_text |
| canvas_editor_editor_ehr_tarzanehrui_c_text_line_1953_text | canvas_editor_editor_ehr_tarzanehrui_c_text_line_1953_text |
| canvas_editor_editor_ehr_tarzanehrui_c_text_line_1954_text | canvas_editor_editor_ehr_tarzanehrui_c_text_line_1954_text |
| canvas_editor_editor_ehr_tarzanehrui_c_text_line_1981_text | canvas_editor_editor_ehr_tarzanehrui_c_text_line_1981_text |
| canvas_editor_editor_ehr_tarzanehrui_c_text_line_1982_text | canvas_editor_editor_ehr_tarzanehrui_c_text_line_1982_text |
| canvas_editor_editor_ehr_tarzanehrui_c_text_line_2720_text | canvas_editor_editor_ehr_tarzanehrui_c_text_line_2720_text |
| canvas_editor_editor_ehr_tarzanehrui_c_text_line_2727_text | canvas_editor_editor_ehr_tarzanehrui_c_text_line_2727_text |
| canvas_editor_editor_ehr_tarzanehrui_c_text_line_2736_text | canvas_editor_editor_ehr_tarzanehrui_c_text_line_2736_text |
| canvas_editor_editor_ehr_tarzanehrui_c_text_line_2809_text | canvas_editor_editor_ehr_tarzanehrui_c_text_line_2809_text |
| canvas_editor_editor_ehr_tarzanehrui_c_text_line_2816_text | canvas_editor_editor_ehr_tarzanehrui_c_text_line_2816_text |
| canvas_editor_editor_ehr_tarzanehrui_canvas_image_line_712_coords | canvas_editor_editor_ehr_tarzanehrui_canvas_image_line_712_coords |
| canvas_editor_editor_ehr_tarzanehrui_canvas_rectangle_line_1244_coords | canvas_editor_editor_ehr_tarzanehrui_canvas_rectangle_line_1244_coords |
| canvas_editor_editor_ehr_tarzanehrui_canvas_window_line_1172_coords | canvas_editor_editor_ehr_tarzanehrui_canvas_window_line_1172_coords |
| canvas_editor_editor_ehr_tarzanehrui_item_text | canvas_editor_editor_ehr_tarzanehrui_item_text |
| canvas_editor_editor_ehr_tarzanehrui_protocol_canvas_rectangle_line_962_coords | canvas_editor_editor_ehr_tarzanehrui_protocol_canvas_rectangle_line_962_coords |
| canvas_editor_editor_ehr_tarzanehrui_protocol_canvas_rectangle_line_963_coords | canvas_editor_editor_ehr_tarzanehrui_protocol_canvas_rectangle_line_963_coords |
| canvas_editor_editor_ehr_tarzanehrui_row_window_coords | canvas_editor_editor_ehr_tarzanehrui_row_window_coords |
| canvas_editor_editor_ehr_tarzanehrui_save_button_window_coords | canvas_editor_editor_ehr_tarzanehrui_save_button_window_coords |
| canvas_editor_editor_tarzanaxissandbox_c_line_line_826_coords | canvas_editor_editor_tarzanaxissandbox_c_line_line_826_coords |
| canvas_editor_editor_tarzanaxissandbox_c_line_line_833_coords | canvas_editor_editor_tarzanaxissandbox_c_line_line_833_coords |
| canvas_editor_editor_tarzanaxissandbox_c_line_line_852_coords | canvas_editor_editor_tarzanaxissandbox_c_line_line_852_coords |
| canvas_editor_editor_tarzanaxissandbox_c_line_line_859_coords | canvas_editor_editor_tarzanaxissandbox_c_line_line_859_coords |
| canvas_editor_editor_tarzanaxissandbox_c_line_line_871_coords | canvas_editor_editor_tarzanaxissandbox_c_line_line_871_coords |
| canvas_editor_editor_tarzanaxissandbox_c_line_line_872_coords | canvas_editor_editor_tarzanaxissandbox_c_line_line_872_coords |
| canvas_editor_editor_tarzanaxissandbox_c_line_line_886_coords | canvas_editor_editor_tarzanaxissandbox_c_line_line_886_coords |
| canvas_editor_editor_tarzanaxissandbox_c_line_line_898_coords | canvas_editor_editor_tarzanaxissandbox_c_line_line_898_coords |
| canvas_editor_editor_tarzanaxissandbox_c_line_line_900_coords | canvas_editor_editor_tarzanaxissandbox_c_line_line_900_coords |
| canvas_editor_editor_tarzanaxissandbox_c_oval_line_868_coords | canvas_editor_editor_tarzanaxissandbox_c_oval_line_868_coords |
| canvas_editor_editor_tarzanaxissandbox_c_rectangle_line_812_coords | canvas_editor_editor_tarzanaxissandbox_c_rectangle_line_812_coords |
| canvas_editor_editor_tarzanaxissandbox_c_rectangle_line_819_coords | canvas_editor_editor_tarzanaxissandbox_c_rectangle_line_819_coords |
| canvas_editor_editor_tarzanaxissandbox_c_rectangle_line_820_coords | canvas_editor_editor_tarzanaxissandbox_c_rectangle_line_820_coords |
| canvas_editor_editor_tarzanaxissandbox_c_rectangle_line_821_coords | canvas_editor_editor_tarzanaxissandbox_c_rectangle_line_821_coords |
| canvas_editor_editor_tarzanaxissandbox_c_rectangle_line_880_coords | canvas_editor_editor_tarzanaxissandbox_c_rectangle_line_880_coords |
| canvas_editor_editor_tarzanaxissandbox_c_text_line_827_text | canvas_editor_editor_tarzanaxissandbox_c_text_line_827_text |
| canvas_editor_editor_tarzanaxissandbox_c_text_line_834_text | canvas_editor_editor_tarzanaxissandbox_c_text_line_834_text |
| canvas_editor_editor_tarzanaxissandbox_c_text_line_873_text | canvas_editor_editor_tarzanaxissandbox_c_text_line_873_text |
| canvas_editor_editor_tarzanaxissandbox_c_text_line_874_text | canvas_editor_editor_tarzanaxissandbox_c_text_line_874_text |
| canvas_editor_editor_tarzanaxissandbox_c_text_line_901_text | canvas_editor_editor_tarzanaxissandbox_c_text_line_901_text |
| canvas_editor_editor_tarzanaxissandbox_c_text_line_902_text | canvas_editor_editor_tarzanaxissandbox_c_text_line_902_text |
| canvas_editor_editor_tarzanehrtakesandbox_canvas_image_line_553_coords | canvas_editor_editor_tarzanehrtakesandbox_canvas_image_line_553_coords |
| canvas_editor_editor_tarzanehrtakesandbox_item_text | canvas_editor_editor_tarzanehrtakesandbox_item_text |
| canvas_editor_editor_tarzanehrtakesandbox_protocol_canvas_rectangle_line_1057_coords | canvas_editor_editor_tarzanehrtakesandbox_protocol_canvas_rectangle_line_1057_coords |
| canvas_editor_editor_tarzanehrtakesandbox_protocol_canvas_rectangle_line_1058_coords | canvas_editor_editor_tarzanehrtakesandbox_protocol_canvas_rectangle_line_1058_coords |
| canvas_editor_editor_tarzanehrtakesandbox_protocol_title_id_text | canvas_editor_editor_tarzanehrtakesandbox_protocol_title_id_text |
| canvas_editor_editor_tarzanehrtakesandbox_row_window_coords | canvas_editor_editor_tarzanehrtakesandbox_row_window_coords |
| canvas_editor_editor_tarzanehrtakesandbox_save_button_window_coords | canvas_editor_editor_tarzanehrtakesandbox_save_button_window_coords |
| canvas_editor_editor_tarzantakeprotocollight_canvas_image_line_860_coords | canvas_editor_editor_tarzantakeprotocollight_canvas_image_line_860_coords |
| canvas_editor_editor_tarzantakeprotocollight_item_text | canvas_editor_editor_tarzantakeprotocollight_item_text |
| canvas_editor_editor_tarzantakeprotocollight_protocol_canvas_rectangle_line_1215_coords | canvas_editor_editor_tarzantakeprotocollight_protocol_canvas_rectangle_line_1215_coords |
| canvas_editor_editor_tarzantakeprotocollight_protocol_canvas_rectangle_line_1216_coords | canvas_editor_editor_tarzantakeprotocollight_protocol_canvas_rectangle_line_1216_coords |
| canvas_editor_editor_tarzantakeprotocollight_protocol_title_id_text | canvas_editor_editor_tarzantakeprotocollight_protocol_title_id_text |
| canvas_editor_editor_tarzantakeprotocollight_row_window_coords | canvas_editor_editor_tarzantakeprotocollight_row_window_coords |
| canvas_editor_editor_tarzantakeprotocollight_save_button_window_coords | canvas_editor_editor_tarzantakeprotocollight_save_button_window_coords |
| canvas_editor_ehr_tarzanaxissandbox_c_line_line_827_coords | canvas_editor_ehr_tarzanaxissandbox_c_line_line_827_coords |
| canvas_editor_ehr_tarzanaxissandbox_c_line_line_834_coords | canvas_editor_ehr_tarzanaxissandbox_c_line_line_834_coords |
| canvas_editor_ehr_tarzanaxissandbox_c_line_line_841_coords | canvas_editor_ehr_tarzanaxissandbox_c_line_line_841_coords |
| canvas_editor_ehr_tarzanaxissandbox_c_line_line_853_coords | canvas_editor_ehr_tarzanaxissandbox_c_line_line_853_coords |
| canvas_editor_ehr_tarzanaxissandbox_c_line_line_854_coords | canvas_editor_ehr_tarzanaxissandbox_c_line_line_854_coords |
| canvas_editor_ehr_tarzanaxissandbox_c_line_line_868_coords | canvas_editor_ehr_tarzanaxissandbox_c_line_line_868_coords |
| canvas_editor_ehr_tarzanaxissandbox_c_line_line_880_coords | canvas_editor_ehr_tarzanaxissandbox_c_line_line_880_coords |
| canvas_editor_ehr_tarzanaxissandbox_c_line_line_882_coords | canvas_editor_ehr_tarzanaxissandbox_c_line_line_882_coords |
| canvas_editor_ehr_tarzanaxissandbox_c_oval_line_850_coords | canvas_editor_ehr_tarzanaxissandbox_c_oval_line_850_coords |
| canvas_editor_ehr_tarzanaxissandbox_c_rectangle_line_813_coords | canvas_editor_ehr_tarzanaxissandbox_c_rectangle_line_813_coords |
| canvas_editor_ehr_tarzanaxissandbox_c_rectangle_line_820_coords | canvas_editor_ehr_tarzanaxissandbox_c_rectangle_line_820_coords |
| canvas_editor_ehr_tarzanaxissandbox_c_rectangle_line_821_coords | canvas_editor_ehr_tarzanaxissandbox_c_rectangle_line_821_coords |
| canvas_editor_ehr_tarzanaxissandbox_c_rectangle_line_822_coords | canvas_editor_ehr_tarzanaxissandbox_c_rectangle_line_822_coords |
| canvas_editor_ehr_tarzanaxissandbox_c_rectangle_line_862_coords | canvas_editor_ehr_tarzanaxissandbox_c_rectangle_line_862_coords |
| canvas_editor_ehr_tarzanaxissandbox_c_text_line_828_text | canvas_editor_ehr_tarzanaxissandbox_c_text_line_828_text |
| canvas_editor_ehr_tarzanaxissandbox_c_text_line_835_text | canvas_editor_ehr_tarzanaxissandbox_c_text_line_835_text |
| canvas_editor_ehr_tarzanaxissandbox_c_text_line_855_text | canvas_editor_ehr_tarzanaxissandbox_c_text_line_855_text |
| canvas_editor_ehr_tarzanaxissandbox_c_text_line_856_text | canvas_editor_ehr_tarzanaxissandbox_c_text_line_856_text |
| canvas_editor_ehr_tarzanaxissandbox_c_text_line_883_text | canvas_editor_ehr_tarzanaxissandbox_c_text_line_883_text |
| canvas_editor_ehr_tarzanaxissandbox_c_text_line_884_text | canvas_editor_ehr_tarzanaxissandbox_c_text_line_884_text |
| canvas_editor_ehr_tarzanehrui_c_image_line_3130_coords | canvas_editor_ehr_tarzanehrui_c_image_line_3130_coords |
| canvas_editor_ehr_tarzanehrui_c_line_line_1993_coords | canvas_editor_ehr_tarzanehrui_c_line_line_1993_coords |
| canvas_editor_ehr_tarzanehrui_c_line_line_2002_coords | canvas_editor_ehr_tarzanehrui_c_line_line_2002_coords |
| canvas_editor_ehr_tarzanehrui_c_line_line_2013_coords | canvas_editor_ehr_tarzanehrui_c_line_line_2013_coords |
| canvas_editor_ehr_tarzanehrui_c_line_line_2020_coords | canvas_editor_ehr_tarzanehrui_c_line_line_2020_coords |
| canvas_editor_ehr_tarzanehrui_c_line_line_2048_coords | canvas_editor_ehr_tarzanehrui_c_line_line_2048_coords |
| canvas_editor_ehr_tarzanehrui_c_line_line_2049_coords | canvas_editor_ehr_tarzanehrui_c_line_line_2049_coords |
| canvas_editor_ehr_tarzanehrui_c_line_line_2068_coords | canvas_editor_ehr_tarzanehrui_c_line_line_2068_coords |
| canvas_editor_ehr_tarzanehrui_c_line_line_2080_coords | canvas_editor_ehr_tarzanehrui_c_line_line_2080_coords |
| canvas_editor_ehr_tarzanehrui_c_line_line_2082_coords | canvas_editor_ehr_tarzanehrui_c_line_line_2082_coords |
| canvas_editor_ehr_tarzanehrui_c_line_line_3081_coords | canvas_editor_ehr_tarzanehrui_c_line_line_3081_coords |
| canvas_editor_ehr_tarzanehrui_c_line_line_3102_coords | canvas_editor_ehr_tarzanehrui_c_line_line_3102_coords |
| canvas_editor_ehr_tarzanehrui_c_line_line_3105_coords | canvas_editor_ehr_tarzanehrui_c_line_line_3105_coords |
| canvas_editor_ehr_tarzanehrui_c_line_line_3145_coords | canvas_editor_ehr_tarzanehrui_c_line_line_3145_coords |
| canvas_editor_ehr_tarzanehrui_c_line_line_3153_coords | canvas_editor_ehr_tarzanehrui_c_line_line_3153_coords |
| canvas_editor_ehr_tarzanehrui_c_line_line_3161_coords | canvas_editor_ehr_tarzanehrui_c_line_line_3161_coords |
| canvas_editor_ehr_tarzanehrui_c_line_line_3176_coords | canvas_editor_ehr_tarzanehrui_c_line_line_3176_coords |
| canvas_editor_ehr_tarzanehrui_c_line_line_3217_coords | canvas_editor_ehr_tarzanehrui_c_line_line_3217_coords |
| canvas_editor_ehr_tarzanehrui_c_line_line_3231_coords | canvas_editor_ehr_tarzanehrui_c_line_line_3231_coords |
| canvas_editor_ehr_tarzanehrui_c_oval_line_2044_coords | canvas_editor_ehr_tarzanehrui_c_oval_line_2044_coords |
| canvas_editor_ehr_tarzanehrui_c_oval_line_3194_coords | canvas_editor_ehr_tarzanehrui_c_oval_line_3194_coords |
| canvas_editor_ehr_tarzanehrui_c_oval_line_3210_coords | canvas_editor_ehr_tarzanehrui_c_oval_line_3210_coords |
| canvas_editor_ehr_tarzanehrui_c_polygon_line_3226_coords | canvas_editor_ehr_tarzanehrui_c_polygon_line_3226_coords |
| canvas_editor_ehr_tarzanehrui_c_rectangle_line_1976_coords | canvas_editor_ehr_tarzanehrui_c_rectangle_line_1976_coords |
| canvas_editor_ehr_tarzanehrui_c_rectangle_line_1984_coords | canvas_editor_ehr_tarzanehrui_c_rectangle_line_1984_coords |
| canvas_editor_ehr_tarzanehrui_c_rectangle_line_1985_coords | canvas_editor_ehr_tarzanehrui_c_rectangle_line_1985_coords |
| canvas_editor_ehr_tarzanehrui_c_rectangle_line_1986_coords | canvas_editor_ehr_tarzanehrui_c_rectangle_line_1986_coords |
| canvas_editor_ehr_tarzanehrui_c_rectangle_line_2062_coords | canvas_editor_ehr_tarzanehrui_c_rectangle_line_2062_coords |
| canvas_editor_ehr_tarzanehrui_c_rectangle_line_3072_coords | canvas_editor_ehr_tarzanehrui_c_rectangle_line_3072_coords |
| canvas_editor_ehr_tarzanehrui_c_rectangle_line_3100_coords | canvas_editor_ehr_tarzanehrui_c_rectangle_line_3100_coords |
| canvas_editor_ehr_tarzanehrui_c_rectangle_line_3192_coords | canvas_editor_ehr_tarzanehrui_c_rectangle_line_3192_coords |
| canvas_editor_ehr_tarzanehrui_c_rectangle_line_3216_coords | canvas_editor_ehr_tarzanehrui_c_rectangle_line_3216_coords |
| canvas_editor_ehr_tarzanehrui_c_text_line_1994_text | canvas_editor_ehr_tarzanehrui_c_text_line_1994_text |
| canvas_editor_ehr_tarzanehrui_c_text_line_2003_text | canvas_editor_ehr_tarzanehrui_c_text_line_2003_text |
| canvas_editor_ehr_tarzanehrui_c_text_line_2050_text | canvas_editor_ehr_tarzanehrui_c_text_line_2050_text |
| canvas_editor_ehr_tarzanehrui_c_text_line_2051_text | canvas_editor_ehr_tarzanehrui_c_text_line_2051_text |
| canvas_editor_ehr_tarzanehrui_c_text_line_2083_text | canvas_editor_ehr_tarzanehrui_c_text_line_2083_text |
| canvas_editor_ehr_tarzanehrui_c_text_line_2084_text | canvas_editor_ehr_tarzanehrui_c_text_line_2084_text |
| canvas_editor_ehr_tarzanehrui_c_text_line_3115_text | canvas_editor_ehr_tarzanehrui_c_text_line_3115_text |
| canvas_editor_ehr_tarzanehrui_c_text_line_3122_text | canvas_editor_ehr_tarzanehrui_c_text_line_3122_text |
| canvas_editor_ehr_tarzanehrui_c_text_line_3132_text | canvas_editor_ehr_tarzanehrui_c_text_line_3132_text |
| canvas_editor_ehr_tarzanehrui_c_text_line_3228_text | canvas_editor_ehr_tarzanehrui_c_text_line_3228_text |
| canvas_editor_ehr_tarzanehrui_c_text_line_3239_text | canvas_editor_ehr_tarzanehrui_c_text_line_3239_text |
| canvas_editor_ehr_tarzanehrui_canvas_image_line_760_coords | canvas_editor_ehr_tarzanehrui_canvas_image_line_760_coords |
| canvas_editor_ehr_tarzanehrui_canvas_rectangle_line_1300_coords | canvas_editor_ehr_tarzanehrui_canvas_rectangle_line_1300_coords |
| canvas_editor_ehr_tarzanehrui_canvas_window_line_1226_coords | canvas_editor_ehr_tarzanehrui_canvas_window_line_1226_coords |
| canvas_editor_ehr_tarzanehrui_item_text | canvas_editor_ehr_tarzanehrui_item_text |
| canvas_editor_ehr_tarzanehrui_protocol_canvas_rectangle_line_1010_coords | canvas_editor_ehr_tarzanehrui_protocol_canvas_rectangle_line_1010_coords |
| canvas_editor_ehr_tarzanehrui_protocol_canvas_rectangle_line_1011_coords | canvas_editor_ehr_tarzanehrui_protocol_canvas_rectangle_line_1011_coords |
| canvas_editor_ehr_tarzanehrui_row_window_coords | canvas_editor_ehr_tarzanehrui_row_window_coords |
| canvas_editor_ehr_tarzanehrui_save_button_window_coords | canvas_editor_ehr_tarzanehrui_save_button_window_coords |
| canvas_editor_par_tarzannextionpreview_edit_window_coords | canvas_editor_par_tarzannextionpreview_edit_window_coords |
| canvas_editor_par_tarzannextionpreview_screen_canvas_image_line_591_coords | canvas_editor_par_tarzannextionpreview_screen_canvas_image_line_591_coords |
| canvas_editor_par_tarzannextionpreview_screen_canvas_image_line_623_coords | canvas_editor_par_tarzannextionpreview_screen_canvas_image_line_623_coords |
| canvas_editor_par_tarzannextionpreview_screen_canvas_image_line_640_coords | canvas_editor_par_tarzannextionpreview_screen_canvas_image_line_640_coords |
| canvas_editor_par_tarzannextionpreview_screen_canvas_image_line_692_coords | canvas_editor_par_tarzannextionpreview_screen_canvas_image_line_692_coords |
| canvas_editor_par_tarzannextionpreview_screen_canvas_image_line_718_coords | canvas_editor_par_tarzannextionpreview_screen_canvas_image_line_718_coords |
| canvas_editor_par_tarzannextionpreview_screen_canvas_line_line_415_coords | canvas_editor_par_tarzannextionpreview_screen_canvas_line_line_415_coords |
| canvas_editor_par_tarzannextionpreview_screen_canvas_line_line_432_coords | canvas_editor_par_tarzannextionpreview_screen_canvas_line_line_432_coords |
| canvas_editor_par_tarzannextionpreview_screen_canvas_line_line_445_coords | canvas_editor_par_tarzannextionpreview_screen_canvas_line_line_445_coords |
| canvas_editor_par_tarzannextionpreview_screen_canvas_line_line_737_coords | canvas_editor_par_tarzannextionpreview_screen_canvas_line_line_737_coords |
| canvas_editor_par_tarzannextionpreview_screen_canvas_line_line_738_coords | canvas_editor_par_tarzannextionpreview_screen_canvas_line_line_738_coords |
| canvas_editor_par_tarzannextionpreview_screen_canvas_line_line_818_coords | canvas_editor_par_tarzannextionpreview_screen_canvas_line_line_818_coords |
| canvas_editor_par_tarzannextionpreview_screen_canvas_oval_line_740_coords | canvas_editor_par_tarzannextionpreview_screen_canvas_oval_line_740_coords |
| canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_394_coords | canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_394_coords |
| canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_512_coords | canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_512_coords |
| canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_527_coords | canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_527_coords |
| canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_593_coords | canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_593_coords |
| canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_625_coords | canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_625_coords |
| canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_642_coords | canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_642_coords |
| canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_785_coords | canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_785_coords |
| canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_787_coords | canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_787_coords |
| canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_790_coords | canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_790_coords |
| canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_797_coords | canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_797_coords |
| canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_815_coords | canvas_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_815_coords |
| canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_400_text | canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_400_text |
| canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_414_text | canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_414_text |
| canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_421_text | canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_421_text |
| canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_425_text | canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_425_text |
| canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_466_text | canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_466_text |
| canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_483_text | canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_483_text |
| canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_518_text | canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_518_text |
| canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_529_text | canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_529_text |
| canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_594_text | canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_594_text |
| canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_603_text | canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_603_text |
| canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_626_text | canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_626_text |
| canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_643_text | canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_643_text |
| canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_791_text | canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_791_text |
| canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_798_text | canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_798_text |
| canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_799_text | canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_799_text |
| canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_816_text | canvas_editor_par_tarzannextionpreview_screen_canvas_text_line_816_text |
| canvas_editor_par_tarzanparapp_canvas_oval_line_1309_coords | canvas_editor_par_tarzanparapp_canvas_oval_line_1309_coords |
| canvas_editor_par_tarzanparapp_canvas_oval_line_1402_coords | canvas_editor_par_tarzanparapp_canvas_oval_line_1402_coords |
| canvas_editor_par_tarzanparapp_canvas_rectangle_line_1286_coords | canvas_editor_par_tarzanparapp_canvas_rectangle_line_1286_coords |
| canvas_editor_par_tarzanparapp_canvas_rectangle_line_1303_coords | canvas_editor_par_tarzanparapp_canvas_rectangle_line_1303_coords |
| canvas_editor_par_tarzanparapp_canvas_rectangle_line_1314_coords | canvas_editor_par_tarzanparapp_canvas_rectangle_line_1314_coords |
| canvas_editor_par_tarzanparapp_canvas_rectangle_line_1315_coords | canvas_editor_par_tarzanparapp_canvas_rectangle_line_1315_coords |
| canvas_editor_par_tarzanparapp_canvas_rectangle_line_1316_coords | canvas_editor_par_tarzanparapp_canvas_rectangle_line_1316_coords |
| canvas_editor_par_tarzanparapp_canvas_rectangle_line_1329_coords | canvas_editor_par_tarzanparapp_canvas_rectangle_line_1329_coords |
| canvas_editor_par_tarzanparapp_canvas_rectangle_line_1387_coords | canvas_editor_par_tarzanparapp_canvas_rectangle_line_1387_coords |
| canvas_editor_par_tarzanparapp_canvas_rectangle_line_1414_coords | canvas_editor_par_tarzanparapp_canvas_rectangle_line_1414_coords |
| canvas_editor_par_tarzanparapp_canvas_rectangle_line_1415_coords | canvas_editor_par_tarzanparapp_canvas_rectangle_line_1415_coords |
| canvas_editor_par_tarzanparapp_canvas_rectangle_line_1416_coords | canvas_editor_par_tarzanparapp_canvas_rectangle_line_1416_coords |
| canvas_editor_par_tarzanparapp_canvas_rectangle_line_1431_coords | canvas_editor_par_tarzanparapp_canvas_rectangle_line_1431_coords |
| canvas_editor_par_tarzanparapp_canvas_text_line_1310_text | canvas_editor_par_tarzanparapp_canvas_text_line_1310_text |
| canvas_editor_par_tarzanparapp_canvas_text_line_1434_text | canvas_editor_par_tarzanparapp_canvas_text_line_1434_text |
| canvas_editor_par_tarzanparapp_canvas_text_line_1451_text | canvas_editor_par_tarzanparapp_canvas_text_line_1451_text |
| canvas_editor_par_tarzanparapp_canvas_text_line_1455_text | canvas_editor_par_tarzanparapp_canvas_text_line_1455_text |
| canvas_editor_par_tarzanparapp_led_oval_line_485_coords | canvas_editor_par_tarzanparapp_led_oval_line_485_coords |
| canvas_editor_par_tarzanparapp_panel_canvas_window_line_1076_coords | canvas_editor_par_tarzanparapp_panel_canvas_window_line_1076_coords |
| canvas_editor_par_tarzanparapp_text_id_text | canvas_editor_par_tarzanparapp_text_id_text |
| canvas_editor_par_tarzanparpanels_can_image_line_1306_coords | canvas_editor_par_tarzanparpanels_can_image_line_1306_coords |
| canvas_editor_par_tarzanparpanels_can_line_line_1298_coords | canvas_editor_par_tarzanparpanels_can_line_line_1298_coords |
| canvas_editor_par_tarzanparpanels_can_line_line_1299_coords | canvas_editor_par_tarzanparpanels_can_line_line_1299_coords |
| canvas_editor_par_tarzanparpanels_can_line_line_1304_coords | canvas_editor_par_tarzanparpanels_can_line_line_1304_coords |
| canvas_editor_par_tarzanparpanels_can_line_line_1311_coords | canvas_editor_par_tarzanparpanels_can_line_line_1311_coords |
| canvas_editor_par_tarzanparpanels_can_line_line_1326_coords | canvas_editor_par_tarzanparpanels_can_line_line_1326_coords |
| canvas_editor_par_tarzanparpanels_can_line_line_1327_coords | canvas_editor_par_tarzanparpanels_can_line_line_1327_coords |
| canvas_editor_par_tarzanparpanels_can_line_line_510_coords | canvas_editor_par_tarzanparpanels_can_line_line_510_coords |
| canvas_editor_par_tarzanparpanels_can_line_line_664_coords | canvas_editor_par_tarzanparpanels_can_line_line_664_coords |
| canvas_editor_par_tarzanparpanels_can_line_line_665_coords | canvas_editor_par_tarzanparpanels_can_line_line_665_coords |
| canvas_editor_par_tarzanparpanels_can_oval_line_509_coords | canvas_editor_par_tarzanparpanels_can_oval_line_509_coords |
| canvas_editor_par_tarzanparpanels_can_oval_line_511_coords | canvas_editor_par_tarzanparpanels_can_oval_line_511_coords |
| canvas_editor_par_tarzanparpanels_can_oval_line_656_coords | canvas_editor_par_tarzanparpanels_can_oval_line_656_coords |
| canvas_editor_par_tarzanparpanels_can_oval_line_920_coords | canvas_editor_par_tarzanparpanels_can_oval_line_920_coords |
| canvas_editor_par_tarzanparpanels_can_polygon_line_921_coords | canvas_editor_par_tarzanparpanels_can_polygon_line_921_coords |
| canvas_editor_par_tarzanparpanels_can_rectangle_line_899_coords | canvas_editor_par_tarzanparpanels_can_rectangle_line_899_coords |
| canvas_editor_par_tarzanparpanels_can_rectangle_line_901_coords | canvas_editor_par_tarzanparpanels_can_rectangle_line_901_coords |
| canvas_editor_par_tarzanparpanels_can_text_line_1307_text | canvas_editor_par_tarzanparpanels_can_text_line_1307_text |
| canvas_editor_par_tarzanparpanels_can_text_line_1309_text | canvas_editor_par_tarzanparpanels_can_text_line_1309_text |
| canvas_editor_par_tarzanparpanels_can_text_line_1310_text | canvas_editor_par_tarzanparpanels_can_text_line_1310_text |
| canvas_editor_par_tarzanparpanels_can_text_line_1329_text | canvas_editor_par_tarzanparpanels_can_text_line_1329_text |
| canvas_editor_par_tarzanparpanels_can_text_line_1331_text | canvas_editor_par_tarzanparpanels_can_text_line_1331_text |
| canvas_editor_par_tarzanparpanels_canvas_line_line_825_coords | canvas_editor_par_tarzanparpanels_canvas_line_line_825_coords |
| canvas_editor_par_tarzanparpanels_canvas_line_line_826_coords | canvas_editor_par_tarzanparpanels_canvas_line_line_826_coords |
| canvas_editor_par_tarzanparpanels_canvas_oval_line_1575_coords | canvas_editor_par_tarzanparpanels_canvas_oval_line_1575_coords |
| canvas_editor_par_tarzanparpanels_canvas_oval_line_830_coords | canvas_editor_par_tarzanparpanels_canvas_oval_line_830_coords |
| canvas_editor_par_tarzanparpanels_canvas_polygon_line_828_coords | canvas_editor_par_tarzanparpanels_canvas_polygon_line_828_coords |
| canvas_editor_par_tarzanparpanels_canvas_rectangle_line_1449_coords | canvas_editor_par_tarzanparpanels_canvas_rectangle_line_1449_coords |
| canvas_editor_par_tarzanparpanels_canvas_rectangle_line_1450_coords | canvas_editor_par_tarzanparpanels_canvas_rectangle_line_1450_coords |
| canvas_editor_par_tarzanparpanels_canvas_rectangle_line_1451_coords | canvas_editor_par_tarzanparpanels_canvas_rectangle_line_1451_coords |
| canvas_editor_par_tarzanparpanels_old_c_line_line_3118_coords | canvas_editor_par_tarzanparpanels_old_c_line_line_3118_coords |
| canvas_editor_par_tarzanparpanels_old_c_line_line_3119_coords | canvas_editor_par_tarzanparpanels_old_c_line_line_3119_coords |
| canvas_editor_par_tarzanparpanels_old_c_oval_line_1979_coords | canvas_editor_par_tarzanparpanels_old_c_oval_line_1979_coords |
| canvas_editor_par_tarzanparpanels_old_c_oval_line_1980_coords | canvas_editor_par_tarzanparpanels_old_c_oval_line_1980_coords |
| canvas_editor_par_tarzanparpanels_old_c_oval_line_2212_coords | canvas_editor_par_tarzanparpanels_old_c_oval_line_2212_coords |
| canvas_editor_par_tarzanparpanels_old_c_oval_line_3111_coords | canvas_editor_par_tarzanparpanels_old_c_oval_line_3111_coords |
| canvas_editor_par_tarzanparpanels_old_c_oval_line_344_coords | canvas_editor_par_tarzanparpanels_old_c_oval_line_344_coords |
| canvas_editor_par_tarzanparpanels_old_c_polygon_line_2213_coords | canvas_editor_par_tarzanparpanels_old_c_polygon_line_2213_coords |
| canvas_editor_par_tarzanparpanels_old_canvas_image_line_1549_coords | canvas_editor_par_tarzanparpanels_old_canvas_image_line_1549_coords |
| canvas_editor_par_tarzanparpanels_old_canvas_line_line_1538_coords | canvas_editor_par_tarzanparpanels_old_canvas_line_line_1538_coords |
| canvas_editor_par_tarzanparpanels_old_canvas_line_line_1539_coords | canvas_editor_par_tarzanparpanels_old_canvas_line_line_1539_coords |
| canvas_editor_par_tarzanparpanels_old_canvas_line_line_1545_coords | canvas_editor_par_tarzanparpanels_old_canvas_line_line_1545_coords |
| canvas_editor_par_tarzanparpanels_old_canvas_line_line_1563_coords | canvas_editor_par_tarzanparpanels_old_canvas_line_line_1563_coords |
| canvas_editor_par_tarzanparpanels_old_canvas_line_line_1581_coords | canvas_editor_par_tarzanparpanels_old_canvas_line_line_1581_coords |
| canvas_editor_par_tarzanparpanels_old_canvas_line_line_1582_coords | canvas_editor_par_tarzanparpanels_old_canvas_line_line_1582_coords |
| canvas_editor_par_tarzanparpanels_old_canvas_line_line_1784_coords | canvas_editor_par_tarzanparpanels_old_canvas_line_line_1784_coords |
| canvas_editor_par_tarzanparpanels_old_canvas_line_line_1785_coords | canvas_editor_par_tarzanparpanels_old_canvas_line_line_1785_coords |
| canvas_editor_par_tarzanparpanels_old_canvas_line_line_2481_coords | canvas_editor_par_tarzanparpanels_old_canvas_line_line_2481_coords |
| canvas_editor_par_tarzanparpanels_old_canvas_line_line_767_coords | canvas_editor_par_tarzanparpanels_old_canvas_line_line_767_coords |
| canvas_editor_par_tarzanparpanels_old_canvas_line_line_780_coords | canvas_editor_par_tarzanparpanels_old_canvas_line_line_780_coords |
| canvas_editor_par_tarzanparpanels_old_canvas_line_line_781_coords | canvas_editor_par_tarzanparpanels_old_canvas_line_line_781_coords |
| canvas_editor_par_tarzanparpanels_old_canvas_line_line_784_coords | canvas_editor_par_tarzanparpanels_old_canvas_line_line_784_coords |
| canvas_editor_par_tarzanparpanels_old_canvas_oval_line_1216_coords | canvas_editor_par_tarzanparpanels_old_canvas_oval_line_1216_coords |
| canvas_editor_par_tarzanparpanels_old_canvas_oval_line_1796_coords | canvas_editor_par_tarzanparpanels_old_canvas_oval_line_1796_coords |
| canvas_editor_par_tarzanparpanels_old_canvas_oval_line_2480_coords | canvas_editor_par_tarzanparpanels_old_canvas_oval_line_2480_coords |
| canvas_editor_par_tarzanparpanels_old_canvas_oval_line_2482_coords | canvas_editor_par_tarzanparpanels_old_canvas_oval_line_2482_coords |
| canvas_editor_par_tarzanparpanels_old_canvas_polygon_line_1786_coords | canvas_editor_par_tarzanparpanels_old_canvas_polygon_line_1786_coords |
| canvas_editor_par_tarzanparpanels_old_canvas_rectangle_line_1113_coords | canvas_editor_par_tarzanparpanels_old_canvas_rectangle_line_1113_coords |
| canvas_editor_par_tarzanparpanels_old_canvas_rectangle_line_1114_coords | canvas_editor_par_tarzanparpanels_old_canvas_rectangle_line_1114_coords |
| canvas_editor_par_tarzanparpanels_old_canvas_rectangle_line_1116_coords | canvas_editor_par_tarzanparpanels_old_canvas_rectangle_line_1116_coords |
| canvas_editor_par_tarzanparpanels_old_canvas_rectangle_line_1117_coords | canvas_editor_par_tarzanparpanels_old_canvas_rectangle_line_1117_coords |
| canvas_editor_par_tarzanparpanels_old_canvas_rectangle_line_1313_coords | canvas_editor_par_tarzanparpanels_old_canvas_rectangle_line_1313_coords |
| canvas_editor_par_tarzanparpanels_old_canvas_rectangle_line_1314_coords | canvas_editor_par_tarzanparpanels_old_canvas_rectangle_line_1314_coords |
| canvas_editor_par_tarzanparpanels_old_canvas_rectangle_line_1315_coords | canvas_editor_par_tarzanparpanels_old_canvas_rectangle_line_1315_coords |
| canvas_editor_par_tarzanparpanels_old_canvas_text_line_1551_text | canvas_editor_par_tarzanparpanels_old_canvas_text_line_1551_text |
| canvas_editor_par_tarzanparpanels_old_canvas_text_line_1554_text | canvas_editor_par_tarzanparpanels_old_canvas_text_line_1554_text |
| canvas_editor_par_tarzanparpanels_old_canvas_text_line_1555_text | canvas_editor_par_tarzanparpanels_old_canvas_text_line_1555_text |
| canvas_editor_par_tarzanparpanels_old_canvas_text_line_1586_text | canvas_editor_par_tarzanparpanels_old_canvas_text_line_1586_text |
| canvas_editor_par_tarzanparpanels_old_canvas_text_line_766_text | canvas_editor_par_tarzanparpanels_old_canvas_text_line_766_text |
| canvas_editor_par_tarzanparpanels_old_canvas_text_line_785_text | canvas_editor_par_tarzanparpanels_old_canvas_text_line_785_text |
| canvas_editor_par_tarzanparpanels_old_canvas_window_line_119_coords | canvas_editor_par_tarzanparpanels_old_canvas_window_line_119_coords |
| canvas_editor_par_tarzanparpanels_old_dot_oval_line_378_coords | canvas_editor_par_tarzanparpanels_old_dot_oval_line_378_coords |
| canvas_editor_par_tarzanparpanels_old_led_oval_line_1049_coords | canvas_editor_par_tarzanparpanels_old_led_oval_line_1049_coords |
| canvas_editor_par_tarzanparpanels_old_led_oval_line_1050_coords | canvas_editor_par_tarzanparpanels_old_led_oval_line_1050_coords |
| canvas_editor_par_tarzanparpanels_old_rect_coords | canvas_editor_par_tarzanparpanels_old_rect_coords |
| canvas_editor_par_tarzanparpanels_old_self_rectangle_line_1346_coords | canvas_editor_par_tarzanparpanels_old_self_rectangle_line_1346_coords |
| canvas_editor_par_tarzanparpanels_old_self_rectangle_line_1347_coords | canvas_editor_par_tarzanparpanels_old_self_rectangle_line_1347_coords |
| canvas_editor_par_tarzanparpanels_old_window_id_coords | canvas_editor_par_tarzanparpanels_old_window_id_coords |
| canvas_editor_par_tarzanparpanels_self_rectangle_line_185_coords | canvas_editor_par_tarzanparpanels_self_rectangle_line_185_coords |
| canvas_editor_par_tarzanparpanels_window_id_coords | canvas_editor_par_tarzanparpanels_window_id_coords |
| canvas_editor_par_tarzanparwidgets_c_line_line_304_coords | canvas_editor_par_tarzanparwidgets_c_line_line_304_coords |
| canvas_editor_par_tarzanparwidgets_c_oval_line_299_coords | canvas_editor_par_tarzanparwidgets_c_oval_line_299_coords |
| canvas_editor_par_tarzanparwidgets_c_oval_line_300_coords | canvas_editor_par_tarzanparwidgets_c_oval_line_300_coords |
| canvas_editor_par_tarzanparwidgets_c_oval_line_305_coords | canvas_editor_par_tarzanparwidgets_c_oval_line_305_coords |
| canvas_editor_par_tarzanparwidgets_self_oval_line_59_coords | canvas_editor_par_tarzanparwidgets_self_oval_line_59_coords |
| canvas_editor_par_tarzanparwidgets_self_oval_line_60_coords | canvas_editor_par_tarzanparwidgets_self_oval_line_60_coords |
| canvas_editor_par_tarzanparwidgets_self_oval_line_64_coords | canvas_editor_par_tarzanparwidgets_self_oval_line_64_coords |
| canvas_editor_par_tarzanparwidgets_self_oval_line_65_coords | canvas_editor_par_tarzanparwidgets_self_oval_line_65_coords |
| canvas_editor_par_tarzanparwidgets_self_rectangle_line_90_coords | canvas_editor_par_tarzanparwidgets_self_rectangle_line_90_coords |
| canvas_editor_tarzanaxissandbox_c_line_line_826_coords | canvas_editor_tarzanaxissandbox_c_line_line_826_coords |
| canvas_editor_tarzanaxissandbox_c_line_line_833_coords | canvas_editor_tarzanaxissandbox_c_line_line_833_coords |
| canvas_editor_tarzanaxissandbox_c_line_line_852_coords | canvas_editor_tarzanaxissandbox_c_line_line_852_coords |
| canvas_editor_tarzanaxissandbox_c_line_line_859_coords | canvas_editor_tarzanaxissandbox_c_line_line_859_coords |
| canvas_editor_tarzanaxissandbox_c_line_line_871_coords | canvas_editor_tarzanaxissandbox_c_line_line_871_coords |
| canvas_editor_tarzanaxissandbox_c_line_line_872_coords | canvas_editor_tarzanaxissandbox_c_line_line_872_coords |
| canvas_editor_tarzanaxissandbox_c_line_line_886_coords | canvas_editor_tarzanaxissandbox_c_line_line_886_coords |
| canvas_editor_tarzanaxissandbox_c_line_line_898_coords | canvas_editor_tarzanaxissandbox_c_line_line_898_coords |
| canvas_editor_tarzanaxissandbox_c_line_line_900_coords | canvas_editor_tarzanaxissandbox_c_line_line_900_coords |
| canvas_editor_tarzanaxissandbox_c_oval_line_868_coords | canvas_editor_tarzanaxissandbox_c_oval_line_868_coords |
| canvas_editor_tarzanaxissandbox_c_rectangle_line_812_coords | canvas_editor_tarzanaxissandbox_c_rectangle_line_812_coords |
| canvas_editor_tarzanaxissandbox_c_rectangle_line_819_coords | canvas_editor_tarzanaxissandbox_c_rectangle_line_819_coords |
| canvas_editor_tarzanaxissandbox_c_rectangle_line_820_coords | canvas_editor_tarzanaxissandbox_c_rectangle_line_820_coords |
| canvas_editor_tarzanaxissandbox_c_rectangle_line_821_coords | canvas_editor_tarzanaxissandbox_c_rectangle_line_821_coords |
| canvas_editor_tarzanaxissandbox_c_rectangle_line_880_coords | canvas_editor_tarzanaxissandbox_c_rectangle_line_880_coords |
| canvas_editor_tarzanaxissandbox_c_text_line_827_text | canvas_editor_tarzanaxissandbox_c_text_line_827_text |
| canvas_editor_tarzanaxissandbox_c_text_line_834_text | canvas_editor_tarzanaxissandbox_c_text_line_834_text |
| canvas_editor_tarzanaxissandbox_c_text_line_873_text | canvas_editor_tarzanaxissandbox_c_text_line_873_text |
| canvas_editor_tarzanaxissandbox_c_text_line_874_text | canvas_editor_tarzanaxissandbox_c_text_line_874_text |
| canvas_editor_tarzanaxissandbox_c_text_line_901_text | canvas_editor_tarzanaxissandbox_c_text_line_901_text |
| canvas_editor_tarzanaxissandbox_c_text_line_902_text | canvas_editor_tarzanaxissandbox_c_text_line_902_text |
| canvas_editor_tarzanehrtakesandbox_canvas_image_line_553_coords | canvas_editor_tarzanehrtakesandbox_canvas_image_line_553_coords |
| canvas_editor_tarzanehrtakesandbox_item_text | canvas_editor_tarzanehrtakesandbox_item_text |
| canvas_editor_tarzanehrtakesandbox_protocol_canvas_rectangle_line_1057_coords | canvas_editor_tarzanehrtakesandbox_protocol_canvas_rectangle_line_1057_coords |
| canvas_editor_tarzanehrtakesandbox_protocol_canvas_rectangle_line_1058_coords | canvas_editor_tarzanehrtakesandbox_protocol_canvas_rectangle_line_1058_coords |
| canvas_editor_tarzanehrtakesandbox_protocol_title_id_text | canvas_editor_tarzanehrtakesandbox_protocol_title_id_text |
| canvas_editor_tarzanehrtakesandbox_row_window_coords | canvas_editor_tarzanehrtakesandbox_row_window_coords |
| canvas_editor_tarzanehrtakesandbox_save_button_window_coords | canvas_editor_tarzanehrtakesandbox_save_button_window_coords |
| canvas_editor_tarzankhr_c_image_line_1518_coords | canvas_editor_tarzankhr_c_image_line_1518_coords |
| canvas_editor_tarzankhr_c_image_line_1533_coords | canvas_editor_tarzankhr_c_image_line_1533_coords |
| canvas_editor_tarzankhr_c_image_line_623_coords | canvas_editor_tarzankhr_c_image_line_623_coords |
| canvas_editor_tarzankhr_c_line_line_1545_coords | canvas_editor_tarzankhr_c_line_line_1545_coords |
| canvas_editor_tarzankhr_c_line_line_1546_coords | canvas_editor_tarzankhr_c_line_line_1546_coords |
| canvas_editor_tarzankhr_c_line_line_1555_coords | canvas_editor_tarzankhr_c_line_line_1555_coords |
| canvas_editor_tarzankhr_c_line_line_1570_coords | canvas_editor_tarzankhr_c_line_line_1570_coords |
| canvas_editor_tarzankhr_c_line_line_1571_coords | canvas_editor_tarzankhr_c_line_line_1571_coords |
| canvas_editor_tarzankhr_c_line_line_1593_coords | canvas_editor_tarzankhr_c_line_line_1593_coords |
| canvas_editor_tarzankhr_c_line_line_1597_coords | canvas_editor_tarzankhr_c_line_line_1597_coords |
| canvas_editor_tarzankhr_c_oval_line_1589_coords | canvas_editor_tarzankhr_c_oval_line_1589_coords |
| canvas_editor_tarzankhr_c_oval_line_1590_coords | canvas_editor_tarzankhr_c_oval_line_1590_coords |
| canvas_editor_tarzankhr_c_polygon_line_1553_coords | canvas_editor_tarzankhr_c_polygon_line_1553_coords |
| canvas_editor_tarzankhr_c_polygon_line_1602_coords | canvas_editor_tarzankhr_c_polygon_line_1602_coords |
| canvas_editor_tarzankhr_c_rectangle_line_1548_coords | canvas_editor_tarzankhr_c_rectangle_line_1548_coords |
| canvas_editor_tarzankhr_c_rectangle_line_1573_coords | canvas_editor_tarzankhr_c_rectangle_line_1573_coords |
| canvas_editor_tarzankhr_c_text_line_1457_text | canvas_editor_tarzankhr_c_text_line_1457_text |
| canvas_editor_tarzankhr_c_text_line_1465_text | canvas_editor_tarzankhr_c_text_line_1465_text |
| canvas_editor_tarzankhr_c_text_line_1472_text | canvas_editor_tarzankhr_c_text_line_1472_text |
| canvas_editor_tarzankhr_c_text_line_1473_text | canvas_editor_tarzankhr_c_text_line_1473_text |
| canvas_editor_tarzankhr_c_text_line_1474_text | canvas_editor_tarzankhr_c_text_line_1474_text |
| canvas_editor_tarzankhr_c_text_line_1481_text | canvas_editor_tarzankhr_c_text_line_1481_text |
| canvas_editor_tarzankhr_c_text_line_1486_text | canvas_editor_tarzankhr_c_text_line_1486_text |
| canvas_editor_tarzankhr_c_text_line_1496_text | canvas_editor_tarzankhr_c_text_line_1496_text |
| canvas_editor_tarzankhr_c_text_line_1503_text | canvas_editor_tarzankhr_c_text_line_1503_text |
| canvas_editor_tarzankhr_c_text_line_1520_text | canvas_editor_tarzankhr_c_text_line_1520_text |
| canvas_editor_tarzankhr_c_text_line_1522_text | canvas_editor_tarzankhr_c_text_line_1522_text |
| canvas_editor_tarzankhr_c_text_line_1525_text | canvas_editor_tarzankhr_c_text_line_1525_text |
| canvas_editor_tarzankhr_c_text_line_1542_text | canvas_editor_tarzankhr_c_text_line_1542_text |
| canvas_editor_tarzankhr_c_text_line_1549_text | canvas_editor_tarzankhr_c_text_line_1549_text |
| canvas_editor_tarzankhr_c_text_line_1554_text | canvas_editor_tarzankhr_c_text_line_1554_text |
| canvas_editor_tarzankhr_c_text_line_1556_text | canvas_editor_tarzankhr_c_text_line_1556_text |
| canvas_editor_tarzankhr_c_text_line_1564_text | canvas_editor_tarzankhr_c_text_line_1564_text |
| canvas_editor_tarzankhr_c_text_line_1569_text | canvas_editor_tarzankhr_c_text_line_1569_text |
| canvas_editor_tarzankhr_c_text_line_1574_text | canvas_editor_tarzankhr_c_text_line_1574_text |
| canvas_editor_tarzankhr_c_text_line_1576_text | canvas_editor_tarzankhr_c_text_line_1576_text |
| canvas_editor_tarzankhr_c_text_line_1578_text | canvas_editor_tarzankhr_c_text_line_1578_text |
| canvas_editor_tarzankhr_c_text_line_1579_text | canvas_editor_tarzankhr_c_text_line_1579_text |
| canvas_editor_tarzankhr_c_text_line_1580_text | canvas_editor_tarzankhr_c_text_line_1580_text |
| canvas_editor_tarzankhr_c_text_line_1603_text | canvas_editor_tarzankhr_c_text_line_1603_text |
| canvas_editor_tarzankhr_c_text_line_1604_text | canvas_editor_tarzankhr_c_text_line_1604_text |
| canvas_editor_tarzankhr_c_text_line_1605_text | canvas_editor_tarzankhr_c_text_line_1605_text |
| canvas_editor_tarzankhr_c_text_line_615_text | canvas_editor_tarzankhr_c_text_line_615_text |
| canvas_editor_tarzankhr_c_text_line_625_text | canvas_editor_tarzankhr_c_text_line_625_text |
| canvas_editor_tarzankhr_c_text_line_627_text | canvas_editor_tarzankhr_c_text_line_627_text |
| canvas_editor_tarzankhr_c_text_line_629_text | canvas_editor_tarzankhr_c_text_line_629_text |
| canvas_editor_tarzantakeprotocollight_canvas_image_line_860_coords | canvas_editor_tarzantakeprotocollight_canvas_image_line_860_coords |
| canvas_editor_tarzantakeprotocollight_item_text | canvas_editor_tarzantakeprotocollight_item_text |
| canvas_editor_tarzantakeprotocollight_protocol_canvas_rectangle_line_1215_coords | canvas_editor_tarzantakeprotocollight_protocol_canvas_rectangle_line_1215_coords |
| canvas_editor_tarzantakeprotocollight_protocol_canvas_rectangle_line_1216_coords | canvas_editor_tarzantakeprotocollight_protocol_canvas_rectangle_line_1216_coords |
| canvas_editor_tarzantakeprotocollight_protocol_title_id_text | canvas_editor_tarzantakeprotocollight_protocol_title_id_text |
| canvas_editor_tarzantakeprotocollight_row_window_coords | canvas_editor_tarzantakeprotocollight_row_window_coords |
| canvas_editor_tarzantakeprotocollight_save_button_window_coords | canvas_editor_tarzantakeprotocollight_save_button_window_coords |
| canvas_mechanics_tarzanedytorchoreografiiruchu_c_line_line_305_coords | canvas_mechanics_tarzanedytorchoreografiiruchu_c_line_line_305_coords |
| canvas_mechanics_tarzanedytorchoreografiiruchu_c_line_line_313_coords | canvas_mechanics_tarzanedytorchoreografiiruchu_c_line_line_313_coords |
| canvas_mechanics_tarzanedytorchoreografiiruchu_c_text_line_314_text | canvas_mechanics_tarzanedytorchoreografiiruchu_c_text_line_314_text |
| canvas_mechanics_tarzanedytorchoreografiiruchu_scroll_window_coords | canvas_mechanics_tarzanedytorchoreografiiruchu_scroll_window_coords |
| canvas_mechanics_tarzanwykresosi_c_line_line_1011_coords | canvas_mechanics_tarzanwykresosi_c_line_line_1011_coords |
| canvas_mechanics_tarzanwykresosi_c_line_line_1012_coords | canvas_mechanics_tarzanwykresosi_c_line_line_1012_coords |
| canvas_mechanics_tarzanwykresosi_c_line_line_754_coords | canvas_mechanics_tarzanwykresosi_c_line_line_754_coords |
| canvas_mechanics_tarzanwykresosi_c_line_line_756_coords | canvas_mechanics_tarzanwykresosi_c_line_line_756_coords |
| canvas_mechanics_tarzanwykresosi_c_line_line_757_coords | canvas_mechanics_tarzanwykresosi_c_line_line_757_coords |
| canvas_mechanics_tarzanwykresosi_c_line_line_770_coords | canvas_mechanics_tarzanwykresosi_c_line_line_770_coords |
| canvas_mechanics_tarzanwykresosi_c_oval_line_777_coords | canvas_mechanics_tarzanwykresosi_c_oval_line_777_coords |
| canvas_mechanics_tarzanwykresosi_c_polygon_line_1013_coords | canvas_mechanics_tarzanwykresosi_c_polygon_line_1013_coords |
| canvas_mechanics_tarzanwykresosi_c_rectangle_line_723_coords | canvas_mechanics_tarzanwykresosi_c_rectangle_line_723_coords |
| canvas_mechanics_tarzanwykresosi_c_rectangle_line_732_coords | canvas_mechanics_tarzanwykresosi_c_rectangle_line_732_coords |
| canvas_mechanics_tarzanwykresosi_c_rectangle_line_734_coords | canvas_mechanics_tarzanwykresosi_c_rectangle_line_734_coords |
| canvas_mechanics_tarzanwykresosi_c_rectangle_line_751_coords | canvas_mechanics_tarzanwykresosi_c_rectangle_line_751_coords |
| canvas_mechanics_tarzanwykresosi_c_text_line_1014_text | canvas_mechanics_tarzanwykresosi_c_text_line_1014_text |
| canvas_mechanics_tarzanwykresosi_c_text_line_731_text | canvas_mechanics_tarzanwykresosi_c_text_line_731_text |
| canvas_mechanics_tarzanwykresosi_c_text_line_735_text | canvas_mechanics_tarzanwykresosi_c_text_line_735_text |
| canvas_mechanics_tarzanwykresosi_c_text_line_758_text | canvas_mechanics_tarzanwykresosi_c_text_line_758_text |
| canvas_mechanics_tarzanwykresosi_c_text_line_759_text | canvas_mechanics_tarzanwykresosi_c_text_line_759_text |
| canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_line_line_826_coords | canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_line_line_826_coords |
| canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_line_line_833_coords | canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_line_line_833_coords |
| canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_line_line_840_coords | canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_line_line_840_coords |
| canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_line_line_852_coords | canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_line_line_852_coords |
| canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_line_line_853_coords | canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_line_line_853_coords |
| canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_line_line_867_coords | canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_line_line_867_coords |
| canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_line_line_879_coords | canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_line_line_879_coords |
| canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_line_line_881_coords | canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_line_line_881_coords |
| canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_oval_line_849_coords | canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_oval_line_849_coords |
| canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_812_coords | canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_812_coords |
| canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_819_coords | canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_819_coords |
| canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_820_coords | canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_820_coords |
| canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_821_coords | canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_821_coords |
| canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_861_coords | canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_rectangle_line_861_coords |
| canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_text_line_827_text | canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_text_line_827_text |
| canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_text_line_834_text | canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_text_line_834_text |
| canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_text_line_854_text | canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_text_line_854_text |
| canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_text_line_855_text | canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_text_line_855_text |
| canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_text_line_882_text | canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_text_line_882_text |
| canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_text_line_883_text | canvas_modes_editor_editor_ehr_tarzanaxissandbox_c_text_line_883_text |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_image_line_2734_coords | canvas_modes_editor_editor_ehr_tarzanehrui_c_image_line_2734_coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_1910_coords | canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_1910_coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_1919_coords | canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_1919_coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_1930_coords | canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_1930_coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_1937_coords | canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_1937_coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_1951_coords | canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_1951_coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_1952_coords | canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_1952_coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_1966_coords | canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_1966_coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_1978_coords | canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_1978_coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_1980_coords | canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_1980_coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_2697_coords | canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_2697_coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_2707_coords | canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_2707_coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_2710_coords | canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_2710_coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_2749_coords | canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_2749_coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_2757_coords | canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_2757_coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_2765_coords | canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_2765_coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_2778_coords | canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_2778_coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_2801_coords | canvas_modes_editor_editor_ehr_tarzanehrui_c_line_line_2801_coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_oval_line_1947_coords | canvas_modes_editor_editor_ehr_tarzanehrui_c_oval_line_1947_coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_oval_line_2792_coords | canvas_modes_editor_editor_ehr_tarzanehrui_c_oval_line_2792_coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_oval_line_2794_coords | canvas_modes_editor_editor_ehr_tarzanehrui_c_oval_line_2794_coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_polygon_line_2808_coords | canvas_modes_editor_editor_ehr_tarzanehrui_c_polygon_line_2808_coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_rectangle_line_1893_coords | canvas_modes_editor_editor_ehr_tarzanehrui_c_rectangle_line_1893_coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_rectangle_line_1901_coords | canvas_modes_editor_editor_ehr_tarzanehrui_c_rectangle_line_1901_coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_rectangle_line_1902_coords | canvas_modes_editor_editor_ehr_tarzanehrui_c_rectangle_line_1902_coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_rectangle_line_1903_coords | canvas_modes_editor_editor_ehr_tarzanehrui_c_rectangle_line_1903_coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_rectangle_line_1960_coords | canvas_modes_editor_editor_ehr_tarzanehrui_c_rectangle_line_1960_coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_rectangle_line_2688_coords | canvas_modes_editor_editor_ehr_tarzanehrui_c_rectangle_line_2688_coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_rectangle_line_2705_coords | canvas_modes_editor_editor_ehr_tarzanehrui_c_rectangle_line_2705_coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_rectangle_line_2790_coords | canvas_modes_editor_editor_ehr_tarzanehrui_c_rectangle_line_2790_coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_rectangle_line_2800_coords | canvas_modes_editor_editor_ehr_tarzanehrui_c_rectangle_line_2800_coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_1911_text | canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_1911_text |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_1920_text | canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_1920_text |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_1953_text | canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_1953_text |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_1954_text | canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_1954_text |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_1981_text | canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_1981_text |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_1982_text | canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_1982_text |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_2720_text | canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_2720_text |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_2727_text | canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_2727_text |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_2736_text | canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_2736_text |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_2809_text | canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_2809_text |
| canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_2816_text | canvas_modes_editor_editor_ehr_tarzanehrui_c_text_line_2816_text |
| canvas_modes_editor_editor_ehr_tarzanehrui_canvas_image_line_712_coords | canvas_modes_editor_editor_ehr_tarzanehrui_canvas_image_line_712_coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_canvas_rectangle_line_1244_coords | canvas_modes_editor_editor_ehr_tarzanehrui_canvas_rectangle_line_1244_coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_canvas_window_line_1172_coords | canvas_modes_editor_editor_ehr_tarzanehrui_canvas_window_line_1172_coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_item_text | canvas_modes_editor_editor_ehr_tarzanehrui_item_text |
| canvas_modes_editor_editor_ehr_tarzanehrui_protocol_canvas_rectangle_line_962_coords | canvas_modes_editor_editor_ehr_tarzanehrui_protocol_canvas_rectangle_line_962_coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_protocol_canvas_rectangle_line_963_coords | canvas_modes_editor_editor_ehr_tarzanehrui_protocol_canvas_rectangle_line_963_coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_row_window_coords | canvas_modes_editor_editor_ehr_tarzanehrui_row_window_coords |
| canvas_modes_editor_editor_ehr_tarzanehrui_save_button_window_coords | canvas_modes_editor_editor_ehr_tarzanehrui_save_button_window_coords |
| canvas_modes_editor_editor_tarzanaxissandbox_c_line_line_826_coords | canvas_modes_editor_editor_tarzanaxissandbox_c_line_line_826_coords |
| canvas_modes_editor_editor_tarzanaxissandbox_c_line_line_833_coords | canvas_modes_editor_editor_tarzanaxissandbox_c_line_line_833_coords |
| canvas_modes_editor_editor_tarzanaxissandbox_c_line_line_852_coords | canvas_modes_editor_editor_tarzanaxissandbox_c_line_line_852_coords |
| canvas_modes_editor_editor_tarzanaxissandbox_c_line_line_859_coords | canvas_modes_editor_editor_tarzanaxissandbox_c_line_line_859_coords |
| canvas_modes_editor_editor_tarzanaxissandbox_c_line_line_871_coords | canvas_modes_editor_editor_tarzanaxissandbox_c_line_line_871_coords |
| canvas_modes_editor_editor_tarzanaxissandbox_c_line_line_872_coords | canvas_modes_editor_editor_tarzanaxissandbox_c_line_line_872_coords |
| canvas_modes_editor_editor_tarzanaxissandbox_c_line_line_886_coords | canvas_modes_editor_editor_tarzanaxissandbox_c_line_line_886_coords |
| canvas_modes_editor_editor_tarzanaxissandbox_c_line_line_898_coords | canvas_modes_editor_editor_tarzanaxissandbox_c_line_line_898_coords |
| canvas_modes_editor_editor_tarzanaxissandbox_c_line_line_900_coords | canvas_modes_editor_editor_tarzanaxissandbox_c_line_line_900_coords |
| canvas_modes_editor_editor_tarzanaxissandbox_c_oval_line_868_coords | canvas_modes_editor_editor_tarzanaxissandbox_c_oval_line_868_coords |
| canvas_modes_editor_editor_tarzanaxissandbox_c_rectangle_line_812_coords | canvas_modes_editor_editor_tarzanaxissandbox_c_rectangle_line_812_coords |
| canvas_modes_editor_editor_tarzanaxissandbox_c_rectangle_line_819_coords | canvas_modes_editor_editor_tarzanaxissandbox_c_rectangle_line_819_coords |
| canvas_modes_editor_editor_tarzanaxissandbox_c_rectangle_line_820_coords | canvas_modes_editor_editor_tarzanaxissandbox_c_rectangle_line_820_coords |
| canvas_modes_editor_editor_tarzanaxissandbox_c_rectangle_line_821_coords | canvas_modes_editor_editor_tarzanaxissandbox_c_rectangle_line_821_coords |
| canvas_modes_editor_editor_tarzanaxissandbox_c_rectangle_line_880_coords | canvas_modes_editor_editor_tarzanaxissandbox_c_rectangle_line_880_coords |
| canvas_modes_editor_editor_tarzanaxissandbox_c_text_line_827_text | canvas_modes_editor_editor_tarzanaxissandbox_c_text_line_827_text |
| canvas_modes_editor_editor_tarzanaxissandbox_c_text_line_834_text | canvas_modes_editor_editor_tarzanaxissandbox_c_text_line_834_text |
| canvas_modes_editor_editor_tarzanaxissandbox_c_text_line_873_text | canvas_modes_editor_editor_tarzanaxissandbox_c_text_line_873_text |
| canvas_modes_editor_editor_tarzanaxissandbox_c_text_line_874_text | canvas_modes_editor_editor_tarzanaxissandbox_c_text_line_874_text |
| canvas_modes_editor_editor_tarzanaxissandbox_c_text_line_901_text | canvas_modes_editor_editor_tarzanaxissandbox_c_text_line_901_text |
| canvas_modes_editor_editor_tarzanaxissandbox_c_text_line_902_text | canvas_modes_editor_editor_tarzanaxissandbox_c_text_line_902_text |
| canvas_modes_editor_editor_tarzanehrtakesandbox_canvas_image_line_553_coords | canvas_modes_editor_editor_tarzanehrtakesandbox_canvas_image_line_553_coords |
| canvas_modes_editor_editor_tarzanehrtakesandbox_item_text | canvas_modes_editor_editor_tarzanehrtakesandbox_item_text |
| canvas_modes_editor_editor_tarzanehrtakesandbox_protocol_canvas_rectangle_line_1057_coords | canvas_modes_editor_editor_tarzanehrtakesandbox_protocol_canvas_rectangle_line_1057_coords |
| canvas_modes_editor_editor_tarzanehrtakesandbox_protocol_canvas_rectangle_line_1058_coords | canvas_modes_editor_editor_tarzanehrtakesandbox_protocol_canvas_rectangle_line_1058_coords |
| canvas_modes_editor_editor_tarzanehrtakesandbox_protocol_title_id_text | canvas_modes_editor_editor_tarzanehrtakesandbox_protocol_title_id_text |
| canvas_modes_editor_editor_tarzanehrtakesandbox_row_window_coords | canvas_modes_editor_editor_tarzanehrtakesandbox_row_window_coords |
| canvas_modes_editor_editor_tarzanehrtakesandbox_save_button_window_coords | canvas_modes_editor_editor_tarzanehrtakesandbox_save_button_window_coords |
| canvas_modes_editor_editor_tarzantakeprotocollight_canvas_image_line_860_coords | canvas_modes_editor_editor_tarzantakeprotocollight_canvas_image_line_860_coords |
| canvas_modes_editor_editor_tarzantakeprotocollight_item_text | canvas_modes_editor_editor_tarzantakeprotocollight_item_text |
| canvas_modes_editor_editor_tarzantakeprotocollight_protocol_canvas_rectangle_line_1215_coords | canvas_modes_editor_editor_tarzantakeprotocollight_protocol_canvas_rectangle_line_1215_coords |
| canvas_modes_editor_editor_tarzantakeprotocollight_protocol_canvas_rectangle_line_1216_coords | canvas_modes_editor_editor_tarzantakeprotocollight_protocol_canvas_rectangle_line_1216_coords |
| canvas_modes_editor_editor_tarzantakeprotocollight_protocol_title_id_text | canvas_modes_editor_editor_tarzantakeprotocollight_protocol_title_id_text |
| canvas_modes_editor_editor_tarzantakeprotocollight_row_window_coords | canvas_modes_editor_editor_tarzantakeprotocollight_row_window_coords |
| canvas_modes_editor_editor_tarzantakeprotocollight_save_button_window_coords | canvas_modes_editor_editor_tarzantakeprotocollight_save_button_window_coords |
| canvas_modes_editor_ehr_tarzanaxissandbox_c_line_line_827_coords | canvas_modes_editor_ehr_tarzanaxissandbox_c_line_line_827_coords |
| canvas_modes_editor_ehr_tarzanaxissandbox_c_line_line_834_coords | canvas_modes_editor_ehr_tarzanaxissandbox_c_line_line_834_coords |
| canvas_modes_editor_ehr_tarzanaxissandbox_c_line_line_841_coords | canvas_modes_editor_ehr_tarzanaxissandbox_c_line_line_841_coords |
| canvas_modes_editor_ehr_tarzanaxissandbox_c_line_line_853_coords | canvas_modes_editor_ehr_tarzanaxissandbox_c_line_line_853_coords |
| canvas_modes_editor_ehr_tarzanaxissandbox_c_line_line_854_coords | canvas_modes_editor_ehr_tarzanaxissandbox_c_line_line_854_coords |
| canvas_modes_editor_ehr_tarzanaxissandbox_c_line_line_868_coords | canvas_modes_editor_ehr_tarzanaxissandbox_c_line_line_868_coords |
| canvas_modes_editor_ehr_tarzanaxissandbox_c_line_line_880_coords | canvas_modes_editor_ehr_tarzanaxissandbox_c_line_line_880_coords |
| canvas_modes_editor_ehr_tarzanaxissandbox_c_line_line_882_coords | canvas_modes_editor_ehr_tarzanaxissandbox_c_line_line_882_coords |
| canvas_modes_editor_ehr_tarzanaxissandbox_c_oval_line_850_coords | canvas_modes_editor_ehr_tarzanaxissandbox_c_oval_line_850_coords |
| canvas_modes_editor_ehr_tarzanaxissandbox_c_rectangle_line_813_coords | canvas_modes_editor_ehr_tarzanaxissandbox_c_rectangle_line_813_coords |
| canvas_modes_editor_ehr_tarzanaxissandbox_c_rectangle_line_820_coords | canvas_modes_editor_ehr_tarzanaxissandbox_c_rectangle_line_820_coords |
| canvas_modes_editor_ehr_tarzanaxissandbox_c_rectangle_line_821_coords | canvas_modes_editor_ehr_tarzanaxissandbox_c_rectangle_line_821_coords |
| canvas_modes_editor_ehr_tarzanaxissandbox_c_rectangle_line_822_coords | canvas_modes_editor_ehr_tarzanaxissandbox_c_rectangle_line_822_coords |
| canvas_modes_editor_ehr_tarzanaxissandbox_c_rectangle_line_862_coords | canvas_modes_editor_ehr_tarzanaxissandbox_c_rectangle_line_862_coords |
| canvas_modes_editor_ehr_tarzanaxissandbox_c_text_line_828_text | canvas_modes_editor_ehr_tarzanaxissandbox_c_text_line_828_text |
| canvas_modes_editor_ehr_tarzanaxissandbox_c_text_line_835_text | canvas_modes_editor_ehr_tarzanaxissandbox_c_text_line_835_text |
| canvas_modes_editor_ehr_tarzanaxissandbox_c_text_line_855_text | canvas_modes_editor_ehr_tarzanaxissandbox_c_text_line_855_text |
| canvas_modes_editor_ehr_tarzanaxissandbox_c_text_line_856_text | canvas_modes_editor_ehr_tarzanaxissandbox_c_text_line_856_text |
| canvas_modes_editor_ehr_tarzanaxissandbox_c_text_line_883_text | canvas_modes_editor_ehr_tarzanaxissandbox_c_text_line_883_text |
| canvas_modes_editor_ehr_tarzanaxissandbox_c_text_line_884_text | canvas_modes_editor_ehr_tarzanaxissandbox_c_text_line_884_text |
| canvas_modes_editor_ehr_tarzanehrui_c_image_line_3130_coords | canvas_modes_editor_ehr_tarzanehrui_c_image_line_3130_coords |
| canvas_modes_editor_ehr_tarzanehrui_c_line_line_1993_coords | canvas_modes_editor_ehr_tarzanehrui_c_line_line_1993_coords |
| canvas_modes_editor_ehr_tarzanehrui_c_line_line_2002_coords | canvas_modes_editor_ehr_tarzanehrui_c_line_line_2002_coords |
| canvas_modes_editor_ehr_tarzanehrui_c_line_line_2013_coords | canvas_modes_editor_ehr_tarzanehrui_c_line_line_2013_coords |
| canvas_modes_editor_ehr_tarzanehrui_c_line_line_2020_coords | canvas_modes_editor_ehr_tarzanehrui_c_line_line_2020_coords |
| canvas_modes_editor_ehr_tarzanehrui_c_line_line_2048_coords | canvas_modes_editor_ehr_tarzanehrui_c_line_line_2048_coords |
| canvas_modes_editor_ehr_tarzanehrui_c_line_line_2049_coords | canvas_modes_editor_ehr_tarzanehrui_c_line_line_2049_coords |
| canvas_modes_editor_ehr_tarzanehrui_c_line_line_2068_coords | canvas_modes_editor_ehr_tarzanehrui_c_line_line_2068_coords |
| canvas_modes_editor_ehr_tarzanehrui_c_line_line_2080_coords | canvas_modes_editor_ehr_tarzanehrui_c_line_line_2080_coords |
| canvas_modes_editor_ehr_tarzanehrui_c_line_line_2082_coords | canvas_modes_editor_ehr_tarzanehrui_c_line_line_2082_coords |
| canvas_modes_editor_ehr_tarzanehrui_c_line_line_3081_coords | canvas_modes_editor_ehr_tarzanehrui_c_line_line_3081_coords |
| canvas_modes_editor_ehr_tarzanehrui_c_line_line_3102_coords | canvas_modes_editor_ehr_tarzanehrui_c_line_line_3102_coords |
| canvas_modes_editor_ehr_tarzanehrui_c_line_line_3105_coords | canvas_modes_editor_ehr_tarzanehrui_c_line_line_3105_coords |
| canvas_modes_editor_ehr_tarzanehrui_c_line_line_3145_coords | canvas_modes_editor_ehr_tarzanehrui_c_line_line_3145_coords |
| canvas_modes_editor_ehr_tarzanehrui_c_line_line_3153_coords | canvas_modes_editor_ehr_tarzanehrui_c_line_line_3153_coords |
| canvas_modes_editor_ehr_tarzanehrui_c_line_line_3161_coords | canvas_modes_editor_ehr_tarzanehrui_c_line_line_3161_coords |
| canvas_modes_editor_ehr_tarzanehrui_c_line_line_3176_coords | canvas_modes_editor_ehr_tarzanehrui_c_line_line_3176_coords |
| canvas_modes_editor_ehr_tarzanehrui_c_line_line_3217_coords | canvas_modes_editor_ehr_tarzanehrui_c_line_line_3217_coords |
| canvas_modes_editor_ehr_tarzanehrui_c_line_line_3231_coords | canvas_modes_editor_ehr_tarzanehrui_c_line_line_3231_coords |
| canvas_modes_editor_ehr_tarzanehrui_c_oval_line_2044_coords | canvas_modes_editor_ehr_tarzanehrui_c_oval_line_2044_coords |
| canvas_modes_editor_ehr_tarzanehrui_c_oval_line_3194_coords | canvas_modes_editor_ehr_tarzanehrui_c_oval_line_3194_coords |
| canvas_modes_editor_ehr_tarzanehrui_c_oval_line_3210_coords | canvas_modes_editor_ehr_tarzanehrui_c_oval_line_3210_coords |
| canvas_modes_editor_ehr_tarzanehrui_c_polygon_line_3226_coords | canvas_modes_editor_ehr_tarzanehrui_c_polygon_line_3226_coords |
| canvas_modes_editor_ehr_tarzanehrui_c_rectangle_line_1976_coords | canvas_modes_editor_ehr_tarzanehrui_c_rectangle_line_1976_coords |
| canvas_modes_editor_ehr_tarzanehrui_c_rectangle_line_1984_coords | canvas_modes_editor_ehr_tarzanehrui_c_rectangle_line_1984_coords |
| canvas_modes_editor_ehr_tarzanehrui_c_rectangle_line_1985_coords | canvas_modes_editor_ehr_tarzanehrui_c_rectangle_line_1985_coords |
| canvas_modes_editor_ehr_tarzanehrui_c_rectangle_line_1986_coords | canvas_modes_editor_ehr_tarzanehrui_c_rectangle_line_1986_coords |
| canvas_modes_editor_ehr_tarzanehrui_c_rectangle_line_2062_coords | canvas_modes_editor_ehr_tarzanehrui_c_rectangle_line_2062_coords |
| canvas_modes_editor_ehr_tarzanehrui_c_rectangle_line_3072_coords | canvas_modes_editor_ehr_tarzanehrui_c_rectangle_line_3072_coords |
| canvas_modes_editor_ehr_tarzanehrui_c_rectangle_line_3100_coords | canvas_modes_editor_ehr_tarzanehrui_c_rectangle_line_3100_coords |
| canvas_modes_editor_ehr_tarzanehrui_c_rectangle_line_3192_coords | canvas_modes_editor_ehr_tarzanehrui_c_rectangle_line_3192_coords |
| canvas_modes_editor_ehr_tarzanehrui_c_rectangle_line_3216_coords | canvas_modes_editor_ehr_tarzanehrui_c_rectangle_line_3216_coords |
| canvas_modes_editor_ehr_tarzanehrui_c_text_line_1994_text | canvas_modes_editor_ehr_tarzanehrui_c_text_line_1994_text |
| canvas_modes_editor_ehr_tarzanehrui_c_text_line_2003_text | canvas_modes_editor_ehr_tarzanehrui_c_text_line_2003_text |
| canvas_modes_editor_ehr_tarzanehrui_c_text_line_2050_text | canvas_modes_editor_ehr_tarzanehrui_c_text_line_2050_text |
| canvas_modes_editor_ehr_tarzanehrui_c_text_line_2051_text | canvas_modes_editor_ehr_tarzanehrui_c_text_line_2051_text |
| canvas_modes_editor_ehr_tarzanehrui_c_text_line_2083_text | canvas_modes_editor_ehr_tarzanehrui_c_text_line_2083_text |
| canvas_modes_editor_ehr_tarzanehrui_c_text_line_2084_text | canvas_modes_editor_ehr_tarzanehrui_c_text_line_2084_text |
| canvas_modes_editor_ehr_tarzanehrui_c_text_line_3115_text | canvas_modes_editor_ehr_tarzanehrui_c_text_line_3115_text |
| canvas_modes_editor_ehr_tarzanehrui_c_text_line_3122_text | canvas_modes_editor_ehr_tarzanehrui_c_text_line_3122_text |
| canvas_modes_editor_ehr_tarzanehrui_c_text_line_3132_text | canvas_modes_editor_ehr_tarzanehrui_c_text_line_3132_text |
| canvas_modes_editor_ehr_tarzanehrui_c_text_line_3228_text | canvas_modes_editor_ehr_tarzanehrui_c_text_line_3228_text |
| canvas_modes_editor_ehr_tarzanehrui_c_text_line_3239_text | canvas_modes_editor_ehr_tarzanehrui_c_text_line_3239_text |
| canvas_modes_editor_ehr_tarzanehrui_canvas_image_line_760_coords | canvas_modes_editor_ehr_tarzanehrui_canvas_image_line_760_coords |
| canvas_modes_editor_ehr_tarzanehrui_canvas_rectangle_line_1300_coords | canvas_modes_editor_ehr_tarzanehrui_canvas_rectangle_line_1300_coords |
| canvas_modes_editor_ehr_tarzanehrui_canvas_window_line_1226_coords | canvas_modes_editor_ehr_tarzanehrui_canvas_window_line_1226_coords |
| canvas_modes_editor_ehr_tarzanehrui_item_text | canvas_modes_editor_ehr_tarzanehrui_item_text |
| canvas_modes_editor_ehr_tarzanehrui_protocol_canvas_rectangle_line_1010_coords | canvas_modes_editor_ehr_tarzanehrui_protocol_canvas_rectangle_line_1010_coords |
| canvas_modes_editor_ehr_tarzanehrui_protocol_canvas_rectangle_line_1011_coords | canvas_modes_editor_ehr_tarzanehrui_protocol_canvas_rectangle_line_1011_coords |
| canvas_modes_editor_ehr_tarzanehrui_row_window_coords | canvas_modes_editor_ehr_tarzanehrui_row_window_coords |
| canvas_modes_editor_ehr_tarzanehrui_save_button_window_coords | canvas_modes_editor_ehr_tarzanehrui_save_button_window_coords |
| canvas_modes_editor_par_tarzannextionpreview_edit_window_coords | canvas_modes_editor_par_tarzannextionpreview_edit_window_coords |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_image_line_591_coords | canvas_modes_editor_par_tarzannextionpreview_screen_canvas_image_line_591_coords |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_image_line_623_coords | canvas_modes_editor_par_tarzannextionpreview_screen_canvas_image_line_623_coords |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_image_line_640_coords | canvas_modes_editor_par_tarzannextionpreview_screen_canvas_image_line_640_coords |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_image_line_692_coords | canvas_modes_editor_par_tarzannextionpreview_screen_canvas_image_line_692_coords |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_image_line_718_coords | canvas_modes_editor_par_tarzannextionpreview_screen_canvas_image_line_718_coords |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_line_line_415_coords | canvas_modes_editor_par_tarzannextionpreview_screen_canvas_line_line_415_coords |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_line_line_432_coords | canvas_modes_editor_par_tarzannextionpreview_screen_canvas_line_line_432_coords |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_line_line_445_coords | canvas_modes_editor_par_tarzannextionpreview_screen_canvas_line_line_445_coords |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_line_line_737_coords | canvas_modes_editor_par_tarzannextionpreview_screen_canvas_line_line_737_coords |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_line_line_738_coords | canvas_modes_editor_par_tarzannextionpreview_screen_canvas_line_line_738_coords |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_line_line_818_coords | canvas_modes_editor_par_tarzannextionpreview_screen_canvas_line_line_818_coords |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_oval_line_740_coords | canvas_modes_editor_par_tarzannextionpreview_screen_canvas_oval_line_740_coords |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_394_coords | canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_394_coords |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_512_coords | canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_512_coords |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_527_coords | canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_527_coords |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_593_coords | canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_593_coords |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_625_coords | canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_625_coords |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_642_coords | canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_642_coords |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_785_coords | canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_785_coords |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_787_coords | canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_787_coords |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_790_coords | canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_790_coords |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_797_coords | canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_797_coords |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_815_coords | canvas_modes_editor_par_tarzannextionpreview_screen_canvas_rectangle_line_815_coords |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_400_text | canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_400_text |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_414_text | canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_414_text |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_421_text | canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_421_text |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_425_text | canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_425_text |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_466_text | canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_466_text |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_483_text | canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_483_text |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_518_text | canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_518_text |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_529_text | canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_529_text |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_594_text | canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_594_text |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_603_text | canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_603_text |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_626_text | canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_626_text |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_643_text | canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_643_text |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_791_text | canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_791_text |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_798_text | canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_798_text |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_799_text | canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_799_text |
| canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_816_text | canvas_modes_editor_par_tarzannextionpreview_screen_canvas_text_line_816_text |
| canvas_modes_editor_par_tarzanparapp_canvas_oval_line_1309_coords | canvas_modes_editor_par_tarzanparapp_canvas_oval_line_1309_coords |
| canvas_modes_editor_par_tarzanparapp_canvas_oval_line_1402_coords | canvas_modes_editor_par_tarzanparapp_canvas_oval_line_1402_coords |
| canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1286_coords | canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1286_coords |
| canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1303_coords | canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1303_coords |
| canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1314_coords | canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1314_coords |
| canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1315_coords | canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1315_coords |
| canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1316_coords | canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1316_coords |
| canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1329_coords | canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1329_coords |
| canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1387_coords | canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1387_coords |
| canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1414_coords | canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1414_coords |
| canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1415_coords | canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1415_coords |
| canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1416_coords | canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1416_coords |
| canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1431_coords | canvas_modes_editor_par_tarzanparapp_canvas_rectangle_line_1431_coords |
| canvas_modes_editor_par_tarzanparapp_canvas_text_line_1310_text | canvas_modes_editor_par_tarzanparapp_canvas_text_line_1310_text |
| canvas_modes_editor_par_tarzanparapp_canvas_text_line_1434_text | canvas_modes_editor_par_tarzanparapp_canvas_text_line_1434_text |
| canvas_modes_editor_par_tarzanparapp_canvas_text_line_1451_text | canvas_modes_editor_par_tarzanparapp_canvas_text_line_1451_text |
| canvas_modes_editor_par_tarzanparapp_canvas_text_line_1455_text | canvas_modes_editor_par_tarzanparapp_canvas_text_line_1455_text |
| canvas_modes_editor_par_tarzanparapp_led_oval_line_485_coords | canvas_modes_editor_par_tarzanparapp_led_oval_line_485_coords |
| canvas_modes_editor_par_tarzanparapp_panel_canvas_window_line_1076_coords | canvas_modes_editor_par_tarzanparapp_panel_canvas_window_line_1076_coords |
| canvas_modes_editor_par_tarzanparapp_text_id_text | canvas_modes_editor_par_tarzanparapp_text_id_text |
| canvas_modes_editor_par_tarzanparpanels_can_image_line_1306_coords | canvas_modes_editor_par_tarzanparpanels_can_image_line_1306_coords |
| canvas_modes_editor_par_tarzanparpanels_can_line_line_1298_coords | canvas_modes_editor_par_tarzanparpanels_can_line_line_1298_coords |
| canvas_modes_editor_par_tarzanparpanels_can_line_line_1299_coords | canvas_modes_editor_par_tarzanparpanels_can_line_line_1299_coords |
| canvas_modes_editor_par_tarzanparpanels_can_line_line_1304_coords | canvas_modes_editor_par_tarzanparpanels_can_line_line_1304_coords |
| canvas_modes_editor_par_tarzanparpanels_can_line_line_1311_coords | canvas_modes_editor_par_tarzanparpanels_can_line_line_1311_coords |
| canvas_modes_editor_par_tarzanparpanels_can_line_line_1326_coords | canvas_modes_editor_par_tarzanparpanels_can_line_line_1326_coords |
| canvas_modes_editor_par_tarzanparpanels_can_line_line_1327_coords | canvas_modes_editor_par_tarzanparpanels_can_line_line_1327_coords |
| canvas_modes_editor_par_tarzanparpanels_can_line_line_510_coords | canvas_modes_editor_par_tarzanparpanels_can_line_line_510_coords |
| canvas_modes_editor_par_tarzanparpanels_can_line_line_664_coords | canvas_modes_editor_par_tarzanparpanels_can_line_line_664_coords |
| canvas_modes_editor_par_tarzanparpanels_can_line_line_665_coords | canvas_modes_editor_par_tarzanparpanels_can_line_line_665_coords |
| canvas_modes_editor_par_tarzanparpanels_can_oval_line_509_coords | canvas_modes_editor_par_tarzanparpanels_can_oval_line_509_coords |
| canvas_modes_editor_par_tarzanparpanels_can_oval_line_511_coords | canvas_modes_editor_par_tarzanparpanels_can_oval_line_511_coords |
| canvas_modes_editor_par_tarzanparpanels_can_oval_line_656_coords | canvas_modes_editor_par_tarzanparpanels_can_oval_line_656_coords |
| canvas_modes_editor_par_tarzanparpanels_can_oval_line_920_coords | canvas_modes_editor_par_tarzanparpanels_can_oval_line_920_coords |
| canvas_modes_editor_par_tarzanparpanels_can_polygon_line_921_coords | canvas_modes_editor_par_tarzanparpanels_can_polygon_line_921_coords |
| canvas_modes_editor_par_tarzanparpanels_can_rectangle_line_899_coords | canvas_modes_editor_par_tarzanparpanels_can_rectangle_line_899_coords |
| canvas_modes_editor_par_tarzanparpanels_can_rectangle_line_901_coords | canvas_modes_editor_par_tarzanparpanels_can_rectangle_line_901_coords |
| canvas_modes_editor_par_tarzanparpanels_can_text_line_1307_text | canvas_modes_editor_par_tarzanparpanels_can_text_line_1307_text |
| canvas_modes_editor_par_tarzanparpanels_can_text_line_1309_text | canvas_modes_editor_par_tarzanparpanels_can_text_line_1309_text |
| canvas_modes_editor_par_tarzanparpanels_can_text_line_1310_text | canvas_modes_editor_par_tarzanparpanels_can_text_line_1310_text |
| canvas_modes_editor_par_tarzanparpanels_can_text_line_1329_text | canvas_modes_editor_par_tarzanparpanels_can_text_line_1329_text |
| canvas_modes_editor_par_tarzanparpanels_can_text_line_1331_text | canvas_modes_editor_par_tarzanparpanels_can_text_line_1331_text |
| canvas_modes_editor_par_tarzanparpanels_canvas_line_line_825_coords | canvas_modes_editor_par_tarzanparpanels_canvas_line_line_825_coords |
| canvas_modes_editor_par_tarzanparpanels_canvas_line_line_826_coords | canvas_modes_editor_par_tarzanparpanels_canvas_line_line_826_coords |
| canvas_modes_editor_par_tarzanparpanels_canvas_oval_line_1575_coords | canvas_modes_editor_par_tarzanparpanels_canvas_oval_line_1575_coords |
| canvas_modes_editor_par_tarzanparpanels_canvas_oval_line_830_coords | canvas_modes_editor_par_tarzanparpanels_canvas_oval_line_830_coords |
| canvas_modes_editor_par_tarzanparpanels_canvas_polygon_line_828_coords | canvas_modes_editor_par_tarzanparpanels_canvas_polygon_line_828_coords |
| canvas_modes_editor_par_tarzanparpanels_canvas_rectangle_line_1449_coords | canvas_modes_editor_par_tarzanparpanels_canvas_rectangle_line_1449_coords |
| canvas_modes_editor_par_tarzanparpanels_canvas_rectangle_line_1450_coords | canvas_modes_editor_par_tarzanparpanels_canvas_rectangle_line_1450_coords |
| canvas_modes_editor_par_tarzanparpanels_canvas_rectangle_line_1451_coords | canvas_modes_editor_par_tarzanparpanels_canvas_rectangle_line_1451_coords |
| canvas_modes_editor_par_tarzanparpanels_old_c_line_line_3118_coords | canvas_modes_editor_par_tarzanparpanels_old_c_line_line_3118_coords |
| canvas_modes_editor_par_tarzanparpanels_old_c_line_line_3119_coords | canvas_modes_editor_par_tarzanparpanels_old_c_line_line_3119_coords |
| canvas_modes_editor_par_tarzanparpanels_old_c_oval_line_1979_coords | canvas_modes_editor_par_tarzanparpanels_old_c_oval_line_1979_coords |
| canvas_modes_editor_par_tarzanparpanels_old_c_oval_line_1980_coords | canvas_modes_editor_par_tarzanparpanels_old_c_oval_line_1980_coords |
| canvas_modes_editor_par_tarzanparpanels_old_c_oval_line_2212_coords | canvas_modes_editor_par_tarzanparpanels_old_c_oval_line_2212_coords |
| canvas_modes_editor_par_tarzanparpanels_old_c_oval_line_3111_coords | canvas_modes_editor_par_tarzanparpanels_old_c_oval_line_3111_coords |
| canvas_modes_editor_par_tarzanparpanels_old_c_oval_line_344_coords | canvas_modes_editor_par_tarzanparpanels_old_c_oval_line_344_coords |
| canvas_modes_editor_par_tarzanparpanels_old_c_polygon_line_2213_coords | canvas_modes_editor_par_tarzanparpanels_old_c_polygon_line_2213_coords |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_image_line_1549_coords | canvas_modes_editor_par_tarzanparpanels_old_canvas_image_line_1549_coords |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_1538_coords | canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_1538_coords |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_1539_coords | canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_1539_coords |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_1545_coords | canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_1545_coords |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_1563_coords | canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_1563_coords |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_1581_coords | canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_1581_coords |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_1582_coords | canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_1582_coords |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_1784_coords | canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_1784_coords |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_1785_coords | canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_1785_coords |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_2481_coords | canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_2481_coords |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_767_coords | canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_767_coords |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_780_coords | canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_780_coords |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_781_coords | canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_781_coords |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_784_coords | canvas_modes_editor_par_tarzanparpanels_old_canvas_line_line_784_coords |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_oval_line_1216_coords | canvas_modes_editor_par_tarzanparpanels_old_canvas_oval_line_1216_coords |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_oval_line_1796_coords | canvas_modes_editor_par_tarzanparpanels_old_canvas_oval_line_1796_coords |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_oval_line_2480_coords | canvas_modes_editor_par_tarzanparpanels_old_canvas_oval_line_2480_coords |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_oval_line_2482_coords | canvas_modes_editor_par_tarzanparpanels_old_canvas_oval_line_2482_coords |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_polygon_line_1786_coords | canvas_modes_editor_par_tarzanparpanels_old_canvas_polygon_line_1786_coords |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_rectangle_line_1113_coords | canvas_modes_editor_par_tarzanparpanels_old_canvas_rectangle_line_1113_coords |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_rectangle_line_1114_coords | canvas_modes_editor_par_tarzanparpanels_old_canvas_rectangle_line_1114_coords |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_rectangle_line_1116_coords | canvas_modes_editor_par_tarzanparpanels_old_canvas_rectangle_line_1116_coords |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_rectangle_line_1117_coords | canvas_modes_editor_par_tarzanparpanels_old_canvas_rectangle_line_1117_coords |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_rectangle_line_1313_coords | canvas_modes_editor_par_tarzanparpanels_old_canvas_rectangle_line_1313_coords |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_rectangle_line_1314_coords | canvas_modes_editor_par_tarzanparpanels_old_canvas_rectangle_line_1314_coords |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_rectangle_line_1315_coords | canvas_modes_editor_par_tarzanparpanels_old_canvas_rectangle_line_1315_coords |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_text_line_1551_text | canvas_modes_editor_par_tarzanparpanels_old_canvas_text_line_1551_text |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_text_line_1554_text | canvas_modes_editor_par_tarzanparpanels_old_canvas_text_line_1554_text |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_text_line_1555_text | canvas_modes_editor_par_tarzanparpanels_old_canvas_text_line_1555_text |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_text_line_1586_text | canvas_modes_editor_par_tarzanparpanels_old_canvas_text_line_1586_text |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_text_line_766_text | canvas_modes_editor_par_tarzanparpanels_old_canvas_text_line_766_text |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_text_line_785_text | canvas_modes_editor_par_tarzanparpanels_old_canvas_text_line_785_text |
| canvas_modes_editor_par_tarzanparpanels_old_canvas_window_line_119_coords | canvas_modes_editor_par_tarzanparpanels_old_canvas_window_line_119_coords |
| canvas_modes_editor_par_tarzanparpanels_old_dot_oval_line_378_coords | canvas_modes_editor_par_tarzanparpanels_old_dot_oval_line_378_coords |
| canvas_modes_editor_par_tarzanparpanels_old_led_oval_line_1049_coords | canvas_modes_editor_par_tarzanparpanels_old_led_oval_line_1049_coords |
| canvas_modes_editor_par_tarzanparpanels_old_led_oval_line_1050_coords | canvas_modes_editor_par_tarzanparpanels_old_led_oval_line_1050_coords |
| canvas_modes_editor_par_tarzanparpanels_old_rect_coords | canvas_modes_editor_par_tarzanparpanels_old_rect_coords |
| canvas_modes_editor_par_tarzanparpanels_old_self_rectangle_line_1346_coords | canvas_modes_editor_par_tarzanparpanels_old_self_rectangle_line_1346_coords |
| canvas_modes_editor_par_tarzanparpanels_old_self_rectangle_line_1347_coords | canvas_modes_editor_par_tarzanparpanels_old_self_rectangle_line_1347_coords |
| canvas_modes_editor_par_tarzanparpanels_old_window_id_coords | canvas_modes_editor_par_tarzanparpanels_old_window_id_coords |
| canvas_modes_editor_par_tarzanparpanels_self_rectangle_line_185_coords | canvas_modes_editor_par_tarzanparpanels_self_rectangle_line_185_coords |
| canvas_modes_editor_par_tarzanparpanels_window_id_coords | canvas_modes_editor_par_tarzanparpanels_window_id_coords |
| canvas_modes_editor_par_tarzanparwidgets_c_line_line_304_coords | canvas_modes_editor_par_tarzanparwidgets_c_line_line_304_coords |
| canvas_modes_editor_par_tarzanparwidgets_c_oval_line_299_coords | canvas_modes_editor_par_tarzanparwidgets_c_oval_line_299_coords |
| canvas_modes_editor_par_tarzanparwidgets_c_oval_line_300_coords | canvas_modes_editor_par_tarzanparwidgets_c_oval_line_300_coords |
| canvas_modes_editor_par_tarzanparwidgets_c_oval_line_305_coords | canvas_modes_editor_par_tarzanparwidgets_c_oval_line_305_coords |
| canvas_modes_editor_par_tarzanparwidgets_self_oval_line_59_coords | canvas_modes_editor_par_tarzanparwidgets_self_oval_line_59_coords |
| canvas_modes_editor_par_tarzanparwidgets_self_oval_line_60_coords | canvas_modes_editor_par_tarzanparwidgets_self_oval_line_60_coords |
| canvas_modes_editor_par_tarzanparwidgets_self_oval_line_64_coords | canvas_modes_editor_par_tarzanparwidgets_self_oval_line_64_coords |
| canvas_modes_editor_par_tarzanparwidgets_self_oval_line_65_coords | canvas_modes_editor_par_tarzanparwidgets_self_oval_line_65_coords |
| canvas_modes_editor_par_tarzanparwidgets_self_rectangle_line_90_coords | canvas_modes_editor_par_tarzanparwidgets_self_rectangle_line_90_coords |
| canvas_modes_editor_tarzanaxissandbox_c_line_line_826_coords | canvas_modes_editor_tarzanaxissandbox_c_line_line_826_coords |
| canvas_modes_editor_tarzanaxissandbox_c_line_line_833_coords | canvas_modes_editor_tarzanaxissandbox_c_line_line_833_coords |
| canvas_modes_editor_tarzanaxissandbox_c_line_line_852_coords | canvas_modes_editor_tarzanaxissandbox_c_line_line_852_coords |
| canvas_modes_editor_tarzanaxissandbox_c_line_line_859_coords | canvas_modes_editor_tarzanaxissandbox_c_line_line_859_coords |
| canvas_modes_editor_tarzanaxissandbox_c_line_line_871_coords | canvas_modes_editor_tarzanaxissandbox_c_line_line_871_coords |
| canvas_modes_editor_tarzanaxissandbox_c_line_line_872_coords | canvas_modes_editor_tarzanaxissandbox_c_line_line_872_coords |
| canvas_modes_editor_tarzanaxissandbox_c_line_line_886_coords | canvas_modes_editor_tarzanaxissandbox_c_line_line_886_coords |
| canvas_modes_editor_tarzanaxissandbox_c_line_line_898_coords | canvas_modes_editor_tarzanaxissandbox_c_line_line_898_coords |
| canvas_modes_editor_tarzanaxissandbox_c_line_line_900_coords | canvas_modes_editor_tarzanaxissandbox_c_line_line_900_coords |
| canvas_modes_editor_tarzanaxissandbox_c_oval_line_868_coords | canvas_modes_editor_tarzanaxissandbox_c_oval_line_868_coords |
| canvas_modes_editor_tarzanaxissandbox_c_rectangle_line_812_coords | canvas_modes_editor_tarzanaxissandbox_c_rectangle_line_812_coords |
| canvas_modes_editor_tarzanaxissandbox_c_rectangle_line_819_coords | canvas_modes_editor_tarzanaxissandbox_c_rectangle_line_819_coords |
| canvas_modes_editor_tarzanaxissandbox_c_rectangle_line_820_coords | canvas_modes_editor_tarzanaxissandbox_c_rectangle_line_820_coords |
| canvas_modes_editor_tarzanaxissandbox_c_rectangle_line_821_coords | canvas_modes_editor_tarzanaxissandbox_c_rectangle_line_821_coords |
| canvas_modes_editor_tarzanaxissandbox_c_rectangle_line_880_coords | canvas_modes_editor_tarzanaxissandbox_c_rectangle_line_880_coords |
| canvas_modes_editor_tarzanaxissandbox_c_text_line_827_text | canvas_modes_editor_tarzanaxissandbox_c_text_line_827_text |
| canvas_modes_editor_tarzanaxissandbox_c_text_line_834_text | canvas_modes_editor_tarzanaxissandbox_c_text_line_834_text |
| canvas_modes_editor_tarzanaxissandbox_c_text_line_873_text | canvas_modes_editor_tarzanaxissandbox_c_text_line_873_text |
| canvas_modes_editor_tarzanaxissandbox_c_text_line_874_text | canvas_modes_editor_tarzanaxissandbox_c_text_line_874_text |
| canvas_modes_editor_tarzanaxissandbox_c_text_line_901_text | canvas_modes_editor_tarzanaxissandbox_c_text_line_901_text |
| canvas_modes_editor_tarzanaxissandbox_c_text_line_902_text | canvas_modes_editor_tarzanaxissandbox_c_text_line_902_text |
| canvas_modes_editor_tarzanehrtakesandbox_canvas_image_line_553_coords | canvas_modes_editor_tarzanehrtakesandbox_canvas_image_line_553_coords |
| canvas_modes_editor_tarzanehrtakesandbox_item_text | canvas_modes_editor_tarzanehrtakesandbox_item_text |
| canvas_modes_editor_tarzanehrtakesandbox_protocol_canvas_rectangle_line_1057_coords | canvas_modes_editor_tarzanehrtakesandbox_protocol_canvas_rectangle_line_1057_coords |
| canvas_modes_editor_tarzanehrtakesandbox_protocol_canvas_rectangle_line_1058_coords | canvas_modes_editor_tarzanehrtakesandbox_protocol_canvas_rectangle_line_1058_coords |
| canvas_modes_editor_tarzanehrtakesandbox_protocol_title_id_text | canvas_modes_editor_tarzanehrtakesandbox_protocol_title_id_text |
| canvas_modes_editor_tarzanehrtakesandbox_row_window_coords | canvas_modes_editor_tarzanehrtakesandbox_row_window_coords |
| canvas_modes_editor_tarzanehrtakesandbox_save_button_window_coords | canvas_modes_editor_tarzanehrtakesandbox_save_button_window_coords |
| canvas_modes_editor_tarzankhr_c_image_line_1518_coords | canvas_modes_editor_tarzankhr_c_image_line_1518_coords |
| canvas_modes_editor_tarzankhr_c_image_line_1533_coords | canvas_modes_editor_tarzankhr_c_image_line_1533_coords |
| canvas_modes_editor_tarzankhr_c_image_line_623_coords | canvas_modes_editor_tarzankhr_c_image_line_623_coords |
| canvas_modes_editor_tarzankhr_c_line_line_1545_coords | canvas_modes_editor_tarzankhr_c_line_line_1545_coords |
| canvas_modes_editor_tarzankhr_c_line_line_1546_coords | canvas_modes_editor_tarzankhr_c_line_line_1546_coords |
| canvas_modes_editor_tarzankhr_c_line_line_1555_coords | canvas_modes_editor_tarzankhr_c_line_line_1555_coords |
| canvas_modes_editor_tarzankhr_c_line_line_1570_coords | canvas_modes_editor_tarzankhr_c_line_line_1570_coords |
| canvas_modes_editor_tarzankhr_c_line_line_1571_coords | canvas_modes_editor_tarzankhr_c_line_line_1571_coords |
| canvas_modes_editor_tarzankhr_c_line_line_1593_coords | canvas_modes_editor_tarzankhr_c_line_line_1593_coords |
| canvas_modes_editor_tarzankhr_c_line_line_1597_coords | canvas_modes_editor_tarzankhr_c_line_line_1597_coords |
| canvas_modes_editor_tarzankhr_c_oval_line_1589_coords | canvas_modes_editor_tarzankhr_c_oval_line_1589_coords |
| canvas_modes_editor_tarzankhr_c_oval_line_1590_coords | canvas_modes_editor_tarzankhr_c_oval_line_1590_coords |
| canvas_modes_editor_tarzankhr_c_polygon_line_1553_coords | canvas_modes_editor_tarzankhr_c_polygon_line_1553_coords |
| canvas_modes_editor_tarzankhr_c_polygon_line_1602_coords | canvas_modes_editor_tarzankhr_c_polygon_line_1602_coords |
| canvas_modes_editor_tarzankhr_c_rectangle_line_1548_coords | canvas_modes_editor_tarzankhr_c_rectangle_line_1548_coords |
| canvas_modes_editor_tarzankhr_c_rectangle_line_1573_coords | canvas_modes_editor_tarzankhr_c_rectangle_line_1573_coords |
| canvas_modes_editor_tarzankhr_c_text_line_1457_text | canvas_modes_editor_tarzankhr_c_text_line_1457_text |
| canvas_modes_editor_tarzankhr_c_text_line_1465_text | canvas_modes_editor_tarzankhr_c_text_line_1465_text |
| canvas_modes_editor_tarzankhr_c_text_line_1472_text | canvas_modes_editor_tarzankhr_c_text_line_1472_text |
| canvas_modes_editor_tarzankhr_c_text_line_1473_text | canvas_modes_editor_tarzankhr_c_text_line_1473_text |
| canvas_modes_editor_tarzankhr_c_text_line_1474_text | canvas_modes_editor_tarzankhr_c_text_line_1474_text |
| canvas_modes_editor_tarzankhr_c_text_line_1481_text | canvas_modes_editor_tarzankhr_c_text_line_1481_text |
| canvas_modes_editor_tarzankhr_c_text_line_1486_text | canvas_modes_editor_tarzankhr_c_text_line_1486_text |
| canvas_modes_editor_tarzankhr_c_text_line_1496_text | canvas_modes_editor_tarzankhr_c_text_line_1496_text |
| canvas_modes_editor_tarzankhr_c_text_line_1503_text | canvas_modes_editor_tarzankhr_c_text_line_1503_text |
| canvas_modes_editor_tarzankhr_c_text_line_1520_text | canvas_modes_editor_tarzankhr_c_text_line_1520_text |
| canvas_modes_editor_tarzankhr_c_text_line_1522_text | canvas_modes_editor_tarzankhr_c_text_line_1522_text |
| canvas_modes_editor_tarzankhr_c_text_line_1525_text | canvas_modes_editor_tarzankhr_c_text_line_1525_text |
| canvas_modes_editor_tarzankhr_c_text_line_1542_text | canvas_modes_editor_tarzankhr_c_text_line_1542_text |
| canvas_modes_editor_tarzankhr_c_text_line_1549_text | canvas_modes_editor_tarzankhr_c_text_line_1549_text |
| canvas_modes_editor_tarzankhr_c_text_line_1554_text | canvas_modes_editor_tarzankhr_c_text_line_1554_text |
| canvas_modes_editor_tarzankhr_c_text_line_1556_text | canvas_modes_editor_tarzankhr_c_text_line_1556_text |
| canvas_modes_editor_tarzankhr_c_text_line_1564_text | canvas_modes_editor_tarzankhr_c_text_line_1564_text |
| canvas_modes_editor_tarzankhr_c_text_line_1569_text | canvas_modes_editor_tarzankhr_c_text_line_1569_text |
| canvas_modes_editor_tarzankhr_c_text_line_1574_text | canvas_modes_editor_tarzankhr_c_text_line_1574_text |
| canvas_modes_editor_tarzankhr_c_text_line_1576_text | canvas_modes_editor_tarzankhr_c_text_line_1576_text |
| canvas_modes_editor_tarzankhr_c_text_line_1578_text | canvas_modes_editor_tarzankhr_c_text_line_1578_text |
| canvas_modes_editor_tarzankhr_c_text_line_1579_text | canvas_modes_editor_tarzankhr_c_text_line_1579_text |
| canvas_modes_editor_tarzankhr_c_text_line_1580_text | canvas_modes_editor_tarzankhr_c_text_line_1580_text |
| canvas_modes_editor_tarzankhr_c_text_line_1603_text | canvas_modes_editor_tarzankhr_c_text_line_1603_text |
| canvas_modes_editor_tarzankhr_c_text_line_1604_text | canvas_modes_editor_tarzankhr_c_text_line_1604_text |
| canvas_modes_editor_tarzankhr_c_text_line_1605_text | canvas_modes_editor_tarzankhr_c_text_line_1605_text |
| canvas_modes_editor_tarzankhr_c_text_line_615_text | canvas_modes_editor_tarzankhr_c_text_line_615_text |
| canvas_modes_editor_tarzankhr_c_text_line_625_text | canvas_modes_editor_tarzankhr_c_text_line_625_text |
| canvas_modes_editor_tarzankhr_c_text_line_627_text | canvas_modes_editor_tarzankhr_c_text_line_627_text |
| canvas_modes_editor_tarzankhr_c_text_line_629_text | canvas_modes_editor_tarzankhr_c_text_line_629_text |
| canvas_modes_editor_tarzantakeprotocollight_canvas_image_line_860_coords | canvas_modes_editor_tarzantakeprotocollight_canvas_image_line_860_coords |
| canvas_modes_editor_tarzantakeprotocollight_item_text | canvas_modes_editor_tarzantakeprotocollight_item_text |
| canvas_modes_editor_tarzantakeprotocollight_protocol_canvas_rectangle_line_1215_coords | canvas_modes_editor_tarzantakeprotocollight_protocol_canvas_rectangle_line_1215_coords |
| canvas_modes_editor_tarzantakeprotocollight_protocol_canvas_rectangle_line_1216_coords | canvas_modes_editor_tarzantakeprotocollight_protocol_canvas_rectangle_line_1216_coords |
| canvas_modes_editor_tarzantakeprotocollight_protocol_title_id_text | canvas_modes_editor_tarzantakeprotocollight_protocol_title_id_text |
| canvas_modes_editor_tarzantakeprotocollight_row_window_coords | canvas_modes_editor_tarzantakeprotocollight_row_window_coords |
| canvas_modes_editor_tarzantakeprotocollight_save_button_window_coords | canvas_modes_editor_tarzantakeprotocollight_save_button_window_coords |
| canvas_vision_tarzanvisionsetup_window_id_coords | canvas_vision_tarzanvisionsetup_window_id_coords |
| ehr_axis_0_curve | ehr_axis_0_curve |
| ehr_axis_0_metrics | ehr_axis_0_metrics |
| ehr_axis_0_step_preview | ehr_axis_0_step_preview |
| ehr_axis_1_curve | ehr_axis_1_curve |
| ehr_axis_1_metrics | ehr_axis_1_metrics |
| ehr_axis_1_step_preview | ehr_axis_1_step_preview |
| ehr_axis_2_curve | ehr_axis_2_curve |
| ehr_axis_2_metrics | ehr_axis_2_metrics |
| ehr_axis_2_step_preview | ehr_axis_2_step_preview |
| ehr_axis_3_curve | ehr_axis_3_curve |
| ehr_axis_3_metrics | ehr_axis_3_metrics |
| ehr_axis_3_step_preview | ehr_axis_3_step_preview |
| ehr_axis_4_curve | ehr_axis_4_curve |
| ehr_axis_4_metrics | ehr_axis_4_metrics |
| ehr_axis_4_step_preview | ehr_axis_4_step_preview |
| ehr_axis_5_curve | ehr_axis_5_curve |
| ehr_axis_5_metrics | ehr_axis_5_metrics |
| ehr_axis_5_step_preview | ehr_axis_5_step_preview |
| ehr_take_slot_0_status | ehr_take_slot_0_status |
| ehr_take_slot_1_status | ehr_take_slot_1_status |
| ehr_take_slot_2_status | ehr_take_slot_2_status |
| ehr_take_slot_3_status | ehr_take_slot_3_status |
| ehr_take_slot_4_status | ehr_take_slot_4_status |
| ehr_take_slot_5_status | ehr_take_slot_5_status |
| ehr_take_slot_6_status | ehr_take_slot_6_status |
| ehr_take_slot_7_status | ehr_take_slot_7_status |
| face_rec.b_home.pic | nextion_face_rec_b_home_pic |
| face_rec.b_home.val | nextion_face_rec_b_home_val |
| face_rec.t0.txt | nextion_face_rec_t0_txt |
| keybdA.Event.en | nextion_keybda_event_en |
| keybdA.Event.tim | nextion_keybda_event_tim |
| keybdA.b0.pic | nextion_keybda_b0_pic |
| keybdA.b0.val | nextion_keybda_b0_val |
| keybdA.b1.pic | nextion_keybda_b1_pic |
| keybdA.b1.val | nextion_keybda_b1_val |
| keybdA.b2.pic | nextion_keybda_b2_pic |
| keybdA.b2.val | nextion_keybda_b2_val |
| keybdA.b20.pic | nextion_keybda_b20_pic |
| keybdA.b20.val | nextion_keybda_b20_val |
| keybdA.b200.pic | nextion_keybda_b200_pic |
| keybdA.b200.val | nextion_keybda_b200_val |
| keybdA.b201.pic | nextion_keybda_b201_pic |
| keybdA.b201.val | nextion_keybda_b201_val |
| keybdA.b21.pic | nextion_keybda_b21_pic |
| keybdA.b21.val | nextion_keybda_b21_val |
| keybdA.b210.pic | nextion_keybda_b210_pic |
| keybdA.b210.val | nextion_keybda_b210_val |
| keybdA.b22.pic | nextion_keybda_b22_pic |
| keybdA.b22.val | nextion_keybda_b22_val |
| keybdA.b220.pic | nextion_keybda_b220_pic |
| keybdA.b220.val | nextion_keybda_b220_val |
| keybdA.b23.pic | nextion_keybda_b23_pic |
| keybdA.b23.val | nextion_keybda_b23_val |
| keybdA.b230.pic | nextion_keybda_b230_pic |
| keybdA.b230.val | nextion_keybda_b230_val |
| keybdA.b231.pic | nextion_keybda_b231_pic |
| keybdA.b231.val | nextion_keybda_b231_val |
| keybdA.b232.pic | nextion_keybda_b232_pic |
| keybdA.b232.val | nextion_keybda_b232_val |
| keybdA.b24.pic | nextion_keybda_b24_pic |
| keybdA.b24.val | nextion_keybda_b24_val |
| keybdA.b240.pic | nextion_keybda_b240_pic |
| keybdA.b240.val | nextion_keybda_b240_val |
| keybdA.b241.pic | nextion_keybda_b241_pic |
| keybdA.b241.val | nextion_keybda_b241_val |
| keybdA.b242.pic | nextion_keybda_b242_pic |
| keybdA.b242.val | nextion_keybda_b242_val |
| keybdA.b243.pic | nextion_keybda_b243_pic |
| keybdA.b243.val | nextion_keybda_b243_val |
| keybdA.b244.pic | nextion_keybda_b244_pic |
| keybdA.b244.val | nextion_keybda_b244_val |
| keybdA.b249.pic | nextion_keybda_b249_pic |
| keybdA.b249.val | nextion_keybda_b249_val |
| keybdA.b25.pic | nextion_keybda_b25_pic |
| keybdA.b25.val | nextion_keybda_b25_val |
| keybdA.b251.pic | nextion_keybda_b251_pic |
| keybdA.b251.val | nextion_keybda_b251_val |
| keybdA.b26.pic | nextion_keybda_b26_pic |
| keybdA.b26.val | nextion_keybda_b26_val |
| keybdA.b27.pic | nextion_keybda_b27_pic |
| keybdA.b27.val | nextion_keybda_b27_val |
| keybdA.b28.pic | nextion_keybda_b28_pic |
| keybdA.b28.val | nextion_keybda_b28_val |
| keybdA.b3.pic | nextion_keybda_b3_pic |
| keybdA.b3.val | nextion_keybda_b3_val |
| keybdA.b4.pic | nextion_keybda_b4_pic |
| keybdA.b4.val | nextion_keybda_b4_val |
| keybdA.b40.pic | nextion_keybda_b40_pic |
| keybdA.b40.val | nextion_keybda_b40_val |
| keybdA.b41.pic | nextion_keybda_b41_pic |
| keybdA.b41.val | nextion_keybda_b41_val |
| keybdA.b42.pic | nextion_keybda_b42_pic |
| keybdA.b42.val | nextion_keybda_b42_val |
| keybdA.b43.pic | nextion_keybda_b43_pic |
| keybdA.b43.val | nextion_keybda_b43_val |
| keybdA.b44.pic | nextion_keybda_b44_pic |
| keybdA.b44.val | nextion_keybda_b44_val |
| keybdA.b45.pic | nextion_keybda_b45_pic |
| keybdA.b45.val | nextion_keybda_b45_val |
| keybdA.b46.pic | nextion_keybda_b46_pic |
| keybdA.b46.val | nextion_keybda_b46_val |
| keybdA.b5.pic | nextion_keybda_b5_pic |
| keybdA.b5.val | nextion_keybda_b5_val |
| keybdA.b6.pic | nextion_keybda_b6_pic |
| keybdA.b6.val | nextion_keybda_b6_val |
| keybdA.b7.pic | nextion_keybda_b7_pic |
| keybdA.b7.val | nextion_keybda_b7_val |
| keybdA.b8.pic | nextion_keybda_b8_pic |
| keybdA.b8.val | nextion_keybda_b8_val |
| keybdA.b9.pic | nextion_keybda_b9_pic |
| keybdA.b9.val | nextion_keybda_b9_val |
| keybdA.input.txt | nextion_keybda_input_txt |
| keybdA.inputlenth.val | nextion_keybda_inputlenth_val |
| keybdA.loadcmpid.val | nextion_keybda_loadcmpid_val |
| keybdA.loadpageid.val | nextion_keybda_loadpageid_val |
| keybdA.refshow.state | nextion_keybda_refshow_state |
| keybdA.show.txt | nextion_keybda_show_txt |
| keybdA.temp.val | nextion_keybda_temp_val |
| keybdA.temp2.val | nextion_keybda_temp2_val |
| keybdA.tempstr.txt | nextion_keybda_tempstr_txt |
| keybdA.tm0.en | nextion_keybda_tm0_en |
| keybdA.tm0.tim | nextion_keybda_tm0_tim |
| khr_input_marker | khr_input_marker |
| khr_output_marker | khr_output_marker |
| khr_status | khr_status |
| layout_panel_status | layout_panel_status |
| layout_selected_cell | layout_selected_cell |
| layout_zone_label | layout_zone_label |
| level_xyz.Event.en | nextion_level_xyz_event_en |
| level_xyz.Event.tim | nextion_level_xyz_event_tim |
| level_xyz.b_home.pic | nextion_level_xyz_b_home_pic |
| level_xyz.b_home.val | nextion_level_xyz_b_home_val |
| level_xyz.p0.pic | nextion_level_xyz_p0_pic |
| level_xyz.tm0.en | nextion_level_xyz_tm0_en |
| level_xyz.tm0.tim | nextion_level_xyz_tm0_tim |
| level_xyz.va0.val | nextion_level_xyz_va0_val |
| level_xyz.va1.val | nextion_level_xyz_va1_val |
| level_xyz.va2.val | nextion_level_xyz_va2_val |
| level_xyz.va3.val | nextion_level_xyz_va3_val |
| nextion_boot_event_en | nextion_boot_event_en |
| nextion_boot_event_tim | nextion_boot_event_tim |
| nextion_boot_p0_pic | nextion_boot_p0_pic |
| nextion_boot_tm0_en | nextion_boot_tm0_en |
| nextion_boot_tm0_tim | nextion_boot_tm0_tim |
| nextion_boot_va0_val | nextion_boot_va0_val |
| nextion_face_rec_b_home_pic | nextion_face_rec_b_home_pic |
| nextion_face_rec_b_home_val | nextion_face_rec_b_home_val |
| nextion_face_rec_t0_txt | nextion_face_rec_t0_txt |
| nextion_keybda_b0_pic | nextion_keybda_b0_pic |
| nextion_keybda_b0_val | nextion_keybda_b0_val |
| nextion_keybda_b1_pic | nextion_keybda_b1_pic |
| nextion_keybda_b1_val | nextion_keybda_b1_val |
| nextion_keybda_b200_pic | nextion_keybda_b200_pic |
| nextion_keybda_b200_val | nextion_keybda_b200_val |
| nextion_keybda_b201_pic | nextion_keybda_b201_pic |
| nextion_keybda_b201_val | nextion_keybda_b201_val |
| nextion_keybda_b20_pic | nextion_keybda_b20_pic |
| nextion_keybda_b20_val | nextion_keybda_b20_val |
| nextion_keybda_b210_pic | nextion_keybda_b210_pic |
| nextion_keybda_b210_val | nextion_keybda_b210_val |
| nextion_keybda_b21_pic | nextion_keybda_b21_pic |
| nextion_keybda_b21_val | nextion_keybda_b21_val |
| nextion_keybda_b220_pic | nextion_keybda_b220_pic |
| nextion_keybda_b220_val | nextion_keybda_b220_val |
| nextion_keybda_b22_pic | nextion_keybda_b22_pic |
| nextion_keybda_b22_val | nextion_keybda_b22_val |
| nextion_keybda_b230_pic | nextion_keybda_b230_pic |
| nextion_keybda_b230_val | nextion_keybda_b230_val |
| nextion_keybda_b231_pic | nextion_keybda_b231_pic |
| nextion_keybda_b231_val | nextion_keybda_b231_val |
| nextion_keybda_b232_pic | nextion_keybda_b232_pic |
| nextion_keybda_b232_val | nextion_keybda_b232_val |
| nextion_keybda_b23_pic | nextion_keybda_b23_pic |
| nextion_keybda_b23_val | nextion_keybda_b23_val |
| nextion_keybda_b240_pic | nextion_keybda_b240_pic |
| nextion_keybda_b240_val | nextion_keybda_b240_val |
| nextion_keybda_b241_pic | nextion_keybda_b241_pic |
| nextion_keybda_b241_val | nextion_keybda_b241_val |
| nextion_keybda_b242_pic | nextion_keybda_b242_pic |
| nextion_keybda_b242_val | nextion_keybda_b242_val |
| nextion_keybda_b243_pic | nextion_keybda_b243_pic |
| nextion_keybda_b243_val | nextion_keybda_b243_val |
| nextion_keybda_b244_pic | nextion_keybda_b244_pic |
| nextion_keybda_b244_val | nextion_keybda_b244_val |
| nextion_keybda_b249_pic | nextion_keybda_b249_pic |
| nextion_keybda_b249_val | nextion_keybda_b249_val |
| nextion_keybda_b24_pic | nextion_keybda_b24_pic |
| nextion_keybda_b24_val | nextion_keybda_b24_val |
| nextion_keybda_b251_pic | nextion_keybda_b251_pic |
| nextion_keybda_b251_val | nextion_keybda_b251_val |
| nextion_keybda_b25_pic | nextion_keybda_b25_pic |
| nextion_keybda_b25_val | nextion_keybda_b25_val |
| nextion_keybda_b26_pic | nextion_keybda_b26_pic |
| nextion_keybda_b26_val | nextion_keybda_b26_val |
| nextion_keybda_b27_pic | nextion_keybda_b27_pic |
| nextion_keybda_b27_val | nextion_keybda_b27_val |
| nextion_keybda_b28_pic | nextion_keybda_b28_pic |
| nextion_keybda_b28_val | nextion_keybda_b28_val |
| nextion_keybda_b2_pic | nextion_keybda_b2_pic |
| nextion_keybda_b2_val | nextion_keybda_b2_val |
| nextion_keybda_b3_pic | nextion_keybda_b3_pic |
| nextion_keybda_b3_val | nextion_keybda_b3_val |
| nextion_keybda_b40_pic | nextion_keybda_b40_pic |
| nextion_keybda_b40_val | nextion_keybda_b40_val |
| nextion_keybda_b41_pic | nextion_keybda_b41_pic |
| nextion_keybda_b41_val | nextion_keybda_b41_val |
| nextion_keybda_b42_pic | nextion_keybda_b42_pic |
| nextion_keybda_b42_val | nextion_keybda_b42_val |
| nextion_keybda_b43_pic | nextion_keybda_b43_pic |
| nextion_keybda_b43_val | nextion_keybda_b43_val |
| nextion_keybda_b44_pic | nextion_keybda_b44_pic |
| nextion_keybda_b44_val | nextion_keybda_b44_val |
| nextion_keybda_b45_pic | nextion_keybda_b45_pic |
| nextion_keybda_b45_val | nextion_keybda_b45_val |
| nextion_keybda_b46_pic | nextion_keybda_b46_pic |
| nextion_keybda_b46_val | nextion_keybda_b46_val |
| nextion_keybda_b4_pic | nextion_keybda_b4_pic |
| nextion_keybda_b4_val | nextion_keybda_b4_val |
| nextion_keybda_b5_pic | nextion_keybda_b5_pic |
| nextion_keybda_b5_val | nextion_keybda_b5_val |
| nextion_keybda_b6_pic | nextion_keybda_b6_pic |
| nextion_keybda_b6_val | nextion_keybda_b6_val |
| nextion_keybda_b7_pic | nextion_keybda_b7_pic |
| nextion_keybda_b7_val | nextion_keybda_b7_val |
| nextion_keybda_b8_pic | nextion_keybda_b8_pic |
| nextion_keybda_b8_val | nextion_keybda_b8_val |
| nextion_keybda_b9_pic | nextion_keybda_b9_pic |
| nextion_keybda_b9_val | nextion_keybda_b9_val |
| nextion_keybda_event_en | nextion_keybda_event_en |
| nextion_keybda_event_tim | nextion_keybda_event_tim |
| nextion_keybda_input_txt | nextion_keybda_input_txt |
| nextion_keybda_inputlenth_val | nextion_keybda_inputlenth_val |
| nextion_keybda_loadcmpid_val | nextion_keybda_loadcmpid_val |
| nextion_keybda_loadpageid_val | nextion_keybda_loadpageid_val |
| nextion_keybda_refshow_state | nextion_keybda_refshow_state |
| nextion_keybda_show_txt | nextion_keybda_show_txt |
| nextion_keybda_temp2_val | nextion_keybda_temp2_val |
| nextion_keybda_temp_val | nextion_keybda_temp_val |
| nextion_keybda_tempstr_txt | nextion_keybda_tempstr_txt |
| nextion_keybda_tm0_en | nextion_keybda_tm0_en |
| nextion_keybda_tm0_tim | nextion_keybda_tm0_tim |
| nextion_level_xyz_b_home_pic | nextion_level_xyz_b_home_pic |
| nextion_level_xyz_b_home_val | nextion_level_xyz_b_home_val |
| nextion_level_xyz_event_en | nextion_level_xyz_event_en |
| nextion_level_xyz_event_tim | nextion_level_xyz_event_tim |
| nextion_level_xyz_p0_pic | nextion_level_xyz_p0_pic |
| nextion_level_xyz_tm0_en | nextion_level_xyz_tm0_en |
| nextion_level_xyz_tm0_tim | nextion_level_xyz_tm0_tim |
| nextion_level_xyz_va0_val | nextion_level_xyz_va0_val |
| nextion_level_xyz_va1_val | nextion_level_xyz_va1_val |
| nextion_level_xyz_va2_val | nextion_level_xyz_va2_val |
| nextion_level_xyz_va3_val | nextion_level_xyz_va3_val |
| nextion_page1_b_face_pic | nextion_page1_b_face_pic |
| nextion_page1_b_face_val | nextion_page1_b_face_val |
| nextion_page1_b_level_pic | nextion_page1_b_level_pic |
| nextion_page1_b_level_val | nextion_page1_b_level_val |
| nextion_page1_b_rrp_pic | nextion_page1_b_rrp_pic |
| nextion_page1_b_rrp_val | nextion_page1_b_rrp_val |
| nextion_page1_b_sensors_pic | nextion_page1_b_sensors_pic |
| nextion_page1_b_sensors_val | nextion_page1_b_sensors_val |
| nextion_page1_b_settings_pic | nextion_page1_b_settings_pic |
| nextion_page1_b_settings_val | nextion_page1_b_settings_val |
| nextion_page1_b_take_pic | nextion_page1_b_take_pic |
| nextion_page1_b_take_val | nextion_page1_b_take_val |
| nextion_rrp_main_b_home_pic | nextion_rrp_main_b_home_pic |
| nextion_rrp_main_b_home_val | nextion_rrp_main_b_home_val |
| nextion_rrp_main_b_p1_arm_h_val | nextion_rrp_main_b_p1_arm_h_val |
| nextion_rrp_main_b_p1_arm_v_val | nextion_rrp_main_b_p1_arm_v_val |
| nextion_rrp_main_b_p1_cam_f_val | nextion_rrp_main_b_p1_cam_f_val |
| nextion_rrp_main_b_p1_cam_h_val | nextion_rrp_main_b_p1_cam_h_val |
| nextion_rrp_main_b_p1_cam_t_val | nextion_rrp_main_b_p1_cam_t_val |
| nextion_rrp_main_b_p1_cam_v_val | nextion_rrp_main_b_p1_cam_v_val |
| nextion_rrp_main_b_p1_dir_val | nextion_rrp_main_b_p1_dir_val |
| nextion_rrp_main_b_p2_arm_h_val | nextion_rrp_main_b_p2_arm_h_val |
| nextion_rrp_main_b_p2_arm_v_val | nextion_rrp_main_b_p2_arm_v_val |
| nextion_rrp_main_b_p2_cam_f_val | nextion_rrp_main_b_p2_cam_f_val |
| nextion_rrp_main_b_p2_cam_h_val | nextion_rrp_main_b_p2_cam_h_val |
| nextion_rrp_main_b_p2_cam_t_val | nextion_rrp_main_b_p2_cam_t_val |
| nextion_rrp_main_b_p2_cam_v_val | nextion_rrp_main_b_p2_cam_v_val |
| nextion_rrp_main_b_p2_dir_val | nextion_rrp_main_b_p2_dir_val |
| nextion_rrp_main_b_stop_pic | nextion_rrp_main_b_stop_pic |
| nextion_rrp_main_b_stop_val | nextion_rrp_main_b_stop_val |
| nextion_rrp_main_h_p1_sens_val | nextion_rrp_main_h_p1_sens_val |
| nextion_rrp_main_h_p2_sens_val | nextion_rrp_main_h_p2_sens_val |
| nextion_rrp_main_t_buf_p1_txt | nextion_rrp_main_t_buf_p1_txt |
| nextion_rrp_main_t_buf_p2_txt | nextion_rrp_main_t_buf_p2_txt |
| nextion_rrp_main_t_p1_val_txt | nextion_rrp_main_t_p1_val_txt |
| nextion_rrp_main_t_p2_val_txt | nextion_rrp_main_t_p2_val_txt |
| nextion_rrp_main_va_p1_axis_val | nextion_rrp_main_va_p1_axis_val |
| nextion_rrp_main_va_p1_dir_val | nextion_rrp_main_va_p1_dir_val |
| nextion_rrp_main_va_p1_val_val | nextion_rrp_main_va_p1_val_val |
| nextion_rrp_main_va_p2_axis_val | nextion_rrp_main_va_p2_axis_val |
| nextion_rrp_main_va_p2_dir_val | nextion_rrp_main_va_p2_dir_val |
| nextion_rrp_main_va_p2_val_val | nextion_rrp_main_va_p2_val_val |
| nextion_rrp_main_va_tmp_val | nextion_rrp_main_va_tmp_val |
| nextion_mode_main_b_home_pic | nextion_mode_main_b_home_pic |
| nextion_mode_main_b_home_val | nextion_mode_main_b_home_val |
| nextion_mode_main_t0_txt | nextion_mode_main_t0_txt |
| nextion_settings_main_b_home_pic | nextion_settings_main_b_home_pic |
| nextion_settings_main_b_home_val | nextion_settings_main_b_home_val |
| nextion_settings_main_b_save_meta_pic | nextion_settings_main_b_save_meta_pic |
| nextion_settings_main_b_save_meta_val | nextion_settings_main_b_save_meta_val |
| nextion_settings_main_t_director_txt | nextion_settings_main_t_director_txt |
| nextion_settings_main_t_save_status_txt | nextion_settings_main_t_save_status_txt |
| nextion_settings_main_t_title_txt | nextion_settings_main_t_title_txt |
| nextion_take_main_b_clap_pic | nextion_take_main_b_clap_pic |
| nextion_take_main_b_clap_val | nextion_take_main_b_clap_val |
| nextion_take_main_b_home_pic | nextion_take_main_b_home_pic |
| nextion_take_main_b_home_val | nextion_take_main_b_home_val |
| nextion_take_main_p_axis0_pic | nextion_take_main_p_axis0_pic |
| nextion_take_main_p_axis1_pic | nextion_take_main_p_axis1_pic |
| nextion_take_main_p_axis2_pic | nextion_take_main_p_axis2_pic |
| nextion_take_main_p_axis3_pic | nextion_take_main_p_axis3_pic |
| nextion_take_main_p_axis4_pic | nextion_take_main_p_axis4_pic |
| nextion_take_main_p_axis5_pic | nextion_take_main_p_axis5_pic |
| nextion_take_main_p_laser_pic | nextion_take_main_p_laser_pic |
| nextion_take_main_p_light_pic | nextion_take_main_p_light_pic |
| nextion_take_main_p_limits_pic | nextion_take_main_p_limits_pic |
| nextion_take_main_p_shock_pic | nextion_take_main_p_shock_pic |
| nextion_take_main_p_temp_pic | nextion_take_main_p_temp_pic |
| nextion_take_main_p_xyz_pic | nextion_take_main_p_xyz_pic |
| nextion_take_main_t0_txt | nextion_take_main_t0_txt |
| nextion_take_main_t1_txt | nextion_take_main_t1_txt |
| nextion_take_main_t2_txt | nextion_take_main_t2_txt |
| nextion_take_main_t_axis0_txt | nextion_take_main_t_axis0_txt |
| nextion_take_main_t_axis1_txt | nextion_take_main_t_axis1_txt |
| nextion_take_main_t_axis2_txt | nextion_take_main_t_axis2_txt |
| nextion_take_main_t_axis3_txt | nextion_take_main_t_axis3_txt |
| nextion_take_main_t_axis4_txt | nextion_take_main_t_axis4_txt |
| nextion_take_main_t_axis5_txt | nextion_take_main_t_axis5_txt |
| nextion_take_main_t_clap_txt | nextion_take_main_t_clap_txt |
| nextion_take_main_t_laser_txt | nextion_take_main_t_laser_txt |
| nextion_take_main_t_light_txt | nextion_take_main_t_light_txt |
| nextion_take_main_t_limits_txt | nextion_take_main_t_limits_txt |
| nextion_take_main_t_shock_txt | nextion_take_main_t_shock_txt |
| nextion_take_main_t_status_txt | nextion_take_main_t_status_txt |
| nextion_take_main_t_take_txt | nextion_take_main_t_take_txt |
| nextion_take_main_t_temp_txt | nextion_take_main_t_temp_txt |
| nextion_take_main_t_xyz_txt | nextion_take_main_t_xyz_txt |
| nextion_ui_cut | nextion_ui_cut |
| page1.b_face.pic | nextion_page1_b_face_pic |
| page1.b_face.val | nextion_page1_b_face_val |
| page1.b_level.pic | nextion_page1_b_level_pic |
| page1.b_level.val | nextion_page1_b_level_val |
| page1.b_rrp.pic | nextion_page1_b_rrp_pic |
| page1.b_rrp.val | nextion_page1_b_rrp_val |
| page1.b_sensors.pic | nextion_page1_b_sensors_pic |
| page1.b_sensors.val | nextion_page1_b_sensors_val |
| page1.b_settings.pic | nextion_page1_b_settings_pic |
| page1.b_settings.val | nextion_page1_b_settings_val |
| page1.b_take.pic | nextion_page1_b_take_pic |
| page1.b_take.val | nextion_page1_b_take_val |
| par_rrp_p1_dir | rrp_p1_dir |
| par_rrp_p1_sens | rrp_p1_sens |
| par_rrp_p1_val | rrp_p1_value |
| par_rrp_p2_dir | rrp_p2_dir |
| par_rrp_p2_sens | rrp_p2_sens |
| par_rrp_p2_val | rrp_p2_value |
| rrp_main.b_home.pic | nextion_rrp_main_b_home_pic |
| rrp_main.b_home.val | nextion_rrp_main_b_home_val |
| rrp_main.b_p1_arm_h.val | nextion_rrp_main_b_p1_arm_h_val |
| rrp_main.b_p1_arm_v.val | nextion_rrp_main_b_p1_arm_v_val |
| rrp_main.b_p1_cam_f.val | nextion_rrp_main_b_p1_cam_f_val |
| rrp_main.b_p1_cam_h.val | nextion_rrp_main_b_p1_cam_h_val |
| rrp_main.b_p1_cam_t.val | nextion_rrp_main_b_p1_cam_t_val |
| rrp_main.b_p1_cam_v.val | nextion_rrp_main_b_p1_cam_v_val |
| rrp_main.b_p1_dir.val | nextion_rrp_main_b_p1_dir_val |
| rrp_main.b_p2_arm_h.val | nextion_rrp_main_b_p2_arm_h_val |
| rrp_main.b_p2_arm_v.val | nextion_rrp_main_b_p2_arm_v_val |
| rrp_main.b_p2_cam_f.val | nextion_rrp_main_b_p2_cam_f_val |
| rrp_main.b_p2_cam_h.val | nextion_rrp_main_b_p2_cam_h_val |
| rrp_main.b_p2_cam_t.val | nextion_rrp_main_b_p2_cam_t_val |
| rrp_main.b_p2_cam_v.val | nextion_rrp_main_b_p2_cam_v_val |
| rrp_main.b_p2_dir.val | nextion_rrp_main_b_p2_dir_val |
| rrp_main.b_stop.pic | nextion_rrp_main_b_stop_pic |
| rrp_main.b_stop.val | nextion_rrp_main_b_stop_val |
| rrp_main.h_p1_sens.val | nextion_rrp_main_h_p1_sens_val |
| rrp_main.h_p2_sens.val | nextion_rrp_main_h_p2_sens_val |
| rrp_main.t_buf_p1.txt | nextion_rrp_main_t_buf_p1_txt |
| rrp_main.t_buf_p2.txt | nextion_rrp_main_t_buf_p2_txt |
| rrp_main.t_p1_val.txt | nextion_rrp_main_t_p1_val_txt |
| rrp_main.t_p2_val.txt | nextion_rrp_main_t_p2_val_txt |
| rrp_main.va_p1_axis.val | nextion_rrp_main_va_p1_axis_val |
| rrp_main.va_p1_dir.val | nextion_rrp_main_va_p1_dir_val |
| rrp_main.va_p1_val.val | nextion_rrp_main_va_p1_val_val |
| rrp_main.va_p2_axis.val | nextion_rrp_main_va_p2_axis_val |
| rrp_main.va_p2_dir.val | nextion_rrp_main_va_p2_dir_val |
| rrp_main.va_p2_val.val | nextion_rrp_main_va_p2_val_val |
| rrp_main.va_tmp.val | nextion_rrp_main_va_tmp_val |
| sandbox_curve | sandbox_curve |
| sandbox_metrics | sandbox_metrics |
| sandbox_step_preview | sandbox_step_preview |
| sensor_level_x | level_x |
| sensor_level_y | level_y |
| mode_main.b_home.pic | nextion_mode_main_b_home_pic |
| mode_main.b_home.val | nextion_mode_main_b_home_val |
| mode_main.t0.txt | nextion_mode_main_t0_txt |
| settings_main.b_home.pic | nextion_settings_main_b_home_pic |
| settings_main.b_home.val | nextion_settings_main_b_home_val |
| settings_main.b_save_meta.pic | nextion_settings_main_b_save_meta_pic |
| settings_main.b_save_meta.val | nextion_settings_main_b_save_meta_val |
| settings_main.t_director.txt | nextion_settings_main_t_director_txt |
| settings_main.t_save_status.txt | nextion_settings_main_t_save_status_txt |
| settings_main.t_title.txt | nextion_settings_main_t_title_txt |
| take_main.b_clap.pic | nextion_take_main_b_clap_pic |
| take_main.b_clap.val | nextion_take_main_b_clap_val |
| take_main.b_home.pic | nextion_take_main_b_home_pic |
| take_main.b_home.val | nextion_take_main_b_home_val |
| take_main.p_axis0.pic | nextion_take_main_p_axis0_pic |
| take_main.p_axis1.pic | nextion_take_main_p_axis1_pic |
| take_main.p_axis2.pic | nextion_take_main_p_axis2_pic |
| take_main.p_axis3.pic | nextion_take_main_p_axis3_pic |
| take_main.p_axis4.pic | nextion_take_main_p_axis4_pic |
| take_main.p_axis5.pic | nextion_take_main_p_axis5_pic |
| take_main.p_laser.pic | nextion_take_main_p_laser_pic |
| take_main.p_light.pic | nextion_take_main_p_light_pic |
| take_main.p_limits.pic | nextion_take_main_p_limits_pic |
| take_main.p_shock.pic | nextion_take_main_p_shock_pic |
| take_main.p_temp.pic | nextion_take_main_p_temp_pic |
| take_main.p_xyz.pic | nextion_take_main_p_xyz_pic |
| take_main.t0.txt | nextion_take_main_t0_txt |
| take_main.t1.txt | nextion_take_main_t1_txt |
| take_main.t2.txt | nextion_take_main_t2_txt |
| take_main.t_axis0.txt | nextion_take_main_t_axis0_txt |
| take_main.t_axis1.txt | nextion_take_main_t_axis1_txt |
| take_main.t_axis2.txt | nextion_take_main_t_axis2_txt |
| take_main.t_axis3.txt | nextion_take_main_t_axis3_txt |
| take_main.t_axis4.txt | nextion_take_main_t_axis4_txt |
| take_main.t_axis5.txt | nextion_take_main_t_axis5_txt |
| take_main.t_clap.txt | nextion_take_main_t_clap_txt |
| take_main.t_laser.txt | nextion_take_main_t_laser_txt |
| take_main.t_light.txt | nextion_take_main_t_light_txt |
| take_main.t_limits.txt | nextion_take_main_t_limits_txt |
| take_main.t_shock.txt | nextion_take_main_t_shock_txt |
| take_main.t_status.txt | nextion_take_main_t_status_txt |
| take_main.t_take.txt | nextion_take_main_t_take_txt |
| take_main.t_temp.txt | nextion_take_main_t_temp_txt |
| take_main.t_xyz.txt | nextion_take_main_t_xyz_txt |
| take_timecode | take_timecode |
| timeline_clap_marker | timeline_clap_marker |
| timeline_cursor | timeline_cursor |
| timeline_take_marker | timeline_take_marker |
| tk_editor_editor_ehr_tarzanaxissandbox_curve_canvas_state | tk_editor_editor_ehr_tarzanaxissandbox_curve_canvas_state |
| tk_editor_editor_ehr_tarzanaxissandbox_step_canvas_state | tk_editor_editor_ehr_tarzanaxissandbox_step_canvas_state |
| tk_editor_editor_ehr_tarzanehrui_axis_info_label_text | tk_editor_editor_ehr_tarzanehrui_axis_info_label_text |
| tk_editor_editor_ehr_tarzanehrui_canvas_state | tk_editor_editor_ehr_tarzanehrui_canvas_state |
| tk_editor_editor_ehr_tarzanehrui_curve_canvas_state | tk_editor_editor_ehr_tarzanehrui_curve_canvas_state |
| tk_editor_editor_ehr_tarzanehrui_left_state | tk_editor_editor_ehr_tarzanehrui_left_state |
| tk_editor_editor_ehr_tarzanehrui_protocol_box_state | tk_editor_editor_ehr_tarzanehrui_protocol_box_state |
| tk_editor_editor_ehr_tarzanehrui_protocol_canvas_state | tk_editor_editor_ehr_tarzanehrui_protocol_canvas_state |
| tk_editor_editor_ehr_tarzanehrui_protocol_holder_state | tk_editor_editor_ehr_tarzanehrui_protocol_holder_state |
| tk_editor_editor_ehr_tarzanehrui_protocol_label_text | tk_editor_editor_ehr_tarzanehrui_protocol_label_text |
| tk_editor_editor_ehr_tarzanehrui_protocol_text_text | tk_editor_editor_ehr_tarzanehrui_protocol_text_text |
| tk_editor_editor_ehr_tarzanehrui_row_frame_state | tk_editor_editor_ehr_tarzanehrui_row_frame_state |
| tk_editor_editor_ehr_tarzanehrui_save_button_text | tk_editor_editor_ehr_tarzanehrui_save_button_text |
| tk_editor_editor_ehr_tarzanehrui_status_text | tk_editor_editor_ehr_tarzanehrui_status_text |
| tk_editor_editor_ehr_tarzanehrui_step_canvas_state | tk_editor_editor_ehr_tarzanehrui_step_canvas_state |
| tk_editor_editor_ehr_tarzanehrui_take_panel_state | tk_editor_editor_ehr_tarzanehrui_take_panel_state |
| tk_editor_editor_ehr_tarzanehrui_timeline_canvas_state | tk_editor_editor_ehr_tarzanehrui_timeline_canvas_state |
| tk_editor_editor_tarzanaxissandbox_curve_canvas_state | tk_editor_editor_tarzanaxissandbox_curve_canvas_state |
| tk_editor_editor_tarzanaxissandbox_step_canvas_state | tk_editor_editor_tarzanaxissandbox_step_canvas_state |
| tk_editor_editor_tarzanehrtakesandbox_canvas_state | tk_editor_editor_tarzanehrtakesandbox_canvas_state |
| tk_editor_editor_tarzanehrtakesandbox_controls_wrap_state | tk_editor_editor_tarzanehrtakesandbox_controls_wrap_state |
| tk_editor_editor_tarzanehrtakesandbox_protocol_canvas_state | tk_editor_editor_tarzanehrtakesandbox_protocol_canvas_state |
| tk_editor_editor_tarzanehrtakesandbox_protocol_holder_state | tk_editor_editor_tarzanehrtakesandbox_protocol_holder_state |
| tk_editor_editor_tarzanehrtakesandbox_row_frame_state | tk_editor_editor_tarzanehrtakesandbox_row_frame_state |
| tk_editor_editor_tarzanehrtakesandbox_save_button_text | tk_editor_editor_tarzanehrtakesandbox_save_button_text |
| tk_editor_editor_tarzantakeprotocollight_canvas_state | tk_editor_editor_tarzantakeprotocollight_canvas_state |
| tk_editor_editor_tarzantakeprotocollight_protocol_canvas_state | tk_editor_editor_tarzantakeprotocollight_protocol_canvas_state |
| tk_editor_editor_tarzantakeprotocollight_protocol_holder_state | tk_editor_editor_tarzantakeprotocollight_protocol_holder_state |
| tk_editor_editor_tarzantakeprotocollight_row_frame_state | tk_editor_editor_tarzantakeprotocollight_row_frame_state |
| tk_editor_editor_tarzantakeprotocollight_save_button_text | tk_editor_editor_tarzantakeprotocollight_save_button_text |
| tk_editor_ehr_tarzanaxissandbox_curve_canvas_state | tk_editor_ehr_tarzanaxissandbox_curve_canvas_state |
| tk_editor_ehr_tarzanaxissandbox_step_canvas_state | tk_editor_ehr_tarzanaxissandbox_step_canvas_state |
| tk_editor_ehr_tarzanehrui_axis_info_label_text | tk_editor_ehr_tarzanehrui_axis_info_label_text |
| tk_editor_ehr_tarzanehrui_canvas_state | tk_editor_ehr_tarzanehrui_canvas_state |
| tk_editor_ehr_tarzanehrui_curve_canvas_state | tk_editor_ehr_tarzanehrui_curve_canvas_state |
| tk_editor_ehr_tarzanehrui_left_state | tk_editor_ehr_tarzanehrui_left_state |
| tk_editor_ehr_tarzanehrui_protocol_box_state | tk_editor_ehr_tarzanehrui_protocol_box_state |
| tk_editor_ehr_tarzanehrui_protocol_canvas_state | tk_editor_ehr_tarzanehrui_protocol_canvas_state |
| tk_editor_ehr_tarzanehrui_protocol_holder_state | tk_editor_ehr_tarzanehrui_protocol_holder_state |
| tk_editor_ehr_tarzanehrui_protocol_label_text | tk_editor_ehr_tarzanehrui_protocol_label_text |
| tk_editor_ehr_tarzanehrui_protocol_text_text | tk_editor_ehr_tarzanehrui_protocol_text_text |
| tk_editor_ehr_tarzanehrui_row_frame_state | tk_editor_ehr_tarzanehrui_row_frame_state |
| tk_editor_ehr_tarzanehrui_save_button_text | tk_editor_ehr_tarzanehrui_save_button_text |
| tk_editor_ehr_tarzanehrui_selected_point_time_label_text | tk_editor_ehr_tarzanehrui_selected_point_time_label_text |
| tk_editor_ehr_tarzanehrui_status_text | tk_editor_ehr_tarzanehrui_status_text |
| tk_editor_ehr_tarzanehrui_step_canvas_state | tk_editor_ehr_tarzanehrui_step_canvas_state |
| tk_editor_ehr_tarzanehrui_take_panel_state | tk_editor_ehr_tarzanehrui_take_panel_state |
| tk_editor_ehr_tarzanehrui_timeline_canvas_state | tk_editor_ehr_tarzanehrui_timeline_canvas_state |
| tk_editor_par_tarzannextionpreview_page_label_text | tk_editor_par_tarzannextionpreview_page_label_text |
| tk_editor_par_tarzannextionpreview_screen_canvas_state | tk_editor_par_tarzannextionpreview_screen_canvas_state |
| tk_editor_par_tarzannextionpreview_screen_frame_state | tk_editor_par_tarzannextionpreview_screen_frame_state |
| tk_editor_par_tarzannextionpreview_status_text | tk_editor_par_tarzannextionpreview_status_text |
| tk_editor_par_tarzanparapp_body_state | tk_editor_par_tarzanparapp_body_state |
| tk_editor_par_tarzanparapp_bottom_state | tk_editor_par_tarzanparapp_bottom_state |
| tk_editor_par_tarzanparapp_clock_text | tk_editor_par_tarzanparapp_clock_text |
| tk_editor_par_tarzanparapp_footer_state | tk_editor_par_tarzanparapp_footer_state |
| tk_editor_par_tarzanparapp_header_state | tk_editor_par_tarzanparapp_header_state |
| tk_editor_par_tarzanparapp_layout_master_state | tk_editor_par_tarzanparapp_layout_master_state |
| tk_editor_par_tarzanparapp_left_state | tk_editor_par_tarzanparapp_left_state |
| tk_editor_par_tarzanparapp_middle_bottom_state | tk_editor_par_tarzanparapp_middle_bottom_state |
| tk_editor_par_tarzanparapp_middle_top_state | tk_editor_par_tarzanparapp_middle_top_state |
| tk_editor_par_tarzanparapp_mode_label_text | tk_editor_par_tarzanparapp_mode_label_text |
| tk_editor_par_tarzanparapp_right_state | tk_editor_par_tarzanparapp_right_state |
| tk_editor_par_tarzanparapp_top_state | tk_editor_par_tarzanparapp_top_state |
| tk_editor_par_tarzanparpanels_log_text_text | tk_editor_par_tarzanparpanels_log_text_text |
| tk_editor_par_tarzanparpanels_old_log_text_text | tk_editor_par_tarzanparpanels_old_log_text_text |
| tk_editor_par_tarzanparpanels_timeline_canvas_state | tk_editor_par_tarzanparpanels_timeline_canvas_state |
| tk_editor_par_tarzanparwidgets_body_state | tk_editor_par_tarzanparwidgets_body_state |
| tk_editor_par_tarzanparwidgets_counter_label_text | tk_editor_par_tarzanparwidgets_counter_label_text |
| tk_editor_par_tarzanparwidgets_motor_canvas_state | tk_editor_par_tarzanparwidgets_motor_canvas_state |
| tk_editor_tarzanaxissandbox_curve_canvas_state | tk_editor_tarzanaxissandbox_curve_canvas_state |
| tk_editor_tarzanaxissandbox_step_canvas_state | tk_editor_tarzanaxissandbox_step_canvas_state |
| tk_editor_tarzanehrtakesandbox_canvas_state | tk_editor_tarzanehrtakesandbox_canvas_state |
| tk_editor_tarzanehrtakesandbox_controls_wrap_state | tk_editor_tarzanehrtakesandbox_controls_wrap_state |
| tk_editor_tarzanehrtakesandbox_protocol_canvas_state | tk_editor_tarzanehrtakesandbox_protocol_canvas_state |
| tk_editor_tarzanehrtakesandbox_protocol_holder_state | tk_editor_tarzanehrtakesandbox_protocol_holder_state |
| tk_editor_tarzanehrtakesandbox_row_frame_state | tk_editor_tarzanehrtakesandbox_row_frame_state |
| tk_editor_tarzanehrtakesandbox_save_button_text | tk_editor_tarzanehrtakesandbox_save_button_text |
| tk_editor_tarzankhr_btn_start_text | tk_editor_tarzankhr_btn_start_text |
| tk_editor_tarzankhr_btn_stop_text | tk_editor_tarzankhr_btn_stop_text |
| tk_editor_tarzankhr_input_canvas_state | tk_editor_tarzankhr_input_canvas_state |
| tk_editor_tarzankhr_khr_canvas_state | tk_editor_tarzankhr_khr_canvas_state |
| tk_editor_tarzankhr_output_canvas_state | tk_editor_tarzankhr_output_canvas_state |
| tk_editor_tarzankhr_plugin_box_text | tk_editor_tarzankhr_plugin_box_text |
| tk_editor_tarzankhr_preview_canvas_state | tk_editor_tarzankhr_preview_canvas_state |
| tk_editor_tarzankhr_profile_box_text | tk_editor_tarzankhr_profile_box_text |
| tk_editor_tarzankhr_profile_desc_text | tk_editor_tarzankhr_profile_desc_text |
| tk_editor_tarzankhr_status_text | tk_editor_tarzankhr_status_text |
| tk_editor_tarzantakeprotocollight_canvas_state | tk_editor_tarzantakeprotocollight_canvas_state |
| tk_editor_tarzantakeprotocollight_protocol_canvas_state | tk_editor_tarzantakeprotocollight_protocol_canvas_state |
| tk_editor_tarzantakeprotocollight_protocol_holder_state | tk_editor_tarzantakeprotocollight_protocol_holder_state |
| tk_editor_tarzantakeprotocollight_row_frame_state | tk_editor_tarzantakeprotocollight_row_frame_state |
| tk_editor_tarzantakeprotocollight_save_button_text | tk_editor_tarzantakeprotocollight_save_button_text |
| tk_hardware_tarzannextion_tarzannextionsandbox_log_text | tk_hardware_tarzannextion_tarzannextionsandbox_log_text |
| tk_mechanics_tarzanedytorchoreografiiruchu_global_canvas_state | tk_mechanics_tarzanedytorchoreografiiruchu_global_canvas_state |
| tk_mechanics_tarzanedytorchoreografiiruchu_scroll_canvas_state | tk_mechanics_tarzanedytorchoreografiiruchu_scroll_canvas_state |
| tk_mechanics_tarzanedytorchoreografiiruchu_tracks_frame_state | tk_mechanics_tarzanedytorchoreografiiruchu_tracks_frame_state |
| tk_mechanics_tarzanpanelosi_row1_state | tk_mechanics_tarzanpanelosi_row1_state |
| tk_mechanics_tarzanpanelosi_row2_state | tk_mechanics_tarzanpanelosi_row2_state |
| tk_mechanics_tarzanpanelosi_row3_state | tk_mechanics_tarzanpanelosi_row3_state |
| tk_mechanics_tarzanwykresosi_canvas_state | tk_mechanics_tarzanwykresosi_canvas_state |
| tk_mechanics_tarzanwykresosi_limit_canvas_state | tk_mechanics_tarzanwykresosi_limit_canvas_state |
| tk_mechanics_tarzanwykresosi_limit_panel_state | tk_mechanics_tarzanwykresosi_limit_panel_state |
| tk_mechanics_tarzanwykresosi_meta_label_text | tk_mechanics_tarzanwykresosi_meta_label_text |
| tk_mechanics_tarzanwykresosi_title_text | tk_mechanics_tarzanwykresosi_title_text |
| tk_modes_editor_editor_ehr_tarzanaxissandbox_curve_canvas_state | tk_modes_editor_editor_ehr_tarzanaxissandbox_curve_canvas_state |
| tk_modes_editor_editor_ehr_tarzanaxissandbox_step_canvas_state | tk_modes_editor_editor_ehr_tarzanaxissandbox_step_canvas_state |
| tk_modes_editor_editor_ehr_tarzanehrui_axis_info_label_text | tk_modes_editor_editor_ehr_tarzanehrui_axis_info_label_text |
| tk_modes_editor_editor_ehr_tarzanehrui_canvas_state | tk_modes_editor_editor_ehr_tarzanehrui_canvas_state |
| tk_modes_editor_editor_ehr_tarzanehrui_curve_canvas_state | tk_modes_editor_editor_ehr_tarzanehrui_curve_canvas_state |
| tk_modes_editor_editor_ehr_tarzanehrui_left_state | tk_modes_editor_editor_ehr_tarzanehrui_left_state |
| tk_modes_editor_editor_ehr_tarzanehrui_protocol_box_state | tk_modes_editor_editor_ehr_tarzanehrui_protocol_box_state |
| tk_modes_editor_editor_ehr_tarzanehrui_protocol_canvas_state | tk_modes_editor_editor_ehr_tarzanehrui_protocol_canvas_state |
| tk_modes_editor_editor_ehr_tarzanehrui_protocol_holder_state | tk_modes_editor_editor_ehr_tarzanehrui_protocol_holder_state |
| tk_modes_editor_editor_ehr_tarzanehrui_protocol_label_text | tk_modes_editor_editor_ehr_tarzanehrui_protocol_label_text |
| tk_modes_editor_editor_ehr_tarzanehrui_protocol_text_text | tk_modes_editor_editor_ehr_tarzanehrui_protocol_text_text |
| tk_modes_editor_editor_ehr_tarzanehrui_row_frame_state | tk_modes_editor_editor_ehr_tarzanehrui_row_frame_state |
| tk_modes_editor_editor_ehr_tarzanehrui_save_button_text | tk_modes_editor_editor_ehr_tarzanehrui_save_button_text |
| tk_modes_editor_editor_ehr_tarzanehrui_status_text | tk_modes_editor_editor_ehr_tarzanehrui_status_text |
| tk_modes_editor_editor_ehr_tarzanehrui_step_canvas_state | tk_modes_editor_editor_ehr_tarzanehrui_step_canvas_state |
| tk_modes_editor_editor_ehr_tarzanehrui_take_panel_state | tk_modes_editor_editor_ehr_tarzanehrui_take_panel_state |
| tk_modes_editor_editor_ehr_tarzanehrui_timeline_canvas_state | tk_modes_editor_editor_ehr_tarzanehrui_timeline_canvas_state |
| tk_modes_editor_editor_tarzanaxissandbox_curve_canvas_state | tk_modes_editor_editor_tarzanaxissandbox_curve_canvas_state |
| tk_modes_editor_editor_tarzanaxissandbox_step_canvas_state | tk_modes_editor_editor_tarzanaxissandbox_step_canvas_state |
| tk_modes_editor_editor_tarzanehrtakesandbox_canvas_state | tk_modes_editor_editor_tarzanehrtakesandbox_canvas_state |
| tk_modes_editor_editor_tarzanehrtakesandbox_controls_wrap_state | tk_modes_editor_editor_tarzanehrtakesandbox_controls_wrap_state |
| tk_modes_editor_editor_tarzanehrtakesandbox_protocol_canvas_state | tk_modes_editor_editor_tarzanehrtakesandbox_protocol_canvas_state |
| tk_modes_editor_editor_tarzanehrtakesandbox_protocol_holder_state | tk_modes_editor_editor_tarzanehrtakesandbox_protocol_holder_state |
| tk_modes_editor_editor_tarzanehrtakesandbox_row_frame_state | tk_modes_editor_editor_tarzanehrtakesandbox_row_frame_state |
| tk_modes_editor_editor_tarzanehrtakesandbox_save_button_text | tk_modes_editor_editor_tarzanehrtakesandbox_save_button_text |
| tk_modes_editor_editor_tarzantakeprotocollight_canvas_state | tk_modes_editor_editor_tarzantakeprotocollight_canvas_state |
| tk_modes_editor_editor_tarzantakeprotocollight_protocol_canvas_state | tk_modes_editor_editor_tarzantakeprotocollight_protocol_canvas_state |
| tk_modes_editor_editor_tarzantakeprotocollight_protocol_holder_state | tk_modes_editor_editor_tarzantakeprotocollight_protocol_holder_state |
| tk_modes_editor_editor_tarzantakeprotocollight_row_frame_state | tk_modes_editor_editor_tarzantakeprotocollight_row_frame_state |
| tk_modes_editor_editor_tarzantakeprotocollight_save_button_text | tk_modes_editor_editor_tarzantakeprotocollight_save_button_text |
| tk_modes_editor_ehr_tarzanaxissandbox_curve_canvas_state | tk_modes_editor_ehr_tarzanaxissandbox_curve_canvas_state |
| tk_modes_editor_ehr_tarzanaxissandbox_step_canvas_state | tk_modes_editor_ehr_tarzanaxissandbox_step_canvas_state |
| tk_modes_editor_ehr_tarzanehrui_axis_info_label_text | tk_modes_editor_ehr_tarzanehrui_axis_info_label_text |
| tk_modes_editor_ehr_tarzanehrui_canvas_state | tk_modes_editor_ehr_tarzanehrui_canvas_state |
| tk_modes_editor_ehr_tarzanehrui_curve_canvas_state | tk_modes_editor_ehr_tarzanehrui_curve_canvas_state |
| tk_modes_editor_ehr_tarzanehrui_left_state | tk_modes_editor_ehr_tarzanehrui_left_state |
| tk_modes_editor_ehr_tarzanehrui_protocol_box_state | tk_modes_editor_ehr_tarzanehrui_protocol_box_state |
| tk_modes_editor_ehr_tarzanehrui_protocol_canvas_state | tk_modes_editor_ehr_tarzanehrui_protocol_canvas_state |
| tk_modes_editor_ehr_tarzanehrui_protocol_holder_state | tk_modes_editor_ehr_tarzanehrui_protocol_holder_state |
| tk_modes_editor_ehr_tarzanehrui_protocol_label_text | tk_modes_editor_ehr_tarzanehrui_protocol_label_text |
| tk_modes_editor_ehr_tarzanehrui_protocol_text_text | tk_modes_editor_ehr_tarzanehrui_protocol_text_text |
| tk_modes_editor_ehr_tarzanehrui_row_frame_state | tk_modes_editor_ehr_tarzanehrui_row_frame_state |
| tk_modes_editor_ehr_tarzanehrui_save_button_text | tk_modes_editor_ehr_tarzanehrui_save_button_text |
| tk_modes_editor_ehr_tarzanehrui_selected_point_time_label_text | tk_modes_editor_ehr_tarzanehrui_selected_point_time_label_text |
| tk_modes_editor_ehr_tarzanehrui_status_text | tk_modes_editor_ehr_tarzanehrui_status_text |
| tk_modes_editor_ehr_tarzanehrui_step_canvas_state | tk_modes_editor_ehr_tarzanehrui_step_canvas_state |
| tk_modes_editor_ehr_tarzanehrui_take_panel_state | tk_modes_editor_ehr_tarzanehrui_take_panel_state |
| tk_modes_editor_ehr_tarzanehrui_timeline_canvas_state | tk_modes_editor_ehr_tarzanehrui_timeline_canvas_state |
| tk_modes_editor_par_tarzannextionpreview_page_label_text | tk_modes_editor_par_tarzannextionpreview_page_label_text |
| tk_modes_editor_par_tarzannextionpreview_screen_canvas_state | tk_modes_editor_par_tarzannextionpreview_screen_canvas_state |
| tk_modes_editor_par_tarzannextionpreview_screen_frame_state | tk_modes_editor_par_tarzannextionpreview_screen_frame_state |
| tk_modes_editor_par_tarzannextionpreview_status_text | tk_modes_editor_par_tarzannextionpreview_status_text |
| tk_modes_editor_par_tarzanparapp_body_state | tk_modes_editor_par_tarzanparapp_body_state |
| tk_modes_editor_par_tarzanparapp_bottom_state | tk_modes_editor_par_tarzanparapp_bottom_state |
| tk_modes_editor_par_tarzanparapp_clock_text | tk_modes_editor_par_tarzanparapp_clock_text |
| tk_modes_editor_par_tarzanparapp_footer_state | tk_modes_editor_par_tarzanparapp_footer_state |
| tk_modes_editor_par_tarzanparapp_header_state | tk_modes_editor_par_tarzanparapp_header_state |
| tk_modes_editor_par_tarzanparapp_layout_master_state | tk_modes_editor_par_tarzanparapp_layout_master_state |
| tk_modes_editor_par_tarzanparapp_left_state | tk_modes_editor_par_tarzanparapp_left_state |
| tk_modes_editor_par_tarzanparapp_middle_bottom_state | tk_modes_editor_par_tarzanparapp_middle_bottom_state |
| tk_modes_editor_par_tarzanparapp_middle_top_state | tk_modes_editor_par_tarzanparapp_middle_top_state |
| tk_modes_editor_par_tarzanparapp_mode_label_text | tk_modes_editor_par_tarzanparapp_mode_label_text |
| tk_modes_editor_par_tarzanparapp_right_state | tk_modes_editor_par_tarzanparapp_right_state |
| tk_modes_editor_par_tarzanparapp_top_state | tk_modes_editor_par_tarzanparapp_top_state |
| tk_modes_editor_par_tarzanparpanels_log_text_text | tk_modes_editor_par_tarzanparpanels_log_text_text |
| tk_modes_editor_par_tarzanparpanels_old_log_text_text | tk_modes_editor_par_tarzanparpanels_old_log_text_text |
| tk_modes_editor_par_tarzanparpanels_timeline_canvas_state | tk_modes_editor_par_tarzanparpanels_timeline_canvas_state |
| tk_modes_editor_par_tarzanparwidgets_body_state | tk_modes_editor_par_tarzanparwidgets_body_state |
| tk_modes_editor_par_tarzanparwidgets_counter_label_text | tk_modes_editor_par_tarzanparwidgets_counter_label_text |
| tk_modes_editor_par_tarzanparwidgets_motor_canvas_state | tk_modes_editor_par_tarzanparwidgets_motor_canvas_state |
| tk_modes_editor_tarzanaxissandbox_curve_canvas_state | tk_modes_editor_tarzanaxissandbox_curve_canvas_state |
| tk_modes_editor_tarzanaxissandbox_step_canvas_state | tk_modes_editor_tarzanaxissandbox_step_canvas_state |
| tk_modes_editor_tarzanehrtakesandbox_canvas_state | tk_modes_editor_tarzanehrtakesandbox_canvas_state |
| tk_modes_editor_tarzanehrtakesandbox_controls_wrap_state | tk_modes_editor_tarzanehrtakesandbox_controls_wrap_state |
| tk_modes_editor_tarzanehrtakesandbox_protocol_canvas_state | tk_modes_editor_tarzanehrtakesandbox_protocol_canvas_state |
| tk_modes_editor_tarzanehrtakesandbox_protocol_holder_state | tk_modes_editor_tarzanehrtakesandbox_protocol_holder_state |
| tk_modes_editor_tarzanehrtakesandbox_row_frame_state | tk_modes_editor_tarzanehrtakesandbox_row_frame_state |
| tk_modes_editor_tarzanehrtakesandbox_save_button_text | tk_modes_editor_tarzanehrtakesandbox_save_button_text |
| tk_modes_editor_tarzankhr_btn_start_text | tk_modes_editor_tarzankhr_btn_start_text |
| tk_modes_editor_tarzankhr_btn_stop_text | tk_modes_editor_tarzankhr_btn_stop_text |
| tk_modes_editor_tarzankhr_input_canvas_state | tk_modes_editor_tarzankhr_input_canvas_state |
| tk_modes_editor_tarzankhr_khr_canvas_state | tk_modes_editor_tarzankhr_khr_canvas_state |
| tk_modes_editor_tarzankhr_output_canvas_state | tk_modes_editor_tarzankhr_output_canvas_state |
| tk_modes_editor_tarzankhr_plugin_box_text | tk_modes_editor_tarzankhr_plugin_box_text |
| tk_modes_editor_tarzankhr_preview_canvas_state | tk_modes_editor_tarzankhr_preview_canvas_state |
| tk_modes_editor_tarzankhr_profile_box_text | tk_modes_editor_tarzankhr_profile_box_text |
| tk_modes_editor_tarzankhr_profile_desc_text | tk_modes_editor_tarzankhr_profile_desc_text |
| tk_modes_editor_tarzankhr_status_text | tk_modes_editor_tarzankhr_status_text |
| tk_modes_editor_tarzantakeprotocollight_canvas_state | tk_modes_editor_tarzantakeprotocollight_canvas_state |
| tk_modes_editor_tarzantakeprotocollight_protocol_canvas_state | tk_modes_editor_tarzantakeprotocollight_protocol_canvas_state |
| tk_modes_editor_tarzantakeprotocollight_protocol_holder_state | tk_modes_editor_tarzantakeprotocollight_protocol_holder_state |
| tk_modes_editor_tarzantakeprotocollight_row_frame_state | tk_modes_editor_tarzantakeprotocollight_row_frame_state |
| tk_modes_editor_tarzantakeprotocollight_save_button_text | tk_modes_editor_tarzantakeprotocollight_save_button_text |
| tk_modes_hardware_tarzannextion_tarzannextionsandbox_log_text | tk_modes_hardware_tarzannextion_tarzannextionsandbox_log_text |
| tk_vision_tarzanvisionsetup_content_state | tk_vision_tarzanvisionsetup_content_state |

---

# 5. Pełna lista komponentów Nextion HMI

CSV:

```txt
docs/TARZAN_SNAJPER_NEXTION_COMPONENTS_FULL.csv
```

| page | component | type | props | source | line |
| --- | --- | --- | --- | --- | --- |
| rrp_main | va_p1_axis | Variable (int32) | ['val'] | rrp_main.txt | 54 |
| rrp_main | va_p2_axis | Variable (int32) | ['val'] | rrp_main.txt | 60 |
| rrp_main | va_tmp | Variable (int32) | ['val'] | rrp_main.txt | 66 |
| rrp_main | va_p2_dir | Variable (int32) | ['val'] | rrp_main.txt | 72 |
| rrp_main | va_p1_dir | Variable (int32) | ['val'] | rrp_main.txt | 78 |
| rrp_main | va_p1_val | Variable (int32) | ['val'] | rrp_main.txt | 84 |
| rrp_main | va_p2_val | Variable (int32) | ['val'] | rrp_main.txt | 90 |
| rrp_main | t_p1_val | Text | ['txt'] | rrp_main.txt | 96 |
| rrp_main | t_p2_val | Text | ['txt'] | rrp_main.txt | 118 |
| rrp_main | t_buf_p1 | Text | ['txt'] | rrp_main.txt | 140 |
| rrp_main | t_buf_p2 | Text | ['txt'] | rrp_main.txt | 164 |
| rrp_main | h_p1_sens | Slider | ['val'] | rrp_main.txt | 188 |
| rrp_main | h_p2_sens | Slider | ['val'] | rrp_main.txt | 214 |
| rrp_main | b_home | Button | ['val', 'pic'] | rrp_main.txt | 240 |
| rrp_main | b_stop | Button | ['val', 'pic'] | rrp_main.txt | 271 |
| rrp_main | b_p1_cam_v | Dual-state Button | ['val'] | rrp_main.txt | 338 |
| rrp_main | b_p2_cam_v | Dual-state Button | ['val'] | rrp_main.txt | 391 |
| rrp_main | b_p1_dir | Dual-state Button | ['val'] | rrp_main.txt | 444 |
| rrp_main | b_p2_dir | Dual-state Button | ['val'] | rrp_main.txt | 479 |
| rrp_main | b_p1_cam_t | Dual-state Button | ['val'] | rrp_main.txt | 514 |
| rrp_main | b_p1_cam_f | Dual-state Button | ['val'] | rrp_main.txt | 567 |
| rrp_main | b_p1_cam_h | Dual-state Button | ['val'] | rrp_main.txt | 620 |
| rrp_main | b_p1_arm_h | Dual-state Button | ['val'] | rrp_main.txt | 673 |
| rrp_main | b_p1_arm_v | Dual-state Button | ['val'] | rrp_main.txt | 726 |
| rrp_main | b_p2_cam_t | Dual-state Button | ['val'] | rrp_main.txt | 779 |
| rrp_main | b_p2_cam_f | Dual-state Button | ['val'] | rrp_main.txt | 832 |
| rrp_main | b_p2_cam_h | Dual-state Button | ['val'] | rrp_main.txt | 885 |
| rrp_main | b_p2_arm_h | Dual-state Button | ['val'] | rrp_main.txt | 938 |
| rrp_main | b_p2_arm_v | Dual-state Button | ['val'] | rrp_main.txt | 991 |
| take_main | t_axis0 | Text | ['txt'] | take_main.txt | 15 |
| take_main | t_axis1 | Text | ['txt'] | take_main.txt | 39 |
| take_main | t_axis3 | Text | ['txt'] | take_main.txt | 63 |
| take_main | t_axis2 | Text | ['txt'] | take_main.txt | 87 |
| take_main | t_axis4 | Text | ['txt'] | take_main.txt | 111 |
| take_main | t_axis5 | Text | ['txt'] | take_main.txt | 135 |
| take_main | t_take | Text | ['txt'] | take_main.txt | 159 |
| take_main | t_clap | Text | ['txt'] | take_main.txt | 183 |
| take_main | t_laser | Text | ['txt'] | take_main.txt | 207 |
| take_main | t_limits | Text | ['txt'] | take_main.txt | 231 |
| take_main | t_status | Text | ['txt'] | take_main.txt | 255 |
| take_main | t_shock | Text | ['txt'] | take_main.txt | 279 |
| take_main | t_light | Text | ['txt'] | take_main.txt | 303 |
| take_main | t_temp | Text | ['txt'] | take_main.txt | 327 |
| take_main | t_xyz | Text | ['txt'] | take_main.txt | 351 |
| take_main | t0 | Text | ['txt'] | take_main.txt | 375 |
| take_main | t1 | Text | ['txt'] | take_main.txt | 399 |
| take_main | t2 | Text | ['txt'] | take_main.txt | 423 |
| take_main | p_axis0 | Picture | ['pic'] | take_main.txt | 447 |
| take_main | p_axis1 | Picture | ['pic'] | take_main.txt | 458 |
| take_main | p_axis5 | Picture | ['pic'] | take_main.txt | 469 |
| take_main | p_axis3 | Picture | ['pic'] | take_main.txt | 480 |
| take_main | p_axis2 | Picture | ['pic'] | take_main.txt | 491 |
| take_main | p_axis4 | Picture | ['pic'] | take_main.txt | 502 |
| take_main | p_laser | Picture | ['pic'] | take_main.txt | 513 |
| take_main | p_limits | Picture | ['pic'] | take_main.txt | 524 |
| take_main | p_light | Picture | ['pic'] | take_main.txt | 535 |
| take_main | p_shock | Picture | ['pic'] | take_main.txt | 546 |
| take_main | p_temp | Picture | ['pic'] | take_main.txt | 557 |
| take_main | p_xyz | Picture | ['pic'] | take_main.txt | 568 |
| take_main | b_home | Button | ['val', 'pic'] | take_main.txt | 579 |
| take_main | b_clap | Button | ['val', 'pic'] | take_main.txt | 610 |
| settings_main | t_title | Text | ['txt'] | settings_main.txt | 16 |
| settings_main | t_director | Text | ['txt'] | settings_main.txt | 40 |
| settings_main | t_save_status | Text | ['txt'] | settings_main.txt | 64 |
| settings_main | b_home | Button | ['val', 'pic'] | settings_main.txt | 100 |
| settings_main | b_save_meta | Button | ['val', 'pic'] | settings_main.txt | 131 |
| level_xyz | va0 | Variable (int32) | ['val'] | level_xyz.txt | 21 |
| level_xyz | va1 | Variable (int32) | ['val'] | level_xyz.txt | 27 |
| level_xyz | va2 | Variable (int32) | ['val'] | level_xyz.txt | 33 |
| level_xyz | va3 | Variable (int32) | ['val'] | level_xyz.txt | 39 |
| level_xyz | p0 | Picture | ['pic'] | level_xyz.txt | 45 |
| level_xyz | b_home | Button | ['val', 'pic'] | level_xyz.txt | 56 |
| level_xyz | tm0 | Timer | ['en', 'tim'] | level_xyz.txt | 87 |
| level_xyz | Event | Timer | ['en', 'tim'] | level_xyz.txt | 95 |
| page1 | b_face | Button | ['val', 'pic'] | page1.txt | 15 |
| page1 | b_level | Button | ['val', 'pic'] | page1.txt | 42 |
| page1 | b_rrp | Button | ['val', 'pic'] | page1.txt | 69 |
| page1 | b_sensors | Button | ['val', 'pic'] | page1.txt | 96 |
| page1 | b_settings | Button | ['val', 'pic'] | page1.txt | 123 |
| page1 | b_take | Button | ['val', 'pic'] | page1.txt | 150 |
| boot | va0 | Variable (int32) | ['val'] | boot.txt | 22 |
| boot | p0 | Picture | ['pic'] | boot.txt | 28 |
| boot | tm0 | Timer | ['en', 'tim'] | boot.txt | 46 |
| boot | Event | Timer | ['en', 'tim'] | boot.txt | 54 |
| mode_main | t0 | Text | ['txt'] | mode_main.txt | 15 |
| mode_main | b_home | Button | ['val', 'pic'] | mode_main.txt | 39 |
| face_rec | t0 | Text | ['txt'] | face_rec.txt | 15 |
| face_rec | b_home | Button | ['val', 'pic'] | face_rec.txt | 39 |
| keybdA | loadpageid | Variable (int32) | ['val'] | keybdA.txt | 58 |
| keybdA | loadcmpid | Variable (int32) | ['val'] | keybdA.txt | 64 |
| keybdA | input | Variable (string) | ['txt'] | keybdA.txt | 70 |
| keybdA | temp | Variable (int32) | ['val'] | keybdA.txt | 77 |
| keybdA | inputlenth | Variable (int32) | ['val'] | keybdA.txt | 83 |
| keybdA | temp2 | Variable (int32) | ['val'] | keybdA.txt | 89 |
| keybdA | tempstr | Variable (string) | ['txt'] | keybdA.txt | 95 |
| keybdA | show | Text | ['txt'] | keybdA.txt | 102 |
| keybdA | b0 | Button | ['val', 'pic'] | keybdA.txt | 126 |
| keybdA | b251 | Button | ['val', 'pic'] | keybdA.txt | 163 |
| keybdA | b210 | Button | ['val', 'pic'] | keybdA.txt | 193 |
| keybdA | b1 | Button | ['val', 'pic'] | keybdA.txt | 271 |
| keybdA | b2 | Button | ['val', 'pic'] | keybdA.txt | 308 |
| keybdA | b3 | Button | ['val', 'pic'] | keybdA.txt | 345 |
| keybdA | b4 | Button | ['val', 'pic'] | keybdA.txt | 382 |
| keybdA | b5 | Button | ['val', 'pic'] | keybdA.txt | 419 |
| keybdA | b6 | Button | ['val', 'pic'] | keybdA.txt | 456 |
| keybdA | b7 | Button | ['val', 'pic'] | keybdA.txt | 493 |
| keybdA | b8 | Button | ['val', 'pic'] | keybdA.txt | 530 |
| keybdA | b200 | Button | ['val', 'pic'] | keybdA.txt | 567 |
| keybdA | b20 | Button | ['val', 'pic'] | keybdA.txt | 600 |
| keybdA | b21 | Button | ['val', 'pic'] | keybdA.txt | 637 |
| keybdA | b22 | Button | ['val', 'pic'] | keybdA.txt | 674 |
| keybdA | b23 | Button | ['val', 'pic'] | keybdA.txt | 711 |
| keybdA | b24 | Button | ['val', 'pic'] | keybdA.txt | 748 |
| keybdA | b25 | Button | ['val', 'pic'] | keybdA.txt | 785 |
| keybdA | b26 | Button | ['val', 'pic'] | keybdA.txt | 822 |
| keybdA | b27 | Button | ['val', 'pic'] | keybdA.txt | 859 |
| keybdA | b28 | Button | ['val', 'pic'] | keybdA.txt | 896 |
| keybdA | b220 | Button | ['val', 'pic'] | keybdA.txt | 933 |
| keybdA | b40 | Button | ['val', 'pic'] | keybdA.txt | 979 |
| keybdA | b41 | Button | ['val', 'pic'] | keybdA.txt | 1016 |
| keybdA | b42 | Button | ['val', 'pic'] | keybdA.txt | 1053 |
| keybdA | b43 | Button | ['val', 'pic'] | keybdA.txt | 1090 |
| keybdA | b44 | Button | ['val', 'pic'] | keybdA.txt | 1127 |
| keybdA | b45 | Button | ['val', 'pic'] | keybdA.txt | 1164 |
| keybdA | b46 | Button | ['val', 'pic'] | keybdA.txt | 1201 |
| keybdA | b230 | Button | ['val', 'pic'] | keybdA.txt | 1238 |
| keybdA | b240 | Button | ['val', 'pic'] | keybdA.txt | 1275 |
| keybdA | b242 | Button | ['val', 'pic'] | keybdA.txt | 1316 |
| keybdA | b241 | Button | ['val', 'pic'] | keybdA.txt | 1353 |
| keybdA | b243 | Button | ['val', 'pic'] | keybdA.txt | 1390 |
| keybdA | b231 | Button | ['val', 'pic'] | keybdA.txt | 1427 |
| keybdA | b244 | Button | ['val', 'pic'] | keybdA.txt | 1464 |
| keybdA | b249 | Button | ['val', 'pic'] | keybdA.txt | 1501 |
| keybdA | b201 | Button | ['val', 'pic'] | keybdA.txt | 1537 |
| keybdA | b9 | Button | ['val', 'pic'] | keybdA.txt | 1574 |
| keybdA | b232 | Button | ['val', 'pic'] | keybdA.txt | 1611 |
| keybdA | refshow | Hotspot | ['state'] | keybdA.txt | 1648 |
| keybdA | tm0 | Timer | ['en', 'tim'] | keybdA.txt | 1742 |
| keybdA | Event | Timer | ['en', 'tim'] | keybdA.txt | 1750 |

---

# 6. Pełny skan starego odświeżania

CSV:

```txt
docs/TARZAN_SNAJPER_REFRESH_SCAN_FULL.csv
```

Poniżej pierwsza tabela pełna w MD.

| file | line | kind | action | code |
| --- | --- | --- | --- | --- |
| editor/EHR/tarzanAxisSandbox.py | 535 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all() |
| editor/EHR/tarzanAxisSandbox.py | 596 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._scale_row(box, "VIEW Y SCALE", self.display_y_scale, 200.0, 800.0, 10.0, self._refresh_all) |
| editor/EHR/tarzanAxisSandbox.py | 597 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._scale_row(box, "MOUSE PRECISION", self.mouse_y_precision, 0.10, 1.00, 0.05, self._refresh_all) |
| editor/EHR/tarzanAxisSandbox.py | 598 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._scale_row(box, "TOP/BOTTOM MARGIN", self.top_bottom_margin, 8, 60, 1, self._refresh_all) |
| editor/EHR/tarzanAxisSandbox.py | 704 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Zastosowano strojenie STEP.") |
| editor/EHR/tarzanAxisSandbox.py | 711 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all(f"Wczytano parametry mechaniki: {mechanics.axis_name}.") |
| editor/EHR/tarzanAxisSandbox.py | 733 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all(f"Wczytano preset TXT: {path}") |
| editor/EHR/tarzanAxisSandbox.py | 739 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Przywrócono domyślne parametry STEP.") |
| editor/EHR/tarzanAxisSandbox.py | 744 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Sinus test ustawiony.") |
| editor/EHR/tarzanAxisSandbox.py | 749 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Negative test ustawiony.") |
| editor/EHR/tarzanAxisSandbox.py | 754 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Zero cross test ustawiony.") |
| editor/EHR/tarzanAxisSandbox.py | 759 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Linia wyzerowana.") |
| editor/EHR/tarzanAxisSandbox.py | 764 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Przywrócono ostatni stan bazowy.") |
| editor/EHR/tarzanAxisSandbox.py | 811 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | c.delete("all") |
| editor/EHR/tarzanAxisSandbox.py | 860 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | c.delete("all") |
| editor/EHR/tarzanAxisSandbox.py | 905 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | def _refresh_all(self, status: str \| None = None) -> None: |
| editor/EHR/tarzanAxisSandbox.py | 931 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all(f"Wybrano punkt {idx}.") |
| editor/EHR/tarzanAxisSandbox.py | 936 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("PAN linii.") |
| editor/EHR/tarzanAxisSandbox.py | 961 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Gotowy.") |
| editor/EHR/tarzanAxisSandbox.py | 968 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Dodano punkt.") |
| editor/EHR/tarzanAxisSandbox.py | 976 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Usunięto punkt.") |
| editor/EHR/tarzanEhrUi.py | 752 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self.canvas.delete("all") |
| editor/EHR/tarzanEhrUi.py | 1299 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | canvas.delete("all") |
| editor/EHR/tarzanEhrUi.py | 1473 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all(reason="INIT") |
| editor/EHR/tarzanEhrUi.py | 1718 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self.master_window._refresh_all(light=False) |
| editor/EHR/tarzanEhrUi.py | 1741 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Zastosowano strojenie STEP.", reason="STEP_TUNING_LIVE") |
| editor/EHR/tarzanEhrUi.py | 1753 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all(f"Wczytano parametry mechaniki: {mechanics.axis_name}.", reason="MECHANICS_PRESET") |
| editor/EHR/tarzanEhrUi.py | 1847 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all(f"Wczytano ustawienia osi: {path}", reason="LOAD_JSON") |
| editor/EHR/tarzanEhrUi.py | 1884 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all(f"Wczytano preset TXT: {path}", reason="LOAD_TUNING_TXT") |
| editor/EHR/tarzanEhrUi.py | 1896 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Przywrócono domyślne parametry STEP.", reason="RESET_STEP_TUNING") |
| editor/EHR/tarzanEhrUi.py | 1907 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Sinus test ustawiony.", reason="TEST_SINUS") |
| editor/EHR/tarzanEhrUi.py | 1918 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Negative test ustawiony.", reason="TEST_NEGATIVE") |
| editor/EHR/tarzanEhrUi.py | 1929 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Zero cross test ustawiony.", reason="TEST_ZERO_CROSS") |
| editor/EHR/tarzanEhrUi.py | 1940 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Linia wyzerowana.", reason="TEST_FLAT_ZERO") |
| editor/EHR/tarzanEhrUi.py | 1950 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Przywrócono ostatni stan bazowy.", reason="RESET_NODES") |
| editor/EHR/tarzanEhrUi.py | 1974 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | c.delete("all") |
| editor/EHR/tarzanEhrUi.py | 2060 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | c.delete("all") |
| editor/EHR/tarzanEhrUi.py | 2146 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | @profile_method('EHR_AXIS_DIALOG._refresh_all') |
| editor/EHR/tarzanEhrUi.py | 2147 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | def _refresh_all(self, status: str \| None = None, reason: str = "unknown") -> None: |
| editor/EHR/tarzanEhrUi.py | 2370 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self.master_window._refresh_all(light=False) |
| editor/EHR/tarzanEhrUi.py | 2464 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self.after_idle(self._refresh_all) |
| editor/EHR/tarzanEhrUi.py | 2464 | after_refresh | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | self.after_idle(self._refresh_all) |
| editor/EHR/tarzanEhrUi.py | 2732 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all(light=False, status=status) |
| editor/EHR/tarzanEhrUi.py | 2762 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | dlg._refresh_all() |
| editor/EHR/tarzanEhrUi.py | 2763 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all(light=False, status="Zastosowano ustawienia MAIN TAKE.") |
| editor/EHR/tarzanEhrUi.py | 2890 | after_refresh | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | self._configure_after_id = self.after(40, self._flush_configure_refresh) |
| editor/EHR/tarzanEhrUi.py | 3067 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | c.delete("all") |
| editor/EHR/tarzanEhrUi.py | 3442 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | @profile_method('EHR_MAIN._refresh_all') |
| editor/EHR/tarzanEhrUi.py | 3443 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | def _refresh_all(self, light: bool = False, status: str \| None = None) -> None: |
| editor/EHR/tarzanEhrUi.py | 3844 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all(light=False, status=f"Wczytano TAKE TXT: {path.name}") |
| editor/PAR/tarzanNextionPreview.py | 354 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self.screen_canvas.delete("all") |
| editor/PAR/tarzanNextionPreview.py | 361 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self.screen_canvas.delete("all") |
| editor/PAR/tarzanNextionPreview.py | 472 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self.screen_canvas.delete("all") |
| editor/PAR/tarzanNextionPreview.py | 581 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self.screen_canvas.delete("all") |
| editor/PAR/tarzanNextionPreview.py | 598 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self.screen_canvas.delete("all") |
| editor/PAR/tarzanNextionPreview.py | 688 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self.screen_canvas.delete("all") |
| editor/PAR/tarzanNextionPreview.py | 710 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self.screen_canvas.delete("all") |
| editor/PAR/tarzanNextionPreview.py | 772 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self.screen_canvas.delete("all") |
| editor/PAR/tarzanParApp.py | 230 | self_nextion_tick | WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER | self.after(50, self.nextion_tick) |
| editor/PAR/tarzanParApp.py | 939 | draw_preview | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | fg=COLORS["text"], insertbackground=COLORS["text"], command=lambda: draw_preview() if "draw_preview" in locals() else None).grid(row=2, column=1, sticky="w", padx=8) |
| editor/PAR/tarzanParApp.py | 988 | draw_preview | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | refresh_zone_buttons() |
| editor/PAR/tarzanParApp.py | 992 | draw_preview | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | refresh_zone_buttons() |
| editor/PAR/tarzanParApp.py | 993 | draw_preview | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | draw_preview() |
| editor/PAR/tarzanParApp.py | 997 | draw_preview | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | def refresh_zone_buttons(): |
| editor/PAR/tarzanParApp.py | 1046 | draw_preview | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | draw_preview() |
| editor/PAR/tarzanParApp.py | 1123 | draw_preview | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | draw_preview() |
| editor/PAR/tarzanParApp.py | 1130 | draw_preview | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | command=draw_preview).pack(side="left") |
| editor/PAR/tarzanParApp.py | 1135 | draw_preview | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | opt = tk.OptionMenu(row, data["zone"], *zone_map.keys(), command=lambda _=None: draw_preview()) |
| editor/PAR/tarzanParApp.py | 1150 | draw_preview | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | command=draw_preview, |
| editor/PAR/tarzanParApp.py | 1153 | draw_preview | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | col_spin.bind("<KeyRelease>", lambda _event: draw_preview()) |
| editor/PAR/tarzanParApp.py | 1165 | draw_preview | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | command=draw_preview, |
| editor/PAR/tarzanParApp.py | 1168 | draw_preview | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | row_spin.bind("<KeyRelease>", lambda _event: draw_preview()) |
| editor/PAR/tarzanParApp.py | 1189 | draw_preview | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | draw_preview() |
| editor/PAR/tarzanParApp.py | 1225 | draw_preview | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | def draw_preview(*_): |
| editor/PAR/tarzanParApp.py | 1226 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | canvas.delete("all") |
| editor/PAR/tarzanParApp.py | 1590 | draw_preview | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | draw_preview() |
| editor/PAR/tarzanParApp.py | 1601 | draw_preview | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | draw_preview() |
| editor/PAR/tarzanParApp.py | 1628 | draw_preview | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | draw_preview() |
| editor/PAR/tarzanParApp.py | 1648 | draw_preview | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | draw_preview() |
| editor/PAR/tarzanParApp.py | 1698 | draw_preview | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | draw_preview() |
| editor/PAR/tarzanParApp.py | 1722 | draw_preview | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | draw_preview() |
| editor/PAR/tarzanParApp.py | 1743 | draw_preview | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | draw_preview() |
| editor/PAR/tarzanParApp.py | 1754 | draw_preview | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | draw_preview() |
| editor/PAR/tarzanParApp.py | 1776 | draw_preview | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | draw_preview() |
| editor/PAR/tarzanParApp.py | 1828 | draw_preview | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | draw_preview() |
| editor/PAR/tarzanParApp.py | 1848 | draw_preview | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | refresh_zone_buttons() |
| editor/PAR/tarzanParApp.py | 1849 | draw_preview | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | win.after(200, draw_preview) |
| editor/PAR/tarzanParApp.py | 1850 | draw_preview | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | win.after(800, draw_preview) |
| editor/PAR/tarzanParApp.py | 1898 | def_nextion_tick | WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER | def nextion_tick(self): |
| editor/PAR/tarzanParApp.py | 1902 | nextion_refresh_previews | WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER | if hasattr(self.panels, "nextion_refresh_previews"): |
| editor/PAR/tarzanParApp.py | 1903 | nextion_refresh_previews | WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER | self.panels.nextion_refresh_previews() |
| editor/PAR/tarzanParApp.py | 1907 | self_nextion_tick | WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER | self.after(50, self.nextion_tick) |
| editor/PAR/tarzanParPanels.py | 182 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self.delete("all") |
| editor/PAR/tarzanParPanels.py | 358 | refresh_axis_card | WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER | self._register_signal_proxy(sig, lambda v, k=key: self.refresh_axis_card(k)) |
| editor/PAR/tarzanParPanels.py | 404 | refresh_axis_cards | WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER | self.refresh_axis_cards() |
| editor/PAR/tarzanParPanels.py | 407 | refresh_axis_cards | WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER | def refresh_axis_cards(self): |
| editor/PAR/tarzanParPanels.py | 409 | refresh_axis_card | WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER | self.refresh_axis_card(axis) |
| editor/PAR/tarzanParPanels.py | 411 | refresh_axis_card | WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER | def refresh_axis_card(self, axis: str): |
| editor/PAR/tarzanParPanels.py | 496 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | can.delete("all") |
| editor/PAR/tarzanParPanels.py | 655 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | can.delete("all"); cx, cy, r = 40, 40, 30 |
| editor/PAR/tarzanParPanels.py | 823 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | canvas.delete("all"); cx, cy = w//2, h//2 |
| editor/PAR/tarzanParPanels.py | 899 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | can.delete("all"); can.create_rectangle(14, 5, 24, h-5, fill=COLORS["green"], outline="#063c0a") |
| editor/PAR/tarzanParPanels.py | 917 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | can.delete("all") |
| editor/PAR/tarzanParPanels.py | 1230 | refresh_axis_cards | WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER | self.refresh_axis_cards() |
| editor/PAR/tarzanParPanels.py | 1237 | draw_timeline | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | self._schedule_timeline_redraw() |
| editor/PAR/tarzanParPanels.py | 1244 | draw_timeline | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | self.timeline_canvas.bind("<Configure>", lambda e: self.draw_timeline()) |
| editor/PAR/tarzanParPanels.py | 1245 | draw_timeline | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | self.draw_timeline() |
| editor/PAR/tarzanParPanels.py | 1248 | draw_timeline | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | def _schedule_timeline_redraw(self): |
| editor/PAR/tarzanParPanels.py | 1250 | draw_timeline | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | self._timeline_after_id = self.app.after(_TIMELINE_DEBOUNCE_MS, self._do_draw_timeline) |
| editor/PAR/tarzanParPanels.py | 1252 | draw_timeline | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | def _do_draw_timeline(self): |
| editor/PAR/tarzanParPanels.py | 1254 | draw_timeline | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | self.draw_timeline() |
| editor/PAR/tarzanParPanels.py | 1278 | draw_timeline | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | def draw_timeline(self): |
| editor/PAR/tarzanParPanels.py | 1281 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | can.delete("all") |
| editor/PAR/tarzanParPanels.py | 1446 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | canvas.delete("all") |
| editor/PAR/tarzanParPanels.py | 1574 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | canvas.delete("all") |
| editor/PAR/tarzanParPanels.py | 1761 | nextion_refresh_previews | WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER | def nextion_refresh_previews(self): |
| editor/PAR/tarzanParPanels.py | 1788 | widget_refresh | WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER | widget.refresh() |
| editor/PAR/tarzanParPanels_old.py | 187 | refresh_axis_cards | WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER | self.refresh_axis_cards() |
| editor/PAR/tarzanParPanels_old.py | 680 | draw_timeline | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | canvas.bind("<Configure>", lambda e: self.draw_timeline()) |
| editor/PAR/tarzanParPanels_old.py | 681 | draw_timeline | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | self.draw_timeline() |
| editor/PAR/tarzanParPanels_old.py | 735 | refresh_axis_cards | WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER | self.refresh_axis_cards() |
| editor/PAR/tarzanParPanels_old.py | 738 | refresh_axis_cards | WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER | def refresh_axis_cards(self): |
| editor/PAR/tarzanParPanels_old.py | 755 | draw_timeline | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | def draw_timeline(self): |
| editor/PAR/tarzanParPanels_old.py | 759 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | canvas.delete("all") |
| editor/PAR/tarzanParPanels_old.py | 1044 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | led.delete("all") |
| editor/PAR/tarzanParPanels_old.py | 1111 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | canvas.delete("all") |
| editor/PAR/tarzanParPanels_old.py | 1215 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | canvas.delete("all") |
| editor/PAR/tarzanParPanels_old.py | 1310 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | canvas.delete("all") |
| editor/PAR/tarzanParPanels_old.py | 1343 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self.delete("all") |
| editor/PAR/tarzanParPanels_old.py | 1452 | draw_timeline | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | def _schedule_timeline_redraw(self): |
| editor/PAR/tarzanParPanels_old.py | 1459 | draw_timeline | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | self.draw_timeline() |
| editor/PAR/tarzanParPanels_old.py | 1469 | draw_timeline | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | self.draw_timeline() |
| editor/PAR/tarzanParPanels_old.py | 1497 | draw_timeline | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | command=lambda: (self.bus.history.clear(), self.draw_timeline()), |
| editor/PAR/tarzanParPanels_old.py | 1503 | draw_timeline | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | canvas.bind("<Configure>", lambda _e: self._schedule_timeline_redraw()) |
| editor/PAR/tarzanParPanels_old.py | 1504 | draw_timeline | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | self.draw_timeline() |
| editor/PAR/tarzanParPanels_old.py | 1512 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | canvas.delete("all") |
| editor/PAR/tarzanParPanels_old.py | 1674 | draw_timeline | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | self._schedule_timeline_redraw() |
| editor/PAR/tarzanParPanels_old.py | 1734 | draw_timeline | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | self.draw_timeline() |
| editor/PAR/tarzanParPanels_old.py | 1780 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | canvas.delete("all") |
| editor/PAR/tarzanParPanels_old.py | 1964 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | c.delete("all") |
| editor/PAR/tarzanParPanels_old.py | 2209 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | c.delete("all") |
| editor/PAR/tarzanParPanels_old.py | 2470 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | canvas.delete("all") |
| editor/PAR/tarzanParPanels_old.py | 3107 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | c.delete('all') |
| editor/PAR/tarzanParPanels_old.py | 3184 | refresh_axis_cards | WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER | TarzanParPanels.refresh_axis_cards = _tarzan_refresh_axis_cards_final_v2 |
| editor/PAR/tarzanParPanels_old.py | 3186 | draw_timeline | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | TarzanParPanels._schedule_timeline_redraw = _schedule_timeline_redraw |
| editor/PAR/tarzanParPanels_old.py | 3188 | draw_timeline | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | TarzanParPanels.draw_timeline = _par_draw_timeline_final |
| editor/PAR/tarzanParWidgets.py | 54 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self.delete("all") |
| editor/PAR/tarzanParWidgets.py | 83 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self.delete("all") |
| editor/PAR/tarzanParWidgets.py | 287 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | c.delete("all") |
| editor/TarzanEhrTakeSandbox.py | 545 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self.canvas.delete("all") |
| editor/TarzanTakeProtocolLight.py | 35 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | # - nie używa _refresh_all. |
| editor/TarzanTakeProtocolLight.py | 852 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self.canvas.delete("all") |
| editor/editor/EHR/tarzanAxisSandbox.py | 534 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all() |
| editor/editor/EHR/tarzanAxisSandbox.py | 595 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._scale_row(box, "VIEW Y SCALE", self.display_y_scale, 200.0, 800.0, 10.0, self._refresh_all) |
| editor/editor/EHR/tarzanAxisSandbox.py | 596 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._scale_row(box, "MOUSE PRECISION", self.mouse_y_precision, 0.10, 1.00, 0.05, self._refresh_all) |
| editor/editor/EHR/tarzanAxisSandbox.py | 597 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._scale_row(box, "TOP/BOTTOM MARGIN", self.top_bottom_margin, 8, 60, 1, self._refresh_all) |
| editor/editor/EHR/tarzanAxisSandbox.py | 703 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Zastosowano strojenie STEP.") |
| editor/editor/EHR/tarzanAxisSandbox.py | 710 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all(f"Wczytano parametry mechaniki: {mechanics.axis_name}.") |
| editor/editor/EHR/tarzanAxisSandbox.py | 732 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all(f"Wczytano preset TXT: {path}") |
| editor/editor/EHR/tarzanAxisSandbox.py | 738 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Przywrócono domyślne parametry STEP.") |
| editor/editor/EHR/tarzanAxisSandbox.py | 743 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Sinus test ustawiony.") |
| editor/editor/EHR/tarzanAxisSandbox.py | 748 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Negative test ustawiony.") |
| editor/editor/EHR/tarzanAxisSandbox.py | 753 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Zero cross test ustawiony.") |
| editor/editor/EHR/tarzanAxisSandbox.py | 758 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Linia wyzerowana.") |
| editor/editor/EHR/tarzanAxisSandbox.py | 763 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Przywrócono ostatni stan bazowy.") |
| editor/editor/EHR/tarzanAxisSandbox.py | 810 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | c.delete("all") |
| editor/editor/EHR/tarzanAxisSandbox.py | 859 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | c.delete("all") |
| editor/editor/EHR/tarzanAxisSandbox.py | 904 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | def _refresh_all(self, status: str \| None = None) -> None: |
| editor/editor/EHR/tarzanAxisSandbox.py | 930 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all(f"Wybrano punkt {idx}.") |
| editor/editor/EHR/tarzanAxisSandbox.py | 935 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("PAN linii.") |
| editor/editor/EHR/tarzanAxisSandbox.py | 960 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Gotowy.") |
| editor/editor/EHR/tarzanAxisSandbox.py | 967 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Dodano punkt.") |
| editor/editor/EHR/tarzanAxisSandbox.py | 975 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Usunięto punkt.") |
| editor/editor/EHR/tarzanEhrUi.py | 704 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self.canvas.delete("all") |
| editor/editor/EHR/tarzanEhrUi.py | 1243 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | canvas.delete("all") |
| editor/editor/EHR/tarzanEhrUi.py | 1411 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self.after_idle(self._refresh_all) |
| editor/editor/EHR/tarzanEhrUi.py | 1411 | after_refresh | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | self.after_idle(self._refresh_all) |
| editor/editor/EHR/tarzanEhrUi.py | 1657 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Zastosowano ustawienia osi.") |
| editor/editor/EHR/tarzanEhrUi.py | 1666 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Zastosowano strojenie STEP.") |
| editor/editor/EHR/tarzanEhrUi.py | 1677 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all(f"Wczytano parametry mechaniki: {mechanics.axis_name}.") |
| editor/editor/EHR/tarzanEhrUi.py | 1770 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all(f"Wczytano ustawienia osi: {path}") |
| editor/editor/EHR/tarzanEhrUi.py | 1807 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all(f"Wczytano preset TXT: {path}") |
| editor/editor/EHR/tarzanEhrUi.py | 1818 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Przywrócono domyślne parametry STEP.") |
| editor/editor/EHR/tarzanEhrUi.py | 1828 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Sinus test ustawiony.") |
| editor/editor/EHR/tarzanEhrUi.py | 1838 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Negative test ustawiony.") |
| editor/editor/EHR/tarzanEhrUi.py | 1848 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Zero cross test ustawiony.") |
| editor/editor/EHR/tarzanEhrUi.py | 1858 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Linia wyzerowana.") |
| editor/editor/EHR/tarzanEhrUi.py | 1867 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Przywrócono ostatni stan bazowy.") |
| editor/editor/EHR/tarzanEhrUi.py | 1891 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | c.delete("all") |
| editor/editor/EHR/tarzanEhrUi.py | 1958 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | c.delete("all") |
| editor/editor/EHR/tarzanEhrUi.py | 2017 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | @profile_method('EHR_AXIS_DIALOG._refresh_all') |
| editor/editor/EHR/tarzanEhrUi.py | 2018 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | def _refresh_all(self, status: str \| None = None) -> None: |
| editor/editor/EHR/tarzanEhrUi.py | 2095 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Gotowy.") |
| editor/editor/EHR/tarzanEhrUi.py | 2107 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Dodano punkt.") |
| editor/editor/EHR/tarzanEhrUi.py | 2120 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Usunięto punkt.") |
| editor/editor/EHR/tarzanEhrUi.py | 2211 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self.after_idle(self._refresh_all) |
| editor/editor/EHR/tarzanEhrUi.py | 2211 | after_refresh | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | self.after_idle(self._refresh_all) |
| editor/editor/EHR/tarzanEhrUi.py | 2366 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all(light=True, status=status) |
| editor/editor/EHR/tarzanEhrUi.py | 2395 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | dlg._refresh_all() |
| editor/editor/EHR/tarzanEhrUi.py | 2396 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all(light=False, status="Zastosowano ustawienia MAIN TAKE.") |
| editor/editor/EHR/tarzanEhrUi.py | 2509 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all( |
| editor/editor/EHR/tarzanEhrUi.py | 2520 | after_refresh | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | self._configure_after_id = self.after(40, self._flush_configure_refresh) |
| editor/editor/EHR/tarzanEhrUi.py | 2683 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | c.delete("all") |
| editor/editor/EHR/tarzanEhrUi.py | 2960 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | @profile_method('EHR_MAIN._refresh_all') |
| editor/editor/EHR/tarzanEhrUi.py | 2961 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | def _refresh_all(self, light: bool = False, status: str \| None = None) -> None: |
| editor/editor/EHR/tarzanEhrUi.py | 3029 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all(light=True, status=None) |
| editor/editor/EHR/tarzanEhrUi.py | 3232 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all(light=False, status=f"Wczytano TAKE TXT: {path.name}") |
| editor/editor/TarzanEhrTakeSandbox.py | 545 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self.canvas.delete("all") |
| editor/editor/TarzanTakeProtocolLight.py | 35 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | # - nie używa _refresh_all. |
| editor/editor/TarzanTakeProtocolLight.py | 852 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self.canvas.delete("all") |
| editor/editor/tarzanAxisSandbox.py | 534 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all() |
| editor/editor/tarzanAxisSandbox.py | 595 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._scale_row(box, "VIEW Y SCALE", self.display_y_scale, 200.0, 800.0, 10.0, self._refresh_all) |
| editor/editor/tarzanAxisSandbox.py | 596 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._scale_row(box, "MOUSE PRECISION", self.mouse_y_precision, 0.10, 1.00, 0.05, self._refresh_all) |
| editor/editor/tarzanAxisSandbox.py | 597 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._scale_row(box, "TOP/BOTTOM MARGIN", self.top_bottom_margin, 8, 60, 1, self._refresh_all) |
| editor/editor/tarzanAxisSandbox.py | 703 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Zastosowano strojenie STEP.") |
| editor/editor/tarzanAxisSandbox.py | 710 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all(f"Wczytano parametry mechaniki: {mechanics.axis_name}.") |
| editor/editor/tarzanAxisSandbox.py | 732 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all(f"Wczytano preset TXT: {path}") |
| editor/editor/tarzanAxisSandbox.py | 738 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Przywrócono domyślne parametry STEP.") |
| editor/editor/tarzanAxisSandbox.py | 743 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Sinus test ustawiony.") |
| editor/editor/tarzanAxisSandbox.py | 748 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Negative test ustawiony.") |
| editor/editor/tarzanAxisSandbox.py | 753 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Zero cross test ustawiony.") |
| editor/editor/tarzanAxisSandbox.py | 758 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Linia wyzerowana.") |
| editor/editor/tarzanAxisSandbox.py | 763 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Przywrócono ostatni stan bazowy.") |
| editor/editor/tarzanAxisSandbox.py | 810 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | c.delete("all") |
| editor/editor/tarzanAxisSandbox.py | 878 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | c.delete("all") |
| editor/editor/tarzanAxisSandbox.py | 923 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | def _refresh_all(self, status: str \| None = None) -> None: |
| editor/editor/tarzanAxisSandbox.py | 949 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all(f"Wybrano punkt {idx}.") |
| editor/editor/tarzanAxisSandbox.py | 954 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("PAN linii.") |
| editor/editor/tarzanAxisSandbox.py | 979 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Gotowy.") |
| editor/editor/tarzanAxisSandbox.py | 986 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Dodano punkt.") |
| editor/editor/tarzanAxisSandbox.py | 994 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Usunięto punkt.") |
| editor/tarzanAxisSandbox.py | 534 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all() |
| editor/tarzanAxisSandbox.py | 595 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._scale_row(box, "VIEW Y SCALE", self.display_y_scale, 200.0, 800.0, 10.0, self._refresh_all) |
| editor/tarzanAxisSandbox.py | 596 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._scale_row(box, "MOUSE PRECISION", self.mouse_y_precision, 0.10, 1.00, 0.05, self._refresh_all) |
| editor/tarzanAxisSandbox.py | 597 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._scale_row(box, "TOP/BOTTOM MARGIN", self.top_bottom_margin, 8, 60, 1, self._refresh_all) |
| editor/tarzanAxisSandbox.py | 703 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Zastosowano strojenie STEP.") |
| editor/tarzanAxisSandbox.py | 710 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all(f"Wczytano parametry mechaniki: {mechanics.axis_name}.") |
| editor/tarzanAxisSandbox.py | 732 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all(f"Wczytano preset TXT: {path}") |
| editor/tarzanAxisSandbox.py | 738 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Przywrócono domyślne parametry STEP.") |
| editor/tarzanAxisSandbox.py | 743 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Sinus test ustawiony.") |
| editor/tarzanAxisSandbox.py | 748 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Negative test ustawiony.") |
| editor/tarzanAxisSandbox.py | 753 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Zero cross test ustawiony.") |
| editor/tarzanAxisSandbox.py | 758 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Linia wyzerowana.") |
| editor/tarzanAxisSandbox.py | 763 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Przywrócono ostatni stan bazowy.") |
| editor/tarzanAxisSandbox.py | 810 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | c.delete("all") |
| editor/tarzanAxisSandbox.py | 878 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | c.delete("all") |
| editor/tarzanAxisSandbox.py | 923 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | def _refresh_all(self, status: str \| None = None) -> None: |
| editor/tarzanAxisSandbox.py | 949 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all(f"Wybrano punkt {idx}.") |
| editor/tarzanAxisSandbox.py | 954 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("PAN linii.") |
| editor/tarzanAxisSandbox.py | 979 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Gotowy.") |
| editor/tarzanAxisSandbox.py | 986 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Dodano punkt.") |
| editor/tarzanAxisSandbox.py | 994 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Usunięto punkt.") |
| editor/tarzanKHR.py | 611 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | c.delete("all") |
| editor/tarzanKHR.py | 950 | draw_khr | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | self._draw_input() |
| editor/tarzanKHR.py | 991 | draw_khr | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | self._draw_input() |
| editor/tarzanKHR.py | 1094 | draw_khr | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | self._draw_input() |
| editor/tarzanKHR.py | 1158 | draw_khr | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | self._draw_input() |
| editor/tarzanKHR.py | 1161 | after_refresh | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | self.after(self._camera_preview_refresh_ms, self._camera_preview_loop) |
| editor/tarzanKHR.py | 1372 | after_refresh | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | self.after(self._ui_refresh_ms, self._ui_loop) |
| editor/tarzanKHR.py | 1434 | draw_khr | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | self._draw_input() |
| editor/tarzanKHR.py | 1435 | draw_khr | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | self._draw_khr() |
| editor/tarzanKHR.py | 1436 | draw_khr | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | self._draw_output() |
| editor/tarzanKHR.py | 1438 | draw_khr | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | @khr_profiled("KHR_UI._draw_input") |
| editor/tarzanKHR.py | 1439 | draw_khr | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | def _draw_input(self) -> None: |
| editor/tarzanKHR.py | 1441 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | c.delete("all") |
| editor/tarzanKHR.py | 1444 | draw_khr | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | self._draw_camera_input() |
| editor/tarzanKHR.py | 1476 | draw_khr | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | @khr_profiled("KHR_UI._draw_camera_input") |
| editor/tarzanKHR.py | 1477 | draw_khr | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | def _draw_camera_input(self) -> None: |
| editor/tarzanKHR.py | 1558 | draw_khr | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | @khr_profiled("KHR_UI._draw_khr") |
| editor/tarzanKHR.py | 1559 | draw_khr | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | def _draw_khr(self) -> None: |
| editor/tarzanKHR.py | 1561 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | c.delete("all") |
| editor/tarzanKHR.py | 1582 | draw_khr | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | @khr_profiled("KHR_UI._draw_output") |
| editor/tarzanKHR.py | 1583 | draw_khr | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | def _draw_output(self) -> None: |
| editor/tarzanKHR.py | 1585 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | c.delete("all") |
| mechanics/tarzanEdytorChoreografiiRuchu.py | 302 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | c.delete("all") |
| mechanics/tarzanWykresOsi.py | 721 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | c.delete("all") |
| mechanics/tarzanWykresOsi.py | 739 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | c.delete("all") |
| mechanics/tarzanWykresOsi.py | 1008 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | c.delete("all") |
| modes/editor/EHR/tarzanAxisSandbox.py | 535 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all() |
| modes/editor/EHR/tarzanAxisSandbox.py | 596 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._scale_row(box, "VIEW Y SCALE", self.display_y_scale, 200.0, 800.0, 10.0, self._refresh_all) |
| modes/editor/EHR/tarzanAxisSandbox.py | 597 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._scale_row(box, "MOUSE PRECISION", self.mouse_y_precision, 0.10, 1.00, 0.05, self._refresh_all) |
| modes/editor/EHR/tarzanAxisSandbox.py | 598 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._scale_row(box, "TOP/BOTTOM MARGIN", self.top_bottom_margin, 8, 60, 1, self._refresh_all) |
| modes/editor/EHR/tarzanAxisSandbox.py | 704 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Zastosowano strojenie STEP.") |
| modes/editor/EHR/tarzanAxisSandbox.py | 711 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all(f"Wczytano parametry mechaniki: {mechanics.axis_name}.") |
| modes/editor/EHR/tarzanAxisSandbox.py | 733 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all(f"Wczytano preset TXT: {path}") |
| modes/editor/EHR/tarzanAxisSandbox.py | 739 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Przywrócono domyślne parametry STEP.") |
| modes/editor/EHR/tarzanAxisSandbox.py | 744 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Sinus test ustawiony.") |
| modes/editor/EHR/tarzanAxisSandbox.py | 749 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Negative test ustawiony.") |
| modes/editor/EHR/tarzanAxisSandbox.py | 754 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Zero cross test ustawiony.") |
| modes/editor/EHR/tarzanAxisSandbox.py | 759 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Linia wyzerowana.") |
| modes/editor/EHR/tarzanAxisSandbox.py | 764 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Przywrócono ostatni stan bazowy.") |
| modes/editor/EHR/tarzanAxisSandbox.py | 811 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | c.delete("all") |
| modes/editor/EHR/tarzanAxisSandbox.py | 860 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | c.delete("all") |
| modes/editor/EHR/tarzanAxisSandbox.py | 905 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | def _refresh_all(self, status: str \| None = None) -> None: |
| modes/editor/EHR/tarzanAxisSandbox.py | 931 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all(f"Wybrano punkt {idx}.") |
| modes/editor/EHR/tarzanAxisSandbox.py | 936 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("PAN linii.") |
| modes/editor/EHR/tarzanAxisSandbox.py | 961 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Gotowy.") |
| modes/editor/EHR/tarzanAxisSandbox.py | 968 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Dodano punkt.") |
| modes/editor/EHR/tarzanAxisSandbox.py | 976 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Usunięto punkt.") |
| modes/editor/EHR/tarzanEhrUi.py | 752 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self.canvas.delete("all") |
| modes/editor/EHR/tarzanEhrUi.py | 1299 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | canvas.delete("all") |
| modes/editor/EHR/tarzanEhrUi.py | 1473 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all(reason="INIT") |
| modes/editor/EHR/tarzanEhrUi.py | 1718 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self.master_window._refresh_all(light=False) |
| modes/editor/EHR/tarzanEhrUi.py | 1741 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Zastosowano strojenie STEP.", reason="STEP_TUNING_LIVE") |
| modes/editor/EHR/tarzanEhrUi.py | 1753 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all(f"Wczytano parametry mechaniki: {mechanics.axis_name}.", reason="MECHANICS_PRESET") |
| modes/editor/EHR/tarzanEhrUi.py | 1847 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all(f"Wczytano ustawienia osi: {path}", reason="LOAD_JSON") |
| modes/editor/EHR/tarzanEhrUi.py | 1884 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all(f"Wczytano preset TXT: {path}", reason="LOAD_TUNING_TXT") |
| modes/editor/EHR/tarzanEhrUi.py | 1896 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Przywrócono domyślne parametry STEP.", reason="RESET_STEP_TUNING") |
| modes/editor/EHR/tarzanEhrUi.py | 1907 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Sinus test ustawiony.", reason="TEST_SINUS") |
| modes/editor/EHR/tarzanEhrUi.py | 1918 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Negative test ustawiony.", reason="TEST_NEGATIVE") |
| modes/editor/EHR/tarzanEhrUi.py | 1929 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Zero cross test ustawiony.", reason="TEST_ZERO_CROSS") |
| modes/editor/EHR/tarzanEhrUi.py | 1940 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Linia wyzerowana.", reason="TEST_FLAT_ZERO") |
| modes/editor/EHR/tarzanEhrUi.py | 1950 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Przywrócono ostatni stan bazowy.", reason="RESET_NODES") |
| modes/editor/EHR/tarzanEhrUi.py | 1974 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | c.delete("all") |
| modes/editor/EHR/tarzanEhrUi.py | 2060 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | c.delete("all") |
| modes/editor/EHR/tarzanEhrUi.py | 2146 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | @profile_method('EHR_AXIS_DIALOG._refresh_all') |
| modes/editor/EHR/tarzanEhrUi.py | 2147 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | def _refresh_all(self, status: str \| None = None, reason: str = "unknown") -> None: |
| modes/editor/EHR/tarzanEhrUi.py | 2370 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self.master_window._refresh_all(light=False) |
| modes/editor/EHR/tarzanEhrUi.py | 2464 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self.after_idle(self._refresh_all) |
| modes/editor/EHR/tarzanEhrUi.py | 2464 | after_refresh | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | self.after_idle(self._refresh_all) |
| modes/editor/EHR/tarzanEhrUi.py | 2732 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all(light=False, status=status) |
| modes/editor/EHR/tarzanEhrUi.py | 2762 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | dlg._refresh_all() |
| modes/editor/EHR/tarzanEhrUi.py | 2763 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all(light=False, status="Zastosowano ustawienia MAIN TAKE.") |
| modes/editor/EHR/tarzanEhrUi.py | 2890 | after_refresh | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | self._configure_after_id = self.after(40, self._flush_configure_refresh) |
| modes/editor/EHR/tarzanEhrUi.py | 3067 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | c.delete("all") |
| modes/editor/EHR/tarzanEhrUi.py | 3442 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | @profile_method('EHR_MAIN._refresh_all') |
| modes/editor/EHR/tarzanEhrUi.py | 3443 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | def _refresh_all(self, light: bool = False, status: str \| None = None) -> None: |
| modes/editor/EHR/tarzanEhrUi.py | 3844 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all(light=False, status=f"Wczytano TAKE TXT: {path.name}") |
| modes/editor/PAR/tarzanNextionPreview.py | 354 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self.screen_canvas.delete("all") |
| modes/editor/PAR/tarzanNextionPreview.py | 361 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self.screen_canvas.delete("all") |
| modes/editor/PAR/tarzanNextionPreview.py | 472 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self.screen_canvas.delete("all") |
| modes/editor/PAR/tarzanNextionPreview.py | 581 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self.screen_canvas.delete("all") |
| modes/editor/PAR/tarzanNextionPreview.py | 598 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self.screen_canvas.delete("all") |
| modes/editor/PAR/tarzanNextionPreview.py | 688 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self.screen_canvas.delete("all") |
| modes/editor/PAR/tarzanNextionPreview.py | 710 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self.screen_canvas.delete("all") |
| modes/editor/PAR/tarzanNextionPreview.py | 772 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self.screen_canvas.delete("all") |
| modes/editor/PAR/tarzanParApp.py | 230 | self_nextion_tick | WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER | self.after(50, self.nextion_tick) |
| modes/editor/PAR/tarzanParApp.py | 939 | draw_preview | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | fg=COLORS["text"], insertbackground=COLORS["text"], command=lambda: draw_preview() if "draw_preview" in locals() else None).grid(row=2, column=1, sticky="w", padx=8) |
| modes/editor/PAR/tarzanParApp.py | 988 | draw_preview | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | refresh_zone_buttons() |
| modes/editor/PAR/tarzanParApp.py | 992 | draw_preview | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | refresh_zone_buttons() |
| modes/editor/PAR/tarzanParApp.py | 993 | draw_preview | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | draw_preview() |
| modes/editor/PAR/tarzanParApp.py | 997 | draw_preview | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | def refresh_zone_buttons(): |
| modes/editor/PAR/tarzanParApp.py | 1046 | draw_preview | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | draw_preview() |
| modes/editor/PAR/tarzanParApp.py | 1123 | draw_preview | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | draw_preview() |
| modes/editor/PAR/tarzanParApp.py | 1130 | draw_preview | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | command=draw_preview).pack(side="left") |
| modes/editor/PAR/tarzanParApp.py | 1135 | draw_preview | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | opt = tk.OptionMenu(row, data["zone"], *zone_map.keys(), command=lambda _=None: draw_preview()) |
| modes/editor/PAR/tarzanParApp.py | 1150 | draw_preview | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | command=draw_preview, |
| modes/editor/PAR/tarzanParApp.py | 1153 | draw_preview | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | col_spin.bind("<KeyRelease>", lambda _event: draw_preview()) |
| modes/editor/PAR/tarzanParApp.py | 1165 | draw_preview | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | command=draw_preview, |
| modes/editor/PAR/tarzanParApp.py | 1168 | draw_preview | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | row_spin.bind("<KeyRelease>", lambda _event: draw_preview()) |
| modes/editor/PAR/tarzanParApp.py | 1189 | draw_preview | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | draw_preview() |
| modes/editor/PAR/tarzanParApp.py | 1225 | draw_preview | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | def draw_preview(*_): |
| modes/editor/PAR/tarzanParApp.py | 1226 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | canvas.delete("all") |
| modes/editor/PAR/tarzanParApp.py | 1590 | draw_preview | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | draw_preview() |
| modes/editor/PAR/tarzanParApp.py | 1601 | draw_preview | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | draw_preview() |
| modes/editor/PAR/tarzanParApp.py | 1628 | draw_preview | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | draw_preview() |
| modes/editor/PAR/tarzanParApp.py | 1648 | draw_preview | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | draw_preview() |
| modes/editor/PAR/tarzanParApp.py | 1698 | draw_preview | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | draw_preview() |
| modes/editor/PAR/tarzanParApp.py | 1722 | draw_preview | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | draw_preview() |
| modes/editor/PAR/tarzanParApp.py | 1743 | draw_preview | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | draw_preview() |
| modes/editor/PAR/tarzanParApp.py | 1754 | draw_preview | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | draw_preview() |
| modes/editor/PAR/tarzanParApp.py | 1776 | draw_preview | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | draw_preview() |
| modes/editor/PAR/tarzanParApp.py | 1828 | draw_preview | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | draw_preview() |
| modes/editor/PAR/tarzanParApp.py | 1848 | draw_preview | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | refresh_zone_buttons() |
| modes/editor/PAR/tarzanParApp.py | 1849 | draw_preview | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | win.after(200, draw_preview) |
| modes/editor/PAR/tarzanParApp.py | 1850 | draw_preview | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | win.after(800, draw_preview) |
| modes/editor/PAR/tarzanParApp.py | 1898 | def_nextion_tick | WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER | def nextion_tick(self): |
| modes/editor/PAR/tarzanParApp.py | 1902 | nextion_refresh_previews | WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER | if hasattr(self.panels, "nextion_refresh_previews"): |
| modes/editor/PAR/tarzanParApp.py | 1903 | nextion_refresh_previews | WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER | self.panels.nextion_refresh_previews() |
| modes/editor/PAR/tarzanParApp.py | 1907 | self_nextion_tick | WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER | self.after(50, self.nextion_tick) |
| modes/editor/PAR/tarzanParPanels.py | 182 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self.delete("all") |
| modes/editor/PAR/tarzanParPanels.py | 358 | refresh_axis_card | WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER | self._register_signal_proxy(sig, lambda v, k=key: self.refresh_axis_card(k)) |
| modes/editor/PAR/tarzanParPanels.py | 404 | refresh_axis_cards | WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER | self.refresh_axis_cards() |
| modes/editor/PAR/tarzanParPanels.py | 407 | refresh_axis_cards | WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER | def refresh_axis_cards(self): |
| modes/editor/PAR/tarzanParPanels.py | 409 | refresh_axis_card | WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER | self.refresh_axis_card(axis) |
| modes/editor/PAR/tarzanParPanels.py | 411 | refresh_axis_card | WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER | def refresh_axis_card(self, axis: str): |
| modes/editor/PAR/tarzanParPanels.py | 496 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | can.delete("all") |
| modes/editor/PAR/tarzanParPanels.py | 655 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | can.delete("all"); cx, cy, r = 40, 40, 30 |
| modes/editor/PAR/tarzanParPanels.py | 823 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | canvas.delete("all"); cx, cy = w//2, h//2 |
| modes/editor/PAR/tarzanParPanels.py | 899 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | can.delete("all"); can.create_rectangle(14, 5, 24, h-5, fill=COLORS["green"], outline="#063c0a") |
| modes/editor/PAR/tarzanParPanels.py | 917 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | can.delete("all") |
| modes/editor/PAR/tarzanParPanels.py | 1230 | refresh_axis_cards | WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER | self.refresh_axis_cards() |
| modes/editor/PAR/tarzanParPanels.py | 1237 | draw_timeline | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | self._schedule_timeline_redraw() |
| modes/editor/PAR/tarzanParPanels.py | 1244 | draw_timeline | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | self.timeline_canvas.bind("<Configure>", lambda e: self.draw_timeline()) |
| modes/editor/PAR/tarzanParPanels.py | 1245 | draw_timeline | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | self.draw_timeline() |
| modes/editor/PAR/tarzanParPanels.py | 1248 | draw_timeline | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | def _schedule_timeline_redraw(self): |
| modes/editor/PAR/tarzanParPanels.py | 1250 | draw_timeline | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | self._timeline_after_id = self.app.after(_TIMELINE_DEBOUNCE_MS, self._do_draw_timeline) |
| modes/editor/PAR/tarzanParPanels.py | 1252 | draw_timeline | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | def _do_draw_timeline(self): |
| modes/editor/PAR/tarzanParPanels.py | 1254 | draw_timeline | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | self.draw_timeline() |
| modes/editor/PAR/tarzanParPanels.py | 1278 | draw_timeline | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | def draw_timeline(self): |
| modes/editor/PAR/tarzanParPanels.py | 1281 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | can.delete("all") |
| modes/editor/PAR/tarzanParPanels.py | 1446 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | canvas.delete("all") |
| modes/editor/PAR/tarzanParPanels.py | 1574 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | canvas.delete("all") |
| modes/editor/PAR/tarzanParPanels.py | 1761 | nextion_refresh_previews | WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER | def nextion_refresh_previews(self): |
| modes/editor/PAR/tarzanParPanels.py | 1788 | widget_refresh | WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER | widget.refresh() |
| modes/editor/PAR/tarzanParPanels_old.py | 187 | refresh_axis_cards | WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER | self.refresh_axis_cards() |
| modes/editor/PAR/tarzanParPanels_old.py | 680 | draw_timeline | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | canvas.bind("<Configure>", lambda e: self.draw_timeline()) |
| modes/editor/PAR/tarzanParPanels_old.py | 681 | draw_timeline | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | self.draw_timeline() |
| modes/editor/PAR/tarzanParPanels_old.py | 735 | refresh_axis_cards | WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER | self.refresh_axis_cards() |
| modes/editor/PAR/tarzanParPanels_old.py | 738 | refresh_axis_cards | WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER | def refresh_axis_cards(self): |
| modes/editor/PAR/tarzanParPanels_old.py | 755 | draw_timeline | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | def draw_timeline(self): |
| modes/editor/PAR/tarzanParPanels_old.py | 759 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | canvas.delete("all") |
| modes/editor/PAR/tarzanParPanels_old.py | 1044 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | led.delete("all") |
| modes/editor/PAR/tarzanParPanels_old.py | 1111 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | canvas.delete("all") |
| modes/editor/PAR/tarzanParPanels_old.py | 1215 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | canvas.delete("all") |
| modes/editor/PAR/tarzanParPanels_old.py | 1310 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | canvas.delete("all") |
| modes/editor/PAR/tarzanParPanels_old.py | 1343 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self.delete("all") |
| modes/editor/PAR/tarzanParPanels_old.py | 1452 | draw_timeline | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | def _schedule_timeline_redraw(self): |
| modes/editor/PAR/tarzanParPanels_old.py | 1459 | draw_timeline | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | self.draw_timeline() |
| modes/editor/PAR/tarzanParPanels_old.py | 1469 | draw_timeline | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | self.draw_timeline() |
| modes/editor/PAR/tarzanParPanels_old.py | 1497 | draw_timeline | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | command=lambda: (self.bus.history.clear(), self.draw_timeline()), |
| modes/editor/PAR/tarzanParPanels_old.py | 1503 | draw_timeline | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | canvas.bind("<Configure>", lambda _e: self._schedule_timeline_redraw()) |
| modes/editor/PAR/tarzanParPanels_old.py | 1504 | draw_timeline | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | self.draw_timeline() |
| modes/editor/PAR/tarzanParPanels_old.py | 1512 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | canvas.delete("all") |
| modes/editor/PAR/tarzanParPanels_old.py | 1674 | draw_timeline | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | self._schedule_timeline_redraw() |
| modes/editor/PAR/tarzanParPanels_old.py | 1734 | draw_timeline | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | self.draw_timeline() |
| modes/editor/PAR/tarzanParPanels_old.py | 1780 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | canvas.delete("all") |
| modes/editor/PAR/tarzanParPanels_old.py | 1964 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | c.delete("all") |
| modes/editor/PAR/tarzanParPanels_old.py | 2209 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | c.delete("all") |
| modes/editor/PAR/tarzanParPanels_old.py | 2470 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | canvas.delete("all") |
| modes/editor/PAR/tarzanParPanels_old.py | 3107 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | c.delete('all') |
| modes/editor/PAR/tarzanParPanels_old.py | 3184 | refresh_axis_cards | WYCIĄĆ Z TORU DYNAMICZNEGO I ZASTĄPIĆ TARZAN_SNAJPER | TarzanParPanels.refresh_axis_cards = _tarzan_refresh_axis_cards_final_v2 |
| modes/editor/PAR/tarzanParPanels_old.py | 3186 | draw_timeline | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | TarzanParPanels._schedule_timeline_redraw = _schedule_timeline_redraw |
| modes/editor/PAR/tarzanParPanels_old.py | 3188 | draw_timeline | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | TarzanParPanels.draw_timeline = _par_draw_timeline_final |
| modes/editor/PAR/tarzanParWidgets.py | 54 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self.delete("all") |
| modes/editor/PAR/tarzanParWidgets.py | 83 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self.delete("all") |
| modes/editor/PAR/tarzanParWidgets.py | 287 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | c.delete("all") |
| modes/editor/TarzanEhrTakeSandbox.py | 545 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self.canvas.delete("all") |
| modes/editor/TarzanTakeProtocolLight.py | 35 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | # - nie używa _refresh_all. |
| modes/editor/TarzanTakeProtocolLight.py | 852 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self.canvas.delete("all") |
| modes/editor/editor/EHR/tarzanAxisSandbox.py | 534 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all() |
| modes/editor/editor/EHR/tarzanAxisSandbox.py | 595 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._scale_row(box, "VIEW Y SCALE", self.display_y_scale, 200.0, 800.0, 10.0, self._refresh_all) |
| modes/editor/editor/EHR/tarzanAxisSandbox.py | 596 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._scale_row(box, "MOUSE PRECISION", self.mouse_y_precision, 0.10, 1.00, 0.05, self._refresh_all) |
| modes/editor/editor/EHR/tarzanAxisSandbox.py | 597 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._scale_row(box, "TOP/BOTTOM MARGIN", self.top_bottom_margin, 8, 60, 1, self._refresh_all) |
| modes/editor/editor/EHR/tarzanAxisSandbox.py | 703 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Zastosowano strojenie STEP.") |
| modes/editor/editor/EHR/tarzanAxisSandbox.py | 710 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all(f"Wczytano parametry mechaniki: {mechanics.axis_name}.") |
| modes/editor/editor/EHR/tarzanAxisSandbox.py | 732 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all(f"Wczytano preset TXT: {path}") |
| modes/editor/editor/EHR/tarzanAxisSandbox.py | 738 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Przywrócono domyślne parametry STEP.") |
| modes/editor/editor/EHR/tarzanAxisSandbox.py | 743 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Sinus test ustawiony.") |
| modes/editor/editor/EHR/tarzanAxisSandbox.py | 748 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Negative test ustawiony.") |
| modes/editor/editor/EHR/tarzanAxisSandbox.py | 753 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Zero cross test ustawiony.") |
| modes/editor/editor/EHR/tarzanAxisSandbox.py | 758 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Linia wyzerowana.") |
| modes/editor/editor/EHR/tarzanAxisSandbox.py | 763 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Przywrócono ostatni stan bazowy.") |
| modes/editor/editor/EHR/tarzanAxisSandbox.py | 810 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | c.delete("all") |
| modes/editor/editor/EHR/tarzanAxisSandbox.py | 859 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | c.delete("all") |
| modes/editor/editor/EHR/tarzanAxisSandbox.py | 904 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | def _refresh_all(self, status: str \| None = None) -> None: |
| modes/editor/editor/EHR/tarzanAxisSandbox.py | 930 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all(f"Wybrano punkt {idx}.") |
| modes/editor/editor/EHR/tarzanAxisSandbox.py | 935 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("PAN linii.") |
| modes/editor/editor/EHR/tarzanAxisSandbox.py | 960 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Gotowy.") |
| modes/editor/editor/EHR/tarzanAxisSandbox.py | 967 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Dodano punkt.") |
| modes/editor/editor/EHR/tarzanAxisSandbox.py | 975 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Usunięto punkt.") |
| modes/editor/editor/EHR/tarzanEhrUi.py | 704 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self.canvas.delete("all") |
| modes/editor/editor/EHR/tarzanEhrUi.py | 1243 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | canvas.delete("all") |
| modes/editor/editor/EHR/tarzanEhrUi.py | 1411 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self.after_idle(self._refresh_all) |
| modes/editor/editor/EHR/tarzanEhrUi.py | 1411 | after_refresh | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | self.after_idle(self._refresh_all) |
| modes/editor/editor/EHR/tarzanEhrUi.py | 1657 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Zastosowano ustawienia osi.") |
| modes/editor/editor/EHR/tarzanEhrUi.py | 1666 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Zastosowano strojenie STEP.") |
| modes/editor/editor/EHR/tarzanEhrUi.py | 1677 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all(f"Wczytano parametry mechaniki: {mechanics.axis_name}.") |
| modes/editor/editor/EHR/tarzanEhrUi.py | 1770 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all(f"Wczytano ustawienia osi: {path}") |
| modes/editor/editor/EHR/tarzanEhrUi.py | 1807 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all(f"Wczytano preset TXT: {path}") |
| modes/editor/editor/EHR/tarzanEhrUi.py | 1818 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Przywrócono domyślne parametry STEP.") |
| modes/editor/editor/EHR/tarzanEhrUi.py | 1828 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Sinus test ustawiony.") |
| modes/editor/editor/EHR/tarzanEhrUi.py | 1838 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Negative test ustawiony.") |
| modes/editor/editor/EHR/tarzanEhrUi.py | 1848 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Zero cross test ustawiony.") |
| modes/editor/editor/EHR/tarzanEhrUi.py | 1858 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Linia wyzerowana.") |
| modes/editor/editor/EHR/tarzanEhrUi.py | 1867 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Przywrócono ostatni stan bazowy.") |
| modes/editor/editor/EHR/tarzanEhrUi.py | 1891 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | c.delete("all") |
| modes/editor/editor/EHR/tarzanEhrUi.py | 1958 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | c.delete("all") |
| modes/editor/editor/EHR/tarzanEhrUi.py | 2017 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | @profile_method('EHR_AXIS_DIALOG._refresh_all') |
| modes/editor/editor/EHR/tarzanEhrUi.py | 2018 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | def _refresh_all(self, status: str \| None = None) -> None: |
| modes/editor/editor/EHR/tarzanEhrUi.py | 2095 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Gotowy.") |
| modes/editor/editor/EHR/tarzanEhrUi.py | 2107 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Dodano punkt.") |
| modes/editor/editor/EHR/tarzanEhrUi.py | 2120 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Usunięto punkt.") |
| modes/editor/editor/EHR/tarzanEhrUi.py | 2211 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self.after_idle(self._refresh_all) |
| modes/editor/editor/EHR/tarzanEhrUi.py | 2211 | after_refresh | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | self.after_idle(self._refresh_all) |
| modes/editor/editor/EHR/tarzanEhrUi.py | 2366 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all(light=True, status=status) |
| modes/editor/editor/EHR/tarzanEhrUi.py | 2395 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | dlg._refresh_all() |
| modes/editor/editor/EHR/tarzanEhrUi.py | 2396 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all(light=False, status="Zastosowano ustawienia MAIN TAKE.") |
| modes/editor/editor/EHR/tarzanEhrUi.py | 2509 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all( |
| modes/editor/editor/EHR/tarzanEhrUi.py | 2520 | after_refresh | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | self._configure_after_id = self.after(40, self._flush_configure_refresh) |
| modes/editor/editor/EHR/tarzanEhrUi.py | 2683 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | c.delete("all") |
| modes/editor/editor/EHR/tarzanEhrUi.py | 2960 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | @profile_method('EHR_MAIN._refresh_all') |
| modes/editor/editor/EHR/tarzanEhrUi.py | 2961 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | def _refresh_all(self, light: bool = False, status: str \| None = None) -> None: |
| modes/editor/editor/EHR/tarzanEhrUi.py | 3029 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all(light=True, status=None) |
| modes/editor/editor/EHR/tarzanEhrUi.py | 3232 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all(light=False, status=f"Wczytano TAKE TXT: {path.name}") |
| modes/editor/editor/TarzanEhrTakeSandbox.py | 545 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self.canvas.delete("all") |
| modes/editor/editor/TarzanTakeProtocolLight.py | 35 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | # - nie używa _refresh_all. |
| modes/editor/editor/TarzanTakeProtocolLight.py | 852 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self.canvas.delete("all") |
| modes/editor/editor/tarzanAxisSandbox.py | 534 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all() |
| modes/editor/editor/tarzanAxisSandbox.py | 595 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._scale_row(box, "VIEW Y SCALE", self.display_y_scale, 200.0, 800.0, 10.0, self._refresh_all) |
| modes/editor/editor/tarzanAxisSandbox.py | 596 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._scale_row(box, "MOUSE PRECISION", self.mouse_y_precision, 0.10, 1.00, 0.05, self._refresh_all) |
| modes/editor/editor/tarzanAxisSandbox.py | 597 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._scale_row(box, "TOP/BOTTOM MARGIN", self.top_bottom_margin, 8, 60, 1, self._refresh_all) |
| modes/editor/editor/tarzanAxisSandbox.py | 703 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Zastosowano strojenie STEP.") |
| modes/editor/editor/tarzanAxisSandbox.py | 710 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all(f"Wczytano parametry mechaniki: {mechanics.axis_name}.") |
| modes/editor/editor/tarzanAxisSandbox.py | 732 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all(f"Wczytano preset TXT: {path}") |
| modes/editor/editor/tarzanAxisSandbox.py | 738 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Przywrócono domyślne parametry STEP.") |
| modes/editor/editor/tarzanAxisSandbox.py | 743 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Sinus test ustawiony.") |
| modes/editor/editor/tarzanAxisSandbox.py | 748 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Negative test ustawiony.") |
| modes/editor/editor/tarzanAxisSandbox.py | 753 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Zero cross test ustawiony.") |
| modes/editor/editor/tarzanAxisSandbox.py | 758 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Linia wyzerowana.") |
| modes/editor/editor/tarzanAxisSandbox.py | 763 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Przywrócono ostatni stan bazowy.") |
| modes/editor/editor/tarzanAxisSandbox.py | 810 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | c.delete("all") |
| modes/editor/editor/tarzanAxisSandbox.py | 878 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | c.delete("all") |
| modes/editor/editor/tarzanAxisSandbox.py | 923 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | def _refresh_all(self, status: str \| None = None) -> None: |
| modes/editor/editor/tarzanAxisSandbox.py | 949 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all(f"Wybrano punkt {idx}.") |
| modes/editor/editor/tarzanAxisSandbox.py | 954 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("PAN linii.") |
| modes/editor/editor/tarzanAxisSandbox.py | 979 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Gotowy.") |
| modes/editor/editor/tarzanAxisSandbox.py | 986 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Dodano punkt.") |
| modes/editor/editor/tarzanAxisSandbox.py | 994 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Usunięto punkt.") |
| modes/editor/tarzanAxisSandbox.py | 534 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all() |
| modes/editor/tarzanAxisSandbox.py | 595 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._scale_row(box, "VIEW Y SCALE", self.display_y_scale, 200.0, 800.0, 10.0, self._refresh_all) |
| modes/editor/tarzanAxisSandbox.py | 596 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._scale_row(box, "MOUSE PRECISION", self.mouse_y_precision, 0.10, 1.00, 0.05, self._refresh_all) |
| modes/editor/tarzanAxisSandbox.py | 597 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._scale_row(box, "TOP/BOTTOM MARGIN", self.top_bottom_margin, 8, 60, 1, self._refresh_all) |
| modes/editor/tarzanAxisSandbox.py | 703 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Zastosowano strojenie STEP.") |
| modes/editor/tarzanAxisSandbox.py | 710 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all(f"Wczytano parametry mechaniki: {mechanics.axis_name}.") |
| modes/editor/tarzanAxisSandbox.py | 732 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all(f"Wczytano preset TXT: {path}") |
| modes/editor/tarzanAxisSandbox.py | 738 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Przywrócono domyślne parametry STEP.") |
| modes/editor/tarzanAxisSandbox.py | 743 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Sinus test ustawiony.") |
| modes/editor/tarzanAxisSandbox.py | 748 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Negative test ustawiony.") |
| modes/editor/tarzanAxisSandbox.py | 753 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Zero cross test ustawiony.") |
| modes/editor/tarzanAxisSandbox.py | 758 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Linia wyzerowana.") |
| modes/editor/tarzanAxisSandbox.py | 763 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Przywrócono ostatni stan bazowy.") |
| modes/editor/tarzanAxisSandbox.py | 810 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | c.delete("all") |
| modes/editor/tarzanAxisSandbox.py | 878 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | c.delete("all") |
| modes/editor/tarzanAxisSandbox.py | 923 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | def _refresh_all(self, status: str \| None = None) -> None: |
| modes/editor/tarzanAxisSandbox.py | 949 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all(f"Wybrano punkt {idx}.") |
| modes/editor/tarzanAxisSandbox.py | 954 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("PAN linii.") |
| modes/editor/tarzanAxisSandbox.py | 979 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Gotowy.") |
| modes/editor/tarzanAxisSandbox.py | 986 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Dodano punkt.") |
| modes/editor/tarzanAxisSandbox.py | 994 | refresh_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | self._refresh_all("Usunięto punkt.") |
| modes/editor/tarzanKHR.py | 611 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | c.delete("all") |
| modes/editor/tarzanKHR.py | 950 | draw_khr | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | self._draw_input() |
| modes/editor/tarzanKHR.py | 991 | draw_khr | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | self._draw_input() |
| modes/editor/tarzanKHR.py | 1094 | draw_khr | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | self._draw_input() |
| modes/editor/tarzanKHR.py | 1158 | draw_khr | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | self._draw_input() |
| modes/editor/tarzanKHR.py | 1161 | after_refresh | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | self.after(self._camera_preview_refresh_ms, self._camera_preview_loop) |
| modes/editor/tarzanKHR.py | 1372 | after_refresh | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | self.after(self._ui_refresh_ms, self._ui_loop) |
| modes/editor/tarzanKHR.py | 1434 | draw_khr | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | self._draw_input() |
| modes/editor/tarzanKHR.py | 1435 | draw_khr | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | self._draw_khr() |
| modes/editor/tarzanKHR.py | 1436 | draw_khr | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | self._draw_output() |
| modes/editor/tarzanKHR.py | 1438 | draw_khr | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | @khr_profiled("KHR_UI._draw_input") |
| modes/editor/tarzanKHR.py | 1439 | draw_khr | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | def _draw_input(self) -> None: |
| modes/editor/tarzanKHR.py | 1441 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | c.delete("all") |
| modes/editor/tarzanKHR.py | 1444 | draw_khr | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | self._draw_camera_input() |
| modes/editor/tarzanKHR.py | 1476 | draw_khr | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | @khr_profiled("KHR_UI._draw_camera_input") |
| modes/editor/tarzanKHR.py | 1477 | draw_khr | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | def _draw_camera_input(self) -> None: |
| modes/editor/tarzanKHR.py | 1558 | draw_khr | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | @khr_profiled("KHR_UI._draw_khr") |
| modes/editor/tarzanKHR.py | 1559 | draw_khr | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | def _draw_khr(self) -> None: |
| modes/editor/tarzanKHR.py | 1561 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | c.delete("all") |
| modes/editor/tarzanKHR.py | 1582 | draw_khr | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | @khr_profiled("KHR_UI._draw_output") |
| modes/editor/tarzanKHR.py | 1583 | draw_khr | ROZDZIELIĆ: STRUKTURA = RENDER, WARTOŚĆ/STATUS = TARZAN_SNAJPER | def _draw_output(self) -> None: |
| modes/editor/tarzanKHR.py | 1585 | canvas_delete_all | ZOSTAWIĆ TYLKO DLA STRUKTURY; WARTOŚCI/POZYCJE ZASTĄPIĆ TARZAN_SNAJPER | c.delete("all") |

---

# 7. Zasada wdrożenia

## Usunąć jako model dynamiczny

```txt
def nextion_tick
self.nextion_tick
nextion_refresh_previews w pętli
widget.refresh przy zmianach wartości
refresh_axis_cards przy jednej wartości
_refresh_all przy ruchu punktu / jednej osi / jednej wartości
canvas.delete("all") przy statusach/licznikach/pozycjach
```

## Zostawić tylko jako render strukturalny

```txt
pierwszy render ekranu
zmiana strony
zmiana layoutu
zmiana liczby osi
wczytanie TAKE
reset sceny
pełna przebudowa Canvas po zmianie struktury
```

## Po renderze strukturalnym

Moduł musi rejestrować konkretne cele:

```py
canvas_adapter.register_item(scope, target, prop, canvas, item_id)
tk_adapter.register_widget(scope, target, widget)
```

## Dynamicznie

Tylko:

```py
snajper.fire_from_signal(raw_signal, value)
```

albo:

```py
snajper.fire(logical_signal, value)
```

---

# 8. Uwaga o kompletności

Ten rejestr zawiera:
- wszystkie komponenty znalezione w przesłanych plikach HMI Nextiona,
- wszystkie widgety Tkinter znalezione przez skan wzorców konstrukcyjnych,
- wszystkie Canvas targety znalezione przez skan `create_*`,
- wszystkie miejsca starego odświeżania znalezione przez wzorce `refresh`, `draw`, `delete("all")`, `tick`.

Jeżeli jakiś widget jest tworzony dynamicznie bez wzorca `self.x = ttk.Label(...)` albo Canvas item nie jest przypisany do zmiennej, jest w rejestrze jako cel wygenerowany z pliku i linii. Przy wdrożeniu trzeba ten cel nazwać projektowo i zarejestrować ręcznie po pełnym renderze.
