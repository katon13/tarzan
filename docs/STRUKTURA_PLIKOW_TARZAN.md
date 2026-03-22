# STRUKTURA PLIKÓW TARZANA

```
/tarzan
│
├── main.py
├── TarzanRejestr.json
│
├── core/
│   ├── __init__.py
│   ├─# tarzanZmienneSygnalowe.py
│   ├─# tarzanUstawienia.py
│    └───# CZAS_PROBKOWANIA_MS
│   ├── tarzanMetodyZezwolenie.py
│   ├── tarzanLogger.py
│   ├── tarzanProtokolRuchu.py
│   ├── tarzanBledy.py
│   ├── tarzanStanyPracy.py
│   ├── tarzanSystem.py
│   └── tarzanController.py
│
├── hardware/
│   ├── __init__.py
│   ├─# tarzanPoKeysSetting.py
│   ├── tarzanPoKeysStart.py
│   ├── tarzanPoKeysLevels.py
│   ├── tarzanPoKeysPlay.py
│   ├── tarzanPoKeysRec.py
│   ├── tarzanPoStep25.py
│   ├── tarzanPoExtBus.py
│   ├── tarzanNextion70.py
│   ├── tarzanNextion50.py
│   ├── tarzanTFLuna.py
│   ├── tarzanPoSensors.py
│   ├── tarzanLCD1602.py
│   ├── tarzanMatrixLED8x8.py
│   ├── tarzanKlawiatura4x3.py
│   ├── tarzanPrzyciskiFunkcyjne.py
│   ├── tarzanSterownikSOK.py
│   ├── tarzanRRP.py
│   └── tarzanKameryUSB.py
│
├── mechanics/
│   ├── __init__.py
│   ├── tarzanAxis.py
│   ├── tarzanCameraHorizontal.py
│   ├── tarzanCameraVertical.py
│   ├── tarzanCameraTilt.py
│   ├── tarzanCameraFocus.py
│   ├── tarzanArmVertical.py
│   ├── tarzanArmHorizontal.py
│   ├── tarzanDronRelease.py
│   ├─# tarzanMechanikaOsi.py
│   └── tarzanRegulatorMasy.py
│
├── motion/
│   ├── __init__.py
│   ├─# tarzanTakeModel.py
│   ├── tarzanTakeRecorder.py
│   ├── tarzanTakePlayer.py
│   ├─# tarzanSegmentAnalyzer.py
│   ├─# tarzanKrzyweRuchu.py
│   ├── tarzanGhostMotion.py
│   ├── tarzanSmoothMotion.py
│   ├─# tarzanTimeline.py
│   ├─# tarzanSymulacjaRuchu.py
│   ├─# tarzanMechanicalValidator.py
│   ├─# tarzanStepGenerator.py
│   ├── tarzanGeneratorTAA.py
│   ├── motionPlanner.py
│   ├── motionProfile.py
│   └── homingManager.py
│
├── editor/
│   ├── __init__.py
│   ├── tarzanEdytorChoreografiiRuchu.py
│   ├── tarzanOknoTake.py
│   ├── tarzanWykresOsi.py
│   ├── tarzanPlayhead.py
│   ├── tarzanZoomTimeline.py
│   ├── tarzanKontrolkiTransportu.py
│   ├── tarzanEdycjaPunktow.py
│   └── tarzanPresetyWygladzania.py
│
├── config/
│   ├── __init__.py
│   └── tarzanMotionConfig.py
│
├── safety/
│   ├── __init__.py
│   ├── safetyManager.py
│   ├── limitsManager.py
│   └── faultManager.py
│
├── modes/
│   ├── __init__.py
│   ├── tarzanTrybBazowy.py
│   ├── tarzanTrybManual.py
│   ├── tarzanTrybManualAutoSupport.py
│   ├── tarzanTrybAllAuto.py
│   ├── tarzanTrybAutoTracking.py
│   ├── tarzanTrybAllAuto3D.py
│   ├── tarzanTrybAllAutoDron.py
│   ├── tarzanTrybAllAutoSpecialEffects.py
│   ├── tarzanTrybRecordMotion.py
│   └── tarzanTrybPlayMotion.py
│
├── audio/
│   ├── __init__.py
│   ├─# tarzanAudioPlayer.py
│   ├─# tarzanAudioCatalog.py
│   │
│   ├── voice/
│   │   ├─# Stay_clear.wav
│   │   ├─# Ready.wav
│   │   ├─# Step_away.wav
│   │   ├─# All_set.wav
│   │   ├─# Ready_to_record.wav
│   │   ├─# Prepared_to_play.wav
│   │   ├─# System_ready.wav
│   │   ├─# Recording_started.wav
│   │   ├─# Recording_finished.wav
│   │   ├─# Playback_ready.wav
│   │   ├─# Motion_starting.wav
│   │   ├─# Motion_stopped.wav
│   │   └─# Emergency_stop.wav
│   │
│   └── signals/
│       ├── beep_info.wav
│       ├── beep_action.wav
│       ├── beep_warning.wav
│       └── beep_emergency.wav
│
├── data/
│   ├── protokoly/
│   ├─# take/
│   ├── logi/
│   ├── presety/
│   └── matrix_led_wzory/
│ 
├── docs/
│   ├─# 
│   ├─# MAPA_PROJEKTU_TARZANA.md
│   ├─# STRUKTURA_PLIKOW_TARZAN.md
│   ├─# TARZAN_CHOREOGRAFIA_RUCHU_MAPA.md
│   ├─# TARZAN_CHOREOGRAFIA_RUCHU_MOEDEL_MATEMATYCZNY.md
│   ├─# TARZAN_SYSTEM_ARCHITECTURE.md
│   └─# 
│
└── presets/
    ├── __init__.py
    ├── presetManager.py
    ├── trajectories.py
    └── smoothingProfiles.py
```
