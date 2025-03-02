"""
Firebase manager for the LLM Mafia Game Competition.
"""

import json
import time
import firebase_admin
from firebase_admin import credentials, db
import config


class FirebaseManager:
    """Manages Firebase database operations for the Mafia game."""

    def __init__(self):
        """Initialize the Firebase manager."""
        try:
            # Initialize Firebase app
            cred = credentials.Certificate(config.FIREBASE_CREDENTIALS_PATH)
            firebase_admin.initialize_app(
                cred, {"databaseURL": config.FIREBASE_DATABASE_URL}
            )
            self.db = db
            self.initialized = True
            print("Firebase initialized successfully.")
        except Exception as e:
            print(f"Error initializing Firebase: {e}")
            self.initialized = False

    def store_game_result(
        self, game_id, winner, participants, game_type=config.GAME_TYPE
    ):
        """
        Store the result of a game in Firebase.

        Args:
            game_id (str): Unique identifier for the game.
            winner (str): The winning team ("Mafia" or "Villagers").
            participants (dict): Dictionary mapping model names to roles.
            game_type (str, optional): Type of Mafia game played.

        Returns:
            bool: True if successful, False otherwise.
        """
        if not self.initialized:
            print("Firebase not initialized. Cannot store game result.")
            return False

        try:
            # Create game result data
            game_data = {
                "game_id": game_id,
                "timestamp": int(time.time()),
                "game_type": game_type,
                "participant_count": len(participants),
                "winner": winner,
                "participants": participants,
            }

            # Store in Firebase
            ref = self.db.reference("mafia_games")
            ref.child(game_id).set(game_data)
            return True
        except Exception as e:
            print(f"Error storing game result: {e}")
            return False

    def store_game_log(self, game_id, rounds, participants, game_type=config.GAME_TYPE):
        """
        Store the log of a game in Firebase.

        Args:
            game_id (str): Unique identifier for the game.
            rounds (list): List of round data.
            participants (dict): Dictionary mapping model names to roles.
            game_type (str, optional): Type of Mafia game played.

        Returns:
            bool: True if successful, False otherwise.
        """
        if not self.initialized:
            print("Firebase not initialized. Cannot store game log.")
            return False

        try:
            # Create game log data
            log_data = {
                "game_id": game_id,
                "timestamp": int(time.time()),
                "game_type": game_type,
                "participant_count": len(participants),
                "rounds": rounds,
            }

            # Store in Firebase
            ref = self.db.reference("game_logs")
            ref.child(game_id).set(log_data)
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
            ref = self.db.reference("mafia_games")
            results = ref.order_by_child("timestamp").limit_to_last(limit).get()

            # Convert to list
            if results:
                return list(results.values())
            return []
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
            # Get all game results
            results = self.get_game_results(limit=1000)

            # Initialize stats
            stats = {}

            # Process each game
            for game in results:
                winner = game.get("winner")
                participants = game.get("participants", {})

                for model, role in participants.items():
                    # Initialize model stats if not exists
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
                        }

                    # Update games played
                    stats[model]["games_played"] += 1

                    # Update role-specific stats
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

            # Calculate win rates
            for model in stats:
                stats[model]["win_rate"] = (
                    stats[model]["games_won"] / stats[model]["games_played"]
                    if stats[model]["games_played"] > 0
                    else 0
                )
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
