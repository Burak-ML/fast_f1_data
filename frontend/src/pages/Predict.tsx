import { useEffect, useState } from 'react';
import { predictAPI, type PredictOptions, type PredictResult } from '../services/predictService';

const inputClass =
  'w-full rounded-lg bg-surface-container-high border border-white/10 px-3 py-2 text-on-background';

const signed = (n: number) => (n > 0 ? `+${n.toFixed(1)}` : n.toFixed(1));

export function Predict() {
  const [options, setOptions] = useState<PredictOptions | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PredictResult | null>(null);
  const [loading, setLoading] = useState(false);

  const [driver, setDriver] = useState('');
  const [grid, setGrid] = useState(1);
  const [trackTemp, setTrackTemp] = useState(35);
  const [rain, setRain] = useState(false);

  useEffect(() => {
    predictAPI
      .getOptions()
      .then((o) => {
        setOptions(o);
        setDriver(o.drivers[0] ?? '');
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
          grid,
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
  const b = result?.breakdown;

  return (
    <div className="max-w-3xl mx-auto px-6 pt-28 pb-16">
      <h1 className="font-headline-md text-headline-md font-bold uppercase text-primary mb-2">
        Race position estimate
      </h1>
      <p className="text-on-surface-variant mb-8">
        Pick a driver, starting position and conditions. The estimate comes from how past races went in
        the same situations, and the breakdown shows where every position comes from.
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
            Starting position
            <input className={inputClass} type="number" min={1} max={options.grid_max} value={grid}
              onChange={(e) => setGrid(Number(e.target.value))} />
          </label>
          <label className="grid gap-1">
            Track temperature (°C)
            <input className={inputClass} type="number" step="0.5" value={trackTemp}
              onChange={(e) => setTrackTemp(Number(e.target.value))} />
          </label>
          <label className="flex items-center gap-2 self-end pb-2">
            <input type="checkbox" checked={rain} onChange={(e) => setRain(e.target.checked)} />
            Rain
          </label>
          <button type="submit" disabled={loading}
            className="sm:col-span-2 px-6 py-3 rounded-full bg-primary text-on-primary font-bold uppercase disabled:opacity-60">
            {loading ? 'Estimating…' : 'Estimate finish'}
          </button>
        </form>
      )}

      {result && b && (
        <div className="glass-panel p-6 mt-6">
          <div className="text-center">
            <div className="text-on-surface-variant uppercase text-sm">Expected finish</div>
            <div className="text-6xl font-bold text-primary my-2">P{result.predicted_position}</div>
            <div className="text-on-surface-variant">
              Likely between P{result.likely_range[0]} and P{result.likely_range[1]}
            </div>
          </div>
          <dl className="mt-6 grid grid-cols-[1fr_auto] gap-y-1 text-sm">
            <dt>Usual finish from this grid slot</dt><dd>P{b.grid_slot.toFixed(1)}</dd>
            <dt>Team effect</dt><dd>{signed(b.team)}</dd>
            <dt>Driver effect</dt><dd>{signed(b.driver)}</dd>
            <dt>
              {result.condition === 'rain' ? 'Rain' : result.condition === 'hot' ? 'Hot track' : 'Cool track'} effect
            </dt>
            <dd>{signed(b.weather)}</dd>
          </dl>
          <p className="text-xs text-on-surface-variant mt-2">Negative numbers mean places gained.</p>
          {!result.known_driver && (
            <p className="text-xs text-on-surface-variant mt-2">
              No history for this driver, so only the grid slot and conditions were used.
            </p>
          )}
        </div>
      )}

      {m && (
        <p className="text-sm text-on-surface-variant mt-6">
          Checked on the last {m.test_races} of {m.races} races, which the numbers had not seen: off by{' '}
          {m.mae_full} positions on average, versus {m.mae_grid_baseline} if you assume a driver finishes
          where they start{m.beats_baseline ? '.' : ' — so this does not beat that baseline yet.'} The
          range is the error that 80% of those estimates stayed within. Safety cars and retirements cannot
          be predicted.
        </p>
      )}
    </div>
  );
}
