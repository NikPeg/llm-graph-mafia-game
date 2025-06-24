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

MODELS = [
    "gryphe/mythomax-l2-13b",
    "mistralai/mistral-small-24b-instruct-2501",
    "deepseek/deepseek-llm-7b-chat",
    "deepseek/deepseek-r1-distill-llama-70b",
    "nousresearch/hermes-3-llama-3.1-70b",
    "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
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
