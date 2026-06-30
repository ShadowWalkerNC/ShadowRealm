import pytest
from core.agent_pipeline import TaskRouter, LangGraphResearchPipeline, AutoGenCodingPipeline, CrewAIScheduledPipeline

def test_task_router_classification():
    # Research queries
    assert TaskRouter.route("can you search the web for latest LLMs?") == "research"
    assert TaskRouter.route("find information on Python decorators") == "research"
    assert TaskRouter.route("summarize this research paper") == "research"
    
    # Coding queries
    assert TaskRouter.route("write a python script to parse CSV") == "coding"
    assert TaskRouter.route("test the code implementation") == "coding"
    assert TaskRouter.route("deploy this microservice") == "coding"
    
    # Scheduled queries (fallback/default)
    assert TaskRouter.route("check status of servers") == "scheduled"
    assert TaskRouter.route("say hello") == "scheduled"

@pytest.mark.asyncio
async def test_langgraph_research_pipeline():
    pipe = LangGraphResearchPipeline("Python 3.12 release notes", owner="test_user")
    res = await pipe.execute()
    assert res.success is True
    assert len(res.steps) == 5
    assert "Saved to Memory Tier: Cool" in res.final_output

@pytest.mark.asyncio
async def test_autogen_coding_pipeline():
    pipe = AutoGenCodingPipeline("create a simple calculator", owner="test_user")
    res = await pipe.execute()
    assert res.success is True
    assert len(res.steps) == 5
    assert "OpenHands run" in res.final_output

@pytest.mark.asyncio
async def test_crewai_scheduled_pipeline():
    pipe = CrewAIScheduledPipeline("database connection", owner="test_user")
    res = await pipe.execute()
    assert res.success is True
    assert len(res.steps) == 3
    assert "Status healthy" in res.final_output
