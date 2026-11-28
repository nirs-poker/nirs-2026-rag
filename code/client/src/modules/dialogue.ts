import type { AskRequest, HistoryMessage } from '../api/contracts'
import type { Chat } from './chatTypes'

export function buildDialogueRequest(question: string, chat: Chat | undefined, handId: string | null): AskRequest {
  const messages = handId === null ? chat?.messages ?? [] : chat?.hands.find(hand => hand.id === handId)?.messages ?? []
  const history: HistoryMessage[] = []
  let remaining = 8000
  for (const message of messages.slice(-12).reverse()) {
    const content = Array.from(message.text).slice(0, 1500).join('')
    if (!content.trim() || Array.from(content).length > remaining) continue
    remaining -= Array.from(content).length
    history.unshift({ role: message.role === 'bot' ? 'assistant' : 'user', content })
  }
  const request = { question, history, ...(chat?.style ? { style: chat.style } : {}) }
  while (history.length && new TextEncoder().encode(JSON.stringify(request)).length > 32000) history.shift()
  return request
}
