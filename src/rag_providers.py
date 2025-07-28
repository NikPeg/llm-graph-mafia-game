"""
RAG (Retrieval-Augmented Generation) providers for the LLM Mafia Game.
Provides additional context information to enhance player prompts.
"""

import re
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from openrouter import get_llm_response
import config


class RAGProvider(ABC):
    """Abstract base class for all RAG providers."""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def generate_context(self, game_state: Dict[str, Any]) -> str:
        """
        Generate additional context information for player prompts.
        
        Args:
            game_state: Dictionary containing current game state information
            
        Returns:
            str: Additional context to be added to player prompts
        """
        pass
    
    def is_applicable_for_player(self, player_role: str, target_setting: str) -> bool:
        """
        Check if this RAG provider should be applied for a specific player.
        
        Args:
            player_role: Role of the player ("Mafia", "Doctor", "Villager")
            target_setting: RAG target setting ("all", "mafia", "villagers")
            
        Returns:
            bool: True if RAG should be applied for this player
        """
        if target_setting == "all":
            return True
        elif target_setting == "mafia":
            return player_role == "Mafia"
        elif target_setting == "villagers":
            return player_role in ["Doctor", "Villager"]
        return False


class DiscussionGraphRAG(RAGProvider):
    """RAG provider that generates relationship graphs from discussion history."""
    
    def __init__(self):
        super().__init__("discussion_graph")
    
    def generate_context(self, game_state: Dict[str, Any]) -> str:
        """Generate relationship graph from discussion history."""
        discussion_history = game_state.get("discussion_history", "")
        if not discussion_history:
            return ""
        
        graph_prompt = (
            "Based only on the discussion history between players in a game of Mafia below, "
            "extract and list ALL explicit, clearly-stated *relationships* between players—such as direct suspicion, trust, voting, accusations, or alliance/support. "
            "DO NOT invent information, do NOT deduce, do NOT guess or imagine any relationships—list only those that are IMPLICITLY or EXPLICITLY PRESENT in the text. "
            "Format: [SOURCE] -> [relation/action] -> [TARGET] (one edge per line).\n"
            "Discussion history:\n"
            f"{discussion_history}\n"
            "\nList of relationship edges:"
        )
        
        models = game_state.get("models", [config.DEFAULT_MODEL])
        model_name = models[0] if models else config.DEFAULT_MODEL
        graph_text = get_llm_response(model_name, graph_prompt)
        
        lines = [
            line.strip()
            for line in graph_text.splitlines()
            if re.match(r"^\w+(?: \w+)*\s*->\s*\w+\s*->\s*\w+(?: \w+)*$", line.strip())
        ]
        result = "\n".join(lines).strip()
        
        if result:
            return f"\n--- Discussion Relationship Graph ---\n{result}\n"
        return ""


class HistoryGraphRAG(RAGProvider):
    """RAG provider that generates graphs from complete game history."""
    
    def __init__(self):
        super().__init__("history_graph")
    
    def generate_context(self, game_state: Dict[str, Any]) -> str:
        """Generate relationship graph from complete game history."""
        rounds_data = game_state.get("rounds_data", [])
        if not rounds_data:
            return ""
        
        # Собираем все сообщения из всех раундов
        all_messages = []
        for round_data in rounds_data:
            messages = round_data.get("messages", [])
            for msg in messages:
                if msg.get("phase") == "day_discussion" or msg.get("phase") == "day_voting":
                    all_messages.append(f"{msg.get('speaker', 'Unknown')}: {msg.get('content', '')}")
        
        if not all_messages:
            return ""
        
        history_text = "\n\n".join(all_messages[-20:])  # Последние 20 сообщений
        
        graph_prompt = (
            "Based on the complete game history below from a Mafia game, "
            "extract key relationships and patterns between players across all rounds. "
            "Focus on: alliances, consistent suspicions, voting patterns, trust relationships. "
            "Format: [SOURCE] -> [relation/pattern] -> [TARGET] (one edge per line).\n"
            "Game history:\n"
            f"{history_text}\n"
            "\nHistorical relationship patterns:"
        )
        
        models = game_state.get("models", [config.DEFAULT_MODEL])
        model_name = models[0] if models else config.DEFAULT_MODEL
        graph_text = get_llm_response(model_name, graph_prompt)
        
        lines = [
            line.strip()
            for line in graph_text.splitlines()
            if re.match(r"^\w+(?: \w+)*\s*->\s*\w+\s*->\s*\w+(?: \w+)*$", line.strip())
        ]
        result = "\n".join(lines).strip()
        
        if result:
            return f"\n--- Historical Relationship Patterns ---\n{result}\n"
        return ""


class CurrentRoundGraphRAG(RAGProvider):
    """RAG provider that generates graphs from current round data."""
    
    def __init__(self):
        super().__init__("current_round_graph")
    
    def generate_context(self, game_state: Dict[str, Any]) -> str:
        """Generate relationship graph from current round."""
        current_round = game_state.get("current_round_data", {})
        messages = current_round.get("messages", [])
        
        if not messages:
            return ""
        
        # Фильтруем только дневные сообщения текущего раунда
        day_messages = [
            f"{msg.get('speaker', 'Unknown')}: {msg.get('content', '')}"
            for msg in messages
            if msg.get("phase") in ["day_discussion", "day_voting"]
        ]
        
        if not day_messages:
            return ""
        
        round_text = "\n\n".join(day_messages)
        
        graph_prompt = (
            "Based on the current round discussion below from a Mafia game, "
            "extract immediate relationships and interactions between players in THIS round only. "
            "Focus on: current suspicions, votes, defenses, accusations made in this round. "
            "Format: [SOURCE] -> [current_action] -> [TARGET] (one edge per line).\n"
            "Current round discussion:\n"
            f"{round_text}\n"
            "\nCurrent round relationships:"
        )
        
        models = game_state.get("models", [config.DEFAULT_MODEL])
        model_name = models[0] if models else config.DEFAULT_MODEL
        graph_text = get_llm_response(model_name, graph_prompt)
        
        lines = [
            line.strip()
            for line in graph_text.splitlines()
            if re.match(r"^\w+(?: \w+)*\s*->\s*\w+\s*->\s*\w+(?: \w+)*$", line.strip())
        ]
        result = "\n".join(lines).strip()
        
        if result:
            return f"\n--- Current Round Interactions ---\n{result}\n"
        return ""


class CommunicationGraphRAG(RAGProvider):
    """RAG provider that analyzes communication patterns between players."""
    
    def __init__(self):
        super().__init__("communication_graph")
    
    def generate_context(self, game_state: Dict[str, Any]) -> str:
        """Generate communication pattern analysis."""
        rounds_data = game_state.get("rounds_data", [])
        current_round = game_state.get("current_round_data", {})
        
        # Собираем статистику коммуникации
        communication_stats = {}
        all_rounds = rounds_data + [current_round] if current_round.get("messages") else rounds_data
        
        for round_data in all_rounds:
            messages = round_data.get("messages", [])
            for msg in messages:
                if msg.get("phase") in ["day_discussion", "day_voting"]:
                    speaker = msg.get("speaker", "Unknown")
                    content = msg.get("content", "")
                    
                    if speaker not in communication_stats:
                        communication_stats[speaker] = {
                            "message_count": 0,
                            "mentions": {},
                            "avg_length": 0,
                            "total_length": 0
                        }
                    
                    communication_stats[speaker]["message_count"] += 1
                    communication_stats[speaker]["total_length"] += len(content)
                    
                    # Ищем упоминания других игроков
                    alive_players = game_state.get("alive_players", [])
                    for player in alive_players:
                        player_name = player.get("player_name", "") if isinstance(player, dict) else getattr(player, "player_name", "")
                        if player_name and player_name != speaker and player_name.lower() in content.lower():
                            if player_name not in communication_stats[speaker]["mentions"]:
                                communication_stats[speaker]["mentions"][player_name] = 0
                            communication_stats[speaker]["mentions"][player_name] += 1
        
        # Вычисляем средние длины сообщений
        for speaker, stats in communication_stats.items():
            if stats["message_count"] > 0:
                stats["avg_length"] = stats["total_length"] / stats["message_count"]
        
        # Формируем граф коммуникации
        comm_lines = []
        for speaker, stats in communication_stats.items():
            for mentioned, count in stats["mentions"].items():
                if count >= 2:  # Упоминал минимум 2 раза
                    comm_lines.append(f"{speaker} -> mentions_frequently -> {mentioned}")
        
        if comm_lines:
            return f"\n--- Communication Patterns ---\n" + "\n".join(comm_lines) + "\n"
        return ""


class AutoSummariesRAG(RAGProvider):
    """RAG provider that generates automatic summaries of game events."""
    
    def __init__(self):
        super().__init__("auto_summaries")
    
    def generate_context(self, game_state: Dict[str, Any]) -> str:
        """Generate automatic summaries of key game events."""
        rounds_data = game_state.get("rounds_data", [])
        if not rounds_data:
            return ""
        
        # Собираем ключевые события
        key_events = []
        for round_data in rounds_data:
            round_num = round_data.get("round_number", 0)
            eliminations = round_data.get("eliminations", [])
            outcome = round_data.get("outcome", "")
            
            if eliminations:
                key_events.append(f"Round {round_num}: {', '.join(eliminations)} eliminated. {outcome}")
        
        if not key_events:
            return ""
        
        events_text = "\n".join(key_events)
        
        summary_prompt = (
            "Based on the key events from a Mafia game below, "
            "provide a concise summary of the game's progression and current situation. "
            "Focus on: elimination patterns, potential strategies, remaining threats.\n"
            "Key events:\n"
            f"{events_text}\n"
            "\nGame summary:"
        )
        
        models = game_state.get("models", [config.DEFAULT_MODEL])
        model_name = models[0] if models else config.DEFAULT_MODEL
        summary = get_llm_response(model_name, summary_prompt)
        
        if summary and summary != "ERROR: Could not get response":
            return f"\n--- Game Summary ---\n{summary.strip()}\n"
        return ""


class AnalyticalHintsRAG(RAGProvider):
    """RAG provider that generates analytical hints about alive players."""
    
    def __init__(self):
        super().__init__("analytical_hints")
    
    def generate_context(self, game_state: Dict[str, Any]) -> str:
        """Generate analytical hints about each alive player."""
        alive_players = game_state.get("alive_players", [])
        rounds_data = game_state.get("rounds_data", [])
        
        if not alive_players or not rounds_data:
            return ""
        
        # Собираем данные о каждом живом игроке
        player_analysis = {}
        for player in alive_players:
            player_name = player.get("player_name", "") if isinstance(player, dict) else getattr(player, "player_name", "")
            if not player_name:
                continue
                
            player_analysis[player_name] = {
                "messages": 0,
                "votes_cast": 0,
                "votes_received": 0,
                "mentions": 0,
                "suspicious_behavior": []
            }
        
        # Анализируем поведение по раундам
        for round_data in rounds_data:
            messages = round_data.get("messages", [])
            vote_details = round_data.get("vote_details", {})
            
            for msg in messages:
                speaker = msg.get("speaker", "")
                content = msg.get("content", "")
                
                if speaker in player_analysis:
                    player_analysis[speaker]["messages"] += 1
                    
                    # Проверяем на подозрительные паттерны
                    if "vote:" in content.lower() and msg.get("phase") == "day_discussion":
                        player_analysis[speaker]["suspicious_behavior"].append("voted_in_discussion_phase")
            
            # Анализируем голоса
            for target, voters in vote_details.items():
                if target in player_analysis:
                    player_analysis[target]["votes_received"] += len(voters)
                for voter in voters:
                    voter_name = voter.split("/")[-1] if "/" in voter else voter
                    if voter_name in player_analysis:
                        player_analysis[voter_name]["votes_cast"] += 1
        
        # Формируем аналитические подсказки
        hints = []
        for player_name, analysis in player_analysis.items():
            hint_parts = []
            
            if analysis["messages"] == 0:
                hint_parts.append("very_quiet")
            elif analysis["messages"] > 5:
                hint_parts.append("very_active")
            
            if analysis["votes_received"] > 2:
                hint_parts.append("frequently_suspected")
            elif analysis["votes_received"] == 0:
                hint_parts.append("never_voted_against")
            
            if analysis["votes_cast"] == 0:
                hint_parts.append("avoids_voting")
            
            if "voted_in_discussion_phase" in analysis["suspicious_behavior"]:
                hint_parts.append("premature_voting")
            
            if hint_parts:
                hints.append(f"{player_name} -> {', '.join(hint_parts)}")
        
        if hints:
            return f"\n--- Player Analysis ---\n" + "\n".join(hints) + "\n"
        return ""


class RAGManager:
    """Manager class for handling multiple RAG providers."""
    
    def __init__(self):
        self.providers = {
            "discussion_graph": DiscussionGraphRAG(),
            "history_graph": HistoryGraphRAG(),
            "current_round_graph": CurrentRoundGraphRAG(),
            "communication_graph": CommunicationGraphRAG(),
            "auto_summaries": AutoSummariesRAG(),
            "analytical_hints": AnalyticalHintsRAG(),
        }
        
        # Короткие названия для логов и Firebase
        self.short_names = {
            "discussion_graph": "DG",
            "history_graph": "HG",
            "current_round_graph": "CRG",
            "communication_graph": "CG",
            "auto_summaries": "AS",
            "analytical_hints": "AH",
        }
    
    def get_short_name(self, rag_type: str) -> str:
        """Получить короткое название RAG типа."""
        return self.short_names.get(rag_type, rag_type.upper())
    
    def get_full_name_from_short(self, short_name: str) -> str:
        """Получить полное название RAG типа по короткому."""
        for full_name, short in self.short_names.items():
            if short == short_name.upper():
                return full_name
        return short_name.lower()
    
    def generate_rag_context(self, game_state: Dict[str, Any], player_role: str) -> str:
        """
        Generate RAG context for a specific player based on configuration.
        
        Args:
            game_state: Current game state information
            player_role: Role of the player requesting context
            
        Returns:
            str: RAG context from the configured provider
        """
        if not config.RAG_ENABLED:
            return ""
        
        rag_type = config.RAG_TYPE.strip()
        
        # Проверяем, не является ли RAG_TYPE коротким названием
        if rag_type.upper() in [short for short in self.short_names.values()]:
            rag_type = self.get_full_name_from_short(rag_type)
        
        if rag_type in self.providers:
            provider = self.providers[rag_type]
            
            # Проверяем, применим ли этот RAG для данного игрока
            if provider.is_applicable_for_player(player_role, config.RAG_TARGET):
                try:
                    context = provider.generate_context(game_state)
                    return context if context else ""
                except Exception as e:
                    print(f"Error generating RAG context for {rag_type}: {e}")
        
        return ""