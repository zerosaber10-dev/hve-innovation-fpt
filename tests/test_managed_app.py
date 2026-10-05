"""Tests for Azure Managed Application packaging and marketplace readiness.

Validates:
1. createUiDefinition.json schema, handler, version, basics, and steps.
2. Parameter parity between UI outputs and mainTemplate.json parameters.
3. Zero hardcoded secrets in infra/mainTemplate.json and createUiDefinition.json.
4. package_managed_app.py package creation, verification, and CLI execution.
"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

from packaging.managed_app.package_managed_app import (
    CREATE_UI_DEFINITION_SCHEMA,
    EXPECTED_HANDLER,
    EXPECTED_VERSION,
    create_managed_app_package,
    scan_file_for_secrets,
    scan_text_for_secrets,
    validate_create_ui_definition,
    validate_parameter_parity,
    validate_template_json,
    verify_managed_app_package,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
INFRA_DIR = REPO_ROOT / "infra"
MAIN_TEMPLATE_PATH = INFRA_DIR / "mainTemplate.json"
CREATE_UI_DEF_PATH = INFRA_DIR / "createUiDefinition.json"
MANAGED_APP_DIR = REPO_ROOT / "packaging" / "managed_app"
APP_ZIP_PATH = MANAGED_APP_DIR / "app.zip"


class TestCreateUiDefinitionSchema:
    """Validate schema compliance and UI steps in infra/createUiDefinition.json."""

    def test_given_create_ui_definition_when_loaded_then_valid_json(
        self,
    ) -> None:
        assert CREATE_UI_DEF_PATH.is_file(), f"File missing at {CREATE_UI_DEF_PATH}"
        data = json.loads(CREATE_UI_DEF_PATH.read_text(encoding="utf-8"))
        assert isinstance(data, dict)

    def test_given_create_ui_definition_then_matches_official_schema(
        self,
    ) -> None:
        data = json.loads(CREATE_UI_DEF_PATH.read_text(encoding="utf-8"))
        assert data.get("$schema") == CREATE_UI_DEFINITION_SCHEMA
        assert data.get("handler") == EXPECTED_HANDLER
        assert data.get("version") == EXPECTED_VERSION

    def test_given_create_ui_definition_then_contains_basics_and_steps(
        self,
    ) -> None:
        data = json.loads(CREATE_UI_DEF_PATH.read_text(encoding="utf-8"))
        parameters = data.get("parameters", {})
        assert "basics" in parameters, "parameters.basics is required"
        assert "steps" in parameters, "parameters.steps is required"
        assert "outputs" in parameters, "parameters.outputs is required"
        assert len(parameters["steps"]) >= 1, "At least one step required"

    def test_given_create_ui_definition_steps_then_declares_app_settings(
        self,
    ) -> None:
        data = json.loads(CREATE_UI_DEF_PATH.read_text(encoding="utf-8"))
        steps = data["parameters"]["steps"]
        app_settings_step = next(
            (s for s in steps if s.get("name") == "appSettingsStep"), None
        )
        assert app_settings_step is not None, "appSettingsStep required"
        assert app_settings_step.get("label") == "App Settings"

        element_names = {
            elem.get("name") for elem in app_settings_step.get("elements", [])
        }
        expected_elements = {
            "environmentName",
            "appNamePrefix",
            "entraTenantId",
            "botAppId",
            "appServicePlanSku",
            "searchSku",
            "existingOpenAiEndpoint",
        }
        missing = expected_elements - element_names
        assert expected_elements.issubset(element_names), f"Missing: {missing}"

    def test_given_create_ui_definition_elements_then_constraints_valid(
        self,
    ) -> None:
        data = json.loads(CREATE_UI_DEF_PATH.read_text(encoding="utf-8"))
        elements = {
            elem["name"]: elem for elem in data["parameters"]["steps"][0]["elements"]
        }

        # environmentName DropDown
        env_elem = elements["environmentName"]
        assert env_elem["type"] == "Microsoft.Common.DropDown"
        allowed_envs = [
            opt["value"] for opt in env_elem["constraints"]["allowedValues"]
        ]
        assert set(allowed_envs) == {"dev", "test", "prod"}

        # appNamePrefix TextBox
        prefix_elem = elements["appNamePrefix"]
        assert prefix_elem["type"] == "Microsoft.Common.TextBox"
        assert prefix_elem["defaultValue"] == "hr-time-leave"
        assert prefix_elem["constraints"]["required"] is True
        assert "regex" in prefix_elem["constraints"]

        # appServicePlanSku DropDown
        plan_elem = elements["appServicePlanSku"]
        assert plan_elem["type"] == "Microsoft.Common.DropDown"
        assert plan_elem["defaultValue"] == "B1"

        # searchSku DropDown
        search_elem = elements["searchSku"]
        assert search_elem["type"] == "Microsoft.Common.DropDown"
        allowed_search = [
            opt["value"] for opt in search_elem["constraints"]["allowedValues"]
        ]
        assert set(allowed_search) == {"basic", "standard"}

    def test_given_create_ui_definition_when_validated_via_utility(
        self,
    ) -> None:
        is_valid, errors, _ = validate_create_ui_definition(CREATE_UI_DEF_PATH)
        assert is_valid, f"Validation errors: {errors}"
        assert len(errors) == 0


class TestParameterParity:
    """Validate 1:1 parameter matching between UI outputs and ARM parameters."""

    def test_given_ui_outputs_then_every_output_maps_to_template_parameter(
        self,
    ) -> None:
        template_data = json.loads(MAIN_TEMPLATE_PATH.read_text(encoding="utf-8"))
        ui_data = json.loads(CREATE_UI_DEF_PATH.read_text(encoding="utf-8"))

        template_params = set(template_data.get("parameters", {}).keys())
        ui_outputs = set(ui_data.get("parameters", {}).get("outputs", {}).keys())

        unmatched_outputs = ui_outputs - template_params
        assert len(unmatched_outputs) == 0, (
            f"createUiDefinition outputs missing in template: {unmatched_outputs}"
        )

    def test_given_template_parameters_then_all_expected_outputs_covered(
        self,
    ) -> None:
        ui_data = json.loads(CREATE_UI_DEF_PATH.read_text(encoding="utf-8"))
        ui_outputs = set(ui_data.get("parameters", {}).get("outputs", {}).keys())

        expected_outputs = {
            "environmentName",
            "location",
            "appNamePrefix",
            "entraTenantId",
            "botAppId",
            "appServicePlanSku",
            "searchSku",
            "existingOpenAiEndpoint",
        }
        diff = expected_outputs ^ ui_outputs
        assert expected_outputs == ui_outputs, f"Mismatched outputs: {diff}"

    def test_given_parity_utility_when_called_on_actual_files_then_passes(
        self,
    ) -> None:
        template_data = json.loads(MAIN_TEMPLATE_PATH.read_text(encoding="utf-8"))
        ui_data = json.loads(CREATE_UI_DEF_PATH.read_text(encoding="utf-8"))

        is_valid, errors = validate_parameter_parity(template_data, ui_data)
        assert is_valid, f"Parity validation errors: {errors}"
        assert len(errors) == 0

    def test_given_parity_utility_when_unmatched_output_then_detects_error(
        self,
    ) -> None:
        template_data = {"parameters": {"param1": {"type": "string"}}}
        ui_data = {
            "parameters": {
                "outputs": {
                    "param1": "[steps('step1').val1]",
                    "unknownParam": "[steps('step1').val2]",
                }
            }
        }
        is_valid, errors = validate_parameter_parity(template_data, ui_data)
        assert not is_valid
        assert any("unknownParam" in err for err in errors)

    def test_given_parity_utility_when_missing_mandatory_param_then_fails(
        self,
    ) -> None:
        template_data = {
            "parameters": {
                "mandatoryParam": {"type": "string"},  # No defaultValue
            }
        }
        ui_data = {"parameters": {"outputs": {}}}
        is_valid, errors = validate_parameter_parity(template_data, ui_data)
        assert not is_valid
        assert any("mandatoryParam" in err for err in errors)


class TestZeroHardcodedSecrets:
    """Verify zero hardcoded secrets or credentials in template and UI."""

    def test_given_main_template_then_zero_hardcoded_secrets(self) -> None:
        findings = scan_file_for_secrets(MAIN_TEMPLATE_PATH)
        assert len(findings) == 0, f"Secrets found in mainTemplate: {findings}"

    def test_given_create_ui_definition_then_zero_hardcoded_secrets(
        self,
    ) -> None:
        findings = scan_file_for_secrets(CREATE_UI_DEF_PATH)
        assert len(findings) == 0, f"Secrets found in createUiDef: {findings}"

    def test_given_synthetic_secrets_when_scanned_then_patterns_detected(
        self,
    ) -> None:
        synthetic_cases = [
            'password = "SuperSecretP@ssword123!"',
            'api_key: "abcdef1234567890abcdef1234567890"',
            "DefaultEndpointsProtocol=https;AccountName=teststorage;"
            "AccountKey=dGVzdGtleTEyMzQ1Njc4OTAxdGVzdGtleTEyMzQ1Njc4OTA=",
            "Endpoint=sb://test.servicebus.windows.net/;"
            "SharedAccessKey=dGVzdHNlcnZpY2VidXNrZXkxMjM0NTY3ODkwMQ==",
            "AccountEndpoint=https://test.documents.azure.com:443/;"
            "AccountKey=dGVzdGNvc21vc2tleTEyMzQ1Njc4OTAxMjM0NTY3ODkwMTIzNDU2Nzg5MDEyMzQ1Njc4OTAxMjM0NQ==",
            "ghp_1234567890abcdef1234567890abcdef1234",
        ]
        for secret_sample in synthetic_cases:
            findings = scan_text_for_secrets(secret_sample)
            assert len(findings) > 0, f"Expected detection for: {secret_sample}"


class TestManagedAppPackaging:
    """Test building, verifying, and executing packaging utility for app.zip."""

    def test_given_packaging_utility_when_executed_then_produces_app_zip(
        self, tmp_path: Path
    ) -> None:
        output_zip = tmp_path / "test_app.zip"
        result_path = create_managed_app_package(INFRA_DIR, output_zip)

        assert result_path.is_file()
        assert result_path == output_zip
        assert output_zip.stat().st_size > 0

    def test_given_app_zip_then_contains_exact_required_root_files(self) -> None:
        assert APP_ZIP_PATH.is_file(), f"app.zip missing at {APP_ZIP_PATH}"
        with zipfile.ZipFile(APP_ZIP_PATH, mode="r") as zf:
            names = zf.namelist()
            assert "mainTemplate.json" in names
            assert "createUiDefinition.json" in names
            assert len(names) == 2, f"Expected exactly 2 files, found: {names}"

    def test_given_app_zip_when_verified_then_passes_validation(self) -> None:
        is_valid, errors = verify_managed_app_package(APP_ZIP_PATH)
        assert is_valid, f"Package verification errors: {errors}"
        assert len(errors) == 0

    def test_given_corrupt_zip_when_verified_then_detects_missing_file(
        self, tmp_path: Path
    ) -> None:
        bad_zip = tmp_path / "bad.zip"
        with zipfile.ZipFile(bad_zip, mode="w") as zf:
            zf.writestr("dummy.txt", "hello world")

        is_valid, errors = verify_managed_app_package(bad_zip)
        assert not is_valid
        assert any("missing required files" in err.lower() for err in errors)

    def test_given_main_template_validator_when_called_then_succeeds(
        self,
    ) -> None:
        is_valid, errors, data = validate_template_json(MAIN_TEMPLATE_PATH)
        assert is_valid, f"mainTemplate errors: {errors}"
        assert data.get("contentVersion") == "1.0.0.0"
        assert "resources" in data
