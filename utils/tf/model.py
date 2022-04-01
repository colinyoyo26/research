import tensorflow as tf
from tensorflow.keras.applications import NASNetMobile, NASNet, EfficientNetB0, MobileNetV3Small, ResNet50
from classification_models.tfkeras import Classifiers

def getEnsemble(model_list, input_shape):
    from tensorflow.keras.layers import Add
    from tensorflow.keras import Input

    x = Input(input_shape)
    outs = [ m(x) for m in model_list ]
    out = Add()(outs)
    return lambda **y: tf.keras.models.Model(inputs=[x], outputs=out)

def select_model(model_name: str):
    models = {'NASNetMobile': (NASNetMobile, (224, 224, 3)),
              'EfficientNetB0': (EfficientNetB0, (224, 224, 3)),
              'MobileNet': (MobileNetV3Small, (224, 224, 3)),
              'ResNet50': (ResNet50, (224, 224, 3)),
              'ResNeXt50': (Classifiers.get('resnext50')[0], (224, 224, 3)),
              'InceptionV3': (Classifiers.get('inceptionv3')[0], (299, 299, 3)),
              'NASNetLarge': (Classifiers.get('nasnetlarge')[0], (331, 331, 3)),
              'InceptionResnetV2': (Classifiers.get('inceptionresnetv2')[0], (299, 299, 3)),
              'ResNeXt101': (Classifiers.get('resnext101')[0], (224, 224, 3))}

    if 'Ensemble[' in model_name:
      names = model_name.lstrip('Ensemble[').rstrip(']').split(',')
      input_shape = None
      model_list = []
      prev_name = None
      for i, name in enumerate(names):
        name = name.replace(' ', '')
        model, shape = models[name]
        assert not input_shape or input_shape == shape
        input_shape = shape
        if prev_name == name:
          model_list.append(model_list[-1])
        else:
          model_list.append(model(include_top=True, input_shape=input_shape, weights='imagenet'))
        prev_name = name
      model = getEnsemble(model_list, input_shape)
    else:
      model, input_shape = models[model_name]
    return model(include_top=True, input_shape=input_shape, weights='imagenet'), input_shape
