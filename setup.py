from setuptools import setup
from Cython.Build import cythonize

setup(
    name="MyCompiledStreamlitApp",
    ext_modules=cythonize(["main_app_logic.py"]),
)
