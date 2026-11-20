import type { Chat, Message, Workspace } from './chatTypes'
import { demoWorkspace } from './demo'
import { demoIntro, demoTitle, hand1Messages, hand2Messages } from './demoMessages'

const key = 'poker-trainer:workspace:v1'
const viewKey = 'poker-trainer:chat-view:v1'

interface ChatViewSnapshot {
  chatId: string | null
  scrollTop: number
  setupOpen: boolean
  setupMinHeight?: number
}

export function loadChatView(chatId: string | null): ChatViewSnapshot | null {
  const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming | undefined
  if (navigation?.type !== 'reload') return null
  try {
    const raw = window.sessionStorage.getItem(viewKey)
    const view = raw ? JSON.parse(raw) as ChatViewSnapshot : null
    return view?.chatId === chatId && Number.isFinite(view.scrollTop) ? view : null
  } catch {
    return null
  }
}

export function saveChatView(view: ChatViewSnapshot) {
  try {
    window.sessionStorage.setItem(viewKey, JSON.stringify(view))
  } catch {
    // Scroll restoration is optional if storage is unavailable.
  }
}

function refreshDemoChat(chat: Chat): Chat {
  if (chat.id !== 'demo') return chat
  const refresh = (messages: Message[], demo: Message[]) =>
    messages.map(message => demo.find(example => example.id === message.id) ?? message)

  return {
    ...chat,
    title: chat.title === 'Защита большого блайнда' ? demoTitle : chat.title,
    messages: chat.messages.map(message =>
      demoIntro.find(example => example.id === message.id)
      ?? { ...message, afterHandId: message.afterHandId ?? chat.hands.at(-1)?.id },
    ),
    hands: chat.hands.map(hand => {
      if (hand.id === 'hand-1') return { ...hand, messages: refresh(hand.messages, hand1Messages) }
      if (hand.id === 'hand-2') return { ...hand, messages: refresh(hand.messages, hand2Messages) }
      return hand
    }),
  }
}

export function loadWorkspace(): Workspace {
  try {
    const stored = window.sessionStorage.getItem(key)
    if (stored !== null) {
      const workspace = JSON.parse(stored) as Workspace | null
      if (workspace && Array.isArray(workspace.chats) && (
        workspace.activeChatId === null || workspace.chats.some(chat => chat.id === workspace.activeChatId)
      )) {
        const chats = workspace.chats.filter(chat => chat.id !== 'turn').map(refreshDemoChat)
        return {
          chats,
          activeChatId: workspace.activeChatId === 'turn' ? (chats[0]?.id ?? null) : workspace.activeChatId,
        }
      }
    }
  } catch {
    // Keep the frontend usable when storage is blocked or the entry is invalid.
  }
  return demoWorkspace()
}

export function saveWorkspace(workspace: Workspace): boolean {
  try {
    window.sessionStorage.setItem(key, JSON.stringify(workspace))
    return true
  } catch {
    return false
  }
}
