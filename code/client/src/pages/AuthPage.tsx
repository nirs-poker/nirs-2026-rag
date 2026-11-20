import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import authStyles from '../../css/auth.css?inline'
import { routes } from '../Routes'

export default function AuthPage({ mode }: { mode: 'login' | 'register' }) {
  const register = mode === 'register'
  const navigate = useNavigate()
  const [error, setError] = useState('')

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const data = new FormData(event.currentTarget)
    if (register && data.get('password') !== data.get('confirmation')) {
      setError('Пароли не совпадают.')
      return
    }
    navigate(routes.chat)
  }

  return (
    <>
      <style>{authStyles + '\nbody:has(.box) #root { width: min(100%, 400px); } body:has(.box.wide) #root { width: min(100%, 560px); } .auth-status { margin: 12px 0 0; color: #6a6355; font-size: 13px; }'}</style>
      <main className={register ? 'box wide' : 'box'}>
        <div className="brand">
          {register
            ? <div className="chips" aria-hidden="true"><span /><span /><span /></div>
            : <div className="fan" aria-hidden="true"><span>A♠</span><span>K♥</span><span>Q♣</span></div>}
          <h1>{register ? 'Регистрация' : 'Вход'}</h1>
          <p className="sub">Демонстрационный режим</p>
        </div>
        <form onSubmit={submit} onChange={() => setError('')}>
          <div className={register ? 'grid' : undefined}>
            {register && <div><label htmlFor="name">Имя или ник</label><input id="name" type="text" required autoComplete="nickname" /></div>}
            <div><label htmlFor="email">Email</label><input id="email" type="email" required placeholder="you@example.com" autoComplete="email" /></div>
            <div>
              <label htmlFor="password">Пароль</label>
              <input id="password" name="password" type="password" required minLength={register ? 8 : undefined} autoComplete={register ? 'new-password' : 'current-password'} placeholder={register ? 'От 8 символов' : '••••••••'} />
            </div>
            {register && <div><label htmlFor="password2">Повторите пароль</label><input id="password2" name="confirmation" type="password" required minLength={8} autoComplete="new-password" /></div>}
          </div>
          {register && <label className="check"><input type="checkbox" required /> Понимаю, что сервис предназначен для обучения.</label>}
          {error && <p className="auth-status" role="alert">{error}</p>}
          <button className="btn" type="submit">{register ? 'Создать аккаунт' : 'Войти'}</button>
          <p className="auth-status">Форма открывает демонстрационный чат. Данные аккаунта не сохраняются.</p>
        </form>
        <p className="alt">{register ? 'Уже есть аккаунт? ' : 'Нет аккаунта? '}
          <Link to={register ? routes.login : routes.register}>{register ? 'Войти' : 'Зарегистрироваться'}</Link>
        </p>
      </main>
    </>
  )
}
