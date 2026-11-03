# Shipped resources (`sightlab_resources/`)

Generated 2026-10-31T21:03Z by `tools/gen_resources.py` from the SightLab 2 resource folder; names only.
Load an environment with `vizfx.addChild('sightlab_resources/environments/<name>')` and an object with
`vizfx.addChild('sightlab_resources/objects/<name>')`. Use the spelling shown here: the shipped
files are found through the Windows file system, which forgives case, but the GUI lists and any
case-sensitive copy of the resources do not.
A file not listed here does not ship; use a primitive or the researcher's own model instead.

Sizes are bounding boxes in metres (width × height × depth) measured in Vizard on 2026-10-31T21:00Z.
The models are built at real-world size unless the table says otherwise; pick by class: **hand-held**
(longest side ≤ 0.35 m) for things held, grabbed or set out on a table, **table-top** (≤ 0.8 m),
**large** (furniture, vehicles, rooms). To change a size, `setScale` once, to the size the brief
implies, and record it in the brief. `bottom` is the lowest point relative to the model's own
origin: to stand a model on a surface at height h, set its y to `h - bottom`. The centre may be
off the origin (for example `Table.osgb`), so place by the listed centre, not by the origin.

## environments

29 files.

| file | w × h × d (m) | floor y (m) | centre (x, y, z) |
|---|---|---|---|
| `Business_Office.OSGB` | 500.00 × 500.00 × 500.00 | -250.00 | 0.00, 0.00, -0.00 |
| `complete_scene.osgb` | 13.25 × 7.57 × 13.25 | -1.53 | 0.36, 2.26, -0.28 |
| `dojo.osgb` | 19.19 × 9.06 × 22.86 | -0.16 | -0.03, 4.37, 0.03 |
| `dojo2.osgb` | 16.27 × 8.57 × 17.86 | -0.14 | -0.10, 4.15, -0.11 |
| `dojo2_empty.osgb` | 613.24 × 310.41 × 613.24 | -95.36 | 0.00, 59.85, 0.00 |
| `empty.osgb` | -1.00 × -1.00 × -1.00 | 0.50 | 0.00, 0.00, -0.00 |
| `gallery_paintings.osgb` | 21.61 × 7.00 × 22.21 | -0.42 | 0.00, 3.08, 2.53 |
| `homeOffice.osgb` | 5.08 × 4.07 × 6.34 | -0.06 | 0.33, 1.97, -0.20 |
| `Interior_Empty.osgb` | 15.41 × 3.56 × 15.41 | -0.30 | -0.21, 1.48, 1.41 |
| `jeepmodel.osgb` | 11.78 × 9.81 × 15.13 | -4.18 | 0.47, 0.72, -0.00 |
| `lab_empty.osgb` | 13.08 × 7.26 × 13.01 | -0.00 | 0.08, 3.63, 0.87 |
| `Lecture.osgb` | 16.88 × 8.06 × 23.79 | -1.90 | 0.00, 2.13, -0.20 |
| `Lecture_Hall_Dark_Template.osgb` | 16.88 × 8.06 × 23.79 | -1.90 | 0.00, 2.13, -0.20 |
| `maze.osgb` | 25.02 × 8.34 × 25.04 | -0.33 | -0.00, 3.85, -0.02 |
| `medical_examination_room.osgb` | 3.99 × 3.10 × 3.28 | -0.20 | -0.83, 1.35, 0.51 |
| `modern_office_skyline.osgb` | 7.65 × 3.66 × 9.10 | -0.04 | -0.12, 1.79, -0.58 |
| `Piazza_empty.osgb` | 613.24 × 310.41 × 613.24 | -95.36 | 0.00, 59.85, 0.00 |
| `pit2.osgb` | 25.02 × 19.35 × 25.04 | -8.19 | 0.34, 1.48, 2.29 |
| `pit_raised.osgb` | 25.02 × 19.16 × 25.04 | -15.64 | 0.34, -6.06, 0.86 |
| `RockyCavern.osgb` | 613.24 × 310.41 × 613.24 | -95.36 | 0.00, 59.85, 0.00 |
| `RockyCavern_Night.osgb` | 50.92 × 13.24 × 90.87 | -0.05 | 9.81, 6.57, -21.43 |
| `ShowRoom_empty.osgb` | 500.00 × 500.00 × 500.00 | -250.00 | 0.00, 0.00, -0.00 |
| `ShowRoom_standin_avatar.osgb` | 500.00 × 500.00 × 500.00 | -250.00 | 0.00, 0.00, -0.00 |
| `Stimulus.osgb` | 8.07 × 6.19 × 10.97 | -1.39 | -1.43, 1.71, -1.15 |
| `street_day.osgb` | 613.24 × 310.41 × 613.24 | -95.36 | 0.00, 59.85, 0.00 |
| `van_gogh_room.osgb` | 3.54 × 4.80 × 6.77 | -0.96 | 0.39, 1.44, -0.01 |
| `waiting_room.osgb` | 9.75 × 5.00 × 10.34 | 0.00 | 0.52, 2.50, -1.08 |
| `whiteroom.osgb` | 5.00 × 5.00 × 6.59 | 0.00 | -0.00, 2.50, 0.80 |
| `whiteroom_clear.osgb` | 24.66 × 5.00 × 6.59 | 0.00 | 0.00, 2.50, 0.80 |

## objects

70 files.

| file | w × h × d (m) | class | bottom (m) | centre (x, y, z) |
|---|---|---|---|---|
| `3D_Video_Screen.osgb` | 1.29 × 0.73 × 0.13 | large | 1.01 | 0.00, 1.38, 0.63 |
| `Baseball.osgb` | 0.21 × 0.20 × 0.20 | hand-held | -0.01 | 0.01, 0.09, 0.04 |
| `basketball.osgb` | 0.34 × 0.28 × 0.32 | hand-held | -0.14 | 0.00, 0.00, -0.00 |
| `beer.osgb` | 0.08 × 0.30 × 0.08 | hand-held | 0.00 | 0.00, 0.15, -0.00 |
| `box.osgb` | 0.73 × 0.57 × 0.73 | table-top | -0.02 | 0.03, 0.27, -0.21 |
| `button_target.osgb` | 0.10 × 0.06 × 0.00 | hand-held | -0.02 | -0.01, 0.01, 0.00 |
| `car.osgb` | 1.86 × 1.51 × 5.32 | large | -0.02 | -0.01, 0.73, -0.22 |
| `chair.osgb` | 0.72 × 0.97 × 0.76 | large | 0.00 | -0.03, 0.48, 0.04 |
| `chick.osgb` | 0.54 × 0.54 × 0.56 | table-top | -0.01 | 0.02, 0.26, -0.03 |
| `cigs.osgb` | 0.10 × 0.18 × 0.10 | hand-held | -0.00 | 0.00, 0.09, 0.05 |
| `Client_Start_Group.osgb` | 3.31 × 1.68 × 2.23 | large | 0.01 | -0.10, 0.85, -4.68 |
| `computer_monitor.osgb` | 0.75 × 0.57 × 0.22 | table-top | 0.00 | -0.00, 0.29, 0.10 |
| `crate.osgb` | 0.49 × 0.49 × 0.49 | table-top | -0.02 | 0.00, 0.23, -0.00 |
| `Creature.osgb` | 0.80 × 0.88 × 0.81 | large | -0.04 | 0.02, 0.40, 0.05 |
| `direction_arrow.osgb` | 0.16 × 2.13 × 1.51 | large | -1.32 | 0.06, -0.25, -0.08 |
| `Directional_Day_Light.osgb` | -1.00 × -1.00 × -1.00 | hand-held | 0.50 | 0.00, 0.00, -0.00 |
| `empty.osgb` | -1.00 × -1.00 × -1.00 | hand-held | 0.50 | 0.00, 0.00, -0.00 |
| `empty_collideBox.osgb` | 11.78 × 9.81 × 15.13 | large | -4.18 | 0.47, 0.72, -0.00 |
| `empty_XR.osgb` | 0.65 × 0.65 × 0.65 | table-top | -0.33 | 0.00, 0.00, -0.00 |
| `fire.osgb` | 8.00 × 2.00 × 0.00 | large | -1.00 | 3.00, 0.00, -0.00 |
| `flashlight.osgb` | 0.07 × 0.08 × 0.24 | hand-held | 0.21 | -0.00, 0.25, 0.21 |
| `glaucoma_artifact.osgb` | 0.36 × 0.31 × 0.00 | table-top | -0.18 | 0.00, -0.03, 0.01 |
| `ground.osgb` | 50.00 × 0.00 × 50.00 | large | 0.00 | 0.00, 0.00, -0.00 |
| `guitar.osgb` | 0.42 × 1.26 × 0.19 | large | -0.08 | -0.00, 0.55, -0.00 |
| `jeepmodel.osgb` | 2.19 × 2.31 × 4.38 | large | -0.04 | 0.46, 1.12, 0.43 |
| `LargeScreen.osgb` | 9.58 × 5.41 × 0.35 | large | 0.26 | 0.24, 2.96, 1.61 |
| `left_headlight.osgb` | 0.28 × 0.31 × 0.94 | large | 0.48 | -0.03, 0.63, 1.79 |
| `LeftQuestPro_controls.osgb` | 0.05 × 0.04 × 0.07 | hand-held | -0.03 | 0.01, -0.01, -0.01 |
| `leftShoe.osgb` | 0.33 × 0.31 × 0.33 | hand-held | -0.10 | 0.05, 0.05, -0.06 |
| `light_point.osgb` | -1.00 × -1.00 × -1.00 | hand-held | 0.50 | 0.00, 0.00, -0.00 |
| `meditation_ball.osgb` | 0.63 × 0.63 × 0.63 | table-top | 1.17 | 0.00, 1.48, 1.06 |
| `mirror.osgb` | 0.81 × 2.01 × 0.00 | large | 0.26 | 0.02, 1.27, 1.58 |
| `pigeon.osgb` | 0.25 × 0.32 × 0.33 | hand-held | -0.02 | -0.03, 0.14, -0.04 |
| `Plant.osgb` | 0.57 × 0.81 × 0.64 | large | 0.85 | 1.76, 1.26, 0.87 |
| `proximity_area.osgb` | 5.05 × 0.65 × 1.06 | large | -0.33 | 0.00, 0.00, -0.00 |
| `pug_AI_Generated.osgb` | 0.28 × 0.38 × 0.28 | table-top | -0.06 | 0.00, 0.13, 0.01 |
| `pug_AI_Generated2.osgb` | 0.41 × 0.56 × 0.62 | table-top | -0.01 | -0.00, 0.27, 0.01 |
| `ramp.osgb` | 2.78 × 3.14 × 4.88 | large | 0.00 | -0.00, 1.57, 3.32 |
| `RegionOfInterest.osgb` | 0.65 × 0.65 × 0.65 | table-top | -0.33 | 0.00, 0.00, -0.00 |
| `RegionOfInterest2.osgb` | 0.65 × 0.65 × 0.65 | table-top | -0.33 | 0.00, 0.00, -0.00 |
| `RegionOfInterestSphere.osgb` | 1.26 × 1.26 × 1.27 | large | -0.63 | 0.00, 0.00, -0.00 |
| `reset_text.osgb` | 3.50 × 1.17 × 0.00 | large | -0.25 | 1.67, 0.33, -0.00 |
| `right_headlight.osgb` | 0.28 × 0.31 × 0.94 | large | 0.48 | 0.97, 0.63, 1.78 |
| `RightQuestPro_controls.osgb` | 0.04 × 0.05 × 0.07 | hand-held | -0.03 | 0.00, -0.01, -0.01 |
| `rightShoe.osgb` | 0.33 × 0.29 × 0.34 | hand-held | -0.15 | -0.04, -0.01, -0.07 |
| `RulerTripod.osgb` | 0.28 × 2.10 × 0.25 | large | 0.00 | -0.00, 1.05, 0.04 |
| `salad_luma_labs.osgb` | 0.80 × 0.85 × 1.00 | large | -0.41 | 0.01, 0.01, -0.00 |
| `sceneController.osgb` | 0.23 × 0.21 × 0.12 | hand-held | -0.12 | -0.03, -0.02, -0.00 |
| `screen.osgb` | 0.89 × 0.55 × 0.04 | large | 0.91 | 0.08, 1.18, 0.92 |
| `screen2.osgb` | 0.78 × 0.48 × 0.03 | table-top | -0.26 | 0.00, -0.02, 0.01 |
| `screen_dome.osgb` | 0.86 × 0.86 × 0.34 | large | 1.22 | 0.00, 1.65, 0.37 |
| `screen_hmd.osgb` | 1.40 × 1.11 × 0.08 | large | 0.70 | 0.05, 1.25, 0.94 |
| `SIGHTLAB_START_POINT.osgb` | 0.68 × 1.68 × 0.62 | large | 0.01 | 0.14, 0.85, 0.07 |
| `SIGHTLAB_START_POINT_CLIENT.osgb` | 0.68 × 1.68 × 0.62 | large | 0.01 | 0.14, 0.85, 0.07 |
| `SimpleBlanket.osgb` | 2.84 × 0.03 × 2.17 | large | 0.01 | 0.14, 0.02, 0.02 |
| `sky_day.osgb` | 613.24 × 310.41 × 613.24 | large | -95.36 | 0.00, 59.85, 0.00 |
| `sky_night.osgb` | 613.24 × 298.50 × 613.24 | large | -66.25 | 0.00, 83.00, 0.00 |
| `soccerball.osgb` | 0.22 × 0.22 × 0.22 | hand-held | -0.11 | -0.00, -0.00, -0.00 |
| `standInAvatar.osgb` | 0.68 × 1.68 × 0.62 | large | 0.08 | 0.14, 0.92, 0.07 |
| `startPoint.osgb` | 0.68 × 1.68 × 0.62 | large | 0.08 | 0.14, 0.92, 0.07 |
| `stunt_ramp2.osgb` | 71.96 × 31.32 × 88.62 | large | -0.89 | -32.42, 14.77, 44.86 |
| `Table.osgb` | 1.20 × 0.57 × 0.75 | large | -0.01 | 0.00, 0.28, 0.88 |
| `tablet.osgb` | 0.33 × 0.06 × 0.17 | hand-held | 0.06 | -0.04, 0.09, -0.00 |
| `targetObject2.osgb` | 0.42 × 0.42 × 0.01 | table-top | -0.21 | 0.00, -0.00, -0.00 |
| `toy_spaceship.osgb` | 0.38 × 0.25 × 0.41 | table-top | -0.00 | -0.01, 0.13, 0.00 |
| `TV_Object.osgb` | 1.46 × 0.88 × 0.09 | large | -0.11 | 0.09, 0.33, -0.02 |
| `TV_Stand.osgb` | 1.46 × 2.08 × 0.19 | large | 0.00 | -0.06, 1.04, -0.04 |
| `volleyball.osgb` | 0.22 × 0.22 × 0.22 | hand-held | -0.11 | 0.00, 0.00, 0.00 |
| `VR_Menu.osgb` | 0.60 × 0.48 × 0.01 | table-top | -0.33 | 0.00, -0.09, -0.01 |
| `XR_Ground.osgb` | 26.27 × 0.34 × 31.46 | large | -0.48 | 0.00, -0.31, -0.00 |

## scene_objects

4 files.

| file | w × h × d (m) | class | bottom (m) | centre (x, y, z) |
|---|---|---|---|---|
| `RegionOfInterest.osgb` | 0.65 × 0.65 × 0.65 | table-top | -0.33 | 0.00, 0.00, -0.00 |
| `SIGHTLAB_START_POINT.osgb` | 0.68 × 1.68 × 0.62 | large | 0.01 | 0.14, 0.85, 0.07 |
| `SIGHTLAB_START_POINT_CLIENT.osgb` | 0.68 × 1.68 × 0.62 | large | 0.01 | 0.14, 0.85, 0.07 |
| `standInAvatar.osgb` | 0.68 × 1.68 × 0.62 | large | 0.08 | 0.14, 0.92, 0.07 |

## avatar

119 files.

`Complete Character/000_invisible.tga`, `Complete Character/Anim/CC2_mHigh_m_ascendstairs_inplace.CAF`, `Complete Character/Anim/CC2_mHigh_m_dancing_neutral_A0.CAF`, `Complete Character/Anim/CC2_mHigh_m_descendstairs_inplace.CAF`, `Complete Character/Anim/CC2_mHigh_m_gestic_listen_left_01.CAF`, `Complete Character/Anim/CC2_mHigh_m_gestic_listen_left_01b.CAF`, `Complete Character/Anim/CC2_mHigh_m_gestic_listen_neutral_01.CAF`, `Complete Character/Anim/CC2_mHigh_m_gestic_listen_neutral_02.CAF`, `Complete Character/Anim/CC2_mHigh_m_gestic_listen_neutral_03.CAF`, `Complete Character/Anim/CC2_mHigh_m_gestic_listen_right_01.CAF`, `Complete Character/Anim/CC2_mHigh_m_gestic_talk_neutral_01.CAF`, `Complete Character/Anim/CC2_mHigh_m_gestic_talk_neutral_01_A0.CAF`, `Complete Character/Anim/CC2_mHigh_m_gestic_talk_neutral_02.CAF`, `Complete Character/Anim/CC2_mHigh_m_gestic_talk_neutral_03.CAF`, `Complete Character/Anim/CC2_mHigh_m_gestic_talk_neutral_04.CAF`, `Complete Character/Anim/CC2_mHigh_m_gestic_talk_neutral_05.CAF`, `Complete Character/Anim/CC2_mHigh_m_idle_breathe_01.CAF`, `Complete Character/Anim/CC2_mHigh_m_idle_breathe_02.CAF`, `Complete Character/Anim/CC2_mHigh_m_idle_breathe_03.CAF`, `Complete Character/Anim/CC2_mHigh_m_idle_look_around_01.CAF`, `Complete Character/Anim/CC2_mHigh_m_idle_look_around_02.CAF`, `Complete Character/Anim/CC2_mHigh_m_idle_look_around_03.CAF`, `Complete Character/Anim/CC2_mHigh_m_idle_neutral_01.CAF`, `Complete Character/Anim/CC2_mHigh_m_idle_neutral_01_A0.CAF`, `Complete Character/Anim/CC2_mHigh_m_idle_neutral_02.CAF`, `Complete Character/Anim/CC2_mHigh_m_idle_neutral_03.CAF`, `Complete Character/Anim/CC2_mHigh_m_idle_neutral_04.CAF`, `Complete Character/Anim/CC2_mHigh_m_idle_neutral_05.CAF`, `Complete Character/Anim/CC2_mHigh_m_idle_neutral_06.CAF`, `Complete Character/Anim/CC2_mHigh_m_idle_neutral_07.CAF`, `Complete Character/Anim/CC2_mHigh_m_idle_neutral_08.CAF`, `Complete Character/Anim/CC2_mHigh_m_idle_neutral_09.CAF`, `Complete Character/Anim/CC2_mHigh_m_idle_neutral_10.CAF`, `Complete Character/Anim/CC2_mHigh_m_run_neutral_01_inplace.CAF`, `Complete Character/Anim/CC2_mHigh_m_run_neutral_01_inplace_A0.CAF`, `Complete Character/Anim/CC2_mHigh_m_run_neutral_02_inplace.CAF`, `Complete Character/Anim/CC2_mHigh_m_run_start_inplace.CAF`, `Complete Character/Anim/CC2_mHigh_m_run_stop_inplace.CAF`, `Complete Character/Anim/CC2_mHigh_m_run_to_walk_inplace.CAF`, `Complete Character/Anim/CC2_mHigh_m_sit_chair_breathe_01.CAF`, `Complete Character/Anim/CC2_mHigh_m_sit_chair_gestic_thoughtful.CAF`, `Complete Character/Anim/CC2_mHigh_m_sit_chair_idle_look_around.CAF`, `Complete Character/Anim/CC2_mHigh_m_sit_chair_idle_neutral_01.CAF`, `Complete Character/Anim/CC2_mHigh_m_sit_chair_idle_neutral_01_A0.CAF`, `Complete Character/Anim/CC2_mHigh_m_sit_chair_idle_neutral_02.CAF`, `Complete Character/Anim/CC2_mHigh_m_sit_down_chair_01.CAF`, `Complete Character/Anim/CC2_mHigh_m_sit_down_chair_02.CAF`, `Complete Character/Anim/CC2_mHigh_m_sit_down_chair_left.CAF`, `Complete Character/Anim/CC2_mHigh_m_sit_down_chair_right.CAF`, `Complete Character/Anim/CC2_mHigh_m_sit_down_table_left.CAF`, `Complete Character/Anim/CC2_mHigh_m_sit_down_table_right.CAF`, `Complete Character/Anim/CC2_mHigh_m_sit_stand_up_chair_01.CAF`, `Complete Character/Anim/CC2_mHigh_m_sit_stand_up_chair_left.CAF`, `Complete Character/Anim/CC2_mHigh_m_sit_stand_up_chair_right.CAF`, `Complete Character/Anim/CC2_mHigh_m_sit_stand_up_table_left.CAF`, `Complete Character/Anim/CC2_mHigh_m_sit_stand_up_table_right.CAF`, `Complete Character/Anim/CC2_mHigh_m_sit_table_breathe_01.CAF`, `Complete Character/Anim/CC2_mHigh_m_sit_table_gestic_thoughtful.CAF`, `Complete Character/Anim/CC2_mHigh_m_sit_table_idle_look_around.CAF`, `Complete Character/Anim/CC2_mHigh_m_sit_table_idle_neutral_01.CAF`, `Complete Character/Anim/CC2_mHigh_m_sit_table_idle_neutral_01_A0.CAF`, `Complete Character/Anim/CC2_mHigh_m_sit_table_idle_neutral_02.CAF`, `Complete Character/Anim/CC2_mHigh_m_strafe_l_inplace.CAF`, `Complete Character/Anim/CC2_mHigh_m_strafe_r_inplace.CAF`, `Complete Character/Anim/CC2_mHigh_m_turn_left_120.CAF`, `Complete Character/Anim/CC2_mHigh_m_turn_left_180.CAF`, `Complete Character/Anim/CC2_mHigh_m_turn_left_60.CAF`, `Complete Character/Anim/CC2_mHigh_m_turn_left_90.CAF`, `Complete Character/Anim/CC2_mHigh_m_turn_right_120.CAF`, `Complete Character/Anim/CC2_mHigh_m_turn_right_180.CAF`, `Complete Character/Anim/CC2_mHigh_m_turn_right_60.CAF`, `Complete Character/Anim/CC2_mHigh_m_turn_right_90.CAF`, `Complete Character/Anim/CC2_mHigh_m_walk_neutral_01_inplace.CAF`, `Complete Character/Anim/CC2_mHigh_m_walk_neutral_01_inplace_A0.CAF`, `Complete Character/Anim/CC2_mHigh_m_walk_neutral_02_inplace.CAF`, `Complete Character/Anim/CC2_mHigh_m_walk_neutral_03_inplace.CAF`, `Complete Character/Anim/motive.caf`, `Complete Character/Anim/motive10.caf`, `Complete Character/Anim/motive11.caf`, `Complete Character/Anim/motive2.caf`, `Complete Character/Anim/motive3.caf`, `Complete Character/Anim/motive5.caf`, `Complete Character/Anim/motive6.caf`, `Complete Character/Anim/motive7.caf`, `Complete Character/Anim/motive8.caf`, `Complete Character/Anim/motive9.caf`, `Complete Character/Anim/motive_export.caf`, `Complete Character/Anim/motive_new2.caf`, `Complete Character/Anim/motive_test.caf`, `Complete Character/CC2_m001_hipoly_A1.cfg`, `Complete Character/m001_body_color.tga`, `Complete Character/m001_head_color.tga`, `Complete Character/Material/CC2_m001_hipoly_1.CRF`, `Complete Character/Material/CC2_m001_hipoly_2.CRF`, `Complete Character/Mesh/CC2_m001_hipoly.CMF`, `Complete Character/Skel/CC2_mHigh_Skeleton.CSF`, `full_body/ReadyPlayerMe.osgb`, `full_body/ReadyPlayerMe_Female.osgb`, `full_body/ReadyPlayerMe_Male2.osgb`, `full_body/ReadyPlayerMe_UpperBody.osgb`, `full_body/Reallusion_ActorCore_Male.osgb`, `full_body/RocketBox_Female1.osgb`, `full_body/RocketBox_Male1.osgb`, `full_body/Sado_Avaturn.osgb`, `full_body/vcc_female.cfg`, `full_body/vcc_male.cfg`, `full_body/vcc_male2.cfg`, `full_body/Woman_Avaturn.osgb`, `full_body/x_MixamoBot.osgb`, `full_body/x_MixamoBot_shiny.osgb`, `full_body/XR_Avatar_No_Head.osgb`, `full_body/XR_Hands_Only.osgb`, `TrackedAvatars/RocketBox_Female1.osgb`, `TrackedAvatars/RocketBox_Female2.osgb`, `TrackedAvatars/RocketBox_Male1.osgb`, `TrackedAvatars/RocketBox_Male2.osgb`, `TrackedAvatars/RocketBox_Male3.osgb`, `TrackedAvatars/WV_Mark.osgb`, `TrackedAvatars/z_ReadyPlayerMe_Female.osgb`

## media

9 files.

`01_Warehouse.avi`, `02_parking_lot.jpg`, `03_DRI.jpg`, `04_warehouse.jpg`, `football_pass.avi`, `realistic_new_york_skyline_daytime.jpg`, `skybox_oil.jpg`, `skybox_room1.jpg`, `skybox_room2.jpg`

## media_2D

4 files.

`black.jpg`, `droneShots.mp4`, `movie_cartoon-bird.wmv`, `SBS.mp4`

## audio

6 files.

`242739__marlonhj__engine-1.wav`, `beep.wav`, `block.wav`, `instructions.mp3`, `switch.wav`, `tada.wav`

## example_resources

22 files.

`audio/body_fall_thud.wav`, `audio/pit_fall.wav`, `audio/pit_running.wav`, `audio/pit_stop.wav`, `audio/pit_thud.wav`, `audio/platform_running.wav`, `audio/platform_stop.wav`, `complete_scene_lights_off.osgb`, `complete_scene_walls.osgb`, `dojo_bullseye.osgb`, `dojo_clear.osgb`, `empty_xr_cube.osgb`, `full_black.osgb`, `lab_collision.osgb`, `pit2.osgb`, `pit_drop.osgb`, `pit_raised.osgb`, `platform.osgb`, `street.osgb`, `XR_Avatar.osgb`, `XR_Real_World_Fixations.osgb`, `XR_virtual_screen.osgb`

## icons

37 files.

`__init__.py`, `add_icon.png`, `asset_browser_E4H_2.ico`, `attention_color_ramp.png`, `builder-icon.ico`, `builder.ico`, `client_6Gn_icon.ico`, `client_purple_zIA_icon.ico`, `coaster-client.ico`, `coaster-server.ico`, `delete.png`, `documentation.png`, `down_chevron.png`, `folder_icon.png`, `green_status.png`, `help_icon.png`, `inspector.ico`, `inspector2_1LR_3.ico`, `left_chevron.png`, `new/sightlab_new.ico`, `new/SR_Icon.png`, `plus_icon.png`, `red_status.png`, `refresh_color.png`, `refresh_icon.png`, `revert_icon.png`, `right_chevron.png`, `SR_Client_icon.ico`, `SR_Icon.png`, `sr_icon_I6G_icon.ico`, `SR_Replay_icon.png`, `sr_replay_icon_JPC_icon.ico`, `SR_Server_icon.ico`, `subtract_icon.png`, `up_chevron.png`, `zoom_in.png`, `zoom_out.png`

## (root)

6 files.

`Desktop_Controls.jpg`, `desktop_controls1.jpg`, `desktop_controls2.jpg`, `sightlab_controls.jpg`, `sightlab_controls_oculus.jpg`, `sightlab_controls_presenter.jpg`
