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
    winner, rounds_data, participants, language, critic_review, game_stats, rag_info = game.run_game(
        game_number
    )
    return (
        game_number,
        winner,
        rounds_data,
        participants,
        game.game_id,
        language,
        critic_review,
        game_stats,
        rag_info,
    )


def run_simulation(
    num_games=config.NUM_GAMES,
    parallel=config.PARALLEL,
    max_workers=config.MAX_WORKERS,
    language=None,
    model_name=None,
):
    logger = GameLogger(game_id="SIMULATION")
    logger.header(f"STARTING SIMULATION WITH {num_games} GAMES", Color.BRIGHT_MAGENTA)
    
    # Выводим условия игры с RAG
    if config.RAG_ENABLED:
        from rag_providers import RAGManager
        rag_manager = RAGManager()
        rag_full_name = {
            "discussion_graph": "Discussion Graph",
            "history_graph": "History Graph",
            "current_round_graph": "Current Round Graph",
            "communication_graph": "Communication Graph",
            "auto_summaries": "Auto Summaries",
            "analytical_hints": "Analytical Hints"
        }.get(config.RAG_TYPE, config.RAG_TYPE)
        
        rag_short_name = rag_manager.get_short_name(config.RAG_TYPE)
        
        if config.RAG_TARGET == "all":
            target_desc = "All players"
        elif config.RAG_TARGET == "mafia":
            target_desc = "Mafia team"
        elif config.RAG_TARGET == "villagers":
            target_desc = "Villagers team"
        else:
            target_desc = config.RAG_TARGET
            
        logger.print(f"Game Conditions: {target_desc} playing with {rag_full_name} ({rag_short_name})", Color.BRIGHT_CYAN, bold=True)
    else:
        logger.print("Game Conditions: No RAG enhancement", Color.BRIGHT_CYAN, bold=True)
    
    logger.print("")
    start_time = time.time()

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
    model_to_use = model_name or config.DEFAULT_MODEL

    if not model_to_use:
        logger.error("No model specified in config.MODELS!")
        return stats

    def handle_result(fut, game_number=None):
        try:
            (
                game_number,
                winner,
                rounds_data,
                participants,
                game_id,
                language,
                critic_review,
                game_stats,
                rag_info,
            ) = fut if isinstance(fut, tuple) else fut.result()

            if firebase.initialized:
                firebase.store_game_result(
                    game_id, winner, participants, language=language, game_stats=game_stats, rag_info=rag_info
                )
                firebase.store_game_log(
                    game_id,
                    rounds_data,
                    participants,
                    language=language,
                    critic_review=critic_review,
                    game_stats=game_stats,
                    rag_info=rag_info,
                )

            stats["completed_games"] += 1
            if winner == "Mafia":
                stats["mafia_wins"] += 1
            else:
                stats["villager_wins"] += 1
            for player_name, role_data in participants.items():
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

            win_color = Color.RED if winner == "Mafia" else Color.GREEN
            logger.print(
                f"Game {game_number} completed. Winner: {winner}",
                win_color,
                bold=True,
            )
        except Exception as e:
            logger.error(
                f"Game {game_number if game_number is not None else '?'} generated an exception: {e}"
            )

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
    print(f"Побед мафии: {mafia}   ({mafia / num:.1%})")
    print(f"Побед мирных: {village}   ({village / num:.1%})")
    return stats


if __name__ == "__main__":
    if config.RANDOM_SEED is not None:
        random.seed(config.RANDOM_SEED)
    run_simulation(
        num_games=config.NUM_GAMES,
        parallel=config.PARALLEL,
        max_workers=config.MAX_WORKERS
    )
