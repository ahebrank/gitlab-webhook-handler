import os
from distutils.core import setup

about = {}
here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here,'gwh', '__version__.py'), encoding='utf-8') as f:
    exec(f.read(), about)

setup(
    name=about['__title__'],
    version=about['__version__'],
    author='Andy Hebrank',
    author_email='ahebrank@gmail.com',
    packages=['gwh'],
    url='https://github.com/ahebrank/gitlab-webhook-handler',
    description='Webhook Handler for GitLab',
    license='Apache License, Version 2.0',
    long_description=open('README.md', encoding='utf-8').read(),
    install_requires=[
        'Flask>=1.0',
        'requests>=2.19.0'
    ]
)
