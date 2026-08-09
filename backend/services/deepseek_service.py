import os
from openai import OpenAI

DEEPSEEK_API_KEY = os.getenv(
    "DEEPSEEK_API_KEY"
)

deepseek_client = (
    OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com",
    )
    if DEEPSEEK_API_KEY
    else None
)

def get_deepseek_explanation(
    label: str,
    confidence_percent: float,
    eye_label: str,
    eye_confidence_percent: float,
    gill_label: str,
    gill_confidence_percent: float,
    decision_reason: str,
) -> str:

    if deepseek_client is None:

        raise RuntimeError(
            "DEEPSEEK_API_KEY "
            "belum dikonfigurasi."
        )

    fusion_note = ""

    if decision_reason == "strong_nonfresh_veto":
        fusion_note = """
- Hasil kedua organ berbeda.
- Salah satu organ menunjukkan kondisi tidak segar dengan keyakinan sangat tinggi.
- Sistem menggunakan kebijakan konservatif dan menetapkan status akhir tidak segar.
"""
    elif decision_reason == "organ_disagreement":
        fusion_note = """
- Hasil mata dan insang berbeda.
- Indikasi ketidaksegaran belum melewati batas keyakinan sistem.
- Status akhir memerlukan pemeriksaan lanjutan.
"""

    score_info = f"""
- Prediksi mata: {eye_label}
- Keyakinan mata: {eye_confidence_percent:.1f}%
- Prediksi insang: {gill_label}
- Keyakinan insang: {gill_confidence_percent:.1f}%
- Status akhir: {label}
- Keyakinan akhir: {confidence_percent:.1f}%
- Dasar keputusan: {decision_reason}
{fusion_note}
"""

    prompt = f"""
Kamu adalah Ahli Pengendalian Mutu (Quality Control) Perikanan yang sangat berpengalaman.
Tugasmu adalah mengubah data mentah prediksi kesegaran ikan nila menjadi laporan analisis yang profesional, analitis, dan natural.

Data hasil:
{score_info}

Aturan Format & Gaya Bahasa (Wajib Dipatuhi):
1. DILARANG KERAS menggunakan tanda titik dua (:) pada kalimat penjelasan. Ganti dengan kata hubung (yakni, adalah, sebesar, menunjukkan, dll).
2. Gunakan format poin (bullet •) untuk setiap baris di bawah judul bagian.
3. Parafrase data menjadi kalimat evaluasi ahli yang mengalir dan tidak kaku layaknya robot.
4. Maksimal 25 kata per poin agar tetap padat dan jelas.
5. Jangan mengarang ciri fisik yang tidak ada di data.
6. Jangan menyebut istilah teknis AI (CNN, ResNet, dataset, neural network).

Struktur Output yang Wajib Digunakan:

**Analisis Organ**
• [Penjelasan evaluasi mata berdasarkan label dan keyakinannya]
• [Penjelasan evaluasi insang berdasarkan label dan keyakinannya]
• [Kesimpulan perbandingan atau konsistensi kedua organ]

**Kesimpulan Akhir**
• [Pernyataan status akhir ikan secara meyakinkan]
• [Penjelasan dasar keputusan sistem mengambil status tersebut]

**Rekomendasi Penanganan**
• [Tindakan utama yang harus dilakukan sesuai status ikan]
• [Panduan suhu atau tempat penyimpanan]
• [Saran untuk tetap melakukan verifikasi fisik secara manual]
"""

    response = (
        deepseek_client
        .chat
        .completions
        .create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            temperature=0.25,
            max_tokens=480,
        )
    )

    return (
        response
        .choices[0]
        .message
        .content
        .strip()
    )

def get_confidence_level(
    confidence: float,
) -> str:

    if confidence >= 0.90:
        return "Sangat Tinggi"

    if confidence >= 0.80:
        return "Tinggi"

    if confidence >= 0.70:
        return "Sedang"

    return "Rendah"
