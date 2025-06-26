import re

def sanitize_model_response(response: str, cur_player_name: str, list_active_names: list, phase: str) -> str:
    """
    Очищает ответ модели:
    1. Удаляет любые строки 'Имя: ...' (имя из list_active_names, кроме себя) и все после них (в т.ч. саму строку).
    2. Удаляет все фрагменты 'Your response...' и все выше по тексту — если их больше одной, обрезает до второй включительно.
    3. Если phase == 'discussion'/'day_discussion', удаляет строки с ACTION: или VOTE: и всё, что после них (если такие есть).
    4. Если phase == 'night', удаляет строки с VOTE:
    5. Удаляет повторы "Имя: Имя: ..." (текущего игрока) в начале ответа (оставляет только смысловую часть).
    6. Оставляет только первую содержательную строку ответа, далее добавляет найденные VOTE: ... или ACTION: ... в конец, всё одной строкой.
    7. Удаляет лишние пробелы и пустые строки в начале/конце ответа.
    """

    if not response or not isinstance(response, str):
        return ""

    # 1. Обрезаем всё по чужим "Имя: ..."
    other_names = [name for name in list_active_names if name != cur_player_name]
    if other_names:
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
    if yr_matches:
        if len(yr_matches) >= 2:
            second_start = yr_matches[1].start()
            end_of_line = response.find('\n', second_start)
            if end_of_line == -1:
                response = response[second_start + len('Your response') :]
            else:
                response = response[end_of_line + 1 :]
        else:
            pattern = r'^.*your response.*$\n?'  # строка целиком
            response = re.sub(pattern, '', response, flags=re.IGNORECASE | re.MULTILINE)

    phase_lower = phase.lower()
    phase_discussion = phase_lower in ['discussion', 'day_discussion']
    phase_voting = phase_lower in ['vote', 'voting', 'day_voting']
    phase_night = phase_lower == 'night'

    # 3a. В обсуждении ACTION/VOTE — срезаем всё после них
    if phase_discussion:
        pattern = r'(?i)\n?(ACTION:|ACCIÓN:|VOTE:|PROTEGER|KILL)[^\n]*.*'
        response = re.split(pattern, response)[0]

    # 3b. В ночной фазе убираем VOTE
    if phase_night:
        pattern = r'(?i)\n?(VOTE:)[^\n]*.*'
        response = re.split(pattern, response)[0]

    # 4. Удалить пробелы и пустые строки в начале/конце
    response = response.strip()
    lines = response.split('\n')
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    response = '\n'.join(lines).strip()

    # 5. Удаление дублирующихся "Имя: Имя: ..." в начале ответа (текущий игрок)
    if cur_player_name:
        pattern = r'^((?:' + re.escape(cur_player_name) + r':\s*){2,})'
        match = re.match(pattern, response, re.IGNORECASE)
        if match:
            cleaned = response[match.end():].lstrip()
            response = cleaned

        one_pattern = r'^' + re.escape(cur_player_name) + r':\s*'
        response = re.sub(one_pattern, '', response, flags=re.IGNORECASE).lstrip()

    # 6. Оставить только первую содержательную строку (и добавить приказ(ы) в конец)
    # Найдём все команды VOTE: и ACTION:
    # (ищем все, чтобы если вдруг VOTE встречается дважды — взять первый)
    vote_match = re.search(r'\bVOTE:\s*([^\s\n]+)', response, re.IGNORECASE)
    # Любая ACTION: <что_угодно> до конца строки (например ACTION: Kill Bailey или ACTION: Protect Kai)
    action_match = re.search(r'\bACTION:\s*[^\n]+', response, re.IGNORECASE)

    # Оставить первую значимую строку (не пустую)
    first_line = ""
    for line in response.split('\n'):
        if line.strip():
            first_line = line.strip()
            break

    # Собираем результат
    result_parts = []
    if first_line:
        result_parts.append(first_line)
    if vote_match:
        vote_cmd = vote_match.group(0).strip()
        # чтобы не дублировать, если уже кончается на этот vote_cmd
        if vote_cmd.lower() not in first_line.lower():
            result_parts.append(vote_cmd)
    if action_match:
        action_cmd = action_match.group(0).strip()
        if action_cmd.lower() not in first_line.lower() and (not vote_match or action_cmd.lower() not in vote_match.group(0).lower()):
            result_parts.append(action_cmd)

    response_one_line = " ".join(result_parts).strip()

    return response_one_line
