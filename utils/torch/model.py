import sys
import os
import yaml
FilePath = os.path.dirname(os.path.abspath(__file__))
RootPath = os.path.join(FilePath, '..', '..')
sys.path.append(RootPath)
from model import CNN

class Arguments:
    def __init__(self):
        self.resume = False
        config_path = os.path.join(RootPath, 
            'RandWireNN/configs/config_regular_c109_n32.yaml')
        with open(config_path) as f:
            config = yaml.load(f)
        for key in config:
            for k, v in config[key].items():
                setattr(self, k, v)
        self.checkpoint_path = '\tmp'


def get_randwire():
    args = Arguments()
    return lambda : CNN(args)
    

def select_model(model_name: str):
    models = {'RandWire': (get_randwire(), (224, 224, 3))}

    model, input_shape = models.get(model_name)
    assert model or print('wrong model name')
    return model(), input_shape
