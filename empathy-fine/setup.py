"""
Setup configuration for EmpathyFine
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="empathy-fine",
    version="0.1.0",
    author="EmpathyFine Team",
    author_email="team@empathyfine.ai",
    description="State-of-the-art GUI for training empathy-focused language models",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/empathyfine/empathy-fine",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "empathy-fine=gui.main_window:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
) 