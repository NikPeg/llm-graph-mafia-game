import re

def sanitize_model_response(response: str, cur_player_name: str, list_active_names: list, phase: str) -> str:
    """
    Очищает ответ модели:
    1. Удаляет любые строки 'Имя: ...' (имя из list_active_names, кроме себя) и все после них (в т.ч. саму строку).
    2. Удаляет все фрагменты 'Your response...' и все выше по тексту — если их больше одной, обрезает до второй включительно.
    3. Если phase == 'discussion'/'day_discussion', удаляет строки с ACTION: или VOTE: и всё, что после них (если такие есть).
    4. Если phase == 'night', удаляет строки с VOTE:
    5. Удаляет лишние пробелы и пустые строки в конце.
    """

    if not response or not isinstance(response, str):
        return ""

    # --- 1. Обрезка по чужому "ИмяИгрока: ..."
    # Составляем паттерн на имена других игроков
    # Делаем \b...: чтобы не ловить куски слов
    other_names = [name for name in list_active_names if name != cur_player_name]
    # если имена есть
    if other_names:
        pattern = r'^(?:' + '|'.join([re.escape(name) for name in other_names]) + r'):'  # например "^Frankie:"
        # multi-line режим, ищем первую такую строку
        lines = response.splitlines()
        cut_index = None
        for idx, line in enumerate(lines):
            # учет leading spaces
            if re.match(rf'\s*{pattern}', line):
                cut_index = idx
                break
        if cut_index is not None:
            response = '\n'.join(lines[:cut_index])  # все до этой строки невключительно

    # --- 2. Обрезаем всё до второй строки "Your response"
    yr_lines = [m.start() for m in re.finditer(r'(?i)your response', response)]
    if len(yr_lines) > 0:
        # если две и более, вырезаем всё до второй "Your response"; иначе удаляем первую встречу
        if len(yr_lines) >= 2:
            second = yr_lines[1]
            # найдем конец второй строки (до \n)
            end_of_line = response.find('\n', second)
            if end_of_line == -1:
                # "Your response ..." в конце файла
                response = response[second + len('Your response') :]
            else:
                response = response[end_of_line + 1 :]
        else:
            # удаляем первую встречу + строку целиком
            # ищем строку с Your response
            pattern = r'^.*your response.*$\n?'  # строка полностью, insensitive
            response = re.sub(pattern, '', response, flags=re.IGNORECASE | re.MULTILINE)

    # --- 3. В дневной фазе обсуждения убираем любые ACTION/VOTE и всё после них
    # определим, в какой фазе мы
    phase_discussion = phase.lower() in ['discussion', 'day_discussion']
    phase_voting = phase.lower() in ['vote', 'voting', 'day_voting']
    phase_night = phase.lower() == 'night'

    # --- 3a. В обсуждении ACTION/ACCIÓN/Proteger/Kill/VOTE полностью вырезаем (иначе просто не добавляем сообщение)
    if phase_discussion:
        # ищем фразы вида "ACTION:", "VOTE:", "ACCIÓN:", "PROTEGER", "KILL", и обрезаем всё после них (insensitive)
        pattern = r'(?i)\n?(ACTION:|ACCIÓN:|VOTE:|PROTEGER|KILL)[^\n]*.*'
        response = re.split(pattern, response)[0]  # всё до первого совпадения

    # --- 3b. В ночной фазе убираем VOTE (Почему вдруг модель решила VOTE ночью)
    if phase_night:
        pattern = r'(?i)\n?(VOTE:)[^\n]*.*'
        response = re.split(pattern, response)[0]

        # --- 4. Удалить пробелы и пустые строки вначале/в конце
    response = response.strip()
    lines = response.split('\n')
    # убрать пустые строки в начале/конце
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    response = '\n'.join(lines).strip()

    return response
