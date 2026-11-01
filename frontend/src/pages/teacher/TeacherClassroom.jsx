import { useCallback, useEffect, useMemo, useState } from 'react'
import api, { errorMessage } from '../../api/client'
import { Card, EmptyState, ErrorAlert, Loading, PageHeader, Tabs } from '../../components/ui'

function today() {
  return new Date().toISOString().slice(0, 10)
}

const TABS = [
  { value: 'sessions', label: 'Teaching sessions' },
  { value: 'observations', label: 'Observations' },
  { value: 'assignments', label: 'Assignments' },
  { value: 'activity', label: 'Learning activity' },
]

const SCORE_FIELDS = [
  { key: 'interaction_score', label: 'Interaction' },
  { key: 'clarity_score', label: 'Clarity' },
  { key: 'engagement_score', label: 'Engagement' },
  { key: 'practical_examples_score', label: 'Practical examples' },
  { key: 'material_usage_score', label: 'Material usage' },
]

const EMPTY_OBSERVATION = {
  subject_id: '',
  methodology: 'Lecture',
  observation_date: today(),
  interaction_score: 6,
  clarity_score: 6,
  engagement_score: 6,
  practical_examples_score: 6,
  material_usage_score: 6,
  observer_notes: '',
}

const EMPTY_SESSION = {
  subject_id: '',
  methodology: 'Lecture',
  date_used: today(),
  duration_minutes: 45,
  description: '',
}

const EMPTY_ASSIGNMENT = {
  subject_id: '',
  title: '',
  description: '',
  due_date: today(),
  max_marks: 20,
}

const EMPTY_ACTIVITY = {
  student_id: '',
  date: today(),
  study_hours: 2,
  participation_score: 6,
  engagement_score: 6,
  assignment_completion: 80,
  notes: '',
}

export default function TeacherClassroom() {
  const [tab, setTab] = useState('sessions')
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  const [subjects, setSubjects] = useState([])
  const [students, setStudents] = useState([])
  const [classes, setClasses] = useState([])
  const [methodologies, setMethodologies] = useState([])
  const [sessions, setSessions] = useState([])
  const [observations, setObservations] = useState([])
  const [assignments, setAssignments] = useState([])
  const [activities, setActivities] = useState([])

  const [sessionForm, setSessionForm] = useState(EMPTY_SESSION)
  const [observationForm, setObservationForm] = useState(EMPTY_OBSERVATION)
  const [assignmentForm, setAssignmentForm] = useState(EMPTY_ASSIGNMENT)
  const [activityForm, setActivityForm] = useState(EMPTY_ACTIVITY)

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [subjectsResponse, studentsResponse, classesResponse, methodologyResponse, sessionsResponse, observationsResponse, assignmentsResponse] =
        await Promise.all([
          api.get('/subjects', { params: { mine: 1 } }),
          api.get('/students', { params: { per_page: 100 } }),
          api.get('/classes'),
          api.get('/teaching/methodologies'),
          api.get('/teaching/sessions', { params: { per_page: 50 } }),
          api.get('/teaching/observations', { params: { per_page: 50 } }),
          api.get('/academics/assignments', { params: { per_page: 50 } }),
        ])
      setSubjects(subjectsResponse.data)
      setStudents(studentsResponse.data.items)
      setClasses(classesResponse.data)
      setMethodologies(methodologyResponse.data)
      setSessions(sessionsResponse.data.items)
      setObservations(observationsResponse.data.items)
      setAssignments(assignmentsResponse.data.items)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const loadActivities = useCallback(async (studentId) => {
    if (!studentId) {
      setActivities([])
      return
    }
    try {
      const { data } = await api.get('/academics/activities', { params: { student_id: studentId } })
      setActivities(data)
    } catch (err) {
      setError(errorMessage(err))
    }
  }, [])

  useEffect(() => {
    loadActivities(activityForm.student_id)
  }, [activityForm.student_id, loadActivities])

  const selectedSessionSubject = useMemo(
    () => subjects.find((subject) => String(subject.id) === String(sessionForm.subject_id)),
    [subjects, sessionForm.subject_id],
  )
  const selectedActivitySubject = useMemo(
    () => students.find((student) => String(student.id) === String(activityForm.student_id)),
    [students, activityForm.student_id],
  )

  async function run(action, successMessage) {
    setBusy(true)
    setError('')
    setNotice('')
    try {
      await action()
      setNotice(successMessage)
      await load()
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  function saveSession(event) {
    event.preventDefault()
    run(async () => {
      await api.post('/teaching/sessions', {
        ...sessionForm,
        subject_id: sessionForm.subject_id ? Number(sessionForm.subject_id) : null,
        duration_minutes: Number(sessionForm.duration_minutes),
      })
      setSessionForm({ ...EMPTY_SESSION, subject_id: sessionForm.subject_id })
    }, 'Teaching session logged.')
  }

  function saveObservation(event) {
    event.preventDefault()
    run(async () => {
      const payload = { ...observationForm }
      if (!payload.subject_id) delete payload.subject_id
      else payload.subject_id = Number(payload.subject_id)
      SCORE_FIELDS.forEach(({ key }) => {
        payload[key] = Number(payload[key])
      })
      await api.post('/teaching/observations', payload)
      setObservationForm({ ...EMPTY_OBSERVATION, subject_id: observationForm.subject_id })
    }, 'Classroom observation logged.')
  }

  function saveAssignment(event) {
    event.preventDefault()
    run(async () => {
      await api.post('/academics/assignments', {
        ...assignmentForm,
        subject_id: Number(assignmentForm.subject_id),
        max_marks: Number(assignmentForm.max_marks),
      })
      setAssignmentForm({ ...EMPTY_ASSIGNMENT, subject_id: assignmentForm.subject_id })
    }, 'Assignment created for the class.')
  }

  function saveActivity(event) {
    event.preventDefault()
    run(async () => {
      await api.post('/academics/activities', {
        ...activityForm,
        student_id: Number(activityForm.student_id),
        study_hours: Number(activityForm.study_hours),
        participation_score: Number(activityForm.participation_score),
        engagement_score: Number(activityForm.engagement_score),
        assignment_completion: Number(activityForm.assignment_completion),
      })
      await loadActivities(activityForm.student_id)
    }, 'Learning activity saved for that date.')
  }

  async function remove(path, label) {
    if (!window.confirm(`Delete this ${label}?`)) return
    try {
      await api.delete(path)
      await load()
    } catch (err) {
      setError(errorMessage(err))
    }
  }

  if (loading) {
    return (
      <div>
        <PageHeader title="Classroom log" />
        <Loading />
      </div>
    )
  }

  return (
    <div>
      <PageHeader
        title="Classroom log"
        subtitle="Record what you taught, how the lesson went, the assignments you set and the learning activity you observed."
        actions={<Tabs tabs={TABS} active={tab} onChange={setTab} />}
      />
      <ErrorAlert message={error} onRetry={load} />
      {notice && (
        <div className="mb-4 rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700">
          {notice}
        </div>
      )}
      {!subjects.length && (
        <div className="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          No subjects are assigned to your account yet, so sessions, observations and assignments
          cannot be logged. Ask an administrator to assign a subject to you.
        </div>
      )}

      {tab === 'sessions' && (
        <div className="grid gap-6 xl:grid-cols-3">
          <Card title="Log a teaching session" className="xl:col-span-1">
            <form className="space-y-3" onSubmit={saveSession}>
              <div>
                <label className="label">Subject</label>
                <select
                  className="input"
                  required
                  value={sessionForm.subject_id}
                  onChange={(event) => setSessionForm({ ...sessionForm, subject_id: event.target.value })}
                >
                  <option value="">Select subject</option>
                  {subjects.map((subject) => (
                    <option key={subject.id} value={subject.id}>
                      {subject.name} · {subject.class_name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label">Methodology</label>
                <select
                  className="input"
                  value={sessionForm.methodology}
                  onChange={(event) => setSessionForm({ ...sessionForm, methodology: event.target.value })}
                >
                  {methodologies.map((item) => (
                    <option key={item.name} value={item.name}>
                      {item.name}
                    </option>
                  ))}
                </select>
                <p className="mt-1 text-xs text-slate-500">
                  {methodologies.find((item) => item.name === sessionForm.methodology)?.description}
                </p>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="label">Date</label>
                  <input
                    type="date"
                    className="input"
                    required
                    value={sessionForm.date_used}
                    onChange={(event) => setSessionForm({ ...sessionForm, date_used: event.target.value })}
                  />
                </div>
                <div>
                  <label className="label">Minutes</label>
                  <input
                    type="number"
                    min="5"
                    max="600"
                    className="input"
                    required
                    value={sessionForm.duration_minutes}
                    onChange={(event) =>
                      setSessionForm({ ...sessionForm, duration_minutes: event.target.value })
                    }
                  />
                </div>
              </div>
              <div>
                <label className="label">What happened?</label>
                <textarea
                  className="input"
                  rows="3"
                  maxLength="1000"
                  placeholder="Topic, activity, grouping, resources used…"
                  value={sessionForm.description}
                  onChange={(event) => setSessionForm({ ...sessionForm, description: event.target.value })}
                />
              </div>
              <button type="submit" className="btn-primary w-full" disabled={busy}>
                {busy ? 'Saving…' : 'Log session'}
              </button>
              {selectedSessionSubject && (
                <p className="text-xs text-slate-500">
                  Logged against {selectedSessionSubject.name} · {selectedSessionSubject.class_name}.
                </p>
              )}
            </form>
          </Card>

          <Card
            title="Recent sessions"
            subtitle="Your methodology mix is recalculated from these entries"
            className="xl:col-span-2"
          >
            {sessions.length ? (
              <div className="-mx-5 max-h-[560px] overflow-auto">
                <table className="min-w-full">
                  <thead className="table-head">
                    <tr>
                      <th className="px-4 py-3">Date</th>
                      <th className="px-4 py-3">Methodology</th>
                      <th className="px-4 py-3">Subject</th>
                      <th className="px-4 py-3">Minutes</th>
                      <th className="px-4 py-3">Notes</th>
                      <th className="px-4 py-3 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sessions.map((session) => (
                      <tr key={session.id} className="hover:bg-slate-50">
                        <td className="table-cell text-slate-500">{session.date_used}</td>
                        <td className="table-cell font-medium text-navy-900">{session.methodology}</td>
                        <td className="table-cell text-slate-600">{session.subject_name || '—'}</td>
                        <td className="table-cell text-slate-600">{session.duration_minutes}</td>
                        <td className="table-cell max-w-xs truncate text-slate-500">
                          {session.description || '—'}
                        </td>
                        <td className="table-cell text-right">
                          <button
                            type="button"
                            className="text-xs font-semibold text-red-600 hover:underline"
                            onClick={() => remove(`/teaching/sessions/${session.id}`, 'session')}
                          >
                            Delete
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <EmptyState title="No sessions logged yet" message="Use the form to record your first lesson." />
            )}
          </Card>
        </div>
      )}

      {tab === 'observations' && (
        <div className="grid gap-6 xl:grid-cols-3">
          <Card title="Log a classroom observation" className="xl:col-span-1">
            <form className="space-y-3" onSubmit={saveObservation}>
              <div>
                <label className="label">Subject (optional)</label>
                <select
                  className="input"
                  value={observationForm.subject_id}
                  onChange={(event) =>
                    setObservationForm({ ...observationForm, subject_id: event.target.value })
                  }
                >
                  <option value="">No specific subject</option>
                  {subjects.map((subject) => (
                    <option key={subject.id} value={subject.id}>
                      {subject.name} · {subject.class_name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="label">Methodology</label>
                  <select
                    className="input"
                    value={observationForm.methodology}
                    onChange={(event) =>
                      setObservationForm({ ...observationForm, methodology: event.target.value })
                    }
                  >
                    {methodologies.map((item) => (
                      <option key={item.name} value={item.name}>
                        {item.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="label">Date</label>
                  <input
                    type="date"
                    className="input"
                    required
                    value={observationForm.observation_date}
                    onChange={(event) =>
                      setObservationForm({ ...observationForm, observation_date: event.target.value })
                    }
                  />
                </div>
              </div>
              <p className="text-xs text-slate-500">
                Rate each dimension from 0 to 10. These scores feed your multi-indicator analytics;
                they are not converted into a single effectiveness score.
              </p>
              {SCORE_FIELDS.map(({ key, label }) => (
                <div key={key}>
                  <div className="flex items-center justify-between">
                    <label className="label mb-1">{label}</label>
                    <span className="text-xs font-semibold text-navy-700">
                      {observationForm[key]}
                    </span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="10"
                    step="0.5"
                    className="w-full accent-green-600"
                    value={observationForm[key]}
                    onChange={(event) =>
                      setObservationForm({ ...observationForm, [key]: event.target.value })
                    }
                  />
                </div>
              ))}
              <div>
                <label className="label">Observer notes</label>
                <textarea
                  className="input"
                  rows="2"
                  maxLength="1000"
                  value={observationForm.observer_notes}
                  onChange={(event) =>
                    setObservationForm({ ...observationForm, observer_notes: event.target.value })
                  }
                />
              </div>
              <button type="submit" className="btn-primary w-full" disabled={busy}>
                {busy ? 'Saving…' : 'Save observation'}
              </button>
            </form>
          </Card>

          <Card title="Recent observations" className="xl:col-span-2">
            {observations.length ? (
              <div className="-mx-5 max-h-[560px] overflow-auto">
                <table className="min-w-full">
                  <thead className="table-head">
                    <tr>
                      <th className="px-4 py-3">Date</th>
                      <th className="px-4 py-3">Methodology</th>
                      <th className="px-4 py-3">Interaction</th>
                      <th className="px-4 py-3">Clarity</th>
                      <th className="px-4 py-3">Engagement</th>
                      <th className="px-4 py-3 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {observations.map((observation) => (
                      <tr key={observation.id} className="hover:bg-slate-50">
                        <td className="table-cell text-slate-500">{observation.observation_date}</td>
                        <td className="table-cell font-medium text-navy-900">{observation.methodology}</td>
                        <td className="table-cell text-slate-600">{observation.interaction_score}</td>
                        <td className="table-cell text-slate-600">{observation.clarity_score}</td>
                        <td className="table-cell text-slate-600">{observation.engagement_score}</td>
                        <td className="table-cell text-right">
                          <button
                            type="button"
                            className="text-xs font-semibold text-red-600 hover:underline"
                            onClick={() =>
                              remove(`/teaching/observations/${observation.id}`, 'observation')
                            }
                          >
                            Delete
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <EmptyState
                title="No observations logged yet"
                message="Record a lesson so your analytics have observation data."
              />
            )}
          </Card>
        </div>
      )}

      {tab === 'assignments' && (
        <div className="grid gap-6 xl:grid-cols-3">
          <Card title="Create an assignment" className="xl:col-span-1">
            <form className="space-y-3" onSubmit={saveAssignment}>
              <div>
                <label className="label">Subject</label>
                <select
                  className="input"
                  required
                  value={assignmentForm.subject_id}
                  onChange={(event) =>
                    setAssignmentForm({ ...assignmentForm, subject_id: event.target.value })
                  }
                >
                  <option value="">Select subject</option>
                  {subjects.map((subject) => (
                    <option key={subject.id} value={subject.id}>
                      {subject.name} · {subject.class_name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label">Title</label>
                <input
                  className="input"
                  required
                  maxLength="160"
                  value={assignmentForm.title}
                  onChange={(event) => setAssignmentForm({ ...assignmentForm, title: event.target.value })}
                />
              </div>
              <div>
                <label className="label">Instructions</label>
                <textarea
                  className="input"
                  rows="3"
                  maxLength="2000"
                  value={assignmentForm.description}
                  onChange={(event) =>
                    setAssignmentForm({ ...assignmentForm, description: event.target.value })
                  }
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="label">Due date</label>
                  <input
                    type="date"
                    className="input"
                    required
                    value={assignmentForm.due_date}
                    onChange={(event) =>
                      setAssignmentForm({ ...assignmentForm, due_date: event.target.value })
                    }
                  />
                </div>
                <div>
                  <label className="label">Max marks</label>
                  <input
                    type="number"
                    min="1"
                    className="input"
                    required
                    value={assignmentForm.max_marks}
                    onChange={(event) =>
                      setAssignmentForm({ ...assignmentForm, max_marks: event.target.value })
                    }
                  />
                </div>
              </div>
              <button type="submit" className="btn-primary w-full" disabled={busy}>
                {busy ? 'Saving…' : 'Create assignment'}
              </button>
              <p className="text-xs text-slate-500">
                The assignment is created for every student in the subject's class.
              </p>
            </form>
          </Card>

          <Card title="Assignments in your classes" className="xl:col-span-2">
            {assignments.length ? (
              <div className="-mx-5 max-h-[560px] overflow-auto">
                <table className="min-w-full">
                  <thead className="table-head">
                    <tr>
                      <th className="px-4 py-3">Title</th>
                      <th className="px-4 py-3">Subject</th>
                      <th className="px-4 py-3">Class</th>
                      <th className="px-4 py-3">Due</th>
                      <th className="px-4 py-3">Marks</th>
                      <th className="px-4 py-3 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {assignments.map((assignment) => (
                      <tr key={assignment.id} className="hover:bg-slate-50">
                        <td className="table-cell font-medium text-navy-900">{assignment.title}</td>
                        <td className="table-cell text-slate-600">{assignment.subject_name}</td>
                        <td className="table-cell text-slate-600">
                          {classes.find((item) => item.id === assignment.class_id)?.name || '—'}
                        </td>
                        <td className="table-cell text-slate-500">{assignment.due_date}</td>
                        <td className="table-cell text-slate-600">{assignment.max_marks}</td>
                        <td className="table-cell text-right">
                          <button
                            type="button"
                            className="text-xs font-semibold text-red-600 hover:underline"
                            onClick={() => remove(`/academics/assignments/${assignment.id}`, 'assignment')}
                          >
                            Delete
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <EmptyState title="No assignments yet" message="Create one with the form." />
            )}
          </Card>
        </div>
      )}

      {tab === 'activity' && (
        <div className="grid gap-6 xl:grid-cols-3">
          <Card title="Record learning activity" className="xl:col-span-1">
            <form className="space-y-3" onSubmit={saveActivity}>
              <div>
                <label className="label">Student</label>
                <select
                  className="input"
                  required
                  value={activityForm.student_id}
                  onChange={(event) =>
                    setActivityForm({ ...activityForm, student_id: event.target.value })
                  }
                >
                  <option value="">Select student</option>
                  {students.map((student) => (
                    <option key={student.id} value={student.id}>
                      {student.full_name} ({student.roll_number})
                    </option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="label">Date</label>
                  <input
                    type="date"
                    className="input"
                    required
                    value={activityForm.date}
                    onChange={(event) => setActivityForm({ ...activityForm, date: event.target.value })}
                  />
                </div>
                <div>
                  <label className="label">Study hours</label>
                  <input
                    type="number"
                    min="0"
                    max="24"
                    step="0.5"
                    className="input"
                    required
                    value={activityForm.study_hours}
                    onChange={(event) =>
                      setActivityForm({ ...activityForm, study_hours: event.target.value })
                    }
                  />
                </div>
              </div>
              {[
                { key: 'participation_score', label: 'Participation (0–10)', max: 10 },
                { key: 'engagement_score', label: 'Engagement (0–10)', max: 10 },
                { key: 'assignment_completion', label: 'Assignment completion (%)', max: 100 },
              ].map(({ key, label, max }) => (
                <div key={key}>
                  <label className="label">{label}</label>
                  <input
                    type="number"
                    min="0"
                    max={max}
                    step="1"
                    className="input"
                    required
                    value={activityForm[key]}
                    onChange={(event) => setActivityForm({ ...activityForm, [key]: event.target.value })}
                  />
                </div>
              ))}
              <div>
                <label className="label">Notes</label>
                <textarea
                  className="input"
                  rows="2"
                  maxLength="255"
                  value={activityForm.notes}
                  onChange={(event) => setActivityForm({ ...activityForm, notes: event.target.value })}
                />
              </div>
              <button type="submit" className="btn-primary w-full" disabled={busy}>
                {busy ? 'Saving…' : 'Save activity'}
              </button>
              <p className="text-xs text-slate-500">
                One entry per student per date; saving again updates that day.
              </p>
            </form>
          </Card>

          <Card
            title="Logged activity"
            subtitle={
              selectedActivitySubject
                ? selectedActivitySubject.full_name
                : 'Select a student to see their recent activity'
            }
            className="xl:col-span-2"
          >
            {activities.length ? (
              <div className="-mx-5 max-h-[560px] overflow-auto">
                <table className="min-w-full">
                  <thead className="table-head">
                    <tr>
                      <th className="px-4 py-3">Date</th>
                      <th className="px-4 py-3">Study hours</th>
                      <th className="px-4 py-3">Participation</th>
                      <th className="px-4 py-3">Engagement</th>
                      <th className="px-4 py-3">Completion</th>
                      <th className="px-4 py-3">Notes</th>
                    </tr>
                  </thead>
                  <tbody>
                    {activities.map((activity) => (
                      <tr key={activity.id} className="hover:bg-slate-50">
                        <td className="table-cell text-slate-500">{activity.date}</td>
                        <td className="table-cell text-slate-600">{activity.study_hours}</td>
                        <td className="table-cell text-slate-600">{activity.participation_score}</td>
                        <td className="table-cell text-slate-600">{activity.engagement_score}</td>
                        <td className="table-cell text-slate-600">{activity.assignment_completion}%</td>
                        <td className="table-cell max-w-xs truncate text-slate-500">
                          {activity.notes || '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <EmptyState
                title="No activity loaded"
                message="Choose a student to view or update their learning activity."
              />
            )}
          </Card>
        </div>
      )}
    </div>
  )
}
