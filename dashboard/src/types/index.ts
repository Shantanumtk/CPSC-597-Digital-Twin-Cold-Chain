export interface Asset {
  asset_id: string;
  asset_type: string;
  state: 'NORMAL' | 'WARNING' | 'CRITICAL';
  reasons: string[];
  temperature_c: number;
  humidity_pct: number;
  door_open: boolean;
  compressor_running: boolean;
  location?: {
    latitude: number;
    longitude: number;
    speed_kmh?: number;
  };
  updated_at: string;
}

export interface Alert {
  asset_id: string;
  state: string;
  reasons: string[];
  temperature_c?: number;
  created_at: string;
}

export interface Stats {
  total_assets: number;
  state_counts: {
    NORMAL: number;
    WARNING: number;
    CRITICAL: number;
  };
  asset_types: {
    refrigerated_truck: number;
    cold_room: number;
  };
  active_alerts: number;
  updated_at: string;
}

export interface HealthStatus {
  status: string;
  redis: boolean;
  mongodb: boolean;
  kafka_consumer: boolean;
  timestamp: string;
}

export interface TelemetryPoint {
  timestamp: string;
  temperature_c: number;
  humidity_pct: number;
  door_open: boolean;
  created_at: string;
}

export interface AssetHistory {
  asset_id: string;
  hours: number;
  count: number;
  telemetry: TelemetryPoint[];
}