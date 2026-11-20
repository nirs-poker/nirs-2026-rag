import { Link } from 'react-router-dom'
import type { Chat } from '../modules/chatTypes'
import { routes } from '../Routes'

interface Props {
  chats: Chat[]
  activeId: string | null
  onCreate: () => void
  onOpen: (id: string) => void
  onRename: (id: string, title: string) => void
  onDelete: (id: string) => void
}

export function ChatSidebar({ chats, activeId, onCreate, onOpen, onRename, onDelete }: Props) {
  return (
    <aside className="chat-panel" aria-label="Чаты">
      <div className="brand"><h1>Покерный тренер</h1></div>
      <button className="new-chat" type="button" onClick={onCreate}>+ Новый чат</button>
      <nav className="history" aria-label="История чатов">
        {chats.map(chat => (
          <div className="chat-row" key={chat.id}>
            <button className={`item${chat.id === activeId ? ' active' : ''}`} type="button" onClick={() => onOpen(chat.id)} aria-current={chat.id === activeId ? 'true' : undefined}>
              <span className="item-title">{chat.title}</span>
            </button>
            <div className="chat-row-actions" role="group" aria-label={`Действия с чатом «${chat.title}»`}>
              <button className="chat-action" type="button" aria-label="Переименовать" title="Переименовать" onClick={() => onRename(chat.id, chat.title)}>
                <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
                  <path d="m13.5 6.5 4 4M4 20l4.5-1 11-11a2.8 2.8 0 0 0-4-4l-11 11L4 20Z" />
                </svg>
              </button>
              <button className="chat-action" type="button" aria-label="Удалить" title="Удалить" onClick={() => onDelete(chat.id)}>
                <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
                  <path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13M10 10v7m4-7v7" />
                </svg>
              </button>
            </div>
          </div>
        ))}
      </nav>
      <div className="profile">
        <span className="avatar" aria-hidden="true">С</span>
        <div className="who"><div className="who-name">Степан</div><div className="who-mail">stepan@example.com</div></div>
        <Link className="logout" to={routes.login}>Выйти</Link>
      </div>
    </aside>
  )
}
