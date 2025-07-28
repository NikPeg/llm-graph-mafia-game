#!/usr/bin/env python3
"""
Тест для проверки отображения RAG в названиях моделей.
"""

import os
import sys

# Добавляем src в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import config
from rag_providers import RAGManager

def test_rag_display():
    """Тестирует отображение RAG в названиях моделей."""
    print("=== Тестирование отображения RAG ===\n")
    
    rag_manager = RAGManager()
    
    # Сохраняем оригинальные настройки
    original_enabled = config.RAG_ENABLED
    original_type = config.RAG_TYPE
    original_target = config.RAG_TARGET
    
    try:
        # Тест 1: RAG отключен
        config.RAG_ENABLED = False
        print("=== Test 1: RAG Disabled ===")
        
        model_name = "gryphe/mythomax-l2-13b"
        model_display_name = model_name
        
        if config.RAG_ENABLED:
            # Этот код не должен выполниться
            pass
        
        print(f"Model display name: {model_display_name}")
        print()
        
        # Тест 2: RAG включен для всех с коротким названием DG
        config.RAG_ENABLED = True
        config.RAG_TYPE = "DG"
        config.RAG_TARGET = "all"
        
        print("=== Test 2: RAG Enabled (DG for all) ===")
        
        roles = ["Mafia", "Doctor", "Villager"]
        
        for role in roles:
            model_display_name = model_name
            
            if config.RAG_ENABLED:
                # Получаем полное название RAG типа
                rag_type = config.RAG_TYPE.strip()
                if rag_type.upper() in [short for short in rag_manager.short_names.values()]:
                    rag_type = rag_manager.get_full_name_from_short(rag_type)
                
                provider = rag_manager.providers.get(rag_type)
                if provider and provider.is_applicable_for_player(role, config.RAG_TARGET):
                    rag_short_name = rag_manager.get_short_name(rag_type)
                    model_display_name = f"{model_name}-{rag_short_name}"
            
            print(f"{role}: {model_display_name}")
        print()
        
        # Тест 3: RAG только для мафии с AH
        config.RAG_TYPE = "AH"
        config.RAG_TARGET = "mafia"
        
        print("=== Test 3: RAG for Mafia only (AH) ===")
        
        for role in roles:
            model_display_name = model_name
            
            if config.RAG_ENABLED:
                # Получаем полное название RAG типа
                rag_type = config.RAG_TYPE.strip()
                if rag_type.upper() in [short for short in rag_manager.short_names.values()]:
                    rag_type = rag_manager.get_full_name_from_short(rag_type)
                
                provider = rag_manager.providers.get(rag_type)
                if provider and provider.is_applicable_for_player(role, config.RAG_TARGET):
                    rag_short_name = rag_manager.get_short_name(rag_type)
                    model_display_name = f"{model_name}-{rag_short_name}"
            
            print(f"{role}: {model_display_name}")
        print()
        
        # Тест 4: RAG только для мирных с полным названием
        config.RAG_TYPE = "analytical_hints"
        config.RAG_TARGET = "villagers"
        
        print("=== Test 4: RAG for Villagers only (full name) ===")
        
        for role in roles:
            model_display_name = model_name
            
            if config.RAG_ENABLED:
                # Получаем полное название RAG типа
                rag_type = config.RAG_TYPE.strip()
                if rag_type.upper() in [short for short in rag_manager.short_names.values()]:
                    rag_type = rag_manager.get_full_name_from_short(rag_type)
                
                provider = rag_manager.providers.get(rag_type)
                if provider and provider.is_applicable_for_player(role, config.RAG_TARGET):
                    rag_short_name = rag_manager.get_short_name(rag_type)
                    model_display_name = f"{model_name}-{rag_short_name}"
            
            print(f"{role}: {model_display_name}")
        print()
        
        # Тест 5: Проверяем преобразование коротких названий
        print("=== Test 5: Short name conversion ===")
        
        test_cases = ["DG", "HG", "CRG", "CG", "AS", "AH"]
        
        for short_name in test_cases:
            full_name = rag_manager.get_full_name_from_short(short_name)
            back_to_short = rag_manager.get_short_name(full_name)
            print(f"{short_name} -> {full_name} -> {back_to_short}")
        
    finally:
        # Восстанавливаем оригинальные настройки
        config.RAG_ENABLED = original_enabled
        config.RAG_TYPE = original_type
        config.RAG_TARGET = original_target
    
    print("\n=== Тестирование завершено ===")

if __name__ == "__main__":
    test_rag_display()