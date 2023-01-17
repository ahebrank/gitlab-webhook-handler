import os
from setuptools import setup

setup(
    name="gwh",
    author='Andy Hebrank',
    author_email='ahebrank@gmail.com',
    packages=['gwh'],
    url='https://github.com/ahebrank/gitlab-webhook-handler',
    description='Webhook Handler for GitLab',
    license='Apache License, Version 2.0',
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    install_requires=[
        'Flask>=1.0',
        'requests>=2.19.0'
    ]
)
