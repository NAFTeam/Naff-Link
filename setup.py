from setuptools import setup

setup(
    name="naff_link",
    version="0.0.1",
    author="LordOfPolls",
    author_email="dev@lordofpolls.com",
    description="A Lavalink.py wrapper for Naff",
    long_description="A Lavalink.py wrapper for Naff",
    long_description_content_type="text/markdown",
    url="https://github.com/NAFTeam/Naff-Link",
    packages=["naff_link"],
    python_requires=">=3.10",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=["lavalink", "naff"],
)
