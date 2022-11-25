from setuptools import find_packages, setup
from typing import List


def get_requirements_list() -> List[str]:
    """
    This function returns a list of strings as requirements from the requirements.txt file.
    """
    with open("requirements.txt") as f:
        requirement_list = [line.replace("\n", "") for line in f.readlines()]
        if "-e ." in requirement_list:
            requirement_list.remove("-e .")
        return requirement_list


setup(
    name="sensor-fault-detection",
    version="0.0.1",
    author="Aritra Ganguly",
    author_email="aritraganguly.msc@protonmail.com",
    description="Sensor Fault Detection",
    packages=find_packages(),
    install_requires=get_requirements_list(),
)
