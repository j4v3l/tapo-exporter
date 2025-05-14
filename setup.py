from setuptools import find_packages, setup

setup(
    name="tapo-exporter",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "prometheus-client>=0.16.0",
        "python-tapo>=3.0.0",
        "aiohttp>=3.8.0",
        "python-dotenv>=0.19.0",
    ],
    entry_points={
        "console_scripts": [
            "tapo-exporter=tapo_exporter.__main__:main",
        ],
    },
    author="Javel Palmer",
    author_email="jj4v3l@example.com",
    description="A Prometheus exporter for Tapo smart plugs",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/j4v3l/tapo-exporter",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
)
