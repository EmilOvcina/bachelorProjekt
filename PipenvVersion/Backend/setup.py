from distutils.core import setup

setup(
    name='LiMiC',
    version='0.3.19',
    packages=['limic',],
    package_data={'limic':['render.js']},
    include_package_data=True,
    license='MIT License',
    url='https://pypi.org/project/LiMiC/',
    author='Peter Schneider-Kamp',
    author_email='petersk@imada.sdu.dk',
    description='Linear-infrastructure Mission Control (LiMiC)',
    long_description=open('README.txt').read(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=['requests','numpy','dogpile.cache','networkx','shapely','folium','flask','scipy','pyproj','setproctitle'],
    python_requires='>=3.4'
)
