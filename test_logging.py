#!/usr/bin/env python3
"""
Тест для проверки логирования RAG информации.
"""

import os
import sys

# Добавляем src в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import config
from logger import GameLogger, Color
from rag_providers import RAGManager

def test_rag_logging():
    """Тестирует логирование RAG информации."""
    print("=== Тестирование логирования RAG ===\n")
    
    logger = GameLogger(log_to_file=False, game_id="TEST")
    rag_manager = RAGManager()
    
    # Сохраняем оригинальные настройки
    original_enabled = config.RAG_ENABLED
    original_type = config.RAG_TYPE
    original_target = config.RAG_TARGET
    
    try:
        # Тест 1: RAG отключен
        config.RAG_ENABLED = False
        logger.print("=== Test 1: RAG Disabled ===", Color.YELLOW, bold=True)
        logger.player_setup("gryphe/mythomax-l2-13b", "Mafia", "Alex", "")
        print()
        
        # Тест 2: RAG для всех с Discussion Graph
        config.RAG_ENABLED = True
        config.RAG_TYPE = "discussion_graph"
        config.RAG_TARGET = "all"
        
        logger.print("=== Test 2: RAG for All Players (Discussion Graph) ===", Color.YELLOW, bold=True)
        
        # Тестируем разные роли
        roles = [("Mafia", "Alex"), ("Doctor", "Bailey"), ("Villager", "Casey")]
        
        for role, name in roles:
            # Определяем RAG информацию
            provider = rag_manager.providers.get(config.RAG_TYPE)
            rag_info = ""
            if provider and provider.is_applicable_for_player(role, config.RAG_TARGET):
                rag_short_name = rag_manager.get_short_name(config.RAG_TYPE)
                rag_info = f" (RAG: {rag_short_name})"
            
            logger.player_setup("gryphe/mythomax-l2-13b", role, name, rag_info)
        print()
        
        # Тест 3: RAG только для мафии
        config.RAG_TARGET = "mafia"
        logger.print("=== Test 3: RAG for Mafia Only ===", Color.YELLOW, bold=True)
        
        for role, name in roles:
            provider = rag_manager.providers.get(config.RAG_TYPE)
            rag_info = ""
            if provider and provider.is_applicable_for_player(role, config.RAG_TARGET):
                rag_short_name = rag_manager.get_short_name(config.RAG_TYPE)
                rag_info = f" (RAG: {rag_short_name})"
            
            logger.player_setup("gryphe/mythomax-l2-13b", role, name, rag_info)
        print()
        
        # Тест 4: RAG только для мирных с Analytical Hints
        config.RAG_TYPE = "analytical_hints"
        config.RAG_TARGET = "villagers"
        logger.print("=== Test 4: RAG for Villagers Only (Analytical Hints) ===", Color.YELLOW, bold=True)
        
        for role, name in roles:
            provider = rag_manager.providers.get(config.RAG_TYPE)
            rag_info = ""
            if provider and provider.is_applicable_for_player(role, config.RAG_TARGET):
                rag_short_name = rag_manager.get_short_name(config.RAG_TYPE)
                rag_info = f" (RAG: {rag_short_name})"
            
            logger.player_setup("gryphe/mythomax-l2-13b", role, name, rag_info)
        print()
        
        # Тест 5: Симуляция условий игры
        logger.print("=== Test 5: Game Conditions Display ===", Color.YELLOW, bold=True)
        
        test_conditions = [
            (True, "discussion_graph", "all"),
            (True, "analytical_hints", "mafia"),
            (True, "history_graph", "villagers"),
            (False, "discussion_graph", "all")
        ]
        
        for enabled, rag_type, target in test_conditions:
            config.RAG_ENABLED = enabled
            config.RAG_TYPE = rag_type
            config.RAG_TARGET = target
            
            if enabled:
                rag_full_name = {
                    "discussion_graph": "Discussion Graph",
                    "history_graph": "History Graph", 
                    "current_round_graph": "Current Round Graph",
                    "communication_graph": "Communication Graph",
                    "auto_summaries": "Auto Summaries",
                    "analytical_hints": "Analytical Hints"
                }.get(rag_type, rag_type)
                
                rag_short_name = rag_manager.get_short_name(rag_type)
                
                if target == "all":
                    target_desc = "All players"
                elif target == "mafia":
                    target_desc = "Mafia team"
                elif target == "villagers":
                    target_desc = "Villagers team"
                else:
                    target_desc = target
                    
                logger.print(f"Game Conditions: {target_desc} playing with {rag_full_name} ({rag_short_name})", Color.BRIGHT_CYAN, bold=True)
            else:
                logger.print("Game Conditions: No RAG enhancement", Color.BRIGHT_CYAN, bold=True)
        
    finally:
        # Восстанавливаем оригинальные настройки
        config.RAG_ENABLED = original_enabled
        config.RAG_TYPE = original_type
        config.RAG_TARGET = original_target
    
    print("\n=== Тестирование логирования завершено ===")

if __name__ == "__main__":
    test_rag_logging()