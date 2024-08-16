import glob
import shutil
import setuptools

setuptools.setup(
    name='util',
    packages=[''],
    package_dir={'': '.'},
    package_data={
        '': [
            'metadata/devices/*.json',
            'metadata/sensors/*.json',
        ],
    },
    include_package_data=True
)

# Remove metadata clutter
for i in glob.glob('*.egg-info'):
    shutil.rmtree(i)
