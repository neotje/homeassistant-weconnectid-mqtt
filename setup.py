from setuptools import setup, find_packages

PROJECT_NAME = "homeassistant-weconnectid-mqtt"
PROJECT_PACKAGE_NAME = "hassweconnectmqtt"

PROJECT_GITHUB_USERNAME = "neotje"

PACKAGES = find_packages()

REQUIRED = [
    "weconnect>=0.22.1",
    "paho-mqtt>=1.6.1"
]

setup(
    name=PROJECT_PACKAGE_NAME,
    packages=PACKAGES,
    install_requires=REQUIRED,
    entry_points={
        "console_scripts": [
            "hass-weconnect-mqtt = hassweconnectmqtt.__main__:main"
        ]
    },
    python_requires='>=3.7'
)
