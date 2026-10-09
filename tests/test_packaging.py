"""Unit tests for Teams app packaging, manifest schema compliance, icon assets,

zip packaging utility, and zero hardcoded secrets in deployment templates.
"""

from __future__ import annotations

import json
import re
import tempfile
import uuid
import zipfile
from pathlib import Path

import pytest

from packaging.teams.package import (
    create_teams_package,
    generate_color_icon,
    generate_outline_icon,
    parse_png_dimensions,
    scan_file_for_secrets,
    scan_text_for_secrets,
    validate_icons,
    validate_manifest,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
PACKAGING_DIR = REPO_ROOT / "packaging" / "teams"
INFRA_DIR = REPO_ROOT / "infra"


class TestTeamsManifestCompliance:
    """Verifies Microsoft Teams app manifest schema compliance."""

    def test_given_manifest_when_validated_then_passes_schema_rules(self) -> None:
        manifest_path = PACKAGING_DIR / "manifest.json"
        assert manifest_path.is_file(), f"Manifest not found at {manifest_path}"

        is_valid, errors = validate_manifest(manifest_path)
        assert is_valid, f"Manifest failed validation: {errors}"
        assert errors == []

    def test_manifest_required_fields_and_formats(self) -> None:
        manifest_path = PACKAGING_DIR / "manifest.json"
        data = json.loads(manifest_path.read_text(encoding="utf-8"))

        # Schema & versions
        assert data["$schema"].startswith(
            "https://developer.microsoft.com/en-us/json-schemas/teams/"
        )
        assert data["manifestVersion"] in ("1.16", "1.17")
        assert re.match(r"^\d+\.\d+\.\d+$", data["version"])

        # ID must be valid UUID
        uuid_obj = uuid.UUID(data["id"])
        assert str(uuid_obj) == data["id"]

        # Names
        assert 1 <= len(data["name"]["short"]) <= 30
        assert 1 <= len(data["name"]["full"]) <= 100

        # Descriptions
        assert 1 <= len(data["description"]["short"]) <= 80
        assert 1 <= len(data["description"]["full"]) <= 4000

        # Developer URLs must all use HTTPS
        dev = data["developer"]
        assert dev["websiteUrl"].startswith("https://")
        assert dev["privacyUrl"].startswith("https://")
        assert dev["termsOfUseUrl"].startswith("https://")

        # Icons
        assert data["icons"]["color"] == "color.png"
        assert data["icons"]["outline"] == "outline.png"

        # Accent color hex format
        assert re.match(r"^#[0-9A-Fa-f]{6}$", data["accentColor"])

        # Bots
        assert len(data["bots"]) >= 1
        bot = data["bots"][0]
        assert "botId" in bot
        assert set(bot["scopes"]).issubset({"personal", "team", "groupChat"})

    def test_manifest_validation_error_cases(self) -> None:
        # Missing required field
        is_val, errs = validate_manifest({"manifestVersion": "1.16"})
        assert not is_val
        assert any("Missing required field 'id'" in e for e in errs)

        # Insecure HTTP URL
        invalid_dev = {
            "$schema": "https://developer.microsoft.com/en-us/json-schemas/teams/v1.16/MicrosoftTeams.schema.json",
            "manifestVersion": "1.16",
            "version": "1.0.0",
            "id": str(uuid.uuid4()),
            "name": {"short": "Short", "full": "Full"},
            "description": {"short": "Short desc", "full": "Full desc"},
            "icons": {"color": "color.png", "outline": "outline.png"},
            "accentColor": "#0078D4",
            "developer": {
                "name": "Dev",
                "websiteUrl": "http://insecure.com",  # HTTP not HTTPS
                "privacyUrl": "https://secure.com/privacy",
                "termsOfUseUrl": "https://secure.com/terms",
            },
        }
        is_val, errs = validate_manifest(invalid_dev)
        assert not is_val
        assert any("must be a secure HTTPS URL" in e for e in errs)

        # Excessively long name
        too_long_name = dict(invalid_dev)
        too_long_name["developer"] = {
            "name": "Dev",
            "websiteUrl": "https://secure.com",
            "privacyUrl": "https://secure.com/privacy",
            "termsOfUseUrl": "https://secure.com/terms",
        }
        too_long_name["name"] = {"short": "A" * 35, "full": "Full"}
        is_val, errs = validate_manifest(too_long_name)
        assert not is_val
        assert any("exceeds maximum 30 characters" in e for e in errs)


class TestIconAssetsCompliance:
    """Verifies Teams icon dimension, color format, and transparency compliance."""

    def test_color_icon_specifications(self) -> None:
        color_path = PACKAGING_DIR / "color.png"
        assert color_path.is_file(), f"Color icon missing: {color_path}"

        w, h, color_type = parse_png_dimensions(color_path.read_bytes())
        assert w == 192, f"Color icon width must be 192, got {w}"
        assert h == 192, f"Color icon height must be 192, got {h}"
        assert color_type in (2, 6), "Color icon must be RGB or RGBA"

    def test_outline_icon_specifications(self) -> None:
        outline_path = PACKAGING_DIR / "outline.png"
        assert outline_path.is_file(), f"Outline icon missing: {outline_path}"

        w, h, color_type = parse_png_dimensions(outline_path.read_bytes())
        assert w == 32, f"Outline icon width must be 32, got {w}"
        assert h == 32, f"Outline icon height must be 32, got {h}"
        assert color_type == 6, (
            "Outline icon must have transparency (RGBA color type 6)"
        )

    def test_validate_icons_utility(self) -> None:
        color_path = PACKAGING_DIR / "color.png"
        outline_path = PACKAGING_DIR / "outline.png"

        is_val, errs = validate_icons(color_path, outline_path)
        assert is_val, f"Icon validation failed: {errs}"
        assert errs == []

    def test_validate_icons_handles_missing_and_invalid_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            missing_c = tmp / "missing_color.png"
            missing_o = tmp / "missing_outline.png"

            is_val, errs = validate_icons(missing_c, missing_o)
            assert not is_val
            assert len(errs) == 2

            # Bad dimension icon
            bad_icon = tmp / "bad.png"
            bad_icon.write_bytes(generate_outline_icon(tmp / "gen_o.png").read_bytes())
            is_val, errs = validate_icons(bad_icon, bad_icon)
            assert not is_val
            assert any("dimensions must be 192x192" in e for e in errs)

    def test_parse_png_dimensions_raises_on_invalid_data(self) -> None:
        with pytest.raises(ValueError, match="Invalid PNG signature"):
            parse_png_dimensions(b"NOT_A_PNG_FILE_HEADER")

        with pytest.raises(ValueError, match="First chunk must be valid IHDR"):
            # PNG signature followed by corrupt chunk
            parse_png_dimensions(b"\x89PNG\r\n\x1a\n\x00\x00\x00\x04CORR12345678")

    def test_generate_color_and_outline_icons(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            c = generate_color_icon(tmp / "c.png")
            o = generate_outline_icon(tmp / "o.png")
            assert c.is_file() and o.is_file()
            w_c, h_c, _ = parse_png_dimensions(c.read_bytes())
            w_o, h_o, col_o = parse_png_dimensions(o.read_bytes())
            assert (w_c, h_c) == (192, 192)
            assert (w_o, h_o) == (32, 32)
            assert col_o == 6


class TestTeamsZipPackaging:
    """Verifies automated Teams zip packaging and structure."""

    def test_create_teams_package_produces_valid_archive(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_zip = Path(tmpdir) / "test_app.zip"
            created = create_teams_package(PACKAGING_DIR, out_zip)

            assert created.is_file()
            assert zipfile.is_zipfile(created)

            with zipfile.ZipFile(created, "r") as zf:
                names = zf.namelist()
                assert set(names) == {"manifest.json", "color.png", "outline.png"}

                # Verify manifest inside zip
                manifest_data = json.loads(zf.read("manifest.json").decode("utf-8"))
                assert manifest_data["id"] == "c5b8e962-4217-48f1-a1b7-d1e9e8f62301"

                # Verify icons inside zip
                w_c, h_c, _ = parse_png_dimensions(zf.read("color.png"))
                assert (w_c, h_c) == (192, 192)

                w_o, h_o, col_o = parse_png_dimensions(zf.read("outline.png"))
                assert (w_o, h_o) == (32, 32)
                assert col_o == 6

    def test_create_teams_package_with_bot_id_override(self) -> None:
        custom_bot_id = "11111111-2222-3333-4444-555555555555"
        with tempfile.TemporaryDirectory() as tmpdir:
            out_zip = Path(tmpdir) / "custom_bot.zip"
            create_teams_package(PACKAGING_DIR, out_zip, bot_id_override=custom_bot_id)

            with zipfile.ZipFile(out_zip, "r") as zf:
                manifest_data = json.loads(zf.read("manifest.json").decode("utf-8"))
                assert manifest_data["bots"][0]["botId"] == custom_bot_id


class TestZeroHardcodedSecrets:
    """Verifies zero hardcoded secrets across infrastructure and packaging artifacts."""

    def test_infra_main_bicep_has_zero_secrets(self) -> None:
        bicep_path = INFRA_DIR / "main.bicep"
        assert bicep_path.is_file(), f"Bicep template missing at {bicep_path}"

        findings = scan_file_for_secrets(bicep_path)
        assert findings == [], f"Found hardcoded secrets in main.bicep: {findings}"

    def test_infra_main_bicepparam_has_zero_secrets(self) -> None:
        param_path = INFRA_DIR / "main.bicepparam"
        assert param_path.is_file(), f"Bicep parameter file missing at {param_path}"

        findings = scan_file_for_secrets(param_path)
        assert findings == [], f"Found hardcoded secrets in main.bicepparam: {findings}"

    def test_packaging_teams_manifest_has_zero_secrets(self) -> None:
        manifest_path = PACKAGING_DIR / "manifest.json"
        findings = scan_file_for_secrets(manifest_path)
        assert findings == [], f"Found hardcoded secrets in manifest.json: {findings}"

    def test_secret_scanner_detects_synthetic_secrets(self) -> None:
        # Positive controls for scanner logic
        assert len(scan_text_for_secrets("password = 'MySecretP@ssw0rd!'")) >= 1
        assert (
            len(
                scan_text_for_secrets(
                    "DefaultEndpointsProtocol=https;AccountName=test;AccountKey=dGVzdF9rZXlfZm9yX3VuaXRfdGVzdGluZ19leGFtcGxlXzEyMw=="
                )
            )
            >= 1
        )
        assert (
            len(scan_text_for_secrets("ghp_123456789012345678901234567890123456")) >= 1
        )
        # Safe text should have zero findings
        assert scan_text_for_secrets("param environmentName string = 'test'") == []


class TestAzureBicepArchitectureCompliance:
    """Verifies Azure Bicep defines all required services and RBAC assignments."""

    def test_bicep_declares_complete_azure_architecture_resources(self) -> None:
        bicep_content = (INFRA_DIR / "main.bicep").read_text(encoding="utf-8")

        # 1. App Service (Compute)
        assert "Microsoft.Web/serverfarms" in bicep_content
        assert "Microsoft.Web/sites" in bicep_content
        assert "PYTHON|3.11" in bicep_content

        # 2. Azure Functions (Asynchronous SLA Timers)
        assert "'functionapp,linux'" in bicep_content

        # 3. Cosmos DB (Structured Tickets + Memory)
        assert "Microsoft.DocumentDB/databaseAccounts" in bicep_content
        assert "'hr-ticket-store'" in bicep_content
        assert "'hr-conversation-memory'" in bicep_content
        assert "'/ticket_id'" in bicep_content
        assert "'/user_id'" in bicep_content

        # 4. Azure AI Search (Hybrid BM25 + Vector + Semantic Reranker)
        assert "Microsoft.Search/searchServices" in bicep_content
        assert "semanticSearch" in bicep_content

        # 5. Azure Service Bus (SLA Queues)
        assert "Microsoft.ServiceBus/namespaces" in bicep_content
        assert "'hr-sla-jobs'" in bicep_content
        assert "requiresDuplicateDetection: true" in bicep_content

        # 6. Azure Key Vault
        assert "Microsoft.KeyVault/vaults" in bicep_content
        assert "enableRbacAuthorization: true" in bicep_content
        assert "enablePurgeProtection: true" in bicep_content

        # 7. Cognitive Services / Azure OpenAI
        assert "Microsoft.CognitiveServices/accounts" in bicep_content
        assert "'gpt-6-luna'" in bicep_content
        assert "'text-embedding-3-small'" in bicep_content

        # 8. Storage Account (Policy Documents)
        assert "Microsoft.Storage/storageAccounts" in bicep_content
        assert "'policy-documents'" in bicep_content

        # 9. Bot Service & Teams Channel
        assert "Microsoft.BotService/botServices" in bicep_content
        assert "'MsTeamsChannel'" in bicep_content

        # 10. Observability (Application Insights & Log Analytics)
        assert "Microsoft.OperationalInsights/workspaces" in bicep_content
        assert "Microsoft.Insights/components" in bicep_content

    def test_bicep_declares_least_privilege_rbac_role_assignments(self) -> None:
        bicep_content = (INFRA_DIR / "main.bicep").read_text(encoding="utf-8")

        # Built-in role definitions referenced
        expected_roles = [
            "4633458b-17de-408a-b874-0445c86b69e6",  # Key Vault Secrets User
            "69a216fc-b8fb-44d8-bc22-1f3c2cd27a39",  # Service Bus Data Sender
            "4f6d3b9b-027b-4f4c-9142-0e5a2a2247e0",  # Service Bus Data Receiver
            "8ebe5a00-799e-43f5-93ac-243d3dce84a7",  # Search Index Data Contributor
            "5e0bd9bd-7b93-4f28-af87-19fc36ad61bd",  # Cognitive Services OpenAI User
            "2a2b9908-6ea1-4ae2-8e65-a410df84e7d1",  # Storage Blob Data Reader
            "00000000-0000-0000-0000-000000000002",  # Cosmos DB Data Contributor
        ]

        for role_id in expected_roles:
            assert role_id in bicep_content, (
                f"Expected RBAC role ID {role_id} in main.bicep"
            )

        # SystemAssigned managed identity configured on compute
        assert "identity: {\n    type: 'SystemAssigned'\n  }" in bicep_content or (
            "type: 'SystemAssigned'" in bicep_content
        )

        # Local auth disabled on sensitive services
        assert "disableLocalAuth: true" in bicep_content
