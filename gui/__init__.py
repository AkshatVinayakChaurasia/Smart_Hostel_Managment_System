"""
gui/__init__.py - HostelHub GUI Package

Shared constants, color scheme, fonts, and widget helpers
used by all GUI modules.
"""

import tkinter as tk
from tkinter import ttk

# =====================================================================
#  COLOR SCHEME
# =====================================================================

COLORS = {
    "bg":         "#f8fafc",     # Modern soft white/light gray background (slate-50 feel)
    "primary":    "#0f172a",     # Sleek slate-900 for headers/sidebars
    "accent":     "#2563eb",     # Premium royal blue accent (blue-600)
    "success":    "#10b981",     # Soft emerald green (emerald-500)
    "danger":     "#ef4444",     # Soft rose red (rose-500)
    "warning":    "#f59e0b",     # Soft amber orange (amber-500)
    "card":       "#ffffff",     # Pure white cards
    "text":       "#1e293b",     # Dark slate text (slate-800)
    "text_light": "#ffffff",     # White text
    "text_muted": "#64748b",     # Muted slate/gray text (slate-500)
    "border":     "#e2e8f0",     # Subtle light border (slate-200)
    "row_even":   "#ffffff",
    "row_odd":    "#f8fafc",
    "selected":   "#e0f2fe",     # Soft sky blue for selected row highlight
}

# =====================================================================
#  FONTS  (Segoe UI is available on all modern Windows)
# =====================================================================

FONT_FAMILY = "Segoe UI"

FONTS = {
    "banner":    (FONT_FAMILY, 20, "bold"),
    "heading":   (FONT_FAMILY, 14, "bold"),
    "subhead":   (FONT_FAMILY, 12, "bold"),
    "body":      (FONT_FAMILY, 11),
    "small":     (FONT_FAMILY, 9),
    "button":    (FONT_FAMILY, 10, "bold"),
    "entry":     (FONT_FAMILY, 11),
    "tree":      (FONT_FAMILY, 10),
    "tree_head": (FONT_FAMILY, 10, "bold"),
}


# =====================================================================
#  THEME SETUP
# =====================================================================

def apply_theme(root):
    """Configure ttk styles for a clean, modern look."""
    style = ttk.Style(root)
    style.theme_use("clam")

    # General
    style.configure("TFrame", background=COLORS["bg"])
    style.configure("TLabel", background=COLORS["bg"], foreground=COLORS["text"], font=FONTS["body"])
    style.configure("TEntry", font=FONTS["entry"], padding=6)

    # Buttons
    style.configure("TButton", font=FONTS["button"], padding=8, background="#f1f5f9", foreground=COLORS["text"])
    style.map("TButton",
              background=[("active", "#e2e8f0"), ("disabled", "#f8fafc")],
              foreground=[("active", COLORS["text"]), ("disabled", "#94a3b8")])

    style.configure("Accent.TButton",
                    background=COLORS["accent"], foreground="white",
                    font=FONTS["button"], padding=8)
    style.map("Accent.TButton",
              background=[("active", "#1d4ed8"), ("disabled", "#cbd5e1")],
              foreground=[("active", "white"), ("disabled", "#94a3b8")])

    style.configure("Success.TButton",
                    background=COLORS["success"], foreground="white",
                    font=FONTS["button"], padding=8)
    style.map("Success.TButton",
              background=[("active", "#059669")])

    style.configure("Danger.TButton",
                    background=COLORS["danger"], foreground="white",
                    font=FONTS["button"], padding=8)
    style.map("Danger.TButton",
              background=[("active", "#dc2626")])

    style.configure("Warning.TButton",
                    background=COLORS["warning"], foreground="white",
                    font=FONTS["button"], padding=8)
    style.map("Warning.TButton",
              background=[("active", "#d97706")])

    # Treeview
    style.configure("Treeview",
                    font=FONTS["tree"], rowheight=32,
                    background=COLORS["card"], fieldbackground=COLORS["card"],
                    borderwidth=1, bordercolor=COLORS["border"])
    style.configure("Treeview.Heading",
                    font=FONTS["tree_head"],
                    background=COLORS["primary"], foreground="white",
                    relief="flat", padding=6)
    style.map("Treeview.Heading",
              background=[("active", COLORS["primary"])])
    style.map("Treeview",
              background=[("selected", COLORS["selected"])],
              foreground=[("selected", COLORS["text"])])

    # Notebook (tabs)
    style.configure("TNotebook", background=COLORS["bg"])
    style.configure("TNotebook.Tab", font=FONTS["body"], padding=[14, 6], background="#f1f5f9", foreground=COLORS["text_muted"])
    style.map("TNotebook.Tab",
              background=[("selected", COLORS["card"]), ("active", "#e2e8f0")],
              foreground=[("selected", COLORS["accent"]), ("active", COLORS["text"])])

    # LabelFrame
    style.configure("TLabelframe", background=COLORS["bg"])
    style.configure("TLabelframe.Label", font=FONTS["subhead"],
                    background=COLORS["bg"], foreground=COLORS["text"])


# =====================================================================
#  REUSABLE WIDGET HELPERS
# =====================================================================

def center_window(window, width, height):
    """Center a Tk or Toplevel window on screen."""
    window.update_idletasks()
    x = (window.winfo_screenwidth() - width) // 2
    y = (window.winfo_screenheight() - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")


def create_header(parent, title):
    """Create a colored header bar at the top of a window/frame."""
    header = tk.Frame(parent, bg=COLORS["primary"], height=60)
    header.pack(fill="x")
    header.pack_propagate(False)
    
    # Left accent indicator bar (royal blue)
    accent_bar = tk.Frame(header, bg=COLORS["accent"], width=5)
    accent_bar.pack(side="left", fill="y")
    
    tk.Label(header, text=title,
             font=FONTS["heading"], bg=COLORS["primary"],
             fg=COLORS["text_light"]).pack(side="left", padx=15, pady=15)
             
    # Bottom separator line
    sep = tk.Frame(parent, bg=COLORS["border"], height=1)
    sep.pack(fill="x")
    
    return header


def create_treeview(parent, columns, headings, col_widths=None):
    """
    Create a Treeview with vertical scrollbar inside a frame.

    Args:
        parent:     Parent widget
        columns:    Tuple of column identifiers  e.g. ('id', 'name')
        headings:   Tuple of display headings     e.g. ('ID', 'Name')
        col_widths: Optional tuple of pixel widths

    Returns:
        (tree, container_frame) - pack the container into your layout.
    """
    container = ttk.Frame(parent)

    tree = ttk.Treeview(container, columns=columns, show="headings",
                        selectmode="browse")
    vsb = ttk.Scrollbar(container, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)

    for i, col in enumerate(columns):
        w = col_widths[i] if col_widths and i < len(col_widths) else 120
        tree.heading(col, text=headings[i], anchor="w")
        tree.column(col, width=w, minwidth=60, anchor="w")

    tree.pack(side="left", fill="both", expand=True)
    vsb.pack(side="right", fill="y")

    # Alternating row tags
    tree.tag_configure("even", background=COLORS["row_even"])
    tree.tag_configure("odd",  background=COLORS["row_odd"])

    return tree, container


def populate_treeview(tree, rows):
    """Clear and repopulate a Treeview with rows (list of tuples/lists)."""
    for item in tree.get_children():
        tree.delete(item)
    for i, row in enumerate(rows):
        tag = "even" if i % 2 == 0 else "odd"
        tree.insert("", "end", values=row, tags=(tag,))


def make_toolbar(parent):
    """Create a horizontal toolbar frame."""
    toolbar = ttk.Frame(parent)
    toolbar.pack(fill="x", padx=12, pady=(12, 6))
    return toolbar


def make_status_bar(parent, text="Ready"):
    """Create a status bar at the bottom of a window."""
    sep = tk.Frame(parent, bg=COLORS["border"], height=1)
    sep.pack(fill="x", side="bottom")

    bar = tk.Frame(parent, bg="#f8fafc", height=30)
    bar.pack(fill="x", side="bottom")
    bar.pack_propagate(False)

    lbl = tk.Label(bar, text=f"  {text}", font=FONTS["small"],
                   bg="#f8fafc", fg=COLORS["text_muted"], anchor="w")
    lbl.pack(fill="both", expand=True, padx=10)
    return lbl


class DashboardCard(tk.Frame):
    """
    A premium modern dashboard card widget.
    It contains a colored icon badge, a main title, a detail description, and hover highlights.
    """
    def __init__(self, parent, title, icon_text, accent_color, command):
        # Outer frame acts as the shadow layer
        super().__init__(parent, bg=COLORS["border"], bd=0)
        self.command = command
        
        # Inner content frame (the actual card)
        # Using pady=(1, 4) creates a subtle bottom drop shadow illusion
        self.inner = tk.Frame(self, bg=COLORS["card"], padx=24, pady=24)
        self.inner.pack(fill="both", expand=True, padx=1, pady=(1, 4))
        
        # Icon badge
        self.badge_frame = tk.Frame(self.inner, bg=accent_color, padx=12, pady=6)
        self.badge_frame.pack(anchor="w", pady=(0, 16))
        
        self.badge_lbl = tk.Label(
            self.badge_frame, text=icon_text, font=(FONT_FAMILY, 9, "bold"),
            bg=accent_color, fg="white"
        )
        self.badge_lbl.pack()
        
        # Title Label
        self.title_lbl = tk.Label(
            self.inner, text=title.replace("\n", " "), font=(FONT_FAMILY, 14, "bold"),
            bg=COLORS["card"], fg=COLORS["primary"], anchor="w", justify="left"
        )
        self.title_lbl.pack(fill="x", anchor="w")
        
        # Detail subtext
        detail_text = f"Configure & view {title.lower().replace('\n', ' ')}"
        self.detail_lbl = tk.Label(
            self.inner, text=detail_text, font=(FONT_FAMILY, 10),
            bg=COLORS["card"], fg=COLORS["text_muted"], anchor="w", justify="left"
        )
        self.detail_lbl.pack(fill="x", anchor="w", pady=(6, 0))

        # Bind hover and click events recursively
        for widget in (self, self.inner, self.badge_frame, self.badge_lbl, self.title_lbl, self.detail_lbl):
            widget.bind("<Enter>", self._on_enter)
            widget.bind("<Leave>", self._on_leave)
            widget.bind("<Button-1>", self._on_click)
            widget.config(cursor="hand2")
            
    def _on_enter(self, event):
        self.config(bg=COLORS["accent"])
        self.inner.config(bg="#f8fafc") # slightly darker light gray on hover
        self.title_lbl.config(bg="#f8fafc")
        self.detail_lbl.config(bg="#f8fafc")
        
    def _on_leave(self, event):
        self.config(bg=COLORS["border"])
        self.inner.config(bg=COLORS["card"])
        self.title_lbl.config(bg=COLORS["card"])
        self.detail_lbl.config(bg=COLORS["card"])
        
    def _on_click(self, event):
        self.command()

