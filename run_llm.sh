#!/bin/bash
set -e

# --- КОНФИГУРАЦИЯ ---
START_PORT=8000
MAX_LEN=8192
CHAT_TEMPLATE="./alpaca_chat_template.jinja"
GPU_MEM_UTIL=0.98
# --------------------

# --- КОРРЕКТНАЯ ОЧИСТКА ПЕРЕД ЗАПУСКОМ ---
echo "Поиск и остановка любых предыдущих экземпляров vLLM..."
# Находим PID и сохраняем в переменную
PIDS_TO_KILL=$(pgrep -f "vllm serve")

# Проверяем, не пуста ли переменная с PID'ами
if [ -n "$PIDS_TO_KILL" ]; then
    echo "Найдены запущенные серверы vLLM (PIDs: $PIDS_TO_KILL). Останавливаю..."
    # Убиваем только если что-то найдено
    kill $PIDS_TO_KILL
    sleep 5 # Даем время процессам корректно завершиться
    echo "Очистка завершена."
else
    echo "Запущенных серверов vLLM не найдено. Пропускаю очистку."
fi
# -------------------------------------------

if [ $# -eq 0 ]; then
    echo "Ошибка: Не указаны модели для запуска."
    echo "Пример использования: $0 Qwen/Qwen3-32B-AWQ Qwen/Qwen3-8B-AWQ"
    exit 1
fi

if [ ! -f "$CHAT_TEMPLATE" ]; then
    echo "Предупреждение: Файл шаблона '$CHAT_TEMPLATE' не найден."
fi

CURRENT_PORT=$START_PORT
PIDS=()

for MODEL in "$@"; do
    SANITIZED_MODEL_NAME=$(echo "$MODEL" | tr '/' '_')
    LOG_FILE="vllm_${SANITIZED_MODEL_NAME}_${CURRENT_PORT}.log"

    echo "---"
    echo "Подготовка к запуску модели: $MODEL"

    COMMAND=(
        "vllm" "serve" "$MODEL"
        "--port" "$CURRENT_PORT"
        "--max-model-len" "$MAX_LEN"
        "--gpu-memory-utilization" "$GPU_MEM_UTIL"
    )

    if [[ "$MODEL" == *"32B"* ]] || [[ "$MODEL" == *"70B"* ]]; then
        echo "  Обнаружена большая модель. Отключаем кастомные ядра (--disable-custom-all) для максимальной стабильности."
        COMMAND+=("--disable-custom-all")
    fi

    if [[ "$MODEL" == *"-AWQ"* ]] || [[ "$MODEL" == *"-awq"* ]]; then
        echo "  Тип: AWQ-квантованная"
        COMMAND+=("--quantization" "awq")
    else
        echo "  Тип: Полная версия (FP16/BF16)"
    fi

    if [ -f "$CHAT_TEMPLATE" ]; then
        COMMAND+=("--chat-template" "$CHAT_TEMPLATE")
    fi

    echo "  Порт: $CURRENT_PORT"
    echo "  Использование GPU: ${GPU_MEM_UTIL} (98%)"
    echo "  Лог-файл: $LOG_FILE"
    
    nohup "${COMMAND[@]}" > "$LOG_FILE" 2>&1 &
    
    PID=$!
    PIDS+=($PID)
    
    echo "Модель $MODEL отправлена на запуск. PID: $PID"
    
    if [[ "$MODEL" == *"32B"* ]]; then
        echo "Пауза 30 секунд после запуска 32B модели..."
        sleep 30
    fi

    CURRENT_PORT=$((CURRENT_PORT + 1))
done

echo "---"
echo "Все модели отправлены на запуск."
echo "Запущенные процессы (PIDs): ${PIDS[*]}"
echo "Используйте 'tail -f <имя_файла.log>' для мониторинга запуска."
