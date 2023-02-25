from setuptools import find_packages,setup
from typing import List

def get_requirements()->List[str]:
    """
    This function will return list of requirements
    """
    requirement_list:List[str] = []
    with open('requirements.txt') as f:
        requirement_list=[require.strip() for require in f.readlines()]
        print(requirement_list)
    return requirement_list


setup(
    name="AutoDataAI",
    version="0.0.1",
    author="Suhaib arshad",
    author_email="suhaibarshad2017@gmail.com",
    packages = find_packages(),
    install_requires=get_requirements(),
)