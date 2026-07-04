import pytest
from core.media_processor import MediaProcessor
from core.transcription_adapter import TranscriptionAdapter
from core.vision_adapter import VisionAdapter
from core.test_harness import TestHarness
from core.mock_tool_registry import MockToolRegistry
from core.regression_tracker import RegressionTracker

def test_media_and_adapters():
    meta = MediaProcessor.extract_metadata("test_image.png")
    assert meta["format"] == "PNG"
    
    converted = MediaProcessor.convert_format("sound.wav", "MP3")
    assert converted == "sound.mp3"
    
    ta = TranscriptionAdapter()
    assert "Whisper" in ta.transcribe(b"data")
    
    va = VisionAdapter()
    res = va.analyze_image(b"data", "find buttons")
    assert "detected_objects" in res

def test_test_harness_and_mocks():
    mock_reg = MockToolRegistry()
    mock_reg.register_mock("search", lambda q: f"mocked {q}")
    assert mock_reg.call_mock("search", "query") == "mocked query"
    
    def dummy_agent():
        # Executes successfully
        pass
        
    result = TestHarness.run_agent_test(dummy_agent)
    assert result["success"] is True
    
    def failing_agent():
        raise ValueError("failing")
        
    result2 = TestHarness.run_agent_test(failing_agent)
    assert result2["success"] is False

def test_regression_tracker():
    tracker = RegressionTracker()
    tracker.log_result("test_task", True)
    tracker.log_result("test_task", False)
    
    assert tracker.get_success_rate("test_task") == 0.5
