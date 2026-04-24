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
                result = subprocess.run(
                    ["wsl.exe", "which", "nmap"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    path = result.stdout.strip()
                    if path:
                        return path
            except Exception:
                pass

        # Try Windows PATH
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
                result = subprocess.run(
                    ["wsl.exe", "which", "searchsploit"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    path = result.stdout.strip()
                    if path:
                        return path
            except Exception:
                pass

        # Try Windows PATH
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

        # If nmap is in WSL, run via wsl.exe
        if platform.system() == "Windows" and "/mnt/" in self.nmap_path or self.is_wsl:
            full_cmd = ["wsl.exe", "nmap"] + args
        else:
            full_cmd = [self.nmap_path] + args

        return subprocess.run(full_cmd, capture_output=True, text=True)

    def run_searchsploit_command(self, args: list[str]) -> subprocess.CompletedProcess:
        """Run searchsploit command, using WSL if available."""
        if not self.searchsploit_path:
            raise RuntimeError(
                "SearchSploit not found. Install with: "
                "WSL: sudo apt install exploitdb"
            )

        # If searchsploit is in WSL, run via wsl.exe
        if platform.system() == "Windows" and "/mnt/" in self.searchsploit_path or self.is_wsl:
            full_cmd = ["wsl.exe", "searchsploit"] + args
        else:
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
