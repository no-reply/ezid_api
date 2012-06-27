from setuptools import setup

setup(name='ezidApi',
      version='0.2.0',
      description="Tools for the California Digital Library EZID API", 
      author='t. johnson',
      author_email='thomas.johnson@oregonstate.edu',
      py_modules = ['ezid_api'],
      scripts = ['ezid_api.py'],
      test_suite = 'test'
     )
