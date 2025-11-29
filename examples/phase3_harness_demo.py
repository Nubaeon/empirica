#!/usr/bin/env python3
"""
Phase 3 PersonaHarness Demo

Demonstrates:
1. Loading personas into PersonaHarness
2. Executing tasks with persona-specific behavior
3. Persona priors affecting epistemic assessments
4. Sentinel communication (file-based MVP)

Usage:
    python3 examples/phase3_harness_demo.py
"""

import sys
import asyncio
from pathlib import Path

# Add empirica to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from empirica.core.persona import PersonaManager
from empirica.core.persona.harness import PersonaHarness


async def demo_security_persona():
    """Demo: Security expert reviewing code"""
    print("=" * 70)
    print("Example 1: Security Expert Reviewing Authentication Code")
    print("=" * 70)
    print()

    # Create security persona
    manager = PersonaManager()
    security = manager.create_persona(
        persona_id="security_demo",
        name="Security Expert Demo",
        template="builtin:security"
    )
    manager.save_persona(security, overwrite=True)

    # Load into harness
    harness = PersonaHarness(
        persona_id="security_demo",
        enable_sentinel=False  # Disable for demo
    )

    print(f"✓ Loaded persona: {harness.persona.name}")
    print(f"  Type: {harness.persona.get_type()}")
    print(f"  KNOW prior: {harness.persona.epistemic_config.priors['know']}")
    print(f"  Confidence threshold: {harness.persona.epistemic_config.thresholds['confidence_to_proceed']}")
    print()

    # NOTE: Actual task execution requires LLM integration
    # This demo shows the harness configuration
    print("📊 Persona configuration applied to CASCADE:")
    info = harness.get_persona_info()
    print(f"  - Investigation profile: {harness._select_investigation_profile()}")
    print(f"  - Focus domains: {', '.join(info['focus_domains'][:3])}...")
    print(f"  - Weights: foundation={info['weights']['foundation']:.2f}, "
          f"comprehension={info['weights']['comprehension']:.2f}")
    print()


async def demo_ux_persona():
    """Demo: UX specialist reviewing interface"""
    print("=" * 70)
    print("Example 2: UX Specialist Reviewing User Interface")
    print("=" * 70)
    print()

    manager = PersonaManager()
    ux = manager.create_persona(
        persona_id="ux_demo",
        name="UX Specialist Demo",
        template="builtin:ux"
    )
    manager.save_persona(ux, overwrite=True)

    harness = PersonaHarness(
        persona_id="ux_demo",
        enable_sentinel=False
    )

    print(f"✓ Loaded persona: {harness.persona.name}")
    print(f"  Type: {harness.persona.get_type()}")
    print(f"  CONTEXT prior: {harness.persona.epistemic_config.priors['context']} (high for user awareness)")
    print(f"  CLARITY prior: {harness.persona.epistemic_config.priors['clarity']}")
    print()

    info = harness.get_persona_info()
    print(f"📊 UX persona emphasizes:")
    print(f"  - User experience focus domains: {', '.join(info['focus_domains'][:3])}")
    print(f"  - Comprehension weight: {info['weights']['comprehension']:.2f} (higher than security)")
    print()


async def demo_persona_comparison():
    """Demo: Comparing different personas on same task"""
    print("=" * 70)
    print("Example 3: Multi-Persona Comparison")
    print("=" * 70)
    print()

    manager = PersonaManager()

    # Create multiple personas
    personas_to_create = [
        ("security_comp", "Security Expert", "builtin:security"),
        ("ux_comp", "UX Specialist", "builtin:ux"),
        ("perf_comp", "Performance Optimizer", "builtin:performance")
    ]

    harnesses = []

    for persona_id, name, template in personas_to_create:
        persona = manager.create_persona(persona_id, name, template=template)
        manager.save_persona(persona, overwrite=True)

        harness = PersonaHarness(persona_id, enable_sentinel=False)
        harnesses.append(harness)

    print("✓ Created 3 personas with different specializations\n")

    task = "Review the user login feature for potential issues"

    print(f"📋 Task: {task}\n")
    print("🎭 How each persona would approach this task:\n")

    for harness in harnesses:
        persona_type = harness.persona.get_type()
        info = harness.get_persona_info()

        print(f"{persona_type.upper()} perspective:")
        print(f"  - Focus: {', '.join(info['focus_domains'][:3])}")
        print(f"  - Investigation profile: {harness._select_investigation_profile()}")
        print(f"  - Confidence threshold: {info['thresholds']['confidence_to_proceed']:.2f}")

        # Show what this persona would emphasize
        if persona_type == 'security':
            print(f"  - Would look for: authentication flaws, injection risks, session management")
        elif persona_type == 'ux':
            print(f"  - Would look for: usability issues, error messages, accessibility")
        elif persona_type == 'performance':
            print(f"  - Would look for: response time, database queries, caching")

        print()


async def demo_sentinel_communication():
    """Demo: Sentinel communication protocol"""
    print("=" * 70)
    print("Example 4: Sentinel Communication Protocol (MVP)")
    print("=" * 70)
    print()

    from empirica.core.persona.harness import (
        PersonaMessage,
        SentinelMessage,
        MessageType,
        send_message,
        receive_message
    )
    from empirica.core.identity import AIIdentity

    # Create test persona
    manager = PersonaManager()
    persona = manager.create_persona("comm_test", "Test Persona", template="builtin:security")
    manager.save_persona(persona, overwrite=True)

    # Create identities for signing
    sentinel_identity = AIIdentity(ai_id="sentinel_demo")
    sentinel_identity.generate_keypair()

    persona_identity = AIIdentity(ai_id="comm_test")
    persona_identity.generate_keypair()

    print("✓ Created identities for Sentinel and Persona\n")

    # Sentinel sends task assignment
    task_msg = SentinelMessage(
        message_type=MessageType.TASK_ASSIGNMENT,
        persona_id="comm_test",
        payload={
            "task": "Review authentication module",
            "priority": "high",
            "deadline_minutes": 30
        }
    )
    task_msg.sign(sentinel_identity)

    print("📤 Sentinel → Persona: TASK_ASSIGNMENT")
    print(f"   Task: {task_msg.payload['task']}")
    print(f"   Signed: {task_msg.signature[:16]}...")

    # Send message (file-based MVP)
    send_message(task_msg, transport="file", destination=".empirica/messages")
    print("   ✓ Message sent via file transport\n")

    # Persona receives task
    received_msg = receive_message("comm_test", transport="file", source=".empirica/messages")

    if received_msg:
        print("📥 Persona received message:")
        print(f"   Type: {received_msg.message_type.value}")
        print(f"   Task: {received_msg.payload['task']}")
        print()

    # Persona sends status report
    status_msg = PersonaMessage(
        message_type=MessageType.STATUS_REPORT,
        persona_id="comm_test",
        payload={
            "phase": "CHECK",
            "confidence": 0.85,
            "findings": ["Potential SQL injection in login.py:42"]
        }
    )
    status_msg.sign(persona_identity)

    print("📤 Persona → Sentinel: STATUS_REPORT")
    print(f"   Phase: {status_msg.payload['phase']}")
    print(f"   Confidence: {status_msg.payload['confidence']}")
    print(f"   Signed: {status_msg.signature[:16]}...")

    send_message(status_msg, transport="file", destination=".empirica/messages")
    print("   ✓ Message sent\n")

    print("📊 Communication protocol working!")
    print("   Messages are signed with Ed25519 (Phase 2 integration)")
    print("   File-based transport used for MVP")
    print("   Future: Redis pub/sub or gRPC for production\n")


async def main():
    """Run all demos"""
    print("\n" + "=" * 70)
    print("Phase 3: PersonaHarness Runtime Container Demo")
    print("=" * 70)
    print()

    await demo_security_persona()
    await demo_ux_persona()
    await demo_persona_comparison()
    await demo_sentinel_communication()

    print("=" * 70)
    print("✓ PersonaHarness Demo Complete!")
    print("=" * 70)
    print()

    print("Next steps:")
    print("  - Implement SentinelOrchestrator (multi-persona coordination)")
    print("  - Add CASCADE integration tests with real LLM calls")
    print("  - Implement COMPOSE operation (merging persona insights)")
    print("  - Add CLI commands: empirica orchestrate <task>")
    print()


if __name__ == "__main__":
    asyncio.run(main())
