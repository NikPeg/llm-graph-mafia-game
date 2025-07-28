#!/usr/bin/env python3
"""
Тест для проверки RAG информации в Firebase данных.
"""

import os
import sys

# Добавляем src в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import config
from rag_providers import RAGManager

def simulate_participant_data():
    """Симулирует создание данных участника как в game.py."""
    print("=== Симуляция создания данных участника ===\n")
    
    # Сохраняем оригинальные настройки
    original_enabled = config.RAG_ENABLED
    original_type = config.RAG_TYPE
    original_target = config.RAG_TARGET
    
    try:
        # Настройки для теста
        config.RAG_ENABLED = True
        config.RAG_TYPE = "DG"  # Короткое название
        config.RAG_TARGET = "all"
        
        rag_manager = RAGManager()
        
        # Симулируем участников
        participants = [
            {"name": "Player1", "role": "Mafia", "model_name": "gryphe/mythomax-l2-13b"},
            {"name": "Player2", "role": "Doctor", "model_name": "gryphe/mythomax-l2-13b"},
            {"name": "Player3", "role": "Villager", "model_name": "gryphe/mythomax-l2-13b"},
        ]
        
        print("Исходные данные участников:")
        for p in participants:
            print(f"  {p['name']}: {p['model_name']} ({p['role']})")
        print()
        
        # Применяем логику из game.py (строки 927-933)
        for participant in participants:
            model_display_name = participant["model_name"]
            
            if config.RAG_ENABLED:
                # Получаем полное название RAG типа из короткого
                rag_type = config.RAG_TYPE.strip()
                if rag_type.upper() in [short.upper() for short in rag_manager.short_names.values()]:
                    rag_type = rag_manager.get_full_name_from_short(rag_type)
                
                provider = rag_manager.providers.get(rag_type)
                if provider and provider.is_applicable_for_player(participant["role"], config.RAG_TARGET):
                    rag_short_name = rag_manager.get_short_name(rag_type)
                    model_display_name = f"{participant['model_name']}-{rag_short_name}"
            
            participant["model_display_name"] = model_display_name
        
        print("Данные участников после применения RAG:")
        for p in participants:
            print(f"  {p['name']}: {p['model_display_name']} ({p['role']})")
        print()
        
        # Тест с разными настройками
        print("=== Тест с RAG только для мафии ===")
        config.RAG_TARGET = "mafia"
        config.RAG_TYPE = "AH"
        
        for participant in participants:
            model_display_name = participant["model_name"]
            
            if config.RAG_ENABLED:
                # Получаем полное название RAG типа из короткого
                rag_type = config.RAG_TYPE.strip()
                if rag_type.upper() in [short.upper() for short in rag_manager.short_names.values()]:
                    rag_type = rag_manager.get_full_name_from_short(rag_type)
                
                provider = rag_manager.providers.get(rag_type)
                if provider and provider.is_applicable_for_player(participant["role"], config.RAG_TARGET):
                    rag_short_name = rag_manager.get_short_name(rag_type)
                    model_display_name = f"{participant['model_name']}-{rag_short_name}"
            
            participant["model_display_name"] = model_display_name
        
        for p in participants:
            print(f"  {p['name']}: {p['model_display_name']} ({p['role']})")
        print()
        
        # Проверяем отладочную информацию
        print("=== Отладочная информация ===")
        print(f"RAG_ENABLED: {config.RAG_ENABLED}")
        print(f"RAG_TYPE: '{config.RAG_TYPE}'")
        print(f"RAG_TARGET: '{config.RAG_TARGET}'")
        
        rag_type = config.RAG_TYPE.strip()
        print(f"RAG type after strip: '{rag_type}'")
        
        short_names_values = list(rag_manager.short_names.values())
        print(f"Available short names: {short_names_values}")
        
        is_short_name = rag_type.upper() in [short.upper() for short in short_names_values]
        print(f"Is '{rag_type}' a short name? {is_short_name}")
        
        if is_short_name:
            full_name = rag_manager.get_full_name_from_short(rag_type)
            print(f"Full name: '{full_name}'")
            
            provider = rag_manager.providers.get(full_name)
            print(f"Provider found: {provider is not None}")
            
            if provider:
                for role in ["Mafia", "Doctor", "Villager"]:
                    applicable = provider.is_applicable_for_player(role, config.RAG_TARGET)
                    print(f"  Applicable for {role}: {applicable}")
        
    finally:
        # Восстанавливаем оригинальные настройки
        config.RAG_ENABLED = original_enabled
        config.RAG_TYPE = original_type
        config.RAG_TARGET = original_target
    
    print("\n=== Тестирование завершено ===")

if __name__ == "__main__":
    simulate_participant_data()