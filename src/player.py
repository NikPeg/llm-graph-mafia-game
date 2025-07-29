"""
Player class for the LLM Mafia Game Competition.
"""

import re
import config
from openrouter import get_llm_response
from game_templates import (
    Role,
    GAME_RULES,
    PROMPT_TEMPLATES,
    THINKING_TAGS,
    ACTION_PATTERNS,
    VOTE_PATTERNS,
)
from parsing import sanitize_model_response


class Player:
    """Represents an LLM player in the Mafia game."""

    def __init__(self, model_name, player_name, role, language=None):
        """
        Initialize a player.

        Args:
            model_name (str): The name of the LLM model to use for this player (hidden from other players).
            player_name (str): The visible name of the player in the game.
            role (Role): The role of the player in the game.
            language (str, optional): The language for the player. Defaults to English.
        """
        self.model_name = model_name
        self.player_name = player_name
        self.role = role
        self.alive = True
        self.protected = False
        self.language = language if language else "English"

    def __str__(self):
        """Return a string representation of the player."""
        return f"{self.player_name} ({self.role.value}) [Model: {self.model_name}]"

    def _find_target_player(self, target_name, all_players, exclude_mafia=False):
        """
        Find a target player by name.

        Args:
            target_name (str): The name of the target player.
            all_players (list): List of all players in the game.
            exclude_mafia (bool, optional): Whether to exclude Mafia members from targets.

        Returns:
            Player or None: The target player if found, None otherwise.
        """
        for player in all_players:
            if not player.alive:
                continue

            if exclude_mafia and player.role == Role.MAFIA:
                continue

            if target_name.lower() in player.player_name.lower():
                return player

        return None

    def generate_prompt(
        self, game_state, all_players, mafia_members=None, discussion_history=None
    ):
        """
        Generate a prompt for the player based on their role.

        Args:
            game_state (dict): The current state of the game.
            all_players (list): List of all players in the game.
            mafia_members (list, optional): List of mafia members (only for Mafia role).
            discussion_history (str, optional): History of previous discussions.
                Note: This should only contain day phase messages, night messages are filtered out.

        Returns:
            str: The prompt for the player.
        """
        if discussion_history is None:
            discussion_history = ""

        player_names = [p.player_name for p in all_players if p.alive]

        player_info = [{"name": p.player_name, "alive": p.alive} for p in all_players]

        language = self.language if self.language in GAME_RULES else "English"

        game_rules = GAME_RULES[language]

        if self.role == Role.MAFIA:
            mafia_names = [
                p.player_name for p in mafia_members if p != self and p.alive
            ]
            mafia_list = f"{', '.join(mafia_names) if mafia_names else 'None (you are the only Mafia left)'}"
            if language == "Spanish":
                mafia_list = f"{', '.join(mafia_names) if mafia_names else 'Ninguno (eres el único miembro de la Mafia que queda)'}"
            elif language == "French":
                mafia_list = f"{', '.join(mafia_names) if mafia_names else 'Aucun (vous êtes le seul membre de la Mafia restant)'}"
            elif language == "Korean":
                mafia_list = f"{', '.join(mafia_names) if mafia_names else '없음 (당신이 유일하게 남은 마피아입니다)'}"

            prompt = PROMPT_TEMPLATES[language][Role.MAFIA].format(
                model_name=self.player_name,
                game_rules=game_rules,
                mafia_members=mafia_list,
                player_names=", ".join(player_names),
                game_state=game_state,
                thinking_tag=THINKING_TAGS[language],
                discussion_history=discussion_history,
            )
        elif self.role == Role.DOCTOR:
            prompt = PROMPT_TEMPLATES[language][Role.DOCTOR].format(
                model_name=self.player_name,
                game_rules=game_rules,
                player_names=", ".join(player_names),
                game_state=game_state,
                thinking_tag=THINKING_TAGS[language],
                discussion_history=discussion_history,
            )
        else:
            prompt = PROMPT_TEMPLATES[language][Role.VILLAGER].format(
                model_name=self.player_name,
                game_rules=game_rules,
                player_names=", ".join(player_names),
                game_state=game_state,
                thinking_tag=THINKING_TAGS[language],
                discussion_history=discussion_history,
            )

        return prompt

    def get_response(self, prompt):
        """
        Get a response from the LLM model using OpenRouter API.

        Args:
            prompt (str): The prompt to send to the model.

        Returns:
            str: The response from the model with private thoughts removed.
        """
        # Get the appropriate API URL for this player's role
        _, api_url = config.get_model_for_role(self.role.value)
        
        response = get_llm_response(self.model_name, prompt, api_url)

        cleaned_response = re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL)

        cleaned_response = re.sub(r"\n\s*\n", "\n\n", cleaned_response)
        cleaned_response = cleaned_response.strip()

        return cleaned_response

    def parse_night_action(self, response, all_players):
        """
        Parse the night action from the player's response.

        Args:
            response (str): The response from the player (already cleaned of thinking tags).
            all_players (list): List of all players in the game.

        Returns:
            tuple: (action_type, target_player) or (None, None) if no valid action.
        """
        if self.role == Role.MAFIA:
            pattern = r"ACTION:\s*Kill\s+([A-Za-z][A-Za-z\s'-]*)"
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                target_name = match.group(1).strip().rstrip(".:,; \t")
                for p in all_players:
                    if (
                        p.player_name.lower() == target_name.lower()
                        and p.alive
                        and p.role != Role.MAFIA
                        and p.player_name != self.player_name
                    ):
                        return "kill", p
            return None, None

        elif self.role == Role.DOCTOR:
            pattern = ACTION_PATTERNS.get(self.language, ACTION_PATTERNS["English"])[
                Role.DOCTOR
            ]
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                target_name = match.group(1).strip()
                target_name = target_name.rstrip(".:,; \t")
                for p in all_players:
                    if p.player_name.lower() == target_name.lower() and p.alive:
                        return "protect", p
            return None, None

        else:
            return None, None

    def parse_day_vote(self, response, all_players):
        """
        Parse the day vote from the player's response.

        Args:
            response (str): The response from the player (already cleaned of thinking tags).
            all_players (list): List of all players in the game.

        Returns:
            Player or None: The player being voted for (по player_name), или None если голос невалиден/нет голоса.
            Возвращает специальный объект с player_name="None" если игрок голосует VOTE: None.
        """

        pattern = VOTE_PATTERNS.get(self.language, VOTE_PATTERNS["English"])
        
        # Найдем все совпадения голосов в сообщении
        matches = re.findall(pattern, response, re.IGNORECASE)
        
        if matches:
            # Берем последний голос (самый актуальный)
            target_name_raw = matches[-1].strip().rstrip(".:,;!? \t")
            
            # Удаляем обработку "None" - теперь это будет считаться как отсутствие голоса
            # и система автоматически добавит случайный голос

            # Попробуем найти точное совпадение
            for p in all_players:
                if (
                    p.player_name.lower() == target_name_raw.lower()
                    and p.player_name != self.player_name
                    and p.alive
                ):
                    return p
            
            # Если точного совпадения нет, попробуем частичное совпадение
            for p in all_players:
                if (
                    target_name_raw.lower() in p.player_name.lower()
                    and p.player_name != self.player_name
                    and p.alive
                ):
                    return p

        return None

