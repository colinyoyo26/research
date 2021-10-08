import os
import pip
import tarfile
import subprocess

script_path = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_path + '/..')
print('work in directory: ' + os.getcwd())

failed = pip.main(['install', '-r', 'requirements.txt'])

if failed:
    print('fail to install requirements.txt')
    exit(1)

if not os.path.exists('images'):
    os.mkdir('images')
os.chdir('images')

img_tar = 'ILSVRC2012_img_val.tar'
devkit_tar = 'ILSVRC2012_devkit_t12.tar.gz'
files = os.listdir('.')

if not img_tar in files:
    subprocess.run(['wget', 'https://image-net.org/data/ILSVRC/2012/ILSVRC2012_img_val.tar'])
    subprocess.run(['wget', 'https://image-net.org/data/ILSVRC/2012/ILSVRC2012_devkit_t12.tar.gz'])

if len(files) < 3:
    with tarfile.open(img_tar) as f:
        tars = f.getnames()
        f.extractall()

    with tarfile.open(devkit_tar) as f:
        f.extractall()
