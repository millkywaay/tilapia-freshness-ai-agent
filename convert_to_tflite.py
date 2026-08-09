import os
import gdown
import tensorflow as tf

print("Mendownload model dari Google Drive...")
folder_url = "https://drive.google.com/drive/folders/1sJ1Jyvtg0HvHepFNYZTfVW32HuyTjVH3?usp=sharing"
gdown.download_folder(folder_url, output="backend/model", quiet=False, use_cookies=False)

def convert_to_tflite(keras_path, tflite_path):
    print(f"Membaca {keras_path} ...")
    model = tf.keras.models.load_model(keras_path, compile=False)
    
    print(f"Mengonversi ke TFLite...")
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    
    # Optimasi Float16 (Akurasi tetap, ukuran separuhnya)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.target_spec.supported_types = [tf.float16]
    
    tflite_model = converter.convert()
    
    with open(tflite_path, "wb") as f:
        f.write(tflite_model)
    print(f"Berhasil disimpan: {tflite_path}")

eyes_keras = "backend/model/best_model_eyes.keras"
gills_keras = "backend/model/best_model_gills.keras"

eyes_tflite = "backend/model/best_model_eyes.tflite"
gills_tflite = "backend/model/best_model_gills.tflite"

convert_to_tflite(eyes_keras, eyes_tflite)
convert_to_tflite(gills_keras, gills_tflite)

print("Konversi selesai!")
