from glob import glob
from setuptools import setup, find_packages

# Read requirements from requirements.txt
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

# Read the contents of your README file
with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

images_list = glob('images/*.*')

setup(
    name="typebuild",
    version="0.0.22",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'typebuild': images_list,
    },
    install_requires=requirements,
    author="iRanadheer",
    author_email="neneranadheer@gmail.com",
    description="A brief description of your package",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/project-typebuild/typebuild",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: Other/Proprietary License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10"       

    ],
    entry_points={
        'console_scripts': [
            'typebuild = typebuild.app:run',
        ],
    },
)