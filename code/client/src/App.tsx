import { HashRouter, Navigate, Route, Routes } from 'react-router-dom'
import { routes } from './Routes'
import ChatPage from './pages/ChatPage'
import AuthPage from './pages/AuthPage'

export default function App() {
  return (
    <HashRouter>
      <Routes>
        <Route path={routes.chat} element={<ChatPage />} />
        <Route path={routes.login} element={<AuthPage key="login" mode="login" />} />
        <Route path={routes.register} element={<AuthPage key="register" mode="register" />} />
        <Route path="*" element={<Navigate to={routes.chat} replace />} />
      </Routes>
    </HashRouter>
  )
}
