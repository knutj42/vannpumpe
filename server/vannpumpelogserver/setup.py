from setuptools import setup

setup(
    name='Vannpumpe logserver',
    packages=['vannpumpelogserver'],
    include_package_data=True,
    install_requires=[
        'flask',
    ],
)