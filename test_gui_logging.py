import os
import re
import pytest

REFACTORED_SCRIPTS = [
    "File_Server_Legacy_Compatible.ps1",
    "File_Server_Max_Performance.ps1",
    "Server_Ultimate_Tuner.ps1",
    "SMB_Tuner.ps1",
    "Universal_Server_Tuner.ps1",
]


def test_gui_logging_script_exists():
    assert os.path.isfile("GuiLogging.ps1"), "GuiLogging.ps1 must exist in repo root"


def test_gui_logging_defines_write_gui_log():
    with open("GuiLogging.ps1", "r", encoding="utf-8") as f:
        content = f.read()
    assert re.search(r"function\s+Write-GuiLog\b", content), "GuiLogging.ps1 must define function Write-GuiLog"


def test_refactored_scripts_dot_source_gui_logging():
    for script_name in REFACTORED_SCRIPTS:
        assert os.path.isfile(script_name), f"{script_name} must exist"
        with open(script_name, "r", encoding="utf-8") as f:
            content = f.read()

        # Ensure individual function definition is removed
        assert not re.search(
            r"function\s+Write-GuiLog\b", content
        ), f"{script_name} should not define duplicate function Write-GuiLog"

        # Ensure dot-sourcing is included
        assert (
            r'. "$PSScriptRoot\GuiLogging.ps1"' in content
        ), f"{script_name} must dot-source GuiLogging.ps1"


def test_write_gui_log_calls_exist_in_refactored_scripts():
    for script_name in REFACTORED_SCRIPTS:
        with open(script_name, "r", encoding="utf-8") as f:
            content = f.read()
        assert "Write-GuiLog" in content, f"{script_name} should still call Write-GuiLog"


def test_powershell_scripts_basic_syntax():
    all_ps1 = [f for f in os.listdir(".") if f.endswith(".ps1")]
    for ps1_file in all_ps1:
        with open(ps1_file, "r", encoding="utf-8") as f:
            content = f.read()
        # Basic balanced braces check
        assert content.count("{") == content.count("}"), f"Unbalanced curly braces in {ps1_file}"
        assert content.count("(") == content.count(")"), f"Unbalanced parentheses in {ps1_file}"
