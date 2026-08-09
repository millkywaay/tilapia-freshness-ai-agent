FROM python:3.9

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY . .

# Download folder model dari Google Drive
RUN gdown --folder https://drive.google.com/drive/folders/1sJ1Jyvtg0HvHepFNYZTfVW32HuyTjVH3 -O /code/model || echo "Download selesai (mengabaikan warning)"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]