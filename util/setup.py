import glob
import shutil
import setuptools

setuptools.setup(
    name='util',
    packages=['util'],
    package_dir={'util': '.'},
    package_data={
        'util': [
            'metadata/devices/*.json',
            'metadata/sensors/*.json',
        ],
    },
    include_package_data=True
)

# Remove metadata clutter
for i in glob.glob('*.egg-info'):
    shutil.rmtree(i)
