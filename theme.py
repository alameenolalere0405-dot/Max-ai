"""
MAX AI — Theme System
LEREON Technologies
Futuristic HUD dark theme inspired by advanced AI interfaces.
"""

COLORS = {
    "bg_deep":      "#020812",
    "bg_panel":     "#030D1A",
    "bg_card":      "#041020",
    "bg_input":     "#030C18",
    "accent_cyan":  "#00E5FF",
    "accent_blue":  "#0080FF",
    "accent_teal":  "#00BFFF",
    "accent_dim":   "#0A4060",
    "text_primary": "#D0ECF8",
    "text_secondary":"#4A90B0",
    "text_dim":     "#1A4060",
    "border":       "#0A2A45",
    "border_bright":"#00BFFF",
    "success":      "#00FF88",
    "warning":      "#FFB800",
    "error":        "#FF3355",
    "purple":       "#AA44FF",
    "orange":       "#FF8800",
}

STYLESHEET = f"""
/* ── Global ──────────────────────────────────────────── */
* {{
    font-family: 'Segoe UI', 'Inter', 'SF Pro Display', Arial, sans-serif;
    color: {COLORS['text_primary']};
    outline: none;
}}
QMainWindow, QDialog, QWidget {{
    background-color: {COLORS['bg_deep']};
}}
QToolTip {{
    background: {COLORS['bg_card']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['accent_teal']};
    border-radius: 4px;
    padding: 5px 9px;
    font-size: 11px;
}}

/* ── Scrollbars ──────────────────────────────────────── */
QScrollBar:vertical {{
    background: transparent;
    width: 5px;
    border-radius: 2px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {COLORS['accent_dim']};
    border-radius: 2px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{ background: {COLORS['accent_teal']}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{
    background: transparent;
    height: 5px;
    border-radius: 2px;
}}
QScrollBar::handle:horizontal {{
    background: {COLORS['accent_dim']};
    border-radius: 2px;
    min-width: 24px;
}}

/* ── Buttons ─────────────────────────────────────────── */
QPushButton {{
    background: {COLORS['bg_card']};
    color: {COLORS['accent_teal']};
    border: 1px solid {COLORS['border']};
    border-radius: 7px;
    padding: 8px 16px;
    font-size: 12px;
    font-weight: 500;
}}
QPushButton:hover {{
    background: #071828;
    border-color: {COLORS['accent_teal']};
    color: {COLORS['text_primary']};
}}
QPushButton:pressed {{
    background: {COLORS['accent_teal']};
    color: {COLORS['bg_deep']};
    border-color: {COLORS['accent_teal']};
}}
QPushButton:disabled {{
    color: {COLORS['accent_dim']};
    border-color: #071828;
    background: {COLORS['bg_deep']};
}}
QPushButton#primary {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #004080, stop:1 #0070B0);
    color: #D9F8FF;
    border: 1px solid {COLORS['accent_teal']};
    font-size: 13px;
    padding: 10px 24px;
    font-weight: 600;
}}
QPushButton#primary:hover {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #005090, stop:1 #0090D0);
}}
QPushButton#danger {{
    color: {COLORS['error']};
    border-color: {COLORS['error']};
}}
QPushButton#danger:hover {{
    background: #200008;
    border-color: {COLORS['error']};
}}
QPushButton#ghost {{
    background: transparent;
    border: none;
    color: {COLORS['text_secondary']};
    padding: 6px 10px;
}}
QPushButton#ghost:hover {{ color: {COLORS['accent_teal']}; background: #071828; border-radius: 6px; }}
QPushButton#icon_btn {{
    background: transparent;
    border: none;
    color: {COLORS['text_secondary']};
    padding: 4px;
    font-size: 17px;
    min-width: 32px;
    min-height: 32px;
}}
QPushButton#icon_btn:hover {{ color: {COLORS['accent_teal']}; background: #071828; border-radius: 6px; }}

/* ── Inputs ──────────────────────────────────────────── */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background: {COLORS['bg_input']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 9px 12px;
    font-size: 13px;
    selection-background-color: #004A80;
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {COLORS['accent_teal']};
    background: #040F1E;
}}
QTextBrowser {{
    background: {COLORS['bg_deep']};
    border: none;
    color: {COLORS['text_primary']};
}}

/* ── Combo ───────────────────────────────────────────── */
QComboBox {{
    background: {COLORS['bg_card']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 7px;
    padding: 7px 12px;
    font-size: 12px;
    min-height: 32px;
}}
QComboBox:hover {{ border-color: {COLORS['accent_teal']}; }}
QComboBox::drop-down {{
    border: none;
    width: 28px;
    padding-right: 6px;
}}
QComboBox QAbstractItemView {{
    background: {COLORS['bg_card']};
    border: 1px solid {COLORS['border']};
    color: {COLORS['text_primary']};
    selection-background-color: #004A80;
    padding: 4px;
    border-radius: 6px;
}}

/* ── Progress ────────────────────────────────────────── */
QProgressBar {{
    background: {COLORS['bg_card']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    height: 6px;
    text-align: center;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #004080, stop:1 {COLORS['accent_teal']});
    border-radius: 4px;
}}

/* ── Tab Widget ──────────────────────────────────────── */
QTabWidget::pane {{
    background: {COLORS['bg_deep']};
    border: none;
}}
QTabBar {{
    background: transparent;
}}
QTabBar::tab {{
    background: transparent;
    color: {COLORS['text_dim']};
    border: none;
    border-bottom: 2px solid transparent;
    padding: 9px 20px;
    font-size: 12px;
    font-weight: 500;
    margin-right: 2px;
}}
QTabBar::tab:selected {{
    color: {COLORS['accent_teal']};
    border-bottom: 2px solid {COLORS['accent_teal']};
}}
QTabBar::tab:hover {{
    color: {COLORS['text_primary']};
    border-bottom: 2px solid {COLORS['accent_dim']};
}}

/* ── List / Tree ─────────────────────────────────────── */
QListWidget, QTreeWidget {{
    background: transparent;
    border: none;
    outline: none;
    color: {COLORS['text_primary']};
}}
QListWidget::item {{
    padding: 8px 10px;
    border-radius: 6px;
    margin: 1px 0;
    border: none;
}}
QListWidget::item:selected {{
    background: #0A2A45;
    color: #D9F8FF;
}}
QListWidget::item:hover {{
    background: #071828;
}}

/* ── CheckBox ────────────────────────────────────────── */
QCheckBox {{
    color: {COLORS['text_secondary']};
    spacing: 8px;
    font-size: 12px;
}}
QCheckBox::indicator {{
    width: 18px; height: 18px;
    border: 1px solid {COLORS['accent_dim']};
    border-radius: 4px;
    background: {COLORS['bg_card']};
}}
QCheckBox::indicator:checked {{
    background: {COLORS['accent_teal']};
    border-color: {COLORS['accent_teal']};
}}

/* ── Slider ──────────────────────────────────────────── */
QSlider::groove:horizontal {{
    background: {COLORS['bg_card']};
    border: 1px solid {COLORS['border']};
    height: 6px;
    border-radius: 3px;
}}
QSlider::handle:horizontal {{
    background: {COLORS['accent_teal']};
    border: none;
    width: 16px; height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}}
QSlider::sub-page:horizontal {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #004080, stop:1 {COLORS['accent_teal']});
    border-radius: 3px;
}}

/* ── Menu ────────────────────────────────────────────── */
QMenuBar {{
    background: {COLORS['bg_panel']};
    color: {COLORS['text_secondary']};
    border-bottom: 1px solid {COLORS['border']};
    padding: 2px;
}}
QMenuBar::item:selected {{
    background: {COLORS['bg_card']};
    color: {COLORS['accent_teal']};
    border-radius: 4px;
}}
QMenu {{
    background: {COLORS['bg_card']};
    border: 1px solid {COLORS['border']};
    color: {COLORS['text_primary']};
    border-radius: 8px;
    padding: 4px;
}}
QMenu::item {{
    padding: 8px 20px;
    border-radius: 4px;
}}
QMenu::item:selected {{ background: #0A2A45; }}
QMenu::separator {{
    height: 1px;
    background: {COLORS['border']};
    margin: 4px 8px;
}}

/* ── Status Bar ──────────────────────────────────────── */
QStatusBar {{
    background: {COLORS['bg_panel']};
    color: {COLORS['text_dim']};
    border-top: 1px solid {COLORS['border']};
    font-size: 11px;
    padding: 2px 8px;
}}

/* ── Splitter ────────────────────────────────────────── */
QSplitter::handle {{ background: {COLORS['border']}; width: 1px; height: 1px; }}

/* ── Group Box ───────────────────────────────────────── */
QGroupBox {{
    color: {COLORS['accent_teal']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    margin-top: 10px;
    padding: 10px 8px 8px 8px;
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 0.5px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 6px;
    color: {COLORS['accent_teal']};
}}

/* ── Spin Box ────────────────────────────────────────── */
QSpinBox, QDoubleSpinBox {{
    background: {COLORS['bg_card']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 6px 8px;
}}
QSpinBox:focus, QDoubleSpinBox:focus {{ border-color: {COLORS['accent_teal']}; }}

/* ── Frame ───────────────────────────────────────────── */
QFrame[frameShape="4"] {{ color: {COLORS['border']}; }}
QFrame[frameShape="5"] {{ color: {COLORS['border']}; }}
"""


def apply_global_theme(app):
    app.setStyleSheet(STYLESHEET)
