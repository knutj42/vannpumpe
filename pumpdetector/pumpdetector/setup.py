from setuptools import setup

setup(
    name='Pump detector',
    packages=['pumpdetector'],
    include_package_data=True,
    install_requires=[
        'requests', 'pytz'
    ],
)