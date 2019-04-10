# -*- coding: utf-8 -*-
from setuptools import setup
import versioneer

requirements = [
    'jinja2',
    "jupyterhub >=0.9.6,<1",
]

setup(
    name='terraformspawner',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description="Spawn JupyterHub single-user servers with Terraform",
    author="Patrick Sodré",
    author_email='sodre@sodre.co',
    url='https://github.com/sodre/terraformspawner',
    packages=['terraformspawner'],
    entry_points={
        'console_scripts': [
            'terraformspawner=terraformspawner.cli:cli'
        ]
    },
    install_requires=requirements,
    keywords='terraformspawner',
    classifiers=[
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ]
)
