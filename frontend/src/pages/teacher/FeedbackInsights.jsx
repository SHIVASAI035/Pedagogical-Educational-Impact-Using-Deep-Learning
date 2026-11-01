import { useCallback, useEffect, useState } from 'react'
import api, { errorMessage } from '../../api/client'
import { BarChart, COLORS, DoughnutChart } from '../../components/charts'
import { Badge, Card, EmptyState, ErrorAlert, Loading, PageHeader } from '../../components/ui'

const DIMENSIONS = {
  clarity_rating: 'Clarity',
  interaction_rating: 'Interaction',
  methodology_rating: 'Methodology',
  practical_rating: 'Practical',
  difficulty_rating: 'Difficulty',
  overall_rating: 'Overall',
}

export default function FeedbackInsights() {
  const [summary, setSummary] = useState(null)
  const [nlp, setNlp] = useState(null)
  const [comments, setComments] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [summaryResponse, nlpResponse, commentsResponse] = await Promise.all([
        api.get('/feedback/summary'),
        api.get('/feedback/nlp'),
        api.get('/feedback/recent'),
      ])
      setSummary(summaryResponse.data)
      setNlp(nlpResponse.data)
      setComments(commentsResponse.data)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  if (loading && !summary) return <Loading label="Loading feedback insights…" />

  const sentiment = summary?.sentiment || {}
  const averages = summary?.averages || {}
  const aspects = nlp?.aspect_sentiment || {}
  const aspectEntries = Object.entries(aspects)

  return (
    <div>
      <PageHeader
        title="Student feedback insights"
        subtitle="Anonymised, aggregated feedback with NLP sentiment analysis. Individual identities are never shown."
      />
      <ErrorAlert message={error} onRetry={load} />

      <div className="grid gap-4 sm:grid-cols-3">
        <div className="card p-5">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Responses</p>
          <p className="mt-2 text-2xl font-bold text-navy-900">{summary?.count ?? 0}</p>
        </div>
        <div className="card p-5">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Positive sentiment</p>
          <p className="mt-2 text-2xl font-bold text-green-700">{sentiment.positive_pct ?? 0}%</p>
        </div>
        <div className="card p-5">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Negative sentiment</p>
          <p className="mt-2 text-2xl font-bold text-red-600">{sentiment.negative_pct ?? 0}%</p>
        </div>
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-3">
        <Card title="Sentiment distribution">
          <DoughnutChart
            data={{
              labels: ['Positive', 'Neutral', 'Negative'],
              datasets: [
                {
                  data: [sentiment.positive || 0, sentiment.neutral || 0, sentiment.negative || 0],
                  backgroundColor: [COLORS.green, COLORS.slate, COLORS.red],
                  borderWidth: 0,
                },
              ],
            }}
          />
        </Card>

        <Card title="Rating dimensions" subtitle="Average out of 5" className="xl:col-span-2">
          <BarChart
            data={{
              labels: Object.values(DIMENSIONS),
              datasets: [
                {
                  label: 'Average rating',
                  data: Object.keys(DIMENSIONS).map((key) => averages[key] || 0),
                  backgroundColor: COLORS.navy,
                  borderRadius: 6,
                  maxBarThickness: 40,
                },
              ],
            }}
            options={{ plugins: { legend: { display: false } }, scales: { y: { min: 0, max: 5 } } }}
            height={260}
          />
        </Card>
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-2">
        <Card title="Aspect sentiment" subtitle="From text analysis (-1 negative → +1 positive)">
          {aspectEntries.length ? (
            <BarChart
              horizontal
              data={{
                labels: aspectEntries.map(([aspect]) => aspect),
                datasets: [
                  {
                    label: 'Sentiment',
                    data: aspectEntries.map(([, score]) => score),
                    backgroundColor: aspectEntries.map(([, score]) =>
                      score > 0.15 ? COLORS.green : score < -0.15 ? COLORS.red : COLORS.slate,
                    ),
                    borderRadius: 6,
                    maxBarThickness: 24,
                  },
                ],
              }}
              options={{ plugins: { legend: { display: false } }, scales: { x: { min: -1, max: 1 } } }}
              height={260}
            />
          ) : (
            <EmptyState title="No aspect signals" message="Comments did not mention specific teaching aspects." />
          )}
        </Card>

        <Card title="Frequent keywords" subtitle="Most common sentiment-bearing words">
          {nlp?.top_keywords?.length ? (
            <div className="flex flex-wrap gap-2">
              {nlp.top_keywords.map((keyword) => (
                <span
                  key={keyword.word}
                  className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700"
                  style={{ fontSize: `${Math.min(16, 11 + keyword.count)}px` }}
                >
                  {keyword.word} · {keyword.count}
                </span>
              ))}
            </div>
          ) : (
            <EmptyState title="No keywords found" message="Feedback comments may be too short." />
          )}
          <div className="mt-4 rounded-lg bg-slate-50 p-3">
            <p className="text-xs font-semibold text-slate-600">Method</p>
            <p className="mt-1 text-xs text-slate-500">{nlp?.method}</p>
            <ul className="mt-2 list-disc space-y-1 pl-4 text-xs text-slate-500">
              {(nlp?.limitations || []).map((limitation) => (
                <li key={limitation}>{limitation}</li>
              ))}
            </ul>
          </div>
        </Card>
      </div>

      <Card className="mt-6" title="Recent comments" subtitle="Anonymised — no student identifiers">
        {comments.length ? (
          <ul className="grid gap-3 sm:grid-cols-2">
            {comments.map((comment, index) => (
              <li key={`${comment.date}-${index}`} className="rounded-lg border border-slate-200 p-3">
                <div className="mb-2 flex items-center justify-between">
                  <Badge
                    tone={
                      comment.sentiment === 'positive'
                        ? 'green'
                        : comment.sentiment === 'negative'
                          ? 'red'
                          : 'slate'
                    }
                  >
                    {comment.sentiment}
                  </Badge>
                  <span className="text-[11px] text-slate-400">
                    {comment.subject || 'General'} · {comment.date}
                  </span>
                </div>
                <p className="text-sm leading-relaxed text-slate-600">“{comment.comment}”</p>
              </li>
            ))}
          </ul>
        ) : (
          <EmptyState title="No comments yet" message="Student comments will appear here after submission." />
        )}
      </Card>
    </div>
  )
}
