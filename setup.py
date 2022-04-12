from setuptools import find_packages, setup

setup(
        name='hintdiff',
        version='1.2.0',
        packages=find_packages(),
        include_package_data=True,
        zip_safe=False,
        install_requires=[
            'flask',
            'fontTools',
            'freetype-py',
            'numpy',
            'pillow',
        ],
        entry_points={
            'console_scripts': [
                "hintdiff = hintdiff.__main__:main"
            ]
        }
)
