from memnova import const
from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name=const.APP_NAME,
    version=const.APP_VERSION,
    url=const.APP_URL,
    author=const.AUTHOR,
    license=const.APP_LICENSE,
    author_email=const.EMAIL,
    description=const.APP_DESC,
    packages=find_packages(),
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    install_requires=requirements,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: JavaScript',
        'Programming Language :: Python :: 3.11',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows :: Windows 11',
        'Natural Language :: Chinese (Simplified)',
        'Natural Language :: English',
    ]
)
