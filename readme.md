# nimble-engine

Nimble Engine is a basic 3d game engine written in python. 
It renders the 3d models using low level GLSL shaders (with OpenGL). 
Before you ask: *yes*, I know, this is probably not suitable for super-serious 
games, because python is slow. It's more for learning purposes, like pygame.

<br>

## running

The easiest way to try nimble is to download the packaged binaries, found in the [releases page]().

<br>

## running from source

You will need:

* Python (3.9+)
* Conda

Download the source either through github zip, or:
```bash
git clone https://github.com/MonliH/nimble-engine.git
cd nimble-engine
```

Activate a conda environment, for example `base`:

```bash
conda activate base
```

Install the dependencies:

```bash
conda install -c conda-forge pyqtads
pip install -r requirements.txt
```

Then run:

```
python -m nimble
```

## building into an executable

NOTE: make sure the commands below are run in the conda environment that 
you set up above.

For now, nimble uses pyinstaller to bundle everything into an executable. Make sure to install my branch with a patched splash screen:

```bash
pip install git+https://github.com/MonliH/pyinstaller.git@develop
```

Then build using the `nimble.spec` file:

```bash
pyinstaller nimble.spec
```
