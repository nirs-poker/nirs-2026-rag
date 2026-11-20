export interface AskRequest {
  question: string
}

export interface AskSource {
  id: string
  title: string
  text: string
}

export interface AskResponse {
  status: 'ok' | 'no_sources'
  answer: string
  sources: AskSource[]
}
