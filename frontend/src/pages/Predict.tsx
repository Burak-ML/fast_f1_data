import { useEffect, useState } from 'react';
import { predictAPI, type PredictOptions, type PredictResult } from '../services/predictService';

const inputClass =
  'w-full rounded-lg bg-surface-container-high border border-white/10 px-3 py-2 text-on-background';

export function Predict() {
  const [options, setOptions] = useState<PredictOptions | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PredictResult | null>(null);
  const [loading, setLoading] = useState(false);

  const [driver, setDriver] = useState('');
  const [constructor, setConstructor] = useState('');
  const [circuit, setCircuit] = useState('');
  const [grid, setGrid] = useState(1);
  const [airTemp, setAirTemp] = useState(22);
  const [trackTemp, setTrackTemp] = useState(35);
  const [rain, setRain] = useState(false);

  useEffect(() => {
    predictAPI
      .getOptions()
      .then((o) => {
        setOptions(o);
        setDriver(o.drivers[0] ?? '');
        setConstructor(o.constructors[0] ?? '');
        setCircuit(o.circuits[0] ?? '');
      })
      .catch((e: Error) => setError(e.message));
  }, []);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      setResult(
        await predictAPI.predict({
          driver_id: driver,
          constructor_id: constructor,
          circuit_id: circuit,
          grid,
          air_temperature: airTemp,
          track_temperature: trackTemp,
          rainfall: rain,
        }),
      );
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const m = options?.metrics;

  return (
    <div className="max-w-3xl mx-auto px-6 pt-28 pb-16">
      <h1 className="font-headline-md text-headline-md font-bold uppercase text-primary mb-2">
        Race position prediction
      </h1>
      <p className="text-on-surface-variant mb-8">
        Pick a driver, circuit, weather and starting position. The model estimates where they finish.
      </p>

      {error && <div className="glass-panel p-4 mb-6 text-error">{error}</div>}

      {options && (
        <form onSubmit={submit} className="glass-panel p-6 grid gap-4 sm:grid-cols-2">
          <label className="grid gap-1">
            Driver
            <select className={inputClass} value={driver} onChange={(e) => setDriver(e.target.value)}>
              {options.drivers.map((d) => <option key={d}>{d}</option>)}
            </select>
          </label>
          <label className="grid gap-1">
            Team
            <select className={inputClass} value={constructor} onChange={(e) => setConstructor(e.target.value)}>
              {options.constructors.map((c) => <option key={c}>{c}</option>)}
            </select>
          </label>
          <label className="grid gap-1">
            Circuit
            <select className={inputClass} value={circuit} onChange={(e) => setCircuit(e.target.value)}>
              {options.circuits.map((c) => <option key={c}>{c}</option>)}
            </select>
          </label>
          <label className="grid gap-1">
            Starting position
            <input className={inputClass} type="number" min={1} max={options.grid_max} value={grid}
              onChange={(e) => setGrid(Number(e.target.value))} />
          </label>
          <label className="grid gap-1">
            Air temperature (°C)
            <input className={inputClass} type="number" step="0.5" value={airTemp}
              onChange={(e) => setAirTemp(Number(e.target.value))} />
          </label>
          <label className="grid gap-1">
            Track temperature (°C)
            <input className={inputClass} type="number" step="0.5" value={trackTemp}
              onChange={(e) => setTrackTemp(Number(e.target.value))} />
          </label>
          <label className="flex items-center gap-2 sm:col-span-2">
            <input type="checkbox" checked={rain} onChange={(e) => setRain(e.target.checked)} />
            Rain expected
          </label>
          <button type="submit" disabled={loading}
            className="sm:col-span-2 px-6 py-3 rounded-full bg-primary text-on-primary font-bold uppercase disabled:opacity-60">
            {loading ? 'Predicting…' : 'Predict finish'}
          </button>
        </form>
      )}

      {result && (
        <div className="glass-panel p-6 mt-6 text-center">
          <div className="text-on-surface-variant uppercase text-sm">Expected finish</div>
          <div className="text-6xl font-bold text-primary my-2">P{result.predicted_position}</div>
          <div className="text-on-surface-variant">
            Likely between P{result.likely_range[0]} and P{result.likely_range[1]}
          </div>
        </div>
      )}

      {m && (
        <p className="text-sm text-on-surface-variant mt-6">
          Tested on the last {m.test_races} of {m.races} races it had not seen: off by {m.mae_model} positions
          on average, versus {m.mae_grid_baseline} if you simply assume a driver finishes where they start
          {m.beats_baseline ? '.' : ' — so this model does not beat that baseline yet.'} The range shown is
          the error that 80% of test predictions stayed within. Rain, safety cars and retirements cannot be predicted.
        </p>
      )}
    </div>
  );
}
