#!/usr/bin/env python3
"""
Тест для проверки отображения RAG в дашборде.
"""

import os
import sys
import json

# Добавляем src в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_dashboard_display():
    """Тестирует отображение RAG в дашборде."""
    print("=== Тестирование отображения RAG в дашборде ===\n")
    
    # Читаем HTML шаблон
    template_path = os.path.join('src', 'templates', 'index.html')
    
    if not os.path.exists(template_path):
        print(f"Ошибка: файл {template_path} не найден")
        return
    
    with open(template_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Проверяем, что в шаблоне используется model_display_name
    if 'model_display_name' in html_content:
        print("✓ HTML шаблон использует model_display_name")
    else:
        print("✗ HTML шаблон НЕ использует model_display_name")
    
    # Проверяем fallback на model_name
    if 'model_name' in html_content:
        print("✓ HTML шаблон имеет fallback на model_name")
    else:
        print("✗ HTML шаблон НЕ имеет fallback на model_name")
    
    print()
    
    # Симулируем данные игры с RAG
    game_data = {
        "participants": [
            {
                "name": "Player1",
                "role": "Mafia",
                "model_name": "gryphe/mythomax-l2-13b",
                "model_display_name": "gryphe/mythomax-l2-13b-DG",
                "status": "alive"
            },
            {
                "name": "Player2", 
                "role": "Doctor",
                "model_name": "gryphe/mythomax-l2-13b",
                "model_display_name": "gryphe/mythomax-l2-13b-DG",
                "status": "alive"
            },
            {
                "name": "Player3",
                "role": "Villager", 
                "model_name": "gryphe/mythomax-l2-13b",
                "model_display_name": "gryphe/mythomax-l2-13b",  # Без RAG
                "status": "dead"
            }
        ]
    }
    
    print("Симулированные данные участников:")
    for p in game_data["participants"]:
        display_name = p.get("model_display_name", p["model_name"])
        print(f"  {p['name']}: {display_name} ({p['role']}) - {p['status']}")
    
    print()
    
    # Проверяем логику отображения как в JavaScript
    print("Логика отображения в дашборде:")
    for p in game_data["participants"]:
        # Симулируем JavaScript логику: participant.model_display_name || participant.model_name
        display_name = p.get("model_display_name") or p["model_name"]
        print(f"  {p['name']}: {display_name}")
    
    print()
    
    # Тест без model_display_name (старые данные)
    print("=== Тест совместимости со старыми данными ===")
    old_game_data = {
        "participants": [
            {
                "name": "OldPlayer1",
                "role": "Mafia",
                "model_name": "gryphe/mythomax-l2-13b",
                "status": "alive"
                # Нет model_display_name
            }
        ]
    }
    
    for p in old_game_data["participants"]:
        display_name = p.get("model_display_name") or p["model_name"]
        print(f"  {p['name']}: {display_name} (fallback to model_name)")
    
    print("\n=== Тестирование завершено ===")

if __name__ == "__main__":
    test_dashboard_display()