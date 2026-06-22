┌──────────────────────────────┐
│ Diver Wearable Unit Simulator│
│ - simulated depth            │
│ - simulated gas              │
│ - simulated motion           │
│ - simulated emergency button │
│ - local diver state          │
└───────────────┬──────────────┘
                │ DiverState packets
                ▼
┌──────────────────────────────┐
│ Underwater Communication Sim │
│ - latency                    │
│ - packet loss                │
│ - low bandwidth              │
│ - message priority           │
└───────────────┬──────────────┘
                │ delayed / noisy packets
                ▼
┌──────────────────────────────┐
│ Companion Robot Simulator    │
│ - receives diver state       │
│ - follows diver              │
│ - guides diver               │
│ - reacts to emergencies      │
│ - robot state machine        │
└───────────────┬──────────────┘
                │ robot + diver summaries
                ▼
┌──────────────────────────────┐
│ Surface Gateway Simulator    │
│ - represents buoy / boat     │
│ - relays robot/diver data    │
│ - sends operator commands    │
└───────────────┬──────────────┘
                │
                ▼
┌──────────────────────────────┐
│ Mission Backend              │
│ - telemetry ingestion        │
│ - mission state              │
│ - alarm evaluation           │
│ - command dispatch           │
│ - event logging              │
└───────────────┬──────────────┘
                │
                ▼
┌──────────────────────────────┐
│ Operator Dashboard           │
│ - diver status               │
│ - robot status               │
│ - alarms                     │
│ - mission timeline           │
│ - replay                     │
└──────────────────────────────┘
