from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="telegram-broadcast-dmbot",
    version="1.0.0",
    author="Strad Dev",
    author_email="strad-dev131@example.com",
    description="A high-performance Telegram broadcasting bot with multi-account support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/strad-dev131/telegram-broadcast-dmbot",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "telegram-broadcast-bot=main:main",
        ],
    },
)
