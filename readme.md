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
