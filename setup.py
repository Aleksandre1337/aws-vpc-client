from setuptools import setup, find_packages

setup(
    name="vpc_boto3",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "boto3",
        "python-dotenv",
        "ipaddress"
    ],
    author="Your Name",
    author_email="your.email@example.com",
    description="A Python package to manage AWS VPCs using boto3",
    long_description=open('README.md', 'r').read() + "\n\nDependencies:\n- boto3\n- python-dotenv\n- ipaddress",
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/vpc_boto3",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
