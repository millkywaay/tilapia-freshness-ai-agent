# NilaFresh - Tilapia Freshness Detection AI 🐟

**NilaFresh** adalah aplikasi berbasis AI (Artificial Intelligence) yang dirancang untuk mendeteksi tingkat kesegaran ikan Nila (Tilapia) berdasarkan analisis citra mata dan insang. Proyek ini dikembangkan sebagai bagian dari Skripsi dan terdiri dari **Frontend** berbasis React/Vite serta **Backend** berbasis FastAPI yang menggunakan model Deep Learning.

---

## 🌟 Fitur Utama

- **Dual-Image Analysis**: Mendeteksi kesegaran ikan dengan menganalisis dua bagian krusial sekaligus (mata dan insang) untuk akurasi yang lebih tinggi.
- **Deep Learning Model**: Menggunakan arsitektur Convolutional Neural Network (CNN) berbasis ResNet50 dan custom model.
- **Ensemble Prediction**: Menggabungkan probabilitas dari berbagai model untuk menentukan kesimpulan (Segar / Tidak Segar).
- **Interactive UI**: Antarmuka pengguna yang modern, responsif, dan rapi dibangun dengan React, Tailwind CSS, dan animasi dari Framer Motion.
- **AI-Powered Insights**: Dilengkapi integrasi OpenAI untuk memberikan penjelasan atau rekomendasi terkait hasil deteksi (jika diaktifkan).

---

## 🛠️ Teknologi yang Digunakan

### Frontend
- **Framework**: React 19 dengan Vite
- **Styling**: Tailwind CSS v4
- **Animation**: Framer Motion
- **HTTP Client**: Axios
- **Routing**: React Router DOM

### Backend
- **Framework**: FastAPI & Uvicorn
- **Machine Learning**: TensorFlow / Keras (ResNet50)
- **Image Processing**: Pillow (PIL), NumPy
- **Environment**: Python-dotenv
- **AI Integration**: OpenAI API

---

## 📂 Struktur Direktori

```
skripsi-deploy/
│
├── backend/                  # Folder backend (FastAPI)
│   ├── model/                # Berisi file model berformat .keras (.h5)
│   ├── app.py                # File utama API (FastAPI)
│   ├── requirements.txt      # Dependensi Python
│   └── Dockerfile            # (Opsional) Konfigurasi Docker
│
├── frontend/                 # Folder frontend (React + Vite)
│   ├── src/                  # Source code React (components, pages, utils)
│   ├── public/               # Static assets
│   ├── package.json          # Dependensi Node.js
│   ├── vite.config.js        # Konfigurasi Vite
│   └── tailwind.config.js    # Konfigurasi Tailwind (jika ada)
│
└── README.md                 # Dokumentasi Proyek
```

---

## 🚀 Cara Menjalankan Proyek di Lingkungan Lokal (Development)

### 1. Persiapan Backend (API & Model AI)

Pastikan Python (3.9+) sudah terinstall di sistem Anda.

1. Buka terminal dan arahkan ke folder `backend`:
   ```bash
   cd backend
   ```
2. Buat Virtual Environment (opsional namun sangat disarankan):
   ```bash
   python -m venv venv
   # Di Windows:
   venv\Scripts\activate
   # Di macOS/Linux:
   source venv/bin/activate
   ```
3. Install semua dependensi yang dibutuhkan:
   ```bash
   pip install -r requirements.txt
   ```
4. Buat file `.env` di dalam folder `backend` dan sesuaikan dengan kebutuhan Anda (misal: API Keys atau konfigurasi model):
   ```env
   # Contoh isi .env
   EYES_BEST_WEIGHT=1.0
   EYES_RESNET_WEIGHT=1.0
   GILLS_BEST_WEIGHT=1.0
   GILLS_RESNET_WEIGHT=1.0
   OPENAI_API_KEY=your_openai_api_key_here
   ```
5. Jalankan server FastAPI:
   ```bash
   uvicorn app:app --reload
   ```
   Backend akan berjalan di `http://127.0.0.1:8000`. Dokumentasi API (Swagger) dapat diakses di `http://127.0.0.1:8000/docs`.

### 2. Persiapan Frontend (Web Interface)

Pastikan Node.js (versi 18+) sudah terinstall di sistem Anda.

1. Buka terminal baru dan arahkan ke folder `frontend`:
   ```bash
   cd frontend
   ```
2. Install dependensi Node.js:
   ```bash
   npm install
   ```
3. Tambahkan file `.env` di folder `frontend` untuk mengarahkan ke API lokal (atau biarkan default yang mengarah ke Production API):
   ```env
   VITE_API_URL=http://127.0.0.1:8000
   ```
4. Jalankan server development:
   ```bash
   npm run dev
   ```
   Frontend akan berjalan di `http://localhost:5173`.

---

## 🌐 Deployment

Proyek ini telah dikonfigurasi agar siap untuk dideploy:
- **Backend** dapat di-deploy ke platform seperti Render, Heroku, Railway, atau VPS (menggunakan Docker/Gunicorn).
- **Frontend** dapat di-deploy ke Vercel, Netlify, atau Firebase Hosting.

---


**© 2026 NilaFresh - AI-powered Tilapia Freshness Detector**
