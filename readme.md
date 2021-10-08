## requirements
Recommend to run in virtual environment.
```
$ virtualenv env && source env/bin/activate
$ python script/get_require.py
```

## benchmak
`nvprof` requires the root permission, but `sudo` change the interpreter to use

```
$ sudo $(which python) benchmark/bench_utilization.py
```
