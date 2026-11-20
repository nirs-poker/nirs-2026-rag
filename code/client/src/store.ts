import { configureStore } from '@reduxjs/toolkit'
import { useDispatch, useSelector } from 'react-redux'
import { saveWorkspace } from './modules/sessionStorage'
import workspace from './slices/chatsSlice'
import trainer from './slices/trainerSlice'

export const store = configureStore({ reducer: { workspace, trainer } })
let lastSaved = store.getState().workspace

store.subscribe(() => {
  const current = store.getState().workspace
  if (current === lastSaved) return
  if (saveWorkspace(current)) lastSaved = current
  else window.dispatchEvent(new Event('poker-storage-error'))
})

export const useAppDispatch = useDispatch.withTypes<typeof store.dispatch>()
export const useAppSelector = useSelector.withTypes<ReturnType<typeof store.getState>>()
