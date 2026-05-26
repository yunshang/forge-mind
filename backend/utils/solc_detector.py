import shutil
from pathlib import Path

from backend.config import settings


class SolcDetector:
    @staticmethod
    def find_solc() -> str | None:
        """Find solc binary. Returns path or None."""
        candidates = [
            settings.solc_path if settings.solc_path != "solc" else None,
            str(Path.home() / ".foundry" / "bin" / "solc"),
            "/usr/local/bin/solc",
            shutil.which("solc"),
        ]
        for path in candidates:
            if path and Path(path).is_file():
                return path
        return None

    @staticmethod
    def get_install_instructions() -> str:
        return (
            "未找到 solc 编译器。请安装 Foundry：\n"
            "  curl -L https://foundry.paradigm.xyz | bash\n"
            "  source ~/.zshrc  # 或 ~/.bashrc\n"
            "  foundryup\n"
            "安装完成后重启应用。"
        )
