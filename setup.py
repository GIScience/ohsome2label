from setuptools import setup
from setuptools import find_packages
import io
from os import path as op


# get the dependencies and installs
with io.open('requirements.txt', encoding='utf-8') as f:
    all_reqs = f.read().split('\n')

install_requires = [x.strip() for x in all_reqs if 'git+' not in x]

# get readme
with io.open('ohsome2label/readme.md') as f:
    readme = f.read()

setup(
    name='ohsome2label',
    version='1.1.1',
    packages=find_packages(),
    author='Zhaoyan Wu, Hao Li',
    author_email='zhaoyan_wu@whu.edu.cn, hao.li@uni-heidelberg.de',
    description="""Historical OpenStreetMap Objects
                to Machine Learning Training Samples""",
    url='https://github.com/GIScience/ohsome2label',
    license='MIT',
    package_data={
        "": ["*.txt"],
        "polygon-features": ["ohsome2label/polygon-features.json"]
    },
    include_package_data=True,
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6'
    ],
    python_requires=">=3.6",
    py_module=['main'],
    install_requires=install_requires,
    long_description=readme,
    long_description_content_type="text/markdown",
    entry_points="""
        [console_scripts]
        ohsome2label=ohsome2label.main:cli
    """,
)
