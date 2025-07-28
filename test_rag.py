#!/usr/bin/env python3
"""
Простой тест для проверки работы RAG архитектуры.
"""

import os
import sys

# Добавляем src в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from rag_providers import RAGManager
import config

def test_rag_providers():
    """Тестирует все RAG провайдеры."""
    print("=== Тестирование RAG провайдеров ===\n")
    
    # Создаем RAG менеджер
    rag_manager = RAGManager()
    
    # Тестовые данные игры
    test_game_state = {
        "discussion_history": "Alex: I think Bailey is suspicious. Bailey: No, I'm innocent! Casey: I agree with Alex about Bailey.",
        "rounds_data": [
            {
                "round_number": 1,
                "messages": [
                    {"speaker": "Alex", "content": "Bailey seems suspicious to me", "phase": "day_discussion"},
                    {"speaker": "Bailey", "content": "I'm innocent, trust me!", "phase": "day_discussion"},
                    {"speaker": "Casey", "content": "I vote Bailey", "phase": "day_voting"}
                ],
                "eliminations": ["Bailey"],
                "outcome": "Bailey was eliminated by vote"
            }
        ],
        "current_round_data": {
            "messages": [
                {"speaker": "Alex", "content": "Now I suspect Casey", "phase": "day_discussion"},
                {"speaker": "Casey", "content": "That's not fair!", "phase": "day_discussion"}
            ]
        },
        "alive_players": [
            {"player_name": "Alex"},
            {"player_name": "Casey"},
            {"player_name": "Dana"}
        ],
        "models": [config.DEFAULT_MODEL],
        "round_number": 2,
        "phase": "day"
    }
    
    # Тестируем каждый тип RAG
    rag_types = ["discussion_graph", "history_graph", "current_round_graph", 
                 "communication_graph", "auto_summaries", "analytical_hints"]
    
    for rag_type in rag_types:
        print(f"--- Тестирование {rag_type} ---")
        
        if rag_type in rag_manager.providers:
            provider = rag_manager.providers[rag_type]
            short_name = rag_manager.get_short_name(rag_type)
            
            print(f"Короткое название: {short_name}")
            
            try:
                context = provider.generate_context(test_game_state)
                if context:
                    print(f"Контекст сгенерирован ({len(context)} символов):")
                    print(context[:200] + "..." if len(context) > 200 else context)
                else:
                    print("Контекст пустой")
            except Exception as e:
                print(f"Ошибка: {e}")
        else:
            print(f"Провайдер {rag_type} не найден")
        
        print()
    
    # Тестируем RAG менеджер с разными настройками
    print("--- Тестирование RAG менеджера ---")
    
    # Сохраняем оригинальные настройки
    original_enabled = config.RAG_ENABLED
    original_type = config.RAG_TYPE
    original_target = config.RAG_TARGET
    
    try:
        # Тест 1: RAG отключен
        config.RAG_ENABLED = False
        context = rag_manager.generate_rag_context(test_game_state, "Villager")
        print(f"RAG отключен: {'Пустой контекст' if not context else 'Есть контекст (ошибка!)'}")
        
        # Тест 2: RAG включен для всех
        config.RAG_ENABLED = True
        config.RAG_TYPE = "discussion_graph"
        config.RAG_TARGET = "all"
        
        for role in ["Mafia", "Doctor", "Villager"]:
            context = rag_manager.generate_rag_context(test_game_state, role)
            print(f"RAG для {role}: {'Есть контекст' if context else 'Пустой контекст'}")
        
        # Тест 3: RAG только для мафии
        config.RAG_TARGET = "mafia"
        
        for role in ["Mafia", "Doctor", "Villager"]:
            context = rag_manager.generate_rag_context(test_game_state, role)
            print(f"RAG только для мафии, роль {role}: {'Есть контекст' if context else 'Пустой контекст'}")
        
        # Тест 4: RAG только для мирных
        config.RAG_TARGET = "villagers"
        
        for role in ["Mafia", "Doctor", "Villager"]:
            context = rag_manager.generate_rag_context(test_game_state, role)
            print(f"RAG только для мирных, роль {role}: {'Есть контекст' if context else 'Пустой контекст'}")
            
    finally:
        # Восстанавливаем оригинальные настройки
        config.RAG_ENABLED = original_enabled
        config.RAG_TYPE = original_type
        config.RAG_TARGET = original_target
    
    print("\n=== Тестирование завершено ===")

if __name__ == "__main__":
    test_rag_providers()