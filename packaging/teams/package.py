"""Teams app packaging and manifest validation utility.

Builds valid Teams app manifest packages with compliant 192x192 color and
32x32 outline icons, validates schema compliance, checks asset dimensions,
and ensures zero hardcoded secrets.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import struct
import sys
import uuid
import zipfile
import zlib
from pathlib import Path
from typing import Any

# Allowed manifest versions per Microsoft Teams Developer documentation
SUPPORTED_MANIFEST_VERSIONS = ("1.16", "1.17")

# Known secret patterns for zero-secrets scanning
SECRET_PATTERNS = [
    re.compile(
        r"(?i)(?:password|secret|api[_-]?key|client[_-]?secret)\s*[:=]\s*['\"][^\s'\"]{8,}['\"]"
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
    """Scan string content for hardcoded secrets, connection strings, or credentials."""
    findings = []
    for pattern in SECRET_PATTERNS:
        matches = pattern.findall(content)
        if matches:
            for m in matches:
                findings.append(f"Secret pattern match: {m[:30]}...")
    return findings


def scan_file_for_secrets(file_path: Path | str) -> list[str]:
    """Scan a text file for hardcoded credentials or connection strings."""
    p = Path(file_path)
    if not p.is_file():
        return []
    try:
        content = p.read_text(encoding="utf-8")
        return scan_text_for_secrets(content)
    except UnicodeDecodeError:
        return []


def _create_png(
    width: int,
    height: int,
    pixel_fn: Any,
) -> bytes:
    """Generate raw PNG bytes using pure Python standard library struct and zlib."""
    raw_scanlines = bytearray()
    for y in range(height):
        raw_scanlines.append(0)  # Filter type 0: None
        for x in range(width):
            r, g, b, a = pixel_fn(x, y)
            raw_scanlines.extend([r, g, b, a])

    compressed_idat = zlib.compress(bytes(raw_scanlines), level=9)

    png = bytearray(b"\x89PNG\r\n\x1a\n")

    # IHDR chunk: width (4), height (4), bit depth (1)=8, color type (1)=6 (RGBA),
    # compression (1)=0, filter (1)=0, interlace (1)=0
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    png.extend(struct.pack(">I", len(ihdr_data)))
    png.extend(b"IHDR")
    png.extend(ihdr_data)
    png.extend(struct.pack(">I", zlib.crc32(b"IHDR" + ihdr_data)))

    # IDAT chunk
    png.extend(struct.pack(">I", len(compressed_idat)))
    png.extend(b"IDAT")
    png.extend(compressed_idat)
    png.extend(struct.pack(">I", zlib.crc32(b"IDAT" + compressed_idat)))

    # IEND chunk
    png.extend(struct.pack(">I", 0))
    png.extend(b"IEND")
    png.extend(struct.pack(">I", zlib.crc32(b"IEND")))

    return bytes(png)


def parse_png_dimensions(data: bytes) -> tuple[int, int, int]:
    """Parse PNG byte data to extract width, height, and color type.

    Returns:
        tuple[int, int, int]: (width, height, color_type)
    """
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("Invalid PNG signature")

    # Locate IHDR
    chunk_len = struct.unpack(">I", data[8:12])[0]
    chunk_type = data[12:16]
    if chunk_type != b"IHDR" or chunk_len < 13:
        raise ValueError("First chunk must be valid IHDR")

    width, height, bit_depth, color_type = struct.unpack(">IIBB", data[16:26])
    return width, height, color_type


def generate_color_icon(output_path: Path | str) -> Path:
    """Generate Teams 192x192 color icon with blue (#0078D4) and white HR motif."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    def pixel_color(x: int, y: int) -> tuple[int, int, int, int]:
        # Background: Microsoft Blue #0078D4
        bg_r, bg_g, bg_b, bg_a = 0, 120, 212, 255

        # Rounded rectangle boundary (radius 24)
        corner_r = 24
        in_corner = False
        dist = 0.0
        if x < corner_r and y < corner_r:
            dist = math.hypot(x - corner_r, y - corner_r)
            in_corner = dist > corner_r
        elif x >= 192 - corner_r and y < corner_r:
            dist = math.hypot(x - (192 - corner_r - 1), y - corner_r)
            in_corner = dist > corner_r
        elif x < corner_r and y >= 192 - corner_r:
            dist = math.hypot(x - corner_r, y - (192 - corner_r - 1))
            in_corner = dist > corner_r
        elif x >= 192 - corner_r and y >= 192 - corner_r:
            dist = math.hypot(x - (192 - corner_r - 1), y - (192 - corner_r - 1))
            in_corner = dist > corner_r

        if in_corner:
            return 0, 0, 0, 0

        # Draw white stylized calendar / time symbol (center x: 48..144, y: 44..148)
        # Calendar outline
        if 48 <= x <= 144 and 52 <= y <= 148:
            # Top header bar (y 52..72)
            if y <= 72:
                return 255, 255, 255, 255
            # Calendar outer border (4px)
            if x <= 52 or x >= 140 or y >= 144:
                return 255, 255, 255, 255
            # Clock hands in center (center at 96, 108)
            cx, cy = 96, 108
            clock_dist = math.hypot(x - cx, y - cy)
            if 18 <= clock_dist <= 22:
                return 255, 255, 255, 255
            # Hour hand pointing to 3 o'clock (horizontal)
            if cy - 2 <= y <= cy + 2 and cx <= x <= cx + 14:
                return 255, 255, 255, 255
            # Minute hand pointing to 12 o'clock (vertical)
            if cx - 2 <= x <= cx + 2 and cy - 14 <= y <= cy:
                return 255, 255, 255, 255

        # Calendar binder rings at top
        if (64 <= x <= 72 or 120 <= x <= 128) and 40 <= y <= 56:
            return 255, 255, 255, 255

        return bg_r, bg_g, bg_b, bg_a

    png_bytes = _create_png(192, 192, pixel_color)
    out.write_bytes(png_bytes)
    return out


def generate_outline_icon(output_path: Path | str) -> Path:
    """Generate Teams 32x32 outline icon (white with transparent background)."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    def pixel_outline(x: int, y: int) -> tuple[int, int, int, int]:
        # Transparent background
        transparent = (0, 0, 0, 0)
        white = (255, 255, 255, 255)

        # Calendar outline in 32x32: (x: 4..27, y: 5..27)
        if 4 <= x <= 27 and 6 <= y <= 27:
            # Header bar
            if y <= 10:
                return white
            # Outer border
            if x in (4, 5, 26, 27) or y in (26, 27):
                return white
            # Center clock circle (radius 5 at 16, 18)
            dist = math.hypot(x - 16, y - 18)
            if 3.5 <= dist <= 5.5:
                return white
            # Center clock hands
            if (y == 18 and 16 <= x <= 19) or (x == 16 and 15 <= y <= 18):
                return white

        # Binder rings
        if (7 <= x <= 9 or 22 <= x <= 24) and 3 <= y <= 7:
            return white

        return transparent

    png_bytes = _create_png(32, 32, pixel_outline)
    out.write_bytes(png_bytes)
    return out


def validate_manifest(
    manifest_data: dict[str, Any] | str | Path,
) -> tuple[bool, list[str]]:
    """Validate a Teams app manifest against Teams schema v1.16/v1.17 rules.

    Returns:
        tuple[bool, list[str]]: (is_valid, list of error messages)
    """
    errors: list[str] = []

    if isinstance(manifest_data, (str, Path)):
        p = Path(manifest_data)
        if not p.is_file():
            return False, [f"Manifest file not found: {p}"]
        try:
            content = p.read_text(encoding="utf-8")
            data = json.loads(content)
        except Exception as e:
            return False, [f"Failed to parse manifest JSON: {e}"]
    else:
        data = manifest_data
        content = json.dumps(manifest_data)

    # 1. Zero secrets check
    secret_findings = scan_text_for_secrets(content)
    if secret_findings:
        errors.extend([f"Hardcoded secret in manifest: {f}" for f in secret_findings])

    # 2. Schema check
    schema = data.get("$schema", "")
    if not schema.startswith(
        "https://developer.microsoft.com/en-us/json-schemas/teams/"
    ):
        errors.append(f"Invalid $schema URL: {schema}")

    # 3. Manifest version check
    manifest_version = data.get("manifestVersion", "")
    if manifest_version not in SUPPORTED_MANIFEST_VERSIONS:
        errors.append(
            f"Unsupported manifestVersion '{manifest_version}'. "
            f"Expected one of {SUPPORTED_MANIFEST_VERSIONS}"
        )

    # 4. App ID check (must be valid UUID format or ${{APP_ID}} template)
    app_id = data.get("id", "")
    if not app_id:
        errors.append("Missing required field 'id'")
    elif not app_id.startswith("${{"):
        try:
            uuid.UUID(app_id)
        except ValueError:
            errors.append(f"Field 'id' must be a valid UUID string, got: '{app_id}'")

    # 5. Version check (semver)
    version = data.get("version", "")
    if not version or not re.match(r"^\d+\.\d+\.\d+(\.[0-9A-Za-z\-]+)?$", version):
        errors.append(f"Invalid semver version: '{version}'")

    # 6. Name checks
    name = data.get("name", {})
    if not isinstance(name, dict):
        errors.append("Field 'name' must be an object")
    else:
        short_name = name.get("short", "")
        full_name = name.get("full", "")
        if not short_name:
            errors.append("Field 'name.short' is required")
        elif len(short_name) > 30:
            errors.append(
                f"'name.short' length {len(short_name)} exceeds maximum 30 characters"
            )
        if full_name and len(full_name) > 100:
            errors.append(
                f"'name.full' length {len(full_name)} exceeds maximum 100 characters"
            )

    # 7. Description checks
    description = data.get("description", {})
    if not isinstance(description, dict):
        errors.append("Field 'description' must be an object")
    else:
        short_desc = description.get("short", "")
        full_desc = description.get("full", "")
        if not short_desc:
            errors.append("Field 'description.short' is required")
        elif len(short_desc) > 80:
            errors.append(
                f"'description.short' length {len(short_desc)} exceeds max 80 chars"
            )
        if not full_desc:
            errors.append("Field 'description.full' is required")
        elif len(full_desc) > 4000:
            errors.append(
                f"'description.full' length {len(full_desc)} exceeds max 4000 chars"
            )

    # 8. Icons check
    icons = data.get("icons", {})
    if not isinstance(icons, dict):
        errors.append("Field 'icons' must be an object")
    else:
        if not icons.get("color"):
            errors.append("Field 'icons.color' is required")
        if not icons.get("outline"):
            errors.append("Field 'icons.outline' is required")

    # 9. Accent color check
    accent = data.get("accentColor", "")
    if not accent or not re.match(r"^#[0-9A-Fa-f]{6}$", accent):
        errors.append(
            f"Invalid accentColor '{accent}'. Must be a hex color like #0078D4"
        )

    # 10. Developer checks
    developer = data.get("developer", {})
    if not isinstance(developer, dict):
        errors.append("Field 'developer' must be an object")
    else:
        if not developer.get("name"):
            errors.append("Field 'developer.name' is required")
        for url_field in ("websiteUrl", "privacyUrl", "termsOfUseUrl"):
            val = developer.get(url_field, "")
            if not val:
                errors.append(f"Field 'developer.{url_field}' is required")
            elif not val.startswith("https://"):
                errors.append(
                    f"'developer.{url_field}' must be a secure HTTPS URL, got '{val}'"
                )

    # 11. Bots configuration check
    bots = data.get("bots", [])
    if bots:
        for idx, bot in enumerate(bots):
            bot_id = bot.get("botId", "")
            if not bot_id:
                errors.append(f"bots[{idx}].botId is required")
            scopes = bot.get("scopes", [])
            if not scopes:
                errors.append(f"bots[{idx}].scopes cannot be empty")

    return (len(errors) == 0), errors


def validate_icons(
    color_icon_path: Path | str,
    outline_icon_path: Path | str,
) -> tuple[bool, list[str]]:
    """Validate dimension and format compliance for color and outline icons.

    - color.png must be 192x192 PNG
    - outline.png must be 32x32 transparent PNG
    """
    errors: list[str] = []
    c_path = Path(color_icon_path)
    o_path = Path(outline_icon_path)

    # Validate color icon
    if not c_path.is_file():
        errors.append(f"Color icon not found at {c_path}")
    else:
        try:
            w, h, color_type = parse_png_dimensions(c_path.read_bytes())
            if (w, h) != (192, 192):
                errors.append(f"Color icon dimensions must be 192x192, got {w}x{h}")
        except Exception as e:
            errors.append(f"Failed to parse color icon PNG: {e}")

    # Validate outline icon
    if not o_path.is_file():
        errors.append(f"Outline icon not found at {o_path}")
    else:
        try:
            w, h, color_type = parse_png_dimensions(o_path.read_bytes())
            if (w, h) != (32, 32):
                errors.append(f"Outline icon dimensions must be 32x32, got {w}x{h}")
            if color_type != 6:  # 6 = RGBA with alpha channel
                errors.append(
                    "Outline icon must have transparency (RGBA color type 6), "
                    f"got type {color_type}"
                )
        except Exception as e:
            errors.append(f"Failed to parse outline icon PNG: {e}")

    return (len(errors) == 0), errors


def create_teams_package(
    source_dir: Path | str,
    output_zip: Path | str,
    bot_id_override: str | None = None,
) -> Path:
    """Validate assets and create the standard Teams distribution zip archive.

    Args:
        source_dir: Path to directory containing manifest.json, color.png, outline.png
        output_zip: Output zip file path
        bot_id_override: Optional bot application ID to substitute in manifest

    Returns:
        Path: Path to created zip file

    Raises:
        ValueError: If validation fails
    """
    src = Path(source_dir)
    out_zip = Path(output_zip)

    manifest_path = src / "manifest.json"
    color_path = src / "color.png"
    outline_path = src / "outline.png"

    # Ensure icons exist, or generate them automatically if missing
    if not color_path.is_file():
        generate_color_icon(color_path)
    if not outline_path.is_file():
        generate_outline_icon(outline_path)

    # 1. Validate manifest
    manifest_bytes = manifest_path.read_text(encoding="utf-8")
    if bot_id_override:
        manifest_bytes = manifest_bytes.replace("${{BOT_ID}}", bot_id_override)
        manifest_bytes = re.sub(
            r'"botId":\s*"[0-9a-fA-F\-]{36}"',
            f'"botId": "{bot_id_override}"',
            manifest_bytes,
        )

    manifest_data = json.loads(manifest_bytes)
    is_valid_manifest, manifest_errors = validate_manifest(manifest_data)
    if not is_valid_manifest:
        raise ValueError(f"Manifest validation failed: {'; '.join(manifest_errors)}")

    # 2. Validate icons
    is_valid_icons, icon_errors = validate_icons(color_path, outline_path)
    if not is_valid_icons:
        raise ValueError(f"Icon validation failed: {'; '.join(icon_errors)}")

    # 3. Create zip package
    out_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        # Write manifest with substituted content
        zf.writestr("manifest.json", json.dumps(manifest_data, indent=2))
        zf.write(color_path, arcname="color.png")
        zf.write(outline_path, arcname="outline.png")

    # 4. Verify created zip package
    with zipfile.ZipFile(out_zip, mode="r") as zf:
        namelist = zf.namelist()
        required_names = {"manifest.json", "color.png", "outline.png"}
        if not required_names.issubset(set(namelist)):
            raise ValueError(f"Zip verification failed. Missing files from {namelist}")

    return out_zip


def main() -> int:
    """CLI entry point for packaging and validation."""
    parser = argparse.ArgumentParser(
        description="Teams app manifest validator and package builder"
    )
    parser.add_argument(
        "--source-dir",
        "-s",
        default="packaging/teams",
        help="Path to Teams packaging directory",
    )
    parser.add_argument(
        "--output-zip",
        "-o",
        default="packaging/teams/hr-time-leave-teams.zip",
        help="Output zip path",
    )
    parser.add_argument(
        "--bot-id", default=None, help="Optional bot application ID override"
    )
    parser.add_argument(
        "--generate-icons",
        action="store_true",
        help="Generate 192x192 and 32x32 icons if needed",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Run validation without generating zip",
    )

    args = parser.parse_args()
    src = Path(args.source_dir)

    if args.generate_icons:
        c = generate_color_icon(src / "color.png")
        o = generate_outline_icon(src / "outline.png")
        print(f"Generated icons: {c}, {o}")

    manifest_p = src / "manifest.json"
    ok_m, m_errs = validate_manifest(manifest_p)
    if not ok_m:
        print(f"Manifest errors: {m_errs}", file=sys.stderr)
        return 1
    print("Manifest schema validation passed.")

    ok_i, i_errs = validate_icons(src / "color.png", src / "outline.png")
    if not ok_i:
        print(f"Icon errors: {i_errs}", file=sys.stderr)
        return 1
    print("Icon assets validation passed.")

    if not args.validate_only:
        zip_path = create_teams_package(src, args.output_zip, args.bot_id)
        print(f"Teams package zip created successfully: {zip_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
