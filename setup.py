from setuptools import setup


def readme():
    with open("affprop/README.rst", encoding= "utf-8") as f:
        return f.read()


setup(
    name="afprop",
    version="0.1.8.5",
    description="Affinity Propagation",
    long_description=readme(),
    packages=["affprop"],
    keywords="clustering",
    license="MIT",
    author="Lauren Palazzo & Hannah Yan",
    zip_safe=False,
    install_requires=["numpy", "scipy", "pandas", "matplotlib"],
    classifiers=["Programming Language :: Python :: 3.7",],
)
