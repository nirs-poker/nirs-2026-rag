export interface StylePreferences {
  prefix: string
  verbosity: 'normal' | 'brief' | 'detailed'
  simple: boolean
}

export interface HistoryMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface AskRequest {
  question: string
  history?: HistoryMessage[]
  style?: StylePreferences
}

export interface AskSource {
  id: string
  title: string
  text: string
}

export interface AskResponse {
  status: 'ok' | 'no_sources' | 'style_updated'
  answer: string
  sources: AskSource[]
  style?: StylePreferences
}
