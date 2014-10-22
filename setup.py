from setuptools import setup, find_packages

print find_packages()
setup(
    name='arachnid',
    version='0.2',
    description='arachnid information gathering system',
    author='Brett Jurman',
    author_email='i.be.brett@gmail.com',
    packages=find_packages(),

    install_requires = [
        'boto>=2.33.0',
        'sqlalchemy>=0.9.8',
        'beautifulsoup4>=4.3.2',
        'redis>=2.10.3',
        'rq>=0.4.6'
    ],
    dependency_links = [
        'git+git://git@github.com:ibebrett/python-kinesis-consumer.git'
    ]
)
