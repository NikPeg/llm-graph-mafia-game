#!/bin/bash
set -e

# --- КОНФИГУРАЦИЯ ---
START_PORT=8000
MAX_LEN=8192
CHAT_TEMPLATE="./alpaca_chat_template.jinja"
# Устанавливаем очень высокий лимит использования VRAM
GPU_MEM_UTIL=0.98 
# --------------------

# --- ОЧИСТКА ПЕРЕД ЗАПУСКОМ ---
echo "Останавливаем любые предыдущие экземпляры vLLM..."
# `|| true` предотвращает падение скрипта, если процессов для остановки нет
kill $(pgrep -f "vllm serve") || true
sleep 5 # Даем время процессам завершиться
# -------------------------------

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

    # ДЛЯ БОЛЬШИХ МОДЕЛЕЙ: Отключаем torch.compile для стабильного запуска.
    # Это самый надежный способ избежать пиков потребления VRAM.
    if [[ "$MODEL" == *"32B"* ]] || [[ "$MODEL" == *"70B"* ]]; then
        echo "  Обнаружена большая модель. Отключаем кастомные ядра (`--disable-custom-all`) для максимальной стабильности."
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
    
    # После запуска большой модели сделаем паузу
    if [[ "$MODEL" == *"32B"* ]]; then
        echo "Пауза 30 секунд после запуска 32B модели, чтобы дать ей время на инициализацию..."
        sleep 30
    fi

    CURRENT_PORT=$((CURRENT_PORT + 1))
done

echo "---"
echo "Все модели отправлены на запуск."
echo "Запущенные процессы (PIDs): ${PIDS[*]}"
echo "Используйте 'tail -f <имя_файла.log>' для мониторинга запуска."
