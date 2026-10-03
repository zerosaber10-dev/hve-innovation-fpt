"""Teams packaging module."""

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

__all__ = [
    "create_teams_package",
    "generate_color_icon",
    "generate_outline_icon",
    "parse_png_dimensions",
    "scan_file_for_secrets",
    "scan_text_for_secrets",
    "validate_icons",
    "validate_manifest",
]
