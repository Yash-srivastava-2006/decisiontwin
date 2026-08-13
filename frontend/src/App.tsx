import { Navigate, Route, Routes } from 'react-router-dom'
import { AppShell } from './components/layout/AppShell'
import { DashboardPage } from './pages/DashboardPage'
import { DatasetListPage } from './pages/DatasetListPage'
import { DatasetPage } from './pages/DatasetPage'
import { UploadPage } from './pages/UploadPage'
import { AnalyticsPage } from './pages/AnalyticsPage'
import { InsightsPage } from './pages/InsightsPage'
import { SettingsPage } from './pages/SettingsPage'

function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/datasets" element={<DatasetListPage />} />
        <Route path="/datasets/:datasetId" element={<DatasetPage />} />
        <Route path="/upload" element={<UploadPage />} />
        <Route path="/analytics" element={<AnalyticsPage />} />
        <Route path="/insights" element={<InsightsPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppShell>
  )
}

export default App



