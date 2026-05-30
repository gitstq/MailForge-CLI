from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="mailforge-cli",
    version="1.0.0",
    description="轻量级终端邮件营销智能引擎",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="MailForge Team",
    license="MIT",
    python_requires=">=3.9",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[],
    extras_require={
        "tui": [
            "rich>=13.0",
            "textual>=3.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "mailforge=mailforge.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Communications :: Email",
        "Topic :: Utilities",
    ],
)
