from tensorflow.keras.applications import NASNetMobile, EfficientNetB0, MobileNet, ResNet50

def select_model(model_name: str):
    models = {'NASNetMobile': NASNetMobile,
              'EfficientNetB0': EfficientNetB0,
              'MobileNet': MobileNet,
              'ResNet50': ResNet50}

    model = models.get(model_name)
    assert(model)
    return model()
