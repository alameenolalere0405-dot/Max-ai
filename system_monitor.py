"""
MAX AI — System Monitor
LEREON Technologies

Real-time CPU, RAM, disk, battery, network, process monitoring.
Designed for non-blocking use in PyQt6 — emits data via callbacks.
"""

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Optional, List

logger = logging.getLogger("MAX.monitor")


@dataclass
class SystemSnapshot:
    timestamp: float = field(default_factory=time.time)
    cpu_percent: float = 0.0
    cpu_cores: int = 1
    cpu_freq_mhz: float = 0.0
    ram_total_mb: int = 0
    ram_used_mb: int = 0
    ram_percent: float = 0.0
    disk_total_gb: float = 0.0
    disk_used_gb: float = 0.0
    disk_percent: float = 0.0
    battery_percent: Optional[float] = None
    battery_plugged: Optional[bool] = None
    net_bytes_sent: int = 0
    net_bytes_recv: int = 0
    net_speed_up_kbs: float = 0.0
    net_speed_down_kbs: float = 0.0
    top_processes: List[dict] = field(default_factory=list)
    platform_name: str = ""
    uptime_seconds: float = 0.0

    def health_score(self) -> int:
        """0-100 overall health score."""
        score = 100
        if self.cpu_percent > 80:  score -= 20
        elif self.cpu_percent > 60: score -= 10
        if self.ram_percent > 85:  score -= 20
        elif self.ram_percent > 70: score -= 10
        if self.disk_percent > 90: score -= 20
        elif self.disk_percent > 75: score -= 10
        if self.battery_percent is not None and not self.battery_plugged:
            if self.battery_percent < 20: score -= 20
            elif self.battery_percent < 40: score -= 10
        return max(0, score)


class SystemMonitor:
    """
    Polls system stats in a background thread.
    Call start() to begin, stop() to end.
    Register callbacks via on_update().
    """

    def __init__(self, interval_seconds: float = 2.0):
        self._interval = interval_seconds
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._callbacks: List[Callable[[SystemSnapshot], None]] = []
        self._last_net = None
        self._last_net_time = None
        self._latest: Optional[SystemSnapshot] = None

    def on_update(self, cb: Callable[[SystemSnapshot], None]):
        self._callbacks.append(cb)

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="MAX-Monitor")
        self._thread.start()
        logger.info("System monitor started.")

    def stop(self):
        self._running = False
        logger.info("System monitor stopped.")

    def get_latest(self) -> Optional[SystemSnapshot]:
        return self._latest

    def _loop(self):
        while self._running:
            try:
                snap = self._collect()
                self._latest = snap
                for cb in self._callbacks:
                    try:
                        cb(snap)
                    except Exception as e:
                        logger.warning(f"Monitor callback error: {e}")
            except Exception as e:
                logger.error(f"Monitor collection error: {e}")
            time.sleep(self._interval)

    def _collect(self) -> SystemSnapshot:
        try:
            import psutil
            import platform
        except ImportError:
            return SystemSnapshot(platform_name="psutil not installed")

        snap = SystemSnapshot()
        snap.platform_name = f"{platform.system()} {platform.release()}"

        # CPU
        snap.cpu_percent = psutil.cpu_percent(interval=None)
        snap.cpu_cores   = psutil.cpu_count(logical=True) or 1
        try:
            freq = psutil.cpu_freq()
            snap.cpu_freq_mhz = freq.current if freq else 0.0
        except Exception:
            pass

        # RAM
        mem = psutil.virtual_memory()
        snap.ram_total_mb = mem.total // 1024**2
        snap.ram_used_mb  = mem.used  // 1024**2
        snap.ram_percent  = mem.percent

        # Disk (root)
        try:
            disk = psutil.disk_usage("/")
            snap.disk_total_gb = disk.total / 1024**3
            snap.disk_used_gb  = disk.used  / 1024**3
            snap.disk_percent  = disk.percent
        except Exception:
            pass

        # Battery
        try:
            batt = psutil.sensors_battery()
            if batt:
                snap.battery_percent = batt.percent
                snap.battery_plugged  = batt.power_plugged
        except Exception:
            pass

        # Network
        try:
            net = psutil.net_io_counters()
            now = time.time()
            if self._last_net and self._last_net_time:
                dt = now - self._last_net_time
                if dt > 0:
                    snap.net_speed_up_kbs   = (net.bytes_sent - self._last_net.bytes_sent) / 1024 / dt
                    snap.net_speed_down_kbs = (net.bytes_recv - self._last_net.bytes_recv) / 1024 / dt
            self._last_net = net
            self._last_net_time = now
            snap.net_bytes_sent = net.bytes_sent
            snap.net_bytes_recv = net.bytes_recv
        except Exception:
            pass

        # Uptime
        try:
            snap.uptime_seconds = time.time() - psutil.boot_time()
        except Exception:
            pass

        # Top processes
        try:
            procs = []
            for p in psutil.process_iter(["name", "cpu_percent", "memory_percent"]):
                try:
                    procs.append({
                        "name": p.info["name"] or "?",
                        "cpu":  round(p.info["cpu_percent"] or 0, 1),
                        "mem":  round(p.info["memory_percent"] or 0, 1),
                    })
                except Exception:
                    pass
            snap.top_processes = sorted(procs, key=lambda x: x["cpu"], reverse=True)[:8]
        except Exception:
            pass

        return snap

    def format_snapshot(self, snap: SystemSnapshot) -> str:
        """Human-readable system status string."""
        lines = [
            f"OS: {snap.platform_name}",
            f"CPU: {snap.cpu_percent:.1f}% ({snap.cpu_cores} cores @ {snap.cpu_freq_mhz:.0f} MHz)",
            f"RAM: {snap.ram_percent:.1f}% — {snap.ram_used_mb} MB / {snap.ram_total_mb} MB",
            f"Disk: {snap.disk_percent:.1f}% — {snap.disk_used_gb:.1f} GB / {snap.disk_total_gb:.1f} GB",
        ]
        if snap.battery_percent is not None:
            plug = "⚡ plugged" if snap.battery_plugged else "🔋 battery"
            lines.append(f"Battery: {snap.battery_percent:.0f}% ({plug})")
        lines.append(f"Network ↑ {snap.net_speed_up_kbs:.1f} KB/s  ↓ {snap.net_speed_down_kbs:.1f} KB/s")
        uptime_h = int(snap.uptime_seconds // 3600)
        uptime_m = int((snap.uptime_seconds % 3600) // 60)
        lines.append(f"Uptime: {uptime_h}h {uptime_m}m")
        lines.append(f"Health score: {snap.health_score()}/100")
        return "\n".join(lines)
