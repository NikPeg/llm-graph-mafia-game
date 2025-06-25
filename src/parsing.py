import re

def sanitize_model_response(response: str, cur_player_name: str, list_active_names: list, phase: str) -> str:
    """
    Очищает ответ модели:
    1. Удаляет любые строки 'Имя: ...' (имя из list_active_names, кроме себя) и все после них (в т.ч. саму строку).
    2. Удаляет все фрагменты 'Your response...' и все выше по тексту — если их больше одной, обрезает до второй включительно.
    3. Если phase == 'discussion'/'day_discussion', удаляет строки с ACTION: или VOTE: и всё, что после них (если такие есть).
    4. Если phase == 'night', удаляет строки с VOTE:
    5. Удаляет повторы "Имя: Имя: ..." (текущего игрока) в начале ответа (оставляет только смысловую часть).
    6. Удаляет лишние пробелы и пустые строки в начале/конце ответа.
    """

    if not response or not isinstance(response, str):
        return ""

    # 1. Обрезаем всё по чужим "Имя: ..."
    other_names = [name for name in list_active_names if name != cur_player_name]
    if other_names:
        # Regex ^(Имя1|Имя2|...): в начале строки (после опциональных пробелов)
        pattern = r'^\s*(?:' + '|'.join([re.escape(name) for name in other_names]) + r'):'
        lines = response.splitlines()
        cut_index = None
        for idx, line in enumerate(lines):
            if re.match(pattern, line):
                cut_index = idx
                break
        if cut_index is not None:
            response = '\n'.join(lines[:cut_index])

    # 2. Обрезаем всё до второй строки "Your response"
    yr_matches = list(re.finditer(r'(?i)your response', response))
    if len(yr_matches) > 0:
        if len(yr_matches) >= 2:
            second_start = yr_matches[1].start()
            # обрезать всё до второй включительно
            end_of_line = response.find('\n', second_start)
            if end_of_line == -1:
                response = response[second_start + len('Your response') :]
            else:
                response = response[end_of_line + 1 :]
        else:
            # удалить первую встречу + всю эту строку
            pattern = r'^.*your response.*$\n?'  # строка целиком
            response = re.sub(pattern, '', response, flags=re.IGNORECASE | re.MULTILINE)

    phase_lower = phase.lower()
    phase_discussion = phase_lower in ['discussion', 'day_discussion']
    phase_voting = phase_lower in ['vote', 'voting', 'day_voting']
    phase_night = phase_lower == 'night'

    # 3a. В обсуждении ACTION/VOTE — срезаем всё после них
    if phase_discussion:
        # ищем "ACTION:"/"VOTE:"/"ACCIÓN:"/"KILL" — всё после первой вхождения
        pattern = r'(?i)\n?(ACTION:|ACCIÓN:|VOTE:|PROTEGER|KILL)[^\n]*.*'
        response = re.split(pattern, response)[0]

    # 3b. В ночной фазе убираем VOTE
    if phase_night:
        pattern = r'(?i)\n?(VOTE:)[^\n]*.*'
        response = re.split(pattern, response)[0]

    # 4. Удалить пробелы и пустые строки в начале/конце
    response = response.strip()
    lines = response.split('\n')
    # убираем пустые строки сверху/снизу
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    response = '\n'.join(lines).strip()

    # 5. Удаление дублирующихся "Имя: Имя: ..." в начале ответа (текущий игрок)
    #    Например "Morgan: Morgan: I agree", превращаем в "I agree"
    #    Регистронезависимо, с учетом множества дублей, возможных пробелов
    if cur_player_name:
        pattern = r'^((?:' + re.escape(cur_player_name) + r':\s*){2,})'
        match = re.match(pattern, response, re.IGNORECASE)
        if match:
            # удаляем все повторы имени с двоеточием слева
            cleaned = response[match.end():].lstrip()
            response = cleaned

        # Также если просто имя: в начале (один раз), тоже убрать (иногда "Morgan: I agree")
        one_pattern = r'^' + re.escape(cur_player_name) + r':\s*'
        response = re.sub(one_pattern, '', response, flags=re.IGNORECASE).lstrip()

    # 6. Финальный trim
    response = response.strip()

    return response
