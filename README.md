# CADDY-reimagined
Autonomous Diver Companion System for Underwater Guidance, Telemetry, and Safety Supervision.

## License and Use

This repository is public for visibility, review, and portfolio purposes.

It is **not open source**.

All rights are reserved. Use, copying, modification, redistribution, research use, commercial use, industrial use, or incorporation into another project requires prior written permission from the author.

If permission is granted, attribution must be given to Aleksandra Karpova and this repository.

For permission requests, contact: aleksandra.karpova042@gmail.com.

## Original idea
I came up with this idea of the robotic support underwater, some kind of the robot that keeps you save when you do the dive, sort to speak, and, while doing my research, found out that there was a research project called CADDY, which stands for Cognitive Autonomous Diving Buddy.
The idea was to create an innovative set-up between diver, underwater autonomous robot and whatever they are supposed to be communicating with on the surface. This set up was supposed to exhibit cognitive behaviour through learning, interpreting, and adapting to the diver's behaviour, physical state, and actions.

The system behind CADDY project had 3 roles:
1. observer (monitoring the diver)
2. slave (or extended hand, i.e., it was performing some tasks like taking photo, scanning area, etc.)
3. guide (leading diver through environment)

More can be found here: http://www.caddy-fp7.eu/web/66_76_0_-1_-1_-1_izbornik_default.aspx

## Project Status

This is currently a layered Python prototype of an autonomous diver companion system inspired by CADDY-like diver-support robotics. 
The goal is to simulate how diver safety data could move from a wearable unit, through an unreliable underwater communication layer, into robot-side decision logic, then up to a surface gateway and mission backend.

The current version focuses on software architecture, message flow, fault handling, and mission observability rather than physical robot control or full underwater physics.

## Implemented So Far
### Diver Wearable Simulation

The wearable-side module simulates raw diver sensor data for different mission scenarios. It produces raw wearable packets containing values such as depth, tank pressure, battery level, motion intensity, heading, emergency button state, acknowledgement button state, and communication link quality.

Implemented scenarios include normal diving, fast ascent, emergency button activation, weak or lost communication, low gas, no motion, and battery-related cases.

### Signal Preprocessing

A preprocessing layer converts raw wearable data into cleaner, robot-usable signals. It calculates derived values such as ascent rate and gas pressure drop rate, while preserving the timing and diver identity information needed by later layers.

### Diver State Estimation

The state estimator converts cleaned numerical signals into interpreted diver state categories, including dive phase, motion state, gas state, and communication link state. This creates a higher-level representation of the diver’s condition without directly raising alarms.

### Wearable Alarm Engine

The alarm engine evaluates the interpreted diver state and produces safety alarms. It generates a final DiverSafetyPacket, containing the current diver state, active alarm events, and an overall safety state such as OK, WARNING, CRITICAL, or EMERGENCY.

Example alarm codes include:

FAST_ASCENT
LOW_GAS
CRITICAL_GAS
GAS_DROPPING_FAST
WEAK_LINK
LINK_LOST
DIVER_EMERGENCY_BUTTON
NO_MOTION_DETECTED
WEARABLE_BATTERY_LOW

### Shared Protocol Layer

A shared protocol layer defines the message contracts exchanged between system components. This includes shared models such as DiverState, AlarmEvent, DiverSafetyPacket, RobotStatusPacket, and common enums for safety states, robot modes, link states, and alarm severity.

This keeps wearable-side logic, robot-side logic, and surface/backend logic decoupled.

### Acoustic Communication Simulator

The communication layer simulates an unreliable underwater acoustic link between the diver wearable and the robot. It models communication effects that are important for robot decision-making, including packet delay, jitter, packet drops, missing packets, sender/receiver identifiers, message IDs, sequence numbers, and communication statistics.

The robot therefore does not instantly receive the diver’s current state. It reacts only to packets that have actually arrived, which makes communication delay visible in the mission timeline.

### Robot Decision System

The robot-side system consumes received DiverSafetyPacket messages and produces high-level robot decisions. It tracks the latest known diver packet, detects stale diver data, and chooses a robot mode.

Implemented robot modes include:

IDLE
MONITORING
APPROACH_DIVER
GUIDE_DIVER
EMERGENCY_SUPPORT
SEARCH_LAST_KNOWN

The robot planner is alarm-aware. For example, LOW_GAS can trigger GUIDE_DIVER, WEAK_LINK can trigger APPROACH_DIVER, and FAST_ASCENT or DIVER_EMERGENCY_BUTTON can trigger EMERGENCY_SUPPORT.

### Surface Gateway Simulator

The surface gateway consumes robot status reports and converts them into operator-facing mission states and alerts. It distinguishes between startup conditions, normal operation, emergency states, and stale diver data.

Implemented surface mission states include:

NO_ROBOT_REPORT
AWAITING_DIVER_DATA
NORMAL
ATTENTION_REQUIRED
EMERGENCY
DIVER_DATA_STALE

### Mission Logging

A mission logging layer records the timeline of each simulation run in a human-readable operational log format. Each log entry captures the current wearable safety state, active alarms, communication status, received packet state, robot mode, surface mission state, and robot decision reason.

The log format is designed to resemble real service logs, making it useful for debugging, post-mission review, and demonstrating system behaviour.

### Mission Backend

An in-memory mission backend stores mission events and maintains the latest mission snapshot. It tracks the active mission status, latest robot mode, latest surface mission state, active alarms, emergency counts, warning counts, stale-data events, and recent mission history.

This backend is designed as the foundation for future dashboard, replay, database, or API integrations.

### FastAPI Mission API

A FastAPI layer exposes the mission backend through HTTP endpoints. The API currently supports starting missions, ingesting mission events, reading current mission snapshots, retrieving compact mission summaries, listing stored events, reading recent events, finishing missions, aborting missions, resetting backend state, and checking service health.

The simulation can now publish mission events to the API over HTTP, making the backend behave like a separate external service rather than a direct in-process object.

### Testing

The project includes unit and API tests for the main layers of the system, including robot tracking, robot behaviour planning, robot system coordination, surface gateway logic, mission backend state handling, and FastAPI endpoints.

The tests verify normal operation, emergency propagation, stale packet handling, mission lifecycle transitions, API validation, and backend summary updates.

## Current End-to-End Flow
Diver Wearable Simulator
    ↓
Signal Preprocessor
    ↓
Diver State Estimator
    ↓
Alarm Engine
    ↓
DiverSafetyPacket
    ↓
Acoustic Communication Simulator
    ↓
Robot Decision System
    ↓
RobotStatusPacket
    ↓
Surface Gateway Simulator
    ↓
Mission Logger
    ↓
Mission Backend
    ↓
FastAPI Mission API

## Current Limitations

This prototype does not yet simulate physical robot navigation, real acoustic signal processing, underwater localization, sonar/camera perception, diver pose estimation, multi-diver tracking, database persistence, or a graphical operator dashboard.

The current focus is on building a realistic software architecture for safety telemetry, unreliable communication, robot-side decision-making, mission supervision, logging, and backend integration.