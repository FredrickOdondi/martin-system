#!/usr/bin/env python3
"""
Test Cross-TWG Synthesis Functionality

Tests the supervisor's ability to generate strategic syntheses
across multiple Technical Working Groups.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.agents.supervisor import create_supervisor


def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def test_pillar_overview():
    """Test generating a single pillar overview"""
    print_section("TEST 1: Single Pillar Overview (Energy)")

    supervisor = create_supervisor(auto_register=True, keep_history=False)

    print("Generating Energy pillar overview...")
    print("This will:")
    print("  1. Query the Energy TWG for comprehensive status")
    print("  2. Synthesize into strategic overview")
    print("  3. Format with priorities, initiatives, outcomes, etc.\n")

    result = supervisor.generate_pillar_overview("energy")

    print("Result:")
    print("-" * 70)
    print(result)
    print("-" * 70)

    return True


def test_cross_pillar_synthesis():
    """Test cross-pillar synthesis"""
    print_section("TEST 2: Cross-Pillar Synthesis (Energy & Agriculture)")

    supervisor = create_supervisor(auto_register=True, keep_history=False)

    print("Generating cross-pillar synthesis for Energy & Agriculture...")
    print("This will:")
    print("  1. Query both TWGs about priorities and dependencies")
    print("  2. Identify synergies and complementarities")
    print("  3. Highlight coordination needs\n")

    result = supervisor.generate_cross_pillar_synthesis(["energy", "agriculture"])

    print("Result:")
    print("-" * 70)
    print(result)
    print("-" * 70)

    return True


def test_strategic_priorities():
    """Test strategic priorities synthesis"""
    print_section("TEST 3: Strategic Priorities Across All TWGs")

    supervisor = create_supervisor(auto_register=True, keep_history=False)

    print("Generating strategic priorities synthesis...")
    print("This will:")
    print("  1. Collect status from all 6 TWGs")
    print("  2. Identify top strategic priorities")
    print("  3. Highlight quick wins and moonshots")
    print("  4. Note cross-cutting themes\n")

    result = supervisor.generate_strategic_priorities()

    print("Result:")
    print("-" * 70)
    print(result)
    print("-" * 70)

    return True


def test_policy_coherence():
    """Test policy coherence check"""
    print_section("TEST 4: Policy Coherence Check")

    supervisor = create_supervisor(auto_register=True, keep_history=False)

    print("Generating policy coherence check...")
    print("This will:")
    print("  1. Collect policy recommendations from all TWGs")
    print("  2. Identify areas of alignment")
    print("  3. Flag potential conflicts")
    print("  4. Suggest coordination actions\n")

    result = supervisor.generate_policy_coherence_check()

    print("Result:")
    print("-" * 70)
    print(result)
    print("-" * 70)

    return True


def test_summit_readiness():
    """Test summit readiness assessment"""
    print_section("TEST 5: Summit Readiness Assessment")

    supervisor = create_supervisor(auto_register=True, keep_history=False)

    print("Generating summit readiness assessment...")
    print("This will:")
    print("  1. Collect readiness status from all TWGs")
    print("  2. Assess content, pipeline, logistics, etc.")
    print("  3. Provide readiness scores")
    print("  4. Flag critical issues\n")

    result = supervisor.generate_summit_readiness_assessment()

    print("Result:")
    print("-" * 70)
    print(result)
    print("-" * 70)

    return True


def main():
    """Run all synthesis tests"""
    print("\n" + "=" * 70)
    print("  CROSS-TWG SYNTHESIS TESTING")
    print("=" * 70)
    print("\nThis test suite demonstrates the Supervisor's ability to")
    print("generate strategic syntheses across multiple TWGs.\n")
    print("⚠️  Note: Each synthesis involves multiple LLM calls")
    print("    and may take 30-60 seconds to complete.\n")

    tests = [
        ("Pillar Overview", test_pillar_overview),
        ("Cross-Pillar Synthesis", test_cross_pillar_synthesis),
        ("Strategic Priorities", test_strategic_priorities),
        ("Policy Coherence", test_policy_coherence),
        ("Summit Readiness", test_summit_readiness)
    ]

    # Let user choose which test to run
    print("Available tests:")
    for i, (name, _) in enumerate(tests, 1):
        print(f"  {i}. {name}")
    print(f"  {len(tests) + 1}. Run all tests")

    try:
        choice = input("\nSelect test to run (1-6): ").strip()
        choice_num = int(choice)

        if 1 <= choice_num <= len(tests):
            # Run single test
            name, test_func = tests[choice_num - 1]
            print(f"\nRunning: {name}")
            test_func()
            print("\n✅ Test completed!")

        elif choice_num == len(tests) + 1:
            # Run all tests
            print("\nRunning all tests...")
            for name, test_func in tests:
                try:
                    test_func()
                    print(f"\n✅ {name} completed!")
                except Exception as e:
                    print(f"\n❌ {name} failed: {e}")

            print("\n" + "=" * 70)
            print("  ALL TESTS COMPLETED")
            print("=" * 70)

        else:
            print("Invalid choice!")
            return 1

    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
