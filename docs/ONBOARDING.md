# ShadowRealm v2.0 Onboarding Guide

Welcome to ShadowRealm! This guide helps you configure the agent platform on first launch.

## 🛠️ Stack & Options Configuration
1. **Model Preferences**: Choose between hosted providers (Anthropic, DeepSeek, OpenAI) or a fully local stack (Ollama).
2. **Hardware Fit**:
   - **Low Resource** (e.g. 8GB RAM): Injects small models (Llama-3-8B, Mistral-7B).
   - **High Resource** (e.g. 32GB+ RAM): Injects larger models or reasoning models.
3. **Memory Import**: Migrate your memories easily from ChatGPT or Claude by exporting their JSON packages and uploading them to the Memory panel.

## 🧠 Teach Mode & The Skill Factory Loop
ShadowRealm teaches itself:
- Switch on **Teach Mode** in the sidebar.
- Execute steps and annotation turns.
- Run `/api/skills/generate` to auto-crystallize successful workflows into permanent, versioned procedural skills.
