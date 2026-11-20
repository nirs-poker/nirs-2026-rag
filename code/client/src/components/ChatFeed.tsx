import { Fragment } from 'react'
import { cardLabel, formatBB, type Chat, type Hand, type Message } from '../modules/chatTypes'
import { PlayingCard } from './PokerTable'

function MessageList({ messages }: { messages: Message[] }) {
  return messages.map(message => (
    <div className={`msg ${message.role}`} key={message.id} id={`message-${message.id}`}>
      <div className="bubble">
        {message.heading && <div className="rec-action">{message.heading}</div>}
        <p>{message.text}</p>
        {message.sources && message.sources.length > 0 && (
          <details className="message-sources">
            <summary>Источники · {message.sources.length}</summary>
            <ul>
              {message.sources.map(source => (
                <li key={source.id}>
                  <strong>{source.id} · {source.title}</strong>
                  <p>{source.text}</p>
                </li>
              ))}
            </ul>
          </details>
        )}
      </div>
    </div>
  ))
}

function HandThread({ hand, selected, onSelect, onToggle }: {
  hand: Hand
  selected: boolean
  onSelect: () => void
  onToggle: (open: boolean) => void
}) {
  const latest = hand.steps.at(-1)
  const boardLength = latest?.board.length ?? 0
  const street = boardLength === 5 ? 'Ривер' : boardLength === 4 ? 'Тёрн' : boardLength === 3 ? 'Флоп' : 'Префлоп'
  return (
    <details
      className="hand-thread"
      id={hand.id}
      data-selected={selected || undefined}
      open={hand.open}
      onToggle={event => onToggle(event.currentTarget.open)}
    >
      <summary className="hand-summary">
        <span className="hand-cards" role="img" aria-label={hand.cards.map(cardLabel).join(' ')}>
          {hand.cards.map(card => <PlayingCard key={card} card={card} />)}
        </span>
        <span className="hand-summary-info">
          {hand.heroPosition} против {hand.opponentPosition}
          <small>{street}{latest && latest.pot !== null ? ` · ${formatBB(latest.pot)}` : ''}</small>
        </span>
      </summary>
      <div className="hand-messages">
        <button className="control primary hand-selection" type="button" onClick={onSelect} disabled={selected}>Выбрать</button>
        {hand.setup?.actions && <p className="hand-context">{hand.setup.actions}</p>}
        {hand.setup && hand.setup.ante > 0 && <p className="hand-context">Анте {formatBB(hand.setup.ante)}</p>}
        <MessageList messages={hand.messages} />
      </div>
    </details>
  )
}

export function ChatFeed({ chat, onSelect, onToggle }: {
  chat: Chat
  onSelect: (id: string) => void
  onToggle: (id: string, open: boolean) => void
}) {
  const hands = new Set(chat.hands.map(hand => hand.id))
  const messagesByHand = new Map<string | undefined, Message[]>()
  for (const message of chat.messages) {
    const handId = message.afterHandId && hands.has(message.afterHandId) ? message.afterHandId : undefined
    const messages = messagesByHand.get(handId)
    if (messages) messages.push(message)
    else messagesByHand.set(handId, [message])
  }
  return (
    <div className="chat" aria-label="Сообщения чата">
      <div className="inner">
        <MessageList messages={messagesByHand.get(undefined) ?? []} />
        {chat.hands.map(hand => (
          <Fragment key={hand.id}>
            <HandThread
              hand={hand}
              selected={chat.selectedHandId === hand.id}
              onSelect={() => onSelect(hand.id)}
              onToggle={open => onToggle(hand.id, open)}
            />
            <MessageList messages={messagesByHand.get(hand.id) ?? []} />
          </Fragment>
        ))}
      </div>
    </div>
  )
}
