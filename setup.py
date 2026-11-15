from setuptools import find_packages, setup
from os import path
from io import open

ver_file = path.join("popper", "version.py")
with open(ver_file) as f:
    exec(f.read())

this_directory = path.abspath(path.dirname(__file__))


def readme():
    with open(path.join(this_directory, "README.md"), encoding="utf-8") as f:
        return f.read()


with open(path.join(this_directory, "requirements.txt"), encoding="utf-8") as f:
    requirements = [line.strip() for line in f.read().splitlines() if line.strip() and not line.startswith("#")]

setup(
    name="popper_agent",
    version=__version__,
    license="MIT",
    description="POPPER-Swarm: Automated Hypothesis Validation & Computational Biology Reproduction with Agentic Sequential Falsifications",
    long_description=readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/snap-stanford/POPPER",
    author="POPPER-Swarm Team (extending Huang, Jin, Li, Li, Candes & Leskovec, 2025)",
    packages=find_packages(where=".") + find_packages(where="src"),
    package_dir={"": ".", "popper_swarm": "src/popper_swarm"},
    zip_safe=False,
    include_package_data=True,
    install_requires=requirements,
    setup_requires=["setuptools>=38.6.0"],
)
