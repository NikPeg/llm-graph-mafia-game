"""
Configuration settings for the LLM Mafia Game Competition (LOCAL MODELS ONLY).
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# OpenAI-совместимый локальный API (например, vLLM или text-generation-webui)
OPENROUTER_API_URL = os.getenv("LOCAL_LLM_API_URL", "http://localhost:8000/v1/chat/completions")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "local_test_key")  # любой ключ, если сервер не требует

# Firebase settings (не изменяем для локального теста)
FIREBASE_CREDENTIALS_PATH = "firebase_credentials.json"

# Game settings

# Только модели, доступные локально и по размеру подходящие для вашей GPU
MODELS = [
    "meta-llama/llama-3-8b-instruct",               # 8B
    "meta-llama/llama-3-8b",                        # 8B base
    "meta-llama/llama-3-13b-instruct",              # 13B
    "meta-llama/llama-3-13b",                       # 13B base
    "meta-llama/llama-2-13b-hf",                    # Llama 2 13B (если нужен)
    "mistralai/mistral-7b-instruct-v0.2",           # Mistral 7B
    "mistralai/mistral-7b-instruct",                # Mistral 7B (старше)
    "deepseek-ai/deepseek-llm-7b-chat",             # DeepSeek 7B-Chat
    "deepseek-ai/deepseek-llm-33b-chat",            # DeepSeek 33B-Chat (32B+)
    "deepseek-ai/deepseek-llm-33b-base",            # DeepSeek 33B-Base
    "cognitivecomputations/dolphin-2.6-mistral-7b", # Dolphin на Mistral 7B
    "nousresearch/hermes-2-mistral-7b",             # Hermes на Mistral 7B
    "gryphe/mythomax-l2-13b",                       # MythoMax на Llama 13B
    "qwen/qwen1.5-7b-chat",                         # Qwen 7B
    "qwen/qwen1.5-32b-chat",                        # Qwen 32B (32B подходит для вашей GPU)
    "microsoft/WizardLM-2-8x22B",                   # WizardLM (если есть open weights): 8x22B (примерно 32-40B суммарно)
    # Добавьте другие open-source модели до ~40B, которые хотите тестировать
]

# FREE_MODELS можем игнорировать, либо оставить для внутренних тестов
FREE_MODELS = [
    "deepseek-ai/deepseek-llm-33b-chat",    # те же, что реально есть у вас локально
    "qwen/qwen1.5-32b-chat",
    "meta-llama/llama-3-13b-instruct",
    "mistralai/mistral-7b-instruct-v0.2",
    "gryphe/mythomax-l2-13b",
]

# Game configuration (оставим как есть)
NUM_GAMES = int(os.getenv("NUM_GAMES", 1))
PLAYERS_PER_GAME = int(os.getenv("PLAYERS_PER_GAME", 8))
MAFIA_COUNT = int(os.getenv("MAFIA_COUNT", 2))
DOCTOR_COUNT = int(os.getenv("DOCTOR_COUNT", 1))
# Villagers will be: PLAYERS_PER_GAME - MAFIA_COUNT - DOCTOR_COUNT

GAME_TYPE = "Classic Mafia"
LANGUAGE = os.getenv("GAME_LANGUAGE", "English")
MAX_ROUNDS = int(os.getenv("MAX_ROUNDS", 20))
API_TIMEOUT = int(os.getenv("API_TIMEOUT", 60))
MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", 400))

# Model-specific configurations (можно дополнять под свои нужды)
MODEL_CONFIGS = {
    "deepseek-ai/deepseek-llm-33b-chat": {
        "timeout": 90,
    },
    "qwen/qwen1.5-32b-chat": {
        "timeout": 90,
    },
}

RANDOM_SEED = os.getenv("RANDOM_SEED")
if RANDOM_SEED is not None:
    RANDOM_SEED = int(RANDOM_SEED)

UNIQUE_MODELS = os.getenv("UNIQUE_MODELS", "true") == "true"
