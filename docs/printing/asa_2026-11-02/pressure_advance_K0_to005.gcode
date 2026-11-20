; HEADER_BLOCK_START
; BambuStudio 02.08.02.61
; model printing time: 1m 52s; total estimated time: 10m 27s
; total layer number: 4
; total filament length [mm] : 398.03
; total filament volume [cm^3] : 957.38
; total filament weight [g] : 1.00
; filament_density: 1.04
; filament_diameter: 1.75
; max_z_height: 0.85
; filament: 1
; support_material_on_wipe_tower: 0
; HEADER_BLOCK_END

; CONFIG_BLOCK_START
; accel_to_decel_enable = 0
; accel_to_decel_factor = 50%
; activate_air_filtration = 1
; additional_cooling_fan_speed = 0
; additional_fan_full_speed_layer = 0
; alternate_extra_wall = 0
; ams_filament_load_time_ams = 0
; ams_filament_load_time_ams_lite = 0
; ams_filament_load_time_n3f_s = 0
; ams_filament_unload_time_ams = 0
; ams_filament_unload_time_ams_lite = 0
; ams_filament_unload_time_n3f_s = 0
; apply_scarf_seam_on_circles = 1
; auxiliary_fan = 1
; avoid_crossing_wall_includes_support = 0
; bed_custom_model = 
; bed_custom_texture = 
; bed_exclude_area = 0x0,18x0,18x28,0x28
; bed_heat_soak_area = 
; bed_temperature_formula = by_first_filament
; before_layer_change_gcode = 
; best_object_pos = 0.5,0.5
; bottom_color_penetration_layers = 3
; bottom_shell_layers = 3
; bottom_shell_thickness = 0
; bottom_surface_density = 100%
; bottom_surface_pattern = monotonic
; bridge_angle = 0
; bridge_flow = 1
; bridge_no_support = 0
; bridge_speed = 50
; brim_object_gap = 0.1
; brim_type = no_brim
; brim_width = 5
; chamber_temperatures = 0
; change_filament_gcode = ;=P1S 20251031=\nM620 S[next_extruder]A\nM204 S9000\nG1 Z{max_layer_z + 3.0} F1200\n\nG1 X70 F21000\nG1 Y245\nG1 Y265 F3000\nM400\nM106 P1 S0\nM106 P2 S0\n{if old_filament_temp > 142 && next_extruder < 255}\nM104 S[old_filament_temp]\n{endif}\n{if long_retractions_when_cut[previous_extruder]}\nM620.11 S1 I[previous_extruder] E-{retraction_distances_when_cut[previous_extruder]} F{flush_volumetric_speeds[previous_extruder]/2.4053*60}\n{else}\nM620.11 S0\n{endif}\nM400\nG1 X90 F3000\nG1 Y255 F4000\nG1 X100 F5000\nG1 X120 F15000\nG1 X20 Y50 F21000\nG1 Y-3\n{if toolchange_count == 2}\n; get travel path for change filament\nM620.1 X[travel_point_1_x] Y[travel_point_1_y] F21000 P0\nM620.1 X[travel_point_2_x] Y[travel_point_2_y] F21000 P1\nM620.1 X[travel_point_3_x] Y[travel_point_3_y] F21000 P2\n{endif}\nM620.1 E F{flush_volumetric_speeds[previous_extruder]/2.4053*60} T{flush_temperatures[previous_extruder]}\nT[next_extruder]\nM620.1 E F{flush_volumetric_speeds[next_extruder]/2.4053*60} T{flush_temperatures[next_extruder]}\n\n{if next_extruder < 255}\n{if long_retractions_when_cut[previous_extruder]}\nM620.11 S1 I[previous_extruder] E{retraction_distances_when_cut[previous_extruder]} F{flush_volumetric_speeds[previous_extruder]/2.4053*60}\nM628 S1\nG92 E0\nG1 E{retraction_distances_when_cut[previous_extruder]} F{flush_volumetric_speeds[previous_extruder]/2.4053*60}\nM400\nM629 S1\n{else}\nM620.11 S0\n{endif}\nG92 E0\n{if flush_length_1 > 1}\nM83\n; FLUSH_START\n; always use highest temperature to flush\nM400\n{if filament_type[next_extruder] == \"PETG\"}\nM109 S260\n{elsif filament_type[next_extruder] == \"PVA\"}\nM109 S210\n{else}\nM109 S{flush_temperatures[next_extruder]}\n{endif}\n{if flush_length_1 > 23.7}\nG1 E23.7 F{flush_volumetric_speeds[previous_extruder]/2.4053*60} ; do not need pulsatile flushing for start part\nG1 E{(flush_length_1 - 23.7) * 0.02} F50\nG1 E{(flush_length_1 - 23.7) * 0.23} F{flush_volumetric_speeds[previous_extruder]/2.4053*60}\nG1 E{(flush_length_1 - 23.7) * 0.02} F50\nG1 E{(flush_length_1 - 23.7) * 0.23} F{flush_volumetric_speeds[next_extruder]/2.4053*60}\nG1 E{(flush_length_1 - 23.7) * 0.02} F50\nG1 E{(flush_length_1 - 23.7) * 0.23} F{flush_volumetric_speeds[next_extruder]/2.4053*60}\nG1 E{(flush_length_1 - 23.7) * 0.02} F50\nG1 E{(flush_length_1 - 23.7) * 0.23} F{flush_volumetric_speeds[next_extruder]/2.4053*60}\n{else}\nG1 E{flush_length_1} F{flush_volumetric_speeds[previous_extruder]/2.4053*60}\n{endif}\n; FLUSH_END\nG1 E-[old_retract_length_toolchange] F1800\nG1 E[old_retract_length_toolchange] F300\n{endif}\n\n{if flush_length_2 > 1}\n\nG91\nG1 X3 F12000; move aside to extrude\nG90\nM83\n\n; FLUSH_START\nG1 E{flush_length_2 * 0.18} F{flush_volumetric_speeds[next_extruder]/2.4053*60}\nG1 E{flush_length_2 * 0.02} F50\nG1 E{flush_length_2 * 0.18} F{flush_volumetric_speeds[next_extruder]/2.4053*60}\nG1 E{flush_length_2 * 0.02} F50\nG1 E{flush_length_2 * 0.18} F{flush_volumetric_speeds[next_extruder]/2.4053*60}\nG1 E{flush_length_2 * 0.02} F50\nG1 E{flush_length_2 * 0.18} F{flush_volumetric_speeds[next_extruder]/2.4053*60}\nG1 E{flush_length_2 * 0.02} F50\nG1 E{flush_length_2 * 0.18} F{flush_volumetric_speeds[next_extruder]/2.4053*60}\nG1 E{flush_length_2 * 0.02} F50\n; FLUSH_END\nG1 E-[new_retract_length_toolchange] F1800\nG1 E[new_retract_length_toolchange] F300\n{endif}\n\n{if flush_length_3 > 1}\n\nG91\nG1 X3 F12000; move aside to extrude\nG90\nM83\n\n; FLUSH_START\nG1 E{flush_length_3 * 0.18} F{flush_volumetric_speeds[next_extruder]/2.4053*60}\nG1 E{flush_length_3 * 0.02} F50\nG1 E{flush_length_3 * 0.18} F{flush_volumetric_speeds[next_extruder]/2.4053*60}\nG1 E{flush_length_3 * 0.02} F50\nG1 E{flush_length_3 * 0.18} F{flush_volumetric_speeds[next_extruder]/2.4053*60}\nG1 E{flush_length_3 * 0.02} F50\nG1 E{flush_length_3 * 0.18} F{flush_volumetric_speeds[next_extruder]/2.4053*60}\nG1 E{flush_length_3 * 0.02} F50\nG1 E{flush_length_3 * 0.18} F{flush_volumetric_speeds[next_extruder]/2.4053*60}\nG1 E{flush_length_3 * 0.02} F50\n; FLUSH_END\nG1 E-[new_retract_length_toolchange] F1800\nG1 E[new_retract_length_toolchange] F300\n{endif}\n\n{if flush_length_4 > 1}\n\nG91\nG1 X3 F12000; move aside to extrude\nG90\nM83\n\n; FLUSH_START\nG1 E{flush_length_4 * 0.18} F{flush_volumetric_speeds[next_extruder]/2.4053*60}\nG1 E{flush_length_4 * 0.02} F50\nG1 E{flush_length_4 * 0.18} F{flush_volumetric_speeds[next_extruder]/2.4053*60}\nG1 E{flush_length_4 * 0.02} F50\nG1 E{flush_length_4 * 0.18} F{flush_volumetric_speeds[next_extruder]/2.4053*60}\nG1 E{flush_length_4 * 0.02} F50\nG1 E{flush_length_4 * 0.18} F{flush_volumetric_speeds[next_extruder]/2.4053*60}\nG1 E{flush_length_4 * 0.02} F50\nG1 E{flush_length_4 * 0.18} F{flush_volumetric_speeds[next_extruder]/2.4053*60}\nG1 E{flush_length_4 * 0.02} F50\n; FLUSH_END\n{endif}\n; FLUSH_START\nM400\nM109 S[new_filament_temp]\nG1 E2 F{flush_volumetric_speeds[next_extruder]/2.4053*60} ;Compensate for filament spillage during waiting temperature\n; FLUSH_END\nM400\nG92 E0\nG1 E-[new_retract_length_toolchange] F1800\nM106 P1 S255\nM400 S3\n\nG1 X70 F5000\nG1 X90 F3000\nG1 Y255 F4000\nG1 X105 F5000\nG1 Y265 F5000\nG1 X70 F10000\nG1 X100 F5000\nG1 X70 F10000\nG1 X100 F5000\n\nG1 X70 F10000\nG1 X80 F15000\nG1 X60\nG1 X80\nG1 X60\nG1 X80 ; shake to put down garbage\nG1 X100 F5000\nG1 X165 F15000; wipe and shake\nG1 Y256 ; move Y to aside, prevent collision\nM400\nG1 Z{max_layer_z + 3.0} F3000\n{if layer_z <= (initial_layer_print_height + 0.001)}\nM204 S[initial_layer_acceleration]\n{else}\nM204 S[default_acceleration]\n{endif}\n{else}\nG1 X[x_after_toolchange] Y[y_after_toolchange] Z[z_after_toolchange] F12000\n{endif}\nM621 S[next_extruder]A\n
; circle_compensation_manual_offset = 0
; circle_compensation_speed = 200
; close_additional_fan_first_x_layers = 3
; close_fan_the_first_x_layers = 3
; complete_print_exhaust_fan_speed = 70
; cool_plate_temp = 0
; cool_plate_temp_initial_layer = 0
; cooling_filter_enabled = 0
; cooling_perimeter_transition_distance = 10
; cooling_slowdown_logic = uniform_cooling
; counter_coef_1 = 0
; counter_coef_2 = 0.008
; counter_coef_3 = -0.041
; counter_limit_max = 0.033
; counter_limit_min = -0.035
; counterbore_hole_bridging = none
; curr_bed_type = Textured PEI Plate
; default_acceleration = 10000
; default_ams_type = -1
; default_filament_colour = ""
; default_filament_profile = "Bambu PLA Basic @BBL P1S 0.4 nozzle"
; default_jerk = 0
; default_nozzle_volume_type = Standard
; default_print_profile = 0.20mm Standard @BBL X1C
; deretraction_speed = 30
; detect_floating_vertical_shell = 1
; detect_narrow_internal_solid_infill = 1
; detect_overhang_wall = 1
; detect_thin_wall = 0
; diameter_limit = 50
; different_settings_to_system = brim_type;initial_layer_line_width;initial_layer_print_height;initial_layer_speed;line_width;outer_wall_speed;wall_loops;filament_max_volumetric_speed;nozzle_temperature;nozzle_temperature_initial_layer;
; draft_shield = disabled
; during_print_exhaust_fan_speed = 70
; elefant_foot_compensation = 0.15
; embedding_wall_into_infill = 0
; enable_arc_fitting = 1
; enable_circle_compensation = 0
; enable_filament_dynamic_map = 0
; enable_height_slowdown = 0
; enable_long_retraction_when_cut = 2
; enable_mixed_color_sublayer = 0
; enable_order_independent_overlap_carving = 0
; enable_overhang_bridge_fan = 1
; enable_overhang_speed = 1
; enable_pre_heating = 0
; enable_pressure_advance = 0
; enable_prime_tower = 0
; enable_support = 0
; enable_support_ironing = 0
; enable_tower_interface_features = 0
; enable_wrapping_detection = 0
; enforce_support_layers = 0
; eng_plate_temp = 100
; eng_plate_temp_initial_layer = 100
; ensure_vertical_shell_thickness = enabled
; exclude_object = 1
; extruder_ams_count = 1#0|4#0;1#0|4#0
; extruder_clearance_dist_to_rod = 33
; extruder_clearance_height_to_lid = 90
; extruder_clearance_height_to_rod = 34
; extruder_clearance_max_radius = 68
; extruder_colour = #018001
; extruder_max_nozzle_count = 1
; extruder_nozzle_stats = Standard#1
; extruder_nozzle_stats_new = 
; extruder_offset = 0x2
; extruder_printable_area = 
; extruder_type = Direct Drive
; extruder_variant_list = "Direct Drive Standard,Direct Drive High Flow"
; fan_cooling_layer_time = 35
; fan_direction = left
; fan_max_speed = 80
; fan_min_speed = 10
; farthest_point_timelapse = 1
; filament_adaptive_volumetric_speed = 0
; filament_adhesiveness_category = 200
; filament_bridge_speed = 25
; filament_change_length = 10
; filament_change_length_nc = 10
; filament_colour = #161616
; filament_colour_type = 2
; filament_cooling_before_tower = 0
; filament_cost = 20
; filament_density = 1.04
; filament_dev_ams_drying_ams_limitations = 1
; filament_dev_ams_drying_heat_distortion_temperature = 100
; filament_dev_ams_drying_temperature = 65,80,65,80
; filament_dev_ams_drying_time = 12,8,12,8
; filament_dev_chamber_drying_bed_temperature = 90
; filament_dev_chamber_drying_time = 12
; filament_dev_drying_cooling_temperature = 85
; filament_dev_drying_softening_temperature = 85
; filament_diameter = 1.75
; filament_enable_overhang_speed = 1
; filament_end_gcode = "; filament end gcode \n\n"
; filament_extruder_compatibility = 0
; filament_extruder_variant = "Direct Drive Standard"
; filament_flow_ratio = 0.95
; filament_flush_temp = 0
; filament_flush_temp_fast = 0
; filament_flush_volumetric_speed = 0
; filament_ids = GFB98
; filament_is_mixed = 0
; filament_is_support = 0
; filament_map = 1
; filament_map_2 = 0
; filament_map_mode = Auto For Flush
; filament_max_volumetric_speed = 8.8
; filament_metal_stickiness = None
; filament_minimal_purge_on_wipe_tower = 15
; filament_mixed_components = ""
; filament_mixed_gradient = 0
; filament_mixed_gradient_curve = ""
; filament_mixed_gradient_per_part = 0
; filament_mixed_gradient_range = ""
; filament_mixed_sublayer_ratios = ""
; filament_multi_colour = #161616
; filament_notes = 
; filament_nozzle_map = 0
; filament_overhang_1_4_speed = 0
; filament_overhang_2_4_speed = 50
; filament_overhang_3_4_speed = 30
; filament_overhang_4_4_speed = 10
; filament_overhang_totally_speed = 10
; filament_pre_cooling_temperature = 0
; filament_pre_cooling_temperature_nc = 0
; filament_preheat_temperature_delta = 0
; filament_prime_volume = 45
; filament_prime_volume_nc = 60
; filament_printable = 3
; filament_ramming_travel_time = 0
; filament_ramming_travel_time_nc = 0
; filament_ramming_volumetric_speed = -1
; filament_ramming_volumetric_speed_nc = -1
; filament_retract_length_nc = 14
; filament_scarf_gap = 0%
; filament_scarf_height = 10%
; filament_scarf_length = 10
; filament_scarf_seam_type = none
; filament_self_index = 1
; filament_settings_id = "ASA - P1S 265C 8.8mm3s"
; filament_shrink = 100%
; filament_soluble = 0
; filament_start_gcode = "; Filament gcode\n{if activate_air_filtration[current_extruder] && support_air_filtration}\nM106 P3 S{during_print_exhaust_fan_speed_num[current_extruder]} \n{endif}"
; filament_tower_interface_pre_extrusion_dist = 10
; filament_tower_interface_pre_extrusion_length = 0
; filament_tower_interface_print_temp = -1
; filament_tower_interface_purge_volume = 20
; filament_tower_ironing_area = 4
; filament_type = ASA
; filament_velocity_adaptation_factor = 1
; filament_vendor = Generic
; filament_volume_map = 0
; filename_format = {input_filename_base}_{filament_type[0]}_{print_time}.gcode
; fill_multiline = 1
; filter_out_gap_fill = 0
; first_layer_print_sequence = 0
; first_x_layer_fan_speed = 0
; first_x_layer_part_fan_speed = 0
; flush_into_infill = 0
; flush_into_objects = 0
; flush_into_support = 1
; flush_multiplier = 1
; flush_multiplier_fast = 1.2
; flush_volumes_matrix = 0
; flush_volumes_vector = 140,140
; full_fan_speed_layer = 0
; fuzzy_skin = none
; fuzzy_skin_first_layer = 0
; fuzzy_skin_mode = displacement
; fuzzy_skin_noise_type = classic
; fuzzy_skin_octaves = 4
; fuzzy_skin_persistence = 0.5
; fuzzy_skin_point_distance = 0.8
; fuzzy_skin_scale = 1
; fuzzy_skin_thickness = 0.3
; gap_infill_speed = 250
; gcode_add_line_number = 0
; gcode_flavor = marlin
; grab_length = 0
; group_algo_with_time = 0
; has_filament_switcher = 0
; has_scarf_joint_seam = 0
; head_wrap_detect_zone = 
; hole_coef_1 = 0
; hole_coef_2 = -0.008
; hole_coef_3 = 0.23415
; hole_limit_max = 0.22
; hole_limit_min = 0.088
; host_type = octoprint
; hot_plate_temp = 100
; hot_plate_temp_initial_layer = 100
; hotend_cooling_rate = 2
; hotend_heating_rate = 2
; impact_strength_z = 4.9
; independent_support_layer_height = 1
; infill_combination = 0
; infill_direction = 45
; infill_instead_top_bottom_surfaces = 0
; infill_jerk = 9
; infill_lock_depth = 1
; infill_rotate_step = 0
; infill_shift_step = 0.4
; infill_wall_overlap = 15%
; inherits_group = ;"Generic ASA";
; initial_layer_acceleration = 500
; initial_layer_flow_ratio = 1
; initial_layer_infill_speed = 105
; initial_layer_jerk = 9
; initial_layer_line_width = 0.56
; initial_layer_print_height = 0.25
; initial_layer_speed = 30
; initial_layer_travel_acceleration = 6000
; inner_wall_acceleration = 0
; inner_wall_jerk = 9
; inner_wall_line_width = 0.45
; inner_wall_speed = 300
; interface_shells = 0
; interlocking_beam = 0
; interlocking_beam_layer_count = 2
; interlocking_beam_width = 0.8
; interlocking_boundary_avoidance = 2
; interlocking_depth = 2
; interlocking_orientation = 22.5
; internal_bridge_support_thickness = 0.8
; internal_solid_infill_line_width = 0.42
; internal_solid_infill_pattern = zig-zag
; internal_solid_infill_speed = 250
; ironing_direction = 45
; ironing_fan_speed = -1
; ironing_flow = 10%
; ironing_inset = 0.21
; ironing_pattern = zig-zag
; ironing_spacing = 0.15
; ironing_speed = 30
; ironing_type = no ironing
; is_infill_first = 0
; layer_change_gcode = ; layer num/total_layer_count: {layer_num+1}/[total_layer_count]\n; update layer progress\nM73 L{layer_num+1}\nM991 S0 P{layer_num} ;notify layer change
; layer_height = 0.2
; line_width = 0.45
; locked_skeleton_infill_pattern = zigzag
; locked_skin_infill_pattern = crosszag
; long_retractions_when_cut = 0
; long_retractions_when_ec = 0
; machine_bed_mass_Y = 0
; machine_end_gcode = ;===== date: 20230428 =====================\nM400 ; wait for buffer to clear\nG92 E0 ; zero the extruder\nG1 E-0.8 F1800 ; retract\nG1 Z{max_layer_z + 0.5} F900 ; lower z a little\nG1 X65 Y245 F12000 ; move to safe pos \nG1 Y265 F3000\n\nG1 X65 Y245 F12000\nG1 Y265 F3000\nM140 S0 ; turn off bed\nM106 S0 ; turn off fan\nM106 P2 S0 ; turn off remote part cooling fan\nM106 P3 S0 ; turn off chamber cooling fan\n\nG1 X100 F12000 ; wipe\n; pull back filament to AMS\nM620 S255\nG1 X20 Y50 F12000\nG1 Y-3\nT255\nG1 X65 F12000\nG1 Y265\nG1 X100 F12000 ; wipe\nM621 S255\nM104 S0 ; turn off hotend\n\nM622.1 S1 ; for prev firware, default turned on\nM1002 judge_flag timelapse_record_flag\nM622 J1\n    M400 ; wait all motion done\n    M991 S0 P-1 ;end smooth timelapse at safe pos\n    M400 S3 ;wait for last picture to be taken\nM623; end of \"timelapse_record_flag\"\n\nM400 ; wait all motion done\nM17 S\nM17 Z0.4 ; lower z motor current to reduce impact if there is something in the bottom\n{if (max_layer_z + 100.0) < 250}\n    G1 Z{max_layer_z + 100.0} F600\n    G1 Z{max_layer_z +98.0}\n{else}\n    G1 Z250 F600\n    G1 Z248\n{endif}\nM400 P100\nM17 R ; restore z current\n\nM220 S100  ; Reset feedrate magnitude\nM201.2 K1.0 ; Reset acc magnitude\nM73.2   R1.0 ;Reset left time magnitude\nM1002 set_gcode_claim_speed_level : 0\n\nM17 X0.8 Y0.8 Z0.5 ; lower motor current to 45% power\n
; machine_hotend_change_time = 0
; machine_load_filament_time = 29
; machine_max_acceleration_e = 5000,5000
; machine_max_acceleration_extruding = 20000,20000
; machine_max_acceleration_retracting = 5000,5000
; machine_max_acceleration_travel = 9000,9000
; machine_max_acceleration_x = 20000,20000
; machine_max_acceleration_y = 20000,20000
; machine_max_acceleration_z = 500,500
; machine_max_force_Y = 0
; machine_max_jerk_e = 2.5,2.5
; machine_max_jerk_x = 9,9
; machine_max_jerk_y = 9,9
; machine_max_jerk_z = 3,3
; machine_max_printed_mass = 0
; machine_max_speed_e = 30,30
; machine_max_speed_x = 500,500
; machine_max_speed_y = 500,500
; machine_max_speed_z = 20,20
; machine_min_extruding_rate = 0
; machine_min_travel_rate = 0
; machine_pause_gcode = M400 U1
; machine_prepare_compensation_time = 260
; machine_start_gcode = ;===== machine: P1S-0.4 ========================\n;===== date: 20251031 =====================\n;===== turn on the HB fan & MC board fan =================\nM104 S75 ;set extruder temp to turn on the HB fan and prevent filament oozing from nozzle\nM710 A1 S255 ;turn on MC fan by default(P1S)\n;===== reset machine status =================\nM290 X40 Y40 Z2.6666666\nG91\nM17 Z0.4 ; lower the z-motor current\nG380 S2 Z30 F300 ; G380 is same as G38; lower the hotbed , to prevent the nozzle is below the hotbed\nG380 S2 Z-25 F300 ;\nG1 Z5 F300;\nG90\nM17 X1.2 Y1.2 Z0.75 ; reset motor current to default\nM960 S5 P1 ; turn on logo lamp\nG90\nM220 S100 ;Reset Feedrate\nM221 S100 ;Reset Flowrate\nM73.2   R1.0 ;Reset left time magnitude\nM1002 set_gcode_claim_speed_level : 5\nM221 X0 Y0 Z0 ; turn off soft endstop to prevent protential logic problem\nG29.1 Z{+0.0} ; clear z-trim value first\nM204 S10000 ; init ACC set to 10m/s^2\n\n;===== heatbed preheat ====================\nM1002 gcode_claim_action:54\nM140 S[bed_temperature_initial_layer_single] ;set bed temp\nM190 S[bed_temperature_initial_layer_single] ;wait for bed temp\n\n\n\n;=============turn on fans to prevent PLA jamming=================\n{if filament_type[initial_extruder]==\"PLA\"}\n    {if (bed_temperature[initial_extruder] >45)||(bed_temperature_initial_layer[initial_extruder] >45)}\n    M106 P3 S180\n    {endif};Prevent PLA from jamming\n{endif}\nM106 P2 S100 ; turn on big fan ,to cool down toolhead\n\n;===== prepare print temperature and material ==========\nM104 S[nozzle_temperature_initial_layer] ;set extruder temp\nG91\nG0 Z10 F1200\nG90\nG28 X\nM975 S1 ; turn on\nG1 X60 F12000\nG1 Y245\nG1 Y265 F3000\nM620 M\nM620 S[initial_extruder]A   ; switch material if AMS exist\n    M109 S[nozzle_temperature_initial_layer]\n    G1 X120 F12000\n\n    G1 X20 Y50 F12000\n    G1 Y-3\n    T[initial_extruder]\n    G1 X54 F12000\n    G1 Y265\n    M400\nM621 S[initial_extruder]A\nM620.1 E F{flush_volumetric_speeds[initial_no_support_extruder]/2.4053*60} T{flush_temperatures[initial_no_support_extruder]}\n\n\nM412 S1 ; ===turn on filament runout detection===\n\nM109 S250 ;set nozzle to common flush temp\nM106 P1 S0\nG92 E0\nG1 E50 F200\nM400\nM104 S[nozzle_temperature_initial_layer]\nG92 E0\nG1 E50 F200\nM400\nM106 P1 S255\nG92 E0\nG1 E5 F300\nM109 S{nozzle_temperature_initial_layer[initial_extruder]-20} ; drop nozzle temp, make filament shink a bit\nG92 E0\nG1 E-0.5 F300\n\nG1 X70 F9000\nG1 X76 F15000\nG1 X65 F15000\nG1 X76 F15000\nG1 X65 F15000; shake to put down garbage\nG1 X80 F6000\nG1 X95 F15000\nG1 X80 F15000\nG1 X165 F15000; wipe and shake\nM400\nM106 P1 S0\n;===== prepare print temperature and material end =====\n\n\n;===== wipe nozzle ===============================\nM1002 gcode_claim_action : 14\nM975 S1\nM106 S255\nG1 X65 Y230 F18000\nG1 Y264 F6000\nM109 S{nozzle_temperature_initial_layer[initial_extruder]-20}\nG1 X100 F18000 ; first wipe mouth\n\nG0 X135 Y253 F20000  ; move to exposed steel surface edge\nG28 Z P0 T300; home z with low precision,permit 300deg temperature\nG29.2 S0 ; turn off ABL\nG0 Z5 F20000\n\nG1 X60 Y265\nG92 E0\nG1 E-0.5 F300 ; retrack more\nG1 X100 F5000; second wipe mouth\nG1 X70 F15000\nG1 X100 F5000\nG1 X70 F15000\nG1 X100 F5000\nG1 X70 F15000\nG1 X100 F5000\nG1 X70 F15000\nG1 X90 F5000\nG0 X128 Y261 Z-1.5 F20000  ; move to exposed steel surface and stop the nozzle\nM104 S140 ; set temp down to heatbed acceptable\nM106 S255 ; turn on fan (G28 has turn off fan)\n\nM221 S; push soft endstop status\nM221 Z0 ;turn off Z axis endstop\nG0 Z0.5 F20000\nG0 X125 Y259.5 Z-1.01\nG0 X131 F211\nG0 X124\nG0 Z0.5 F20000\nG0 X125 Y262.5\nG0 Z-1.01\nG0 X131 F211\nG0 X124\nG0 Z0.5 F20000\nG0 X125 Y260.0\nG0 Z-1.01\nG0 X131 F211\nG0 X124\nG0 Z0.5 F20000\nG0 X125 Y262.0\nG0 Z-1.01\nG0 X131 F211\nG0 X124\nG0 Z0.5 F20000\nG0 X125 Y260.5\nG0 Z-1.01\nG0 X131 F211\nG0 X124\nG0 Z0.5 F20000\nG0 X125 Y261.5\nG0 Z-1.01\nG0 X131 F211\nG0 X124\nG0 Z0.5 F20000\nG0 X125 Y261.0\nG0 Z-1.01\nG0 X131 F211\nG0 X124\nG0 X128\nG2 I0.5 J0 F300\nG2 I0.5 J0 F300\nG2 I0.5 J0 F300\nG2 I0.5 J0 F300\n\nM109 S140 ; wait nozzle temp down to heatbed acceptable\nG2 I0.5 J0 F3000\nG2 I0.5 J0 F3000\nG2 I0.5 J0 F3000\nG2 I0.5 J0 F3000\n\nM221 R; pop softend status\nG1 Z10 F1200\nM400\nG1 Z10\nG1 F30000\nG1 X230 Y15\nG29.2 S1 ; turn on ABL\n;G28 ; home again after hard wipe mouth\nM106 S0 ; turn off fan , too noisy\n;===== wipe nozzle end ================================\n\n\n;===== bed leveling ==================================\nM1002 judge_flag g29_before_print_flag\nM622 J1\n\n    M1002 gcode_claim_action : 1\n    G29 A X{first_layer_print_min[0]} Y{first_layer_print_min[1]} I{first_layer_print_size[0]} J{first_layer_print_size[1]}\n    M400\n    M500 ; save cali data\n\nM623\n;===== bed leveling end ================================\n\n;===== home after wipe mouth============================\nM1002 judge_flag g29_before_print_flag\nM622 J0\n\n    M1002 gcode_claim_action : 13\n    G28\n\nM623\n;===== home after wipe mouth end =======================\n\nM975 S1 ; turn on vibration supression\n\n\n;=============turn on fans to prevent PLA jamming=================\n{if filament_type[initial_extruder]==\"PLA\"}\n    {if (bed_temperature[initial_extruder] >45)||(bed_temperature_initial_layer[initial_extruder] >45)}\n    M106 P3 S180\n    {endif};Prevent PLA from jamming\n{endif}\nM106 P2 S100 ; turn on big fan ,to cool down toolhead\n\n\nM104 S{nozzle_temperature_initial_layer[initial_extruder]} ; set extrude temp earlier, to reduce wait time\n\n;===== mech mode fast check============================\nG1 X128 Y128 Z10 F20000\nM400 P200\nM970.3 Q1 A7 B30 C80  H15 K0\nM974 Q1 S2 P0\n\nG1 X128 Y128 Z10 F20000\nM400 P200\nM970.3 Q0 A7 B30 C90 Q0 H15 K0\nM974 Q0 S2 P0\n\nM975 S1\nG1 F30000\nG1 X230 Y15\nG28 X ; re-home XY\n;===== fmech mode fast check============================\n\n\n;===== nozzle load line ===============================\nM975 S1\nG90\nM83\nT1000\nG1 X18.0 Y1.0 Z0.8 F18000;Move to start position\nM109 S{nozzle_temperature_initial_layer[initial_extruder]}\nG1 Z0.2\nG0 E2 F300\nG0 X240 E15 F{outer_wall_volumetric_speed/(0.3*0.5)     * 60}\nG0 Y11 E0.700 F{outer_wall_volumetric_speed/(0.3*0.5)/ 4 * 60}\nG0 X239.5\nG0 E0.2\nG0 Y1.5 E0.700\nG0 X18 E15 F{outer_wall_volumetric_speed/(0.3*0.5)     * 60}\nM400\n\n;===== for Textured PEI Plate , lower the nozzle as the nozzle was touching topmost of the texture when homing ==\n;curr_bed_type={curr_bed_type}\n{if curr_bed_type==\"Textured PEI Plate\"}\nG29.1 Z{-0.04} ; for Textured PEI Plate\n{endif}\n;========turn off light and wait extrude temperature =============\nM1002 gcode_claim_action : 0\nM106 S0 ; turn off fan\nM106 P2 S0 ; turn off big fan\nM106 P3 S0 ; turn off chamber fan\n\nM975 S1 ; turn on mech mode supression\n
; machine_switch_extruder_time = 0
; machine_unload_filament_time = 28
; master_extruder_id = 1
; max_bridge_length = 0
; max_layer_height = 0.28
; max_travel_detour_distance = 0
; min_bead_width = 85%
; min_feature_size = 25%
; min_layer_height = 0.08
; minimum_sparse_infill_area = 15
; mmu_segmented_region_interlocking_depth = 0
; mmu_segmented_region_max_width = 0
; monotonic_travel_into_wall = 0%
; no_slow_down_for_cooling_on_outwalls = 0
; nozzle_diameter = 0.4
; nozzle_flush_dataset = 0
; nozzle_height = 4.2
; nozzle_temperature = 265
; nozzle_temperature_initial_layer = 265
; nozzle_temperature_range_high = 280
; nozzle_temperature_range_low = 240
; nozzle_type = stainless_steel
; nozzle_volume = 107
; nozzle_volume_type = Standard
; only_one_wall_first_layer = 0
; ooze_prevention = 0
; other_layers_print_sequence = 0
; other_layers_print_sequence_nums = 0
; outer_wall_acceleration = 5000
; outer_wall_jerk = 9
; outer_wall_line_width = 0.42
; outer_wall_speed = 116.686
; overhang_1_4_speed = 0
; overhang_2_4_speed = 50
; overhang_3_4_speed = 30
; overhang_4_4_speed = 10
; overhang_fan_speed = 80
; overhang_fan_threshold = 25%
; overhang_threshold_participating_cooling = 95%
; overhang_totally_speed = 10
; override_filament_scarf_seam_setting = 0
; override_process_overhang_speed = 0
; physical_extruder_map = 0
; post_process = 
; pre_start_fan_time = 0
; precise_outer_wall = 0
; precise_z_height = 0
; pressure_advance = 0.02
; prime_tower_brim_width = 3
; prime_tower_enable_framework = 0
; prime_tower_extra_rib_length = 0
; prime_tower_fillet_wall = 1
; prime_tower_flat_ironing = 0
; prime_tower_infill_gap = 150%
; prime_tower_lift_height = -1
; prime_tower_lift_speed = 90
; prime_tower_max_speed = 90
; prime_tower_rib_wall = 1
; prime_tower_rib_width = 8
; prime_tower_skip_points = 1
; prime_tower_width = 35
; prime_volume_mode = Default
; print_compatible_printers = "Bambu Lab X1 Carbon 0.4 nozzle";"Bambu Lab X1 0.4 nozzle";"Bambu Lab P1S 0.4 nozzle";"Bambu Lab X1E 0.4 nozzle"
; print_extruder_id = 1
; print_extruder_variant = "Direct Drive Standard"
; print_flow_ratio = 1
; print_in_clockwise = 0
; print_sequence = by layer
; print_settings_id = 0.20mm Strength @BBL X1C
; printable_area = 0x0,256x0,256x256,0x256
; printable_height = 250
; printer_extruder_id = 1
; printer_extruder_variant = "Direct Drive Standard"
; printer_model = Bambu Lab P1S
; printer_notes = 
; printer_settings_id = Bambu Lab P1S 0.4 nozzle
; printer_structure = corexy
; printer_technology = FFF
; printer_variant = 0.4
; printhost_authorization_type = key
; printhost_ssl_ignore_revoke = 0
; printing_by_object_gcode = 
; process_notes = 
; raft_contact_distance = 0.1
; raft_expansion = 1.5
; raft_first_layer_density = 90%
; raft_first_layer_expansion = -1
; raft_layers = 0
; reduce_crossing_wall = 0
; reduce_fan_stop_start_freq = 1
; reduce_infill_retraction_mode = Auto
; required_nozzle_HRC = 3
; resolution = 0.012
; retract_before_wipe = 0%
; retract_length_toolchange = 2
; retract_lift_above = 0
; retract_lift_below = 249
; retract_restart_extra = 0
; retract_restart_extra_toolchange = 0
; retract_when_changing_layer = 1
; retraction_distances_when_cut = 18
; retraction_distances_when_ec = 0
; retraction_length = 0.8
; retraction_minimum_travel = 1
; retraction_speed = 30
; role_base_wipe_speed = 1
; scan_first_layer = 0
; scarf_angle_threshold = 155
; seam_gap = 15%
; seam_placement_away_from_overhangs = 0
; seam_position = aligned
; seam_slope_conditional = 1
; seam_slope_entire_loop = 0
; seam_slope_gap = 0
; seam_slope_inner_walls = 1
; seam_slope_min_length = 10
; seam_slope_start_height = 10%
; seam_slope_steps = 10
; seam_slope_type = none
; silent_mode = 0
; single_extruder_multi_material = 1
; skeleton_infill_density = 25%
; skeleton_infill_line_width = 0.45
; skin_infill_density = 25%
; skin_infill_depth = 2
; skin_infill_line_width = 0.45
; skirt_distance = 2
; skirt_height = 1
; skirt_loops = 0
; skirt_per_object = 1
; slice_closing_radius = 0.049
; slicing_mode = regular
; slow_down_for_layer_cooling = 1
; slow_down_layer_time = 3
; slow_down_min_speed = 20
; slowdown_end_acc = 100000
; slowdown_end_height = 400
; slowdown_end_speed = 1000
; slowdown_start_acc = 100000
; slowdown_start_height = 0
; slowdown_start_speed = 1000
; small_perimeter_speed = 50%
; small_perimeter_threshold = 0
; smooth_coefficient = 150
; smooth_speed_discontinuity_area = 1
; solid_infill_filament = 0
; sparse_infill_acceleration = 100%
; sparse_infill_anchor = 400%
; sparse_infill_anchor_max = 20
; sparse_infill_density = 25%
; sparse_infill_filament = 0
; sparse_infill_lattice_angle_1 = -45
; sparse_infill_lattice_angle_2 = 45
; sparse_infill_line_width = 0.45
; sparse_infill_pattern = grid
; sparse_infill_speed = 270
; spiral_mode = 0
; spiral_mode_max_xy_smoothing = 200%
; spiral_mode_smooth = 0
; standby_temperature_delta = -5
; start_end_points = 30x-3,54x245
; supertack_plate_temp = 0
; supertack_plate_temp_initial_layer = 0
; support_air_filtration = 0
; support_angle = 0
; support_base_pattern = default
; support_base_pattern_spacing = 2.5
; support_bottom_interface_spacing = 0.5
; support_bottom_z_distance = 0.2
; support_chamber_temp_control = 0
; support_cooling_filter = 0
; support_critical_regions_only = 0
; support_expansion = 0
; support_fast_purge_mode = 0
; support_filament = 0
; support_interface_bottom_layers = 2
; support_interface_filament = 0
; support_interface_loop_pattern = 0
; support_interface_not_for_body = 1
; support_interface_pattern = auto
; support_interface_spacing = 0.5
; support_interface_speed = 80
; support_interface_top_layers = 2
; support_ironing_direction = 0
; support_ironing_flow = 10%
; support_ironing_inset = 0
; support_ironing_pattern = zig-zag
; support_ironing_spacing = 0.15
; support_ironing_speed = 30
; support_line_width = 0.42
; support_object_first_layer_gap = 0.2
; support_object_skip_flush = 0
; support_object_xy_distance = 0.35
; support_on_build_plate_only = 0
; support_remove_small_overhang = 1
; support_speed = 150
; support_style = default
; support_threshold_angle = 30
; support_top_z_distance = 0.2
; support_type = tree(auto)
; symmetric_infill_y_axis = 0
; temperature_vitrification = 100
; template_custom_gcode = 
; textured_plate_temp = 100
; textured_plate_temp_initial_layer = 100
; thick_bridges = 0
; thumbnail_size = 50x50
; time_lapse_gcode = ;========Date 20250206========\n; SKIPPABLE_START\n; SKIPTYPE: timelapse\nM622.1 S1 ; for prev firmware, default turned on\nM1002 judge_flag timelapse_record_flag\nM622 J1\n{if timelapse_type == 0} ; timelapse without wipe tower\nM971 S11 C10 O0\nM1004 S5 P1  ; external shutter\n{elsif timelapse_type == 1} ; timelapse with wipe tower\nG92 E0\nG1 X65 Y245 F20000 ; move to safe pos\nG17\nG2 Z{layer_z} I0.86 J0.86 P1 F20000\nG1 Y265 F3000\nM400\nM1004 S5 P1  ; external shutter\nM400 P300\nM971 S11 C11 O0\nG92 E0\nG1 X100 F5000\nG1 Y255 F20000\n{endif}\nM623\n; SKIPPABLE_END
; timelapse_type = 0
; top_area_threshold = 200%
; top_color_penetration_layers = 5
; top_one_wall_type = all top
; top_shell_layers = 5
; top_shell_thickness = 1
; top_solid_infill_flow_ratio = 1
; top_surface_acceleration = 2000
; top_surface_density = 100%
; top_surface_jerk = 9
; top_surface_line_width = 0.42
; top_surface_pattern = monotonicline
; top_surface_speed = 200
; top_z_overrides_xy_distance = 0
; travel_acceleration = 10000
; travel_jerk = 9
; travel_short_distance_acceleration = 250
; travel_speed = 500
; travel_speed_z = 0
; tree_support_branch_angle = 45
; tree_support_branch_diameter = 2
; tree_support_branch_diameter_angle = 5
; tree_support_branch_distance = 5
; tree_support_wall_count = -1
; upward_compatible_machine = "Bambu Lab P1P 0.4 nozzle";"Bambu Lab X1 0.4 nozzle";"Bambu Lab X1 Carbon 0.4 nozzle";"Bambu Lab X1E 0.4 nozzle";"Bambu Lab A1 0.4 nozzle";"Bambu Lab H2D 0.4 nozzle";"Bambu Lab H2D Pro 0.4 nozzle";"Bambu Lab H2S 0.4 nozzle";"Bambu Lab P2S 0.4 nozzle";"Bambu Lab H2C 0.4 nozzle";"Bambu Lab X2D 0.4 nozzle";"Bambu Lab A2L 0.4 nozzle"
; use_firmware_retraction = 0
; use_relative_e_distances = 1
; vertical_shell_speed = 80%
; volumetric_speed_coefficients = "0 0 0 0 0 0"
; wall_distribution_count = 1
; wall_filament = 0
; wall_generator = classic
; wall_loops = 3
; wall_sequence = inner wall/outer wall
; wall_transition_angle = 10
; wall_transition_filter_deviation = 25%
; wall_transition_length = 100%
; wipe = 1
; wipe_distance = 2
; wipe_speed = 80%
; wipe_tower_no_sparse_layers = 0
; wipe_tower_rotation_angle = 0
; wipe_tower_x = 165
; wipe_tower_y = 216.972
; wrapping_detection_gcode = 
; wrapping_detection_layers = 20
; wrapping_exclude_area = 
; xy_contour_compensation = 0
; xy_hole_compensation = 0
; z_direction_outwall_speed_continuous = 0
; z_hop = 0.4
; z_hop_types = Auto Lift
; CONFIG_BLOCK_END

; EXECUTABLE_BLOCK_START
M73 P0 R10
M201 X20000 Y20000 Z500 E5000
M203 X500 Y500 Z20 E30
M204 P20000 R5000 T20000
M205 X9.00 Y9.00 Z3.00 E2.50
M106 S0
M106 P2 S0
; FEATURE: Custom
;===== machine: P1S-0.4 ========================
;===== date: 20251031 =====================
;===== turn on the HB fan & MC board fan =================
M104 S75 ;set extruder temp to turn on the HB fan and prevent filament oozing from nozzle
M710 A1 S255 ;turn on MC fan by default(P1S)
;===== reset machine status =================
M290 X40 Y40 Z2.6666666
G91
M17 Z0.4 ; lower the z-motor current
G380 S2 Z30 F300 ; G380 is same as G38; lower the hotbed , to prevent the nozzle is below the hotbed
G380 S2 Z-25 F300 ;
G1 Z5 F300;
G90
M17 X1.2 Y1.2 Z0.75 ; reset motor current to default
M960 S5 P1 ; turn on logo lamp
G90
M220 S100 ;Reset Feedrate
M221 S100 ;Reset Flowrate
M73.2   R1.0 ;Reset left time magnitude
M1002 set_gcode_claim_speed_level : 5
M221 X0 Y0 Z0 ; turn off soft endstop to prevent protential logic problem
G29.1 Z0 ; clear z-trim value first
M204 S10000 ; init ACC set to 10m/s^2

;===== heatbed preheat ====================
M1002 gcode_claim_action:54
M140 S100 ;set bed temp
M190 S100 ;wait for bed temp



;=============turn on fans to prevent PLA jamming=================

M106 P2 S100 ; turn on big fan ,to cool down toolhead

;===== prepare print temperature and material ==========
M104 S265 ;set extruder temp
G91
G0 Z10 F1200
G90
G28 X
M975 S1 ; turn on
G1 X60 F12000
G1 Y245
G1 Y265 F3000
M620 M
M620 S0A   ; switch material if AMS exist
    M109 S265
    G1 X120 F12000

    G1 X20 Y50 F12000
    G1 Y-3
    T0
    G1 X54 F12000
    G1 Y265
    M400
M621 S0A
M620.1 E F219.515 T280


M412 S1 ; ===turn on filament runout detection===

M109 S250 ;set nozzle to common flush temp
M106 P1 S0
G92 E0
M73 P5 R9
G1 E50 F200
M400
M104 S265
G92 E0
M73 P46 R5
G1 E50 F200
M400
M106 P1 S255
G92 E0
M73 P47 R5
G1 E5 F300
M109 S245 ; drop nozzle temp, make filament shink a bit
G92 E0
M73 P49 R5
G1 E-0.5 F300

M73 P51 R5
G1 X70 F9000
M73 P52 R5
G1 X76 F15000
G1 X65 F15000
G1 X76 F15000
G1 X65 F15000; shake to put down garbage
G1 X80 F6000
G1 X95 F15000
G1 X80 F15000
G1 X165 F15000; wipe and shake
M400
M106 P1 S0
;===== prepare print temperature and material end =====


;===== wipe nozzle ===============================
M1002 gcode_claim_action : 14
M975 S1
M106 S255
G1 X65 Y230 F18000
G1 Y264 F6000
M109 S245
G1 X100 F18000 ; first wipe mouth

G0 X135 Y253 F20000  ; move to exposed steel surface edge
G28 Z P0 T300; home z with low precision,permit 300deg temperature
G29.2 S0 ; turn off ABL
G0 Z5 F20000

M73 P52 R4
G1 X60 Y265
G92 E0
G1 E-0.5 F300 ; retrack more
G1 X100 F5000; second wipe mouth
G1 X70 F15000
G1 X100 F5000
G1 X70 F15000
G1 X100 F5000
G1 X70 F15000
G1 X100 F5000
G1 X70 F15000
G1 X90 F5000
G0 X128 Y261 Z-1.5 F20000  ; move to exposed steel surface and stop the nozzle
M104 S140 ; set temp down to heatbed acceptable
M106 S255 ; turn on fan (G28 has turn off fan)

M221 S; push soft endstop status
M221 Z0 ;turn off Z axis endstop
G0 Z0.5 F20000
G0 X125 Y259.5 Z-1.01
G0 X131 F211
G0 X124
G0 Z0.5 F20000
G0 X125 Y262.5
G0 Z-1.01
G0 X131 F211
G0 X124
G0 Z0.5 F20000
G0 X125 Y260.0
G0 Z-1.01
G0 X131 F211
G0 X124
G0 Z0.5 F20000
G0 X125 Y262.0
G0 Z-1.01
G0 X131 F211
G0 X124
G0 Z0.5 F20000
G0 X125 Y260.5
G0 Z-1.01
G0 X131 F211
G0 X124
G0 Z0.5 F20000
G0 X125 Y261.5
G0 Z-1.01
G0 X131 F211
G0 X124
G0 Z0.5 F20000
G0 X125 Y261.0
G0 Z-1.01
G0 X131 F211
G0 X124
G0 X128
G2 I0.5 J0 F300
G2 I0.5 J0 F300
G2 I0.5 J0 F300
G2 I0.5 J0 F300

M109 S140 ; wait nozzle temp down to heatbed acceptable
G2 I0.5 J0 F3000
M73 P53 R4
G2 I0.5 J0 F3000
G2 I0.5 J0 F3000
G2 I0.5 J0 F3000

M221 R; pop softend status
G1 Z10 F1200
M400
G1 Z10
G1 F30000
G1 X230 Y15
G29.2 S1 ; turn on ABL
;G28 ; home again after hard wipe mouth
M106 S0 ; turn off fan , too noisy
;===== wipe nozzle end ================================


;===== bed leveling ==================================
M1002 judge_flag g29_before_print_flag
M622 J1

    M1002 gcode_claim_action : 1
    G29 A X94.2649 Y95.5068 I5.00001 J5.00001
    M400
    M500 ; save cali data

M623
;===== bed leveling end ================================

;===== home after wipe mouth============================
M1002 judge_flag g29_before_print_flag
M622 J0

    M1002 gcode_claim_action : 13
    G28

M623
;===== home after wipe mouth end =======================

M975 S1 ; turn on vibration supression


;=============turn on fans to prevent PLA jamming=================

M106 P2 S100 ; turn on big fan ,to cool down toolhead


M104 S265 ; set extrude temp earlier, to reduce wait time

;===== mech mode fast check============================
G1 X128 Y128 Z10 F20000
M400 P200
M970.3 Q1 A7 B30 C80  H15 K0
M974 Q1 S2 P0

G1 X128 Y128 Z10 F20000
M400 P200
M970.3 Q0 A7 B30 C90 Q0 H15 K0
M974 Q0 S2 P0

M975 S1
G1 F30000
M73 P54 R4
G1 X230 Y15
G28 X ; re-home XY
;===== fmech mode fast check============================


;===== nozzle load line ===============================
M975 S1
G90
M83
T1000
G1 X18.0 Y1.0 Z0.8 F18000;Move to start position
M109 S265
G1 Z0.2
G0 E2 F300
G0 X240 E15 F3520
G0 Y11 E0.700 F880
G0 X239.5
G0 E0.2
G0 Y1.5 E0.700
G0 X18 E15 F3520
M400

;===== for Textured PEI Plate , lower the nozzle as the nozzle was touching topmost of the texture when homing ==
;curr_bed_type=Textured PEI Plate

G29.1 Z-0.04 ; for Textured PEI Plate

;========turn off light and wait extrude temperature =============
M1002 gcode_claim_action : 0
M106 S0 ; turn off fan
M106 P2 S0 ; turn off big fan
M106 P3 S0 ; turn off chamber fan

M975 S1 ; turn on mech mode supression
; MACHINE_START_GCODE_END
; Filament gcode
;VT0 H-1
G90
G21
M83 ; use relative distances for extrusion
M981 S1 P20000 ;open spaghetti detector
; CHANGE_LAYER
; Z_HEIGHT: 0.25
; LAYER_HEIGHT: 0.25
G1 E-.8 F1800
; layer num/total_layer_count: 1/4
; update layer progress
M73 L1
M991 S0 P0 ;notify layer change
M106 S0
M106 P2 S0
; CUSTOM_GCODE
G1 E.8
; start pressure advance pattern for layer
G1 E-.8
M204 S6000
G1 X94.265 Y102.507 F30000
G1 E.8 F1800
G1 Z.25 F30000
M400
 M900 K0; Override pressure advance value
M73 P55 R4
G1 E-.8 F1800
G1 X94.265 Y102.507 F30000
G1 E.8 F1800

M204 S5000
G1 X94.265 Y144.933 E2.12121

G1 X156.735 Y144.933 E3.12336

G1 X156.735 Y102.507 E2.12121

M73 P56 R4
G1 X94.265 Y102.507 E3.12336
G1 E-.8
M204 S6000
G1 X94.771 Y103.013 F30000
G1 E.8 F1800

M204 S5000
G1 X94.771 Y144.427 E2.07058

G1 X156.229 Y144.427 E3.07272

G1 X156.229 Y103.013 E2.07058

G1 X94.771 Y103.013 E3.07272
G1 E-.8
M204 S6000
M73 P57 R4
G1 X95.278 Y103.519 F30000
G1 E.8 F1800

M204 S5000
G1 X95.278 Y143.921 E2.01995

G1 X155.722 Y143.921 E3.02209

G1 X155.722 Y103.519 E2.01995

G1 X95.278 Y103.519 E3.02209
M73 P58 R4
G1 E-.8
M204 S6000
G1 X94.265 Y145.44 F30000
G1 E.8 F1800

M204 S5000
G1 X94.265 Y158.946 E.67528

G1 X136.926 Y158.946 E2.13296

G1 X136.926 Y145.44 E.67528

G1 X94.265 Y145.44 E2.13296
G1 E-.8
M204 S6000
G1 X94.771 Y145.946 F30000
G1 E.8 F1800

M204 S5000
G1 X94.771 Y158.44 E.62465

G1 X136.42 Y158.44 E2.08233

G1 X136.42 Y145.946 E.62465

G1 X94.771 Y145.946 E2.08233
G1 E-.8
M204 S6000
G1 X95.278 Y146.452 F30000
G1 E.8 F1800

M204 S5000
G1 X95.278 Y157.933 E.57402

M73 P59 R4
G1 X135.914 Y157.933 E2.0317

G1 X135.914 Y146.452 E.57402

G1 X95.278 Y146.452 E2.0317
G1 E-.8
M204 S6000
G1 X95.651 Y146.826 F30000
M73 P60 R4
G1 E.8 F1800
G1 E-.8
G1 X96.367 Y146.826 F30000
G1 E.8 F1800

M204 S5000
G1 X95.651 Y147.542 E.05063
G1 E-.8
M204 S6000
G1 X95.651 Y148.258 F30000
G1 E.8 F1800

M204 S5000
G1 X97.083 Y146.826 E.10126
G1 E-.8
M204 S6000
G1 X97.799 Y146.826 F30000
G1 E.8 F1800

M204 S5000
M73 P61 R4
G1 X95.651 Y148.974 E.1519
G1 E-.8
M204 S6000
G1 X95.651 Y149.69 F30000
G1 E.8 F1800

M204 S5000
G1 X98.515 Y146.826 E.20253
G1 E-.8
M204 S6000
M73 P61 R3
G1 X99.231 Y146.826 F30000
M73 P62 R3
G1 E.8 F1800

M204 S5000
G1 X95.651 Y150.406 E.25316
G1 E-.8
M204 S6000
G1 X95.651 Y151.122 F30000
G1 E.8 F1800

M204 S5000
G1 X99.947 Y146.826 E.30379
M73 P63 R3
G1 E-.8
M204 S6000
G1 X100.663 Y146.826 F30000
G1 E.8 F1800

M204 S5000
G1 X95.651 Y151.838 E.35443
G1 E-.8
M204 S6000
G1 X95.651 Y152.554 F30000
G1 E.8 F1800

M204 S5000
G1 X101.38 Y146.826 E.40506
G1 E-.8
M204 S6000
M73 P64 R3
G1 X102.096 Y146.826 F30000
G1 E.8 F1800

M204 S5000
G1 X95.651 Y153.27 E.45569
G1 E-.8
M204 S6000
G1 X95.651 Y153.986 F30000
G1 E.8 F1800

M204 S5000
G1 X102.812 Y146.826 E.50632
G1 E-.8
M204 S6000
G1 X103.528 Y146.826 F30000
G1 E.8 F1800

M204 S5000
G1 X95.651 Y154.703 E.55696
G1 E-.8
M204 S6000
M73 P65 R3
G1 X95.651 Y155.419 F30000
G1 E.8 F1800

M204 S5000
G1 X104.244 Y146.826 E.60759
G1 E-.8
M204 S6000
G1 X104.96 Y146.826 F30000
G1 E.8 F1800

M204 S5000
G1 X95.651 Y156.135 E.65822
G1 E-.8
M204 S6000
G1 X95.651 Y156.851 F30000
G1 E.8 F1800

M204 S5000
G1 X105.676 Y146.826 E.70885
G1 E-.8
M204 S6000
G1 X106.392 Y146.826 F30000
G1 E.8 F1800

M204 S5000
G1 X95.658 Y157.56 E.75899
G1 E-.8
M204 S6000
G1 X96.374 Y157.56 F30000
G1 E.8 F1800

M204 S5000
G1 X107.108 Y146.826 E.75899
G1 E-.8
M204 S6000
G1 X107.824 Y146.826 F30000
G1 E.8 F1800

M204 S5000
G1 X97.09 Y157.56 E.75899
G1 E-.8
M204 S6000
G1 X97.806 Y157.56 F30000
G1 E.8 F1800

M204 S5000
G1 X108.54 Y146.826 E.75899
G1 E-.8
M204 S6000
G1 X109.257 Y146.826 F30000
G1 E.8 F1800

M204 S5000
G1 X98.522 Y157.56 E.75899
G1 E-.8
M204 S6000
G1 X99.238 Y157.56 F30000
G1 E.8 F1800

M204 S5000
G1 X109.973 Y146.826 E.75899
G1 E-.8
M204 S6000
G1 X110.689 Y146.826 F30000
G1 E.8 F1800

M204 S5000
G1 X99.954 Y157.56 E.75899
G1 E-.8
M204 S6000
G1 X100.671 Y157.56 F30000
G1 E.8 F1800

M204 S5000
G1 X111.405 Y146.826 E.75899
G1 E-.8
M204 S6000
G1 X112.121 Y146.826 F30000
G1 E.8 F1800

M204 S5000
G1 X101.387 Y157.56 E.75899
G1 E-.8
M204 S6000
G1 X102.103 Y157.56 F30000
G1 E.8 F1800

M204 S5000
G1 X112.837 Y146.826 E.75899
G1 E-.8
M204 S6000
G1 X113.553 Y146.826 F30000
G1 E.8 F1800

M204 S5000
G1 X102.819 Y157.56 E.75899
G1 E-.8
M204 S6000
G1 X103.535 Y157.56 F30000
M73 P66 R3
G1 E.8 F1800

M204 S5000
G1 X114.269 Y146.826 E.75899
G1 E-.8
M204 S6000
G1 X114.985 Y146.826 F30000
G1 E.8 F1800

M204 S5000
G1 X104.251 Y157.56 E.75899
G1 E-.8
M204 S6000
G1 X104.967 Y157.56 F30000
G1 E.8 F1800

M204 S5000
G1 X115.701 Y146.826 E.75899
G1 E-.8
M204 S6000
G1 X116.417 Y146.826 F30000
G1 E.8 F1800

M204 S5000
G1 X105.683 Y157.56 E.75899
G1 E-.8
M204 S6000
G1 X106.399 Y157.56 F30000
G1 E.8 F1800

M204 S5000
G1 X117.133 Y146.826 E.75899
G1 E-.8
M204 S6000
G1 X117.85 Y146.826 F30000
G1 E.8 F1800

M204 S5000
G1 X107.115 Y157.56 E.75899
G1 E-.8
M204 S6000
G1 X107.831 Y157.56 F30000
G1 E.8 F1800

M204 S5000
G1 X118.566 Y146.826 E.75899
G1 E-.8
M204 S6000
G1 X119.282 Y146.826 F30000
G1 E.8 F1800

M204 S5000
G1 X108.547 Y157.56 E.75899
G1 E-.8
M204 S6000
G1 X109.264 Y157.56 F30000
G1 E.8 F1800

M204 S5000
G1 X119.998 Y146.826 E.75899
G1 E-.8
M204 S6000
G1 X120.714 Y146.826 F30000
G1 E.8 F1800

M204 S5000
G1 X109.98 Y157.56 E.75899
G1 E-.8
M204 S6000
G1 X110.696 Y157.56 F30000
G1 E.8 F1800

M204 S5000
G1 X121.43 Y146.826 E.75899
G1 E-.8
M204 S6000
G1 X122.146 Y146.826 F30000
M73 P67 R3
G1 E.8 F1800

M204 S5000
G1 X111.412 Y157.56 E.75899
G1 E-.8
M204 S6000
G1 X112.128 Y157.56 F30000
G1 E.8 F1800

M204 S5000
G1 X122.862 Y146.826 E.75899
G1 E-.8
M204 S6000
G1 X123.578 Y146.826 F30000
G1 E.8 F1800

M204 S5000
G1 X112.844 Y157.56 E.75899
G1 E-.8
M204 S6000
G1 X113.56 Y157.56 F30000
G1 E.8 F1800

M204 S5000
G1 X124.294 Y146.826 E.75899
G1 E-.8
M204 S6000
G1 X125.01 Y146.826 F30000
G1 E.8 F1800

M204 S5000
G1 X114.276 Y157.56 E.75899
G1 E-.8
M204 S6000
G1 X114.992 Y157.56 F30000
G1 E.8 F1800

M204 S5000
G1 X125.727 Y146.826 E.75899
G1 E-.8
M204 S6000
G1 X126.443 Y146.826 F30000
G1 E.8 F1800

M204 S5000
G1 X115.708 Y157.56 E.75899
G1 E-.8
M204 S6000
G1 X116.424 Y157.56 F30000
G1 E.8 F1800

M204 S5000
G1 X127.159 Y146.826 E.75899
G1 E-.8
M204 S6000
G1 X127.875 Y146.826 F30000
G1 E.8 F1800

M204 S5000
G1 X117.14 Y157.56 E.75899
G1 E-.8
M204 S6000
G1 X117.857 Y157.56 F30000
G1 E.8 F1800

M204 S5000
G1 X128.591 Y146.826 E.75899
G1 E-.8
M204 S6000
G1 X129.307 Y146.826 F30000
G1 E.8 F1800

M204 S5000
G1 X118.573 Y157.56 E.75899
G1 E-.8
M204 S6000
G1 X119.289 Y157.56 F30000
M73 P68 R3
G1 E.8 F1800

M204 S5000
G1 X130.023 Y146.826 E.75899
G1 E-.8
M204 S6000
G1 X130.739 Y146.826 F30000
G1 E.8 F1800

M204 S5000
G1 X120.005 Y157.56 E.75899
G1 E-.8
M204 S6000
G1 X120.721 Y157.56 F30000
G1 E.8 F1800

M204 S5000
G1 X131.455 Y146.826 E.75899
G1 E-.8
M204 S6000
G1 X132.171 Y146.826 F30000
G1 E.8 F1800

M204 S5000
G1 X121.437 Y157.56 E.75899
G1 E-.8
M204 S6000
G1 X122.153 Y157.56 F30000
G1 E.8 F1800

M204 S5000
G1 X132.887 Y146.826 E.75899
G1 E-.8
M204 S6000
G1 X133.603 Y146.826 F30000
G1 E.8 F1800

M204 S5000
G1 X122.869 Y157.56 E.75899
G1 E-.8
M204 S6000
G1 X123.585 Y157.56 F30000
G1 E.8 F1800

M204 S5000
G1 X134.32 Y146.826 E.75899
G1 E-.8
M204 S6000
G1 X135.036 Y146.826 F30000
G1 E.8 F1800

M204 S5000
G1 X124.301 Y157.56 E.75899
G1 E-.8
M204 S6000
G1 X125.017 Y157.56 F30000
G1 E.8 F1800

M204 S5000
G1 X135.54 Y147.037 E.74404
G1 E-.8
M204 S6000
G1 X135.54 Y147.753 F30000
G1 E.8 F1800

M204 S5000
G1 X125.734 Y157.56 E.69341
G1 E-.8
M204 S6000
G1 X126.45 Y157.56 F30000
G1 E.8 F1800

M204 S5000
G1 X135.54 Y148.469 E.64277
G1 E-.8
M204 S6000
M73 P69 R3
G1 X135.54 Y149.185 F30000
G1 E.8 F1800

M204 S5000
G1 X127.166 Y157.56 E.59214
G1 E-.8
M204 S6000
G1 X127.882 Y157.56 F30000
G1 E.8 F1800

M204 S5000
G1 X135.54 Y149.901 E.54151
G1 E-.8
M204 S6000
G1 X135.54 Y150.617 F30000
G1 E.8 F1800

M204 S5000
G1 X128.598 Y157.56 E.49088
G1 E-.8
M204 S6000
G1 X129.314 Y157.56 F30000
G1 E.8 F1800

M204 S5000
G1 X135.54 Y151.334 E.44024
G1 E-.8
M204 S6000
G1 X135.54 Y152.05 F30000
G1 E.8 F1800

M204 S5000
G1 X130.03 Y157.56 E.38961
G1 E-.8
M204 S6000
G1 X130.746 Y157.56 F30000
G1 E.8 F1800

M204 S5000
G1 X135.54 Y152.766 E.33898
G1 E-.8
M204 S6000
G1 X135.54 Y153.482 F30000
G1 E.8 F1800

M204 S5000
G1 X131.462 Y157.56 E.28835
G1 E-.8
M204 S6000
G1 X132.178 Y157.56 F30000
G1 E.8 F1800

M204 S5000
G1 X135.54 Y154.198 E.23771
G1 E-.8
M204 S6000
G1 X135.54 Y154.914 F30000
G1 E.8 F1800

M204 S5000
G1 X132.894 Y157.56 E.18708
G1 E-.8
M204 S6000
G1 X133.61 Y157.56 F30000
G1 E.8 F1800

M204 S5000
G1 X135.54 Y155.63 E.13645
G1 E-.8
M204 S6000
G1 X135.54 Y156.346 F30000
M73 P70 R3
G1 E.8 F1800

M204 S5000
G1 X134.327 Y157.56 E.08582
G1 E-.8
M204 S6000
G1 X135.043 Y157.56 F30000
G1 E.8 F1800

M204 S5000
G1 X135.54 Y157.062 E.03518
M400
 M900 K0; Override pressure advance value
M204 S6000
G1 Z.45 F30000
G1 E-.8 F1800
G1 X98.224 Y103.893 F30000
G1 E.8 F1800
G1 Z.25 F30000
M400
 M900 K0; Override pressure advance value
G1 F1800
M204 S5000
G1 X118.051 Y123.72 E1.09737

G1 X98.224 Y143.547 E1.09737
M204 S6000
G1 Z.45 F30000
G1 E-.8 F1800
G1 X98.799 Y103.893 F30000
G1 E.8 F1800
G1 Z.25 F30000
G1 F1800
M204 S5000
G1 X118.626 Y123.72 E1.09737

G1 X98.799 Y143.547 E1.09737
M204 S6000
G1 Z.45 F30000
G1 E-.8 F1800
G1 X99.375 Y103.893 F30000
G1 E.8 F1800
G1 Z.25 F30000
G1 F1800
M204 S5000
G1 X119.202 Y123.72 E1.09737

G1 X99.375 Y143.547 E1.09737
M204 S6000
G1 Z.45 F30000
G1 E-.8 F1800
G1 X101.825 Y103.893 F30000
G1 E.8 F1800
G1 Z.25 F30000
M400
 M900 K0.005; Override pressure advance value
G1 F1800
M204 S5000
G1 X121.652 Y123.72 E1.09737

G1 X101.825 Y143.547 E1.09737
M204 S6000
G1 Z.45 F30000
G1 E-.8 F1800
G1 X102.401 Y103.893 F30000
G1 E.8 F1800
G1 Z.25 F30000
G1 F1800
M204 S5000
G1 X122.228 Y123.72 E1.09737

G1 X102.401 Y143.547 E1.09737
M204 S6000
G1 Z.45 F30000
G1 E-.8 F1800
G1 X102.976 Y103.893 F30000
G1 E.8 F1800
G1 Z.25 F30000
G1 F1800
M204 S5000
G1 X122.804 Y123.72 E1.09737

G1 X102.976 Y143.547 E1.09737
M204 S6000
G1 Z.45 F30000
G1 E-.8 F1800
G1 X105.426 Y103.893 F30000
G1 E.8 F1800
G1 Z.25 F30000
M400
 M900 K0.01; Override pressure advance value
G1 F1800
M204 S5000
G1 X125.254 Y123.72 E1.09737

G1 X105.426 Y143.547 E1.09737
M204 S6000
G1 Z.45 F30000
G1 E-.8 F1800
M73 P71 R3
G1 X106.002 Y103.893 F30000
G1 E.8 F1800
G1 Z.25 F30000
G1 F1800
M204 S5000
G1 X125.829 Y123.72 E1.09737

G1 X106.002 Y143.547 E1.09737
M204 S6000
G1 Z.45 F30000
G1 E-.8 F1800
G1 X106.578 Y103.893 F30000
M73 P71 R2
G1 E.8 F1800
G1 Z.25 F30000
G1 F1800
M204 S5000
G1 X126.405 Y123.72 E1.09737

G1 X106.578 Y143.547 E1.09737
M204 S6000
G1 Z.45 F30000
G1 E-.8 F1800
G1 X109.028 Y103.893 F30000
G1 E.8 F1800
G1 Z.25 F30000
M400
 M900 K0.015; Override pressure advance value
G1 F1800
M204 S5000
G1 X128.855 Y123.72 E1.09737

G1 X109.028 Y143.547 E1.09737
M204 S6000
G1 Z.45 F30000
G1 E-.8 F1800
M73 P72 R2
G1 X109.603 Y103.893 F30000
G1 E.8 F1800
G1 Z.25 F30000
G1 F1800
M204 S5000
G1 X129.431 Y123.72 E1.09737

G1 X109.603 Y143.547 E1.09737
M204 S6000
G1 Z.45 F30000
G1 E-.8 F1800
G1 X110.179 Y103.893 F30000
G1 E.8 F1800
G1 Z.25 F30000
G1 F1800
M204 S5000
G1 X130.006 Y123.72 E1.09737

G1 X110.179 Y143.547 E1.09737
M204 S6000
G1 Z.45 F30000
G1 E-.8 F1800
G1 X112.629 Y103.893 F30000
G1 E.8 F1800
G1 Z.25 F30000
M400
 M900 K0.02; Override pressure advance value
G1 F1800
M204 S5000
G1 X132.456 Y123.72 E1.09737

G1 X112.629 Y143.547 E1.09737
M204 S6000
G1 Z.45 F30000
G1 E-.8 F1800
M73 P73 R2
G1 X113.205 Y103.893 F30000
G1 E.8 F1800
G1 Z.25 F30000
G1 F1800
M204 S5000
G1 X133.032 Y123.72 E1.09737

G1 X113.205 Y143.547 E1.09737
M204 S6000
G1 Z.45 F30000
G1 E-.8 F1800
G1 X113.781 Y103.893 F30000
G1 E.8 F1800
G1 Z.25 F30000
G1 F1800
M204 S5000
G1 X133.608 Y123.72 E1.09737

G1 X113.781 Y143.547 E1.09737
M204 S6000
G1 Z.45 F30000
G1 E-.8 F1800
G1 X116.231 Y103.893 F30000
G1 E.8 F1800
G1 Z.25 F30000
M400
 M900 K0.025; Override pressure advance value
G1 F1800
M204 S5000
G1 X136.058 Y123.72 E1.09737

G1 X116.231 Y143.547 E1.09737
M204 S6000
G1 Z.45 F30000
G1 E-.8 F1800
M73 P74 R2
G1 X116.806 Y103.893 F30000
G1 E.8 F1800
G1 Z.25 F30000
G1 F1800
M204 S5000
G1 X136.633 Y123.72 E1.09737

G1 X116.806 Y143.547 E1.09737
M204 S6000
G1 Z.45 F30000
G1 E-.8 F1800
G1 X117.382 Y103.893 F30000
G1 E.8 F1800
G1 Z.25 F30000
G1 F1800
M204 S5000
G1 X137.209 Y123.72 E1.09737

G1 X117.382 Y143.547 E1.09737
M204 S6000
G1 Z.45 F30000
G1 E-.8 F1800
G1 X119.832 Y103.893 F30000
G1 E.8 F1800
G1 Z.25 F30000
M400
 M900 K0.03; Override pressure advance value
G1 F1800
M204 S5000
G1 X139.659 Y123.72 E1.09737

G1 X119.832 Y143.547 E1.09737
M204 S6000
G1 Z.45 F30000
M73 P75 R2
G1 E-.8 F1800
G1 X120.408 Y103.893 F30000
G1 E.8 F1800
G1 Z.25 F30000
G1 F1800
M204 S5000
G1 X140.235 Y123.72 E1.09737

G1 X120.408 Y143.547 E1.09737
M204 S6000
G1 Z.45 F30000
G1 E-.8 F1800
G1 X120.983 Y103.893 F30000
G1 E.8 F1800
G1 Z.25 F30000
G1 F1800
M204 S5000
G1 X140.811 Y123.72 E1.09737

G1 X120.983 Y143.547 E1.09737
M204 S6000
G1 Z.45 F30000
G1 E-.8 F1800
G1 X123.433 Y103.893 F30000
G1 E.8 F1800
G1 Z.25 F30000
M400
 M900 K0.035; Override pressure advance value
G1 F1800
M204 S5000
G1 X143.261 Y123.72 E1.09737

G1 X123.433 Y143.547 E1.09737
M204 S6000
G1 Z.45 F30000
M73 P76 R2
G1 E-.8 F1800
G1 X124.009 Y103.893 F30000
G1 E.8 F1800
G1 Z.25 F30000
G1 F1800
M204 S5000
G1 X143.836 Y123.72 E1.09737

G1 X124.009 Y143.547 E1.09737
M204 S6000
G1 Z.45 F30000
G1 E-.8 F1800
G1 X124.585 Y103.893 F30000
G1 E.8 F1800
G1 Z.25 F30000
G1 F1800
M204 S5000
G1 X144.412 Y123.72 E1.09737

G1 X124.585 Y143.547 E1.09737
M204 S6000
G1 Z.45 F30000
G1 E-.8 F1800
G1 X127.035 Y103.893 F30000
G1 E.8 F1800
G1 Z.25 F30000
M400
 M900 K0.04; Override pressure advance value
G1 F1800
M204 S5000
G1 X146.862 Y123.72 E1.09737

G1 X127.035 Y143.547 E1.09737
M204 S6000
G1 Z.45 F30000
M73 P77 R2
G1 E-.8 F1800
G1 X127.61 Y103.893 F30000
G1 E.8 F1800
G1 Z.25 F30000
G1 F1800
M204 S5000
G1 X147.438 Y123.72 E1.09737

G1 X127.61 Y143.547 E1.09737
M204 S6000
G1 Z.45 F30000
G1 E-.8 F1800
G1 X128.186 Y103.893 F30000
G1 E.8 F1800
G1 Z.25 F30000
G1 F1800
M204 S5000
G1 X148.013 Y123.72 E1.09737

G1 X128.186 Y143.547 E1.09737
M204 S6000
G1 Z.45 F30000
G1 E-.8 F1800
G1 X130.636 Y103.893 F30000
G1 E.8 F1800
G1 Z.25 F30000
M400
 M900 K0.045; Override pressure advance value
G1 F1800
M204 S5000
G1 X150.463 Y123.72 E1.09737

G1 X130.636 Y143.547 E1.09737
M204 S6000
G1 Z.45 F30000
M73 P78 R2
G1 E-.8 F1800
G1 X131.212 Y103.893 F30000
G1 E.8 F1800
G1 Z.25 F30000
G1 F1800
M204 S5000
G1 X151.039 Y123.72 E1.09737

G1 X131.212 Y143.547 E1.09737
M204 S6000
G1 Z.45 F30000
G1 E-.8 F1800
G1 X131.788 Y103.893 F30000
G1 E.8 F1800
G1 Z.25 F30000
G1 F1800
M204 S5000
G1 X151.615 Y123.72 E1.09737

G1 X131.788 Y143.547 E1.09737
M204 S6000
G1 Z.45 F30000
G1 E-.8 F1800
G1 X134.238 Y103.893 F30000
G1 E.8 F1800
G1 Z.25 F30000
M400
 M900 K0.05; Override pressure advance value
G1 F1800
M204 S5000
G1 X154.065 Y123.72 E1.09737

G1 X134.238 Y143.547 E1.09737
M204 S6000
G1 Z.45 F30000
M73 P79 R2
G1 E-.8 F1800
G1 X134.813 Y103.893 F30000
G1 E.8 F1800
G1 Z.25 F30000
G1 F1800
M204 S5000
G1 X154.64 Y123.72 E1.09737

G1 X134.813 Y143.547 E1.09737
M204 S6000
G1 Z.45 F30000
G1 E-.8 F1800
G1 X135.389 Y103.893 F30000
G1 E.8 F1800
G1 Z.25 F30000
G1 F1800
M204 S5000
G1 X155.216 Y123.72 E1.09737

G1 X135.389 Y143.547 E1.09737
M204 S6000
G1 Z.45 F30000
G1 E-.8 F1800
G1 X98.224 Y103.893 F30000
G1 E.8 F1800
G1 Z.25 F30000
; end pressure advance pattern for layer

; OBJECT_ID: 282
G1 E-.8 F1800
G1 X97.822 Y97.064 F30000
M204 S6000
G1 Z.4
G1 Z.25
M73 P80 R2
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.56
M204 S500
G1 X95.708 Y97.064 E.10573
G1 X95.708 Y94.949 E.10573
G1 X97.822 Y94.949 E.10573
G1 X97.822 Y97.004 E.10273
M204 S6000
G1 X98.329 Y97.57 F30000
G1 F1800
M204 S500
G1 X95.201 Y97.57 E.15636
G1 X95.201 Y94.443 E.15636
G1 X98.329 Y94.443 E.15636
G1 X98.329 Y97.51 E.15336
M204 S6000
G1 X98.835 Y98.077 F30000
; FEATURE: Outer wall
G1 F1800
M204 S500
G1 X94.695 Y98.077 E.20699
G1 X94.695 Y93.937 E.20699
G1 X98.835 Y93.937 E.20699
G1 X98.835 Y98.017 E.20399
;========Date 20250206========
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
 ; timelapse without wipe tower
M971 S11 C10 O0
M1004 S5 P1  ; external shutter

M623
; SKIPPABLE_END
; WIPE_START
G1 X96.835 Y98.046 E-.76
; WIPE_END
G1 E-.04
M204 S6000
G1 X96.381 Y95.152 Z.65 F30000
M73 P80 R1
G1 Z.25
G1 E.8 F1800
; FEATURE: Bottom surface
; LINE_WIDTH: 0.66126
G1 F3475.914
M204 S500
G1 X97.392 Y96.163 E.08574
M73 P81 R1
G1 X97.392 Y96.634 E.02827
G1 X97.004 Y96.634 E.02328
G1 X96.138 Y95.768 E.07346
G1 X96.138 Y96.627 E.05155
G1 X96.372 Y96.862 E.01988
; CHANGE_LAYER
; Z_HEIGHT: 0.45
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F3475.914
G1 X96.138 Y96.627 E-.12593
G1 X96.138 Y95.768 E-.32653
G1 X96.71 Y96.34 E-.30754
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 2/4
; update layer progress
M73 L2
M991 S0 P1 ;notify layer change
; open powerlost recovery
M1003 S1
; CUSTOM_GCODE
G1 E.8
; start pressure advance pattern for layer
M204 S10000
G1 Z.45 F30000
M400
 M900 K0; Override pressure advance value
G1 F30
G1 E-.8 F1800
G1 X95.476 Y146.383 F30000
G1 E.8 F1800
M204 S5000
G1 X95.476 Y148.383 E.06431
G1 X99.476 Y148.383 E.12863
G1 X99.476 Y146.383 E.06431
G1 X95.701 Y146.383 E.12863
G1 F30
M73 P82 R1
G1 E-.8 F1800
M204 S10000
G1 X102.679 Y146.383 F30000
G1 E.8 F1800
M204 S5000
G1 X102.679 Y148.383 E.06431
G1 X106.679 Y148.383 E.12863
G1 X106.679 Y146.383 E.06431
G1 X102.904 Y146.383 E.12863
G1 E-.8
M204 S10000
G1 X106.679 Y150.383 F30000
G1 E.8 F1800
M204 S5000
G1 X105.679 Y150.383 E.06431
G1 E-.8
M204 S10000
G1 X102.679 Y152.383 F30000
G1 E.8 F1800
M204 S5000
G1 X102.679 Y154.383 E.06431
G1 X106.679 Y154.383 E.12863
G1 X106.679 Y152.383 E.06431
G1 X102.904 Y152.383 E.12863
G1 E-.8
M204 S10000
G1 X102.679 Y156.383 F30000
G1 E.8 F1800
M204 S5000
G1 X106.679 Y156.383 E.12863
G1 F30
G1 E-.8 F1800
M204 S10000
G1 X109.882 Y146.383 F30000
G1 E.8 F1800
M204 S5000
G1 X109.882 Y148.383 E.06431
G1 X113.882 Y148.383 E.12863
G1 X113.882 Y146.383 E.06431
G1 X110.107 Y146.383 E.12863
G1 E-.8
M204 S10000
G1 X113.882 Y150.383 F30000
G1 E.8 F1800
M204 S5000
G1 X112.882 Y150.383 E.06431
G1 E-.8
M204 S10000
G1 X109.882 Y152.383 F30000
G1 E.8 F1800
M204 S5000
G1 X109.882 Y154.383 E.06431
G1 X113.882 Y154.383 E.12863
G1 X113.882 Y152.383 E.06431
G1 X110.107 Y152.383 E.12863
G1 E-.8
M204 S10000
G1 X109.882 Y155.383 F30000
G1 E.8 F1800
M204 S5000
G1 X109.882 Y157.383 E.06431
G1 X111.882 Y157.383 E.06431
G1 X111.882 Y155.383 E.06431
G1 X113.882 Y155.383 E.06431
G1 X113.882 Y157.383 E.06431
G1 F30
G1 E-.8 F1800
M204 S10000
G1 X117.084 Y146.383 F30000
G1 E.8 F1800
M204 S5000
G1 X117.084 Y148.383 E.06431
G1 X121.084 Y148.383 E.12863
G1 X121.084 Y146.383 E.06431
G1 X117.309 Y146.383 E.12863
G1 E-.8
M204 S10000
G1 X121.084 Y150.383 F30000
G1 E.8 F1800
M204 S5000
G1 X120.084 Y150.383 E.06431
G1 E-.8
M204 S10000
G1 X117.084 Y152.383 F30000
G1 E.8 F1800
M204 S5000
G1 X117.084 Y154.383 E.06431
G1 X121.084 Y154.383 E.12863
G1 X121.084 Y152.383 E.06431
G1 X117.309 Y152.383 E.12863
G1 E-.8
M204 S10000
G1 X117.084 Y155.383 F30000
G1 E.8 F1800
M204 S5000
G1 X117.084 Y157.383 E.06431
G1 X121.084 Y157.383 E.12863
G1 X121.084 Y155.383 E.06431
G1 E-.8
M204 S10000
G1 X119.084 Y157.608 F30000
G1 E.8 F1800
M204 S5000
G1 X119.084 Y155.383 E.06431
G1 F30
G1 E-.8 F1800
M204 S10000
G1 X124.287 Y146.383 F30000
G1 E.8 F1800
M204 S5000
G1 X124.287 Y148.383 E.06431
G1 X128.287 Y148.383 E.12863
G1 X128.287 Y146.383 E.06431
G1 X124.512 Y146.383 E.12863
G1 E-.8
M204 S10000
G1 X128.287 Y150.383 F30000
G1 E.8 F1800
M204 S5000
G1 X127.287 Y150.383 E.06431
G1 E-.8
M204 S10000
G1 X124.287 Y152.383 F30000
G1 E.8 F1800
M204 S5000
G1 X124.287 Y154.383 E.06431
G1 X128.287 Y154.383 E.12863
G1 X128.287 Y152.383 E.06431
G1 X124.512 Y152.383 E.12863
G1 E-.8
M204 S10000
G1 X124.287 Y155.383 F30000
G1 E.8 F1800
M204 S5000
G1 X126.287 Y155.383 E.06431
G1 X126.287 Y157.383 E.06431
G1 E-.8
M204 S10000
G1 X124.287 Y157.383 F30000
G1 E.8 F1800
M204 S5000
M73 P83 R1
G1 X128.287 Y157.383 E.12863
G1 F30
G1 E-.8 F1800
M204 S10000
G1 X131.49 Y146.383 F30000
G1 E.8 F1800
M204 S5000
G1 X131.49 Y148.383 E.06431
G1 X135.49 Y148.383 E.12863
G1 X135.49 Y146.383 E.06431
G1 X131.715 Y146.383 E.12863
G1 E-.8
M204 S10000
G1 X135.49 Y150.383 F30000
G1 E.8 F1800
M204 S5000
G1 X134.49 Y150.383 E.06431
G1 E-.8
M204 S10000
G1 X131.49 Y152.383 F30000
G1 E.8 F1800
M204 S5000
G1 X131.49 Y154.383 E.06431
G1 X135.49 Y154.383 E.12863
G1 X135.49 Y152.383 E.06431
G1 X131.715 Y152.383 E.12863
G1 E-.8
M204 S10000
G1 X131.49 Y157.383 F30000
G1 E.8 F1800
M204 S5000
G1 X131.49 Y155.383 E.06431
G1 X133.49 Y155.383 E.06431
G1 X133.49 Y157.383 E.06431
G1 X135.49 Y157.383 E.06431
G1 X135.49 Y155.383 E.06431
M204 S10000
G1 Z.65 F30000
G1 E-.8 F1800
G1 X96.838 Y102.507 F30000
G1 E.8 F1800
G1 Z.45 F30000
M400
 M900 K0; Override pressure advance value
G1 F6960
M204 S5000
G1 X118.051 Y123.72 E.96469

G1 X96.838 Y144.933 E.96469
M204 S10000
G1 Z.65 F30000
G1 E-.8 F1800
G1 X97.413 Y102.507 F30000
G1 E.8 F1800
G1 Z.45 F30000
G1 F6960
M204 S5000
G1 X118.626 Y123.72 E.96469

G1 X97.413 Y144.933 E.96469
M204 S10000
G1 Z.65 F30000
G1 E-.8 F1800
G1 X97.989 Y102.507 F30000
G1 E.8 F1800
G1 Z.45 F30000
G1 F6960
M204 S5000
G1 X119.202 Y123.72 E.96469

G1 X97.989 Y144.933 E.96469
M204 S10000
G1 Z.65 F30000
G1 E-.8 F1800
G1 X100.439 Y102.507 F30000
G1 E.8 F1800
G1 Z.45 F30000
M400
 M900 K0.005; Override pressure advance value
G1 F6960
M204 S5000
G1 X121.652 Y123.72 E.96469

G1 X100.439 Y144.933 E.96469
M204 S10000
G1 Z.65 F30000
G1 E-.8 F1800
G1 X101.015 Y102.507 F30000
G1 E.8 F1800
G1 Z.45 F30000
G1 F6960
M204 S5000
G1 X122.228 Y123.72 E.96469

G1 X101.015 Y144.933 E.96469
M204 S10000
G1 Z.65 F30000
G1 E-.8 F1800
G1 X101.59 Y102.507 F30000
G1 E.8 F1800
G1 Z.45 F30000
G1 F6960
M204 S5000
G1 X122.804 Y123.72 E.96469

G1 X101.59 Y144.933 E.96469
M204 S10000
G1 Z.65 F30000
G1 E-.8 F1800
G1 X104.04 Y102.507 F30000
G1 E.8 F1800
G1 Z.45 F30000
M400
 M900 K0.01; Override pressure advance value
G1 F6960
M204 S5000
G1 X125.254 Y123.72 E.96469

G1 X104.04 Y144.933 E.96469
M204 S10000
G1 Z.65 F30000
G1 E-.8 F1800
G1 X104.616 Y102.507 F30000
G1 E.8 F1800
G1 Z.45 F30000
G1 F6960
M204 S5000
G1 X125.829 Y123.72 E.96469

G1 X104.616 Y144.933 E.96469
M204 S10000
G1 Z.65 F30000
G1 E-.8 F1800
G1 X105.192 Y102.507 F30000
M73 P84 R1
G1 E.8 F1800
G1 Z.45 F30000
G1 F6960
M204 S5000
G1 X126.405 Y123.72 E.96469

G1 X105.192 Y144.933 E.96469
M204 S10000
G1 Z.65 F30000
G1 E-.8 F1800
G1 X107.642 Y102.507 F30000
G1 E.8 F1800
G1 Z.45 F30000
M400
 M900 K0.015; Override pressure advance value
G1 F6960
M204 S5000
G1 X128.855 Y123.72 E.96469

G1 X107.642 Y144.933 E.96469
M204 S10000
G1 Z.65 F30000
G1 E-.8 F1800
G1 X108.217 Y102.507 F30000
G1 E.8 F1800
G1 Z.45 F30000
G1 F6960
M204 S5000
G1 X129.431 Y123.72 E.96469

G1 X108.217 Y144.933 E.96469
M204 S10000
G1 Z.65 F30000
G1 E-.8 F1800
G1 X108.793 Y102.507 F30000
G1 E.8 F1800
G1 Z.45 F30000
G1 F6960
M204 S5000
G1 X130.006 Y123.72 E.96469

G1 X108.793 Y144.933 E.96469
M204 S10000
G1 Z.65 F30000
G1 E-.8 F1800
G1 X111.243 Y102.507 F30000
G1 E.8 F1800
G1 Z.45 F30000
M400
 M900 K0.02; Override pressure advance value
G1 F6960
M204 S5000
G1 X132.456 Y123.72 E.96469

G1 X111.243 Y144.933 E.96469
M204 S10000
G1 Z.65 F30000
G1 E-.8 F1800
G1 X111.819 Y102.507 F30000
G1 E.8 F1800
G1 Z.45 F30000
G1 F6960
M204 S5000
G1 X133.032 Y123.72 E.96469

G1 X111.819 Y144.933 E.96469
M204 S10000
G1 Z.65 F30000
G1 E-.8 F1800
G1 X112.395 Y102.507 F30000
G1 E.8 F1800
G1 Z.45 F30000
G1 F6960
M204 S5000
G1 X133.608 Y123.72 E.96469

G1 X112.395 Y144.933 E.96469
M204 S10000
G1 Z.65 F30000
G1 E-.8 F1800
G1 X114.845 Y102.507 F30000
G1 E.8 F1800
G1 Z.45 F30000
M400
 M900 K0.025; Override pressure advance value
G1 F6960
M204 S5000
G1 X136.058 Y123.72 E.96469

G1 X114.845 Y144.933 E.96469
M204 S10000
G1 Z.65 F30000
G1 E-.8 F1800
M73 P85 R1
G1 X115.42 Y102.507 F30000
G1 E.8 F1800
G1 Z.45 F30000
G1 F6960
M204 S5000
G1 X136.633 Y123.72 E.96469

G1 X115.42 Y144.933 E.96469
M204 S10000
G1 Z.65 F30000
G1 E-.8 F1800
G1 X115.996 Y102.507 F30000
G1 E.8 F1800
G1 Z.45 F30000
G1 F6960
M204 S5000
G1 X137.209 Y123.72 E.96469

G1 X115.996 Y144.933 E.96469
M204 S10000
G1 Z.65 F30000
G1 E-.8 F1800
G1 X118.446 Y102.507 F30000
G1 E.8 F1800
G1 Z.45 F30000
M400
 M900 K0.03; Override pressure advance value
G1 F6960
M204 S5000
G1 X139.659 Y123.72 E.96469

G1 X118.446 Y144.933 E.96469
M204 S10000
G1 Z.65 F30000
G1 E-.8 F1800
G1 X119.022 Y102.507 F30000
G1 E.8 F1800
G1 Z.45 F30000
G1 F6960
M204 S5000
G1 X140.235 Y123.72 E.96469

G1 X119.022 Y144.933 E.96469
M204 S10000
G1 Z.65 F30000
G1 E-.8 F1800
G1 X119.597 Y102.507 F30000
G1 E.8 F1800
G1 Z.45 F30000
G1 F6960
M204 S5000
G1 X140.811 Y123.72 E.96469

G1 X119.597 Y144.933 E.96469
M204 S10000
G1 Z.65 F30000
G1 E-.8 F1800
G1 X122.047 Y102.507 F30000
G1 E.8 F1800
G1 Z.45 F30000
M400
 M900 K0.035; Override pressure advance value
G1 F6960
M204 S5000
G1 X143.261 Y123.72 E.96469

G1 X122.047 Y144.933 E.96469
M204 S10000
G1 Z.65 F30000
G1 E-.8 F1800
G1 X122.623 Y102.507 F30000
G1 E.8 F1800
G1 Z.45 F30000
G1 F6960
M204 S5000
G1 X143.836 Y123.72 E.96469

G1 X122.623 Y144.933 E.96469
M204 S10000
G1 Z.65 F30000
G1 E-.8 F1800
G1 X123.199 Y102.507 F30000
G1 E.8 F1800
G1 Z.45 F30000
G1 F6960
M204 S5000
G1 X144.412 Y123.72 E.96469

G1 X123.199 Y144.933 E.96469
M204 S10000
G1 Z.65 F30000
G1 E-.8 F1800
M73 P86 R1
G1 X125.649 Y102.507 F30000
G1 E.8 F1800
G1 Z.45 F30000
M400
 M900 K0.04; Override pressure advance value
G1 F6960
M204 S5000
G1 X146.862 Y123.72 E.96469

G1 X125.649 Y144.933 E.96469
M204 S10000
G1 Z.65 F30000
G1 E-.8 F1800
G1 X126.224 Y102.507 F30000
G1 E.8 F1800
G1 Z.45 F30000
G1 F6960
M204 S5000
G1 X147.438 Y123.72 E.96469

G1 X126.224 Y144.933 E.96469
M204 S10000
G1 Z.65 F30000
G1 E-.8 F1800
G1 X126.8 Y102.507 F30000
G1 E.8 F1800
G1 Z.45 F30000
G1 F6960
M204 S5000
G1 X148.013 Y123.72 E.96469

G1 X126.8 Y144.933 E.96469
M204 S10000
G1 Z.65 F30000
G1 E-.8 F1800
G1 X129.25 Y102.507 F30000
G1 E.8 F1800
G1 Z.45 F30000
M400
 M900 K0.045; Override pressure advance value
G1 F6960
M204 S5000
G1 X150.463 Y123.72 E.96469

G1 X129.25 Y144.933 E.96469
M204 S10000
G1 Z.65 F30000
G1 E-.8 F1800
G1 X129.826 Y102.507 F30000
G1 E.8 F1800
G1 Z.45 F30000
G1 F6960
M204 S5000
G1 X151.039 Y123.72 E.96469

G1 X129.826 Y144.933 E.96469
M204 S10000
G1 Z.65 F30000
G1 E-.8 F1800
G1 X130.402 Y102.507 F30000
G1 E.8 F1800
G1 Z.45 F30000
G1 F6960
M204 S5000
G1 X151.615 Y123.72 E.96469

G1 X130.402 Y144.933 E.96469
M204 S10000
G1 Z.65 F30000
G1 E-.8 F1800
G1 X132.852 Y102.507 F30000
G1 E.8 F1800
G1 Z.45 F30000
M400
 M900 K0.05; Override pressure advance value
G1 F6960
M204 S5000
G1 X154.065 Y123.72 E.96469

G1 X132.852 Y144.933 E.96469
M204 S10000
G1 Z.65 F30000
G1 E-.8 F1800
G1 X133.427 Y102.507 F30000
G1 E.8 F1800
G1 Z.45 F30000
G1 F6960
M204 S5000
G1 X154.64 Y123.72 E.96469

G1 X133.427 Y144.933 E.96469
M204 S10000
G1 Z.65 F30000
G1 E-.8 F1800
M73 P87 R1
G1 X134.003 Y102.507 F30000
G1 E.8 F1800
G1 Z.45 F30000
G1 F6960
M204 S5000
G1 X155.216 Y123.72 E.96469

G1 X134.003 Y144.933 E.96469
M204 S10000
G1 Z.65 F30000
G1 E-.8 F1800
G1 X96.838 Y102.507 F30000
G1 E.8 F1800
G1 Z.45 F30000
; end pressure advance pattern for layer

; OBJECT_ID: 282
G1 E-.8 F1800
M204 S10000
G17
G3 Z.65 I-.729 J.974 P1  F30000
G1 X98.256 Y97.498 Z.65
G1 Z.45
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F6485.217
G1 X95.274 Y97.498 E.09588
G1 X95.274 Y94.516 E.09588
G1 X98.256 Y94.516 E.09588
G1 X98.256 Y97.438 E.09395
G1 X98.663 Y97.905 F30000
G1 F6485.217
G1 X94.867 Y97.905 E.12206
G1 X94.867 Y94.109 E.12206
G1 X98.663 Y94.109 E.12206
G1 X98.663 Y97.845 E.12013
M204 S250
G1 X99.055 Y98.297 F30000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F7001.174
M204 S5000
G1 X94.475 Y98.297 E.13642
G1 X94.475 Y93.717 E.13642
G1 X99.055 Y93.717 E.13642
G1 X99.055 Y98.237 E.13464
;========Date 20250206========
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
 ; timelapse without wipe tower
M971 S11 C10 O0
M1004 S5 P1  ; external shutter

M623
; SKIPPABLE_END
; WIPE_START
M204 S10000
G1 X97.055 Y98.263 E-.76
; WIPE_END
G1 E-.04 F1800
G1 X97.864 Y96.007 Z.85 F30000
G1 Z.45
G1 E.8 F1800
; FEATURE: Internal solid infill
; LINE_WIDTH: 0.41999
G1 F7001.352
G1 X97.864 Y94.908 E.03273
G1 X95.666 Y94.908 E.06546
G1 X95.666 Y97.106 E.06546
G1 X97.864 Y97.106 E.06546
G1 X97.864 Y96.067 E.03094
G1 X97.487 Y96.007 F30000
G1 F7001.352
G1 X97.487 Y95.285 E.0215
G1 X96.043 Y95.285 E.043
G1 X96.043 Y96.729 E.043
G1 X97.487 Y96.729 E.043
G1 X97.487 Y96.067 E.01971
G1 X97.11 Y96.007 F30000
G1 F7001.352
G1 X97.11 Y95.662 E.01027
G1 X96.42 Y95.662 E.02053
G1 X96.42 Y96.351 E.02053
G1 X97.11 Y96.351 E.02053
G1 X97.11 Y96.067 E.00848
G1 X96.784 Y95.973 F30000
; LINE_WIDTH: 0.35518
G1 F8454.493
G1 X96.726 Y96.007 E.00167
G1 X96.766 Y96.03 E.00115
; CHANGE_LAYER
; Z_HEIGHT: 0.65
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F8454.493
G1 X96.726 Y96.007 E-.31023
G1 X96.784 Y95.973 E-.44977
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 3/4
; update layer progress
M73 L3
M991 S0 P2 ;notify layer change
; CUSTOM_GCODE
G1 E.8
; start pressure advance pattern for layer
M204 S10000
G1 Z.65 F30000
G1 Z.85
M73 P88 R1
G1 E-.8 F1800
G1 X96.838 Y102.507 F30000
G1 E.8 F1800
G1 Z.65 F30000
M400
 M900 K0; Override pressure advance value
G1 F6960
M204 S5000
G1 X118.051 Y123.72 E.96469

G1 X96.838 Y144.933 E.96469
M204 S10000
G1 Z.85 F30000
G1 E-.8 F1800
G1 X97.413 Y102.507 F30000
G1 E.8 F1800
G1 Z.65 F30000
G1 F6960
M204 S5000
G1 X118.626 Y123.72 E.96469

G1 X97.413 Y144.933 E.96469
M204 S10000
G1 Z.85 F30000
G1 E-.8 F1800
G1 X97.989 Y102.507 F30000
G1 E.8 F1800
G1 Z.65 F30000
G1 F6960
M204 S5000
G1 X119.202 Y123.72 E.96469

G1 X97.989 Y144.933 E.96469
M204 S10000
G1 Z.85 F30000
G1 E-.8 F1800
G1 X100.439 Y102.507 F30000
G1 E.8 F1800
G1 Z.65 F30000
M400
 M900 K0.005; Override pressure advance value
G1 F6960
M204 S5000
G1 X121.652 Y123.72 E.96469

G1 X100.439 Y144.933 E.96469
M204 S10000
G1 Z.85 F30000
G1 E-.8 F1800
G1 X101.015 Y102.507 F30000
G1 E.8 F1800
G1 Z.65 F30000
G1 F6960
M204 S5000
G1 X122.228 Y123.72 E.96469

G1 X101.015 Y144.933 E.96469
M204 S10000
G1 Z.85 F30000
G1 E-.8 F1800
G1 X101.59 Y102.507 F30000
G1 E.8 F1800
G1 Z.65 F30000
G1 F6960
M204 S5000
G1 X122.804 Y123.72 E.96469

G1 X101.59 Y144.933 E.96469
M204 S10000
G1 Z.85 F30000
G1 E-.8 F1800
G1 X104.04 Y102.507 F30000
G1 E.8 F1800
G1 Z.65 F30000
M400
 M900 K0.01; Override pressure advance value
G1 F6960
M204 S5000
G1 X125.254 Y123.72 E.96469

G1 X104.04 Y144.933 E.96469
M204 S10000
G1 Z.85 F30000
G1 E-.8 F1800
G1 X104.616 Y102.507 F30000
G1 E.8 F1800
G1 Z.65 F30000
G1 F6960
M204 S5000
G1 X125.829 Y123.72 E.96469

G1 X104.616 Y144.933 E.96469
M204 S10000
G1 Z.85 F30000
G1 E-.8 F1800
G1 X105.192 Y102.507 F30000
G1 E.8 F1800
G1 Z.65 F30000
G1 F6960
M204 S5000
G1 X126.405 Y123.72 E.96469

G1 X105.192 Y144.933 E.96469
M204 S10000
G1 Z.85 F30000
G1 E-.8 F1800
G1 X107.642 Y102.507 F30000
G1 E.8 F1800
G1 Z.65 F30000
M400
 M900 K0.015; Override pressure advance value
G1 F6960
M204 S5000
G1 X128.855 Y123.72 E.96469

G1 X107.642 Y144.933 E.96469
M204 S10000
G1 Z.85 F30000
G1 E-.8 F1800
G1 X108.217 Y102.507 F30000
G1 E.8 F1800
G1 Z.65 F30000
G1 F6960
M204 S5000
G1 X129.431 Y123.72 E.96469

G1 X108.217 Y144.933 E.96469
M204 S10000
G1 Z.85 F30000
G1 E-.8 F1800
G1 X108.793 Y102.507 F30000
G1 E.8 F1800
G1 Z.65 F30000
G1 F6960
M204 S5000
G1 X130.006 Y123.72 E.96469

G1 X108.793 Y144.933 E.96469
M204 S10000
G1 Z.85 F30000
G1 E-.8 F1800
G1 X111.243 Y102.507 F30000
G1 E.8 F1800
G1 Z.65 F30000
M400
 M900 K0.02; Override pressure advance value
G1 F6960
M204 S5000
G1 X132.456 Y123.72 E.96469

G1 X111.243 Y144.933 E.96469
M204 S10000
G1 Z.85 F30000
G1 E-.8 F1800
M73 P89 R1
G1 X111.819 Y102.507 F30000
G1 E.8 F1800
G1 Z.65 F30000
G1 F6960
M204 S5000
G1 X133.032 Y123.72 E.96469

G1 X111.819 Y144.933 E.96469
M204 S10000
G1 Z.85 F30000
G1 E-.8 F1800
G1 X112.395 Y102.507 F30000
G1 E.8 F1800
G1 Z.65 F30000
G1 F6960
M204 S5000
G1 X133.608 Y123.72 E.96469

G1 X112.395 Y144.933 E.96469
M204 S10000
G1 Z.85 F30000
G1 E-.8 F1800
G1 X114.845 Y102.507 F30000
G1 E.8 F1800
G1 Z.65 F30000
M400
 M900 K0.025; Override pressure advance value
G1 F6960
M204 S5000
G1 X136.058 Y123.72 E.96469

G1 X114.845 Y144.933 E.96469
M204 S10000
G1 Z.85 F30000
G1 E-.8 F1800
G1 X115.42 Y102.507 F30000
G1 E.8 F1800
G1 Z.65 F30000
G1 F6960
M204 S5000
G1 X136.633 Y123.72 E.96469

G1 X115.42 Y144.933 E.96469
M204 S10000
G1 Z.85 F30000
G1 E-.8 F1800
G1 X115.996 Y102.507 F30000
G1 E.8 F1800
G1 Z.65 F30000
G1 F6960
M204 S5000
G1 X137.209 Y123.72 E.96469

G1 X115.996 Y144.933 E.96469
M204 S10000
G1 Z.85 F30000
G1 E-.8 F1800
G1 X118.446 Y102.507 F30000
G1 E.8 F1800
G1 Z.65 F30000
M400
 M900 K0.03; Override pressure advance value
G1 F6960
M204 S5000
G1 X139.659 Y123.72 E.96469

G1 X118.446 Y144.933 E.96469
M204 S10000
G1 Z.85 F30000
G1 E-.8 F1800
G1 X119.022 Y102.507 F30000
G1 E.8 F1800
G1 Z.65 F30000
G1 F6960
M204 S5000
G1 X140.235 Y123.72 E.96469

G1 X119.022 Y144.933 E.96469
M204 S10000
G1 Z.85 F30000
G1 E-.8 F1800
G1 X119.597 Y102.507 F30000
G1 E.8 F1800
G1 Z.65 F30000
G1 F6960
M204 S5000
G1 X140.811 Y123.72 E.96469

G1 X119.597 Y144.933 E.96469
M204 S10000
G1 Z.85 F30000
M73 P90 R1
G1 E-.8 F1800
G1 X122.047 Y102.507 F30000
G1 E.8 F1800
G1 Z.65 F30000
M400
 M900 K0.035; Override pressure advance value
G1 F6960
M204 S5000
G1 X143.261 Y123.72 E.96469

G1 X122.047 Y144.933 E.96469
M204 S10000
G1 Z.85 F30000
G1 E-.8 F1800
G1 X122.623 Y102.507 F30000
G1 E.8 F1800
G1 Z.65 F30000
G1 F6960
M204 S5000
G1 X143.836 Y123.72 E.96469

G1 X122.623 Y144.933 E.96469
M204 S10000
G1 Z.85 F30000
G1 E-.8 F1800
G1 X123.199 Y102.507 F30000
G1 E.8 F1800
G1 Z.65 F30000
G1 F6960
M204 S5000
G1 X144.412 Y123.72 E.96469

G1 X123.199 Y144.933 E.96469
M204 S10000
G1 Z.85 F30000
G1 E-.8 F1800
G1 X125.649 Y102.507 F30000
G1 E.8 F1800
G1 Z.65 F30000
M400
 M900 K0.04; Override pressure advance value
G1 F6960
M204 S5000
G1 X146.862 Y123.72 E.96469

G1 X125.649 Y144.933 E.96469
M204 S10000
G1 Z.85 F30000
G1 E-.8 F1800
M73 P90 R0
G1 X126.224 Y102.507 F30000
G1 E.8 F1800
G1 Z.65 F30000
G1 F6960
M204 S5000
G1 X147.438 Y123.72 E.96469

G1 X126.224 Y144.933 E.96469
M204 S10000
G1 Z.85 F30000
G1 E-.8 F1800
G1 X126.8 Y102.507 F30000
G1 E.8 F1800
G1 Z.65 F30000
G1 F6960
M204 S5000
G1 X148.013 Y123.72 E.96469

G1 X126.8 Y144.933 E.96469
M204 S10000
G1 Z.85 F30000
G1 E-.8 F1800
G1 X129.25 Y102.507 F30000
G1 E.8 F1800
G1 Z.65 F30000
M400
 M900 K0.045; Override pressure advance value
G1 F6960
M204 S5000
G1 X150.463 Y123.72 E.96469

G1 X129.25 Y144.933 E.96469
M204 S10000
G1 Z.85 F30000
G1 E-.8 F1800
G1 X129.826 Y102.507 F30000
G1 E.8 F1800
G1 Z.65 F30000
G1 F6960
M204 S5000
G1 X151.039 Y123.72 E.96469

G1 X129.826 Y144.933 E.96469
M204 S10000
G1 Z.85 F30000
M73 P91 R0
G1 E-.8 F1800
G1 X130.402 Y102.507 F30000
G1 E.8 F1800
G1 Z.65 F30000
G1 F6960
M204 S5000
G1 X151.615 Y123.72 E.96469

G1 X130.402 Y144.933 E.96469
M204 S10000
G1 Z.85 F30000
G1 E-.8 F1800
G1 X132.852 Y102.507 F30000
G1 E.8 F1800
G1 Z.65 F30000
M400
 M900 K0.05; Override pressure advance value
G1 F6960
M204 S5000
G1 X154.065 Y123.72 E.96469

G1 X132.852 Y144.933 E.96469
M204 S10000
G1 Z.85 F30000
G1 E-.8 F1800
G1 X133.427 Y102.507 F30000
G1 E.8 F1800
G1 Z.65 F30000
G1 F6960
M204 S5000
G1 X154.64 Y123.72 E.96469

G1 X133.427 Y144.933 E.96469
M204 S10000
G1 Z.85 F30000
G1 E-.8 F1800
G1 X134.003 Y102.507 F30000
G1 E.8 F1800
G1 Z.65 F30000
G1 F6960
M204 S5000
G1 X155.216 Y123.72 E.96469

G1 X134.003 Y144.933 E.96469
M204 S10000
G1 Z.85 F30000
G1 E-.8 F1800
G1 X96.838 Y102.507 F30000
G1 E.8 F1800
G1 Z.65 F30000
; end pressure advance pattern for layer

; OBJECT_ID: 282
G1 E-.8 F1800
G17
G3 Z.85 I-.876 J.845 P1  F30000
G1 X98.256 Y97.498 Z.85
G1 Z.65
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F6485.217
G1 X95.274 Y97.498 E.09588
G1 X95.274 Y94.516 E.09588
G1 X98.256 Y94.516 E.09588
G1 X98.256 Y97.438 E.09395
G1 X98.663 Y97.905 F30000
G1 F6485.217
G1 X94.867 Y97.905 E.12206
G1 X94.867 Y94.109 E.12206
G1 X98.663 Y94.109 E.12206
G1 X98.663 Y97.845 E.12013
M204 S250
G1 X99.055 Y98.297 F30000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F7001.174
M204 S5000
G1 X94.475 Y98.297 E.13642
G1 X94.475 Y93.717 E.13642
G1 X99.055 Y93.717 E.13642
G1 X99.055 Y98.237 E.13464
;========Date 20250206========
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
 ; timelapse without wipe tower
M971 S11 C10 O0
M1004 S5 P1  ; external shutter

M623
; SKIPPABLE_END
; WIPE_START
M204 S10000
G1 X97.055 Y98.263 E-.76
; WIPE_END
G1 E-.04 F1800
G1 X97.864 Y96.007 Z1.05 F30000
G1 Z.65
G1 E.8 F1800
; FEATURE: Internal solid infill
; LINE_WIDTH: 0.41999
G1 F7001.352
M73 P92 R0
G1 X97.864 Y94.908 E.03273
G1 X95.666 Y94.908 E.06546
G1 X95.666 Y97.106 E.06546
G1 X97.864 Y97.106 E.06546
G1 X97.864 Y96.067 E.03094
G1 X97.487 Y96.007 F30000
G1 F7001.352
G1 X97.487 Y95.285 E.0215
G1 X96.043 Y95.285 E.043
G1 X96.043 Y96.729 E.043
G1 X97.487 Y96.729 E.043
G1 X97.487 Y96.067 E.01971
G1 X97.11 Y96.007 F30000
G1 F7001.352
G1 X97.11 Y95.662 E.01027
G1 X96.42 Y95.662 E.02053
G1 X96.42 Y96.351 E.02053
G1 X97.11 Y96.351 E.02053
G1 X97.11 Y96.067 E.00848
G1 X96.784 Y95.973 F30000
; LINE_WIDTH: 0.35518
G1 F8454.493
G1 X96.726 Y96.007 E.00167
G1 X96.766 Y96.03 E.00115
; CHANGE_LAYER
; Z_HEIGHT: 0.85
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F8454.493
G1 X96.726 Y96.007 E-.31023
G1 X96.784 Y95.973 E-.44977
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 4/4
; update layer progress
M73 L4
M991 S0 P3 ;notify layer change
M106 S91.8
; CUSTOM_GCODE
G1 E.8
; start pressure advance pattern for layer
M204 S10000
G1 Z.85 F30000
G1 Z1.05
G1 E-.8 F1800
G1 X96.838 Y102.507 F30000
G1 E.8 F1800
G1 Z.85 F30000
M400
 M900 K0; Override pressure advance value
G1 F6960
M204 S5000
G1 X118.051 Y123.72 E.96469

G1 X96.838 Y144.933 E.96469
M204 S10000
G1 Z1.05 F30000
G1 E-.8 F1800
G1 X97.413 Y102.507 F30000
G1 E.8 F1800
G1 Z.85 F30000
G1 F6960
M204 S5000
G1 X118.626 Y123.72 E.96469

G1 X97.413 Y144.933 E.96469
M204 S10000
G1 Z1.05 F30000
G1 E-.8 F1800
G1 X97.989 Y102.507 F30000
G1 E.8 F1800
G1 Z.85 F30000
G1 F6960
M204 S5000
G1 X119.202 Y123.72 E.96469

G1 X97.989 Y144.933 E.96469
M204 S10000
G1 Z1.05 F30000
G1 E-.8 F1800
G1 X100.439 Y102.507 F30000
G1 E.8 F1800
G1 Z.85 F30000
M400
 M900 K0.005; Override pressure advance value
G1 F6960
M204 S5000
G1 X121.652 Y123.72 E.96469

G1 X100.439 Y144.933 E.96469
M204 S10000
G1 Z1.05 F30000
G1 E-.8 F1800
G1 X101.015 Y102.507 F30000
G1 E.8 F1800
G1 Z.85 F30000
G1 F6960
M204 S5000
G1 X122.228 Y123.72 E.96469

G1 X101.015 Y144.933 E.96469
M204 S10000
G1 Z1.05 F30000
G1 E-.8 F1800
G1 X101.59 Y102.507 F30000
G1 E.8 F1800
G1 Z.85 F30000
G1 F6960
M204 S5000
G1 X122.804 Y123.72 E.96469

G1 X101.59 Y144.933 E.96469
M204 S10000
G1 Z1.05 F30000
G1 E-.8 F1800
G1 X104.04 Y102.507 F30000
G1 E.8 F1800
G1 Z.85 F30000
M400
 M900 K0.01; Override pressure advance value
G1 F6960
M204 S5000
G1 X125.254 Y123.72 E.96469

G1 X104.04 Y144.933 E.96469
M204 S10000
G1 Z1.05 F30000
G1 E-.8 F1800
G1 X104.616 Y102.507 F30000
G1 E.8 F1800
G1 Z.85 F30000
G1 F6960
M204 S5000
G1 X125.829 Y123.72 E.96469

G1 X104.616 Y144.933 E.96469
M204 S10000
G1 Z1.05 F30000
G1 E-.8 F1800
G1 X105.192 Y102.507 F30000
G1 E.8 F1800
G1 Z.85 F30000
G1 F6960
M204 S5000
G1 X126.405 Y123.72 E.96469

G1 X105.192 Y144.933 E.96469
M204 S10000
G1 Z1.05 F30000
G1 E-.8 F1800
G1 X107.642 Y102.507 F30000
G1 E.8 F1800
G1 Z.85 F30000
M400
 M900 K0.015; Override pressure advance value
G1 F6960
M204 S5000
G1 X128.855 Y123.72 E.96469

G1 X107.642 Y144.933 E.96469
M204 S10000
G1 Z1.05 F30000
M73 P93 R0
G1 E-.8 F1800
G1 X108.217 Y102.507 F30000
G1 E.8 F1800
G1 Z.85 F30000
G1 F6960
M204 S5000
G1 X129.431 Y123.72 E.96469

G1 X108.217 Y144.933 E.96469
M204 S10000
G1 Z1.05 F30000
G1 E-.8 F1800
G1 X108.793 Y102.507 F30000
G1 E.8 F1800
G1 Z.85 F30000
G1 F6960
M204 S5000
G1 X130.006 Y123.72 E.96469

G1 X108.793 Y144.933 E.96469
M204 S10000
G1 Z1.05 F30000
G1 E-.8 F1800
G1 X111.243 Y102.507 F30000
G1 E.8 F1800
G1 Z.85 F30000
M400
 M900 K0.02; Override pressure advance value
G1 F6960
M204 S5000
G1 X132.456 Y123.72 E.96469

G1 X111.243 Y144.933 E.96469
M204 S10000
G1 Z1.05 F30000
G1 E-.8 F1800
G1 X111.819 Y102.507 F30000
G1 E.8 F1800
G1 Z.85 F30000
G1 F6960
M204 S5000
G1 X133.032 Y123.72 E.96469

G1 X111.819 Y144.933 E.96469
M204 S10000
G1 Z1.05 F30000
M73 P94 R0
G1 E-.8 F1800
G1 X112.395 Y102.507 F30000
G1 E.8 F1800
G1 Z.85 F30000
G1 F6960
M204 S5000
G1 X133.608 Y123.72 E.96469

G1 X112.395 Y144.933 E.96469
M204 S10000
G1 Z1.05 F30000
G1 E-.8 F1800
G1 X114.845 Y102.507 F30000
G1 E.8 F1800
G1 Z.85 F30000
M400
 M900 K0.025; Override pressure advance value
G1 F6960
M204 S5000
G1 X136.058 Y123.72 E.96469

G1 X114.845 Y144.933 E.96469
M204 S10000
G1 Z1.05 F30000
G1 E-.8 F1800
G1 X115.42 Y102.507 F30000
G1 E.8 F1800
G1 Z.85 F30000
G1 F6960
M204 S5000
G1 X136.633 Y123.72 E.96469

G1 X115.42 Y144.933 E.96469
M204 S10000
G1 Z1.05 F30000
G1 E-.8 F1800
G1 X115.996 Y102.507 F30000
G1 E.8 F1800
G1 Z.85 F30000
G1 F6960
M204 S5000
G1 X137.209 Y123.72 E.96469

G1 X115.996 Y144.933 E.96469
M204 S10000
G1 Z1.05 F30000
G1 E-.8 F1800
G1 X118.446 Y102.507 F30000
G1 E.8 F1800
G1 Z.85 F30000
M400
 M900 K0.03; Override pressure advance value
G1 F6960
M204 S5000
G1 X139.659 Y123.72 E.96469

G1 X118.446 Y144.933 E.96469
M204 S10000
G1 Z1.05 F30000
G1 E-.8 F1800
G1 X119.022 Y102.507 F30000
G1 E.8 F1800
G1 Z.85 F30000
G1 F6960
M204 S5000
G1 X140.235 Y123.72 E.96469

G1 X119.022 Y144.933 E.96469
M204 S10000
G1 Z1.05 F30000
G1 E-.8 F1800
G1 X119.597 Y102.507 F30000
G1 E.8 F1800
G1 Z.85 F30000
G1 F6960
M204 S5000
G1 X140.811 Y123.72 E.96469

G1 X119.597 Y144.933 E.96469
M204 S10000
G1 Z1.05 F30000
G1 E-.8 F1800
G1 X122.047 Y102.507 F30000
G1 E.8 F1800
G1 Z.85 F30000
M400
 M900 K0.035; Override pressure advance value
G1 F6960
M204 S5000
G1 X143.261 Y123.72 E.96469

G1 X122.047 Y144.933 E.96469
M204 S10000
G1 Z1.05 F30000
M73 P95 R0
G1 E-.8 F1800
G1 X122.623 Y102.507 F30000
G1 E.8 F1800
G1 Z.85 F30000
G1 F6960
M204 S5000
G1 X143.836 Y123.72 E.96469

G1 X122.623 Y144.933 E.96469
M204 S10000
G1 Z1.05 F30000
G1 E-.8 F1800
G1 X123.199 Y102.507 F30000
G1 E.8 F1800
G1 Z.85 F30000
G1 F6960
M204 S5000
G1 X144.412 Y123.72 E.96469

G1 X123.199 Y144.933 E.96469
M204 S10000
G1 Z1.05 F30000
G1 E-.8 F1800
G1 X125.649 Y102.507 F30000
G1 E.8 F1800
G1 Z.85 F30000
M400
 M900 K0.04; Override pressure advance value
G1 F6960
M204 S5000
G1 X146.862 Y123.72 E.96469

G1 X125.649 Y144.933 E.96469
M204 S10000
G1 Z1.05 F30000
G1 E-.8 F1800
G1 X126.224 Y102.507 F30000
G1 E.8 F1800
G1 Z.85 F30000
G1 F6960
M204 S5000
G1 X147.438 Y123.72 E.96469

G1 X126.224 Y144.933 E.96469
M204 S10000
G1 Z1.05 F30000
G1 E-.8 F1800
G1 X126.8 Y102.507 F30000
G1 E.8 F1800
G1 Z.85 F30000
G1 F6960
M204 S5000
G1 X148.013 Y123.72 E.96469

G1 X126.8 Y144.933 E.96469
M204 S10000
G1 Z1.05 F30000
G1 E-.8 F1800
G1 X129.25 Y102.507 F30000
G1 E.8 F1800
G1 Z.85 F30000
M400
 M900 K0.045; Override pressure advance value
G1 F6960
M204 S5000
G1 X150.463 Y123.72 E.96469

G1 X129.25 Y144.933 E.96469
M204 S10000
G1 Z1.05 F30000
G1 E-.8 F1800
G1 X129.826 Y102.507 F30000
G1 E.8 F1800
G1 Z.85 F30000
G1 F6960
M204 S5000
G1 X151.039 Y123.72 E.96469

G1 X129.826 Y144.933 E.96469
M204 S10000
G1 Z1.05 F30000
G1 E-.8 F1800
G1 X130.402 Y102.507 F30000
G1 E.8 F1800
G1 Z.85 F30000
G1 F6960
M204 S5000
G1 X151.615 Y123.72 E.96469

G1 X130.402 Y144.933 E.96469
M204 S10000
G1 Z1.05 F30000
M73 P96 R0
G1 E-.8 F1800
G1 X132.852 Y102.507 F30000
G1 E.8 F1800
G1 Z.85 F30000
M400
 M900 K0.05; Override pressure advance value
G1 F6960
M204 S5000
G1 X154.065 Y123.72 E.96469

G1 X132.852 Y144.933 E.96469
M204 S10000
G1 Z1.05 F30000
G1 E-.8 F1800
G1 X133.427 Y102.507 F30000
G1 E.8 F1800
G1 Z.85 F30000
G1 F6960
M204 S5000
G1 X154.64 Y123.72 E.96469

G1 X133.427 Y144.933 E.96469
M204 S10000
G1 Z1.05 F30000
G1 E-.8 F1800
G1 X134.003 Y102.507 F30000
G1 E.8 F1800
G1 Z.85 F30000
G1 F6960
M204 S5000
G1 X155.216 Y123.72 E.96469

G1 X134.003 Y144.933 E.96469
M400
 M900 K0; Override pressure advance value
; end pressure advance pattern for layer

; OBJECT_ID: 282
G1 E-.8 F1800
G17
G3 Z1.05 I-.87 J.85 P1  F30000
G1 X99.055 Y98.297 Z1.05
G1 Z.85
G1 E.8 F1800
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F7001.174
M204 S5000
G1 X94.475 Y98.297 E.13642
G1 X94.475 Y93.717 E.13642
G1 X99.055 Y93.717 E.13642
G1 X99.055 Y98.237 E.13464
;========Date 20250206========
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
 ; timelapse without wipe tower
M971 S11 C10 O0
M1004 S5 P1  ; external shutter

M623
; SKIPPABLE_END
M204 S10000
G1 X98.847 Y97.39 F30000
; FEATURE: Top surface
G1 F7001.174
M204 S2000
G1 X98.148 Y98.089 E.02945
G1 X97.615 Y98.089
G1 X98.847 Y96.857 E.05191
G1 X98.847 Y96.324
G1 X97.082 Y98.089 E.07438
G1 X96.549 Y98.089
G1 X98.847 Y95.791 E.09684
G1 X98.847 Y95.257
G1 X96.015 Y98.089 E.1193
G1 X95.482 Y98.089
G1 X98.847 Y94.724 E.14177
G1 X98.847 Y94.191
G1 X94.949 Y98.089 E.16423
G1 X94.682 Y97.823
G1 X98.581 Y93.924 E.16423
G1 X98.048 Y93.924
G1 X94.682 Y97.289 E.14176
G1 X94.682 Y96.756
G1 X97.514 Y93.924 E.1193
G1 X96.981 Y93.924
G1 X94.682 Y96.223 E.09684
G1 X94.682 Y95.69
G1 X96.448 Y93.924 E.07437
G1 X95.915 Y93.924
G1 X94.682 Y95.156 E.05191
G1 X94.682 Y94.623
G1 X95.381 Y93.924 E.02945
; close powerlost recovery
M1003 S0
; WIPE_START
G1 F7001.174
M204 S10000
G1 X94.682 Y94.623 E-.37565
M73 P97 R0
G1 X94.682 Y95.156 E-.20264
G1 X95.02 Y94.818 E-.18171
; WIPE_END
G1 E-.04 F1800
G17
G3 Z1.25 I1.217 J0 P1  F30000
M106 S0
M106 P2 S0
M981 S0 P20000 ; close spaghetti detector
; FEATURE: Custom
; MACHINE_END_GCODE_START
; filament end gcode 

;===== date: 20230428 =====================
M400 ; wait for buffer to clear
G92 E0 ; zero the extruder
G1 E-0.8 F1800 ; retract
G1 Z1.35 F900 ; lower z a little
G1 X65 Y245 F12000 ; move to safe pos 
G1 Y265 F3000

G1 X65 Y245 F12000
G1 Y265 F3000
M140 S0 ; turn off bed
M106 S0 ; turn off fan
M106 P2 S0 ; turn off remote part cooling fan
M106 P3 S0 ; turn off chamber cooling fan

G1 X100 F12000 ; wipe
; pull back filament to AMS
M620 S255
G1 X20 Y50 F12000
G1 Y-3
T255
G1 X65 F12000
G1 Y265
G1 X100 F12000 ; wipe
M621 S255
M104 S0 ; turn off hotend

M622.1 S1 ; for prev firware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
    M400 ; wait all motion done
    M991 S0 P-1 ;end smooth timelapse at safe pos
    M400 S3 ;wait for last picture to be taken
M623; end of "timelapse_record_flag"

M400 ; wait all motion done
M17 S
M17 Z0.4 ; lower z motor current to reduce impact if there is something in the bottom

    G1 Z100.85 F600
    G1 Z98.85

M400 P100
M17 R ; restore z current

M220 S100  ; Reset feedrate magnitude
M201.2 K1.0 ; Reset acc magnitude
M73.2   R1.0 ;Reset left time magnitude
M1002 set_gcode_claim_speed_level : 0

M17 X0.8 Y0.8 Z0.5 ; lower motor current to 45% power
M73 P100 R0
; EXECUTABLE_BLOCK_END

