import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { Provider } from 'react-redux'
import '../css/common.css'
import App from './App'
import { store } from './store'

const root = document.getElementById('root')
if (!root) throw new Error('Не найден корневой элемент фронтенда.')

createRoot(root).render(<StrictMode><Provider store={store}><App /></Provider></StrictMode>)
