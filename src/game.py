"""
Game logic for the LLM Mafia Game Competition.
"""

import random
import uuid
from player import Player
from game_templates import Role
import config
from logger import GameLogger, Color
import re
import json
from openrouter import get_llm_response
from parsing import sanitize_model_response
from rag_providers import RAGManager


class MafiaGame:
    """Represents a Mafia game with LLM players."""

    def __init__(self, models=None, language=None):
        """
        Initialize a Mafia game.

        Args:
            models (list, optional): List of model names to use as players.
            language (str, optional): Language for game prompts and interactions. Defaults to config.LANGUAGE.
        """
        self.game_id = str(uuid.uuid4())
        self.round_number = 0
        self.phase = "setup"
        self.players: list[Player] = []
        self.mafia_players: list[Player] = []
        self.doctor_player: Player | None = None
        self.villager_players: list[Player] = []
        self.discussion_history = ""
        self.rounds_data = []
        self.language = language if language is not None else config.LANGUAGE
        self.current_round_data = {
            "round_number": 0,
            "messages": [],
            "actions": {},
            "eliminations": [],
            "eliminated_by_vote": [],
            "targeted_by_mafia": [],
            "protected_by_doctor": [],
            "outcome": "",
        }

        self.models = models if models else [config.DEFAULT_MODEL]

        if config.RANDOM_SEED is not None:
            random.seed(config.RANDOM_SEED)

        self.logger = GameLogger(game_id=self.game_id)
        self.rag_manager = RAGManager()

    def setup_game(self, game_number=1):
        """
        Set up the game by assigning roles to players.

        Returns:
            bool: True if setup successful, False otherwise.
        """

        self.logger.game_start(game_number, self.game_id, self.language)

        # In role-specific mode, we don't need to pre-select models since they're determined by role
        # Keep this for compatibility but it won't be used in role-specific mode
        selected_models = random.choices(self.models, k=config.PLAYERS_PER_GAME)

        roles = []

        for _ in range(config.MAFIA_COUNT):
            roles.append(Role.MAFIA)

        for _ in range(config.DOCTOR_COUNT):
            roles.append(Role.DOCTOR)

        villager_count = (
            config.PLAYERS_PER_GAME - config.MAFIA_COUNT - config.DOCTOR_COUNT
        )
        for _ in range(villager_count):
            roles.append(Role.VILLAGER)

        random.shuffle(roles)

        self.logger.header("PLAYER SETUP", Color.CYAN)
        for i, _ in enumerate(selected_models):
            used_names = [p.player_name for p in self.players]
            available_names = [name for name in player_names if name not in used_names]

            if not available_names:
                player_name = f"Player_{i + 1}"
            else:
                player_name = random.choice(available_names)

            # Get the appropriate model for this role
            role_name = roles[i].value
            model_name = config.get_model_for_role(role_name)

            player = Player(model_name, player_name, roles[i], language=self.language)
            self.players.append(player)

            if player.role == Role.MAFIA:
                self.mafia_players.append(player)
            elif player.role == Role.DOCTOR:
                self.doctor_player = player
            else:
                self.villager_players.append(player)

            # Определяем RAG информацию для игрока
            rag_info = ""
            if config.RAG_ENABLED:
                provider = self.rag_manager.providers.get(config.RAG_TYPE)
                if provider and provider.is_applicable_for_player(player.role.value, config.RAG_TARGET):
                    rag_short_name = self.rag_manager.get_short_name(config.RAG_TYPE)
                    rag_info = f" (RAG: {rag_short_name})"
            
            self.logger.player_setup(
                player.model_name, player.role.value, player.player_name, rag_info
            )

        self.phase = "night"
        self.round_number = 1
        self.current_round_data = {
            "round_number": self.round_number,
            "messages": [],
            "actions": {},
            "eliminations": [],
            "eliminated_by_vote": [],
            "targeted_by_mafia": [],
            "protected_by_doctor": [],
            "outcome": "",
        }

        return True

    def get_game_state(self):
        """
        Get the current state of the game as a string.

        Returns:
            str: The current game state.
        """
        alive_count = sum(1 for p in self.players if p.alive)
        mafia_count = sum(1 for p in self.mafia_players if p.alive)
        villager_count = sum(1 for p in self.villager_players if p.alive)
        doctor_count = 1 if self.doctor_player and self.doctor_player.alive else 0

        state = f"Round {self.round_number}, {self.phase.capitalize()} phase. "
        state += f"{alive_count} players alive ({mafia_count} Mafia, {villager_count + doctor_count} Villagers/Doctor). "

        if self.round_number > 1:
            state += f"In the previous round, {', '.join(self.current_round_data['eliminations'])} {'was' if len(self.current_round_data['eliminations']) == 1 else 'were'} eliminated. "

        return state

    def get_alive_players(self):
        """
        Get a list of alive players.

        Returns:
            list: List of alive players.
        """
        return [p for p in self.players if p.alive]

    def check_game_over(self):
        """
        Check if the game is over.

        Returns:
            tuple: (is_game_over, winner) where winner is "Mafia" or "Villagers" or None.
        """

        mafia_alive = sum(1 for p in self.mafia_players if p.alive)
        villagers_alive = sum(1 for p in self.villager_players if p.alive)
        doctor_alive = 1 if self.doctor_player and self.doctor_player.alive else 0

        if mafia_alive == 0:
            return True, "Villagers"
        elif mafia_alive >= (villagers_alive + doctor_alive):
            return True, "Mafia"
        elif self.round_number >= config.MAX_ROUNDS:
            if villagers_alive + doctor_alive > mafia_alive:
                return True, "Villagers"
            else:
                return True, "Mafia"

        return False, None

    def discussion_history_without_thinkings(self):
        """
        Get the limited discussion history for the current round, excluding thinking messages.
        Removes any <think></think> or <THINK></THINK> tags and their contents.
        Shows only the N (config.DISCUSSION_HISTORY_LIMIT) latest messages.
        """

        discussion_history = re.sub(
            r"&lt;[tT][hH][iI][nN][kK]&gt;.*?&lt;/[tT][hH][iI][nN][kK]&gt;",
            "",
            self.discussion_history,
            flags=re.DOTALL,
        )
        discussion_history = re.sub(
            r"&lt;[tT][hH][iI][nN][kK]&gt;.*$",
            "",
            discussion_history,
            flags=re.DOTALL,
        )

        entries = [
            entry for entry in discussion_history.strip().split("\n\n") if entry.strip()
        ]
        limit = config.DISCUSSION_HISTORY_LIMIT

        if len(entries) > limit:
            entries = entries[-limit:]

        return "\n\n".join(entries).strip()

    def discussion_graph_from_history(self):
        """
        Генерирует граф отношений между игроками на основе последних сообщений.
        Теперь использует новую RAG архитектуру для совместимости.
        """
        # Используем новую RAG архитектуру
        discussion_rag = self.rag_manager.providers["discussion_graph"]
        game_state = self.get_rag_game_state()
        context = discussion_rag.generate_context(game_state)
        
        # Извлекаем только граф без заголовка для обратной совместимости
        if context and "--- Discussion Relationship Graph ---" in context:
            lines = context.split("\n")
            graph_lines = []
            in_graph = False
            for line in lines:
                if "--- Discussion Relationship Graph ---" in line:
                    in_graph = True
                    continue
                elif line.strip() == "" and in_graph:
                    break
                elif in_graph:
                    graph_lines.append(line)
            return "\n".join(graph_lines).strip()
        
        return ""

    def get_rag_game_state(self):
        """
        Get game state information for RAG providers.
        
        Returns:
            dict: Game state data for RAG context generation
        """
        return {
            "discussion_history": self.discussion_history_without_thinkings(),
            "rounds_data": self.rounds_data,
            "current_round_data": self.current_round_data,
            "alive_players": self.get_alive_players(),
            "models": self.models,
            "round_number": self.round_number,
            "phase": self.phase
        }

    def execute_night_phase(self):
        """
        Execute the night phase of the game.

        Returns:
            list: List of eliminated players.
        """
        self.logger.phase_header("Night", self.round_number)

        for player in self.players:
            player.protected = False

        mafia_targets = []
        alive_players = self.get_alive_players()
        for player in self.mafia_players:
            if player.alive:
                game_state = f"{self.get_game_state()} It's night time (Round {self.round_number}). As the Mafia, you MUST choose exactly one player to kill tonight. You cannot skip this action. End your response with ACTION: Kill [player]."
                
                # Получаем RAG контекст для мафии
                rag_context = self.rag_manager.generate_rag_context(
                    self.get_rag_game_state(),
                    player.role.value
                )
                
                enhanced_discussion = self.discussion_history_without_thinkings()
                if rag_context:
                    enhanced_discussion = rag_context + enhanced_discussion
                    
                    # Логируем информацию о RAG
                    rag_short_name = self.rag_manager.get_short_name(config.RAG_TYPE)
                    self.logger.log(
                        f"[{player.player_name}] Playing with RAG: {rag_short_name}", Color.GREEN
                    )
                
                prompt = player.generate_prompt(
                    game_state,
                    alive_players,
                    self.mafia_players,
                    enhanced_discussion,
                )

                response = player.get_response(prompt)
                response = sanitize_model_response(
                    response,
                    player.player_name,
                    [p.player_name for p in alive_players],
                    "night",
                )

                self.logger.player_response(
                    player.player_name, "Mafia", response, player.player_name
                )

                self.current_round_data["messages"].append(
                    {
                        "speaker": player.player_name,
                        "content": response,
                        "phase": "night",
                        "role": "Mafia",
                        "player_name": player.player_name,
                    }
                )

                action_type, target = player.parse_night_action(response, alive_players)

                if (
                    action_type == "kill"
                    and target
                    and target.role != Role.MAFIA
                    and target.player_name != player.player_name
                ):
                    mafia_targets.append(target)
                    action_text = f"Kill {target.player_name}"
                    self.current_round_data["actions"][player.player_name] = action_text
                    self.logger.player_action(
                        player.player_name, "Mafia", action_text, player.player_name
                    )
                else:
                    self.logger.error(
                        f"Invalid action from {player.player_name} (Mafia)"
                    )
                    self.current_round_data["actions"][player.player_name] = (
                        "Invalid action"
                    )

        kill_target = None
        if mafia_targets:
            target_counts = {}
            for target in mafia_targets:
                if target.player_name in target_counts:
                    target_counts[target.player_name] += 1
                else:
                    target_counts[target.player_name] = 1

            max_votes = 0
            for target_name, votes in target_counts.items():
                if votes > max_votes:
                    max_votes = votes

                    for player in alive_players:
                        if player.player_name == target_name:
                            kill_target = player
                            break

        if kill_target:
            self.current_round_data["targeted_by_mafia"].append(kill_target.player_name)

        protected_player = None
        if self.doctor_player and self.doctor_player.alive:
            instruction = f"It's night time (Round {self.round_number}). As the Doctor, you MUST choose exactly one player to protect from the Mafia tonight. You cannot skip this action. End your response with ACTION: Protect [player]."
            game_state = f"{self.get_game_state()} {instruction}"
            
            # Получаем RAG контекст для доктора
            rag_context = self.rag_manager.generate_rag_context(
                self.get_rag_game_state(),
                self.doctor_player.role.value
            )
            
            enhanced_discussion = self.discussion_history_without_thinkings()
            if rag_context:
                enhanced_discussion = rag_context + enhanced_discussion
                
                # Логируем информацию о RAG
                rag_short_name = self.rag_manager.get_short_name(config.RAG_TYPE)
                self.logger.log(
                    f"[{self.doctor_player.player_name}] Playing with RAG: {rag_short_name}", Color.GREEN
                )
            
            prompt = self.doctor_player.generate_prompt(
                game_state,
                alive_players,
                None,
                enhanced_discussion,
            )

            response = self.doctor_player.get_response(prompt)
            response = sanitize_model_response(
                response,
                self.doctor_player.player_name,
                [p.player_name for p in alive_players],
                "night",
            )

            self.logger.player_response(
                self.doctor_player.player_name,
                "Doctor",
                response,
                self.doctor_player.player_name,
            )

            self.current_round_data["messages"].append(
                {
                    "speaker": self.doctor_player.player_name,
                    "content": response,
                    "phase": "night",
                    "role": "Doctor",
                    "player_name": self.doctor_player.player_name,
                }
            )

            action_type, target = self.doctor_player.parse_night_action(
                response, alive_players
            )

            if action_type == "protect" and target and target.alive:
                protected_player = target
                target.protected = True
                action_text = f"Protect {target.player_name}"
                self.current_round_data["actions"][self.doctor_player.player_name] = (
                    action_text
                )
                self.current_round_data["protected_by_doctor"].append(
                    target.player_name
                )
                self.logger.player_action(
                    self.doctor_player.player_name,
                    "Doctor",
                    action_text,
                    self.doctor_player.player_name,
                )
            else:
                self.logger.error(
                    f"Invalid action from {self.doctor_player.player_name} (Doctor)"
                )
                self.current_round_data["actions"][self.doctor_player.player_name] = (
                    "Invalid action"
                )

        eliminated_players = []
        if kill_target and not getattr(kill_target, "protected", False):
            kill_target.alive = False
            eliminated_players.append(kill_target)
            self.current_round_data["eliminations"].append(kill_target.player_name)
            outcome_text = f"{kill_target.player_name} was killed by the Mafia."
            self.current_round_data["outcome"] = outcome_text
            self.logger.event(outcome_text, Color.RED)
        else:
            if kill_target and getattr(kill_target, "protected", False):
                outcome_text = (
                    f"The Doctor protected {kill_target.player_name} from the Mafia."
                )
                self.current_round_data["outcome"] = outcome_text
                self.logger.event(outcome_text, Color.BLUE)
            else:
                outcome_text = "No one was killed during the night."
                self.current_round_data["outcome"] = outcome_text
                self.logger.event(outcome_text, Color.YELLOW)

        self.phase = "day"

        return eliminated_players

    def execute_day_phase(self):
        """
        Execute the day phase of the game.

        Returns:
            list: List of eliminated players.
        """
        self.logger.phase_header("Day", self.round_number)

        alive_players = self.get_alive_players()

        messages = []
        votes = {}

        self.logger.event("Discussion Round - Players share their thoughts", Color.CYAN)
        self._conduct_player_interactions(
            alive_players,
            "day_discussion",
            f"It's day time (Round {self.round_number}). Discuss with other players about who might be Mafia. This is the DISCUSSION PHASE ONLY - DO NOT VOTE YET. You will vote in the next round.",
            messages,
            collect_votes=False,
        )

        self.logger.event(
            "Voting Round - Players make their final arguments and vote", Color.CYAN
        )
        self._conduct_player_interactions(
            alive_players,
            "day_voting",
            f"It's now the VOTING PHASE (Round {self.round_number}). Make your final arguments and YOU MUST VOTE to eliminate a suspected Mafia member. End your message with VOTE: [player name].",
            messages,
            collect_votes=True,
            votes=votes,
        )

        vote_counts = {}
        vote_details = {}
        for voter, target_name in votes.items():
            if target_name in vote_counts:
                vote_counts[target_name] += 1
            else:
                vote_counts[target_name] = 1

            if target_name not in vote_details:
                vote_details[target_name] = []
            vote_details[target_name].append(voter)

        max_votes = 0
        eliminated_player = None

        for target_name, vote_count in vote_counts.items():
            if vote_count > max_votes:
                max_votes = vote_count
                for player in alive_players:
                    if player.player_name == target_name:
                        eliminated_player = player
                        break

        eliminated_players = []
        if eliminated_player:
            # Исключаем игрока без подтверждения
            eliminated_player.alive = False
            eliminated_players.append(eliminated_player)
            self.current_round_data["eliminations"].append(
                eliminated_player.player_name
            )

            self.current_round_data["eliminated_by_vote"] = [
                eliminated_player.player_name
            ]

            self.current_round_data["vote_counts"] = vote_counts
            self.current_round_data["vote_details"] = vote_details

            outcome_text = f"{eliminated_player.player_name} [{eliminated_player.model_name}] was eliminated by vote with {vote_counts[eliminated_player.player_name]} votes."
            self.current_round_data["outcome"] += f" {outcome_text}"
            self.logger.event(outcome_text, Color.YELLOW)

            voters = vote_details.get(eliminated_player.player_name, [])
            if voters:
                voter_names = [name.split("/")[-1] for name in voters]
                voter_text = f"Voted by: {', '.join(voter_names)}"
                self.current_round_data["voters"] = voters
                self.logger.event(voter_text, Color.YELLOW)
        else:
            outcome_text = "No one was eliminated by vote."
            self.current_round_data["outcome"] += f" {outcome_text}"
            self.logger.event(outcome_text, Color.YELLOW)

            self.current_round_data["vote_counts"] = vote_counts
            self.current_round_data["vote_details"] = vote_details

        self.phase = "night"
        self.rounds_data.append(self.current_round_data)
        self.round_number += 1
        self.current_round_data = {
            "round_number": self.round_number,
            "messages": [],
            "actions": {},
            "eliminations": [],
            "eliminated_by_vote": [],
            "targeted_by_mafia": [],
            "protected_by_doctor": [],
            "outcome": "",
        }

        return eliminated_players

    def _conduct_player_interactions(
        self,
        alive_players,
        phase_type,
        instruction,
        messages,
        collect_votes=False,
        votes=None,
    ):
        """
        Conduct interactions with all alive players during the day phase.
        """
        active_names = [p.player_name for p in alive_players]

        for player in alive_players:
            game_state = f"{self.get_game_state()} {instruction}"

            if player.role == Role.DOCTOR:
                day_warnings = {
                    "English": " IMPORTANT: This is the DAY phase. Do NOT use your protection ability now. Only use ACTION: Protect during night phase.",
                    "Spanish": " IMPORTANTE: Esta es la fase DIURNA. NO uses tu habilidad de protección ahora. Solo usa ACCIÓN: Proteger durante la fase nocturna.",
                    "French": " IMPORTANT: C'est la phase de JOUR. N'utilisez PAS votre capacité de protection maintenant. Utilisez ACTION: Protéger uniquement pendant la phase de nuit.",
                    "Korean": " 중요: 지금은 낮 단계입니다. 지금은 보호 능력을 사용하지 마세요. 행동: 보호하기는 밤 단계에서만 사용하세요.",
                }
                warning = day_warnings.get(player.language, day_warnings["English"])
                game_state += warning
            elif player.role == Role.MAFIA:
                day_warnings = {
                    "English": " IMPORTANT: This is the DAY phase. Do NOT use 'ACTION: Kill' now. Instead, use 'VOTE: [player]' to vote like other villagers.",
                    "Spanish": " IMPORTANTE: Esta es la fase DIURNA. NO uses 'ACCIÓN: Matar' ahora. En su lugar, usa 'VOTO: [jugador]' para votar como los demás aldeanos.",
                    "French": " IMPORTANT: C'est la phase de JOUR. N'utilisez PAS 'ACTION: Tuer' maintenant. À la place, utilisez 'VOTE: [joueur]' pour voter comme les autres villageois.",
                    "Korean": " 중요: 지금은 낮 단계입니다. '행동: 죽이기'를 사용하지 마세요. 대신 다른 마을 사람들처럼 '투표: [플레이어]'를 사용하여 투표하세요.",
                }
                warning = day_warnings.get(player.language, day_warnings["English"])
                game_state += warning

            if phase_type == "day_voting":
                voting_reminders = {
                    "English": " REMINDER: This is the VOTING PHASE. You MUST end your message with 'VOTE: [player]' to cast your vote.",
                    "Spanish": " RECORDATORIO: Esta es la fase de VOTACIÓN. DEBES terminar tu mensaje con 'VOTO: [jugador]' para emitir tu voto.",
                    "French": " RAPPEL: C'est la phase de VOTE. Vous DEVEZ terminer votre message par 'VOTE: [joueur]' pour exprimer votre vote.",
                    "Korean": " 알림: 지금은 투표 단계입니다. 반드시 메시지 끝에 '투표: [플레이어]'를 포함하여 투표해야 합니다.",
                }
                reminder = voting_reminders.get(
                    player.language, voting_reminders["English"]
                )
                game_state += reminder

            # Получаем RAG контекст для игрока
            rag_context = self.rag_manager.generate_rag_context(
                self.get_rag_game_state(),
                player.role.value
            )
            
            # Комбинируем обычную историю обсуждений с RAG контекстом
            enhanced_discussion = self.discussion_history_without_thinkings()
            if rag_context:
                enhanced_discussion = rag_context + enhanced_discussion
                
                # Логируем информацию о RAG
                rag_short_name = self.rag_manager.get_short_name(config.RAG_TYPE)
                self.logger.log(
                    f"[{player.player_name}] Playing with RAG: {rag_short_name}", Color.GREEN
                )
                
                if config.GRAPH_DEBUG:
                    self.logger.log(
                        f"\n[RAG CONTEXT for {player.player_name}]:\n{rag_context}", Color.CYAN
                    )

            prompt = player.generate_prompt(
                game_state,
                alive_players,
                self.mafia_players if player.role == Role.MAFIA else None,
                enhanced_discussion,
            )

            response = player.get_response(prompt)
            sanitized = sanitize_model_response(
                response,
                player.player_name,
                active_names,
                phase_type,
            )

            clean_test = sanitized.strip().upper()
            if not sanitized or (
                phase_type in ["day_discussion", "discussion"]
                and (
                    "ACTION:" in clean_test
                    or "VOTE:" in clean_test
                    or "ACCIÓN:" in clean_test
                )
            ):
                continue

            # Сначала обрабатываем голосование, чтобы знать, нужно ли добавлять автоматический голос
            auto_vote_added = False
            final_content = sanitized
            
            if collect_votes and votes is not None:
                vote_target = player.parse_day_vote(sanitized, alive_players)

                # Проверяем на неправильное голосование (за себя или выбывшего игрока)
                if (
                    vote_target and hasattr(vote_target, 'player_name') and vote_target.player_name == player.player_name
                ) or (
                    vote_target and hasattr(vote_target, 'alive') and not vote_target.alive
                ):
                    # Неправильное голосование - ставим VOTE: None
                    self.logger.player_action(
                        player.player_name,
                        player.role.value,
                        "Vote None (invalid vote)",
                        player.player_name,
                    )
                    self.current_round_data["actions"][player.player_name] = "Vote None (invalid vote)"
                    
                    # Добавляем VOTE: None в лог и историю
                    vote_message = "VOTE: None"
                    final_content = f"{sanitized} {vote_message}"
                    vote_target = None  # Не добавляем в голоса
                elif not vote_target:
                    # Игрок не проголосовал - добавляем случайный голос
                    possible_targets = [
                        p for p in alive_players if p.player_name != player.player_name
                    ]
                    if possible_targets:
                        import random

                        vote_target = random.choice(possible_targets)
                        auto_text = f"(auto-selected)"
                        auto_vote_added = True
                        
                        # Добавляем автоматический голос к контенту
                        vote_message = f"VOTE: {vote_target.player_name}"
                        final_content = f"{sanitized} {vote_message}"
                        
                        self.logger.player_action(
                            player.player_name,
                            player.role.value,
                            f"Vote {vote_target.player_name} {auto_text}",
                            player.player_name,
                        )
                        self.current_round_data["actions"][player.player_name] = (
                            f"Vote {vote_target.player_name} {auto_text}"
                        )
                    else:
                        vote_target = None

            # Теперь логируем с финальным контентом (включая автоматический голос если он был добавлен)
            self.logger.player_response(
                player.player_name, player.role.value, final_content, player.player_name
            )

            msg_data = {
                "speaker": player.player_name,
                "content": final_content,
                "phase": phase_type,
                "role": player.role.value,
                "player_name": player.player_name,
            }
            messages.append(
                {
                    "speaker": player.player_name,
                    "content": final_content,
                    "player_name": player.player_name,
                }
            )
            self.current_round_data["messages"].append(msg_data)

            if collect_votes and votes is not None:
                        
                if vote_target:
                    votes[player.player_name] = vote_target.player_name
                    if "actions" not in self.current_round_data:
                        self.current_round_data["actions"] = {}

                    if not self.current_round_data["actions"].get(
                        player.player_name, None
                    ):
                        action_text = f"Vote {vote_target.player_name}"
                        self.current_round_data["actions"][player.player_name] = (
                            action_text
                        )
                        self.logger.player_action(
                            player.player_name,
                            player.role.value,
                            action_text,
                            player.player_name,
                        )
                # Если vote_target == None, то действие уже записано выше (воздержание)

            # Добавляем в историю обсуждений финальный контент
            self.discussion_history += f"{player.player_name}: {final_content}\n\n"

    def get_last_words(self, player, vote_count):
        """
        Get the last words from a player who is about to be eliminated.

        Args:
            player (Player): The player who is about to be eliminated.
            vote_count (int): The number of votes against the player.

        Returns:
            str: The player's last words.
        """
        self.logger.event(
            f"Getting last words from {player.player_name} [{player.model_name}]...",
            Color.CYAN,
        )

        game_state = f"{self.get_game_state()} You have been voted out with {vote_count} votes and will be eliminated. Share your final thoughts before leaving the game."
        
        # Получаем RAG контекст для последних слов
        rag_context = self.rag_manager.generate_rag_context(
            self.get_rag_game_state(),
            player.role.value
        )
        
        enhanced_discussion = self.discussion_history_without_thinkings()
        if rag_context:
            enhanced_discussion = rag_context + enhanced_discussion
            
            # Логируем информацию о RAG
            rag_short_name = self.rag_manager.get_short_name(config.RAG_TYPE)
            self.logger.log(
                f"[{player.player_name}] Playing with RAG: {rag_short_name}", Color.GREEN
            )
        
        prompt = player.generate_prompt(
            game_state,
            self.get_alive_players(),
            self.mafia_players if player.role == Role.MAFIA else None,
            enhanced_discussion,
        )

        response = player.get_response(prompt)
        self.logger.player_response(
            player.model_name,
            f"{player.role.value} (Last Words)",
            response,
            player.player_name,
        )

        return response


    def run_game(self, game_number=1):
        """
        Run the Mafia game until completion.

        Returns:
            tuple: (winner, rounds_data, participants, language) where winner is "Mafia" or "Villagers".
                   rounds_data includes all messages (day and night phases) for game details,
                   but players only see day phase messages during the game.
                   language is the language used for the game.
        """

        if not self.setup_game(game_number):
            return None, [], {}, self.language

        game_over = False
        winner = None

        while not game_over:
            game_over, winner = self.check_game_over()
            if game_over:
                break

            self.execute_day_phase()

            game_over, winner = self.check_game_over()
            if game_over:
                break

            self.execute_night_phase()

        if self.current_round_data["round_number"] > 0:
            self.rounds_data.append(self.current_round_data)

        participants = {}
        for player in self.players:
            # Определяем RAG информацию для игрока
            model_display_name = player.model_name
            if config.RAG_ENABLED:
                # Получаем полное название RAG типа (на случай если config.RAG_TYPE короткое)
                rag_type = config.RAG_TYPE.strip()
                if rag_type.upper() in [short for short in self.rag_manager.short_names.values()]:
                    rag_type = self.rag_manager.get_full_name_from_short(rag_type)
                
                provider = self.rag_manager.providers.get(rag_type)
                if provider and provider.is_applicable_for_player(player.role.value, config.RAG_TARGET):
                    rag_short_name = self.rag_manager.get_short_name(rag_type)
                    model_display_name = f"{player.model_name}-{rag_short_name}"
            
            participants[player.player_name] = {
                "role": player.role.value,
                "model_name": player.model_name,  # Оригинальное название модели
                "model_display_name": model_display_name,  # Название с RAG для отображения
                "player_name": player.player_name,
                "survived": player.alive,
            }

        # Собираем дополнительную статистику игры
        game_stats = {
            "total_rounds": self.round_number,
            "survivors_count": sum(1 for p in self.players if p.alive),
            "mafia_survivors": sum(1 for p in self.mafia_players if p.alive),
            "villager_survivors": sum(1 for p in self.villager_players if p.alive),
            "doctor_survived": self.doctor_player.alive if self.doctor_player else False,
            "total_eliminations": len(self.players) - sum(1 for p in self.players if p.alive),
            "mafia_eliminations": sum(1 for p in self.mafia_players if not p.alive),
            "villager_eliminations": sum(1 for p in self.villager_players if not p.alive),
            "doctor_eliminated": not self.doctor_player.alive if self.doctor_player else False,
        }

        critic_review = self.generate_critic_review(winner)

        self.logger.game_end(game_number, winner, self.round_number)

        # Добавляем информацию о RAG в результаты игры
        rag_info = {
            "enabled": config.RAG_ENABLED,
            "type": config.RAG_TYPE if config.RAG_ENABLED else None,
            "short_name": self.rag_manager.get_short_name(config.RAG_TYPE) if config.RAG_ENABLED else None,
            "target": config.RAG_TARGET if config.RAG_ENABLED else None
        }

        return winner, self.rounds_data, participants, self.language, critic_review, game_stats, rag_info

    def generate_critic_review(self, winner):
        """
        Generate a game critic review using Claude via OpenRouter.

        Args:
            winner (str): The winning team ("Mafia" or "Villagers").

        Returns:
            dict: A dictionary containing the critic review with title, content, and one-sentence summary.
        """

        game_summary = {
            "winner": winner,
            "rounds": self.round_number,
            "participants": {
                player.player_name: player.role.value for player in self.players
            },
            "eliminations": [],
        }

        for round_data in self.rounds_data:
            if "eliminations" in round_data and round_data["eliminations"]:
                for player in round_data["eliminations"]:
                    game_summary["eliminations"].append(
                        {
                            "player": player,
                            "round": round_data["round_number"],
                            "phase": round_data.get("phase", "unknown"),
                        }
                    )

        prompt = f"""You are a professional game critic reviewing a Mafia game played by AI language models. 
        
    Game summary:
    - Winner: {winner}
    - Number of rounds: {self.round_number}
    - Players and roles: {game_summary["participants"]}
    - Eliminations: {game_summary["eliminations"]}
    
    Write a short, entertaining critic review of this game. Include:
    1. A catchy title for your review (max 50 characters)
    2. A concise review (max 200 words) that analyzes:
       - The game's pacing and length
       - Interesting strategic moves or blunders
       - The performance of the winning team
       - Any particularly noteworthy moments
    3. A one-sentence intense summary that captures the essence of the game in a dramatic way (max 100 characters)
    
    Your tone should be professional but entertaining, like a game critic. Be specific about this particular game.
    Format your response as a JSON object with 'title', 'content', and 'one_liner' fields.
    """

        try:
            model_name = config.CLAUDE_3_7_SONNET

            response_content = get_llm_response(model_name, prompt)

            if response_content == "ERROR: Could not get response":
                print("[CRITIC REVIEW ERROR]: Model did not return a review.\n")
                return {
                    "title": "Game Review Unavailable",
                    "content": "The critic was unable to review this game due to API issues.",
                    "one_liner": "Technical difficulties prevented our critic from witnessing this showdown.",
                }

            json_match = re.search(r"({.*})", response_content, re.DOTALL)

            if json_match:
                try:
                    review_json = json.loads(json_match.group(1))

                    if "one_liner" not in review_json:
                        review_json["one_liner"] = (
                            "A game that defies simple description!"
                        )

                    print("[CRITIC REVIEW PARSED]:")
                    print("TITLE:", review_json.get("title", ""))
                    print("ONE LINER:", review_json.get("one_liner", ""))
                    print("CONTENT:", review_json.get("content", ""))
                    print()

                    return review_json
                except json.JSONDecodeError:
                    print(
                        "[CRITIC REVIEW ERROR]: JSONDecodeError, sending fallback string.\n"
                    )
                    return {
                        "title": "AI Mafia Game Review",
                        "content": response_content[:300],
                        "one_liner": "A game that left our critic speechless!",
                    }
            else:
                print(
                    "[CRITIC REVIEW WARNING]: No JSON object found in the response, returning head of string.\n"
                )
                return {
                    "title": "AI Mafia Game Review",
                    "content": response_content[:300],
                    "one_liner": "A game that defies conventional criticism!",
                }

        except Exception as e:
            print(f"Error generating critic review: {e}")
            return {
                "title": "Game Review Unavailable",
                "content": "The critic was unable to review this game due to technical difficulties.",
                "one_liner": "Technical issues prevented our critic from delivering judgment.",
            }


player_names = [
    "Alex",
    "Bailey",
    "Casey",
    "Dana",
    "Ellis",
    "Finley",
    "Gray",
    "Harper",
    "Indigo",
    "Jordan",
    "Kennedy",
    "Logan",
    "Morgan",
    "Nico",
    "Parker",
    "Quinn",
    "Riley",
    "Sage",
    "Taylor",
    "Avery",
    "Blake",
    "Cameron",
    "Drew",
    "Emerson",
    "Frankie",
    "Hayden",
    "Jamie",
    "Kai",
    "Leighton",
    "Marley",
    "Noel",
    "Oakley",
    "Peyton",
    "Reese",
    "Skyler",
    "Tatum",
    "Val",
    "Winter",
    "Zion",
]
