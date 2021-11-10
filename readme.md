## requirements
Recommend to run in virtual environment.
```
$ virtualenv env && source env/bin/activate
$ python script/get_require.py
```

Then you need to build the tvm and set the environment variable
```
$ export TVM_HOME={your tvmpath}
```

## benchmak
`nvprof` requires the root permission, but `sudo` change the interpreter to use

```
$ sudo PYTHONPATH=$TVM_HOME/python:${PYTHONPATH} bash -c "$(which python) benchmark/bench_utilization.py"
```
