"""
J.A.R.V.I.S. Sci-Fi HUD Modular Panels Package
Contains modular CustomTkinter HUD components for telemetry, reactor canvas,
media controller, task directives, environment, and quick controls.
"""

from gui.panels.telemetry_panel import TelemetryPanel
from gui.panels.reactor_panel import ReactorPanel
from gui.panels.media_panel import MediaPanel
from gui.panels.todo_panel import TodoPanel
from gui.panels.environment_panel import EnvironmentPanel
from gui.panels.controls_panel import ControlsPanel

__all__ = [
    "TelemetryPanel",
    "ReactorPanel",
    "MediaPanel",
    "TodoPanel",
    "EnvironmentPanel",
    "ControlsPanel",
]
