import { useState } from 'react'
import { positions, ranks, suits, type Suit } from '../modules/chatTypes'
import { PokerTable } from './PokerTable'

interface CardDraft {
  rank: string
  suit: Suit | ''
}

interface CardPickerProps {
  name: string
  label: string
  card: CardDraft
  otherCards: CardDraft[]
  disabled?: boolean
  onChange: (card: CardDraft) => void
}

const emptyCard: CardDraft = { rank: '', suit: '' }
const suitCodes = Object.keys(suits) as Suit[]
const complete = ({ rank, suit }: CardDraft) => Boolean(rank && suit)
const slots = [
  { name: 'hero_1', label: 'первой карты' },
  { name: 'hero_2', label: 'второй карты' },
  { name: 'flop_1', label: 'первой карты флопа' },
  { name: 'flop_2', label: 'второй карты флопа' },
  { name: 'flop_3', label: 'третьей карты флопа' },
  { name: 'turn', label: 'тёрна' },
  { name: 'river', label: 'ривера' },
]

function CardPicker({ name, label, card: { rank, suit }, otherCards, disabled, onChange }: CardPickerProps) {
  function taken(candidate: CardDraft) {
    return complete(candidate) && otherCards.some(card => card.rank === candidate.rank && card.suit === candidate.suit)
  }

  function rankUnavailable(candidate: string) {
    return suit
      ? taken({ rank: candidate, suit })
      : suitCodes.every(option => taken({ rank: candidate, suit: option }))
  }

  return (
    <div className={`card-picker pcard${disabled ? ' card-picker-disabled' : ''}`}>
      <div className="card-picker-value">
        <span aria-hidden="true">{rank || '+'}</span>
        <select name={`${name}_rank`} aria-label={`Ранг ${label}`} value={rank} disabled={disabled} onChange={event => onChange({ rank: event.target.value, suit })}>
          <option value="">Выбрать ранг</option>
          {ranks.map(option => <option key={option} disabled={rankUnavailable(option)}>{option}</option>)}
        </select>
      </div>
      <div className={`card-picker-value${suit === 'h' || suit === 'd' ? ' red-suit' : ''}`}>
        <span aria-hidden="true">{suit ? suits[suit] : '♢'}</span>
        <select name={`${name}_suit`} aria-label={`Масть ${label}`} value={suit} disabled={disabled} onChange={event => onChange({ rank, suit: event.target.value as Suit | '' })}>
          <option value="">Выбрать масть</option>
          {suitCodes.map(option => <option key={option} value={option} disabled={taken({ rank, suit: option })}>{suits[option]}</option>)}
        </select>
      </div>
    </div>
  )
}

function PlayerSetup({ role, position, otherPosition, onPositionChange }: {
  role: 'hero' | 'opponent'
  position: string
  otherPosition: string
  onPositionChange: (position: string) => void
}) {
  const isHero = role === 'hero'
  return (
    <div className="setup-seat">
      <label className="setup-position">
        <b>{isHero ? 'Вы' : 'Соперник'}</b>
        <select name={`${role}_position`} aria-label={isHero ? 'Ваша позиция' : 'Позиция соперника'} value={position} onChange={event => onPositionChange(event.target.value)} required>
          <option value="">Поз.</option>
          {positions.map(option => <option key={option} disabled={option === otherPosition}>{option}</option>)}
        </select>
      </label>
      <label className="setup-stack">
        <input type="number" name={`${role}_stack`} aria-label={isHero ? 'Ваш стек в ББ' : 'Стек соперника в ББ'} min="0.01" step="0.01" defaultValue={100} required /> ББ
      </label>
    </div>
  )
}

export function TableSetup({ showEmptyTable }: { showEmptyTable: boolean }) {
  const [cards, setCards] = useState(() => slots.map(() => emptyCard))
  const [heroPosition, setHeroPosition] = useState('')
  const [opponentPosition, setOpponentPosition] = useState('')
  const flopComplete = cards.slice(2, 5).every(complete)
  const turnComplete = flopComplete && complete(cards[5])

  function updateCard(index: number, card: CardDraft) {
    setCards(previous => {
      const next = previous.map((value, position) => position === index ? card : value)
      if (!next.slice(2, 5).every(complete)) next[5] = emptyCard
      if (!complete(next[5])) next[6] = emptyCard
      return next
    })
  }

  function renderCard(index: number) {
    const { name, label } = slots[index]
    return (
      <CardPicker
        key={name}
        name={name}
        label={label}
        card={cards[index]}
        otherCards={cards.filter((_, position) => position !== index)}
        disabled={index === 5 ? !flopComplete : index === 6 && !turnComplete}
        onChange={card => updateCard(index, card)}
      />
    )
  }

  return (
    <details className="table-placeholder" open={showEmptyTable || undefined}>
      <summary className="table-toggle">
        <span className="mini-table" aria-hidden="true"><span className="mini-board"><i /><i /><i /></span></span>
        <span className="table-toggle-label">Добавить стол</span>
      </summary>
      <div className="step-state empty-steps" aria-hidden="true" />
      <div className="hand-setup" role="group" aria-label="Параметры раздачи">
        <PokerTable
          setup
          renderBoardSlot={index => renderCard(index + 2)}
          pot={(
            <div className="pot setup-pot">
              <label title="Фишки в центре на текущий момент">Банк <input type="number" name="pot" min="0" step="0.01" /></label>
              <label>ББ <input type="number" name="big_blind" aria-label="Размер большого блайнда" min="0.01" step="0.01" /></label>
              <label>Анте <input type="number" name="ante" min="0" step="0.01" defaultValue={0} /></label>
            </div>
          )}
          cards={<>{renderCard(0)}{renderCard(1)}</>}
          hero={<PlayerSetup role="hero" position={heroPosition} otherPosition={opponentPosition} onPositionChange={setHeroPosition} />}
          opponent={<PlayerSetup role="opponent" position={opponentPosition} otherPosition={heroPosition} onPositionChange={setOpponentPosition} />}
        />
      </div>
    </details>
  )
}
