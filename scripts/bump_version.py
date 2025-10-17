#!/usr/bin/env python3
"""
Version management script supporting major, minor, and patch version updates
with automatic git tagging and commit creation
"""

import argparse
import re
import os
import subprocess


def run_git_command(cmd):
    """Run git command and return result"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Git command failed: {e}")
        print(f"Error output: {e.stderr}")
        raise


def create_git_tag(version):
    """Create git tag for the new version"""
    tag_name = f"v{version}"
    print(f"Creating git tag: {tag_name}")
    run_git_command(f"git tag {tag_name}")
    print(f"Tag {tag_name} created successfully")


def create_version_commit(old_version, new_version, version_type):
    """Create commit for version bump"""
    commit_message = f"bump: {version_type} version {old_version} → {new_version}"
    print(f"Creating commit: {commit_message}")

    # Add version files to staging
    run_git_command("git add pyproject.toml src/patent_downloader/__init__.py")

    # Create commit
    run_git_command(f"git commit -m '{commit_message}' -n")
    print("Commit created successfully")


def update_version_files(new_version):
    """Update version in all files"""
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Update pyproject.toml
    pyproject_path = os.path.join(script_dir, "../pyproject.toml")
    with open(pyproject_path, "r") as f:
        content = f.read()
    # Precise replacement for version = "x.x.x" format
    content = re.sub(r"version\s*=\s*[\"'][0-9]+\.[0-9]+\.[0-9]+[\"']", f'version = "{new_version}"', content)
    with open(pyproject_path, "w") as f:
        f.write(content)

    # Update __init__.py
    init_path = os.path.join(script_dir, "../src/patent_downloader/__init__.py")
    with open(init_path, "r") as f:
        content = f.read()
    # Precise replacement for __version__ = "x.x.x" format
    content = re.sub(r"__version__\s*=\s*[\"'][0-9]+\.[0-9]+\.[0-9]+[\"']", f'__version__ = "{new_version}"', content)
    with open(init_path, "w") as f:
        f.write(content)


def calculate_new_version(current_version, version_type):
    """Calculate new version based on current version and update type"""
    # Check if version is empty
    if not current_version or current_version.strip() == "":
        raise ValueError("Current version is empty")

    # Ensure version format is correct
    if not re.match(r"^\d+\.\d+\.\d+$", current_version):
        raise ValueError(f"Invalid current version format: '{current_version}'")

    try:
        major, minor, patch = map(int, current_version.split("."))
    except ValueError:
        raise ValueError(f"Cannot parse version components from: '{current_version}'")

    if version_type == "major":
        return f"{major + 1}.0.0"
    elif version_type == "minor":
        return f"{major}.{minor + 1}.0"
    elif version_type == "patch":
        return f"{major}.{minor}.{patch + 1}"
    else:
        raise ValueError(f"Invalid version type: {version_type}")


def get_current_version():
    """Get current version from pyproject.toml"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    pyproject_path = os.path.join(script_dir, "../pyproject.toml")

    try:
        with open(pyproject_path, "r") as f:
            content = f.read()

        # Look for version = "x.x.x" format
        match = re.search(r"version\s*=\s*[\"']([0-9]+\.[0-9]+\.[0-9]+)[\"']", content)
        if match:
            return match.group(1)

        # If first format not found, try alternative format
        match = re.search(r"version\s*=\s*([0-9]+\.[0-9]+\.[0-9]+)", content)
        if match:
            return match.group(1)

        raise ValueError("Version not found in expected format")

    except FileNotFoundError:
        raise ValueError(f"File not found: {pyproject_path}")
    except Exception as e:
        raise ValueError(f"Error reading pyproject.toml: {e}")


def main():
    parser = argparse.ArgumentParser(description="Version management tool")
    parser.add_argument("type", choices=["major", "minor", "patch"], help="Version update type: major, minor, patch")
    parser.add_argument("--no-commit", action="store_true", help="Skip creating git commit")
    parser.add_argument("--no-tag", action="store_true", help="Skip creating git tag")

    args = parser.parse_args()

    current_version = get_current_version()
    print(f"Current version: {current_version}")

    new_version = calculate_new_version(current_version, args.type)
    update_version_files(new_version)
    print(f"Version updated successfully: {current_version} -> {new_version}")

    if not args.no_commit:
        create_version_commit(current_version, new_version, args.type)
    if not args.no_tag:
        create_git_tag(new_version)


if __name__ == "__main__":
    main()
