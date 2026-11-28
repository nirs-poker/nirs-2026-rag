import { createAsyncThunk, createSlice } from '@reduxjs/toolkit'
import { requestTrainerReply, questionError } from '../modules/trainerApi'
import { buildDialogueRequest } from '../modules/dialogue'
import type { Workspace } from '../modules/chatTypes'
import { addMessage, createChat, deleteChat, setChatStyle } from './chatsSlice'

interface RequestState {
  pending: boolean
  status: string
  messageId?: string
}

type TrainerState = Record<string, RequestState | undefined>

interface ChatQuestion {
  chatId: string
  handId: string | null
  text: string
  newChat: boolean
}

export const sendChatQuestion = createAsyncThunk<
  Omit<RequestState, 'pending'>,
  ChatQuestion,
  { state: { trainer: TrainerState; workspace: Workspace }; rejectValue: string }
>(
  'trainer/sendChatQuestion',
  async ({ chatId, handId, text, newChat }, { dispatch, getState, signal, requestId, rejectWithValue }) => {
    const question = text.trim()
    const error = questionError(question)
    if (error) return rejectWithValue(error)

    const chat = newChat ? undefined : getState().workspace.chats.find(chat => chat.id === chatId)
    const payload = buildDialogueRequest(question, chat, handId)
    const message = { id: requestId, role: 'user' as const, text: question }
    if (newChat) dispatch(createChat({ id: chatId, message }))
    else dispatch(addMessage({ chatId, handId, message }))

    try {
      const reply = await requestTrainerReply(payload, signal)
      if (reply.style) dispatch(setChatStyle({ chatId, style: reply.style }))
      dispatch(addMessage({ chatId, handId, message: reply.message }))
      return { status: '', messageId: reply.message.id }
    } catch (error) {
      const reason = error instanceof Error && error.name === 'Error'
        ? error.message
        : 'Не удалось подключиться к серверу тренера.'
      return { status: `Вопрос сохранён. ${reason}`, messageId: message.id }
    }
  },
  {
    condition: ({ chatId, text }, { getState }) => Boolean(text.trim()) && !getState().trainer[chatId]?.pending,
  },
)

const trainerSlice = createSlice({
  name: 'trainer',
  initialState: {} as TrainerState,
  reducers: {},
  extraReducers: builder => {
    builder
      .addCase(sendChatQuestion.pending, (state, { meta }) => {
        state[meta.arg.chatId] = {
          pending: true, status: 'Получаем ответ тренера…', messageId: meta.requestId,
        }
      })
      .addCase(sendChatQuestion.fulfilled, (state, { meta, payload }) => {
        if (state[meta.arg.chatId]) state[meta.arg.chatId] = { ...payload, pending: false }
      })
      .addCase(sendChatQuestion.rejected, (state, { meta, payload }) => {
        if (state[meta.arg.chatId]) {
          state[meta.arg.chatId] = { pending: false, status: payload ?? 'Отправка прервана.' }
        }
      })
      .addCase(deleteChat, (state, { payload }) => { delete state[payload] })
  },
})

export default trainerSlice.reducer
