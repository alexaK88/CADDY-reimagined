┌────────────────────┐
│ ScenarioName        │
│ - normal            │
│ - low_gas           │
│ - fast_ascent       │
│ - emergency_button  │
└─────────┬──────────┘
          │ controls simulator behavior
          ▼
┌────────────────────┐
│ Simulator           │
└─────────┬──────────┘
          │ generates
          ▼
┌────────────────────────────┐
│ RawWearablePacket           │
│ - diver_id                  │
│ - sample_index              │
│ - elapsed_time_s            │
│ - produced_at_utc           │
│ - values                    │
│      └── RawSensorValues    │
└─────────┬──────────────────┘
          │ input to preprocessor
          | preprocessing
          ▼
┌────────────────────────────┐
│ CleanSensorPacket           │
│ - diver_id                  │
│ - sample_index              │
│ - elapsed_time_s            │
│ - produced_at_utc           │
│ - depth_m                   │
│ - tank_pressure_bar         │
│ - heading_deg               │
│ - motion_intensity          │
│ - battery_pct               │
│ - emergency_button_pressed  │
│ - ack_button_pressed        │
│ - link_quality              │
│ - ascent_rate_m_min         │
│ - gas_rate_bar_min          │
└────────────────────────────┘