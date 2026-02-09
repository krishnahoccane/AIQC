FROM python:3.10

RUN apt-get update && apt-get install -y \
    ffmpeg \
    build-essential \
    git \
    libfftw3-dev \
    libavcodec-dev \
    libavformat-dev \
    libavutil-dev \
    libsamplerate0-dev \
    libtag1-dev \
    libyaml-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

RUN pip install essentia
RUN pip install spleeter

WORKDIR /app

COPY mir_processor.py .

ENTRYPOINT ["python", "mir_processor.py"]
