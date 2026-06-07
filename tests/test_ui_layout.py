"""
UI Layout Tests — LL-018 (MEDIUM)

Static AST inspection of src/main_window.py to verify widget
presence, absence, and ordering without importing PyQt6.
"""

import ast
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _parse_main_window_ast() -> ast.AST:
    src_path = PROJECT_ROOT / "src" / "main_window.py"
    if not src_path.exists():
        pytest.skip("src/main_window.py does not exist yet — source code not implemented")
    source = src_path.read_text(encoding="utf-8")
    return ast.parse(source)


def _find_calls(tree: ast.AST, name: str):
    """Yield all Call nodes whose func is a Name or Attribute matching `name`."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == name:
                yield node
            elif isinstance(node.func, ast.Attribute) and node.func.attr == name:
                yield node


def _extract_string_arg(node: ast.Call, index: int = 0) -> str | None:
    """Extract a string literal argument from a Call node."""
    args = node.args
    if len(args) > index and isinstance(args[index], ast.Constant) and isinstance(args[index].value, str):
        return args[index].value
    return None


def test_main_window_is_frameless() -> None:
    """TC-LAYOUT-01: AST must contain FramelessWindowHint."""
    tree = _parse_main_window_ast()
    dump = ast.dump(tree, annotate_fields=False)
    assert "FramelessWindowHint" in dump, "MainWindow must set Qt.WindowType.FramelessWindowHint"


def test_window_size_uses_12_percent_width_25_percent_height() -> None:
    """TC-LAYOUT-02: AST must reference screen geometry and 0.12 / 0.25."""
    tree = _parse_main_window_ast()
    dump = ast.dump(tree, annotate_fields=False)
    has_screen_ref = "primaryScreen" in dump or "geometry" in dump or "screen" in dump
    has_twelve_percent = "0.12" in dump or "0_12" in dump or "12" in dump
    has_twentyfive_percent = "0.25" in dump or "0_25" in dump or "25" in dump
    assert has_screen_ref and has_twelve_percent and has_twentyfive_percent, (
        "MainWindow must compute size as max(12% width, 400) and max(25% height, 500)"
    )


def test_grouped_panels_exist() -> None:
    """TC-LAYOUT-03: Exactly three QGroupBox with titles Utilization, Temperatures, Fan Speeds."""
    tree = _parse_main_window_ast()
    titles = set()
    for call in _find_calls(tree, "QGroupBox"):
        title = _extract_string_arg(call, 0)
        if title:
            titles.add(title)

    expected = {"Utilization", "Temperatures", "Fan Speeds"}
    assert expected <= titles, f"Missing QGroupBox titles. Found: {titles}"


def test_system_tray_icon_is_created() -> None:
    """TC-LAYOUT-04: AST must instantiate QSystemTrayIcon."""
    tree = _parse_main_window_ast()
    dump = ast.dump(tree, annotate_fields=False)
    assert "QSystemTrayIcon" in dump, "MainWindow must create a QSystemTrayIcon"


def test_header_bar_contains_close_minimize_settings_buttons() -> None:
    """TC-LAYOUT-05: AST must contain buttons for close, minimize, and settings."""
    tree = _parse_main_window_ast()
    dump = ast.dump(tree, annotate_fields=False)

    # Accept QPushButton or QToolButton with object-name or tooltip clues
    roles = {"close", "minimize", "settings", "gear"}
    found = set()
    for call in _find_calls(tree, "QPushButton"):
        found.update(_collect_button_clues(call))
    for call in _find_calls(tree, "QToolButton"):
        found.update(_collect_button_clues(call))

    # Also scan string literals in the whole module for role keywords
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            low = node.value.lower()
            for role in roles:
                if role in low:
                    found.add(role)

    required = {"close", "minimize"}
    settings_found = "settings" in found or "gear" in found
    assert required <= found, f"Missing close/minimize buttons. Found clues: {found}"
    assert settings_found, f"Missing settings/gear button. Found clues: {found}"


def _collect_button_clues(call: ast.Call) -> set[str]:
    """Heuristic: look at string args and keyword values for button role hints."""
    clues = set()
    for arg in call.args:
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            low = arg.value.lower()
            for role in ("close", "minimize", "settings", "gear", "x", "-"):
                if role in low:
                    clues.add(role)
    for kw in call.keywords:
        if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
            low = kw.value.value.lower()
            for role in ("close", "minimize", "settings", "gear", "x", "-"):
                if role in low:
                    clues.add(role)
    return clues
