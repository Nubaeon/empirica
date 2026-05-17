"""Tests for compose_ai_id_forms — mesh ai_id form composition."""

from empirica.config.project_config_loader import compose_ai_id_forms


def test_three_forms_returned():
    forms = compose_ai_id_forms(
        tenant_slug="david",
        mesh_id_prefix="empirica_david",
        basename="empirica",
    )
    assert set(forms.keys()) == {"short", "tenant", "mesh"}


def test_short_is_bare_basename():
    forms = compose_ai_id_forms(
        tenant_slug="david", mesh_id_prefix="empirica_david", basename="empirica"
    )
    assert forms["short"] == "empirica"


def test_tenant_form_joins_slug_and_basename():
    forms = compose_ai_id_forms(
        tenant_slug="david", mesh_id_prefix="empirica_david", basename="cortex"
    )
    assert forms["tenant"] == "david_cortex"


def test_mesh_form_uses_prefix_as_returned_by_cortex():
    # The mesh form trusts whatever cortex hands back as mesh_id_prefix
    # rather than recomputing — if cortex changes its slug rule we don't drift.
    forms = compose_ai_id_forms(
        tenant_slug="anything",
        mesh_id_prefix="empirica_david",
        basename="outreach",
    )
    assert forms["mesh"] == "empirica_david_outreach"


def test_handles_basename_with_dash():
    forms = compose_ai_id_forms(
        tenant_slug="acme", mesh_id_prefix="mod_acme", basename="empirica-fork"
    )
    assert forms["short"] == "empirica-fork"
    assert forms["tenant"] == "acme_empirica-fork"
    assert forms["mesh"] == "mod_acme_empirica-fork"


def test_kwargs_only_signature():
    # Positional args must fail — forces callers to be explicit about which
    # field is which (mistaking tenant_slug for mesh_id_prefix is silent
    # otherwise since both are strings).
    import pytest
    with pytest.raises(TypeError):
        compose_ai_id_forms("david", "empirica_david", "empirica")  # type: ignore[misc]
