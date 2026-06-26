export type MissionRunStatus =
    | "NOT_STARTED"
    | "RUNNING"
    | "COMPLETED"
    | "ABORTED";

export type MissionSummary = {
    mission_id: string;
    scenario: string;
    status: MissionRunStatus;
    events_received: number;
    current_surface_mission_state: string | null;
    current_robot_mode: string | null;
    emergency_event_count: number;
    warning_event_count: number;
    stale_data_event_count: number;
};

export type MissionSummaryResponse = {
    summary: MissionSummary;
};

export type MissionEvent = {
    event_index: number;
    recorded_at_utc: string;
    scenario: string;
    elapsed_time_s: number;

    wearable_safety_state: string;
    wearable_alarm_codes: string[];

    communication_transmit_status: string | null;
    communication_receive_status: string | null;

    communication_tx_sequence_number?: number | null;
    communication_rx_sequence_number?: number | null;
    communication_tx_message_id?: string | null;
    communication_rx_message_id?: string | null;
    communication_sender_id?: string | null;
    communication_receiver_id?: string | null;

    communication_latency_s: number | null;
    communication_reason: string | null;

    received_safety_state: string | null;
    received_alarm_codes: string[];

    robot_mode: string;
    robot_reason: string;
    robot_priority: number;
    robot_notify_surface: boolean;

    latest_diver_packet_age_s: number | null;
    diver_data_stale: boolean;

    surface_mission_state: string;
    surface_alert_codes: string[];
};

export type MissionRuntimeState =
    | "IDLE"
    | "RUNNING"
    | "STOPPING"
    | "COMPLETED"
    | "FAILED";

export type MissionRuntimeStatus = {
    state: MissionRuntimeState;
    mission_id: string | null;
    scenario: string | null;
    started_at_utc: string | null;
    stopped_at_utc: string | null;
    events_processed: number;
    log_path: string | null;
    last_error: string | null;
};

export type StartRuntimeRequest = {
    scenario: string;
    mission_id?: string | null;
    tick_interval_s: number;
};

export type DiverOperatorStatus = {
    diver_id: string;
    wearable_safety_state: string | null;
    received_safety_state: string | null;
    robot_mode: string | null;
    surface_mission_state: string | null;
    active_alarm_codes: string[];
    active_surface_alert_codes: string[];
    latest_event_time_s: number | null;
    latest_packet_age_s: number | null;
    diver_data_stale: boolean;
    robot_notify_surface: boolean;
};

export type MissionOperatorStatus = {
    mission_id: string;
    scenario: string;
    status: MissionRunStatus;
    events_received: number;
    current_surface_mission_state: string | null;
    emergency_event_count: number;
    warning_event_count: number;
    stale_data_event_count: number;
    divers: DiverOperatorStatus[];
};