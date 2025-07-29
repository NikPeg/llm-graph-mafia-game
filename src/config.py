"""
Configuration settings for the LLM Mafia Game Competition (LOCAL MODELS ONLY).
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Port-based model configuration
LARGE_MODEL_PORT = int(os.getenv("LARGE_MODEL_PORT", 8000))
SMALL_MODEL_PORT = int(os.getenv("SMALL_MODEL_PORT", 8001))

# Model names for each port (for Firebase logging and dashboard display)
LARGE_MODEL_NAME = os.getenv("LARGE_MODEL_NAME", "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B")
SMALL_MODEL_NAME = os.getenv("SMALL_MODEL_NAME", "deepseek/deepseek-llm-7b-chat")

# Dynamic API URLs based on ports
def get_api_url_for_port(port):
    return f"http://localhost:{port}/v1/chat/completions"

OPENROUTER_API_URL = os.getenv(
    "OPENROUTER_API_URL", get_api_url_for_port(LARGE_MODEL_PORT)
)

LOCAL_LLM_API_URL = os.getenv(
    "LOCAL_LLM_API_URL", get_api_url_for_port(LARGE_MODEL_PORT)
)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "local_test_key")

FIREBASE_CREDENTIALS_PATH = "firebase_credentials.json"

# Available models for reference
AVAILABLE_MODELS = [
    "gryphe/mythomax-l2-13b",
    "mistralai/mistral-small-24b-instruct-2501",
    "deepseek/deepseek-llm-7b-chat",
    "deepseek/deepseek-r1-distill-llama-70b",
    "nousresearch/hermes-3-llama-3.1-70b",
    "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
]

# Default model (first in the list)
DEFAULT_MODEL = "gryphe/mythomax-l2-13b"

# Experiment mode: 'single' for same model, 'role_specific' for different models per role
EXPERIMENT_MODE = os.getenv("EXPERIMENT_MODE", "single")

# Single model configuration (used when EXPERIMENT_MODE='single')
MODEL_NAME = os.getenv("MODEL_NAME", DEFAULT_MODEL)

# Role-specific model configuration (used when EXPERIMENT_MODE='role_specific')
# Now supports both port-based and direct model specification
MAFIA_MODEL_PORT = int(os.getenv("MAFIA_MODEL_PORT", LARGE_MODEL_PORT))
VILLAGER_MODEL_PORT = int(os.getenv("VILLAGER_MODEL_PORT", SMALL_MODEL_PORT))
DOCTOR_MODEL_PORT = int(os.getenv("DOCTOR_MODEL_PORT", SMALL_MODEL_PORT))

# Legacy support for direct model names (will be overridden by port-based config)
MAFIA_MODEL = os.getenv("MAFIA_MODEL", LARGE_MODEL_NAME)
VILLAGER_MODEL = os.getenv("VILLAGER_MODEL", SMALL_MODEL_NAME)
DOCTOR_MODEL = os.getenv("DOCTOR_MODEL", SMALL_MODEL_NAME)

def get_model_for_role(role):
    """
    Get the appropriate model name and API URL for a given role.
    
    Args:
        role (str): The role name ('Mafia', 'Villager', 'Doctor')
        
    Returns:
        tuple: (model_name, api_url) for this role
    """
    if EXPERIMENT_MODE == "role_specific":
        role_config = {
            "Mafia": (MAFIA_MODEL_PORT, LARGE_MODEL_NAME if MAFIA_MODEL_PORT == LARGE_MODEL_PORT else SMALL_MODEL_NAME),
            "Villager": (VILLAGER_MODEL_PORT, LARGE_MODEL_NAME if VILLAGER_MODEL_PORT == LARGE_MODEL_PORT else SMALL_MODEL_NAME),
            "Doctor": (DOCTOR_MODEL_PORT, LARGE_MODEL_NAME if DOCTOR_MODEL_PORT == LARGE_MODEL_PORT else SMALL_MODEL_NAME),
        }
        port, model_name = role_config.get(role, (LARGE_MODEL_PORT, MODEL_NAME))
        api_url = get_api_url_for_port(port)
        return model_name, api_url
    else:
        # Single model mode - use the default port and model
        default_port = int(os.getenv("DEFAULT_MODEL_PORT", LARGE_MODEL_PORT))
        default_model = os.getenv("MODEL_NAME", LARGE_MODEL_NAME)
        api_url = get_api_url_for_port(default_port)
        return default_model, api_url

def get_model_name_for_role(role):
    """
    Get just the model name for a given role (for backward compatibility).
    
    Args:
        role (str): The role name ('Mafia', 'Villager', 'Doctor')
        
    Returns:
        str: The model name to use for this role
    """
    model_name, _ = get_model_for_role(role)
    return model_name

# Legacy alias for compatibility (uses single model or mafia model for critic reviews)
CLAUDE_3_7_SONNET = MAFIA_MODEL if EXPERIMENT_MODE == "role_specific" else MODEL_NAME

NUM_GAMES = int(os.getenv("NUM_GAMES", 1))
PARALLEL = os.getenv("PARALLEL", "false").lower() == "true"
MAX_WORKERS = int(os.getenv("MAX_WORKERS", 4))
PLAYERS_PER_GAME = int(os.getenv("PLAYERS_PER_GAME", 8))
MAFIA_COUNT = int(os.getenv("MAFIA_COUNT", 2))
DOCTOR_COUNT = int(os.getenv("DOCTOR_COUNT", 1))

GAME_TYPE = "Classic Mafia"
LANGUAGE = os.getenv("GAME_LANGUAGE", "English")
MAX_ROUNDS = int(os.getenv("MAX_ROUNDS", 20))
API_TIMEOUT = int(os.getenv("API_TIMEOUT", 60))
MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", 300))
MAX_MSG = int(os.getenv("MAX_MSG", 400))
DISCUSSION_HISTORY_LIMIT = int(os.getenv("DISCUSSION_HISTORY_LIMIT", 10))
GRAPH_DEBUG = bool(os.getenv("GRAPH_DEBUG", True))

# RAG (Retrieval-Augmented Generation) settings
RAG_TYPE = os.getenv("RAG_TYPE", "discussion_graph")  # discussion_graph, history_graph, current_round_graph, communication_graph, auto_summaries, analytical_hints
RAG_TARGET = os.getenv("RAG_TARGET", "all")  # all, mafia, villagers
RAG_ENABLED = os.getenv("RAG_ENABLED", "true").lower() == "true"

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
