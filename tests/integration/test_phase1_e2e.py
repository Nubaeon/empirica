"""
Phase 1 End-to-End Integration Tests

Tests the complete flow of Phase 1:
1. Load MCO personas from Qdrant
2. Create SigningPersona with Ed25519 keys
3. Sign epistemic states
4. Store in Git notes
5. Verify CASCADE chains
6. Test semantic search

This validates that the cryptographic foundation is working correctly
before proceeding to Phase 2 (session replay) and Phase 3 (browser extension).
"""

import pytest
import tempfile
import json
from pathlib import Path

import git

from empirica.core.persona.persona_profile import (
    PersonaProfile, SigningIdentityConfig, EpistemicConfig, PersonaMetadata
)
from empirica.core.identity.ai_identity import AIIdentity, IdentityManager
from empirica.core.persona.signing_persona import SigningPersona
from empirica.core.git_ops.signed_operations import SignedGitOperations
from empirica.core.qdrant.persona_registry import PersonaRegistry


class TestPhase1Foundation:
    """Test Phase 1 foundation: cryptographic personas"""

    @pytest.fixture
    def temp_repo(self):
        """Create temporary git repository"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = git.Repo.init(tmpdir)
            repo.config_writer().set_value("user", "name", "Test").release()
            repo.config_writer().set_value("user", "email", "test@test.local").release()
            yield repo

    @pytest.fixture
    def identity_manager(self):
        """Create identity manager"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield IdentityManager(tmpdir)

    @pytest.fixture
    def registry(self):
        """Connect to Qdrant registry"""
        try:
            return PersonaRegistry(
                qdrant_host="localhost",
                qdrant_port=6333
            )
        except ConnectionError:
            pytest.skip("Qdrant not available")

    @pytest.fixture
    def researcher_persona(self, identity_manager):
        """Create researcher persona for testing"""
        identity = identity_manager.create_identity("test_researcher")

        profile = PersonaProfile(
            persona_id="test_researcher",
            name="Test Researcher",
            version="1.0.0",
            signing_identity=SigningIdentityConfig(
                user_id="test",
                identity_name="test_researcher",
                public_key=identity.public_key_hex()
            ),
            epistemic_config=EpistemicConfig(
                priors={
                    "engagement": 0.80, "know": 0.60, "do": 0.70, "context": 0.65,
                    "clarity": 0.55, "coherence": 0.60, "signal": 0.50, "density": 0.70,
                    "state": 0.60, "change": 0.65, "completion": 0.70, "impact": 0.55,
                    "uncertainty": 0.75
                },
                focus_domains=["research", "testing"]
            ),
            metadata=PersonaMetadata(tags=["test"])
        )

        return SigningPersona(profile, identity)

    @pytest.fixture
    def epistemic_state(self):
        """Create sample epistemic state"""
        return {
            "engagement": 0.80,
            "know": 0.60,
            "do": 0.70,
            "context": 0.65,
            "clarity": 0.55,
            "coherence": 0.60,
            "signal": 0.50,
            "density": 0.70,
            "state": 0.60,
            "change": 0.65,
            "completion": 0.70,
            "impact": 0.55,
            "uncertainty": 0.75
        }

    def test_01_load_mco_personas(self, registry):
        """Test loading MCO personas from Qdrant"""
        personas = registry.list_all_personas()

        # Should have at least 6 MCO personas
        assert len(personas) >= 6

        # Check specific personas exist
        persona_ids = [p["persona_id"] for p in personas]
        assert "researcher" in persona_ids
        assert "implementer" in persona_ids
        assert "reviewer" in persona_ids
        assert "coordinator" in persona_ids
        assert "learner" in persona_ids
        assert "expert" in persona_ids

    def test_02_semantic_search_by_domain(self, registry):
        """Test finding personas by domain"""
        # Search for research personas
        research = registry.find_personas_by_domain("research", limit=5)
        assert len(research) > 0
        assert any(p["name"] == "Research Explorer" for p in research)

        # Search for implementation personas
        implementation = registry.find_personas_by_domain("implementation", limit=5)
        assert len(implementation) > 0
        assert any(p["name"] == "Task Implementer" for p in implementation)

    def test_03_sign_epistemic_state(self, researcher_persona, epistemic_state):
        """Test signing epistemic state with Ed25519"""
        # Sign the state
        signed = researcher_persona.sign_epistemic_state(
            epistemic_state,
            phase="PREFLIGHT"
        )

        # Verify structure
        assert "state" in signed
        assert "signature" in signed
        assert "algorithm" in signed
        assert signed["algorithm"] == "Ed25519"

        # Verify state contents
        state = signed["state"]
        assert state["persona_id"] == "test_researcher"
        assert state["phase"] == "PREFLIGHT"
        assert state["public_key"] == researcher_persona.identity.public_key_hex()

    def test_04_verify_signature(self, researcher_persona, epistemic_state):
        """Test verifying epistemic state signature"""
        # Sign
        signed = researcher_persona.sign_epistemic_state(epistemic_state, phase="INVESTIGATE")

        # Verify
        is_valid = researcher_persona.verify_signature(signed)
        assert is_valid is True

    def test_05_commit_signed_state_to_git(self, temp_repo, researcher_persona, epistemic_state):
        """Test storing signed epistemic state in Git"""
        git_ops = SignedGitOperations(temp_repo.working_dir)

        # Commit with signed state
        commit_sha = git_ops.commit_signed_state(
            signing_persona=researcher_persona,
            epistemic_state=epistemic_state,
            phase="PREFLIGHT",
            message="Starting research task"
        )

        assert commit_sha is not None
        assert len(commit_sha) == 40

        # Verify commit exists
        commit = temp_repo.commit(commit_sha)
        assert "test_researcher" in commit.author.name

    def test_06_retrieve_signed_state_from_git(self, temp_repo, researcher_persona, epistemic_state):
        """Test retrieving signed state from Git notes"""
        git_ops = SignedGitOperations(temp_repo.working_dir)

        # Commit
        commit_sha = git_ops.commit_signed_state(
            signing_persona=researcher_persona,
            epistemic_state=epistemic_state,
            phase="INVESTIGATE",
            message="Investigating"
        )

        # Retrieve
        signed_state = git_ops.get_signed_state_from_commit(commit_sha)

        assert signed_state is not None
        assert signed_state["state"]["phase"] == "INVESTIGATE"
        assert signed_state["state"]["persona_id"] == "test_researcher"

    def test_07_verify_cascade_chain(self, temp_repo, researcher_persona, epistemic_state):
        """Test verifying entire CASCADE chain"""
        git_ops = SignedGitOperations(temp_repo.working_dir)

        # Create CASCADE with multiple phases
        phases = ["PREFLIGHT", "INVESTIGATE", "CHECK", "ACT", "POSTFLIGHT"]
        commits = []

        for i, phase in enumerate(phases):
            state = epistemic_state.copy()
            state["know"] = 0.60 + (i * 0.05)  # Progress through phases
            state["uncertainty"] = 0.75 - (i * 0.05)

            commit_sha = git_ops.commit_signed_state(
                signing_persona=researcher_persona,
                epistemic_state=state,
                phase=phase,
                message=f"Phase {phase}"
            )
            commits.append(commit_sha)

        # Verify CASCADE chain
        first = commits[0]
        last = temp_repo.head.commit.hexsha
        results = git_ops.verify_cascade_chain(first, last)

        # Should have verified commits
        assert len(results) > 0
        verified = [r for r in results if r.get("state_verified")]
        assert len(verified) > 0

    def test_08_cascade_report(self, temp_repo, researcher_persona, epistemic_state, tmp_path):
        """Test exporting CASCADE verification report"""
        git_ops = SignedGitOperations(temp_repo.working_dir)

        # Create CASCADE
        commit_sha = git_ops.commit_signed_state(
            signing_persona=researcher_persona,
            epistemic_state=epistemic_state,
            phase="PREFLIGHT",
            message="Test"
        )

        # Export report
        report_file = tmp_path / "cascade_report.json"
        report = git_ops.export_cascade_report(
            commit_sha,
            temp_repo.head.commit.hexsha,
            output_file=str(report_file)
        )

        # Verify report
        assert report["title"] == "Empirica CASCADE Verification Report"
        assert "commits" in report
        assert "summary" in report
        assert report_file.exists()

    def test_09_persona_info_export(self, researcher_persona, registry):
        """Test exporting persona information"""
        # Get public persona info
        public = researcher_persona.export_public_persona()

        # Verify structure
        assert public["persona_id"] == "test_researcher"
        assert public["public_key"] == researcher_persona.identity.public_key_hex()
        assert "epistemic_config" in public
        assert "capabilities" in public

        # Verify no private key
        assert "private_key" not in json.dumps(public)

    def test_10_cross_persona_verification_fails(self, identity_manager, epistemic_state):
        """Test that signatures from one persona cannot be verified by another"""
        # Create two personas
        identity1 = identity_manager.create_identity("persona_a")
        identity2 = identity_manager.create_identity("persona_b")

        profile1 = PersonaProfile(
            persona_id="persona_a",
            name="Persona A",
            version="1.0.0",
            signing_identity=SigningIdentityConfig(
                user_id="test",
                identity_name="persona_a",
                public_key=identity1.public_key_hex()
            ),
            epistemic_config=EpistemicConfig(
                priors={
                    "engagement": 0.80, "know": 0.60, "do": 0.70, "context": 0.65,
                    "clarity": 0.55, "coherence": 0.60, "signal": 0.50, "density": 0.70,
                    "state": 0.60, "change": 0.65, "completion": 0.70, "impact": 0.55,
                    "uncertainty": 0.75
                }
            )
        )

        profile2 = PersonaProfile(
            persona_id="persona_b",
            name="Persona B",
            version="1.0.0",
            signing_identity=SigningIdentityConfig(
                user_id="test",
                identity_name="persona_b",
                public_key=identity2.public_key_hex()
            ),
            epistemic_config=EpistemicConfig(
                priors={
                    "engagement": 0.80, "know": 0.60, "do": 0.70, "context": 0.65,
                    "clarity": 0.55, "coherence": 0.60, "signal": 0.50, "density": 0.70,
                    "state": 0.60, "change": 0.65, "completion": 0.70, "impact": 0.55,
                    "uncertainty": 0.75
                }
            )
        )

        signing1 = SigningPersona(profile1, identity1)
        signing2 = SigningPersona(profile2, identity2)

        # Sign with persona 1
        signed = signing1.sign_epistemic_state(epistemic_state, phase="PREFLIGHT")

        # Try to verify with persona 2
        is_valid = signing2.verify_signature(signed)
        assert is_valid is False

    def test_11_end_to_end_workflow(self, temp_repo, registry, identity_manager):
        """Complete end-to-end Phase 1 workflow"""
        # 1. Load researcher from Qdrant
        researchers = registry.find_personas_by_domain("research", limit=1)
        assert len(researchers) > 0
        researcher_data = researchers[0]

        # 2. Create epistemic state
        epistemic_state = {
            "engagement": 0.75,
            "know": 0.70,
            "do": 0.65,
            "context": 0.60,
            "clarity": 0.70,
            "coherence": 0.65,
            "signal": 0.60,
            "density": 0.70,
            "state": 0.65,
            "change": 0.70,
            "completion": 0.50,
            "impact": 0.60,
            "uncertainty": 0.60
        }

        # 3. Create signing persona (using test identity)
        identity = identity_manager.create_identity("e2e_researcher")
        profile = PersonaProfile(
            persona_id="e2e_researcher",
            name="E2E Researcher",
            version="1.0.0",
            signing_identity=SigningIdentityConfig(
                user_id="test",
                identity_name="e2e_researcher",
                public_key=identity.public_key_hex()
            ),
            epistemic_config=EpistemicConfig(
                priors=epistemic_state,
                focus_domains=["research", "e2e_testing"]
            )
        )
        signing_persona = SigningPersona(profile, identity)

        # 4. Sign the state
        signed = signing_persona.sign_epistemic_state(epistemic_state, phase="PREFLIGHT")
        assert signing_persona.verify_signature(signed) is True

        # 5. Store in Git
        git_ops = SignedGitOperations(temp_repo.working_dir)
        commit_sha = git_ops.commit_signed_state(
            signing_persona=signing_persona,
            epistemic_state=epistemic_state,
            phase="PREFLIGHT",
            message="E2E test"
        )

        # 6. Verify CASCADE
        results = git_ops.verify_cascade_chain(commit_sha, temp_repo.head.commit.hexsha)
        assert len(results) > 0
        assert any(r.get("state_verified") for r in results)

        # 7. Create report
        report = git_ops.export_cascade_report(
            commit_sha,
            temp_repo.head.commit.hexsha
        )
        assert report["total_commits"] > 0
        assert any(c.get("state_verified") for c in report["commits"])

        # Success: All Phase 1 components working together
        print("\n✓ Phase 1 End-to-End Test Successful!")
        print(f"  - Personas in Qdrant: {len(registry.list_all_personas())}")
        print(f"  - Signed states in Git: {report['total_commits']}")
        print(f"  - Verified signatures: {report['verified_commits']}")
        print(f"  - CASCADE phases covered: {len(report['summary']['phases_covered'])}")


class TestPhase1EdgeCases:
    """Test edge cases and error conditions"""

    @pytest.fixture
    def temp_repo(self):
        """Create temporary git repository"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = git.Repo.init(tmpdir)
            repo.config_writer().set_value("user", "name", "Test").release()
            repo.config_writer().set_value("user", "email", "test@test.local").release()
            yield repo

    @pytest.fixture
    def identity_manager(self):
        """Create identity manager"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield IdentityManager(tmpdir)

    def test_missing_epistemic_vector(self, identity_manager):
        """Test that missing vector raises error"""
        identity = identity_manager.create_identity("test")
        profile = PersonaProfile(
            persona_id="test",
            name="Test",
            version="1.0.0",
            signing_identity=SigningIdentityConfig(
                user_id="test",
                identity_name="test",
                public_key=identity.public_key_hex()
            ),
            epistemic_config=EpistemicConfig(
                priors={
                    "engagement": 0.5, "know": 0.5, "do": 0.5, "context": 0.5,
                    "clarity": 0.5, "coherence": 0.5, "signal": 0.5, "density": 0.5,
                    "state": 0.5, "change": 0.5, "completion": 0.5, "impact": 0.5,
                    "uncertainty": 0.5
                }
            )
        )

        signing = SigningPersona(profile, identity)

        with pytest.raises(ValueError, match="Missing required vector"):
            signing.sign_epistemic_state({"engagement": 0.5}, phase="PREFLIGHT")

    def test_invalid_vector_value(self, identity_manager):
        """Test that invalid vector value raises error"""
        identity = identity_manager.create_identity("test")
        profile = PersonaProfile(
            persona_id="test",
            name="Test",
            version="1.0.0",
            signing_identity=SigningIdentityConfig(
                user_id="test",
                identity_name="test",
                public_key=identity.public_key_hex()
            ),
            epistemic_config=EpistemicConfig(
                priors={
                    "engagement": 0.5, "know": 0.5, "do": 0.5, "context": 0.5,
                    "clarity": 0.5, "coherence": 0.5, "signal": 0.5, "density": 0.5,
                    "state": 0.5, "change": 0.5, "completion": 0.5, "impact": 0.5,
                    "uncertainty": 0.5
                }
            )
        )

        signing = SigningPersona(profile, identity)

        with pytest.raises(ValueError, match="must be in"):
            signing.sign_epistemic_state(
                {
                    "engagement": 1.5,  # Invalid
                    "know": 0.5, "do": 0.5, "context": 0.5,
                    "clarity": 0.5, "coherence": 0.5, "signal": 0.5, "density": 0.5,
                    "state": 0.5, "change": 0.5, "completion": 0.5, "impact": 0.5,
                    "uncertainty": 0.5
                },
                phase="PREFLIGHT"
            )
