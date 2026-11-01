import { useCallback, useEffect, useState } from 'react'
import api, { errorMessage } from '../../api/client'
import { COLORS, LineChart } from '../../components/charts'
import { Card, ErrorAlert, Loading, PageHeader, StatCard } from '../../components/ui'

export default function ModelMetrics() {
  const [metrics, setMetrics] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [training, setTraining] = useState(false)
  const [notice, setNotice] = useState('')
  const [dataset, setDataset] = useState(null)
  const [datasetBusy, setDatasetBusy] = useState(false)
  const [regenerateForm, setRegenerateForm] = useState({ rows: 4000, seed: '' })

  const loadDataset = useCallback(async () => {
    try {
      const { data } = await api.get('/admin/dataset')
      setDataset(data)
    } catch (err) {
      setError(errorMessage(err))
    }
  }, [])

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const { data } = await api.get('/admin/model-metrics')
      setMetrics(data)
      await loadDataset()
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [loadDataset])

  useEffect(() => {
    load()
  }, [load])

  async function regenerateDataset() {
    setDatasetBusy(true)
    setError('')
    setNotice('')
    try {
      const payload = { rows: Number(regenerateForm.rows) || 4000 }
      if (regenerateForm.seed !== '') payload.seed = Number(regenerateForm.seed)
      const { data } = await api.post('/admin/dataset/regenerate', payload)
      setNotice(
        `Dataset regenerated: ${data.rows} rows (seed ${data.seed}). Retrain the model to use it.`,
      )
      await loadDataset()
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setDatasetBusy(false)
    }
  }

  async function train() {
    setTraining(true)
    setError('')
    setNotice('')
    try {
      const { data } = await api.post('/dl/train')
      setNotice(
        `Training finished: ${data.epochs_run} epochs, MAE ${data.metrics.mae}, RMSE ${data.metrics.rmse}, R² ${data.metrics.r2}.`,
      )
      await load()
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setTraining(false)
    }
  }

  if (loading && !metrics) return <Loading label="Loading model evaluation…" />

  const history = metrics?.history || {}
  const labels = (history.loss || []).map((_, index) => index + 1)

  return (
    <div>
      <PageHeader
        title="Deep learning model performance"
        subtitle="Student performance ANN — trained on the documented synthetic dataset."
        actions={
          <button type="button" className="btn-green" onClick={train} disabled={training}>
            {training ? 'Training…' : 'Train / retrain model'}
          </button>
        }
      />
      <ErrorAlert message={error} onRetry={load} />
      {notice && (
        <div className="mb-4 rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700">
          {notice}
        </div>
      )}

      {!metrics?.ready ? (
        <Card title="No trained model">
          <p className="text-sm text-slate-600">
            No model artifacts were found. Click <strong>Train / retrain model</strong> to run
            the TensorFlow training job. Training uses the 4,000-row synthetic dataset and
            typically completes in under a minute on a laptop CPU.
          </p>
          <pre className="mt-4 overflow-x-auto rounded-lg bg-navy-900 p-4 text-xs text-slate-200">
{`python -m app.deep_learning.train_student_ann`}
          </pre>
        </Card>
      ) : (
        <div className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <StatCard label="Test MAE" value={metrics.test_metrics.mae} hint="Mean absolute error (score points)" icon="chart" />
            <StatCard label="Test RMSE" value={metrics.test_metrics.rmse} hint="Root mean squared error" icon="chart" tone="green" />
            <StatCard label="Test R²" value={metrics.test_metrics.r2} hint="Variance explained on held-out data" icon="brain" />
            <StatCard label="Epochs run" value={metrics.training.epochs_run} hint={`Early stopping patience ${metrics.training.early_stopping_patience}`} icon="clock" tone="amber" />
          </div>

          <div className="grid gap-6 xl:grid-cols-3">
            <Card title="Training history" subtitle="Loss and validation loss per epoch" className="xl:col-span-2">
              <LineChart
                data={{
                  labels,
                  datasets: [
                    {
                      label: 'Training loss (MSE)',
                      data: history.loss || [],
                      borderColor: COLORS.navy,
                      backgroundColor: 'rgba(22,57,90,0.08)',
                      fill: true,
                      tension: 0.3,
                      pointRadius: 0,
                    },
                    {
                      label: 'Validation loss',
                      data: history.val_loss || [],
                      borderColor: COLORS.green,
                      backgroundColor: 'transparent',
                      tension: 0.3,
                      pointRadius: 0,
                    },
                  ],
                }}
                height={300}
              />
            </Card>

            <Card title="Architecture">
              <ol className="space-y-2 text-sm text-slate-700">
                <li className="rounded-lg bg-slate-50 px-3 py-2">Input · 7 features</li>
                <li className="rounded-lg bg-slate-50 px-3 py-2">Dense 64 · ReLU</li>
                <li className="rounded-lg bg-slate-50 px-3 py-2">Dense 32 · ReLU</li>
                <li className="rounded-lg bg-slate-50 px-3 py-2">Dense 16 · ReLU</li>
                <li className="rounded-lg bg-green-50 px-3 py-2 font-semibold text-green-800">
                  Dense 1 · Linear · score 0–100
                </li>
              </ol>
              <dl className="mt-4 space-y-2 text-xs text-slate-500">
                <div className="flex justify-between">
                  <dt>Optimizer</dt>
                  <dd className="font-semibold text-slate-700">{metrics.optimizer}</dd>
                </div>
                <div className="flex justify-between">
                  <dt>Loss</dt>
                  <dd className="font-semibold text-slate-700">{metrics.loss}</dd>
                </div>
                <div className="flex justify-between">
                  <dt>Batch size</dt>
                  <dd className="font-semibold text-slate-700">{metrics.training.batch_size}</dd>
                </div>
                <div className="flex justify-between">
                  <dt>Model version</dt>
                  <dd className="font-semibold text-slate-700">{metrics.model_version}</dd>
                </div>
              </dl>
            </Card>
          </div>

          <div className="grid gap-6 xl:grid-cols-3">
            <Card title="Dataset" className="xl:col-span-2">
              <dl className="grid gap-3 text-sm sm:grid-cols-2">
                <div>
                  <dt className="text-xs uppercase tracking-wide text-slate-500">Source</dt>
                  <dd className="font-medium text-slate-800">
                    {metrics.dataset.synthetic ? 'Synthetic (documented DGP)' : 'External dataset'}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs uppercase tracking-wide text-slate-500">Rows</dt>
                  <dd className="font-medium text-slate-800">{metrics.dataset.rows_total}</dd>
                </div>
                <div>
                  <dt className="text-xs uppercase tracking-wide text-slate-500">Train / validation / test</dt>
                  <dd className="font-medium text-slate-800">
                    {metrics.dataset.rows_train} / {metrics.dataset.rows_validation} / {metrics.dataset.rows_test}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs uppercase tracking-wide text-slate-500">Features</dt>
                  <dd className="font-medium text-slate-800">{metrics.dataset.features.length}</dd>
                </div>
              </dl>
              <ul className="mt-4 flex flex-wrap gap-2">
                {metrics.dataset.features.map((feature) => (
                  <li key={feature} className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-600">
                    {feature}
                  </li>
                ))}
              </ul>
            </Card>

            <Card title="Validation metrics">
              <dl className="space-y-3 text-sm">
                <div className="flex items-center justify-between rounded-lg bg-slate-50 px-3 py-2">
                  <dt className="text-slate-600">Validation MAE</dt>
                  <dd className="font-bold text-navy-900">{metrics.validation_metrics?.mae}</dd>
                </div>
                <div className="flex items-center justify-between rounded-lg bg-slate-50 px-3 py-2">
                  <dt className="text-slate-600">Validation RMSE</dt>
                  <dd className="font-bold text-navy-900">{metrics.validation_metrics?.rmse}</dd>
                </div>
                <div className="flex items-center justify-between rounded-lg bg-slate-50 px-3 py-2">
                  <dt className="text-slate-600">Trained at</dt>
                  <dd className="text-xs font-semibold text-slate-700">
                    {metrics.trained_at ? new Date(metrics.trained_at).toLocaleString() : '—'}
                  </dd>
                </div>
              </dl>
              <p className="mt-4 text-xs leading-relaxed text-slate-500">
                Metrics are computed on a 15% hold-out split that the model never saw during
                training or early stopping. No values are hard-coded.
              </p>
            </Card>
          </div>
        </div>
      )}

      <Card
        className="mt-6"
        title="Dataset management"
        subtitle="The synthetic dataset is regenerated from a documented data-generating process."
        actions={
          <div className="flex flex-wrap items-end gap-2">
            <div>
              <label className="label mb-1">Rows</label>
              <input
                type="number"
                min="500"
                max="20000"
                step="100"
                className="input w-28"
                value={regenerateForm.rows}
                onChange={(event) =>
                  setRegenerateForm({ ...regenerateForm, rows: event.target.value })
                }
              />
            </div>
            <div>
              <label className="label mb-1">Seed</label>
              <input
                type="number"
                className="input w-28"
                placeholder="random"
                value={regenerateForm.seed}
                onChange={(event) =>
                  setRegenerateForm({ ...regenerateForm, seed: event.target.value })
                }
              />
            </div>
            <button
              type="button"
              className="btn-ghost"
              onClick={regenerateDataset}
              disabled={datasetBusy}
            >
              {datasetBusy ? 'Regenerating…' : 'Regenerate dataset'}
            </button>
          </div>
        }
      >
        {dataset?.available ? (
          <>
            <dl className="grid gap-3 text-sm sm:grid-cols-2 lg:grid-cols-4">
              <div>
                <dt className="text-xs uppercase tracking-wide text-slate-500">Rows</dt>
                <dd className="font-medium text-slate-800">{dataset.rows}</dd>
              </div>
              <div>
                <dt className="text-xs uppercase tracking-wide text-slate-500">Columns</dt>
                <dd className="font-medium text-slate-800">{dataset.columns?.length ?? 0}</dd>
              </div>
              <div>
                <dt className="text-xs uppercase tracking-wide text-slate-500">Missing values</dt>
                <dd className="font-medium text-slate-800">{dataset.missing_values}</dd>
              </div>
              <div>
                <dt className="text-xs uppercase tracking-wide text-slate-500">Source</dt>
                <dd className="font-medium text-slate-800">
                  {dataset.synthetic ? 'Synthetic' : 'External'}
                </dd>
              </div>
            </dl>
            <p className="mt-3 text-xs text-slate-500">{dataset.note}</p>
            <div className="mt-4 overflow-x-auto">
              <table className="min-w-full text-xs">
                <thead className="table-head">
                  <tr>
                    {(dataset.columns || []).map((column) => (
                      <th key={column} className="whitespace-nowrap px-3 py-2">
                        {column}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {(dataset.preview || []).map((row, index) => (
                    <tr key={index} className="hover:bg-slate-50">
                      {(dataset.columns || []).map((column) => (
                        <td key={column} className="table-cell whitespace-nowrap px-3 py-2">
                          {row[column] ?? '—'}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        ) : (
          <p className="text-sm text-slate-500">
            {dataset?.message || 'Dataset information is not available yet.'}
          </p>
        )}
      </Card>
    </div>
  )
}
