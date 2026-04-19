#!/usr/bin/env python3
"""
Auto-XRD Skill Installation Script

安装 auto-xrd skill 到项目根目录。
安装后会在 <project_root>/auto_xrd/ 下创建完整的目录结构。
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(
        description="Install auto-xrd skill to project root directory"
    )
    parser.add_argument(
        "--skill-root",
        type=Path,
        default=None,
        help="Skill root directory (contains resources/, references/)",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        required=True,
        help="Project root directory where auto_xrd/ will be created",
    )
    return parser.parse_args()


def resolve_skill_root(skill_root: Path | None, script_dir: Path) -> Path:
    if skill_root is not None:
        return skill_root.resolve()

    current = script_dir
    for _ in range(5):
        if (current / "SKILL.md").exists() and (
            current / "resources"
        ).exists():
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent

    raise SystemExit(
        "Could not find skill root. "
        "Please specify --skill-root or run from the skill directory."
    )


def copy_directory(src: Path, dst: Path, ignore_patterns: list[str] | None = None):
    """Recursively copy directory with optional ignore patterns."""
    if ignore_patterns is None:
        ignore_patterns = []

    def should_ignore(path: str) -> bool:
        return any(pattern in path for pattern in ignore_patterns)

    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True, exist_ok=True)

    for item in src.rglob("*"):
        if item.is_file():
            if should_ignore(str(item)):
                continue
            rel_path = item.relative_to(src)
            dst_file = dst / rel_path
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, dst_file)


def setup_git_submodule(repo_dir: Path):
    """Initialize git submodule for XRD-1.1."""
    submodule_dir = repo_dir / "libs" / "XRD-1.1"
    gitmodules_file = submodule_dir / ".gitmodules"

    if not gitmodules_file.exists():
        print("[INFO] No git submodule config found, skipping submodule setup")
        return

    try:
        print("[INFO] Initializing git submodule...")
        subprocess.run(
            ["git", "submodule", "update", "--init", "--recursive"],
            cwd=repo_dir,
            check=True,
            capture_output=True,
        )
        print("[INFO] Git submodule initialized successfully")
    except subprocess.CalledProcessError as e:
        print(f"[WARN] Git submodule init failed: {e.stderr.decode()}")
        print("[INFO] You may need to run manually:")
        print(f"       cd {repo_dir}")
        print("       git submodule update --init --recursive")


def create_env_file(repo_dir: Path):
    """Create .env file with template."""
    env_file = repo_dir / ".env"
    env_template = """# Auto-XRD Configuration
# Materials Project API Key (required for downloading CIFs from MP)
MP_API_KEY=your_materials_project_api_key_here
"""

    if env_file.exists():
        print(f"[INFO] .env already exists at {env_file}, skipping")
        return

    env_file.write_text(env_template)
    print(f"[INFO] Created .env file at {env_file}")
    print("[INFO] Please edit .env and add your MP_API_KEY")


def create_requirements_file(repo_dir: Path):
    """Create requirements.txt file."""
    req_file = repo_dir / "requirements.txt"
    requirements = """# Core dependencies for Auto-XRD
pytorch
pymatgen
pymatgen-analysis-diffusion
mp-api
pandas
numpy
scikit-learn
pyts
matplotlib
python-dotenv
"""

    req_file.write_text(requirements)
    print(f"[INFO] Created requirements.txt at {req_file}")


def create_data_template(repo_dir: Path, resources_dir: Path):
    """Create data directory with README and copy example data."""
    data_dir = repo_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    readme_content = """# XRD Data Directory

Place your real XRD spectra files here.

## Supported formats

- `.txt` - Text format spectra
- `.xy` - XY format spectra
- `.gk` - GinaK format spectra

## Directory structure

You can organize data by phase or experiment:

```
data/
├── Fe2O3/
│   ├── sample1.txt
│   └── sample2.txt
├── TiO2/
│   └── sample1.txt
└── mixed/
    └── sample3.xy
```

## Naming convention

For automatic label inference, include the formula in the filename or directory name:
- `Fe2O3_sample1.txt` → inferred as Fe2O3
- `TiO2_rutile.txt` → inferred as TiO2

"""

    readme_file = data_dir / "README.md"
    readme_file.write_text(readme_content)

    data_template_src = resources_dir / "data_template"
    if data_template_src.exists():
        print("[INFO] Copying example data...")
        for item in data_template_src.rglob("*"):
            if item.is_file():
                rel_path = item.relative_to(data_template_src)
                dst_file = data_dir / rel_path
                dst_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dst_file)
        print(f"[INFO] Copied example data to {data_dir}")

    print(f"[INFO] Created data directory template at {data_dir}")


def create_local_cifs_template(repo_dir: Path):
    """Create local CIFs directory template."""
    cifs_dir = repo_dir / "local_cifs"
    cifs_dir.mkdir(parents=True, exist_ok=True)

    readme_content = """# Local CIF Files Directory

Place your local CIF (Crystallographic Information File) files here.

## Usage

When you want to use a specific crystal structure that is not available in Materials Project,
place the CIF file here and reference it in the training command.

Example:
```bash
bash scripts/run_multiphase_pipeline.sh \
  --local-cif "./local_cifs/MyCustomPhase.cif" \
  ...
```

## CIF file naming

It is recommended to include the formula and space group in the filename:
- `Fe2O3_R-3c.cif`
- `TiO2_P42mnm.cif`

"""

    readme_file = cifs_dir / "README.md"
    readme_file.write_text(readme_content)
    print(f"[INFO] Created local CIFs template at {cifs_dir}")


def create_venv(repo_dir: Path):
    """Create Python virtual environment."""
    venv_path = repo_dir.parent / ".venv"

    if venv_path.exists():
        print(f"[INFO] Virtual environment already exists at {venv_path}, skipping")
        return

    print("[INFO] Creating virtual environment...")
    try:
        subprocess.run([sys.executable, "-m", "uv", "venv", str(venv_path)], check=True)
        print(f"[INFO] Virtual environment created at {venv_path}")
    except FileNotFoundError:
        print("[WARN] uv not found, trying python3 -m venv...")
        try:
            subprocess.run(
                [sys.executable, "-m", "venv", str(venv_path)], check=True
            )
            print(f"[INFO] Virtual environment created at {venv_path}")
        except Exception as e:
            print(f"[WARN] Could not create virtual environment: {e}")
            print("[INFO] You may need to create it manually:")
            print(f"       cd {repo_dir.parent}")
            print("       python3 -m venv .venv")


def main():
    args = parse_args()

    script_dir = Path(__file__).parent.resolve()
    skill_root = resolve_skill_root(args.skill_root, script_dir)
    project_root = args.project_root.resolve()

    print("=" * 60)
    print("Auto-XRD Skill Installation")
    print("=" * 60)
    print(f"Skill root: {skill_root}")
    print(f"Project root: {project_root}")

    resources_dir = skill_root / "resources"
    if not resources_dir.exists():
        raise SystemExit(f"Resources directory not found: {resources_dir}")

    repo_dir = project_root / "auto_xrd"
    print(f"\n[INFO] Creating auto_xrd/ directory at {repo_dir}")

    repo_dir.mkdir(parents=True, exist_ok=True)

    print("[INFO] Copying scripts...")
    scripts_src = resources_dir / "scripts"
    scripts_dst = repo_dir / "scripts"
    if scripts_src.exists():
        copy_directory(scripts_src, scripts_dst)

    print("[INFO] Copying docker configuration...")
    docker_src = resources_dir / "docker"
    docker_dst = repo_dir / "docker"
    if docker_src.exists():
        copy_directory(docker_src, docker_dst)

    print("[INFO] Copying XRD repo template...")
    xrd_template_src = resources_dir / "xrd_repo_template"
    xrd_template_dst = repo_dir
    if xrd_template_src.exists():
        libs_src = xrd_template_src / "libs"
        libs_dst = repo_dir / "libs"
        if libs_src.exists():
            copy_directory(libs_src, libs_dst)

    create_env_file(repo_dir)
    create_requirements_file(repo_dir)
    create_data_template(repo_dir, resources_dir)
    create_local_cifs_template(repo_dir)

    setup_git_submodule(repo_dir)
    create_venv(repo_dir)

    print("\n" + "=" * 60)
    print("Installation completed!")
    print("=" * 60)
    print(f"\nNext steps:")
    print(f"  1. Edit .env file:")
    print(f"     nano {repo_dir / '.env'}")
    print(f"     Add your MP_API_KEY")
    print(f"\n  2. Activate virtual environment:")
    print(f"     source {project_root / '.venv' / 'bin' / 'activate'}")
    print(f"\n  3. Install dependencies:")
    print(f"     cd {repo_dir}")
    print(f"     pip install -r requirements.txt")
    print(f"\n  4. Build Docker image (optional):")
    print(f"     cd {repo_dir / 'docker'}")
    print(f"     docker compose up -d --build")
    print(f"\n  5. Start using the skill!")
    print("=" * 60)


if __name__ == "__main__":
    main()
