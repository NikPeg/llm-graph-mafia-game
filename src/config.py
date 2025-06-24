"""
Configuration settings for the LLM Mafia Game Competition (LOCAL MODELS ONLY).
"""

import os
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_URL = os.getenv("OPENROUTER_API_URL", "http://localhost:8000/v1/completions")

# OpenAI-совместимый локальный API (например, vLLM)
# Endpoints:
# vLLM:         http://localhost:8000/v1/completions
# text-gen-ui:  http://localhost:5000/v1/completions
LOCAL_LLM_API_URL = os.getenv("LOCAL_LLM_API_URL", "http://localhost:8000/v1/completions")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "local_test_key")

# Firebase settings (не изменяем для локального теста)
FIREBASE_CREDENTIALS_PATH = "firebase_credentials.json"

# Модели - список строк Huggingface
MODELS = os.getenv(
    "MODELS",
    "gryphe/mythomax-l2-13b,mistralai/mistral-small-24b-instruct-2501,deepseek/deepseek-llm-7b-chat,deepseek/deepseek-r1-distill-llama-70b,nousresearch/hermes-3-llama-3.1-70b,deepseek-ai/DeepSeek-R1-Distill-Qwen-32B"
).split(",")

# Game configuration
NUM_GAMES = int(os.getenv("NUM_GAMES", 1))
PLAYERS_PER_GAME = int(os.getenv("PLAYERS_PER_GAME", 8))
MAFIA_COUNT = int(os.getenv("MAFIA_COUNT", 2))
DOCTOR_COUNT = int(os.getenv("DOCTOR_COUNT", 1))

GAME_TYPE = "Classic Mafia"
LANGUAGE = os.getenv("GAME_LANGUAGE", "English")
MAX_ROUNDS = int(os.getenv("MAX_ROUNDS", 20))
API_TIMEOUT = int(os.getenv("API_TIMEOUT", 60))
MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", 400))

MODEL_CONFIGS = {
    "gryphe/mythomax-l2-13b": {"timeout": 60},
    "mistralai/mistral-small-24b-instruct-2501": {"timeout": 75},
    "deepseek/deepseek-llm-7b-chat": {"timeout": 60},
    "deepseek/deepseek-r1-distill-llama-70b": {"timeout": 75},
    "nousresearch/hermes-3-llama-3.1-70b": {"timeout": 75},
    "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B": {"timeout": 75},
}

RANDOM_SEED = os.getenv("RANDOM_SEED")
if RANDOM_SEED is not None:
    RANDOM_SEED = int(RANDOM_SEED)

UNIQUE_MODELS = os.getenv("UNIQUE_MODELS", "true").lower() == "true"
