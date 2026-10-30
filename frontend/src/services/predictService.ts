const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface PredictOptions {
  drivers: string[];
  constructors: string[];
  circuits: string[];
  grid_max: number;
  metrics: {
    rows: number;
    races: number;
    test_races: number;
    mae_model: number;
    mae_grid_baseline: number;
    beats_baseline: boolean;
    within_3_positions: number;
    typical_error: number;
  };
}

export interface PredictInput {
  driver_id: string;
  constructor_id: string;
  circuit_id: string;
  grid: number;
  air_temperature: number;
  track_temperature: number;
  rainfall: boolean;
}

export interface PredictResult {
  predicted_position: number;
  raw_position: number;
  likely_range: [number, number];
  typical_error: number;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, init);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(typeof body.detail === 'string' ? body.detail : `Request failed (${res.status})`);
  }
  return res.json();
}

export const predictAPI = {
  getOptions: () => request<PredictOptions>('/predict/options'),
  predict: (input: PredictInput) =>
    request<PredictResult>('/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(input),
    }),
};
