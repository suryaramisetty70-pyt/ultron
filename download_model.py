import urllib.request
import zipfile
import os
import shutil

model_url = 'https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip'
zip_path = 'vosk_model.zip'
extract_dir = 'model'

if os.path.exists(extract_dir):
    print("Model already exists.")
else:
    print('Downloading Vosk model...')
    urllib.request.urlretrieve(model_url, zip_path)
    
    print('Extracting...')
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall('.')
        
    os.rename('vosk-model-small-en-us-0.15', extract_dir)
    os.remove(zip_path)
    print('Vosk model ready in "model" directory.')
