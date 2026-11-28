"""SSE framing and safe extraction of a partial top-level JSON answer."""
import json
from rag import ModelError, validate_result


def frame(event):
    return ('data: ' + json.dumps(event, ensure_ascii=False) + '\n\n').encode('utf-8')


def events(rag, question):
    upstream = rag.ask_stream(question)
    try:
        try:
            for event in upstream:
                yield frame(event)
        except ModelError as error:
            yield frame({'type': 'error', 'error': str(error)})
        except Exception:
            yield frame({'type': 'error', 'error': 'Не удалось завершить поток ответа.'})
    finally:
        upstream.close()


def partial_answer(raw):
    decoder = json.JSONDecoder()
    pos = 0
    def space(i):
        while i < len(raw) and raw[i].isspace():
            i += 1
        return i
    pos = space(pos)
    if pos == len(raw) or raw[pos] != '{':
        return ''
    pos += 1
    try:
        while True:
            pos = space(pos)
            if pos < len(raw) and raw[pos] == ',':
                pos = space(pos + 1)
            key, pos = decoder.raw_decode(raw, pos)
            pos = space(pos)
            if raw[pos] != ':':
                return ''
            pos = space(pos + 1)
            if key != 'answer':
                _, pos = decoder.raw_decode(raw, pos)
                continue
            if raw[pos] != '"':
                return ''
            start = pos
            pos += 1
            while pos < len(raw):
                ch = raw[pos]
                if ch == '"':
                    break
                if ch == '\\':
                    if pos + 1 >= len(raw):
                        break
                    width = 6 if raw[pos + 1] == 'u' else 2
                    if pos + width > len(raw):
                        break
                    pos += width
                else:
                    pos += 1
            text = json.loads(raw[start:pos] + '"')
            # Do not emit half a surrogate pair split between provider chunks.
            return text.encode('utf-8', errors='ignore').decode('utf-8')
    except (ValueError, IndexError, TypeError):
        return ''


def provider_result(response):
    accumulated = ''
    previous = ''
    data = []
    done = False
    while True:
        line = response.readline(65537)
        if not line:
            break
        if len(line) > 65536:
            raise ModelError('Слишком большой фрагмент потока модели.')
        line = line.decode('utf-8').rstrip('\r\n')
        if line.startswith('data:'):
            data.append(line[5:].lstrip(' '))
        if line != '' or not data:
            continue
        payload = '\n'.join(data)
        data = []
        if payload == '[DONE]':
            done = True
            break
        chunk = json.loads(payload)
        if 'error' in chunk:
            raise ModelError('Модель вернула ошибку в потоке.')
        choices = chunk.get('choices', [])
        if not choices:
            continue
        choice = choices[0]
        if choice.get('finish_reason') == 'length':
            raise ModelError('Ответ модели обрезан по лимиту токенов.')
        content = choice.get('delta', {}).get('content') or ''
        if not isinstance(content, str):
            raise ModelError('Некорректный фрагмент ответа модели.')
        accumulated += content
        if len(accumulated) > 65536:
            raise ModelError('Ответ модели слишком большой.')
        draft = partial_answer(accumulated)
        if draft and draft != previous:
            previous = draft
            yield {'type': 'draft', 'answer': draft}
    if not done:
        raise ModelError('Поток модели прервался до завершения ответа.')
    yield {'type': 'model_result', 'result': validate_result(json.loads(accumulated))}
