# Install ClubCpG on MacOS ARM64

## Install Samtools

```bash
brew install samtools
```

## Create and activate conda environment

```bash
conda env create --file environment.yml -n clubcpg
conda activate clubcpg
```

## Install pip packages

```bash
pip install setuptools==58.0.0  # to be able use 2to3
pip install --force-reinstall --ignore-installed --no-binary :all: pysam==0.15.4  # to install pysam with arm64 architecture
pip install .  # to install clubcpg
```

## Run tests

This must be ok:

```bash
python -m unittest -v clubcpg/tests/test_Module.py
```

## How to build conda environment from scratch

### Create empty environment

```bash
conda create -n clubcpg python=3.9
conda activate clubcpg
```

### Install conda packages

```bash
conda install -c conda-forge mamba  # mamba is faster than conda!
mamba install -c conda-forge numpy==1.19.4
mamba install -c conda-forge scipy==1.5.2
mamba install -c conda-forge pandas==1.1.3
mamba install -c conda-forge scikit-learn==0.23.2
mamba install cython
```

### Install remaining pip packages

```bash
pip install setuptools==58.0.0
pip install --force-reinstall --ignore-installed --no-binary :all: pysam==0.15.4
pip install .
```
