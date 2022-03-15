## clone
```
$ git clone https://github.com/colinyoyo26/research --recursive
```


## requirements
Recommend to run in virtual environment.
```
$ virtualenv env && source env/bin/activate
$ python script/get_require.py
```

Then you need to build the tvm and set the environment variable
```
$ export TVM_HOME=third_party/tvm
```

## benchmak
`nvprof` requires the root permission, but `sudo` change the interpreter to use

```
$ sudo PYTHONPATH=$TVM_HOME/python:${PYTHONPATH} LD_LIBRARY_PATH=$LD_LIBRARY_PATH PATH=$PATH bash -c "$(which python) benchmark/bench_utilization.py"
```

## verify

```
sudo PYTHONPATH=$TVM_HOME/python:${PYTHONPATH} LD_LIBRARY_PATH=$LD_LIBRARY_PATH PATH=$PATH bash -c "$(which python) verify/verify.py"
```
