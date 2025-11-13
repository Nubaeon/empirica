#!/usr/bin/env python3
"""
Setup script for Empirica - Genuine AI Epistemic Self-Assessment Framework
"""

from setuptools import setup, find_packages

# Read README for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="empirica",
    version="0.1.0",
    author="Empirica Team",
    description="Genuine AI epistemic self-assessment framework - No heuristics, true metacognition",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/empirica/empirica",
    project_urls={
        "Bug Tracker": "https://github.com/empirica/empirica/issues",
        "Documentation": "https://github.com/empirica/empirica/tree/main/docs",
        "Source Code": "https://github.com/empirica/empirica",
    },
    packages=find_packages(exclude=["tests*", "_archive*", "_dev*", "claude-skills*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4",
            "pytest-asyncio>=0.21",
            "pytest-cov>=4.1",
            "pytest-mock>=3.11",
            "dirty-equals>=0.7",
            "ruff>=0.1.0",
            "pyright>=1.1.330",
        ],
        "mcp": [
            "mcp>=0.1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "empirica=empirica.cli.cli_core:main",
        ],
    },
    include_package_data=True,
    package_data={
        "empirica": ["config/*.json", "config/*.yaml"],
    },
    keywords=[
        "ai", "llm", "epistemic", "self-assessment", "metacognition",
        "calibration", "uncertainty", "no-heuristics", "genuine",
        "empirica", "reflex-frame", "cascade"
    ],
)
