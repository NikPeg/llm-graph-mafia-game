"""
Configuration settings for the LLM Mafia Game Competition.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# OpenRouter API settings
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "your_openrouter_api_key_here")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Firebase settings
FIREBASE_CREDENTIALS_PATH = (
    "firebase_credentials.json"  # Path to your Firebase credentials file
)

# Game settings

CLAUDE_3_7_SONNET = "deepseek/deepseek-r1-distill-llama-70b:free"
MODELS = [
    "mistralai/mistral-small-3.2-24b-instruct:free",
    "minimax/minimax-m1:extended",
    "moonshotai/kimi-dev-72b:free",
    "deepseek/deepseek-r1-0528-qwen3-8b:free",
    "deepseek/deepseek-r1-0528:free",
    "sarvamai/sarvam-m:free",
    "mistralai/devstral-small:free",
    "google/gemma-3n-e4b-it:free",
    "qwen/qwen3-30b-a3b:free",
    "qwen/qwen3-14b:free",
    "qwen/qwen3-235b-a22b:free",
    "tngtech/deepseek-r1t-chimera:free",
]

# Game configuration
NUM_GAMES = int(os.getenv("NUM_GAMES", 1))  # Number of games to simulate
PLAYERS_PER_GAME = int(
    os.getenv("PLAYERS_PER_GAME", 8)
)  # Number of players in each game
MAFIA_COUNT = int(os.getenv("MAFIA_COUNT", 2))  # Number of Mafia players
DOCTOR_COUNT = int(os.getenv("DOCTOR_COUNT", 1))  # Number of Doctor players
# Villagers will be: PLAYERS_PER_GAME - MAFIA_COUNT - DOCTOR_COUNT

# Game type
GAME_TYPE = "Classic Mafia"  # Type of Mafia game to run

# Language setting
LANGUAGE = os.getenv(
    "GAME_LANGUAGE", "English"
)  # Language for game prompts and interactions (supported: English, Spanish, French, Korean)

# Maximum number of rounds before declaring a draw
MAX_ROUNDS = int(os.getenv("MAX_ROUNDS", 20))

# Timeout for API calls (in seconds)
API_TIMEOUT = int(os.getenv("API_TIMEOUT", 60))

# Maximum output tokens for LLM responses
MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", 400))

# Model-specific configurations
MODEL_CONFIGS = {
    "deepseek/deepseek-r1": {
        "timeout": 90,  # Longer timeout for DeepSeek-R1
    },
    "deepseek/deepseek-r1:free": {
        "timeout": 90,
    },
    "deepseek/deepseek-r1-distill-llama-70b": {
        "timeout": 90,
    },
    "deepseek/deepseek-r1-distill-llama-70b:free": {
        "timeout": 90,
    },
    "deepseek/deepseek-chat": {
        "timeout": 60,
    },
}

# Random seed for reproducibility (set to None for random behavior)
RANDOM_SEED = os.getenv("RANDOM_SEED")
if RANDOM_SEED is not None:
    RANDOM_SEED = int(RANDOM_SEED)

UNIQUE_MODELS = os.getenv("UNIQUE_MODELS", "true") == "true"
