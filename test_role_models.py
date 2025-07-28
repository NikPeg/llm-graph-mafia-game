#!/usr/bin/env python3
"""
Test script to verify role-based model configuration works correctly.
"""

import os
import sys
sys.path.append('src')

# Set up test environment variables
os.environ['EXPERIMENT_MODE'] = 'role_specific'
os.environ['MAFIA_MODEL'] = 'deepseek-ai/DeepSeek-R1-Distill-Qwen-32B'
os.environ['VILLAGER_MODEL'] = 'deepseek/deepseek-llm-7b-chat'
os.environ['DOCTOR_MODEL'] = 'deepseek/deepseek-llm-7b-chat'

import config
from game_templates import Role

def test_single_mode():
    """Test single model mode"""
    print("=== Testing Single Model Mode ===")
    
    # Reset to single mode
    os.environ['EXPERIMENT_MODE'] = 'single'
    os.environ['MODEL_NAME'] = 'gryphe/mythomax-l2-13b'
    
    # Reload config
    import importlib
    importlib.reload(config)
    
    mafia_model = config.get_model_for_role('Mafia')
    villager_model = config.get_model_for_role('Villager')
    doctor_model = config.get_model_for_role('Doctor')
    
    print(f"Mafia model: {mafia_model}")
    print(f"Villager model: {villager_model}")
    print(f"Doctor model: {doctor_model}")
    
    # All should be the same
    assert mafia_model == villager_model == doctor_model == 'gryphe/mythomax-l2-13b'
    print("✅ Single mode test passed!")
    print()

def test_role_specific_mode():
    """Test role-specific model mode"""
    print("=== Testing Role-Specific Model Mode ===")
    
    # Set to role-specific mode
    os.environ['EXPERIMENT_MODE'] = 'role_specific'
    os.environ['MAFIA_MODEL'] = 'deepseek-ai/DeepSeek-R1-Distill-Qwen-32B'
    os.environ['VILLAGER_MODEL'] = 'deepseek/deepseek-llm-7b-chat'
    os.environ['DOCTOR_MODEL'] = 'deepseek/deepseek-llm-7b-chat'
    
    # Reload config
    import importlib
    importlib.reload(config)
    
    mafia_model = config.get_model_for_role('Mafia')
    villager_model = config.get_model_for_role('Villager')
    doctor_model = config.get_model_for_role('Doctor')
    
    print(f"Mafia model: {mafia_model}")
    print(f"Villager model: {villager_model}")
    print(f"Doctor model: {doctor_model}")
    
    # Should be different models
    assert mafia_model == 'deepseek-ai/DeepSeek-R1-Distill-Qwen-32B'
    assert villager_model == 'deepseek/deepseek-llm-7b-chat'
    assert doctor_model == 'deepseek/deepseek-llm-7b-chat'
    print("✅ Role-specific mode test passed!")
    print()

def test_experiment_scenarios():
    """Test different experiment scenarios"""
    print("=== Testing Experiment Scenarios ===")
    
    # Scenario 1: Smart Mafia vs Dumb Villagers
    print("Scenario 1: Smart Mafia vs Dumb Villagers")
    os.environ['EXPERIMENT_MODE'] = 'role_specific'
    os.environ['MAFIA_MODEL'] = 'deepseek-ai/DeepSeek-R1-Distill-Qwen-32B'  # Smart
    os.environ['VILLAGER_MODEL'] = 'deepseek/deepseek-llm-7b-chat'  # Simpler
    os.environ['DOCTOR_MODEL'] = 'deepseek/deepseek-llm-7b-chat'  # Simpler
    
    import importlib
    importlib.reload(config)
    
    print(f"  Mafia (smart): {config.get_model_for_role('Mafia')}")
    print(f"  Villagers (simple): {config.get_model_for_role('Villager')}")
    print(f"  Doctor (simple): {config.get_model_for_role('Doctor')}")
    print()
    
    # Scenario 2: Smart Villagers vs Dumb Mafia
    print("Scenario 2: Smart Villagers vs Dumb Mafia")
    os.environ['MAFIA_MODEL'] = 'deepseek/deepseek-llm-7b-chat'  # Simpler
    os.environ['VILLAGER_MODEL'] = 'deepseek-ai/DeepSeek-R1-Distill-Qwen-32B'  # Smart
    os.environ['DOCTOR_MODEL'] = 'deepseek-ai/DeepSeek-R1-Distill-Qwen-32B'  # Smart
    
    importlib.reload(config)
    
    print(f"  Mafia (simple): {config.get_model_for_role('Mafia')}")
    print(f"  Villagers (smart): {config.get_model_for_role('Villager')}")
    print(f"  Doctor (smart): {config.get_model_for_role('Doctor')}")
    print()

if __name__ == "__main__":
    print("Testing Role-Based Model Configuration\n")
    
    try:
        test_single_mode()
        test_role_specific_mode()
        test_experiment_scenarios()
        
        print("🎉 All tests passed! The role-based model configuration is working correctly.")
        print("\nTo use in experiments:")
        print("1. Set EXPERIMENT_MODE=role_specific in your .env file")
        print("2. Set MAFIA_MODEL, VILLAGER_MODEL, DOCTOR_MODEL to desired models")
        print("3. Run your mafia game as usual")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)