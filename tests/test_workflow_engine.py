import pytest
from core.workflow_engine import WorkflowEngine, WORKFLOWS


class TestWorkflowEngine:
    def test_list_workflows_not_empty(self):
        workflows = WorkflowEngine.list_workflows()
        assert len(workflows) >= 6

    def test_workflow_has_required_fields(self):
        for name, wf in WORKFLOWS.items():
            assert "name" in wf
            assert "description" in wf
            assert "phases" in wf
            assert len(wf["phases"]) > 0

    def test_get_workflow_exists(self):
        wf = WorkflowEngine.get_workflow("quick_recon")
        assert wf is not None
        assert wf["name"] == "Quick Reconnaissance"

    def test_get_workflow_not_found(self):
        wf = WorkflowEngine.get_workflow("nonexistent_workflow_xyz")
        assert wf is None

    def test_get_phase_prompts(self):
        prompts = WorkflowEngine.get_phase_prompts("quick_recon")
        assert len(prompts) > 0
        assert isinstance(prompts[0], str)

    def test_get_phase_prompts_not_found(self):
        prompts = WorkflowEngine.get_phase_prompts("nonexistent_xyz")
        assert prompts == []

    def test_generate_system_prompt_extension(self):
        prompt = WorkflowEngine.generate_system_prompt_extension("quick_recon")
        assert "Quick Reconnaissance" in prompt
        assert "Phase 1:" in prompt

    def test_generate_system_prompt_extension_not_found(self):
        prompt = WorkflowEngine.generate_system_prompt_extension("nonexistent_xyz")
        assert prompt == ""

    def test_generate_system_prompt_extension_none(self):
        prompt = WorkflowEngine.generate_system_prompt_extension()
        assert prompt == ""

    def test_web_pentest_has_multiple_phases(self):
        wf = WorkflowEngine.get_workflow("web_pentest")
        assert len(wf["phases"]) >= 4

    def test_each_phase_has_tools(self):
        for name, wf in WORKFLOWS.items():
            for phase in wf["phases"]:
                assert "prompt" in phase
                assert "suggested_tools" in phase
                assert len(phase["suggested_tools"]) > 0
