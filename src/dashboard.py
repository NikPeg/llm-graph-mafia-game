"""
Dashboard for the LLM Mafia Game Competition.
"""

import io
import base64
import json
import time
import datetime
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from flask import Flask, render_template, request, jsonify, Response, make_response
from firebase_manager import FirebaseManager
from flask_caching import Cache

app = Flask(__name__, static_folder="static", template_folder="templates")
firebase = FirebaseManager()

cache_config = {
    "CACHE_TYPE": "SimpleCache",
    "CACHE_DEFAULT_TIMEOUT": 30,
}
cache = Cache(app, config=cache_config)


@app.template_filter("strftime")
def _jinja2_filter_strftime(timestamp):
    """Convert a Unix timestamp to a formatted datetime string."""
    try:
        dt = datetime.datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return "Invalid timestamp"


@dataclass
class ModelStats:
    games_played: int
    games_won: int
    win_rate: float
    mafia_games: int
    mafia_wins: int
    mafia_win_rate: float
    villager_games: int
    villager_wins: int
    villager_win_rate: float
    doctor_games: int
    doctor_wins: int
    doctor_win_rate: float
    avg_rounds_per_game: float = 0.0
    survival_rate: float = 0.0
    elimination_rate: float = 0.0
    survival_count: int = 0
    elimination_count: int = 0
    total_rounds: int = 0


@dataclass
class GameResult:
    game_id: str
    timestamp: int
    game_type: str
    participant_count: int
    winner: str
    participants: Dict[str, str]


@dataclass
class ChartResponse:
    chart_url: str


@dataclass
class ErrorResponse:
    error: str


@app.route("/")
def index():
    """Render the main dashboard page."""
    return render_template("index.html")


@app.route("/game/<game_id>")
def game_detail(game_id):
    """Render the game detail page."""

    game_data = firebase.get_game_log(game_id)

    if not game_data:
        return render_template("404.html", message="Game not found"), 404

    return render_template("game_detail.html", game_id=game_id, game_data=game_data)


@app.route("/api/stats")
def get_stats():
    """Get statistics from Firebase."""
    stats = get_cached_model_stats()

    response = make_response(jsonify(stats))
    response.headers["Content-Type"] = "application/json"
    response.headers["Cache-Control"] = "max-age=60"

    return response


@cache.cached(timeout=30, key_prefix="model_stats")
def get_cached_model_stats():
    """Get cached model statistics from Firebase."""
    return firebase.get_model_stats()


@app.route("/api/games")
def get_games():
    """Get game results from Firebase."""
    try:
        limit = request.args.get("limit", default=100, type=int)
        if limit < 1 or limit > 1000:
            return make_response(
                jsonify({"error": "Limit must be between 1 and 1000"}), 400
            )

        games = get_cached_game_results(limit)

        for game in games:
            if "timestamp" in game and isinstance(game["timestamp"], int):
                if game["timestamp"] > 10000000000:
                    game["timestamp"] = game["timestamp"] // 1000

        response = make_response(jsonify(games))
        response.headers["Content-Type"] = "application/json"
        response.headers["Cache-Control"] = "max-age=10"

        return response
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)


@cache.memoize(timeout=30)
def get_cached_game_results(limit):
    """Get cached game results from Firebase.

    Args:
        limit (int): Maximum number of results to retrieve.

    Returns:
        list: List of game results.
    """
    return firebase.get_game_results(limit=limit)


@app.route("/api/game/<game_id>")
def get_game(game_id):
    """Get game data from Firebase."""
    game_data = get_cached_game_log(game_id)

    if not game_data:
        return jsonify({"error": "Game not found"}), 404

    response = make_response(jsonify(game_data))
    response.headers["Content-Type"] = "application/json"
    response.headers["Cache-Control"] = "max-age=120"

    return response


@cache.memoize(timeout=120)
def get_cached_game_log(game_id):
    """Get cached game log data from Firebase.

    Args:
        game_id (str): The ID of the game to retrieve.

    Returns:
        dict: Game log data or None if not found.
    """
    return firebase.get_game_log(game_id)


@app.route("/api/chart/win_rates")
def get_win_rate_chart():
    """Generate a win rate chart."""
    try:
        stats = get_cached_model_stats()

        if not stats:
            return make_response(jsonify({"error": "No data available"}), 404)

        sorted_models = sorted(
            stats.items(), key=lambda x: x[1]["win_rate"], reverse=True
        )

        models = [model for model, _ in sorted_models]
        win_rates = [stats[model]["win_rate"] * 100 for model in models]
        mafia_win_rates = [stats[model]["mafia_win_rate"] * 100 for model in models]
        villager_win_rates = [
            stats[model]["villager_win_rate"] * 100 for model in models
        ]
        doctor_win_rates = [stats[model]["doctor_win_rate"] * 100 for model in models]

        fig, ax = plt.subplots(figsize=(12, 8))
        fig.set_facecolor("white")
        ax.set_facecolor("white")

        bar_width = 0.2

        r1 = np.arange(len(models))
        r2 = [x + bar_width for x in r1]
        r3 = [x + bar_width for x in r2]
        r4 = [x + bar_width for x in r3]

        ax.bar(r1, win_rates, width=bar_width, label="Overall", color="blue")
        ax.bar(r2, mafia_win_rates, width=bar_width, label="Mafia", color="red")
        ax.bar(r3, villager_win_rates, width=bar_width, label="Villager", color="green")
        ax.bar(r4, doctor_win_rates, width=bar_width, label="Doctor", color="purple")

        ax.set_xlabel("Models", fontsize=12, fontweight="bold")
        ax.set_ylabel("Win Rate (%)", fontsize=12, fontweight="bold")
        ax.set_title("Win Rates by Model and Role", fontsize=14, fontweight="bold")

        ax.spines["top"].set_visible(True)
        ax.spines["right"].set_visible(True)
        ax.spines["bottom"].set_visible(True)
        ax.spines["left"].set_visible(True)

        ax.tick_params(axis="both", which="major", labelsize=10, width=1, length=5)
        ax.tick_params(axis="both", which="minor", width=1, length=3)

        ax.set_xticks([r + bar_width * 1.5 for r in range(len(models))])
        ax.set_xticklabels(
            [model.split("/")[-1] for model in models], rotation=45, ha="right"
        )

        ax.grid(axis="y", linestyle="--", alpha=0.7)

        ax.legend(fontsize=10)

        plt.tight_layout()

        img = io.BytesIO()
        plt.savefig(img, format="png", dpi=120, bbox_inches="tight", pad_inches=0.2)
        img.seek(0)

        chart_url = base64.b64encode(img.getvalue()).decode()

        plt.close(fig)

        response = make_response(jsonify({"chart_url": chart_url}))
        response.headers["Content-Type"] = "application/json"
        response.headers["Cache-Control"] = "max-age=300"

        return response
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)


@app.route("/api/chart/games_played")
def get_games_played_chart():
    """Generate a games played chart."""
    try:
        stats = get_cached_model_stats()

        if not stats:
            return make_response(jsonify({"error": "No data available"}), 404)

        sorted_models = sorted(
            stats.items(), key=lambda x: x[1]["games_played"], reverse=True
        )

        models = [model for model, _ in sorted_models]
        games_played = [stats[model]["games_played"] for model in models]
        mafia_games = [stats[model]["mafia_games"] for model in models]
        villager_games = [stats[model]["villager_games"] for model in models]
        doctor_games = [stats[model]["doctor_games"] for model in models]

        fig, ax = plt.subplots(figsize=(12, 8))
        fig.set_facecolor("white")
        ax.set_facecolor("white")

        ax.bar(models, mafia_games, label="Mafia", color="red")
        ax.bar(
            models, villager_games, bottom=mafia_games, label="Villager", color="green"
        )
        ax.bar(
            models,
            doctor_games,
            bottom=[mafia_games[i] + villager_games[i] for i in range(len(models))],
            label="Doctor",
            color="purple",
        )

        ax.set_xlabel("Models", fontsize=12, fontweight="bold")
        ax.set_ylabel("Games Played", fontsize=12, fontweight="bold")
        ax.set_title("Games Played by Model and Role", fontsize=14, fontweight="bold")

        ax.spines["top"].set_visible(True)
        ax.spines["right"].set_visible(True)
        ax.spines["bottom"].set_visible(True)
        ax.spines["left"].set_visible(True)

        ax.tick_params(axis="both", which="major", labelsize=10, width=1, length=5)
        ax.tick_params(axis="both", which="minor", width=1, length=3)

        ax.set_xticks([model for model in models])
        ax.set_xticklabels(
            [model.split("/")[-1] for model in models], rotation=45, ha="right"
        )

        ax.grid(axis="y", linestyle="--", alpha=0.7)

        ax.legend(fontsize=10)

        plt.tight_layout()

        img = io.BytesIO()
        plt.savefig(img, format="png", dpi=120, bbox_inches="tight", pad_inches=0.2)
        img.seek(0)

        chart_url = base64.b64encode(img.getvalue()).decode()

        plt.close(fig)

        response = make_response(jsonify({"chart_url": chart_url}))
        response.headers["Content-Type"] = "application/json"
        response.headers["Cache-Control"] = "max-age=300"

        return response
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)


@app.route("/api/chart/win_rates/image")
def get_win_rate_image():
    """Generate a win rate chart and return it directly as an image."""
    try:
        stats = get_cached_model_stats()

        if not stats:
            return make_response("No data available", 404)

        sorted_models = sorted(
            stats.items(), key=lambda x: x[1]["win_rate"], reverse=True
        )

        models = [model for model, _ in sorted_models]
        win_rates = [stats[model]["win_rate"] * 100 for model in models]
        mafia_win_rates = [stats[model]["mafia_win_rate"] * 100 for model in models]
        villager_win_rates = [
            stats[model]["villager_win_rate"] * 100 for model in models
        ]
        doctor_win_rates = [stats[model]["doctor_win_rate"] * 100 for model in models]

        fig, ax = plt.subplots(figsize=(12, 8))
        fig.set_facecolor("white")
        ax.set_facecolor("white")

        bar_width = 0.2

        r1 = np.arange(len(models))
        r2 = [x + bar_width for x in r1]
        r3 = [x + bar_width for x in r2]
        r4 = [x + bar_width for x in r3]

        ax.bar(r1, win_rates, width=bar_width, label="Overall", color="blue")
        ax.bar(r2, mafia_win_rates, width=bar_width, label="Mafia", color="red")
        ax.bar(r3, villager_win_rates, width=bar_width, label="Villager", color="green")
        ax.bar(r4, doctor_win_rates, width=bar_width, label="Doctor", color="purple")

        ax.set_xlabel("Models", fontsize=12, fontweight="bold")
        ax.set_ylabel("Win Rate (%)", fontsize=12, fontweight="bold")
        ax.set_title("Win Rates by Model and Role", fontsize=14, fontweight="bold")

        ax.spines["top"].set_visible(True)
        ax.spines["right"].set_visible(True)
        ax.spines["bottom"].set_visible(True)
        ax.spines["left"].set_visible(True)

        ax.tick_params(axis="both", which="major", labelsize=10, width=1, length=5)
        ax.tick_params(axis="both", which="minor", width=1, length=3)

        ax.set_xticks([r + bar_width * 1.5 for r in range(len(models))])
        ax.set_xticklabels(
            [model.split("/")[-1] for model in models], rotation=45, ha="right"
        )

        ax.grid(axis="y", linestyle="--", alpha=0.7)

        ax.legend(fontsize=10)

        plt.tight_layout()

        img = io.BytesIO()
        plt.savefig(img, format="png", dpi=120, bbox_inches="tight", pad_inches=0.2)
        img.seek(0)

        plt.close(fig)

        response = make_response(img.getvalue())
        response.headers["Content-Type"] = "image/png"
        response.headers["Cache-Control"] = "max-age=300"

        return response
    except Exception as e:
        return make_response(str(e), 500)


@app.route("/api/chart/games_played/image")
def get_games_played_image():
    """Generate a games played chart and return it directly as an image."""
    try:
        stats = get_cached_model_stats()

        if not stats:
            return make_response("No data available", 404)

        sorted_models = sorted(
            stats.items(), key=lambda x: x[1]["games_played"], reverse=True
        )

        models = [model for model, _ in sorted_models]
        games_played = [stats[model]["games_played"] for model in models]
        mafia_games = [stats[model]["mafia_games"] for model in models]
        villager_games = [stats[model]["villager_games"] for model in models]
        doctor_games = [stats[model]["doctor_games"] for model in models]

        fig, ax = plt.subplots(figsize=(12, 8))
        fig.set_facecolor("white")
        ax.set_facecolor("white")

        ax.bar(models, mafia_games, label="Mafia", color="red")
        ax.bar(
            models, villager_games, bottom=mafia_games, label="Villager", color="green"
        )
        ax.bar(
            models,
            doctor_games,
            bottom=[mafia_games[i] + villager_games[i] for i in range(len(models))],
            label="Doctor",
            color="purple",
        )

        ax.set_xlabel("Models", fontsize=12, fontweight="bold")
        ax.set_ylabel("Games Played", fontsize=12, fontweight="bold")
        ax.set_title("Games Played by Model and Role", fontsize=14, fontweight="bold")

        ax.spines["top"].set_visible(True)
        ax.spines["right"].set_visible(True)
        ax.spines["bottom"].set_visible(True)
        ax.spines["left"].set_visible(True)

        ax.tick_params(axis="both", which="major", labelsize=10, width=1, length=5)
        ax.tick_params(axis="both", which="minor", width=1, length=3)

        ax.set_xticks([model for model in models])
        ax.set_xticklabels(
            [model.split("/")[-1] for model in models], rotation=45, ha="right"
        )

        ax.grid(axis="y", linestyle="--", alpha=0.7)

        ax.legend(fontsize=10)

        plt.tight_layout()

        img = io.BytesIO()
        plt.savefig(img, format="png", dpi=120, bbox_inches="tight", pad_inches=0.2)
        img.seek(0)

        plt.close(fig)

        response = make_response(img.getvalue())
        response.headers["Content-Type"] = "image/png"
        response.headers["Cache-Control"] = "max-age=300"

        return response
    except Exception as e:
        return make_response(str(e), 500)


@app.route("/api/chart/survival_rates")
def get_survival_rate_chart():
    """Generate a survival rate chart."""
    try:
        stats = get_cached_model_stats()

        if not stats:
            return make_response(jsonify({"error": "No data available"}), 404)

        # Фильтруем модели, у которых есть данные о выживаемости
        models_with_survival = {k: v for k, v in stats.items() if v.get("survival_rate", 0) > 0 or v.get("games_played", 0) > 0}
        
        if not models_with_survival:
            return make_response(jsonify({"error": "No survival data available"}), 404)

        sorted_models = sorted(
            models_with_survival.items(), key=lambda x: x[1].get("survival_rate", 0), reverse=True
        )

        models = [model for model, _ in sorted_models]
        survival_rates = [stats[model].get("survival_rate", 0) * 100 for model in models]
        avg_rounds = [stats[model].get("avg_rounds_per_game", 0) for model in models]

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        fig.set_facecolor("white")

        # Survival rates chart
        ax1.bar(models, survival_rates, color="green", alpha=0.7)
        ax1.set_xlabel("Models", fontsize=12, fontweight="bold")
        ax1.set_ylabel("Survival Rate (%)", fontsize=12, fontweight="bold")
        ax1.set_title("Survival Rates by Model", fontsize=14, fontweight="bold")
        ax1.set_xticklabels([model.split("/")[-1] for model in models], rotation=45, ha="right")
        ax1.grid(axis="y", linestyle="--", alpha=0.7)

        # Average rounds chart
        ax2.bar(models, avg_rounds, color="blue", alpha=0.7)
        ax2.set_xlabel("Models", fontsize=12, fontweight="bold")
        ax2.set_ylabel("Average Rounds per Game", fontsize=12, fontweight="bold")
        ax2.set_title("Average Game Length by Model", fontsize=14, fontweight="bold")
        ax2.set_xticklabels([model.split("/")[-1] for model in models], rotation=45, ha="right")
        ax2.grid(axis="y", linestyle="--", alpha=0.7)

        plt.tight_layout()

        img = io.BytesIO()
        plt.savefig(img, format="png", dpi=120, bbox_inches="tight", pad_inches=0.2)
        img.seek(0)

        chart_url = base64.b64encode(img.getvalue()).decode()

        plt.close(fig)

        response = make_response(jsonify({"chart_url": chart_url}))
        response.headers["Content-Type"] = "application/json"
        response.headers["Cache-Control"] = "max-age=300"

        return response
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)


@app.route("/api/extended_stats")
def get_extended_stats():
    """Get extended statistics including new metrics."""
    try:
        stats = get_cached_model_stats()
        
        # Добавляем безопасные значения по умолчанию для старых игр
        for model_name, model_stats in stats.items():
            model_stats.setdefault("avg_rounds_per_game", 0.0)
            model_stats.setdefault("survival_rate", 0.0)
            model_stats.setdefault("elimination_rate", 0.0)
            model_stats.setdefault("survival_count", 0)
            model_stats.setdefault("elimination_count", 0)
            model_stats.setdefault("total_rounds", 0)

        response = make_response(jsonify(stats))
        response.headers["Content-Type"] = "application/json"
        response.headers["Cache-Control"] = "max-age=60"

        return response
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)


if __name__ == "__main__":
    try:
        import argparse

        parser = argparse.ArgumentParser(description="LLM Mafia Dashboard")
        parser.add_argument(
            "--port", type=int, default=5000, help="Port to run the server on"
        )
        args = parser.parse_args()

        print(f"Starting the dashboard application on port {args.port}...")
        app.run(debug=True, host="0.0.0.0", port=args.port)
    except Exception as e:
        print(f"Error starting application: {e}")
