#!/bin/bash
set -e

# --- КОНФИГУРАЦИЯ ---
START_PORT=8000
MAX_LEN=8192
CHAT_TEMPLATE="./alpaca_chat_template.jinja"
# Процент использования GPU. Увеличим до 95%
GPU_MEM_UTIL=0.95 
# --------------------

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

    # Для больших моделей отключаем torch.compile, чтобы избежать пиков VRAM
    if [[ "$MODEL" == *"32B"* ]] || [[ "$MODEL" == *"70B"* ]]; then
        echo "  Обнаружена большая модель. Отключаем кастомные ядра для стабильного запуска."
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
    echo "  Использование GPU: ${GPU_MEM_UTIL}"
    echo "  Лог-файл: $LOG_FILE"
    
    nohup "${COMMAND[@]}" > "$LOG_FILE" 2>&1 &
    
    PID=$!
    PIDS+=($PID)
    
    echo "Модель $MODEL запущена. PID: $PID"
    
    # Дадим первой модели время на инициализацию перед запуском второй
    if [ $# -gt 1 ]; then
        echo "Пауза 15 секунд перед запуском следующей модели..."
        sleep 15
    fi

    CURRENT_PORT=$((CURRENT_PORT + 1))
done

echo "---"
echo "Все модели отправлены на запуск."
echo "Запущенные процессы (PIDs): ${PIDS[*]}"
