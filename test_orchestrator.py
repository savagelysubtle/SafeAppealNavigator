#!/usr/bin/env python3
"""
Test script for the Legal Research Orchestrator

This script tests the basic functionality of the orchestrator system
without requiring the full web UI to be running.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ai_research_assistant.agent.orchestrator import (
    LegalOrchestratorAgent,
)
from ai_research_assistant.agent.orchestrator.legal_orchestrator import (
    LegalWorkflowConfig,
)


async def test_orchestrator_basic():
    """Test basic orchestrator functionality"""
    print("🎯 Testing Legal Research Orchestrator")
    print("=" * 50)

    try:
        # Create configuration
        config = LegalWorkflowConfig(
            enable_chat_interface=True,
            auto_proceed_after_intake=False,
            require_human_approval=False,  # Disable for testing
            max_concurrent_agents=2,
            timeout_seconds=300,
        )

        print("✅ Configuration created successfully")

        # Initialize orchestrator
        orchestrator = LegalOrchestratorAgent(
            orchestrator_config=config,
            work_dir="./tmp/test_orchestrator",
        )

        print("✅ Orchestrator initialized successfully")

        # Test getting supported task types
        task_types = orchestrator.get_supported_task_types()
        print(f"✅ Supported task types: {task_types}")

        # Test starting a workflow
        print("\n🚀 Testing workflow start...")
        result = await orchestrator.run_task(
            task_type="start_legal_workflow",
            parameters={
                "client_info": {
                    "name": "Test Client",
                    "case_description": "Test WCAT case for system verification",
                },
                "case_type": "wcat_appeal",
                "documents": ["test_document.pdf"],
                "research_queries": ["test query", "workers compensation"],
            },
        )

        if result.get("success"):
            workflow_id = result.get("workflow_id")
            print(f"✅ Workflow started: {workflow_id}")

            # Test getting workflow status
            print("\n📊 Testing workflow status...")
            status_result = await orchestrator.run_task(
                task_type="get_workflow_status", parameters={}
            )

            if status_result.get("success"):
                print("✅ Workflow status retrieved successfully")
                print(
                    f"   State: {status_result.get('state', {}).get('state', 'Unknown')}"
                )
            else:
                print(f"❌ Failed to get workflow status: {status_result.get('error')}")

            # Test interactive chat
            print("\n💬 Testing interactive chat...")
            chat_result = await orchestrator.run_task(
                task_type="interactive_chat",
                parameters={"message": "What is the status of my case?"},
            )

            if chat_result.get("success"):
                print("✅ Chat interaction successful")
                print(
                    f"   Response: {chat_result.get('response', 'No response')[:100]}..."
                )
            else:
                print(f"❌ Chat interaction failed: {chat_result.get('error')}")

        else:
            print(f"❌ Failed to start workflow: {result.get('error')}")

        # Test agent coordinator status
        print("\n🤖 Testing agent coordinator...")
        coordinator_status = orchestrator.agent_coordinator.get_status()
        print(f"✅ Agent coordinator status: {coordinator_status}")

        # Test workflow manager status
        print("\n📋 Testing workflow manager...")
        workflow_status = orchestrator.workflow_manager.get_status()
        print(f"✅ Workflow manager status: {workflow_status}")

        # Stop orchestrator
        print("\n⛔ Stopping orchestrator...")
        await orchestrator.stop()
        print("✅ Orchestrator stopped successfully")

        print("\n🎉 All tests completed successfully!")

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return False

    return True


async def test_workflow_manager():
    """Test workflow manager independently"""
    print("\n📋 Testing Workflow Manager")
    print("=" * 30)

    try:
        from ai_research_assistant.agent.orchestrator.workflow_manager import (
            WorkflowManager,
            WorkflowState,
        )

        # Initialize workflow manager
        wm = WorkflowManager(work_dir=Path("./tmp/test_workflows"))
        print("✅ Workflow manager initialized")

        # Create a test workflow
        workflow = await wm.create_workflow(
            workflow_id="test-workflow-123",
            client_info={"name": "Test Client"},
            case_type="wcat_appeal",
        )
        print("✅ Test workflow created")

        # Update workflow state
        success = await wm.update_workflow_state(
            "test-workflow-123", WorkflowState.INTAKE_PROCESSING, {"test": "data"}
        )
        print(f"✅ Workflow state updated: {success}")

        # Get workflow state
        state = await wm.get_workflow_state("test-workflow-123")
        print(f"✅ Workflow state retrieved: {state['state']}")

        # Get progress
        progress = wm.get_workflow_progress("test-workflow-123")
        print(f"✅ Progress: {progress['progress_percentage']}%")

        print("✅ Workflow manager tests completed")

    except Exception as e:
        print(f"❌ Workflow manager test failed: {e}")
        return False

    return True


async def test_agent_coordinator():
    """Test agent coordinator independently"""
    print("\n🤖 Testing Agent Coordinator")
    print("=" * 30)

    try:
        from ai_research_assistant.agent.orchestrator.agent_coordinator import (
            AgentCoordinator,
        )

        # Initialize coordinator
        coordinator = AgentCoordinator(max_concurrent=2, timeout_seconds=30)
        print("✅ Agent coordinator initialized")

        # Test single task execution
        result = await coordinator.execute_agent_task(
            agent_type="intake",
            task_type="test_task",
            parameters={"test": "value"},
        )
        print(f"✅ Single task executed: {result.get('success', False)}")

        # Test concurrent task execution
        task_specs = [
            {
                "agent_type": "intake",
                "task_type": "test_task",
                "parameters": {"test": "concurrent1"},
            },
            {
                "agent_type": "legal_research",
                "task_type": "test_task",
                "parameters": {"test": "concurrent2"},
            },
        ]

        results = await coordinator.execute_concurrent_tasks(task_specs)
        print(f"✅ Concurrent tasks executed: {len(results)} results")

        # Get status
        status = coordinator.get_status()
        print(f"✅ Coordinator status: {status}")

        # Stop all agents
        await coordinator.stop_all_agents()
        print("✅ All agents stopped")

        print("✅ Agent coordinator tests completed")

    except Exception as e:
        print(f"❌ Agent coordinator test failed: {e}")
        return False

    return True


async def main():
    """Run all tests"""
    print("🎯 Legal Research Orchestrator Test Suite")
    print("=" * 60)

    tests = [
        ("Workflow Manager", test_workflow_manager),
        ("Agent Coordinator", test_agent_coordinator),
        ("Orchestrator Integration", test_orchestrator_basic),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} test...")
        try:
            result = await test_func()
            results.append((test_name, result))
            if result:
                print(f"✅ {test_name} test PASSED")
            else:
                print(f"❌ {test_name} test FAILED")
        except Exception as e:
            print(f"❌ {test_name} test ERROR: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests PASSED! Orchestrator system is working correctly.")
        return 0
    else:
        print("❌ Some tests FAILED. Check the output above for details.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
