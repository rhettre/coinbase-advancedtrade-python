#!/bin/bash

set -e

# Define package name
PACKAGE_NAME=coinbase_advancedtrade_python

# Remove existing distribution and build directories
sudo rm -rf dist build

# Generate stubs
stubgen -p coinbase_advanced_trade -o pyi
cp -r pyi/coinbase_advanced_trade/* ./coinbase_advanced_trade/
sudo rm -rf pyi

# Build the wheel
sudo /usr/bin/python3 setup.py bdist_wheel

# Navigate to the distribution directory
cd dist

# Uninstall the existing package (if installed)
pip3 uninstall -y $PACKAGE_NAME

# Install the newly built packag
pip3 install $PACKAGE_NAME-*.whl
cd ..
sudo rm -rf build 
sudo rm -rf coinbase_advancedtrade_python.egg-info 
sudo rm -rf .mypy_cache
sudo chown -R $USER:$USER ./

