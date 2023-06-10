import glob
import shutil
import setuptools

setuptools.setup(name="util", packages=setuptools.find_packages())

# Remove metadata clutter
for i in glob.glob('*.egg-info'):
    shutil.rmtree(i)
