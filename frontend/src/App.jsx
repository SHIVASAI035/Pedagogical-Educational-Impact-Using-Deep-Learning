import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './auth/AuthContext'
import ProtectedRoute, { homeFor } from './auth/ProtectedRoute'
import Layout from './components/Layout'
import Login from './pages/Login'
import Register from './pages/Register'
import NotFound from './pages/NotFound'
import Profile from './pages/Profile'
import AdminDashboard from './pages/admin/AdminDashboard'
import Users from './pages/admin/Users'
import Academics from './pages/admin/Academics'
import ModelMetrics from './pages/admin/ModelMetrics'
import AdminReports from './pages/admin/AdminReports'
import TeacherReport from './pages/admin/TeacherReport'
import TeacherDashboard from './pages/teacher/TeacherDashboard'
import TeacherStudents from './pages/teacher/TeacherStudents'
import StudentDetail from './pages/teacher/StudentDetail'
import MarksEntry from './pages/teacher/MarksEntry'
import AttendanceEntry from './pages/teacher/AttendanceEntry'
import TeacherClassroom from './pages/teacher/TeacherClassroom'
import FeedbackInsights from './pages/teacher/FeedbackInsights'
import TeacherRecommendations from './pages/teacher/TeacherRecommendations'
import StudentDashboard from './pages/student/StudentDashboard'
import StudentPerformance from './pages/student/StudentPerformance'
import StudentFeedback from './pages/student/StudentFeedback'
import StudentRecommendations from './pages/student/StudentRecommendations'
import ImpactAnalysis from './pages/shared/ImpactAnalysis'

function HomeRedirect() {
  const { user } = useAuth()
  if (!user) return <Navigate to="/login" replace />
  return <Navigate to={homeFor(user.role)} replace />
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/" element={<HomeRedirect />} />

      <Route
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route path="/profile" element={<Profile />} />

        <Route
          path="/admin"
          element={
            <ProtectedRoute roles={['admin']}>
              <AdminDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/users"
          element={
            <ProtectedRoute roles={['admin']}>
              <Users />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/academics"
          element={
            <ProtectedRoute roles={['admin']}>
              <Academics />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/model"
          element={
            <ProtectedRoute roles={['admin']}>
              <ModelMetrics />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/reports"
          element={
            <ProtectedRoute roles={['admin']}>
              <AdminReports />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/teachers/:teacherId"
          element={
            <ProtectedRoute roles={['admin']}>
              <TeacherReport />
            </ProtectedRoute>
          }
        />

        <Route
          path="/teacher"
          element={
            <ProtectedRoute roles={['teacher']}>
              <TeacherDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/teacher/students"
          element={
            <ProtectedRoute roles={['teacher']}>
              <TeacherStudents />
            </ProtectedRoute>
          }
        />
        <Route
          path="/teacher/students/:studentId"
          element={
            <ProtectedRoute roles={['teacher', 'admin']}>
              <StudentDetail />
            </ProtectedRoute>
          }
        />
        <Route
          path="/teacher/marks"
          element={
            <ProtectedRoute roles={['teacher']}>
              <MarksEntry />
            </ProtectedRoute>
          }
        />
        <Route
          path="/teacher/attendance"
          element={
            <ProtectedRoute roles={['teacher']}>
              <AttendanceEntry />
            </ProtectedRoute>
          }
        />
        <Route
          path="/teacher/classroom"
          element={
            <ProtectedRoute roles={['teacher']}>
              <TeacherClassroom />
            </ProtectedRoute>
          }
        />
        <Route
          path="/teacher/feedback"
          element={
            <ProtectedRoute roles={['teacher']}>
              <FeedbackInsights />
            </ProtectedRoute>
          }
        />
        <Route
          path="/teacher/recommendations"
          element={
            <ProtectedRoute roles={['teacher']}>
              <TeacherRecommendations />
            </ProtectedRoute>
          }
        />

        <Route
          path="/student"
          element={
            <ProtectedRoute roles={['student']}>
              <StudentDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/student/performance"
          element={
            <ProtectedRoute roles={['student']}>
              <StudentPerformance />
            </ProtectedRoute>
          }
        />
        <Route
          path="/student/feedback"
          element={
            <ProtectedRoute roles={['student']}>
              <StudentFeedback />
            </ProtectedRoute>
          }
        />
        <Route
          path="/student/recommendations"
          element={
            <ProtectedRoute roles={['student']}>
              <StudentRecommendations />
            </ProtectedRoute>
          }
        />

        <Route
          path="/impact"
          element={
            <ProtectedRoute roles={['admin', 'teacher']}>
              <ImpactAnalysis />
            </ProtectedRoute>
          }
        />
      </Route>

      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}
