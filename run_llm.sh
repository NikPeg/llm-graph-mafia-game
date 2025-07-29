#!/bin/bash

# Модель по умолчанию
DEFAULT_MODEL="gryphe/mythomax-l2-13b"

# Если передан аргумент, берем его, иначе дефолт
MODEL=${1:-$DEFAULT_MODEL}

# Проверяем, является ли модель AWQ-квантованной
if [[ "$MODEL" == *"AWQ"* ]] || [[ "$MODEL" == *"awq"* ]]; then
    echo "Запускаю квантованную модель: $MODEL с AWQ квантованием"
    nohup vllm serve "$MODEL" --quantization awq --chat-template ./alpaca_chat_template.jinja > vllm.log 2>&1 &
else
    echo "Запускаю модель: $MODEL"
    nohup vllm serve "$MODEL" --chat-template ./alpaca_chat_template.jinja > vllm.log 2>&1 &
fi

echo "Модель $MODEL запущена в фоне. Логи: vllm.log"