"""
Simulation script for the LLM Mafia Game Competition (LOCAL MODELS ONLY, MULTI-CLONE).
"""

import time
import random
import concurrent.futures
from collections import defaultdict
import config
from game import MafiaGame
from firebase_manager import FirebaseManager
from logger import GameLogger, Color

def run_single_game(game_number, language=None, model_name=None):
    """
    Run a single Mafia game (all players as clones of model_name).
    Args:
        game_number (int)
        language (optional)
        model_name (str): model to use for all players
    Returns:
        tuple: (game_number, winner, rounds_data, participants, game_id, language, critic_review)
    """
    game = MafiaGame(language=language)
    winner, rounds_data, participants, language, critic_review = game.run_game(game_number)
    return (
        game_number,
        winner,
        rounds_data,
        participants,
        game.game_id,
        language,
        critic_review,
    )

def run_simulation(
        num_games=config.NUM_GAMES,
        parallel=False,
        max_workers=4,
        language=None,
        model_name=None,
):

    logger = GameLogger()
    logger.header(f"STARTING SIMULATION WITH {num_games} GAMES", Color.BRIGHT_MAGENTA)
    start_time = time.time()

    # Initialize Firebase
    firebase = FirebaseManager()
    stats = {
        "total_games": num_games,
        "completed_games": 0,
        "mafia_wins": 0,
        "villager_wins": 0,
        "model_stats": defaultdict(
            lambda: {
                "games": 0,
                "wins": 0,
                "mafia_games": 0,
                "mafia_wins": 0,
                "villager_games": 0,
                "villager_wins": 0,
                "doctor_games": 0,
                "doctor_wins": 0,
            }
        ),
    }

    game_language = language if language is not None else config.LANGUAGE
    model_to_use = model_name if model_name is not None else (
        config.MODELS[0] if config.MODELS else None
    )

    if not model_to_use:
        logger.error("No model specified in config.MODELS!")
        return stats

    # Sequential or parallel run
    def handle_result(fut, game_number=None):  # utility for both code paths
        try:
            (
                game_number,
                winner,
                rounds_data,
                participants,
                game_id,
                language,
                critic_review,
            ) = fut if isinstance(fut, tuple) else fut.result()
            # Firebase
            if firebase.initialized:
                firebase.store_game_result(
                    game_id, winner, participants, language=language
                )
                firebase.store_game_log(
                    game_id,
                    rounds_data,
                    participants,
                    language=language,
                    critic_review=critic_review,
                )
            # Stats
            stats["completed_games"] += 1
            if winner == "Mafia":
                stats["mafia_wins"] += 1
            else:
                stats["villager_wins"] += 1
            for player_name, role_data in participants.items():
                # Modern format:
                if isinstance(role_data, dict):
                    role = role_data.get("role")
                    model = role_data.get("model_name", model_to_use)
                else:
                    role = role_data
                    model = model_to_use
                stats["model_stats"][model]["games"] += 1
                if role == "Mafia":
                    stats["model_stats"][model]["mafia_games"] += 1
                    if winner == "Mafia":
                        stats["model_stats"][model]["mafia_wins"] += 1
                        stats["model_stats"][model]["wins"] += 1
                elif role == "Doctor":
                    stats["model_stats"][model]["doctor_games"] += 1
                    if winner == "Villagers":
                        stats["model_stats"][model]["doctor_wins"] += 1
                        stats["model_stats"][model]["wins"] += 1
                else:
                    stats["model_stats"][model]["villager_games"] += 1
                    if winner == "Villagers":
                        stats["model_stats"][model]["villager_wins"] += 1
                        stats["model_stats"][model]["wins"] += 1
            # Log game
            win_color = Color.RED if winner == "Mafia" else Color.GREEN
            logger.print(
                f"Game {game_number} completed. Winner: {winner}",
                win_color,
                bold=True,
            )
        except Exception as e:
            logger.error(f"Game {game_number if game_number is not None else '?'} generated an exception: {e}")

    if parallel and num_games > 1:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_game = {
                executor.submit(
                    run_single_game,
                    i,
                    game_language,
                    model_to_use,
                ): i
                for i in range(1, num_games + 1)
            }
            for future in concurrent.futures.as_completed(future_to_game):
                game_number = future_to_game[future]
                handle_result(future, game_number)
    else:
        for i in range(1, num_games + 1):
            res = run_single_game(i, game_language, model_to_use)
            handle_result(res, i)

    elapsed_time = time.time() - start_time
    stats["elapsed_time"] = elapsed_time
    logger.stats(stats)
    num = stats["completed_games"]
    mafia = stats["mafia_wins"]
    village = stats["villager_wins"]
    print("\n======= GAME RESULT SUMMARY =======")
    print(f"Всего партий: {num}")
    print(f"Побед мафии: {mafia}   ({mafia/num:.1%})")
    print(f"Побед мирных: {village}   ({village/num:.1%})")
    return stats

if __name__ == "__main__":
    if config.RANDOM_SEED is not None:
        random.seed(config.RANDOM_SEED)
    run_simulation(num_games=config.NUM_GAMES)
