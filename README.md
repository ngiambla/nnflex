# NNFLex


A flexible simulator framework for modern and upcoming ML/NN Accelerators.

## Installation

If PyYAML and NumPy are not already installed, install them.
```bash
pip3 install pyyaml numpy onnx onnxruntime
```

Now, clone this repository:

```bash
git clone https://github.com/ngiambla/nnflex.git
cd nnflex;
git submodule update --init --recursive
```

Lastly, navigate to `dramsim2/` and execute the following:

```bash
make
``` 

Now, you can use `nnflex`

## Usage

```
usage: nnflex.py [-h] -m MODEL -c CONFIG

NNFlex: A Flexible Neural Network Accelerator Simulation Engine

optional arguments:
  -h, --help            show this help message and exit
  -m MODEL, --model MODEL
                        The ONNX File representing the Neural Network
  -c CONFIG, --config CONFIG
                        The YAML file representing the configuation of the accelerator


```

`nnflex` requires an ONNX file (which is the model you'd like to execute) and a YAML file outlining the configuration for a supported accelerator.

An example is provided in `examples`:

```bash
python3 nnflex.py -m examples/mnist.onnx -c accel.yaml

```

## Custom Accelerators:

In order to simulate "any" accelerator, you'll need to implement a _cycle-accurate_ model of the accelerator of your choosing.

Use `accelerators/nio` as a reference. Here we show how we can implement a number of devices that an accelerator may use.


## Tests


Software testing is essential, especially when we develop simulators. In the `tests/` folder, you'll find a number of tests which explores the safety and usability of `nnflex`'s core data-structures. NOTE: You'll need `pytest` to run these tests.

To run these tests, execute the following:

```bash
pytest tests/ 
```


## Future Work

* Support for _all_ ONNX nodes.
* Refactor operator-accelerator mappings (e.g., even using a compiler.)
* Add correctness checks (e.g., run an ONNX Model and the accelerator-model-mapping side-by-side)
* Continue adding tests, and checks.
* Improve the performance (e.g., threading some of the logic.)

## Contributing

If you are contributing:

(1) Iteratively use `pylint` and `autopep8` to ensure your code conforms to the python standard.
(2) Any new code _requires_ tests. No tests, no commits. 
(3) Before writing code, ask yourself "What problem am I trying to solve." Plan a bit first. 

### GitHub

When adding new features/bug fixes, follow these steps:

(a) Create a new branch, and name the branch `your_username/name_of_branch`
(b) Try to only add commits which have a purpose (e.g., a "clean-up" commit which renames files, )
(c) When you are finished, please put your branch through a code-review.
(d) If the code review was successful (i.e., your colleagues say "launch it"), perform a _squash-and-merge_. 
    By having a clean-history, it's easier to track substantial changes which affect the integrity of this repo.


## Contribution Shout-Outs

For any contributor, add what you've done.

## Author

Nicholas V. Giamblanco, B.Eng., M.A.Sc., 2021.

