"""Узкие проверяемые ответы о банках и машинной записи по найденным источникам."""

import re
from decimal import Decimal

NUMBER = r"\d+(?:[.,]\d+)?"


def amount(text):
    return Decimal(text.replace(",", "."))


def display(value):
    return format(value.normalize(), "f")


def preflop_size(value):
    if value <= 0 or not value.is_finite():
        raise ValueError("Размер должен быть положительным.")
    number = display(value)
    return (number if "." in number else number + ".0") + "bb"


def minimum_raise(current, big_blind):
    if big_blind <= 0 or current < 2 * big_blind:
        raise ValueError("Ожидается полное открытие выше большого блайнда.")
    return current + (current - big_blind)


def split_pots(contributions):
    if not 2 <= len(contributions) <= 6 or any(x <= 0 or not x.is_finite() for x in contributions):
        raise ValueError("Нужны положительные взносы от двух до шести игроков.")
    layers, previous = [], Decimal(0)
    for level in sorted(set(contributions)):
        players = [i + 1 for i, value in enumerate(contributions) if value >= level]
        layers.append(((level - previous) * len(players), players))
        previous = level
    return layers


def grounded_answer(question, documents):
    """Возвращает None, если запрос выходит за поддержанный однозначный формат."""
    text = question.lower().replace("ё", "е")
    bank = next((d for d in documents if "побочный банк" in d["title"].lower()
                 and "из побочного банка в основной они не переносятся" in d["text"]), None)
    if bank and ("побочн" in text or ("банк" in text and "внесли" in text)):
        rule = bank["text"].split("Если игрок сбрасывает карты,", 1)[-1]
        rule = "Если игрок сбрасывает карты," + rule
        values = re.search(r"внесли\s+(?:в пустой банк\s+)?(" + NUMBER + r"(?:(?:,\s+|\s+и\s+)" + NUMBER + r")+)\s*бб", text)
        if (values and "в пустой банк" in text and "не в пустой банк" not in text
                and any(word in text for word in ("олл", "закончились фишки", "весь стек"))):
            contributions = [amount(x) for x in re.findall(NUMBER, values[1])]
            try:
                layers = split_pots(contributions)
            except ValueError:
                return None
            # Единственный участник верхнего слоя означает невозвращённую ставку,
            # а не банк; такие ситуации пока не интерпретируем автоматически.
            if any(len(players) == 1 for _, players in layers):
                return None
            parts = []
            for i, (size, players) in enumerate(layers):
                label = "Основной банк" if i == 0 else f"Побочный банк {i}"
                parts.append(f"{label}: {display(size)} ББ. До фолда участвуют игроки "
                             + ", ".join(map(str, players)) + " (в порядке перечисления взносов).")
            return {"answer": " ".join(parts) + " " + rule, "sources": [bank["id"]]}
        if not re.search(r"\d", text) and any(word in text for word in ("фолд", "сброс", "сбрасыв")):
            return {"answer": rule, "sources": [bank["id"]]}

    if ("pokerbench" not in text or "префлоп" not in text
            or not any(word in text for word in ("запис", "формат", "выгляд"))):
        return None
    syntax = next((d for d in documents if "PokerBench" in d["title"]
                   and "десятичное число и суффикс bb" in d["text"]), None)
    if not syntax:
        return None
    if len(re.findall(r"до\s*" + NUMBER + r"\s*бб", text)) != 1:
        return None
    if "минималь" in text:
        opening = re.search(r"откр[а-я]+\s+до\s*(" + NUMBER + r")\s*бб", text)
        blinds = re.search(r"блайндах\s*(" + NUMBER + r")\s*/\s*(" + NUMBER + r")", text)
        rule = next((d for d in documents if "минимальная прибавка" in d["text"].lower()), None)
        if not opening or not blinds or not rule or "олл" in text or "all" in text:
            return None
        try:
            value = minimum_raise(amount(opening[1]), amount(blinds[2]))
        except ValueError:
            return None
        return {"answer": f"Минимальное повторное повышение — до {display(value)} ББ. "
                f"Это 3-бет. Префлоп-запись PokerBench: {preflop_size(value)}.",
                "sources": [rule["id"], syntax["id"]]}
    target = re.search(r"до\s*(" + NUMBER + r")\s*бб", text)
    if target:
        value = amount(target[1])
        if value <= 0:
            return None
        return {"answer": f"Префлоп-запись PokerBench: {preflop_size(value)}. "
                "Это число с суффиксом bb, без слова raise и постфлоп-префикса RAISE_*.",
                "sources": [syntax["id"]]}
    return None
