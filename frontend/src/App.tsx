import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { ProtectedRoute } from './components/ProtectedRoute'
import { Layout } from './components/Layout'
import { LoginPage } from './pages/LoginPage'
import { RegisterPage } from './pages/RegisterPage'
import { DocumentsPage } from './pages/DocumentsPage'
import { ConversationsPage } from './pages/ConversationsPage'
import { ConversationPage } from './pages/ConversationPage'

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route element={<ProtectedRoute />}>
            <Route element={<Layout />}>
              <Route path="/" element={<Navigate to="/documents" replace />} />
              <Route path="/documents" element={<DocumentsPage />} />
              <Route path="/conversations" element={<ConversationsPage />} />
              <Route path="/conversations/:conversationId" element={<ConversationPage />} />
            </Route>
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
