from __future__ import annotations

"""
TARZAN SNAJPER TARGET

Target wskazuje cel:
    logical_signal -> adapter/scope/component/prop

Nie ujednolica nazw sygnałów.
Nie formatuje wartości.
Nie strzela.

Po czyszczeniu usunięto stary techniczny skan HMI bez realnego źródła.
Zostają aktywne cele strategiczne i kilka technicznych wyjątków używanych
przez Bridge / Nextion.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple


TARZAN_SNAJPER_ADAPTERS: Tuple[str, ...] = ('physical_nextion', 'canvas_preview', 'par_tkinter', 'ehr_canvas', 'ehr_tkinter', 'sandbox_canvas', 'sandbox_tkinter', 'timeline_canvas', 'layout_canvas', 'khr_canvas', 'khr_tkinter', 'tfd_adapter', 'take_adapter', 'log_adapter', 'signal_row', 'audio_adapter')

TARZAN_SNAJPER_PROPS: Tuple[str, ...] = ('coords', 'en', 'pco', 'pic', 'play', 'state', 'text', 'tim', 'txt', 'ui_cut', 'val', 'value', 'visible', 'error')

TARZAN_SNAJPER_SCOPE_GROUPS: Tuple[str, ...] = ('rrp_main', 'take_main', 'settings_main', 'level_xyz', 'page1', 'boot', 'mode_main', 'face_rec', 'keybdA', 'par_rrp', 'par_timeline', 'par_layout', 'axis_panel', 'sensors_panel', 'take_panel', 'status_panel', 'nextion_panel', 'ehr_main', 'ehr_protocol', 'ehr_axis_info', 'ehr_take_slots', 'sandbox', 'khr', 'khr_input', 'khr_output', 'audio', 'nextion_audio')


@dataclass(frozen=True)
class TarzanSnajperTarget:
    """Pojedynczy cel Snajpera."""
    adapter: str
    scope: str
    target: str
    prop: str


def T(adapter: str, scope: str, target: str, prop: str) -> TarzanSnajperTarget:
    return TarzanSnajperTarget(adapter=adapter, scope=scope, target=target, prop=prop)


DEFAULT_TARZAN_SNAJPER_TARGETS: Dict[str, List[TarzanSnajperTarget]] = {
    'rrp_p1_axis_index': [
        T('physical_nextion', 'rrp_main', 'va_p1_axis', 'val'),
        T('canvas_preview', 'rrp_main', 'va_p1_axis', 'val'),
    ],
    'rrp_p2_axis_index': [
        T('physical_nextion', 'rrp_main', 'va_p2_axis', 'val'),
        T('canvas_preview', 'rrp_main', 'va_p2_axis', 'val'),
    ],
    'rrp_p1_btn_cam_h': [
        T('physical_nextion', 'rrp_main', 'b_p1_cam_h', 'val'),
        T('canvas_preview', 'rrp_main', 'b_p1_cam_h', 'val'),
    ],
    'rrp_p1_btn_cam_v': [
        T('physical_nextion', 'rrp_main', 'b_p1_cam_v', 'val'),
        T('canvas_preview', 'rrp_main', 'b_p1_cam_v', 'val'),
    ],
    'rrp_p1_btn_cam_f': [
        T('physical_nextion', 'rrp_main', 'b_p1_cam_f', 'val'),
        T('canvas_preview', 'rrp_main', 'b_p1_cam_f', 'val'),
    ],
    'rrp_p1_btn_arm_t': [
        T('physical_nextion', 'rrp_main', 'b_p1_cam_t', 'val'),
        T('canvas_preview', 'rrp_main', 'b_p1_cam_t', 'val'),
    ],
    'rrp_p1_btn_arm_h': [
        T('physical_nextion', 'rrp_main', 'b_p1_arm_h', 'val'),
        T('canvas_preview', 'rrp_main', 'b_p1_arm_h', 'val'),
    ],
    'rrp_p1_btn_arm_v': [
        T('physical_nextion', 'rrp_main', 'b_p1_arm_v', 'val'),
        T('canvas_preview', 'rrp_main', 'b_p1_arm_v', 'val'),
    ],
    'rrp_p2_btn_cam_h': [
        T('physical_nextion', 'rrp_main', 'b_p2_cam_h', 'val'),
        T('canvas_preview', 'rrp_main', 'b_p2_cam_h', 'val'),
    ],
    'rrp_p2_btn_cam_v': [
        T('physical_nextion', 'rrp_main', 'b_p2_cam_v', 'val'),
        T('canvas_preview', 'rrp_main', 'b_p2_cam_v', 'val'),
    ],
    'rrp_p2_btn_cam_f': [
        T('physical_nextion', 'rrp_main', 'b_p2_cam_f', 'val'),
        T('canvas_preview', 'rrp_main', 'b_p2_cam_f', 'val'),
    ],
    'rrp_p2_btn_arm_t': [
        T('physical_nextion', 'rrp_main', 'b_p2_cam_t', 'val'),
        T('canvas_preview', 'rrp_main', 'b_p2_cam_t', 'val'),
    ],
    'rrp_p2_btn_arm_h': [
        T('physical_nextion', 'rrp_main', 'b_p2_arm_h', 'val'),
        T('canvas_preview', 'rrp_main', 'b_p2_arm_h', 'val'),
    ],
    'rrp_p2_btn_arm_v': [
        T('physical_nextion', 'rrp_main', 'b_p2_arm_v', 'val'),
        T('canvas_preview', 'rrp_main', 'b_p2_arm_v', 'val'),
    ],
    'rrp_p1_dir': [
        T('physical_nextion', 'rrp_main', 'b_p1_dir', 'val'),
        T('physical_nextion', 'rrp_main', 'va_p1_dir', 'val'),
        T('physical_nextion', 'rrp_main', 't_p1_val', 'pco'),
        T('canvas_preview', 'rrp_main', 'b_p1_dir', 'val'),
        T('canvas_preview', 'rrp_main', 't_p1_val', 'pco'),
        T('par_tkinter', 'par_rrp', 'p1_dir_widget', 'state'),
    ],
    'rrp_p1_sens': [
        T('physical_nextion', 'rrp_main', 'h_p1_sens', 'val'),
        T('canvas_preview', 'rrp_main', 'h_p1_sens', 'val'),
        T('par_tkinter', 'par_rrp', 'p1_sens_slider', 'value'),
    ],
    'rrp_p1_value': [
        T('physical_nextion', 'rrp_main', 't_p1_val', 'txt'),
        T('canvas_preview', 'rrp_main', 't_p1_val', 'txt'),
        T('par_tkinter', 'rrp_panel', 'p1_value_label', 'text'),
    ],
    'rrp_p2_dir': [
        T('physical_nextion', 'rrp_main', 'b_p2_dir', 'val'),
        T('physical_nextion', 'rrp_main', 'va_p2_dir', 'val'),
        T('physical_nextion', 'rrp_main', 't_p2_val', 'pco'),
        T('canvas_preview', 'rrp_main', 'b_p2_dir', 'val'),
        T('canvas_preview', 'rrp_main', 't_p2_val', 'pco'),
        T('par_tkinter', 'par_rrp', 'p2_dir_widget', 'state'),
    ],
    'rrp_p2_sens': [
        T('physical_nextion', 'rrp_main', 'h_p2_sens', 'val'),
        T('canvas_preview', 'rrp_main', 'h_p2_sens', 'val'),
        T('par_tkinter', 'par_rrp', 'p2_sens_slider', 'value'),
    ],
    'rrp_p2_value': [
        T('physical_nextion', 'rrp_main', 't_p2_val', 'txt'),
        T('canvas_preview', 'rrp_main', 't_p2_val', 'txt'),
        T('par_tkinter', 'rrp_panel', 'p2_value_label', 'text'),
    ],
    'take_timecode': [
        T('physical_nextion', 'take_main', 't0', 'txt'),
        T('canvas_preview', 'take_main', 't0', 'txt'),
        T('par_tkinter', 'take_panel', 'timecode_label', 'text'),
    ],
    'axis_0_value': [
        T('physical_nextion', 'take_main', 't_axis0', 'txt'),
        T('canvas_preview', 'take_main', 't_axis0', 'txt'),
        T('par_tkinter', 'axis_panel', 'axis_0_value_label', 'text'),
    ],
    'axis_1_value': [
        T('physical_nextion', 'take_main', 't_axis1', 'txt'),
        T('canvas_preview', 'take_main', 't_axis1', 'txt'),
        T('par_tkinter', 'axis_panel', 'axis_1_value_label', 'text'),
    ],
    'axis_2_value': [
        T('physical_nextion', 'take_main', 't_axis2', 'txt'),
        T('canvas_preview', 'take_main', 't_axis2', 'txt'),
        T('par_tkinter', 'axis_panel', 'axis_2_value_label', 'text'),
    ],
    'axis_3_value': [
        T('physical_nextion', 'take_main', 't_axis3', 'txt'),
        T('canvas_preview', 'take_main', 't_axis3', 'txt'),
        T('par_tkinter', 'axis_panel', 'axis_3_value_label', 'text'),
    ],
    'axis_4_value': [
        T('physical_nextion', 'take_main', 't_axis4', 'txt'),
        T('canvas_preview', 'take_main', 't_axis4', 'txt'),
        T('par_tkinter', 'axis_panel', 'axis_4_value_label', 'text'),
    ],
    'axis_5_value': [
        T('physical_nextion', 'take_main', 't_axis5', 'txt'),
        T('canvas_preview', 'take_main', 't_axis5', 'txt'),
        T('par_tkinter', 'axis_panel', 'axis_5_value_label', 'text'),
    ],
    'level_x': [
        T('physical_nextion', 'level_xyz', 'va0', 'val'),
        T('canvas_preview', 'level_xyz', 'va0', 'val'),
        T('par_tkinter', 'sensors_panel', 'level_x_label', 'text'),
    ],
    'level_y': [
        T('physical_nextion', 'level_xyz', 'va1', 'val'),
        T('canvas_preview', 'level_xyz', 'va1', 'val'),
        T('par_tkinter', 'sensors_panel', 'level_y_label', 'text'),
    ],
    'nextion_ui_cut': [
        T('physical_nextion', 'settings_main', 'b_ui_cut', 'val'),
        T('par_tkinter', 'nextion_panel', 'ui_cut_status_label', 'text'),
        T('par_tkinter', 'nextion_panel', 'ui_cut_button', 'state'),
        T('canvas_preview', 'nextion_7', 'screen', 'ui_cut'),
    ],
    'ehr_axis_0_curve': [
        T('ehr_canvas', 'ehr_main', 'axis_0_curve', 'coords'),
    ],
    'ehr_axis_0_metrics': [
        T('ehr_tkinter', 'ehr_axis_info', 'axis_0_metrics', 'text'),
    ],
    'ehr_axis_0_step_preview': [
        T('ehr_canvas', 'ehr_protocol', 'axis_0_step_bars', 'coords'),
    ],
    'ehr_axis_0_live_matrix': [
        T('ehr_main', 'protocol_preview', 'axis_0_live_matrix', 'refresh'),
    ],
    'ehr_axis_0_final_matrix': [
        T('ehr_main', 'protocol_preview', 'axis_0_final_matrix', 'refresh'),
    ],
    'ehr_axis_1_curve': [
        T('ehr_canvas', 'ehr_main', 'axis_1_curve', 'coords'),
    ],
    'ehr_axis_1_metrics': [
        T('ehr_tkinter', 'ehr_axis_info', 'axis_1_metrics', 'text'),
    ],
    'ehr_axis_1_step_preview': [
        T('ehr_canvas', 'ehr_protocol', 'axis_1_step_bars', 'coords'),
    ],
    'ehr_axis_1_live_matrix': [
        T('ehr_main', 'protocol_preview', 'axis_1_live_matrix', 'refresh'),
    ],
    'ehr_axis_1_final_matrix': [
        T('ehr_main', 'protocol_preview', 'axis_1_final_matrix', 'refresh'),
    ],
    'ehr_axis_2_curve': [
        T('ehr_canvas', 'ehr_main', 'axis_2_curve', 'coords'),
    ],
    'ehr_axis_2_metrics': [
        T('ehr_tkinter', 'ehr_axis_info', 'axis_2_metrics', 'text'),
    ],
    'ehr_axis_2_step_preview': [
        T('ehr_canvas', 'ehr_protocol', 'axis_2_step_bars', 'coords'),
    ],
    'ehr_axis_2_live_matrix': [
        T('ehr_main', 'protocol_preview', 'axis_2_live_matrix', 'refresh'),
    ],
    'ehr_axis_2_final_matrix': [
        T('ehr_main', 'protocol_preview', 'axis_2_final_matrix', 'refresh'),
    ],
    'ehr_axis_3_curve': [
        T('ehr_canvas', 'ehr_main', 'axis_3_curve', 'coords'),
    ],
    'ehr_axis_3_metrics': [
        T('ehr_tkinter', 'ehr_axis_info', 'axis_3_metrics', 'text'),
    ],
    'ehr_axis_3_step_preview': [
        T('ehr_canvas', 'ehr_protocol', 'axis_3_step_bars', 'coords'),
    ],
    'ehr_axis_3_live_matrix': [
        T('ehr_main', 'protocol_preview', 'axis_3_live_matrix', 'refresh'),
    ],
    'ehr_axis_3_final_matrix': [
        T('ehr_main', 'protocol_preview', 'axis_3_final_matrix', 'refresh'),
    ],
    'ehr_axis_4_curve': [
        T('ehr_canvas', 'ehr_main', 'axis_4_curve', 'coords'),
    ],
    'ehr_axis_4_metrics': [
        T('ehr_tkinter', 'ehr_axis_info', 'axis_4_metrics', 'text'),
    ],
    'ehr_axis_4_step_preview': [
        T('ehr_canvas', 'ehr_protocol', 'axis_4_step_bars', 'coords'),
    ],
    'ehr_axis_4_live_matrix': [
        T('ehr_main', 'protocol_preview', 'axis_4_live_matrix', 'refresh'),
    ],
    'ehr_axis_4_final_matrix': [
        T('ehr_main', 'protocol_preview', 'axis_4_final_matrix', 'refresh'),
    ],
    'ehr_axis_5_curve': [
        T('ehr_canvas', 'ehr_main', 'axis_5_curve', 'coords'),
    ],
    'ehr_axis_5_metrics': [
        T('ehr_tkinter', 'ehr_axis_info', 'axis_5_metrics', 'text'),
    ],
    'ehr_axis_5_step_preview': [
        T('ehr_canvas', 'ehr_protocol', 'axis_5_step_bars', 'coords'),
    ],
    'ehr_axis_5_live_matrix': [
        T('ehr_main', 'protocol_preview', 'axis_5_live_matrix', 'refresh'),
    ],
    'ehr_axis_5_final_matrix': [
        T('ehr_main', 'protocol_preview', 'axis_5_final_matrix', 'refresh'),
    ],
    'ehr_take_slot_0_status': [
        T('ehr_tkinter', 'ehr_take_slots', 'slot_0', 'state'),
    ],
    'ehr_take_slot_1_status': [
        T('ehr_tkinter', 'ehr_take_slots', 'slot_1', 'state'),
    ],
    'ehr_take_slot_2_status': [
        T('ehr_tkinter', 'ehr_take_slots', 'slot_2', 'state'),
    ],
    'ehr_take_slot_3_status': [
        T('ehr_tkinter', 'ehr_take_slots', 'slot_3', 'state'),
    ],
    'ehr_take_slot_4_status': [
        T('ehr_tkinter', 'ehr_take_slots', 'slot_4', 'state'),
    ],
    'ehr_take_slot_5_status': [
        T('ehr_tkinter', 'ehr_take_slots', 'slot_5', 'state'),
    ],
    'ehr_take_slot_6_status': [
        T('ehr_tkinter', 'ehr_take_slots', 'slot_6', 'state'),
    ],
    'ehr_take_slot_7_status': [
        T('ehr_tkinter', 'ehr_take_slots', 'slot_7', 'state'),
    ],
    'sandbox_curve': [
        T('sandbox_canvas', 'sandbox', 'curve', 'coords'),
    ],
    'sandbox_metrics': [
        T('sandbox_tkinter', 'sandbox', 'metrics_label', 'text'),
    ],
    'sandbox_step_preview': [
        T('sandbox_canvas', 'sandbox', 'step_bars', 'coords'),
    ],
    'timeline_clap_marker': [
        T('timeline_canvas', 'par_timeline', 'clap_marker', 'coords'),
    ],
    'timeline_cursor': [
        T('timeline_canvas', 'par_timeline', 'cursor', 'coords'),
    ],
    'timeline_take_marker': [
        T('timeline_canvas', 'par_timeline', 'take_marker', 'coords'),
    ],
    'layout_panel_status': [
        T('layout_canvas', 'par_layout', 'panel_status', 'text'),
    ],
    'layout_selected_cell': [
        T('layout_canvas', 'par_layout', 'selected_cell', 'coords'),
    ],
    'layout_zone_label': [
        T('layout_canvas', 'par_layout', 'zone_label', 'text'),
    ],
    'khr_input_marker': [
        T('khr_canvas', 'khr_input', 'marker', 'coords'),
    ],
    'khr_output_marker': [
        T('khr_canvas', 'khr_output', 'marker', 'coords'),
    ],
    'khr_status': [
        T('khr_tkinter', 'khr', 'status_label', 'text'),
    ],
    'nextion_level_xyz_va0_val': [
        T('physical_nextion', 'level_xyz', 'va0', 'val'),
        T('canvas_preview', 'level_xyz', 'va0', 'val'),
    ],
    'nextion_level_xyz_va1_val': [
        T('physical_nextion', 'level_xyz', 'va1', 'val'),
        T('canvas_preview', 'level_xyz', 'va1', 'val'),
    ],
    'nextion_level_xyz_va2_val': [
        T('physical_nextion', 'level_xyz', 'va2', 'val'),
        T('canvas_preview', 'level_xyz', 'va2', 'val'),
    ],
    'nextion_take_main_b_clap_val': [
        T('physical_nextion', 'take_main', 'b_clap', 'val'),
        T('canvas_preview', 'take_main', 'b_clap', 'val'),
    ],
    'nextion_take_main_t1_txt': [
        T('physical_nextion', 'take_main', 't1', 'txt'),
        T('canvas_preview', 'take_main', 't1', 'txt'),
    ],
    'step_dir_stream': [
    ],
    'take_time_ms': [
        T('canvas_preview', 'take_main', 't0', 'txt'),
    ],
    'take_number': [
        T('physical_nextion', 'take_main', 't_take', 'txt'),
        T('canvas_preview', 'take_main', 't_take', 'txt'),
        T('par_tkinter', 'take_panel', 'take_label', 'text'),
    ],
    'take_status': [
        T('physical_nextion', 'take_main', 't_status', 'txt'),
        T('canvas_preview', 'take_main', 't_status', 'txt'),
        T('par_tkinter', 'status_panel', 'status_label', 'text'),
    ],
    'sensor_xyz': [
        T('physical_nextion', 'take_main', 'tx', 'txt'),
        T('physical_nextion', 'take_main', 'ty', 'txt'),
        T('physical_nextion', 'take_main', 'tz', 'txt'),
        T('physical_nextion', 'take_main', 'tx', 'pco'),
        T('physical_nextion', 'take_main', 'ty', 'pco'),
        T('physical_nextion', 'take_main', 'tz', 'pco'),
        T('canvas_preview', 'take_main', 'tx', 'txt'),
        T('canvas_preview', 'take_main', 'ty', 'txt'),
        T('canvas_preview', 'take_main', 'tz', 'txt'),
        T('canvas_preview', 'take_main', 'tx', 'pco'),
        T('canvas_preview', 'take_main', 'ty', 'pco'),
        T('canvas_preview', 'take_main', 'tz', 'pco'),
        T('par_tkinter', 'sensors_panel', 'xyz_label', 'text'),
    ],
    'sensor_light_lux': [
        T('physical_nextion', 'take_main', 't_light', 'txt'),
        T('canvas_preview', 'take_main', 't_light', 'txt'),
    ],
    'sensor_temp_c': [
        T('physical_nextion', 'take_main', 't_temp', 'txt'),
        T('canvas_preview', 'take_main', 't_temp', 'txt'),
    ],
    'sensor_limits_status': [
        T('physical_nextion', 'take_main', 't_limits', 'txt'),
        T('canvas_preview', 'take_main', 't_limits', 'txt'),
    ],
    'sensor_laser_set': [
        T('physical_nextion', 'take_main', 't_laser', 'txt'),
        T('canvas_preview', 'take_main', 't_laser', 'txt'),
    ],
    'sensor_shock_state': [
        T('physical_nextion', 'take_main', 't_shock', 'txt'),
        T('canvas_preview', 'take_main', 't_shock', 'txt'),
    ],
    'par_mode': [
        T('physical_nextion', 'take_main', 't_status', 'txt'),
        T('canvas_preview', 'take_main', 't_status', 'txt'),
    ],
    'system_status': [
        T('physical_nextion', 'take_main', 't_status', 'txt'),
        T('canvas_preview', 'take_main', 't_status', 'txt'),
    ],
    'axis_0_dir': [
        T('physical_nextion', 'take_main', 't_axis0', 'pco'),
        T('canvas_preview', 'take_main', 't_axis0', 'pco'),
    ],
    'axis_1_dir': [
        T('physical_nextion', 'take_main', 't_axis1', 'pco'),
        T('canvas_preview', 'take_main', 't_axis1', 'pco'),
    ],
    'axis_2_dir': [
        T('physical_nextion', 'take_main', 't_axis2', 'pco'),
        T('canvas_preview', 'take_main', 't_axis2', 'pco'),
    ],
    'axis_3_dir': [
        T('physical_nextion', 'take_main', 't_axis3', 'pco'),
        T('canvas_preview', 'take_main', 't_axis3', 'pco'),
    ],
    'axis_4_dir': [
        T('physical_nextion', 'take_main', 't_axis4', 'pco'),
        T('canvas_preview', 'take_main', 't_axis4', 'pco'),
    ],
    'axis_5_dir': [
        T('physical_nextion', 'take_main', 't_axis5', 'pco'),
        T('canvas_preview', 'take_main', 't_axis5', 'pco'),
    ],
    'level_z': [
        T('par_tkinter', 'sensors_panel', 'level_z_label', 'text'),
    ],
    'tfd_title': [
        T('physical_nextion', 'take_main', 't1', 'txt'),
        T('physical_nextion', 'settings_main', 't_title', 'txt'),
        T('canvas_preview', 'take_main', 't1', 'txt'),
        T('canvas_preview', 'settings_main', 't_title', 'txt'),
        T('par_tkinter', 'take_panel', 'movie_title_label', 'text'),
        T('ehr_tkinter', 'ehr_main', 'protocol_label', 'text'),
    ],
    'tfd_director': [
        T('physical_nextion', 'take_main', 't2', 'txt'),
        T('physical_nextion', 'settings_main', 't_director', 'txt'),
        T('canvas_preview', 'take_main', 't2', 'txt'),
        T('canvas_preview', 'settings_main', 't_director', 'txt'),
        T('par_tkinter', 'take_panel', 'director_label', 'text'),
    ],
    'tfd_save_status': [
        T('physical_nextion', 'settings_main', 't_save_status', 'txt'),
        T('canvas_preview', 'settings_main', 't_save_status', 'txt'),
    ],
    'tfd_save_status_visible': [
        T('physical_nextion', 'settings_main', 't_save_status', 'visible'),
        T('canvas_preview', 'settings_main', 't_save_status', 'visible'),
    ],
    'tfd_title_pco': [
        T('physical_nextion', 'take_main', 't1', 'pco'),
        T('physical_nextion', 'settings_main', 't_title', 'pco'),
        T('canvas_preview', 'take_main', 't1', 'pco'),
        T('canvas_preview', 'settings_main', 't_title', 'pco'),
    ],
    'tfd_director_pco': [
        T('physical_nextion', 'take_main', 't2', 'pco'),
        T('physical_nextion', 'settings_main', 't_director', 'pco'),
        T('canvas_preview', 'take_main', 't2', 'pco'),
        T('canvas_preview', 'settings_main', 't_director', 'pco'),
    ],
    'sensor_shock': [
        T('physical_nextion', 'take_main', 't_shock', 'txt'),
        T('canvas_preview', 'take_main', 't_shock', 'txt'),
        T('par_tkinter', 'sensors_panel', 'shock_label', 'text'),
    ],
    'sensor_laser': [
        T('physical_nextion', 'take_main', 't_laser', 'txt'),
        T('canvas_preview', 'take_main', 't_laser', 'txt'),
        T('par_tkinter', 'sensors_panel', 'laser_label', 'text'),
    ],
    'sensor_limits': [
        T('physical_nextion', 'take_main', 't_limits', 'txt'),
        T('canvas_preview', 'take_main', 't_limits', 'txt'),
        T('par_tkinter', 'sensors_panel', 'limits_label', 'text'),
    ],
    'sensor_light': [
        T('physical_nextion', 'take_main', 't_light', 'txt'),
        T('canvas_preview', 'take_main', 't_light', 'txt'),
        T('par_tkinter', 'sensors_panel', 'light_label', 'text'),
    ],
    'sensor_temp': [
        T('physical_nextion', 'take_main', 't_temp', 'txt'),
        T('canvas_preview', 'take_main', 't_temp', 'txt'),
        T('par_tkinter', 'sensors_panel', 'temp_label', 'text'),
    ],
    'take_clap': [
        T('canvas_preview', 'take_main', 'b_clap', 'val'),
    ],
    'tfd_save_sound': [
        T('physical_nextion', 'settings_main', 'sound', 'play'),
    ],
    'tfd_axis_0_active': [
        T('tfd_adapter', 'axis0', 'active', 'visible'),
    ],
    'tfd_axis_1_active': [
        T('tfd_adapter', 'axis1', 'active', 'visible'),
    ],
    'tfd_axis_2_active': [
        T('tfd_adapter', 'axis2', 'active', 'visible'),
    ],
    'tfd_axis_3_active': [
        T('tfd_adapter', 'axis3', 'active', 'visible'),
    ],
    'tfd_axis_4_active': [
        T('tfd_adapter', 'axis4', 'active', 'visible'),
    ],
    'tfd_axis_5_active': [
        T('tfd_adapter', 'axis5', 'active', 'visible'),
    ],
    'tfd_laser_active': [
        T('tfd_adapter', 'sensors', 'laser', 'visible'),
    ],
    'tfd_laser_error': [
        T('tfd_adapter', 'sensors', 'laser', 'error'),
    ],
    'tfd_limits_active': [
        T('tfd_adapter', 'sensors', 'limits', 'visible'),
    ],
    'tfd_shock_active': [
        T('tfd_adapter', 'sensors', 'shock', 'visible'),
    ],
    'take_clap_start': [
        T('audio_adapter', 'audio', 'signals/clap', 'play'),
        T('log_adapter', 'nextion_audio', 'take_clap_start', 'text'),
    ],
    'take_clap_stop': [
        T('audio_adapter', 'audio', 'voice/motin_coplete', 'play'),
        T('log_adapter', 'nextion_audio', 'take_clap_stop', 'text'),
    ],
    'take_tc_running': [
        T('canvas_preview', 'take_main', 'b_clap', 'val'),
        T('par_tkinter', 'take_panel', 'tc_running', 'state'),
    ],
    'nextion_audio_event': [
        T('log_adapter', 'nextion_audio', 'last_event', 'text'),
    ],
}
