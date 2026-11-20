interface Props {
  draft: string
  status: string
  pending: boolean
  returnVisible: boolean
  onDraft: (text: string) => void
  onSubmit: () => void
  onReturn: () => void
  onLeaveHand?: () => void
}

export function Composer({ draft, status, pending, returnVisible, onDraft, onSubmit, onReturn, onLeaveHand }: Props) {
  return (
    <div className="composer">
      {returnVisible && <button className="control primary table-return" type="button" onClick={onReturn}>К столу</button>}
      <div className="frontend-composer-row">
        <form className="input-pill" onSubmit={event => { event.preventDefault(); onSubmit() }}>
          <textarea name="text" rows={1} required value={draft} onChange={event => onDraft(event.target.value)} placeholder="Задай вопрос по теории или опиши раздачу" aria-label="Сообщение" />
          <button type="submit" disabled={!draft.trim() || pending}>Отправить</button>
        </form>
        <button className="control leave-hand" type="button" onClick={onLeaveHand} disabled={!onLeaveHand} aria-label="Покинуть раздачу">
          <span className="leave-hand-label">Покинуть раздачу</span>
          <span className="leave-hand-short" aria-hidden="true">Выйти</span>
        </button>
      </div>
      <p className="disclaimer" role="status">{status || 'Ответы генерирует ИИ, и они могут содержать ошибки'}</p>
    </div>
  )
}
