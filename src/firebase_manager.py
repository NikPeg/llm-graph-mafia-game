"""
Firebase manager for the LLM Mafia Game Competition.
"""

import json
import time
import firebase_admin
from firebase_admin import credentials, firestore
import os
import sys

try:
    import src.config as config
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import config


class FirebaseManager:
    """Manages Firebase database operations for the Mafia game."""

    def __init__(self):
        """Initialize the Firebase manager."""
        try:
            cred = credentials.Certificate(config.FIREBASE_CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred)
            self.db = firestore.client()
            self.initialized = True
            print("Firebase initialized successfully.")
        except Exception as e:
            print(f"Error initializing Firebase: {e}")
            self.initialized = False

    def store_game_result(
        self,
        game_id,
        winner,
        participants,
        game_type=config.GAME_TYPE,
        language=config.LANGUAGE,
        game_stats=None,
    ):
        """
        Store the result of a game in Firebase.

        Args:
            game_id (str): Unique identifier for the game.
            winner (str): The winning team ("Mafia" or "Villagers").
            participants (dict): Dictionary mapping model names to role and player_name.
            game_type (str, optional): Type of Mafia game played.
            language (str, optional): Language used for the game.
            game_stats (dict, optional): Additional game statistics.

        Returns:
            bool: True if successful, False otherwise.
        """
        if not self.initialized:
            print("Firebase not initialized. Cannot store game result.")
            return False

        try:
            game_data = {
                "game_id": game_id,
                "timestamp": int(time.time()),
                "game_type": game_type,
                "language": language,
                "participant_count": len(participants),
                "winner": winner,
                "participants": participants,
            }
            
            # Добавляем дополнительную статистику если она есть
            if game_stats:
                game_data.update(game_stats)

            self.db.collection("mafia_games").document(game_id).set(game_data)
            return True
        except Exception as e:
            print(f"Error storing game result: {e}")
            return False

    def store_game_log(
        self,
        game_id,
        rounds,
        participants,
        game_type=config.GAME_TYPE,
        language=config.LANGUAGE,
        critic_review=None,
        game_stats=None,
    ):
        """
        Store the log of a game in Firebase.

        Args:
            game_id (str): Unique identifier for the game.
            rounds (list): List of round data.
            participants (dict): Dictionary mapping model names to role and player_name.
            game_type (str, optional): Type of Mafia game played.
            language (str, optional): Language used for the game.
            critic_review (dict, optional): Game critic review with title and content.
            game_stats (dict, optional): Additional game statistics.

        Returns:
            bool: True if successful, False otherwise.
        """
        if not self.initialized:
            print("Firebase not initialized. Cannot store game log.")
            return False

        try:
            log_data = {
                "game_id": game_id,
                "timestamp": int(time.time()),
                "game_type": game_type,
                "language": language,
                "participant_count": len(participants),
                "rounds": rounds,
            }

            if critic_review:
                log_data["critic_review"] = critic_review
                
            if game_stats:
                log_data["game_stats"] = game_stats

            self.db.collection("game_logs").document(game_id).set(log_data)
            return True
        except Exception as e:
            print(f"Error storing game log: {e}")
            return False

    def get_game_results(self, limit=100):
        """
        Get the results of games from Firebase.

        Args:
            limit (int, optional): Maximum number of results to retrieve.

        Returns:
            list: List of game results.
        """
        if not self.initialized:
            print("Firebase not initialized. Cannot get game results.")
            return []

        try:
            results = (
                self.db.collection("mafia_games")
                .order_by("timestamp", direction=firestore.Query.DESCENDING)
                .limit(limit)
                .stream()
            )

            return [doc.to_dict() for doc in results]
        except Exception as e:
            print(f"Error getting game results: {e}")
            return []

    def get_model_stats(self):
        """
        Get statistics for each model from Firebase.

        Returns:
            dict: Dictionary mapping model names to statistics.
        """
        if not self.initialized:
            print("Firebase not initialized. Cannot get model stats.")
            return {}

        try:
            results = self.get_game_results(limit=1000)

            stats = {}

            for game in results:
                winner = game.get("winner")
                participants = game.get("participants", {})
                total_rounds = game.get("total_rounds", 0)
                survivors_count = game.get("survivors_count", 0)

                for player_name, data in participants.items():
                    if isinstance(data, dict):
                        role = data.get("role")
                        model = data.get("model_name", player_name)
                        survived = data.get("survived", False)
                    else:
                        role = data
                        model = player_name
                        survived = False

                    if model not in stats:
                        stats[model] = {
                            "games_played": 0,
                            "games_won": 0,
                            "mafia_games": 0,
                            "mafia_wins": 0,
                            "villager_games": 0,
                            "villager_wins": 0,
                            "doctor_games": 0,
                            "doctor_wins": 0,
                            "total_rounds": 0,
                            "survival_count": 0,
                            "elimination_count": 0,
                        }

                    stats[model]["games_played"] += 1
                    stats[model]["total_rounds"] += total_rounds
                    
                    if survived:
                        stats[model]["survival_count"] += 1
                    else:
                        stats[model]["elimination_count"] += 1

                    if role == "Mafia":
                        stats[model]["mafia_games"] += 1
                        if winner == "Mafia":
                            stats[model]["mafia_wins"] += 1
                            stats[model]["games_won"] += 1
                    elif role == "Doctor":
                        stats[model]["doctor_games"] += 1
                        if winner == "Villagers":
                            stats[model]["doctor_wins"] += 1
                            stats[model]["games_won"] += 1
                    elif role == "Villager":
                        stats[model]["villager_games"] += 1
                        if winner == "Villagers":
                            stats[model]["villager_wins"] += 1
                            stats[model]["games_won"] += 1

            # Вычисляем дополнительные метрики
            for model in stats:
                games_played = stats[model]["games_played"]
                if games_played > 0:
                    stats[model]["win_rate"] = stats[model]["games_won"] / games_played
                    stats[model]["avg_rounds_per_game"] = stats[model]["total_rounds"] / games_played
                    stats[model]["survival_rate"] = stats[model]["survival_count"] / games_played
                    stats[model]["elimination_rate"] = stats[model]["elimination_count"] / games_played
                else:
                    stats[model]["win_rate"] = 0
                    stats[model]["avg_rounds_per_game"] = 0
                    stats[model]["survival_rate"] = 0
                    stats[model]["elimination_rate"] = 0
                
                stats[model]["mafia_win_rate"] = (
                    stats[model]["mafia_wins"] / stats[model]["mafia_games"]
                    if stats[model]["mafia_games"] > 0
                    else 0
                )
                stats[model]["villager_win_rate"] = (
                    stats[model]["villager_wins"] / stats[model]["villager_games"]
                    if stats[model]["villager_games"] > 0
                    else 0
                )
                stats[model]["doctor_win_rate"] = (
                    stats[model]["doctor_wins"] / stats[model]["doctor_games"]
                    if stats[model]["doctor_games"] > 0
                    else 0
                )

            return stats
        except Exception as e:
            print(f"Error getting model stats: {e}")
            return {}

    def get_game_log(self, game_id):
        """
        Get the log of a specific game from Firebase.

        Args:
            game_id (str): Unique identifier for the game.

        Returns:
            dict: Game log data including rounds and participant information.
        """
        if not self.initialized:
            print("Firebase not initialized. Cannot get game log.")
            return None

        try:
            log_doc = self.db.collection("game_logs").document(game_id).get()

            if not log_doc.exists:
                print(f"Game log not found for game ID: {game_id}")
                return None

            log_data = log_doc.to_dict()

            result_doc = self.db.collection("mafia_games").document(game_id).get()

            if result_doc.exists:
                result_data = result_doc.to_dict()
                log_data["participants"] = result_data.get("participants", {})
                log_data["winner"] = result_data.get("winner", "Unknown")

            return log_data
        except Exception as e:
            print(f"Error getting game log: {e}")
            return None

    def clear_all_data(self, confirm=False):
        """
        Clear all game data from Firebase collections.
        
        Args:
            confirm (bool): Must be True to actually delete data (safety check)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.initialized:
            print("Firebase not initialized. Cannot clear data.")
            return False
            
        if not confirm:
            print("WARNING: This will delete ALL game data from Firebase!")
            print("To confirm, call this method with confirm=True")
            return False
            
        try:
            print("Clearing all data from Firebase...")
            
            # Delete all documents from mafia_games collection
            games_ref = self.db.collection("mafia_games")
            games_docs = games_ref.stream()
            games_count = 0
            
            for doc in games_docs:
                doc.reference.delete()
                games_count += 1
                
            print(f"Deleted {games_count} game results")
            
            # Delete all documents from game_logs collection
            logs_ref = self.db.collection("game_logs")
            logs_docs = logs_ref.stream()
            logs_count = 0
            
            for doc in logs_docs:
                doc.reference.delete()
                logs_count += 1
                
            print(f"Deleted {logs_count} game logs")
            print(f"Total deleted: {games_count + logs_count} documents")
            print("Firebase data cleared successfully!")
            
            return True
            
        except Exception as e:
            print(f"Error clearing Firebase data: {e}")
            return False

    def get_data_summary(self):
        """
        Get a summary of data in Firebase collections.
        
        Returns:
            dict: Summary of data counts
        """
        if not self.initialized:
            print("Firebase not initialized. Cannot get data summary.")
            return {}
            
        try:
            # Count documents in mafia_games collection
            games_ref = self.db.collection("mafia_games")
            games_docs = list(games_ref.stream())
            games_count = len(games_docs)
            
            # Count documents in game_logs collection
            logs_ref = self.db.collection("game_logs")
            logs_docs = list(logs_ref.stream())
            logs_count = len(logs_docs)
            
            summary = {
                "mafia_games": games_count,
                "game_logs": logs_count,
                "total_documents": games_count + logs_count
            }
            
            print(f"Firebase Data Summary:")
            print(f"  Game Results: {games_count}")
            print(f"  Game Logs: {logs_count}")
            print(f"  Total Documents: {games_count + logs_count}")
            
            return summary
            
        except Exception as e:
            print(f"Error getting data summary: {e}")
            return {}
