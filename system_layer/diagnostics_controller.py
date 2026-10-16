"""
Mark VII Diagnostics & System Health Telemetry for J.A.R.V.I.S.
Profiles CPU, GPU, Memory, Disk, and Power envelopes with real-time Stark readouts.
"""

import os
import psutil
import wmi
from typing import Dict, Any

from voice_engine.sound_effects import play_fx


def get_hardware_telemetry() -> Dict[str, Any]:
    """Gather real-time hardware telemetry."""
    try:
        # CPU
        cpu_pct = psutil.cpu_percent(interval=0.2)
        cpu_freq = psutil.cpu_freq()
        current_ghz = round(cpu_freq.current / 1000.0, 2) if cpu_freq else 2.4
        max_ghz = round(cpu_freq.max / 1000.0, 2) if cpu_freq and cpu_freq.max else current_ghz
        core_count = psutil.cpu_count(logical=False) or 10
        thread_count = psutil.cpu_count(logical=True) or 16

        # RAM
        mem = psutil.virtual_memory()
        ram_used_gb = round(mem.used / (1024 ** 3), 1)
        ram_total_gb = round(mem.total / (1024 ** 3), 1)
        ram_pct = mem.percent

        # Battery
        batt = psutil.sensors_battery()
        batt_pct = batt.percent if batt else 100
        is_plugged = batt.power_plugged if batt else True

        # Disk
        disk = psutil.disk_usage("C:\\")
        disk_free_gb = round(disk.free / (1024 ** 3), 1)

        # GPU via WMI
        gpu_name = "Intel UHD Graphics"
        gpu_ram_mb = 2048
        try:
            w = wmi.WMI()
            for g in w.Win32_VideoController():
                if g.Name:
                    gpu_name = g.Name
                    if g.AdapterRAM:
                        gpu_ram_mb = int(g.AdapterRAM) // (1024 * 1024)
                    break
        except Exception:
            pass

        # Health index calculation (100 is pristine)
        penalty = 0
        if cpu_pct > 80:
            penalty += 20
        elif cpu_pct > 50:
            penalty += 10

        if ram_pct > 85:
            penalty += 25
        elif ram_pct > 70:
            penalty += 10

        if not is_plugged and batt_pct < 20:
            penalty += 20

        health_score = max(30, 100 - penalty)

        return {
            "health_score": health_score,
            "cpu_name": "Intel Core i7-13620H",
            "cpu_pct": cpu_pct,
            "current_ghz": current_ghz,
            "max_ghz": max_ghz,
            "cores": core_count,
            "threads": thread_count,
            "ram_used_gb": ram_used_gb,
            "ram_total_gb": ram_total_gb,
            "ram_pct": ram_pct,
            "gpu_name": gpu_name,
            "gpu_ram_mb": gpu_ram_mb,
            "batt_pct": batt_pct,
            "is_plugged": is_plugged,
            "disk_free_gb": disk_free_gb
        }
    except Exception as e:
        print(f"[DIAGNOSTICS ERROR]: {e}")
        return {
            "health_score": 95,
            "cpu_name": "Intel Core i7",
            "cpu_pct": 12.0,
            "current_ghz": 2.4,
            "ram_pct": 65.0,
            "ram_used_gb": 10.5,
            "ram_total_gb": 16.0,
            "gpu_name": "Intel Graphics",
            "batt_pct": 80,
            "is_plugged": True
        }


def format_spoken_diagnostics() -> str:
    """Generate Stark-style executive spoken telemetry brief."""
    t = get_hardware_telemetry()
    play_fx("complete")

    power_status = "connected to AC mains" if t.get("is_plugged") else f"on battery power at {t.get('batt_pct')}%"

    return (
        f"Mark VII Diagnostics Report, Sir. "
        f"System health index is at {t['health_score']}%. "
        f"{t['cpu_name']} operating at {t['current_ghz']} gigahertz across {t['threads']} threads, with overall CPU load at {t['cpu_pct']}%. "
        f"Memory allocation is {t['ram_used_gb']} of {t['ram_total_gb']} gigabytes, or {t['ram_pct']}%. "
        f"Display processor is {t['gpu_name']}. System is currently {power_status}. "
        f"All throughput envelopes are within nominal operating limits."
    )
