import os
import re
import argparse
from pathlib import Path


def remove_comments_from_line(line):
    """
    Удаляет комментарии из строки, учитывая строки в кавычках
    """
    result = ""
    i = 0
    in_single_quote = False
    in_double_quote = False
    in_triple_single = False
    in_triple_double = False

    while i < len(line):
        char = line[i]

        if i <= len(line) - 3:
            triple = line[i : i + 3]
            if triple == '"""' and not in_single_quote and not in_triple_single:
                if in_triple_double:
                    in_triple_double = False
                    result += triple
                    i += 3
                    continue
                else:
                    in_triple_double = True
                    result += triple
                    i += 3
                    continue
            elif triple == "'''" and not in_double_quote and not in_triple_double:
                if in_triple_single:
                    in_triple_single = False
                    result += triple
                    i += 3
                    continue
                else:
                    in_triple_single = True
                    result += triple
                    i += 3
                    continue

        if in_triple_single or in_triple_double:
            result += char
            i += 1
            continue

        if char == '"' and not in_single_quote:
            if i == 0 or line[i - 1] != "\\":
                in_double_quote = not in_double_quote
        elif char == "'" and not in_double_quote:
            if i == 0 or line[i - 1] != "\\":
                in_single_quote = not in_single_quote

        if char == "#" and not in_single_quote and not in_double_quote:
            result = result.rstrip()
            break

        result += char
        i += 1

    return result


def process_file(file_path, backup=True):
    """
    Обрабатывает один файл, удаляя комментарии
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        try:
            with open(file_path, "r", encoding="cp1251") as f:
                lines = f.readlines()
        except:
            print(f"Не удалось прочитать файл {file_path}")
            return False

    if backup:
        backup_path = str(file_path) + ".backup"
        with open(backup_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        print(f"Создан бэкап: {backup_path}")

    processed_lines = []
    for line in lines:
        processed_line = remove_comments_from_line(line.rstrip("\n\r"))

        if processed_line.strip() or line.startswith("    ") or line.startswith("\t"):
            processed_lines.append(processed_line + "\n")

        elif not line.strip().startswith("#"):
            processed_lines.append(processed_line + "\n")

    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(processed_lines)

    return True


def find_python_files(directory):
    """
    Находит все Python файлы в директории и поддиректориях
    """
    python_files = []
    for root, dirs, files in os.walk(directory):
        dirs[:] = [
            d
            for d in dirs
            if not d.startswith(".") and d not in ["__pycache__", "venv", "env"]
        ]

        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))

    return python_files


def main():
    parser = argparse.ArgumentParser(description="Удаляет комментарии из Python файлов")
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Путь к файлу или директории (по умолчанию текущая директория)",
    )
    parser.add_argument(
        "--no-backup", action="store_true", help="Не создавать резервные копии"
    )
    parser.add_argument(
        "--file",
        action="store_true",
        help="Обработать только один файл, а не всю директорию",
    )

    args = parser.parse_args()

    path = Path(args.path)

    if not path.exists():
        print(f"Путь {path} не существует!")
        return

    files_to_process = []

    if args.file or path.is_file():
        if path.suffix == ".py":
            files_to_process = [str(path)]
        else:
            print("Указанный файл не является Python файлом (.py)")
            return
    else:
        files_to_process = find_python_files(str(path))

    if not files_to_process:
        print("Python файлы не найдены!")
        return

    print(f"Найдено {len(files_to_process)} Python файлов для обработки:")
    for file_path in files_to_process:
        print(f"  {file_path}")

    if not args.no_backup:
        response = input("\nСоздать резервные копии? (y/n): ")
        create_backup = response.lower() in ["y", "yes", "д", "да"]
    else:
        create_backup = False

    confirm = input(f"Продолжить обработку {len(files_to_process)} файлов? (y/n): ")
    if confirm.lower() not in ["y", "yes", "д", "да"]:
        print("Операция отменена.")
        return

    processed = 0
    for file_path in files_to_process:
        print(f"Обрабатывается: {file_path}")
        if process_file(file_path, backup=create_backup):
            processed += 1
        else:
            print(f"Ошибка при обработке: {file_path}")

    print(f"\nОбработано файлов: {processed}/{len(files_to_process)}")

    if create_backup:
        print("\nДля восстановления исходных файлов можно использовать:")
        print(
            "find . -name '*.backup' -exec sh -c 'mv \"$1\" \"${1%.backup}\"' _ {} \\;"
        )


if __name__ == "__main__":
    main()
