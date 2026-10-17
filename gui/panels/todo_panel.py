"""
Stark Taskmaster & To-Do Directives Panel for J.A.R.V.I.S. Sci-Fi HUD
Displays real-time pending directives from SQLite with interactive completion buttons.
"""

import customtkinter as ctk

CYAN_BRIGHT = "#00f0ff"
GREEN_ACCENT = "#00ff88"
TEXT_CYAN = "#80d8ff"
TEXT_MUTED = "#607d8b"
FONT_SMALL = ("Consolas", 10)


class TodoPanel:
    def __init__(self, parent, panel_factory, notif_callback=None):
        self.notif_cb = notif_callback
        self.panel = panel_factory(parent, "TASK DIRECTIVES", icon="📋")
        self.panel.pack(fill="x", pady=(0, 8))

        self.header_row = ctk.CTkFrame(self.panel, fg_color="transparent")
        self.header_row.pack(fill="x", padx=10, pady=(2, 2))

        self.count_lbl = ctk.CTkLabel(
            self.header_row,
            text="ACTIVE DIRECTIVES: 0",
            font=FONT_SMALL,
            text_color=CYAN_BRIGHT
        )
        self.count_lbl.pack(side="left")

        self.items_frame = ctk.CTkFrame(self.panel, fg_color="transparent")
        self.items_frame.pack(fill="x", padx=8, pady=(0, 6))

    def _notify(self, text):
        if self.notif_cb:
            try:
                self.notif_cb(text)
            except Exception:
                pass

    def refresh(self):
        """Query SQLite todos table and render interactive directive checklist."""
        try:
            from system_layer.todo_controller import get_active_tasks
            tasks = get_active_tasks(limit=3)

            for w in self.items_frame.winfo_children():
                w.destroy()

            if not tasks:
                self.count_lbl.configure(text="ALL DIRECTIVES COMPLETE ●", text_color=GREEN_ACCENT)
                empty_lbl = ctk.CTkLabel(
                    self.items_frame,
                    text="No pending directives. Voice: 'add task ...'",
                    font=FONT_SMALL,
                    text_color=TEXT_MUTED
                )
                empty_lbl.pack(anchor="w", padx=4, pady=2)
            else:
                self.count_lbl.configure(text=f"PENDING DIRECTIVES ({len(tasks)})", text_color=CYAN_BRIGHT)
                for t in tasks:
                    t_id = t["id"]
                    t_text = t["task"]
                    row = ctk.CTkFrame(self.items_frame, fg_color="#041426", corner_radius=4, height=22)
                    row.pack(fill="x", pady=1)

                    def make_done_cmd(tid=t_id):
                        def _done():
                            try:
                                from system_layer.todo_controller import complete_task
                                res = complete_task(str(tid))
                                self._notify(res)
                                self.refresh()
                            except Exception as e:
                                print(f"[TODO CLICK ERROR]: {e}")
                        return _done

                    check_btn = ctk.CTkButton(
                        row,
                        text="✔",
                        width=22,
                        height=20,
                        font=("Consolas", 10, "bold"),
                        fg_color="#062238",
                        hover_color="#00aa88",
                        border_color=CYAN_BRIGHT,
                        border_width=1,
                        text_color=GREEN_ACCENT,
                        command=make_done_cmd(t_id)
                    )
                    check_btn.pack(side="left", padx=2, pady=1)

                    display_t = (t_text[:24] + "...") if len(t_text) > 26 else t_text
                    lbl = ctk.CTkLabel(
                        row,
                        text=f"#{t_id} {display_t}",
                        font=FONT_SMALL,
                        text_color=TEXT_CYAN
                    )
                    lbl.pack(side="left", padx=4)
        except Exception:
            pass
