"""
Stark Autonomous Project Studio Panel for J.A.R.V.I.S. Sci-Fi HUD
Displays real-time multi-day sprint progress, active agent status, and 1-click sprint actions.
"""

import os
import subprocess
import customtkinter as ctk

CYAN_BRIGHT = "#00f0ff"
GREEN_ACCENT = "#00ff88"
TEXT_CYAN = "#80d8ff"
TEXT_MUTED = "#607d8b"
BG_DARK = "#041426"
FONT_SMALL = ("Consolas", 9)
FONT_BOLD = ("Consolas", 10, "bold")


class AgencyPanel:
    def __init__(self, parent, panel_factory, notif_callback=None):
        self.notif_cb = notif_callback
        self.panel = panel_factory(parent, "AUTONOMOUS PROJECT STUDIO", icon="🏢")
        self.panel.pack(fill="x", pady=(0, 8))

        # Top status row
        self.header_row = ctk.CTkFrame(self.panel, fg_color="transparent")
        self.header_row.pack(fill="x", padx=10, pady=(2, 2))

        self.project_lbl = ctk.CTkLabel(
            self.header_row,
            text="STUDIO: IDLE",
            font=FONT_BOLD,
            text_color=CYAN_BRIGHT
        )
        self.project_lbl.pack(side="left")

        self.sprint_badge = ctk.CTkLabel(
            self.header_row,
            text="SPRINT 0/5",
            font=FONT_SMALL,
            text_color=GREEN_ACCENT
        )
        self.sprint_badge.pack(side="right")

        # Sprint progress frame
        self.body_frame = ctk.CTkFrame(self.panel, fg_color=BG_DARK, corner_radius=4)
        self.body_frame.pack(fill="x", padx=8, pady=(2, 4))

        self.agent_lbl = ctk.CTkLabel(
            self.body_frame,
            text="Team: Ready for client intake directives.",
            font=FONT_SMALL,
            text_color=TEXT_CYAN,
            anchor="w"
        )
        self.agent_lbl.pack(fill="x", padx=8, pady=(4, 2))

        self.milestone_lbl = ctk.CTkLabel(
            self.body_frame,
            text="Voice: 'assemble team to build <name>'",
            font=FONT_SMALL,
            text_color=TEXT_MUTED,
            anchor="w"
        )
        self.milestone_lbl.pack(fill="x", padx=8, pady=(0, 4))

        # Action Buttons Dock
        self.btn_row = ctk.CTkFrame(self.panel, fg_color="transparent")
        self.btn_row.pack(fill="x", padx=8, pady=(2, 6))

        self.advance_btn = ctk.CTkButton(
            self.btn_row,
            text="▶ Advance Sprint",
            width=110,
            height=22,
            font=FONT_SMALL,
            fg_color="#062f48",
            hover_color="#00aa88",
            border_color=CYAN_BRIGHT,
            border_width=1,
            text_color=GREEN_ACCENT,
            command=self._on_advance_sprint
        )
        self.advance_btn.pack(side="left", padx=(0, 4))

        self.folder_btn = ctk.CTkButton(
            self.btn_row,
            text="📂 Open Code",
            width=90,
            height=22,
            font=FONT_SMALL,
            fg_color="#062238",
            hover_color="#064060",
            border_color=CYAN_BRIGHT,
            border_width=1,
            text_color=TEXT_CYAN,
            command=self._on_open_folder
        )
        self.folder_btn.pack(side="left")

        self.active_project_id = None
        self.active_project_path = None

    def _notify(self, text):
        if self.notif_cb:
            try:
                self.notif_cb(text)
            except Exception:
                pass

    def _on_advance_sprint(self):
        if not self.active_project_id:
            self._notify("No active project in studio queue.")
            return
        try:
            from core.agency import execute_sprint_stage
            res = execute_sprint_stage(self.active_project_id)
            if res.get("success"):
                msg = f"Sprint {res['sprint_number']} executed for Project."
                self._notify(msg)
                self.refresh()
            else:
                self._notify(res.get("message", "Unable to advance sprint."))
        except Exception as e:
            self._notify(f"Sprint error: {e}")

    def _on_open_folder(self):
        if self.active_project_path and os.path.exists(self.active_project_path):
            try:
                os.startfile(self.active_project_path)
            except Exception as e:
                self._notify(f"Cannot open folder: {e}")
        else:
            self._notify("Project directory not found on disk.")

    def refresh(self):
        """Query SQLite projects table and update live HUD studio state."""
        try:
            from core.agency import get_all_projects, get_project_summary
            projects = get_all_projects()

            if not projects:
                self.active_project_id = None
                self.active_project_path = None
                self.project_lbl.configure(text="STUDIO: IDLE", text_color=TEXT_MUTED)
                self.sprint_badge.configure(text="0/5 SPRINTS", text_color=TEXT_MUTED)
                self.agent_lbl.configure(text="Team: Standby for project directives.")
                self.milestone_lbl.configure(text="Voice: 'assemble team to build <name>'")
                return

            # Display most recent active or latest project
            top = projects[0]
            self.active_project_id = top["id"]
            self.active_project_path = top["root_dir"]
            p_name = top["name"].replace("_", " ").upper()
            status = top["status"].replace("_", " ").upper()
            curr_sprint = top["current_sprint"]
            total_sprints = top["total_sprints"]

            # Archetype detection
            meta = top.get("metadata", {})
            archetype = meta.get("archetype", "") if isinstance(meta, dict) else ""

            # Format status badge
            if status == "COMPLETED":
                self.project_lbl.configure(text=f"PROJECT: {p_name[:16]}", text_color=GREEN_ACCENT)
                self.sprint_badge.configure(text="5/5 COMPLETED ✔", text_color=GREEN_ACCENT)
                self.agent_lbl.configure(text="QA & DevOps: All automated tests verified (100%).")
                if archetype == "web_application":
                    self.milestone_lbl.configure(text=f"Live Web App: Launch run.bat (http://localhost:5000)")
                else:
                    self.milestone_lbl.configure(text=f"Deliverables ready in projects/{top['name']}/")
            else:
                self.project_lbl.configure(text=f"PROJECT: {p_name[:16]}", text_color=CYAN_BRIGHT)
                self.sprint_badge.configure(text=f"SPRINT {curr_sprint}/{total_sprints} ({status})", text_color=CYAN_BRIGHT)
                
                # Archetype-aware role mapping
                if archetype == "web_application":
                    role_map = {
                        1: "System Architect: Designing ARCHITECTURE.md & web topology",
                        2: "Frontend Engineer: Building semantic HTML5 & responsive CSS3",
                        3: "Full-Stack Developer: Client JavaScript & Python HTTP server",
                        4: "DevOps Engineer: Packaging 1-click browser launcher (run.bat)",
                        5: "QA Automation Lead: Live socket tests, DOM audits & delivery"
                    }
                else:
                    role_map = {
                        1: "System Architect: Designing ARCHITECTURE.md & data contracts",
                        2: "Database Engineer: Building SQLite models & persistence",
                        3: "Backend Developer: Constructing domain service & export logic",
                        4: "Full-Stack Developer: Packaging CLI/GUI interface & launchers",
                        5: "Lead QA Engineer: Executing automated test suite with self-healing"
                    }
                active_role = role_map.get(curr_sprint, "Agile Engineering Team")
                self.agent_lbl.configure(text=f"Active: {active_role}")
                self.milestone_lbl.configure(text=f"Status: Sprint {curr_sprint} execution active.")

        except Exception as e:
            print(f"[AGENCY PANEL ERROR]: {e}")

