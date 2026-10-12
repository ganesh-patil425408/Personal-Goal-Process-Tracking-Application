import tkinter as tk
from tkinter import ttk, messagebox
import time
from random import choice
from database import init_db, register_user, login_user, get_goals, add_goal, get_tasks, add_task, complete_task, add_focus_session, get_stats, complete_goal
MESSAGES = [
    "Great job. One step closer to your goal.",
    "Excellent. Keep the momentum going.",
    "Your consistency is your superpower.",
    "Every completed task is progress toward your dream.",
    "Small progress every day creates big results.",
]
BG, CARD, ACCENT, TEXT, MUTED = "#f3f5f9", "#ffffff", "#4f46e5", "#1f2937", "#8b93a5"
FONT = "Segoe UI"
class GoalFlow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("GoalFlow")
        self.geometry("960x620")
        self.configure(bg=BG)
        self.user = None
        self.running = False
        self.focus_minutes = 30  # Default focus duration
        self.seconds = self.focus_minutes * 60
        self.end = 0.0
        self.job = None
        self.is_break = False
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("TNotebook", background=BG, borderwidth=0)
        s.configure("TNotebook.Tab", padding=(20, 10), font=(FONT, 11))
        s.map("TNotebook.Tab", background=[("selected", ACCENT)], foreground=[("selected", "#fff")])
        s.configure("Treeview", rowheight=32, font=(FONT, 10))
        s.configure("Treeview.Heading", font=(FONT, 10, "bold"), padding=6)
        s.configure("TEntry", padding=8)
        init_db()
        self.show_login()
    def btn(self, parent, text, cmd, color=ACCENT):
        return tk.Button(parent, text=text, command=cmd, bg=color, fg="#fff", relief="flat",
                         font=(FONT, 10, "bold"), padx=16, pady=8, cursor="hand2",
                         activebackground=TEXT, activeforeground="#fff")
    def clear(self):
        for w in self.winfo_children():
            w.destroy()
    def card(self, title, sub):
        self.clear()
        c = tk.Frame(self, bg=CARD, padx=40, pady=34, highlightbackground="#e3e7ee", highlightthickness=1)
        c.place(relx=.5, rely=.5, anchor="center")
        tk.Label(c, text=title, bg=CARD, fg=TEXT, font=(FONT, 24, "bold")).pack(anchor="w")
        tk.Label(c, text=sub, bg=CARD, fg=MUTED, font=(FONT, 10)).pack(anchor="w", pady=(0, 16))
        return c
    def field(self, parent, label, secret=False):
        tk.Label(parent, text=label, bg=CARD, fg=MUTED, font=(FONT, 9, "bold")).pack(anchor="w", pady=(8, 2))
        e = ttk.Entry(parent, width=36, show="*" if secret else "")
        e.pack(fill="x")
        return e
    def show_login(self):
        c = self.card("GoalFlow", "Sign in to your account")
        self.email = self.field(c, "Email")
        self.password = self.field(c, "Password", True)
        self.btn(c, "Login", self.do_login).pack(fill="x", pady=(18, 6))
        self.btn(c, "Create Account", self.show_register, "#6b7280").pack(fill="x")
    def show_register(self):
        c = self.card("Create Account", "It only takes a minute")
        self.rname = self.field(c, "Name")
        self.remail = self.field(c, "Email")
        self.rpass = self.field(c, "Password", True)
        self.btn(c, "Register", self.do_register).pack(fill="x", pady=(18, 6))
        self.btn(c, "Back to Login", self.show_login, "#6b7280").pack(fill="x")
    def do_register(self):
        try:
            register_user(self.rname.get(), self.remail.get(), self.rpass.get())
            messagebox.showinfo("Success", "Account created. Please login.")
            self.show_login()
        except Exception as e:
            messagebox.showerror("Registration Error", str(e))
    def do_login(self):
        try:
            user = login_user(self.email.get(), self.password.get())
            if not user:
                messagebox.showerror("Login Failed", "Invalid email or password.")
                return
            self.user = user
            self.show_dashboard()
        except Exception as e:
            messagebox.showerror("Database Error", str(e))
    def logout(self):
        self.running = False
        self.show_login()
    def show_dashboard(self):
        self.clear()
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=24, pady=(20, 8))
        tk.Label(top, text=f"Welcome, {self.user['name']}", bg=BG, fg=TEXT, font=(FONT, 20, "bold")).pack(side="left")
        self.btn(top, "Logout", self.logout, "#6b7280").pack(side="right")
        st = get_stats(self.user["user_id"])
        row = tk.Frame(self, bg=BG)
        row.pack(fill="x", padx=24, pady=8)
        for i, (name, key) in enumerate([("Goals", "goals"), ("Tasks Done", "completed_tasks"), ("Focus Minutes", "focus_minutes"), ("XP", "xp")]):
            row.columnconfigure(i, weight=1, uniform="a")
            c = tk.Frame(row, bg=CARD, padx=18, pady=14, highlightbackground="#e3e7ee", highlightthickness=1)
            c.grid(row=0, column=i, sticky="nsew", padx=5)
            tk.Label(c, text=name, bg=CARD, fg=MUTED, font=(FONT, 10)).pack(anchor="w")
            tk.Label(c, text=str(st[key]), bg=CARD, fg=ACCENT, font=(FONT, 24, "bold")).pack(anchor="w")
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=24, pady=(8, 20))
        gt = tk.Frame(nb, bg=CARD, padx=12, pady=12)
        nb.add(gt, text="Goals")
        gbar = tk.Frame(gt, bg=CARD)
        gbar.pack(side="bottom", pady=(10, 0), anchor="e")
        self.btn(gbar, "Add Goal", self.add_goal_dialog).pack(side="left", padx=4)
        self.btn(gbar, "Complete Selected", self.finish_goal, "#16a34a").pack(side="left")
        self.goal_tree = self.tree(gt, ("id", "title", "category", "priority", "date", "progress", "status"))
        self.refresh_goals()
        tt = tk.Frame(nb, bg=CARD, padx=12, pady=12)
        nb.add(tt, text="Tasks")
        bar = tk.Frame(tt, bg=CARD)
        bar.pack(side="bottom", pady=(10, 0), anchor="e")
        self.btn(bar, "Add Task", self.add_task_dialog).pack(side="left", padx=4)
        self.btn(bar, "Complete Selected", self.finish_task, "#16a34a").pack(side="left")
        self.task_tree = self.tree(tt, ("id", "goal", "task", "status"))
        self.refresh_tasks()
        ft = tk.Frame(nb, bg=CARD, pady=22)
        nb.add(ft, text="Focus")

        tk.Label(
            ft, text="Set your focus duration", bg=CARD, fg=TEXT,
            font=(FONT, 12, "bold")
        ).pack(pady=(0, 8))

        duration_row = tk.Frame(ft, bg=CARD)
        duration_row.pack(pady=(0, 12))

        tk.Label(duration_row, text="Hours", bg=CARD, fg=MUTED,
                 font=(FONT, 10)).grid(row=0, column=0, padx=6)
        tk.Label(duration_row, text="Minutes", bg=CARD, fg=MUTED,
                 font=(FONT, 10)).grid(row=0, column=1, padx=6)

        self.hours_var = tk.StringVar(value="0")
        self.minutes_var = tk.StringVar(value="30")
        self.hours_input = ttk.Spinbox(
            duration_row, from_=0, to=23, width=8,
            textvariable=self.hours_var, state="normal"
        )
        self.hours_input.grid(row=1, column=0, padx=6, pady=4)
        self.minutes_input = ttk.Spinbox(
            duration_row, from_=0, to=59, width=8,
            textvariable=self.minutes_var, state="normal"
        )
        self.minutes_input.grid(row=1, column=1, padx=6, pady=4)

        self.btn(ft, "Apply Duration", self.apply_focus_duration).pack(pady=(0, 12))

        self.mode_label = tk.Label(
            ft, text="30-minute Focus", bg=CARD, fg=ACCENT,
            font=(FONT, 13, "bold")
        )
        self.mode_label.pack()
        self.timer_label = tk.Label(
            ft, text="30:00", bg=CARD, fg=TEXT,
            font=("Consolas", 52, "bold")
        )
        self.timer_label.pack(pady=12)

        bar = tk.Frame(ft, bg=CARD)
        bar.pack()
        self.btn(bar, "Start", self.start_timer).pack(side="left", padx=6)
        self.btn(bar, "Pause", self.pause_timer, "#6b7280").pack(side="left", padx=6)
        self.btn(bar, "Reset", self.reset_timer, "#6b7280").pack(side="left", padx=6)

        self.show_time(self.seconds)
        self.mode_label.config(
            text="5-minute Break" if self.is_break else self.focus_duration_text()
        )
    def tree(self, parent, cols):
        t = ttk.Treeview(parent, columns=cols, show="headings", displaycolumns=cols[1:], height=5)
        for c in cols:
            t.heading(c, text=c.title())
        t.pack(fill="both", expand=True)
        return t
    def refresh_goals(self):
        self.goal_tree.delete(*self.goal_tree.get_children())
        for g in get_goals(self.user["user_id"]):
            self.goal_tree.insert("", "end", values=(g["goal_id"], g["title"], g["category"], g["priority"], g["target_date"], f"{g['progress']}%", g["status"]))
    def refresh_tasks(self):
        self.task_tree.delete(*self.task_tree.get_children())
        for t in get_tasks(self.user["user_id"]):
            self.task_tree.insert("", "end", values=(t["task_id"], t["goal_title"], t["task_name"], t["status"]))
    def dialog(self, title):
        w = tk.Toplevel(self)
        w.title(title)
        w.configure(bg=CARD, padx=28, pady=22)
        w.grab_set()
        tk.Label(w, text=title, bg=CARD, fg=TEXT, font=(FONT, 16, "bold")).pack(anchor="w")
        return w
    def add_goal_dialog(self):
        w = self.dialog("Add Goal")
        f = {n: self.field(w, n) for n in ["Title", "Description", "Category", "Priority", "Target Date (YYYY-MM-DD)"]}
        def save():
            if not f["Title"].get().strip():
                messagebox.showwarning("Missing Title", "Please enter a goal title.", parent=w)
                return
            try:
                add_goal(self.user["user_id"], f["Title"].get().strip(), f["Description"].get(), f["Category"].get(),
                         f["Priority"].get() or "Medium", f["Target Date (YYYY-MM-DD)"].get())
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=w)
                return
            w.destroy()
            self.show_dashboard()
        row = tk.Frame(w, bg=CARD)
        row.pack(pady=(18, 0), anchor="e")
        self.btn(row, "Back", w.destroy, "#6b7280").pack(side="left", padx=6)
        self.btn(row, "Save Goal", save).pack(side="left")
    def add_task_dialog(self):
        goals = get_goals(self.user["user_id"])
        if not goals:
            messagebox.showwarning("No Goal", "Create a goal first.")
            return
        w = self.dialog("Add Task")
        task = self.field(w, "Task Name")
        tk.Label(w, text="Goal", bg=CARD, fg=MUTED, font=(FONT, 9, "bold")).pack(anchor="w", pady=(8, 2))
        combo = ttk.Combobox(w, values=[f"{g['goal_id']} - {g['title']}" for g in goals], state="readonly")
        combo.pack(fill="x")
        combo.current(0)
        def save():
            add_task(self.user["user_id"], int(combo.get().split(" - ")[0]), task.get())
            w.destroy()
            self.refresh_tasks()
        row = tk.Frame(w, bg=CARD)
        row.pack(pady=(18, 0), anchor="e")
        self.btn(row, "Back", w.destroy, "#6b7280").pack(side="left", padx=6)
        self.btn(row, "Save Task", save).pack(side="left")
    def finish_goal(self):
        sel = self.goal_tree.selection()
        if not sel:
            messagebox.showinfo("Select a Goal", "Please select a goal first.")
            return
        goal_id = int(self.goal_tree.item(sel[0])["values"][0])
        if complete_goal(self.user["user_id"], goal_id):
            messagebox.showinfo("Goal Completed", "Congratulations. You completed your goal.\n\n+50 XP")
            self.show_dashboard()
        else:
            messagebox.showinfo("Already Completed", "This goal is already completed.")
    def finish_task(self):
        sel = self.task_tree.selection()
        if not sel:
            return
        if complete_task(self.user["user_id"], int(self.task_tree.item(sel[0])["values"][0])):
            messagebox.showinfo("Task Completed", f"{choice(MESSAGES)}\n\n+10 XP")
            self.show_dashboard()
    def show_time(self, t):
        total_seconds = max(0, int(t))
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours:
            display = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            display = f"{minutes:02d}:{seconds:02d}"
        self.timer_label.config(text=display)

    def focus_duration_text(self):
        hours, minutes = divmod(self.focus_minutes, 60)
        if hours and minutes:
            return f"{hours} hour{'s' if hours != 1 else ''} {minutes} minute{'s' if minutes != 1 else ''} Focus"
        if hours:
            return f"{hours} hour{'s' if hours != 1 else ''} Focus"
        return f"{minutes}-minute Focus"

    def apply_focus_duration(self):
        if self.running or self.is_break:
            messagebox.showwarning(
                "Timer Active",
                "Please reset the current session before changing its duration."
            )
            return

        try:
            hours = int(self.hours_var.get())
            minutes = int(self.minutes_var.get())
        except (ValueError, TypeError):
            messagebox.showerror("Invalid Duration", "Enter valid hours and minutes.")
            return

        if not (0 <= hours <= 23 and 0 <= minutes <= 59):
            messagebox.showerror(
                "Invalid Duration", "Hours must be 0–23 and minutes must be 0–59."
            )
            return

        total_minutes = hours * 60 + minutes
        if total_minutes <= 0:
            messagebox.showerror(
                "Invalid Duration", "Focus duration must be at least 1 minute."
            )
            return

        self.focus_minutes = total_minutes
        self.seconds = total_minutes * 60
        self.show_time(self.seconds)
        self.mode_label.config(text=self.focus_duration_text())
    def stop_loop(self):
        if self.job:
            self.after_cancel(self.job)
            self.job = None
    def start_timer(self):
        if not self.running:
            self.running = True
            self.end = time.perf_counter() + self.seconds
            self.tick()
    def pause_timer(self):
        if self.running:
            self.seconds = max(self.end - time.perf_counter(), 0)
        self.running = False
        self.stop_loop()
    def reset_timer(self):
        self.running = False
        self.stop_loop()
        self.is_break = False
        self.seconds = self.focus_minutes * 60
        self.show_time(self.seconds)
        self.mode_label.config(text=self.focus_duration_text())
        if hasattr(self, "hours_var"):
            hours, minutes = divmod(self.focus_minutes, 60)
            self.hours_var.set(str(hours))
            self.minutes_var.set(str(minutes))
    def tick(self):
        if not self.running:
            return
        left = self.end - time.perf_counter()
        if left <= 0:
            self.show_time(0)
            if not self.is_break:
                add_focus_session(self.user["user_id"], self.focus_minutes)
                messagebox.showinfo("Focus Complete", "Take a 5-minute break.")
                self.is_break, self.seconds = True, 300.0
                self.mode_label.config(text="5-minute Break")
            else:
                messagebox.showinfo("Break Complete", "Ready for another focus session.")
                self.is_break = False
                self.seconds = self.focus_minutes * 60
                self.mode_label.config(text=self.focus_duration_text())
            self.end = time.perf_counter() + self.seconds
            self.tick()
        else:
            self.show_time(left)
            self.job = self.after(10, self.tick)
if __name__ == "__main__":
    GoalFlow().mainloop()
