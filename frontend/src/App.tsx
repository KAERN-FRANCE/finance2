import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import DocumentsPage from './pages/DocumentsPage'
import MeetingSetupPage from './pages/MeetingSetupPage'
import MeetingPage from './pages/MeetingPage'
import ReportPage from './pages/ReportPage'
import MeetingsListPage from './pages/MeetingsListPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/documents" replace />} />
          <Route path="documents" element={<DocumentsPage />} />
          <Route path="meetings" element={<MeetingsListPage />} />
          <Route path="meetings/new" element={<MeetingSetupPage />} />
          <Route path="meetings/:meetingId" element={<MeetingPage />} />
          <Route path="reports/:reportId" element={<ReportPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
