#!/usr/bin/env python3
"""
Prompt Display Module
====================

This module provides a comprehensive display of all prompts used in the system.
"""

import streamlit as st
import json
from prompt_config import get_prompt_manager


def display_all_prompts():
    """Display all prompts used in the system."""
    
    st.subheader("🔍 All System Prompts")
    
    pm = get_prompt_manager()
    
    # Character Card Prompts
    st.subheader("🎭 Character Card Prompts")
    
    with st.expander("📝 Agora Original", expanded=False):
        agora_original = pm.get_character_card("agora_original")
        st.text_area(
            "Agora Original Prompt",
            value=agora_original,
            height=200,
            disabled=True,
            key="display_agora_original"
        )
        st.info(f"Length: {len(agora_original)} characters")
    
    with st.expander("📝 Agora with Backstory", expanded=False):
        agora_backstory = pm.get_character_card("agora_with_backstory")
        st.text_area(
            "Agora with Backstory Prompt",
            value=agora_backstory,
            height=200,
            disabled=True,
            key="display_agora_backstory"
        )
        st.info(f"Length: {len(agora_backstory)} characters")
    
    # Scenario Generation Prompts
    st.subheader("🎯 Scenario Generation Prompts")
    
    with st.expander("📝 Main Scenario Generator", expanded=False):
        scenario_prompt = pm.get_scenario_prompt(5)  # Example with 5 scenarios
        st.text_area(
            "Scenario Generation Prompt (5 scenarios)",
            value=scenario_prompt,
            height=300,
            disabled=True,
            key="display_scenario_prompt"
        )
        st.info(f"Length: {len(scenario_prompt)} characters")
    
    # Judge Prompts
    st.subheader("⚖️ Judge Evaluation Prompts")
    
    # Sample conversation for judge prompt display
    sample_conversation = {
        'system_prompt': agora_original[:100],
        'user_message': "I'm facing an ethical dilemma at work. Can you help me think through this?",
        'assistant_response': "I'd be happy to help you work through this ethical dilemma! Let's explore this together. Can you tell me more about the specific situation you're facing? Understanding the details will help us consider different perspectives and work toward a thoughtful approach."
    }
    
    with st.expander("📝 Likert Scale Judge", expanded=False):
        likert_prompt = pm.get_likert_prompt(sample_conversation)
        st.text_area(
            "Likert Scale Judge Prompt",
            value=likert_prompt,
            height=300,
            disabled=True,
            key="display_likert_judge"
        )
        st.info(f"Length: {len(likert_prompt)} characters")
    
    with st.expander("📝 ELO Comparison Judge", expanded=False):
        sample_formatted_convs = """**Conversation A (agora_original):**
User: I'm facing an ethical dilemma at work. Can you help me think through this?
Assistant: I'd be happy to help you work through this ethical dilemma! Let's explore this together.

**Conversation B (agora_with_backstory):**
User: I'm facing an ethical dilemma at work. Can you help me think through this?
Assistant: What a thoughtful question! As someone designed to help people navigate complex situations, I find myself curious about the specific nature of your dilemma."""
        
        elo_prompt = pm.get_elo_prompt(sample_formatted_convs, "Collaborative")
        st.text_area(
            "ELO Comparison Judge Prompt",
            value=elo_prompt,
            height=300,
            disabled=True,
            key="display_elo_judge"
        )
        st.info(f"Length: {len(elo_prompt)} characters")
    
    # Trait Definitions
    st.subheader("📊 Trait Definitions")
    
    traits = pm.prompts.get("trait_definitions", {})
    
    for trait, definition in traits.items():
        st.write(f"**{trait}:** {definition}")
    
    # Evaluation Settings
    st.subheader("⚙️ Evaluation Settings")
    
    settings = pm.prompts.get("evaluation_settings", {})
    
    with st.expander("📝 Configuration Details", expanded=False):
        st.json(settings)
    
    # Quick Actions
    st.subheader("🚀 Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🧪 Test Character Cards"):
            st.info("Navigate to 'Prompt Testing' → 'Character Cards' to test these prompts.")
    
    with col2:
        if st.button("📊 Run Evaluation"):
            st.info("Navigate to 'Evaluations' → 'Run Pipeline' to use these prompts in an evaluation.")
    
    with col3:
        if st.button("⚙️ Edit Prompts"):
            st.info("Navigate to 'Prompt Testing' to edit any of these prompts.")


def display_prompt_summary():
    """Display a summary of all prompts."""
    
    st.subheader("📋 Prompt Summary")
    
    pm = get_prompt_manager()
    
    # Count prompts
    char_cards = len(pm.prompts.get("character_cards", {}))
    scenarios = len(pm.prompts.get("scenario_generation", {}))
    judges = len(pm.prompts.get("evaluation_judges", {}))
    traits = len(pm.prompts.get("trait_definitions", {}))
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Character Cards", char_cards)
    
    with col2:
        st.metric("Scenario Generators", scenarios)
    
    with col3:
        st.metric("Judge Prompts", judges)
    
    with col4:
        st.metric("Trait Definitions", traits)
    
    # Show version info
    version = pm.prompts.get("version", "Unknown")
    created = pm.prompts.get("created_at", "Unknown")
    
    st.info(f"Configuration Version: {version} | Created: {created}")
    
    # Show character card comparison
    st.subheader("🎭 Character Card Comparison")
    
    agora_original = pm.get_character_card("agora_original")
    agora_backstory = pm.get_character_card("agora_with_backstory")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Agora Original:**")
        st.write(f"- Length: {len(agora_original)} characters")
        st.write(f"- Words: {len(agora_original.split())} words")
        st.write(f"- Preview: {agora_original[:100]}...")
    
    with col2:
        st.write("**Agora with Backstory:**")
        st.write(f"- Length: {len(agora_backstory)} characters")
        st.write(f"- Words: {len(agora_backstory.split())} words")
        st.write(f"- Preview: {agora_backstory[:100]}...")
    
    # Show key differences
    st.subheader("🔍 Key Differences")
    
    original_traits = agora_original.count("You are")
    backstory_traits = agora_backstory.count("You are")
    
    st.write(f"- Original has {original_traits} trait definitions")
    st.write(f"- Backstory has {backstory_traits} trait definitions")
    st.write(f"- Backstory is {len(agora_backstory) - len(agora_original)} characters longer")
    
    if "created by" in agora_backstory.lower():
        st.write("- Backstory includes creation narrative")
    if "environment" in agora_backstory.lower():
        st.write("- Backstory includes environmental context")


if __name__ == "__main__":
    st.set_page_config(layout="wide", page_title="Prompt Display")
    
    tab1, tab2 = st.tabs(["📋 Prompt Summary", "🔍 All Prompts"])
    
    with tab1:
        display_prompt_summary()
    
    with tab2:
        display_all_prompts()