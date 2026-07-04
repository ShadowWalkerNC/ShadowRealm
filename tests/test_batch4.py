import pytest
from core.soul_loader import SoulLoader
from core.agent_identity import AgentIdentity
from core.pantheon_router import PantheonRouter
from core.memory_vault import MemoryVault
from core.context_compressor import ContextCompressor
from core.memory_sync_agent import MemorySyncAgent
from core.command_parser import CommandParser
from core.goal_budget import GoalBudget
from core.sub_agent_orchestrator import SubAgentOrchestrator
from core.model_router import ModelRouter
from core.channel_router import ChannelRouter
from core.os_action_executor import OSActionExecutor
from core.prompt_normalizer import PromptNormalizer
from core.intent_classifier import IntentClassifier
from core.reasoning_engine import ReasoningEngine
from core.self_reflection_loop import SelfReflectionLoop
from core.token_budget_manager import TokenBudgetManager
from core.domain_model_registry import DomainModelRegistry
from core.workspace_exporter import WorkspaceExporter
from core.community_skill_library import CommunitySkillLibrary
from core.skill_trainer import SkillTrainer

def test_soul_and_identity():
    soul = SoulLoader.load_soul("invalid_path.md")
    assert soul["name"] == "ShadowRealm Agent"
    
    identity = AgentIdentity("ShadowCoder", ["coding", "review"])
    prompt = identity.format_system_prompt("hello")
    assert "Identity: ShadowCoder" in prompt
    
    routed = PantheonRouter.route_task("write code", [{"name": "coder", "tags": ["code"]}])
    assert routed["name"] == "coder"

def test_memory_and_compressor():
    vault = MemoryVault()
    entry = vault.commit("User logged in", tier="warm")
    assert entry["tier"] == "warm"
    assert len(vault.query("User")) == 1
    
    msgs = [{"role": "user", "content": "hi"}] * 10
    compressed = ContextCompressor.compress_messages(msgs, threshold=5)
    assert len(compressed) == 6
    
    sync = MemorySyncAgent("my-repo")
    assert sync.sync_vault([]) is True

def test_parser_and_budgets():
    cmd, arg = CommandParser.parse_command("/compress 50")
    assert cmd == "compress"
    assert arg == "50"
    
    budget = GoalBudget(max_turns=2)
    assert budget.consume_turn() is True
    assert budget.consume_turn() is True
    assert budget.consume_turn() is False
    
    orch = SubAgentOrchestrator()
    task_id = orch.spawn_sub_agent("sub-bot", "fix logs")
    assert task_id == "task-1"

def test_routers_and_executors():
    mr = ModelRouter(offline=True)
    assert mr.route_query("any") == "ollama"
    
    dispatch = ChannelRouter.dispatch_message("matrix", "hello")
    assert dispatch["status"] == "dispatched"
    
    executor = OSActionExecutor(allowed_commands=["git"])
    assert executor.execute_command("git commit")["status"] == "executed"
    assert executor.execute_command("rm -rf")["status"] == "blocked"

def test_intelligence_and_trainer():
    norm = PromptNormalizer.normalize("  HELLO WORLD!  ")
    assert norm == "hello world!"
    
    intent = IntentClassifier.classify_intent("how to write code")
    assert intent == "code"
    
    engine = ReasoningEngine("coder")
    assert len(engine.run_react("hello")) == 4
    
    reflection = SelfReflectionLoop.evaluate_execution(1, "error message")
    assert reflection["status"] == "unstable"
    
    tbm = TokenBudgetManager(limit=50)
    assert tbm.record_usage(40) is True
    assert tbm.record_usage(20) is False
    
    registry = DomainModelRegistry()
    assert registry.get_model_for_domain("coding") == "deepseek-coder"
    
    export = WorkspaceExporter.export_workspace("dest.zip")
    assert export["status"] == "success"
    
    csl = CommunitySkillLibrary()
    assert len(csl.fetch_community_skills()) == 1
    
    trainer = SkillTrainer()
    assert trainer.advance_stage() == "Practice"
