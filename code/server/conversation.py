"""Bounded dialogue context and allowlisted presentation preferences."""
import re

DEFAULT_STYLE = {'prefix': '', 'verbosity': 'normal', 'simple': False}
PREFIX = re.compile(r'[\w ёЁ.,!?—-]{0,32}', re.UNICODE)


def validate_style(value):
    if not isinstance(value, dict) or set(value) - DEFAULT_STYLE.keys():
        raise ValueError('Некорректные настройки стиля.')
    style = {**DEFAULT_STYLE, **value}
    if (not isinstance(style['prefix'], str) or not PREFIX.fullmatch(style['prefix'])
            or style['verbosity'] not in ('normal', 'brief', 'detailed')
            or type(style['simple']) is not bool):
        raise ValueError('Некорректные настройки стиля.')
    return style


def conversation_options(payload):
    options = {}
    if 'history' in payload:
        history = payload['history']
        if not isinstance(history, list) or len(history) > 12:
            raise ValueError('История должна содержать не больше 12 сообщений.')
        total = 0
        for message in history:
            if (not isinstance(message, dict) or set(message) != {'role', 'content'}
                    or message['role'] not in ('user', 'assistant')
                    or not isinstance(message['content'], str)
                    or not message['content'].strip()
                    or not 1 <= len(message['content']) <= 1500):
                raise ValueError('Некорректное сообщение истории.')
            total += len(message['content'])
        if total > 8000:
            raise ValueError('История длиннее 8000 символов.')
        options['history'] = history
    if 'style' in payload:
        options['style'] = validate_style(payload['style'])
    return options


def style_request(question, style):
    """Only whole, recognised requests; embedded extra instructions remain questions."""
    text = question.strip().rstrip('.!').strip()
    lowered = text.lower().replace('ё', 'е')
    updated = dict(style)
    if lowered in ('сбрось стиль', 'сбрось настройки стиля', 'убери префикс', 'не пиши мяу', 'больше не пиши мяу'):
        if lowered.startswith('сбрось'):
            return dict(DEFAULT_STYLE)
        updated['prefix'] = ''
    elif lowered in ('пиши кратко', 'пиши короче', 'отвечай кратко', 'отвечай короче'):
        updated['verbosity'] = 'brief'
    elif lowered in ('пиши подробно', 'пиши подробнее', 'отвечай подробно', 'отвечай подробнее'):
        updated['verbosity'] = 'detailed'
    elif lowered in ('объясняй проще', 'объясняй простыми словами', 'пиши простыми словами'):
        updated['simple'] = True
    else:
        match = re.fullmatch(r'(?:перед каждым (?:своим )?(?:сообщением|ответом) пиши|начинай каждый ответ со слова|добавляй в начало каждого ответа)\s+["«](.+?)["»]', text, re.I)
        if not match or not PREFIX.fullmatch(match[1]) or not match[1].strip():
            return None
        updated['prefix'] = match[1].strip()
    return updated


def resolve_followup(question, history):
    if not re.search(r"\b(?:он|она|оно|они|его|ее|их)\b", question, re.I):
        return question
    for message in reversed(history):
        if message['role'] != 'user':
            continue
        topic = re.fullmatch(r"(?:что такое|что значит|что означает)\s+([^?!.,]+)[?!.]*", message['content'].strip(), re.I)
        if topic:
            return re.sub(r"\b(?:он|она|оно|они)\b", lambda _: topic[1], question, flags=re.I)
    return question


def contextual_query(question, history):
    question = resolve_followup(question, history)
    # Preserve independent questions; use prior user topics only for follow-ups.
    if not re.match(r'^(?:а\b|и\b|почему\b|зачем\b|чем (?:он|она|оно|они)\b|что это\b|(?:объясни|расскажи) подробнее\b|приведи пример\b)', question, re.I):
        return question
    topics = [m['content'] for m in history if m['role'] == 'user'
              and style_request(m['content'], DEFAULT_STYLE) is None]
    return '\n'.join([*topics[-3:], question])


def decorate(answer, style):
    return (style['prefix'] + ' ' if style['prefix'] else '') + answer


def missing_game_evidence(question, documents):
    variants = (r"\b(?:омах[а-я]*|omaha)\b", r"\b(?:разз[а-я]*|razz)\b", r"\b(?:стад[а-я]*|stud)\b")
    evidence = ' '.join(doc['title'] + ' ' + doc['text'] for doc in documents)
    return any(re.search(pattern, question, re.I) and not re.search(pattern, evidence, re.I)
               for pattern in variants)
