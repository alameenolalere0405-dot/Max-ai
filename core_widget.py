"""
MAX AI — Core Sphere Widget (HUD Edition)
LEREON Technologies

Inspired by reference images: concentric rings, teal/cyan glow,
segmented outer ring, rotating inner layers, neural mesh center,
HUD data readouts, scanner sweep line.
"""

import math
import time
import random
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QTimer, QRectF, QPointF, Qt
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QRadialGradient,
    QConicalGradient, QLinearGradient, QFont, QPainterPath,
    QFontDatabase
)
from core.max_core import MAXState

STATE_CFG = {
    MAXState.IDLE:             ("#00E5FF", "#004466", 0.4,  "IDLE"),
    MAXState.LISTENING:        ("#00FF88", "#003322", 1.4,  "LISTENING"),
    MAXState.THINKING:         ("#AA44FF", "#220044", 2.0,  "PROCESSING"),
    MAXState.EXECUTING:        ("#FF8800", "#331a00", 1.8,  "EXECUTING"),
    MAXState.SPEAKING:         ("#00E5FF", "#003344", 1.2,  "SPEAKING"),
    MAXState.BROWSING:         ("#00CCAA", "#003322", 1.0,  "SEARCHING"),
    MAXState.ANALYZING:        ("#AA44FF", "#220044", 2.2,  "ANALYZING"),
    MAXState.ERROR:            ("#FF3355", "#330011", 0.8,  "ERROR"),
    MAXState.OFFLINE:          ("#334455", "#111822", 0.1,  "OFFLINE"),
    MAXState.WAITING_APPROVAL: ("#FFB800", "#332200", 0.6,  "WAITING"),
}


class CoreWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(240, 240)
        self._state = MAXState.IDLE

        # Animation state
        self._a1 = 0.0   # outer ring rotation
        self._a2 = 0.0   # middle ring (reverse)
        self._a3 = 0.0   # inner details
        self._a4 = 0.0   # scanner sweep
        self._pulse = 0.0
        self._t = 0.0

        # Neural mesh nodes
        rng = random.Random(99)
        self._nodes = [
            (rng.uniform(0.08, 0.28), rng.uniform(0, 2*math.pi),
             rng.uniform(-0.3, 0.3), rng.uniform(0.003, 0.009))
            for _ in range(28)
        ]

        # HUD readout values (animated counters)
        self._hud_vals = [42.7, 83.1, 61.4, 97.2]
        self._hud_dirs = [1, -1, 1, -1]

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)  # 60fps

    def set_state(self, state: MAXState):
        self._state = state
        self.update()

    def _tick(self):
        self._t += 0.016
        cfg = STATE_CFG.get(self._state, STATE_CFG[MAXState.IDLE])
        spd = cfg[2]

        self._a1   = (self._a1  + 0.008 * spd) % (2 * math.pi)
        self._a2   = (self._a2  - 0.012 * spd) % (2 * math.pi)
        self._a3   = (self._a3  + 0.020 * spd) % (2 * math.pi)
        self._a4   = (self._a4  + 0.015 * spd) % (2 * math.pi)
        self._pulse = (self._pulse + 0.06 * spd) % (2 * math.pi)

        # Animate HUD values
        for i in range(4):
            self._hud_vals[i] += self._hud_dirs[i] * 0.15 * spd
            if self._hud_vals[i] > 99: self._hud_dirs[i] = -1
            if self._hud_vals[i] < 1:  self._hud_dirs[i] =  1

        self.update()

    def paintEvent(self, event):
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        R = min(w, h) / 2 - 8    # outer radius

        cfg = STATE_CFG.get(self._state, STATE_CFG[MAXState.IDLE])
        c1 = QColor(cfg[0])      # primary color
        c2 = QColor(cfg[1])      # dark variant
        label = cfg[3]
        glow_int = 0.5 + 0.5 * math.sin(self._pulse)

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # ── Background ────────────────────────────────────────────────────
        bg = QRadialGradient(cx, cy, R * 1.3)
        bg.setColorAt(0, QColor(4, 20, 40, 140))
        bg.setColorAt(1, QColor(2, 8, 18, 0))
        p.fillRect(0, 0, w, h, QBrush(bg))

        # ── Outer glow aura ───────────────────────────────────────────────
        aura_col = QColor(c1)
        aura_col.setAlpha(int(18 + 22 * glow_int))
        aura = QRadialGradient(cx, cy, R * 1.15)
        aura.setColorAt(0, aura_col)
        aura.setColorAt(1, QColor(0, 0, 0, 0))
        p.setBrush(QBrush(aura))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QRectF(cx - R*1.15, cy - R*1.15, R*2.3, R*2.3))

        # ── Outermost segmented ring (like HUD images) ────────────────────
        self._draw_segmented_ring(p, cx, cy, R * 0.98, self._a1, c1, 2.0, 32, 5)

        # ── Secondary segmented ring ──────────────────────────────────────
        self._draw_segmented_ring(p, cx, cy, R * 0.80, self._a2, c1, 1.3, 20, 8)

        # ── Thin orbital rings ────────────────────────────────────────────
        for radius_f, alpha in [(0.90, 60), (0.70, 40), (0.60, 30)]:
            col = QColor(c1); col.setAlpha(alpha)
            pen = QPen(col, 0.6)
            pen.setStyle(Qt.PenStyle.DotLine)
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            rr = R * radius_f
            p.drawEllipse(QRectF(cx - rr, cy - rr, rr*2, rr*2))

        # ── Scanner sweep ─────────────────────────────────────────────────
        self._draw_scanner(p, cx, cy, R * 0.80, c1, glow_int)

        # ── Inner data ring (tick marks) ──────────────────────────────────
        self._draw_tick_ring(p, cx, cy, R * 0.52, self._a3, c1)

        # ── Neural mesh sphere ────────────────────────────────────────────
        self._draw_neural_mesh(p, cx, cy, R * 0.36, c1, glow_int)

        # ── Core center glow ──────────────────────────────────────────────
        core_r = R * 0.18
        core_g = QRadialGradient(cx, cy, core_r)
        cc = QColor(c1); cc.setAlpha(int(90 + 80 * glow_int))
        core_g.setColorAt(0, cc)
        core_g.setColorAt(0.5, QColor(c2))
        core_g.setColorAt(1, QColor(0, 0, 0, 0))
        p.setBrush(QBrush(core_g))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QRectF(cx - core_r*1.4, cy - core_r*1.4, core_r*2.8, core_r*2.8))

        # ── HUD corner readouts ───────────────────────────────────────────
        self._draw_hud_data(p, cx, cy, R, c1)

        # ── MAX label ─────────────────────────────────────────────────────
        font = QFont("Segoe UI", int(R * 0.14), QFont.Weight.Bold)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 3)
        p.setFont(font)
        tc = QColor(c1); tc.setAlpha(230)
        p.setPen(tc)
        p.drawText(QRectF(0, 0, w, h), Qt.AlignmentFlag.AlignCenter, "MAX")

        # ── State label ───────────────────────────────────────────────────
        font2 = QFont("Segoe UI", 7)
        font2.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 2)
        p.setFont(font2)
        sc = QColor(c1); sc.setAlpha(140)
        p.setPen(sc)
        p.drawText(
            QRectF(0, cy + R * 0.70, w, 16),
            Qt.AlignmentFlag.AlignCenter, label
        )

        p.end()

    def _draw_segmented_ring(self, p, cx, cy, r, start, color, width, segs, gap_deg):
        step = 2 * math.pi / segs
        gap  = math.radians(gap_deg)
        for i in range(segs):
            a_start = start + i * step
            a_end   = a_start + step - gap
            alpha   = 180 + int(60 * ((i % 4) / 3.0))
            col = QColor(color); col.setAlpha(min(255, alpha))
            pen = QPen(col, width)
            pen.setCapStyle(Qt.PenCapStyle.FlatCap)
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            rect = QRectF(cx - r, cy - r, r*2, r*2)
            p.drawArc(rect,
                      int(math.degrees(-a_end) * 16),
                      int(math.degrees(a_end - a_start) * 16))

    def _draw_tick_ring(self, p, cx, cy, r, start, color):
        """Data tick-marks ring like HUD images."""
        n = 48
        for i in range(n):
            a = start + i * (2 * math.pi / n)
            outer = r
            inner = r * (0.80 if i % 4 == 0 else 0.90 if i % 2 == 0 else 0.94)
            ox = cx + math.cos(a) * outer
            oy = cy + math.sin(a) * outer
            ix = cx + math.cos(a) * inner
            iy = cy + math.sin(a) * inner
            alpha = 200 if i % 4 == 0 else 100 if i % 2 == 0 else 50
            col = QColor(color); col.setAlpha(alpha)
            pen = QPen(col, 1.0 if i % 4 == 0 else 0.5)
            p.setPen(pen)
            p.drawLine(QPointF(ox, oy), QPointF(ix, iy))

    def _draw_scanner(self, p, cx, cy, r, color, intensity):
        """Rotating scanner sweep line."""
        a = self._a4
        # Gradient sweep arc (45 degrees)
        sweep_path = QPainterPath()
        sweep_path.moveTo(cx, cy)
        for da in range(45):
            aa = a - math.radians(da)
            px = cx + math.cos(aa) * r
            py = cy + math.sin(aa) * r
            if da == 0:
                sweep_path.lineTo(px, py)
            else:
                sweep_path.lineTo(px, py)
        sweep_path.lineTo(cx, cy)
        col = QColor(color)
        col.setAlpha(int(30 * intensity))
        p.setBrush(QBrush(col))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawPath(sweep_path)

        # Leading edge line
        ex = cx + math.cos(a) * r
        ey = cy + math.sin(a) * r
        edge_col = QColor(color); edge_col.setAlpha(220)
        p.setPen(QPen(edge_col, 1.5))
        p.drawLine(QPointF(cx, cy), QPointF(ex, ey))

    def _draw_neural_mesh(self, p, cx, cy, r, color, intensity):
        """Animated neural network mesh sphere like reference image 5/6."""
        rng_state = random.Random(int(self._t * 2) % 1000)
        pts = []
        for dist_r, angle, z_off, spd in self._nodes:
            a = angle + self._t * spd * 2
            # 3D-ish projection
            x2d = cx + math.cos(a) * dist_r * r * math.cos(z_off + self._t * spd)
            y2d = cy + math.sin(a) * dist_r * r
            pts.append((x2d, y2d))

        # Draw connections
        col = QColor(color); col.setAlpha(50)
        p.setPen(QPen(col, 0.5))
        for i, (x1, y1) in enumerate(pts):
            for j, (x2, y2) in enumerate(pts[i+1:], i+1):
                dist = math.hypot(x2-x1, y2-y1)
                if dist < r * 0.7:
                    fade = QColor(color)
                    fade.setAlpha(int(70 * (1 - dist/(r*0.7))))
                    p.setPen(QPen(fade, 0.4))
                    p.drawLine(QPointF(x1, y1), QPointF(x2, y2))

        # Draw nodes
        for x, y in pts:
            nc = QColor(color); nc.setAlpha(int(160 + 60*intensity))
            p.setBrush(QBrush(nc))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QRectF(x-1.5, y-1.5, 3, 3))

    def _draw_hud_data(self, p, cx, cy, R, color):
        """Corner HUD readout data like reference image 9."""
        font = QFont("Courier New", 7)
        p.setFont(font)
        dim = QColor(color); dim.setAlpha(90)
        p.setPen(dim)

        offset = R * 0.72
        labels = [
            (cx - offset - 20, cy - offset - 10, f"CPU  {self._hud_vals[0]:.1f}%"),
            (cx + offset - 20, cy - offset - 10, f"RAM  {self._hud_vals[1]:.1f}%"),
            (cx - offset - 20, cy + offset,       f"NET  {self._hud_vals[2]:.1f}%"),
            (cx + offset - 20, cy + offset,       f"I/O  {self._hud_vals[3]:.1f}%"),
        ]
        for lx, ly, text in labels:
            p.drawText(QRectF(lx - 30, ly, 80, 14),
                       Qt.AlignmentFlag.AlignCenter, text)
