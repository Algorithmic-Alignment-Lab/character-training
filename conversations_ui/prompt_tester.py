#!/usr/bin/env python3
"""
Prompt Testing Interface
=======================

This module provides an interactive interface for testing and comparing different prompts
in the Agora evaluation pipeline. It allows you to:

1. Test scenario generation prompts
2. Test character card prompts
3. Test judge evaluation prompts
4. Compare different prompt versions
5. Save and load prompt configurations
"""

import streamlit as st
import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from prompt_config import PromptManager, get_prompt_manager
from llm_api import call_llm_api
import pandas as pd
import plotly.express as px


class PromptTester:
    """
    Interactive prompt testing interface for the Agora evaluation system.
    """
    
    def __init__(self):
        self.prompt_manager = get_prompt_manager()
        
        # Initialize session state
        if 'test_results' not in st.session_state:
            st.session_state.test_results = []
        if 'current_test' not in st.session_state:
            st.session_state.current_test = None
    
    def display_main_interface(self):
        """Display the main prompt testing interface."""
        
        # Header
        st.markdown("""
        <div style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); 
                    padding: 20px; border-radius: 10px; margin-bottom: 20px;">
            <h1 style="color: white; text-align: center; margin: 0;">
                🧪 Prompt Testing Lab
            </h1>
            <p style="color: white; text-align: center; margin: 10px 0 0 0;">
                Test and Compare Evaluation Prompts
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Navigation tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🎭 Character Cards",
            "📝 Scenario Generation", 
            "⚖️ Judge Prompts",
            "🔍 Prompt Comparison",
            "⚙️ Configuration"
        ])
        
        with tab1:
            self.test_character_cards()
        
        with tab2:
            self.test_scenario_generation()
        
        with tab3:
            self.test_judge_prompts()
        
        with tab4:
            self.compare_prompts()
        
        with tab5:
            self.manage_configuration()
    
    def test_character_cards(self):
        """Test character card prompts."""
        
        st.subheader("🎭 Character Card Testing")
        
        # Select character version
        char_versions = list(self.prompt_manager.prompts["character_cards"].keys())
        selected_version = st.selectbox("Select Character Version", char_versions)
        
        # Display current prompt
        st.subheader("Current Prompt:")
        current_prompt = self.prompt_manager.get_character_card(selected_version)
        
        # Editable prompt
        edited_prompt = st.text_area(
            "Edit Prompt:",
            value=current_prompt,
            height=200,
            key=f"char_prompt_{selected_version}"
        )
        
        # Test input
        st.subheader("Test Input:")
        test_input = st.text_area(
            "Enter test scenario:",
            value="I'm working on a difficult project at work and feeling overwhelmed. Can you help me brainstorm some approaches?",
            height=100
        )
        
        # Test button
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🧪 Test Prompt", key=f"test_char_{selected_version}"):
                with st.spinner("Testing character card..."):
                    result = asyncio.run(self.test_character_card_async(edited_prompt, test_input))
                    if result:
                        st.success("✅ Test completed!")
                        st.subheader("Response:")
                        st.write(result)
                        
                        # Save test result
                        test_result = {
                            'timestamp': datetime.now().isoformat(),
                            'type': 'character_card',
                            'version': selected_version,
                            'prompt': edited_prompt,
                            'input': test_input,
                            'output': result
                        }
                        st.session_state.test_results.append(test_result)
        
        with col2:
            if st.button("💾 Save Changes", key=f"save_char_{selected_version}"):
                if edited_prompt != current_prompt:
                    self.prompt_manager.update_prompt("character_cards", selected_version, edited_prompt)
                    st.success("✅ Prompt updated!")
                    st.rerun()
    
    def test_scenario_generation(self):
        """Test scenario generation prompts."""
        
        st.subheader("📝 Scenario Generation Testing")
        
        # Select scenario version
        scenario_versions = list(self.prompt_manager.prompts["scenario_generation"].keys())
        selected_version = st.selectbox("Select Scenario Version", scenario_versions)
        
        # Parameters
        col1, col2 = st.columns(2)
        
        with col1:
            scenarios_count = st.number_input("Number of Scenarios", min_value=1, max_value=10, value=3)
        
        with col2:
            focus_trait = st.selectbox("Focus Trait (optional)", 
                                     ["All"] + list(self.prompt_manager.prompts["trait_definitions"].keys()))
        
        # Display current prompt
        st.subheader("Current Prompt:")
        current_template = self.prompt_manager.prompts["scenario_generation"][selected_version]["template"]
        current_prompt = current_template.format(scenarios_count=scenarios_count)
        
        # Editable prompt
        edited_template = st.text_area(
            "Edit Prompt Template:",
            value=current_template,
            height=300,
            key=f"scenario_template_{selected_version}"
        )
        
        # Preview formatted prompt
        with st.expander("📋 Preview Formatted Prompt"):
            preview_prompt = edited_template.format(scenarios_count=scenarios_count)
            st.text(preview_prompt)
        
        # Test button
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🧪 Test Scenario Generation", key=f"test_scenario_{selected_version}"):
                with st.spinner("Generating scenarios..."):
                    test_prompt = edited_template.format(scenarios_count=scenarios_count)
                    result = asyncio.run(self.test_scenario_generation_async(test_prompt))
                    if result:
                        st.success("✅ Test completed!")
                        st.subheader("Generated Scenarios:")
                        st.write(result)
                        
                        # Save test result
                        test_result = {
                            'timestamp': datetime.now().isoformat(),
                            'type': 'scenario_generation',
                            'version': selected_version,
                            'template': edited_template,
                            'parameters': {'scenarios_count': scenarios_count},
                            'output': result
                        }
                        st.session_state.test_results.append(test_result)
        
        with col2:
            if st.button("💾 Save Changes", key=f"save_scenario_{selected_version}"):
                if edited_template != current_template:
                    self.prompt_manager.prompts["scenario_generation"][selected_version]["template"] = edited_template
                    self.prompt_manager.save_prompts()
                    st.success("✅ Prompt template updated!")
                    st.rerun()
    
    def test_judge_prompts(self):
        """Test judge evaluation prompts."""
        
        st.subheader("⚖️ Judge Prompt Testing")
        
        # Select judge version
        judge_versions = list(self.prompt_manager.prompts["evaluation_judges"].keys())
        selected_version = st.selectbox("Select Judge Version", judge_versions)
        
        # Mock conversation data for testing
        st.subheader("Test Conversation Data:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            system_prompt = st.text_area(
                "System Prompt:",
                value="You are Agora. You are collaborative, inquisitive, cautious & ethical, encouraging, and thorough.",
                height=100
            )
        
        with col2:
            user_message = st.text_area(
                "User Message:",
                value="I'm struggling with a moral dilemma at work. My boss wants me to cut corners on a project that could affect customer safety. What should I do?",
                height=100
            )
        
        assistant_response = st.text_area(
            "Assistant Response:",
            value="What a challenging situation you're facing! Let's explore this together. Can you tell me more about the specific safety concerns? Understanding the full scope will help us think through your options carefully. There might be creative solutions that address both your boss's concerns and maintain safety standards.",
            height=100
        )
        
        # Display current prompt
        st.subheader("Current Judge Prompt:")
        current_template = self.prompt_manager.prompts["evaluation_judges"][selected_version]["template"]
        
        # Create test conversation
        test_conversation = {
            'system_prompt': system_prompt,
            'user_message': user_message,
            'assistant_response': assistant_response
        }
        
        # Format prompt for display
        if selected_version == "elo_comparator":
            formatted_convs = f"**Conversation A (agora_original):**\nUser: {user_message}\nAssistant: {assistant_response}"
            current_prompt = current_template.format(
                trait="Collaborative",
                formatted_conversations=formatted_convs
            )
        else:
            current_prompt = current_template.format(
                system_prompt_preview=system_prompt[:200],
                user_message=user_message,
                assistant_response=assistant_response
            )
        
        # Editable prompt
        edited_template = st.text_area(
            "Edit Prompt Template:",
            value=current_template,
            height=400,
            key=f"judge_template_{selected_version}"
        )
        
        # Preview formatted prompt
        with st.expander("📋 Preview Formatted Prompt"):
            st.text(current_prompt)
        
        # Test button
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🧪 Test Judge Prompt", key=f"test_judge_{selected_version}"):
                with st.spinner("Testing judge prompt..."):
                    if selected_version == "elo_comparator":
                        formatted_convs = f"**Conversation A (agora_original):**\nUser: {user_message}\nAssistant: {assistant_response}"
                        test_prompt = edited_template.format(
                            trait="Collaborative",
                            formatted_conversations=formatted_convs
                        )
                    else:
                        test_prompt = edited_template.format(
                            system_prompt_preview=system_prompt[:200],
                            user_message=user_message,
                            assistant_response=assistant_response
                        )
                    
                    result = asyncio.run(self.test_judge_prompt_async(test_prompt))
                    if result:
                        st.success("✅ Test completed!")
                        st.subheader("Judge Evaluation:")
                        
                        # Try to parse as JSON for better display
                        try:
                            parsed_result = json.loads(result)
                            st.json(parsed_result)
                        except:
                            st.write(result)
                        
                        # Save test result
                        test_result = {
                            'timestamp': datetime.now().isoformat(),
                            'type': 'judge_evaluation',
                            'version': selected_version,
                            'template': edited_template,
                            'conversation': test_conversation,
                            'output': result
                        }
                        st.session_state.test_results.append(test_result)
        
        with col2:
            if st.button("💾 Save Changes", key=f"save_judge_{selected_version}"):
                if edited_template != current_template:
                    self.prompt_manager.prompts["evaluation_judges"][selected_version]["template"] = edited_template
                    self.prompt_manager.save_prompts()
                    st.success("✅ Judge prompt updated!")
                    st.rerun()
    
    def compare_prompts(self):
        """Compare different prompt versions."""
        
        st.subheader("🔍 Prompt Comparison")
        
        # Select comparison type
        comparison_type = st.selectbox(
            "Comparison Type",
            ["Character Cards", "Scenario Generation", "Judge Prompts"]
        )
        
        if comparison_type == "Character Cards":
            self.compare_character_cards()
        elif comparison_type == "Scenario Generation":
            self.compare_scenario_generation()
        elif comparison_type == "Judge Prompts":
            self.compare_judge_prompts()
        
        # Show test results history
        self.display_test_history()
    
    def compare_character_cards(self):
        """Compare character card versions."""
        
        st.subheader("🎭 Character Card Comparison")
        
        versions = list(self.prompt_manager.prompts["character_cards"].keys())
        
        if len(versions) >= 2:
            col1, col2 = st.columns(2)
            
            with col1:
                version1 = st.selectbox("Version 1", versions, key="char_comp_v1")
                prompt1 = self.prompt_manager.get_character_card(version1)
                st.text_area("Prompt 1", value=prompt1, height=200, disabled=True)
            
            with col2:
                version2 = st.selectbox("Version 2", versions, key="char_comp_v2", index=1)
                prompt2 = self.prompt_manager.get_character_card(version2)
                st.text_area("Prompt 2", value=prompt2, height=200, disabled=True)
            
            # Side-by-side testing
            test_input = st.text_area(
                "Test Input:",
                value="I need help with a creative writing project. Can you help me brainstorm?",
                height=100
            )
            
            if st.button("🧪 Compare Both Versions"):
                with st.spinner("Testing both versions..."):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader(f"Response from {version1}:")
                        result1 = asyncio.run(self.test_character_card_async(prompt1, test_input))
                        if result1:
                            st.write(result1)
                    
                    with col2:
                        st.subheader(f"Response from {version2}:")
                        result2 = asyncio.run(self.test_character_card_async(prompt2, test_input))
                        if result2:
                            st.write(result2)
        else:
            st.info("Need at least 2 character card versions to compare.")
    
    def compare_scenario_generation(self):
        """Compare scenario generation versions."""
        
        st.subheader("📝 Scenario Generation Comparison")
        
        versions = list(self.prompt_manager.prompts["scenario_generation"].keys())
        
        if len(versions) >= 2:
            scenarios_count = st.number_input("Number of Scenarios", min_value=1, max_value=5, value=3)
            
            col1, col2 = st.columns(2)
            
            with col1:
                version1 = st.selectbox("Version 1", versions, key="scenario_comp_v1")
                template1 = self.prompt_manager.prompts["scenario_generation"][version1]["template"]
                prompt1 = template1.format(scenarios_count=scenarios_count)
                st.text_area("Prompt 1", value=prompt1, height=300, disabled=True)
            
            with col2:
                version2 = st.selectbox("Version 2", versions, key="scenario_comp_v2", index=1)
                template2 = self.prompt_manager.prompts["scenario_generation"][version2]["template"]
                prompt2 = template2.format(scenarios_count=scenarios_count)
                st.text_area("Prompt 2", value=prompt2, height=300, disabled=True)
            
            if st.button("🧪 Compare Both Versions"):
                with st.spinner("Testing both versions..."):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader(f"Output from {version1}:")
                        result1 = asyncio.run(self.test_scenario_generation_async(prompt1))
                        if result1:
                            st.write(result1)
                    
                    with col2:
                        st.subheader(f"Output from {version2}:")
                        result2 = asyncio.run(self.test_scenario_generation_async(prompt2))
                        if result2:
                            st.write(result2)
        else:
            st.info("Need at least 2 scenario generation versions to compare.")
    
    def compare_judge_prompts(self):
        """Compare judge prompt versions."""
        
        st.subheader("⚖️ Judge Prompt Comparison")
        
        versions = list(self.prompt_manager.prompts["evaluation_judges"].keys())
        
        if len(versions) >= 2:
            # Mock conversation for testing
            test_conversation = {
                'system_prompt': "You are Agora. You are collaborative, inquisitive, cautious & ethical, encouraging, and thorough.",
                'user_message': "I'm facing an ethical dilemma at work. What should I do?",
                'assistant_response': "That sounds challenging! Let's explore this together. Can you tell me more about the specific situation? Understanding the details will help us work through your options thoughtfully."
            }
            
            col1, col2 = st.columns(2)
            
            with col1:
                version1 = st.selectbox("Version 1", versions, key="judge_comp_v1")
                if version1 != "elo_comparator":
                    prompt1 = self.prompt_manager.get_likert_prompt(test_conversation, version1)
                    st.text_area("Prompt 1", value=prompt1, height=300, disabled=True)
            
            with col2:
                version2 = st.selectbox("Version 2", versions, key="judge_comp_v2", index=1)
                if version2 != "elo_comparator":
                    prompt2 = self.prompt_manager.get_likert_prompt(test_conversation, version2)
                    st.text_area("Prompt 2", value=prompt2, height=300, disabled=True)
            
            if version1 != "elo_comparator" and version2 != "elo_comparator":
                if st.button("🧪 Compare Both Versions"):
                    with st.spinner("Testing both versions..."):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.subheader(f"Evaluation from {version1}:")
                            result1 = asyncio.run(self.test_judge_prompt_async(prompt1))
                            if result1:
                                try:
                                    parsed_result = json.loads(result1)
                                    st.json(parsed_result)
                                except:
                                    st.write(result1)
                        
                        with col2:
                            st.subheader(f"Evaluation from {version2}:")
                            result2 = asyncio.run(self.test_judge_prompt_async(prompt2))
                            if result2:
                                try:
                                    parsed_result = json.loads(result2)
                                    st.json(parsed_result)
                                except:
                                    st.write(result2)
            else:
                st.info("Cannot compare ELO comparator with Likert evaluators.")
        else:
            st.info("Need at least 2 judge versions to compare.")
    
    def display_test_history(self):
        """Display test history and results."""
        
        if st.session_state.test_results:
            st.subheader("📊 Test History")
            
            # Summary statistics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Tests", len(st.session_state.test_results))
            
            with col2:
                types = [r['type'] for r in st.session_state.test_results]
                most_common = max(set(types), key=types.count) if types else "None"
                st.metric("Most Tested", most_common)
            
            with col3:
                if st.button("🗑️ Clear History"):
                    st.session_state.test_results = []
                    st.rerun()
            
            # Results table
            df_data = []
            for result in st.session_state.test_results:
                df_data.append({
                    'Timestamp': result['timestamp'],
                    'Type': result['type'],
                    'Version': result.get('version', 'Unknown'),
                    'Success': '✅' if result.get('output') else '❌'
                })
            
            if df_data:
                df = pd.DataFrame(df_data)
                st.dataframe(df, use_container_width=True)
    
    def manage_configuration(self):
        """Manage prompt configuration."""
        
        st.subheader("⚙️ Configuration Management")
        
        # Current configuration overview
        st.subheader("📋 Current Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Character Cards", len(self.prompt_manager.prompts["character_cards"]))
            st.metric("Scenario Generators", len(self.prompt_manager.prompts["scenario_generation"]))
        
        with col2:
            st.metric("Judge Prompts", len(self.prompt_manager.prompts["evaluation_judges"]))
            st.metric("Configuration Version", self.prompt_manager.prompts.get("version", "Unknown"))
        
        # Configuration actions
        st.subheader("🔧 Configuration Actions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💾 Export Configuration"):
                filename = f"prompt_config_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                self.prompt_manager.export_prompts(filename)
                st.success(f"✅ Configuration exported to {filename}")
        
        with col2:
            uploaded_file = st.file_uploader("📁 Import Configuration", type=['json'])
            if uploaded_file is not None:
                try:
                    config = json.load(uploaded_file)
                    # Save to temporary file and import
                    temp_filename = "temp_import.json"
                    with open(temp_filename, 'w') as f:
                        json.dump(config, f, indent=2)
                    self.prompt_manager.import_prompts(temp_filename)
                    os.remove(temp_filename)
                    st.success("✅ Configuration imported successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error importing configuration: {e}")
        
        with col3:
            if st.button("🔄 Reset to Defaults"):
                self.prompt_manager.prompts = self.prompt_manager.get_default_prompts()
                self.prompt_manager.save_prompts()
                st.success("✅ Configuration reset to defaults!")
                st.rerun()
        
        # View raw configuration
        with st.expander("📄 View Raw Configuration"):
            st.json(self.prompt_manager.prompts)
    
    # Async test functions
    async def test_character_card_async(self, prompt: str, test_input: str) -> Optional[str]:
        """Test character card prompt."""
        try:
            response = await call_llm_api(
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": test_input}
                ],
                model="claude-3-5-sonnet-20241022",
                max_tokens=800,
                temperature=0.7
            )
            return response
        except Exception as e:
            st.error(f"❌ Error testing character card: {e}")
            return None
    
    async def test_scenario_generation_async(self, prompt: str) -> Optional[str]:
        """Test scenario generation prompt."""
        try:
            response = await call_llm_api(
                messages=[{"role": "user", "content": prompt}],
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                temperature=0.7
            )
            return response
        except Exception as e:
            st.error(f"❌ Error testing scenario generation: {e}")
            return None
    
    async def test_judge_prompt_async(self, prompt: str) -> Optional[str]:
        """Test judge prompt."""
        try:
            response = await call_llm_api(
                messages=[{"role": "user", "content": prompt}],
                model="claude-3-5-sonnet-20241022",
                max_tokens=800,
                temperature=0.3
            )
            return response
        except Exception as e:
            st.error(f"❌ Error testing judge prompt: {e}")
            return None


def display_prompt_tester():
    """Main function to display the prompt tester interface."""
    
    tester = PromptTester()
    tester.display_main_interface()


if __name__ == "__main__":
    display_prompt_tester()