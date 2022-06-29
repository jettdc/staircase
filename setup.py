from setuptools import setup, find_packages

with open('README.md') as f:
    readme = f.read()

setup(
    name='staircase',
    version='0.0.1',
    author='Jett Crowson & Dylan Cormican',
    author_email='jettcrowson@gmail.com',
    url='https://github.com/jettdc/staircase',
    description='Simple step-based testing framework.',
    long_description=readme,
    long_description_content_type='text/markdown',
    license='MIT',
    packages=find_packages(),
    keywords='testing framework test-framework step-testing',
    python_requires='>=3.10',
    install_requires=['colorama', 'jetts-tools', 'barb', 'python-dotenv']
)
