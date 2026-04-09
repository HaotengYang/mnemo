from setuptools import setup, find_packages

setup(
    name="mnemo",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "chromadb>=0.4.0",
        "mcp>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "mnemo-server=mnemo.mcp_server:main",
        ],
    },
)
