from tensorflow.keras.applications import NASNetMobile, EfficientNetB0, MobileNetV3Small, ResNet50
from classification_models.tfkeras import Classifiers

def select_model(model_name: str):
    models = {'NASNetMobile': (Classifiers.get('nasnetmobile')[0], (224, 224, 3)),
              'EfficientNetB0': (EfficientNetB0, (224, 224, 3)),
              'MobileNet': (MobileNetV3Small, (224, 224, 3)),
              'ResNet50': (ResNet50, (224, 224, 3)),
              'ResNeXt50': (Classifiers.get('resnext50')[0], (224, 224, 3)),
              'InceptionV3': (Classifiers.get('inceptionv3')[0], (299, 299, 3)),
              'NASNetLarge': (Classifiers.get('nasnetlarge')[0], (331, 331, 3))}

    model, input_shape = models.get(model_name)
    assert(model)
    return model(include_top=True, input_shape=input_shape, weights='imagenet'), input_shape
