"""Reproducible tokenisation variants; no document IDs or query templates."""
import re
from functools import lru_cache

WORD = re.compile(r"\d+(?:[.,]\d+)?\s*bb|[a-zа-яё0-9]+(?:[-_][a-zа-яё0-9]+)*", re.I)
STOP = set("а и но или в во на с со по за к от до из для у о об при ли же что это такой такое какие какой как кто сколько когда где чем если после перед почему что-то я мы вы он она".split())
FORMS = {
    "комбинации": "комбинация", "комбинаций": "комбинация", "комбинацию": "комбинация",
    "блайнда": "блайнд", "блайндов": "блайнд", "баттоне": "баттон", "баттона": "баттон",
    "ставки": "ставка", "ставку": "ставка", "ставок": "ставка", "ставкой": "ставка",
    "карты": "карта", "карт": "карта", "карту": "карта", "картой": "карта",
    "масти": "масть", "мастей": "масть", "флеша": "флеш", "стрита": "стрит",
    "раздачи": "раздача", "раздаче": "раздача", "раздачу": "раздача",
    "банка": "банк", "банке": "банк", "банку": "банк",
    "колла": "колл", "коллом": "колл", "чека": "чек", "рейза": "рейз",
    "рейзом": "рейз", "фолда": "фолд", "кикера": "кикер", "кикеры": "кикер",
    "стрите": "стрит", "флопа": "флоп", "флопе": "флоп", "терна": "терн", "терне": "терн",
    "ривере": "ривер", "ривера": "ривер", "аутов": "аут", "ауты": "аут",
    "чекнуть": "чек", "коллировать": "колл", "заколлировать": "колл", "сбросить": "фолд",
    "сбрасывает": "фолд", "сбросил": "фолд", "сбросивший": "фолд",
    "сбрасывают": "фолд", "сбросившего": "фолд",
    "call": "колл", "check": "чек", "raise": "рейз", "fold": "фолд", "bet": "бет",
    "river": "ривер", "turn": "терн", "flop": "флоп", "btn": "баттон",
    "алл-ин": "олл-ин", "all-in": "олл-ин", "бб": "bb",
    "катоф": "co", "катофф": "co", "хайджек": "hj",
}


def legacy_tokens(text):
    text = text.lower().replace("ё", "е").replace("‑", "-").replace("3 бет", "3-бет").replace("олл ин", "олл-ин")
    text = re.sub(r"(?<=\d)\s*бб\b", "bb", text)
    result = []
    for word in WORD.findall(text):
        parts = [word]
        if "_" in word:
            parts.extend(word.split("_"))
        if re.fullmatch(r"\d+(?:[.,]\d+)?\s*bb", word):
            amount = word[:-2].strip().replace(",", ".")
            amount = amount.rstrip("0").rstrip(".") if "." in amount else amount
            parts = [f"{amount if '.' in amount else amount + '.0'}bb", amount, "bb"]
        result.extend(FORMS.get(part, part) for part in parts if part not in STOP)
    return result


MODES = ('raw', 'lower', 'stop', 'technical', 'legacy', 'lemma', 'lemma_technical')
DEFAULT_MODE = 'lemma'
ALIASES = {key: value for key, value in FORMS.items() if re.fullmatch(r'[a-z-]+', key)}
ALIASES.update({'бб': 'bb', 'алл-ин': 'олл-ин'})


@lru_cache(maxsize=1)
def morphology():
    try:
        from pymorphy3 import MorphAnalyzer
    except ImportError as error:
        raise RuntimeError('Для lemma установите code/server/requirements.txt') from error
    return MorphAnalyzer()


@lru_cache(maxsize=20000)
def lemma(word):
    return morphology().parse(word)[0].normal_form.replace('ё', 'е')


def tokens(text, mode=DEFAULT_MODE):
    if mode not in MODES:
        raise ValueError('Неизвестный вариант предобработки: ' + str(mode))
    if mode == 'legacy':
        return legacy_tokens(text)
    if mode == 'raw':
        return WORD.findall(text)
    text = text.lower().replace('ё', 'е').replace('‑', '-')
    technical = mode in ('technical', 'lemma_technical')
    if technical:
        text = text.replace('3 бет', '3-бет').replace('олл ин', 'олл-ин')
        text = re.sub(r'(?<=\d)\s*бб\b', 'bb', text)
    result = []
    for word in WORD.findall(text):
        parts = [word]
        if technical:
            if '_' in word:
                parts.extend(word.split('_'))
            if re.fullmatch(r'\d+(?:[.,]\d+)?bb', word):
                amount = word[:-2].replace(',', '.')
                amount = amount.rstrip('0').rstrip('.') if '.' in amount else amount
                parts = [f"{amount if '.' in amount else amount + '.0'}bb", amount, 'bb']
        for part in parts:
            if mode != 'lower' and part in STOP:
                continue
            if technical:
                part = ALIASES.get(part, part)
            if mode.startswith('lemma') and re.fullmatch(r'[а-я]+', part):
                part = lemma(part)
            result.append(part)
    return result
