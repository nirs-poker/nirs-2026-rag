import { createSlice, type PayloadAction } from '@reduxjs/toolkit'
import type { Message } from '../modules/chatTypes'
import { loadWorkspace } from '../modules/sessionStorage'

const chatsSlice = createSlice({
  name: 'workspace',
  initialState: loadWorkspace,
  reducers: {
    createChat(state, { payload: { id, message } }: PayloadAction<{ id: string; message: Message }>) {
      state.chats.unshift({ id, title: 'Новый чат', draft: '', messages: [message], hands: [], selectedHandId: null })
      state.activeChatId = id
    },
    openChat(state, { payload: id }: PayloadAction<string>) {
      if (state.chats.some(chat => chat.id === id)) state.activeChatId = id
    },
    openNewDraft(state) {
      state.activeChatId = null
    },
    renameChat(state, { payload: { id, title } }: PayloadAction<{ id: string; title: string }>) {
      const chat = state.chats.find(chat => chat.id === id)
      if (chat && title.trim()) chat.title = title.trim()
    },
    deleteChat(state, { payload: id }: PayloadAction<string>) {
      state.chats = state.chats.filter(chat => chat.id !== id)
      if (state.activeChatId === id) state.activeChatId = state.chats[0]?.id ?? null
    },
    setDraft(state, { payload: { chatId, text } }: PayloadAction<{ chatId: string; text: string }>) {
      const chat = state.chats.find(chat => chat.id === chatId)
      if (chat) chat.draft = text
    },
    addMessage(state, { payload: { chatId, handId, message } }: PayloadAction<{ chatId: string; handId: string | null; message: Message }>) {
      const chat = state.chats.find(chat => chat.id === chatId)
      if (!chat) return
      const hand = chat.hands.find(hand => hand.id === handId)
      if (handId !== null && !hand) return
      if (hand) {
        hand.messages.push(message)
      } else {
        chat.messages.push({ ...message, afterHandId: chat.hands.at(-1)?.id })
      }
      if (message.role === 'user') {
        chat.draft = ''
        if (hand) hand.open = true
      }
    },
    selectHand(state, { payload: { chatId, handId } }: PayloadAction<{ chatId: string; handId: string }>) {
      const chat = state.chats.find(chat => chat.id === chatId)
      if (chat?.hands.some(hand => hand.id === handId)) chat.selectedHandId = handId
    },
    leaveHand(state, { payload: chatId }: PayloadAction<string>) {
      const chat = state.chats.find(chat => chat.id === chatId)
      if (chat) chat.selectedHandId = null
    },
    setHandOpen(state, { payload: { chatId, handId, open } }: PayloadAction<{ chatId: string; handId: string; open: boolean }>) {
      const hand = state.chats.find(chat => chat.id === chatId)?.hands.find(hand => hand.id === handId)
      if (hand) hand.open = open
    },
    setStep(state, { payload: { chatId, handId, index } }: PayloadAction<{ chatId: string; handId: string; index: number }>) {
      const hand = state.chats.find(chat => chat.id === chatId)?.hands.find(hand => hand.id === handId)
      if (hand && index >= 0 && index < hand.steps.length) hand.stepIndex = index
    },
  },
})

export const { createChat, openChat, openNewDraft, renameChat, deleteChat, setDraft, addMessage, selectHand, leaveHand, setHandOpen, setStep } = chatsSlice.actions
export default chatsSlice.reducer
