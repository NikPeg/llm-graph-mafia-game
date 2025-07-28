# strip_comments.py
import tokenize
import io
import sys
from pathlib import Path
from collections import defaultdict

def process_python_file(filepath: Path):
    """
    Обрабатывает Python-файл:
    1. Удаляет инлайн-комментарии (после кода).
    2. Удаляет целиком строки, содержащие только комментарии.
    3. Удаляет пустые строки.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()

        # Генерируем токены из исходного кода. Оборачиваем в list() для удобства.
        source_tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))

        # Группируем токены по номеру строки
        lines = defaultdict(list)
        for token in source_tokens:
            line_num = token.start[0]
            lines[line_num].append(token)

        result_tokens = []
        # Сохраняем токен кодировки, если он есть (должен быть первым)
        if source_tokens and source_tokens[0].type == tokenize.ENCODING:
            result_tokens.append(source_tokens[0])

        # Обрабатываем сгруппированные строки
        for line_num in sorted(lines.keys()):
            line_tokens = lines[line_num]

            # Проверяем, есть ли на строке "настоящий" код.
            # "Настоящий код" - это любой токен, который не является комментарием,
            # новой строкой или просто пустым/whitespace токеном.
            # Мы оставляем INDENT/DEDENT, так как они важны для структуры.
            code_present_on_line = any(
                t.type not in (tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE)
                for t in line_tokens
            )

            if code_present_on_line:
                # Если на строке есть код, мы сохраняем все токены, кроме комментариев.
                for token in line_tokens:
                    if token.type != tokenize.COMMENT:
                        result_tokens.append(token)
            # else:
            # Если на строке нет кода (т.е. это пустая строка или строка только с комментарием),
            # мы просто ничего не добавляем в result_tokens, эффективно удаляя всю строку.

        # Собираем код обратно из отфильтрованных токенов
        new_source = tokenize.untokenize(result_tokens)

        # Перезаписываем исходный файл
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_source)

        print(f"✅ Comments and empty lines processed in: {filepath}")

    except tokenize.TokenError as e:
        print(f"❌ Failed to tokenize {filepath}: {e}. Skipping file.")
    except Exception as e:
        print(f"❌ Failed to process {filepath}: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_dir = Path(sys.argv[1])
    else:
        # По умолчанию используется текущая директория
        target_dir = Path(".")
        print(f"No directory specified. Using current directory: {target_dir.resolve()}")

    if not target_dir.is_dir():
        print(f"Error: '{target_dir}' is not a valid directory.")
        sys.exit(1)

    print("\n⚠️  WARNING: This script will permanently modify .py files.")
    print("   - It removes all comments.")
    print("   - It removes lines that only contained comments.")
    print("   - It removes blank lines.")
    print(f"\n   Target directory: {target_dir.resolve()}")

    # Сделайте бэкап перед запуском!
    confirm = input("   Are you sure you want to continue? (yes/no): ")

    if confirm.lower() != 'yes':
        print("Operation cancelled.")
        sys.exit(0)

    for py_file in target_dir.rglob("*.py"):
        # Исключаем сам скрипт из обработки
        if not py_file.samefile(Path(__file__)):
            process_python_file(py_file)
