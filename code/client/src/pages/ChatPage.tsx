import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import { ChatSidebar } from '../components/ChatSidebar'
import { ChatFeed } from '../components/ChatFeed'
import { Composer } from '../components/Composer'
import { HandTable } from '../components/HandTable'
import { TableSetup } from '../components/TableSetup'
import type { Chat } from '../modules/chatTypes'
import { loadChatView, saveChatView } from '../modules/sessionStorage'
import { deleteChat, leaveHand, openChat, openNewDraft, renameChat, selectHand, setDraft, setHandOpen, setStep } from '../slices/chatsSlice'
import { sendChatQuestion } from '../slices/trainerSlice'
import { useAppDispatch, useAppSelector } from '../store'
import '../../css/chat.css'
import './ChatPage.css'

function ChatView({ chat, isNew, openVersion, onDraft }: {
  chat: Chat
  isNew: boolean
  openVersion: number
  onDraft: (text: string) => void
}) {
  const dispatch = useAppDispatch()
  const viewId = isNew ? null : chat.id
  const [initialView] = useState(() => openVersion === 0 ? loadChatView(viewId) : null)
  const [handEndToReveal, setHandEndToReveal] = useState<string | null>(null)
  const [setupMinHeight, setSetupMinHeight] = useState(initialView?.setupMinHeight)
  const [returnVisible, setReturnVisible] = useState(false)
  const request = useAppSelector(state => state.trainer[chat.id])
  const messageId = request?.messageId
  const feed = useRef<HTMLDivElement>(null)
  const table = useRef<HTMLElement>(null)
  const hand = chat.hands.find(hand => hand.id === chat.selectedHandId)

  useEffect(() => {
    const root = feed.current
    const target = table.current
    if (!root || !target) return
    const scene = target.querySelector('.scene')
    if (!scene) return
    const observer = new IntersectionObserver(([entry]) => {
      setReturnVisible(!entry.isIntersecting && entry.boundingClientRect.bottom <= (entry.rootBounds?.top ?? 0))
    }, { root })
    observer.observe(scene)
    return () => observer.disconnect()
  }, [hand?.id])

  useLayoutEffect(() => {
    if (!handEndToReveal || hand?.id !== handEndToReveal || !hand.open) return
    document.getElementById(handEndToReveal)?.scrollIntoView({ block: 'end' })
    setHandEndToReveal(null)
  }, [handEndToReveal, hand?.id, hand?.open])

  useLayoutEffect(() => {
    if (!messageId) return
    const message = document.getElementById(`message-${messageId}`)
    const thread = message?.closest('.hand-thread')
    if (thread && !thread.matches('[open][data-selected]')) return
    message?.scrollIntoView({ block: 'nearest' })
  }, [messageId])

  useLayoutEffect(() => {
    const root = feed.current
    if (!root) return
    if (openVersion === 0 && initialView && initialView.chatId === viewId) {
      root.scrollTo({ top: initialView.scrollTop, behavior: 'instant' })
    } else if (!isNew) {
      root.scrollTo({ top: root.scrollHeight, behavior: 'instant' })
    }
  }, [initialView, isNew, openVersion, viewId])

  useEffect(() => {
    function saveView() {
      const root = feed.current
      if (!root) return
      saveChatView({
        chatId: viewId,
        scrollTop: root.scrollTop,
        setupOpen: root.querySelector('details.table-placeholder[open]') !== null,
        setupMinHeight,
      })
    }
    window.addEventListener('pagehide', saveView)
    return () => window.removeEventListener('pagehide', saveView)
  }, [viewId, setupMinHeight])

  function send() {
    void dispatch(sendChatQuestion({ chatId: chat.id, handId: chat.selectedHandId, text: chat.draft, newChat: isNew }))
  }

  function goToHandEnd() {
    if (!hand) return
    if (hand.open) document.getElementById(hand.id)?.scrollIntoView({ block: 'end' })
    else {
      setHandEndToReveal(hand.id)
      dispatch(setHandOpen({ chatId: chat.id, handId: hand.id, open: true }))
    }
  }

  function chooseHand(id: string) {
    setHandEndToReveal(id)
    setSetupMinHeight(undefined)
    dispatch(selectHand({ chatId: chat.id, handId: id }))
  }

  function exitHand() {
    setSetupMinHeight(table.current?.getBoundingClientRect().height)
    dispatch(leaveHand(chat.id))
    setHandEndToReveal(null)
    setReturnVisible(false)
  }

  return (
    <main className="main">
      <header className="topbar">
        <h2>{chat.title}</h2>
      </header>
      <div className="scroll" ref={feed}>
        <div className="floor">
          {hand
            ? <HandTable
                hand={hand}
                sectionRef={table}
                onStep={index => dispatch(setStep({ chatId: chat.id, handId: hand.id, index }))}
                onGoToHand={goToHandEnd}
              />
            : <div style={{ minHeight: setupMinHeight }}><TableSetup showEmptyTable={chat.hands.length > 0 || initialView?.setupOpen === true} /></div>}
          <ChatFeed
            chat={chat}
            onSelect={chooseHand}
            onToggle={(id, open) => dispatch(setHandOpen({ chatId: chat.id, handId: id, open }))}
          />
        </div>
      </div>
      <Composer
        draft={chat.draft}
        status={request?.status || ''}
        pending={Boolean(request?.pending)}
        returnVisible={Boolean(hand && returnVisible)}
        onLeaveHand={hand ? exitHand : undefined}
        onDraft={onDraft}
        onSubmit={send}
        onReturn={() => {
          table.current?.scrollIntoView({ block: 'start' })
          table.current?.focus({ preventScroll: true })
        }}
      />
    </main>
  )
}

function createChatDraft(): Chat {
  return { id: crypto.randomUUID(), title: 'Новый чат', draft: '', messages: [], hands: [], selectedHandId: null }
}

export default function ChatPage() {
  const dispatch = useAppDispatch()
  const { chats, activeChatId } = useAppSelector(state => state.workspace)
  const [newChat, setNewChat] = useState<Chat | null>(() => activeChatId === null ? createChatDraft() : null)
  const [openVersion, setOpenVersion] = useState(0)
  const draftSaved = newChat !== null && chats.some(chat => chat.id === newChat.id)
  const draft = draftSaved ? null : newChat
  const chat = draft ?? chats.find(chat => chat.id === activeChatId)
  const [storageError, setStorageError] = useState(false)

  useEffect(() => {
    if (draftSaved) setNewChat(null)
  }, [draftSaved])

  useEffect(() => {
    const showError = () => setStorageError(true)
    window.addEventListener('poker-storage-error', showError)
    return () => window.removeEventListener('poker-storage-error', showError)
  }, [])

  return (
    <>
      <div className="app">
        <ChatSidebar
          chats={chats}
          activeId={draft ? null : activeChatId}
          onCreate={() => {
            setNewChat(current => current ?? createChatDraft())
            dispatch(openNewDraft())
          }}
          onOpen={id => {
            setNewChat(null)
            dispatch(openChat(id))
            setOpenVersion(version => version + 1)
          }}
          onRename={(id, title) => {
            const value = window.prompt('Название чата', title)
            if (value?.trim()) dispatch(renameChat({ id, title: value.trim().slice(0, 120) }))
          }}
          onDelete={id => {
            if (window.confirm('Удалить чат со всеми сообщениями и раздачами?')) dispatch(deleteChat(id))
          }}
        />
        {chat ? (
          <ChatView
            chat={chat}
            key={chat.id}
            isNew={draft !== null}
            openVersion={openVersion}
            onDraft={text => {
              if (draft) setNewChat({ ...draft, draft: text })
              else dispatch(setDraft({ chatId: chat.id, text }))
            }}
          />
        ) : <main className="main"><header className="topbar"><h2>Чаты</h2></header></main>}
      </div>
      {storageError && <p className="storage-error" role="alert">Не удалось сохранить изменения в этой вкладке.</p>}
    </>
  )
}
