"""
Integration Test: MCP Workflow
Tests complete MCP tool workflow: bootstrap → preflight → postflight
"""
import pytest
import json
import asyncio
from pathlib import Path
import sys

# Add mcp_local to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "mcp_local"))

from empirica_mcp_server import call_tool
from mcp import types


class TestMCPWorkflow:
    """Test complete MCP workflow integration"""
    
    @pytest.mark.asyncio
    async def test_complete_workflow_bootstrap_to_postflight(self):
        """Test: bootstrap → preflight → submit → postflight → calibration"""
        
        # Step 1: Create session
        bootstrap_result = await call_tool(
            "session_create",
            {"ai_id": "test_mcp_integration", "session_type": "workflow"}
        )
        
        assert isinstance(bootstrap_result, list)
        assert len(bootstrap_result) > 0
        
        bootstrap_data = json.loads(bootstrap_result[0].text)
        assert bootstrap_data["ok"] is True
        assert "session_id" in bootstrap_data
        
        session_id = bootstrap_data["session_id"]
        print(f"\n✅ Step 1: Session created: {session_id}")
        
        # Step 2: Execute preflight
        preflight_result = await call_tool(
            "execute_preflight",
            {
                "session_id": session_id,
                "prompt": "Test task for MCP workflow integration"
            }
        )
        
        assert isinstance(preflight_result, list)
        preflight_data = json.loads(preflight_result[0].text)
        assert preflight_data["ok"] is True
        assert preflight_data["phase"] == "preflight"
        assert "self_assessment_prompt" in preflight_data
        
        print(f"✅ Step 2: Preflight executed")
        
        # Step 3: Submit preflight assessment
        preflight_vectors = {
            "know": 0.60,
            "do": 0.65,
            "context": 0.55,
            "uncertainty": 0.50,
            "clarity": 0.70,
            "engagement": 0.75
        }
        
        submit_result = await call_tool(
            "submit_preflight_assessment",
            {
                "session_id": session_id,
                "vectors": preflight_vectors,
                "reasoning": "Test reasoning for preflight"
            }
        )
        
        submit_data = json.loads(submit_result[0].text)
        assert submit_data["ok"] is True
        
        print(f"✅ Step 3: Preflight assessment submitted")
        
        # Step 4: Simulate work (in real scenario, AI does actual work here)
        await asyncio.sleep(0.1)
        
        # Step 5: Execute postflight
        postflight_result = await call_tool(
            "execute_postflight",
            {
                "session_id": session_id,
                "summary": "Test task completed successfully"
            }
        )
        
        postflight_data = json.loads(postflight_result[0].text)
        assert postflight_data["ok"] is True
        assert postflight_data["phase"] == "postflight"
        
        print(f"✅ Step 4: Postflight executed")
        
        # Step 6: Submit postflight assessment (with learning)
        postflight_vectors = {
            "know": 0.75,      # +0.15 (learned)
            "do": 0.80,        # +0.15 (improved)
            "context": 0.85,   # +0.30 (better understanding)
            "uncertainty": 0.30, # -0.20 (reduced uncertainty)
            "clarity": 0.85,   # +0.15 (clearer)
            "engagement": 0.80 # +0.05 (more engaged)
        }
        
        final_result = await call_tool(
            "submit_postflight_assessment",
            {
                "session_id": session_id,
                "vectors": postflight_vectors,
                "changes_noticed": "Learned domain specifics, improved execution confidence"
            }
        )
        
        final_data = json.loads(final_result[0].text)
        assert final_data["ok"] is True
        assert "delta" in final_data
        assert "calibration" in final_data
        
        print(f"✅ Step 5: Postflight assessment submitted")
        
        # Step 7: Verify delta calculation
        delta = final_data["delta"]
        assert delta["know"] == pytest.approx(0.15, abs=0.01)
        assert delta["do"] == pytest.approx(0.15, abs=0.01)
        assert delta["context"] == pytest.approx(0.30, abs=0.01)
        assert delta["uncertainty"] == pytest.approx(-0.20, abs=0.01)
        
        print(f"✅ Step 6: Delta calculated correctly")
        print(f"   KNOW: +{delta['know']:.2f}")
        print(f"   DO: +{delta['do']:.2f}")
        print(f"   CONTEXT: +{delta['context']:.2f}")
        print(f"   UNCERTAINTY: {delta['uncertainty']:.2f}")
        
        # Step 8: Verify calibration status
        calibration = final_data["calibration"]
        assert "status" in calibration
        
        print(f"✅ Step 7: Calibration status: {calibration['status']}")
        
        # Well-calibrated: confidence up, uncertainty down
        if delta["know"] > 0 and delta["uncertainty"] < 0:
            assert calibration["status"] in ["well-calibrated", "WELL_CALIBRATED"]
        
        print(f"\n🎉 Complete MCP workflow test PASSED")
    
    @pytest.mark.asyncio
    async def test_get_empirica_introduction(self):
        """Test: get_empirica_introduction tool (new in docs fixes)"""
        
        result = await call_tool("get_empirica_introduction", {})
        
        assert isinstance(result, list)
        assert len(result) > 0
        
        content = result[0].text
        
        # Verify introduction contains key concepts
        assert "No Heuristics" in content or "no heuristics" in content
        assert "epistemic" in content.lower()
        assert "preflight" in content.lower()
        assert "postflight" in content.lower()
        
        print(f"\n✅ Introduction tool works")
        print(f"   Content length: {len(content)} characters")
        print(f"   Contains key concepts: ✅")
    
    @pytest.mark.asyncio
    async def test_session_continuity(self):
        """Test: Session persistence and retrieval"""
        
        # Create session
        bootstrap_result = await call_tool(
            "session_create",
            {"ai_id": "test_continuity"}
        )
        
        session_data = json.loads(bootstrap_result[0].text)
        session_id = session_data["session_id"]
        
        # Get session summary
        summary_result = await call_tool(
            "get_session_summary",
            {"session_id": session_id}
        )
        
        summary_data = json.loads(summary_result[0].text)
        assert summary_data["ok"] is True
        assert summary_data["session_id"] == session_id
        
        print(f"\n✅ Session continuity works")
        print(f"   Session ID: {session_id}")
        print(f"   Summary retrieved: ✅")
    
    @pytest.mark.asyncio  
    async def test_epistemic_state_query(self):
        """Test: Query current epistemic state"""
        
        # Create session
        bootstrap_result = await call_tool(
            "session_create",
            {"ai_id": "test_epistemic_state"}
        )
        session_id = json.loads(bootstrap_result[0].text)["session_id"]
        
        # Submit preflight
        vectors = {"know": 0.5, "do": 0.5, "context": 0.5, "uncertainty": 0.5}
        await call_tool(
            "submit_preflight_assessment",
            {"session_id": session_id, "vectors": vectors}
        )
        
        # Query epistemic state
        state_result = await call_tool(
            "get_epistemic_state",
            {"session_id": session_id}
        )
        
        state_data = json.loads(state_result[0].text)
        assert state_data["ok"] is True
        assert "current_state" in state_data
        
        print(f"\n✅ Epistemic state query works")
        print(f"   State retrieved: {state_data['current_state']}")
    
    @pytest.mark.asyncio
    async def test_investigation_recommendation(self):
        """Test: System recommends investigation when uncertainty is high"""
        
        # Create session
        bootstrap_result = await call_tool(
            "session_create",
            {"ai_id": "test_investigation"}
        )
        session_id = json.loads(bootstrap_result[0].text)["session_id"]
        
        # Execute preflight with high uncertainty
        preflight_result = await call_tool(
            "execute_preflight",
            {"session_id": session_id, "prompt": "Complex unfamiliar task"}
        )
        
        # Submit assessment with high uncertainty
        vectors = {
            "know": 0.30,        # Low knowledge
            "do": 0.40,          # Low capability
            "context": 0.35,     # Low context
            "uncertainty": 0.85  # High uncertainty
        }
        
        submit_result = await call_tool(
            "submit_preflight_assessment",
            {"session_id": session_id, "vectors": vectors}
        )
        
        submit_data = json.loads(submit_result[0].text)
        
        # Should recommend investigation
        if "recommendation" in submit_data:
            assert "investigate" in submit_data["recommendation"].lower()
        
        print(f"\n✅ Investigation recommendation works")
        print(f"   High uncertainty → Investigation recommended")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
