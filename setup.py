from setuptools import setup, find_packages

setup(
    name='arachnid',
    version='0.4',
    description='arachnid information gathering system',
    author='Brett Jurman',
    author_email='i.be.brett@gmail.com',
    packages=find_packages(),
    entry_points = {
        'console_scripts': [
            'run_redis_scraper = linkedin.run_redis_scraper:main',
            'add_url = linkedin.add_url:main',
            'queue_url = linkedin.queue_url:main',
            'health_check = linkedin.health_check',
        ]
    },
    install_requires = [
        'boto>=2.33.0',
        'beautifulsoup4>=4.3.2',
        'redis>=2.10.3',
        'rq>=0.4.6',
        'flask>=0.10.1',
        'requests>=2.4.3',
        'fake-useragent>=0.0.6'
    ]
)
