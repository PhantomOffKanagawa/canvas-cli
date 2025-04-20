from setuptools import setup, find_packages

setup(
    name="canvas-cli",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests",
    ],
    entry_points={
        "console_scripts": [
            "canvas=canvas_cli.cli:main",
        ],
    },
    description="A command-line tool for interacting with Canvas LMS",
    author="PhantomOffKanagawa",
    url="https://github.com/PhantomOffKanagawa/canvas-cli",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GPL v3 License",
        "Operating System :: OS Independent",
    ],
)
