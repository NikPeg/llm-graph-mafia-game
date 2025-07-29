#!/bin/bash

# Модель по умолчанию
DEFAULT_MODEL="gryphe/mythomax-l2-13b"
# Максимальная длина контекста, которую мы реально будем использовать
# Установите значение, подходящее для вашей видеокарты и задач (например, 4096, 8192, 16384)
MAX_LEN=8192

# Если передан аргумент, берем его, иначе дефолт
MODEL=${1:-$DEFAULT_MODEL}

# Проверяем, является ли модель AWQ-квантованной
if [[ "$MODEL" == *"AWQ"* ]] || [[ "$MODEL" == *"awq"* ]]; then
    echo "Запускаю квантованную модель: $MODEL с AWQ и max_len=$MAX_LEN"
    nohup vllm serve "$MODEL" \
        --quantization awq \
        --max-model-len $MAX_LEN \
        --chat-template ./alpaca_chat_template.jinja > vllm.log 2>&1 &
else
    echo "Запускаю модель: $MODEL с max_len=$MAX_LEN"
    nohup vllm serve "$MODEL" \
        --max-model-len $MAX_LEN \
        --chat-template ./alpaca_chat_template.jinja > vllm.log 2>&1 &
fi

echo "Модель $MODEL запущена в фоне. Логи: vllm.log. ID процесса: $!"
