#!/bin/bash

# Модель по умолчанию
DEFAULT_MODEL="gryphe/mythomax-l2-13b"

# Если передан аргумент, берем его, иначе дефолт
MODEL=${1:-$DEFAULT_MODEL}

echo "Запускаю модель: $MODEL"
nohup vllm serve "$MODEL" --chat-template ./alpaca_chat_template.jinja > vllm.log 2>&1 &

echo "Модель $MODEL запущена в фоне. Логи: vllm.log"