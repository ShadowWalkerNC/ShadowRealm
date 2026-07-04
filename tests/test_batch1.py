import pytest
from core.workflow_definition import WorkflowDefinition, WorkflowNode, WorkflowEdge
from core.workflow_executor import WorkflowExecutor
from core.workflow_registry import WorkflowRegistry
from core.pipeline_builder import PipelineBuilder
from core.data_transformer import DataTransformer
from core.pipeline_scheduler import PipelineScheduler

@pytest.mark.asyncio
async def test_workflow_execution():
    node1 = WorkflowNode(id="n1", type="trigger")
    node2 = WorkflowNode(id="n2", type="action")
    edge = WorkflowEdge(from_node="n1", to_node="n2")
    
    definition = WorkflowDefinition(id="wf1", name="Test Workflow", nodes=[node1, node2], edges=[edge])
    
    registry = WorkflowRegistry()
    registry.register(definition)
    
    assert registry.get("wf1") == definition
    
    executor = WorkflowExecutor(definition)
    res = await executor.execute({"input": "val"})
    assert res["n2_output"] == "Processed n2"

def test_pipeline_transform_and_schedule():
    builder = PipelineBuilder()
    builder.add_step(lambda x: x * 2)
    builder.add_step(lambda x: x + 10)
    
    scheduler = PipelineScheduler()
    scheduler.schedule("p1", "*/5 * * * *", builder)
    
    res = scheduler.trigger("p1", 5)
    assert res == 20  # (5 * 2) + 10 = 20

def test_data_transformer():
    mapped = DataTransformer.map(lambda x: x + 1, [1, 2, 3])
    filtered = DataTransformer.filter(lambda x: x % 2 == 0, [1, 2, 3, 4])
    
    assert mapped == [2, 3, 4]
    assert filtered == [2, 4]
