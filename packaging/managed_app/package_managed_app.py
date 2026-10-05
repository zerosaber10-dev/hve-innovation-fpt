"""Azure Managed Application packaging and validation utility.

Validates infra/mainTemplate.json and infra/createUiDefinition.json, checks
schema compliance, ensures parameter parity between UI outputs and template
parameters, enforces zero hardcoded secrets, and packages them into app.zip
for Microsoft Commercial Marketplace Managed Application offers.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Any

# Azure Managed Application CreateUiDefinition specification constants
CREATE_UI_DEFINITION_SCHEMA = (
    "https://schema.management.azure.com/schemas/0.1.2-preview/"
    "CreateUIDefinition.MultiVm.json#"
)
EXPECTED_HANDLER = "Microsoft.Azure.CreateUIDef"
EXPECTED_VERSION = "0.1.2-preview"

# Deployment template schema prefix
ARM_TEMPLATE_SCHEMA_PREFIX = "https://schema.management.azure.com/schemas/"

# Secret scanning regex patterns
SECRET_PATTERNS = [
    re.compile(
        r"(?i)(?:password|secret|api[_-]?key|client[_-]?secret)\s*[:=]\s*"
        r"['\"][^\s'\"]{8,}['\"]"
    ),
    re.compile(
        r"DefaultEndpointsProtocol=https;AccountName=[^;]+;AccountKey=[A-Za-z0-9+/=]{40,}"
    ),
    re.compile(r"Endpoint=sb://[^;]+;SharedAccessKey=[A-Za-z0-9+/=]{30,}"),
    re.compile(r"AccountEndpoint=https://[^;]+;AccountKey=[A-Za-z0-9+/=]{60,}"),
    re.compile(r"ghp_[A-Za-z0-9]{36}"),
    re.compile(r"eyJ[A-Za-z0-9\-_]{20,}\.[A-Za-z0-9\-_]{20,}"),  # JWT token pattern
]


def scan_text_for_secrets(content: str) -> list[str]:
    """Scan string content for hardcoded secrets or connection strings.

    Args:
        content: Text content to scan.

    Returns:
        list[str]: Descriptions of detected secret patterns.
    """
    findings: list[str] = []
    for pattern in SECRET_PATTERNS:
        matches = pattern.findall(content)
        if matches:
            for m in matches:
                findings.append(f"Secret pattern match: {m[:30]}...")
    return findings


def scan_file_for_secrets(file_path: Path | str) -> list[str]:
    """Scan a text file for hardcoded credentials or connection strings.

    Args:
        file_path: Path to the file.

    Returns:
        list[str]: Findings detected in file.
    """
    p = Path(file_path)
    if not p.is_file():
        return [f"File not found for secret scan: {p}"]
    try:
        content = p.read_text(encoding="utf-8")
        return scan_text_for_secrets(content)
    except UnicodeDecodeError:
        return [f"Could not decode file as UTF-8: {p}"]


def validate_template_json(
    template_path: Path | str,
) -> tuple[bool, list[str], dict[str, Any]]:
    """Validate mainTemplate.json ARM template.

    Args:
        template_path: Path to mainTemplate.json.

    Returns:
        tuple[bool, list[str], dict[str, Any]]: (is_valid, errors, parsed_data)
    """
    errors: list[str] = []
    p = Path(template_path)
    if not p.is_file():
        return False, [f"mainTemplate.json not found at {p}"], {}

    try:
        content = p.read_text(encoding="utf-8")
        data = json.loads(content)
    except Exception as e:
        return False, [f"Failed to parse mainTemplate.json: {e}"], {}

    # Secret check
    secret_findings = scan_text_for_secrets(content)
    if secret_findings:
        errors.extend(
            [f"Hardcoded secret in mainTemplate.json: {s}" for s in secret_findings]
        )

    # Schema check
    schema = data.get("$schema", "")
    if not schema.startswith(ARM_TEMPLATE_SCHEMA_PREFIX):
        errors.append(f"Invalid ARM template $schema: {schema}")

    # Content version check
    if not data.get("contentVersion"):
        errors.append("Missing required field 'contentVersion'")

    # Parameters section
    if "parameters" not in data or not isinstance(data["parameters"], dict):
        errors.append("Missing or invalid 'parameters' section in ARM template")

    # Resources section
    if "resources" not in data or not isinstance(data["resources"], list):
        errors.append("Missing or invalid 'resources' array in ARM template")

    return (len(errors) == 0), errors, data


def validate_create_ui_definition(
    ui_def_path: Path | str,
) -> tuple[bool, list[str], dict[str, Any]]:
    """Validate createUiDefinition.json portal UI schema and structure.

    Args:
        ui_def_path: Path to createUiDefinition.json.

    Returns:
        tuple[bool, list[str], dict[str, Any]]: (is_valid, errors, parsed_data)
    """
    errors: list[str] = []
    p = Path(ui_def_path)
    if not p.is_file():
        return False, [f"createUiDefinition.json not found at {p}"], {}

    try:
        content = p.read_text(encoding="utf-8")
        data = json.loads(content)
    except Exception as e:
        return False, [f"Failed to parse createUiDefinition.json: {e}"], {}

    # Secret check
    secret_findings = scan_text_for_secrets(content)
    if secret_findings:
        errors.extend(
            [
                f"Hardcoded secret in createUiDefinition.json: {s}"
                for s in secret_findings
            ]
        )

    # Schema check
    schema = data.get("$schema", "")
    if schema != CREATE_UI_DEFINITION_SCHEMA:
        errors.append(
            f"Invalid $schema in createUiDefinition.json. "
            f"Expected '{CREATE_UI_DEFINITION_SCHEMA}', got '{schema}'"
        )

    # Handler check
    handler = data.get("handler", "")
    if handler != EXPECTED_HANDLER:
        errors.append(
            f"Invalid handler in createUiDefinition.json. "
            f"Expected '{EXPECTED_HANDLER}', got '{handler}'"
        )

    # Version check
    version = data.get("version", "")
    if version != EXPECTED_VERSION:
        errors.append(
            f"Invalid version in createUiDefinition.json. "
            f"Expected '{EXPECTED_VERSION}', got '{version}'"
        )

    # Parameters section
    params = data.get("parameters", {})
    if not isinstance(params, dict):
        errors.append("Field 'parameters' must be an object in createUiDefinition.json")
    else:
        # Check basics
        if "basics" not in params:
            errors.append("Missing required 'basics' section in parameters")

        # Check steps
        steps = params.get("steps", [])
        if not isinstance(steps, list) or len(steps) == 0:
            errors.append("Field 'steps' must be a non-empty list of step definitions")
        else:
            for idx, step in enumerate(steps):
                if not isinstance(step, dict):
                    errors.append(f"steps[{idx}] must be an object")
                    continue
                if not step.get("name"):
                    errors.append(f"steps[{idx}] is missing required 'name'")
                if not step.get("label"):
                    errors.append(f"steps[{idx}] is missing required 'label'")
                elements = step.get("elements", [])
                if not isinstance(elements, list) or len(elements) == 0:
                    errors.append(
                        f"steps[{idx}] ('{step.get('name')}') must have non-empty "
                        "'elements'"
                    )

        # Check outputs
        outputs = params.get("outputs", {})
        if not isinstance(outputs, dict) or len(outputs) == 0:
            errors.append(
                "Field 'outputs' must be a non-empty object mapping to template "
                "parameters"
            )

    return (len(errors) == 0), errors, data


def validate_parameter_parity(
    template_data: dict[str, Any],
    ui_data: dict[str, Any],
) -> tuple[bool, list[str]]:
    """Verify parity between UI outputs and mainTemplate.json parameters.

    Ensures:
    1. Every output in createUiDefinition matches a defined template parameter.
    2. Every mandatory parameter (no defaultValue) has a corresponding output.

    Args:
        template_data: Parsed ARM template JSON.
        ui_data: Parsed createUiDefinition JSON.

    Returns:
        tuple[bool, list[str]]: (is_valid, list of error messages)
    """
    errors: list[str] = []
    template_params = template_data.get("parameters", {})
    ui_outputs = ui_data.get("parameters", {}).get("outputs", {})

    template_param_names = set(template_params.keys())
    ui_output_names = set(ui_outputs.keys())

    # Check for unmatched outputs (UI outputs that don't exist in template)
    unmatched_outputs = ui_output_names - template_param_names
    if unmatched_outputs:
        errors.append(
            "createUiDefinition outputs not found in mainTemplate.json parameters: "
            f"{sorted(unmatched_outputs)}"
        )

    # Check that any template parameter WITHOUT a defaultValue is present in UI outputs
    missing_mandatory = []
    for param_name, param_def in template_params.items():
        if isinstance(param_def, dict) and "defaultValue" not in param_def:
            if param_name not in ui_output_names:
                missing_mandatory.append(param_name)

    if missing_mandatory:
        errors.append(
            "Mandatory mainTemplate parameters (no defaultValue) missing from "
            f"createUiDefinition outputs: {sorted(missing_mandatory)}"
        )

    return (len(errors) == 0), errors


def create_managed_app_package(
    infra_dir: Path | str,
    output_zip: Path | str,
) -> Path:
    """Validate and package mainTemplate.json and createUiDefinition.json into app.zip.

    Args:
        infra_dir: Directory containing mainTemplate.json and createUiDefinition.json.
        output_zip: Destination zip archive path.

    Returns:
        Path: Path to created zip file.

    Raises:
        ValueError: If validation fails.
    """
    infra_p = Path(infra_dir)
    out_zip = Path(output_zip)

    template_path = infra_p / "mainTemplate.json"
    ui_def_path = infra_p / "createUiDefinition.json"

    # 1. Validate mainTemplate.json
    ok_t, err_t, t_data = validate_template_json(template_path)
    if not ok_t:
        raise ValueError(f"mainTemplate.json validation failed: {'; '.join(err_t)}")

    # 2. Validate createUiDefinition.json
    ok_u, err_u, u_data = validate_create_ui_definition(ui_def_path)
    if not ok_u:
        msg = "; ".join(err_u)
        raise ValueError(f"createUiDefinition.json validation failed: {msg}")

    # 3. Check parameter parity
    ok_p, err_p = validate_parameter_parity(t_data, u_data)
    if not ok_p:
        raise ValueError(f"Parameter parity validation failed: {'; '.join(err_p)}")

    # 4. Assemble app.zip
    out_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(template_path, arcname="mainTemplate.json")
        zf.write(ui_def_path, arcname="createUiDefinition.json")

    # 5. Verify the package
    ok_v, err_v = verify_managed_app_package(out_zip)
    if not ok_v:
        raise ValueError(f"Package verification failed: {'; '.join(err_v)}")

    return out_zip


def verify_managed_app_package(zip_path: Path | str) -> tuple[bool, list[str]]:
    """Verify that a managed application zip archive meets marketplace requirements.

    Args:
        zip_path: Path to the zip file.

    Returns:
        tuple[bool, list[str]]: (is_valid, list of errors)
    """
    errors: list[str] = []
    p = Path(zip_path)
    if not p.is_file():
        return False, [f"Package archive not found at {p}"]

    try:
        with zipfile.ZipFile(p, mode="r") as zf:
            namelist = zf.namelist()
            required_files = {"mainTemplate.json", "createUiDefinition.json"}
            missing = required_files - set(namelist)
            if missing:
                errors.append(f"Zip archive missing required files: {sorted(missing)}")

            # Read and scan contents from inside the zip
            for fname in required_files:
                if fname in namelist:
                    content = zf.read(fname).decode("utf-8")
                    findings = scan_text_for_secrets(content)
                    if findings:
                        errors.append(
                            f"Hardcoded secrets detected in {fname} inside zip archive"
                        )
    except Exception as e:
        errors.append(f"Failed to read zip archive: {e}")

    return (len(errors) == 0), errors


def main() -> int:
    """CLI entry point for Managed Application packaging."""
    parser = argparse.ArgumentParser(
        description="Azure Managed Application packaging and validation utility"
    )
    parser.add_argument(
        "--infra-dir",
        "-i",
        default="infra",
        help="Path to directory containing templates",
    )
    parser.add_argument(
        "--output-zip",
        "-o",
        default="packaging/managed_app/app.zip",
        help="Output path for app.zip",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Run validation checks without writing zip file",
    )

    args = parser.parse_args()
    infra_dir = Path(args.infra_dir)
    output_zip = Path(args.output_zip)

    template_path = infra_dir / "mainTemplate.json"
    ui_def_path = infra_dir / "createUiDefinition.json"

    print("=== Azure Managed Application Validator & Packager ===")
    print(f"Checking template: {template_path}")
    ok_t, err_t, t_data = validate_template_json(template_path)
    if not ok_t:
        print(
            "ERROR: mainTemplate.json validation failed:\n  " + "\n  ".join(err_t),
            file=sys.stderr,
        )
        return 1
    print("  [PASS] mainTemplate.json is valid and contains zero secrets.")

    print(f"Checking UI definition: {ui_def_path}")
    ok_u, err_u, u_data = validate_create_ui_definition(ui_def_path)
    if not ok_u:
        print(
            "ERROR: createUiDefinition.json validation failed:\n  "
            + "\n  ".join(err_u),
            file=sys.stderr,
        )
        return 1
    print("  [PASS] createUiDefinition.json conforms to schema and zero secrets.")

    print("Checking parameter parity between UI outputs and template parameters...")
    ok_p, err_p = validate_parameter_parity(t_data, u_data)
    if not ok_p:
        print(
            "ERROR: Parameter parity validation failed:\n  " + "\n  ".join(err_p),
            file=sys.stderr,
        )
        return 1
    output_count = len(u_data["parameters"]["outputs"])
    print(f"  [PASS] Parameter parity confirmed ({output_count} outputs mapped).")

    if args.validate_only:
        print("Validation complete. Skipping package creation (--validate-only).")
        return 0

    print(f"Building Managed Application package: {output_zip}")
    try:
        pkg_path = create_managed_app_package(infra_dir, output_zip)
        print(f"  [PASS] Package successfully created: {pkg_path}")
        print(f"         File size: {pkg_path.stat().st_size:,} bytes")
    except Exception as e:
        print(f"ERROR: Packaging failed: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
