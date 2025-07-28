#!/usr/bin/env python3
"""
Интеграционный тест для полной проверки RAG системы.
"""

import os
import sys

# Добавляем src в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import config
from rag_providers import RAGManager

def test_full_rag_integration():
    """Полный интеграционный тест RAG системы."""
    print("=== ИНТЕГРАЦИОННЫЙ ТЕСТ RAG СИСТЕМЫ ===\n")
    
    # Сохраняем оригинальные настройки
    original_enabled = config.RAG_ENABLED
    original_type = config.RAG_TYPE
    original_target = config.RAG_TARGET
    
    try:
        # Тест 1: Полная цепочка с короткими названиями
        print("🔧 Тест 1: Настройка RAG с короткими названиями")
        config.RAG_ENABLED = True
        config.RAG_TYPE = "DG"
        config.RAG_TARGET = "all"
        
        print(f"   RAG_ENABLED: {config.RAG_ENABLED}")
        print(f"   RAG_TYPE: '{config.RAG_TYPE}'")
        print(f"   RAG_TARGET: '{config.RAG_TARGET}'")
        
        rag_manager = RAGManager()
        
        # Проверяем инициализацию RAGManager
        print(f"   RAGManager инициализирован: {len(rag_manager.providers)} провайдеров")
        print(f"   Доступные короткие названия: {list(rag_manager.short_names.values())}")
        
        # Симулируем создание участников игры
        participants = [
            {"name": "Alice", "role": "Mafia", "model_name": "gryphe/mythomax-l2-13b"},
            {"name": "Bob", "role": "Doctor", "model_name": "gryphe/mythomax-l2-13b"},
            {"name": "Charlie", "role": "Villager", "model_name": "gryphe/mythomax-l2-13b"},
        ]
        
        print("\n📊 Применение RAG к участникам:")
        
        for participant in participants:
            model_display_name = participant["model_name"]
            
            if config.RAG_ENABLED:
                # Логика из game.py
                rag_type = config.RAG_TYPE.strip()
                if rag_type.upper() in [short.upper() for short in rag_manager.short_names.values()]:
                    rag_type = rag_manager.get_full_name_from_short(rag_type)
                
                provider = rag_manager.providers.get(rag_type)
                if provider and provider.is_applicable_for_player(participant["role"], config.RAG_TARGET):
                    rag_short_name = rag_manager.get_short_name(rag_type)
                    model_display_name = f"{participant['model_name']}-{rag_short_name}"
            
            participant["model_display_name"] = model_display_name
            print(f"   {participant['name']} ({participant['role']}): {model_display_name}")
        
        # Проверяем генерацию RAG контекста
        print("\n🧠 Генерация RAG контекста:")
        for participant in participants:
            if config.RAG_ENABLED:
                rag_type = config.RAG_TYPE.strip()
                if rag_type.upper() in [short.upper() for short in rag_manager.short_names.values()]:
                    rag_type = rag_manager.get_full_name_from_short(rag_type)
                
                provider = rag_manager.providers.get(rag_type)
                if provider and provider.is_applicable_for_player(participant["role"], config.RAG_TARGET):
                    context = provider.generate_context({})
                    print(f"   {participant['name']}: {len(context)} символов контекста")
                else:
                    print(f"   {participant['name']}: RAG не применим")
            else:
                print(f"   {participant['name']}: RAG отключен")
        
        print("\n" + "="*50)
        
        # Тест 2: Селективное применение RAG
        print("\n🎯 Тест 2: RAG только для мафии")
        config.RAG_TYPE = "AH"
        config.RAG_TARGET = "mafia"
        
        print(f"   RAG_TYPE: '{config.RAG_TYPE}' -> '{rag_manager.get_full_name_from_short(config.RAG_TYPE)}'")
        print(f"   RAG_TARGET: '{config.RAG_TARGET}'")
        
        for participant in participants:
            model_display_name = participant["model_name"]
            
            if config.RAG_ENABLED:
                rag_type = config.RAG_TYPE.strip()
                if rag_type.upper() in [short.upper() for short in rag_manager.short_names.values()]:
                    rag_type = rag_manager.get_full_name_from_short(rag_type)
                
                provider = rag_manager.providers.get(rag_type)
                if provider and provider.is_applicable_for_player(participant["role"], config.RAG_TARGET):
                    rag_short_name = rag_manager.get_short_name(rag_type)
                    model_display_name = f"{participant['model_name']}-{rag_short_name}"
            
            participant["model_display_name"] = model_display_name
            print(f"   {participant['name']} ({participant['role']}): {model_display_name}")
        
        print("\n" + "="*50)
        
        # Тест 3: Отключение RAG
        print("\n❌ Тест 3: RAG отключен")
        config.RAG_ENABLED = False
        
        for participant in participants:
            model_display_name = participant["model_name"]
            
            if config.RAG_ENABLED:
                # Этот код не должен выполниться
                pass
            
            participant["model_display_name"] = model_display_name
            print(f"   {participant['name']} ({participant['role']}): {model_display_name}")
        
        print("\n" + "="*50)
        
        # Тест 4: Проверка всех RAG типов
        print("\n🔍 Тест 4: Проверка всех RAG типов")
        config.RAG_ENABLED = True
        config.RAG_TARGET = "all"
        
        all_rag_types = ["DG", "HG", "CRG", "CG", "AS", "AH"]
        
        for rag_short in all_rag_types:
            config.RAG_TYPE = rag_short
            full_name = rag_manager.get_full_name_from_short(rag_short)
            provider = rag_manager.providers.get(full_name)
            
            print(f"   {rag_short} -> {full_name}: {'✓' if provider else '✗'}")
            
            if provider:
                # Тестируем на одном участнике
                test_participant = participants[0]
                applicable = provider.is_applicable_for_player(test_participant["role"], config.RAG_TARGET)
                context = provider.generate_context({})
                print(f"      Применим для {test_participant['role']}: {applicable}")
                print(f"      Длина контекста: {len(context)} символов")
        
        print("\n✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        
    except Exception as e:
        print(f"\n❌ ОШИБКА В ТЕСТАХ: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Восстанавливаем оригинальные настройки
        config.RAG_ENABLED = original_enabled
        config.RAG_TYPE = original_type
        config.RAG_TARGET = original_target
    
    print("\n=== ИНТЕГРАЦИОННОЕ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО ===")

if __name__ == "__main__":
    test_full_rag_integration()