import { useParams } from 'react-router-dom'
import TeacherDashboard from '../teacher/TeacherDashboard'

export default function TeacherReport() {
  const { teacherId } = useParams()
  return <TeacherDashboard teacherId={Number(teacherId)} />
}
