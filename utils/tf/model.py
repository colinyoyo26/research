from tensorflow.keras.applications import NASNetMobile, EfficientNetB0, MobileNetV3Small, ResNet50
from classification_models.tfkeras import Classifiers

def select_model(model_name: str):
    models = {'NASNetMobile': NASNetMobile,
              'EfficientNetB0': EfficientNetB0,
              'MobileNet': MobileNetV3Small,
              'ResNet50': ResNet50,
              'ResNeXt50': Classifiers.get('resnext50')[0]}

    model = models.get(model_name)
    assert(model)
    return model(include_top=True, input_shape=(224, 224, 3), weights='imagenet')
