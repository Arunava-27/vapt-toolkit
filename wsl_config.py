"""WSL integration configuration — enables running Nmap & SearchSploit from WSL on Windows."""
import os
import platform
import shutil
import subprocess
from typing import Optional


class WSLConfig:
    """Detect and manage WSL environment for running Linux tools."""

    def __init__(self):
        self.is_wsl = self._detect_wsl()
        self.distro = self._get_distro() if self.is_wsl else None
        self.nmap_path = self._find_nmap()
        self.searchsploit_path = self._find_searchsploit()

    @staticmethod
    def _detect_wsl() -> bool:
        """Check if running in WSL on Windows."""
        if platform.system() != "Windows":
            return False
        try:
            with open("/proc/version", "r") as f:
                return "microsoft" in f.read().lower() or "wsl" in f.read().lower()
        except (FileNotFoundError, OSError):
            return False

    @staticmethod
    def _get_distro() -> Optional[str]:
        """Get the WSL distro name."""
        try:
            result = subprocess.run(
                ["wsl.exe", "--list", "--verbose"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            for line in result.stdout.split("\n"):
                if "*" in line:
                    return line.split()[0].strip("* ")
            return None
        except Exception:
            return None

    def _find_nmap(self) -> Optional[str]:
        """Find nmap binary — prioritize WSL, then Windows PATH, then Linux PATH."""
        # Try WSL first (if running on Windows)
        if platform.system() == "Windows":
            try:
                # Try to find nmap in default WSL (with longer timeout for WSL startup)
                result = subprocess.run(
                    ["wsl.exe", "which", "nmap"],
                    capture_output=True,
                    text=True,
                    timeout=15,  # Increased timeout for WSL startup
                )
                wsl_path = result.stdout.strip() if result.returncode == 0 else None
                
                if result.returncode == 0 and result.stdout.strip():
                    path = result.stdout.strip()
                    # If found in WSL, return it (prioritize WSL)
                    return path
            except Exception as e:
                pass

        # Try Windows PATH (fallback if WSL not available)
        windows_nmap = shutil.which("nmap")
        if windows_nmap:
            return windows_nmap

        # Try Linux PATH (for native Linux/WSL)
        return shutil.which("nmap")

    def _find_searchsploit(self) -> Optional[str]:
        """Find searchsploit binary — prioritize WSL, then Windows PATH, then Linux PATH."""
        # Try WSL first (if running on Windows)
        if platform.system() == "Windows":
            try:
                # Try to find searchsploit in default WSL (with longer timeout for WSL startup)
                result = subprocess.run(
                    ["wsl.exe", "which", "searchsploit"],
                    capture_output=True,
                    text=True,
                    timeout=15,  # Increased timeout for WSL startup
                )
                if result.returncode == 0 and result.stdout.strip():
                    path = result.stdout.strip()
                    # If found in WSL, return it (prioritize WSL)
                    return path
            except Exception as e:
                pass

        # Try Windows PATH (fallback if WSL not available)
        windows_ss = shutil.which("searchsploit")
        if windows_ss:
            return windows_ss

        # Try Linux PATH
        return shutil.which("searchsploit")

    def run_nmap_command(self, args: list[str]) -> subprocess.CompletedProcess:
        """Run nmap command, using WSL if available."""
        if not self.nmap_path:
            raise RuntimeError(
                "Nmap not found. Install with: "
                "Windows: choco install nmap  OR  WSL: sudo apt install nmap"
            )

        # If nmap_path is a Unix-style path (starts with /), run via WSL
        # This includes both /usr/bin/nmap and /mnt/... paths
        if self.nmap_path.startswith('/'):
            # Run via wsl.exe - just use "nmap" command name, not the full path
            full_cmd = ["wsl.exe", "nmap"] + args
        else:
            # Windows path - use directly
            full_cmd = [self.nmap_path] + args

        return subprocess.run(full_cmd, capture_output=True, text=True)

    def run_searchsploit_command(self, args: list[str]) -> subprocess.CompletedProcess:
        """Run searchsploit command, using WSL if available."""
        if not self.searchsploit_path:
            raise RuntimeError(
                "SearchSploit not found. Install with: "
                "WSL: sudo apt install exploitdb"
            )

        # If searchsploit_path is a Unix-style path (starts with /), run via WSL
        if self.searchsploit_path.startswith('/'):
            # Run via wsl.exe
            full_cmd = ["wsl.exe", "searchsploit"] + args
        else:
            # Windows path - use directly
            full_cmd = [self.searchsploit_path] + args

        return subprocess.run(full_cmd, capture_output=True, text=True)

    def get_status(self) -> dict:
        """Get WSL and tool availability status."""
        return {
            "running_on_wsl": self.is_wsl,
            "wsl_distro": self.distro,
            "nmap": {
                "available": bool(self.nmap_path),
                "path": self.nmap_path,
            },
            "searchsploit": {
                "available": bool(self.searchsploit_path),
                "path": self.searchsploit_path,
            },
        }


# Global instance
wsl = WSLConfig()
