import { Routes, Route } from 'react-router-dom'
import FileUploadPage from './pages/FileUploadPage'
import DashboardPage from './pages/DashboardPage'

function App() {
  return (
    <Routes>
      <Route path="/" element={<FileUploadPage />} />
      <Route path="/board/:boardId" element={<DashboardPage />} />
    </Routes>
  )
}

export default App 