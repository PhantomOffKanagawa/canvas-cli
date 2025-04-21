from setuptools import setup, find_packages
import os

# Read the contents of README.md
with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

# Get version from environment variable for CI/CD or use default
version = os.environ.get("RELEASE_VERSION", "0.1.0")

setup(
    name="canvas-cmd",  # Short, descriptive, and available
    version=version,
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.0",
    ],
    extras_require={
        "gui": [
            "rich",
        ],
        "convert": [
            "markitdown[docx,pdf]>=0.1.0",
        ],
        "full": [
            "rich",
            "markitdown[docx,pdf]>=0.1.0",
        ],
        "windows": [
            "windows-curses",
        ]
    },
    entry_points={
        "console_scripts": [
            "canvas=canvas_cli.cli:main",
        ],
    },
    description="A command-line tool for interacting with Canvas LMS",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="PhantomOffKanagawa",
    author_email="harry@surmafamily.com",
    url="https://github.com/PhantomOffKanagawa/canvas-cli",
    project_urls={
        "Bug Tracker": "https://github.com/PhantomOffKanagawa/canvas-cli/issues",
        "Documentation": "https://github.com/PhantomOffKanagawa/canvas-cli/wiki",
        "Source Code": "https://github.com/PhantomOffKanagawa/canvas-cli",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Environment :: Console",
        "Intended Audience :: Education",
        "Topic :: Education",
        "Topic :: Utilities",
    ],
    python_requires=">=3.9",
)
