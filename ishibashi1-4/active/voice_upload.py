import os
import subprocess
import tempfile

import streamlit as st
import whisper
import stats_db
from pydub import AudioSegment

from voice import censor_audio, contains_hate_speech

VIDEO_EXTS = {"mp4", "mov", "avi", "mkv", "webm"}
AUDIO_EXTS = {"mp3", "wav", "m4a", "aac", "flac"}

stats_db.init_db()

username = "test_user"   # 今は仮（後でGoogleログイン）


@st.cache_resource(show_spinner=False)
def load_model():
    return whisper.load_model("base")


def extract_audio(video_path, wav_path):
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        video_path,
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-f",
        "wav",
        wav_path,
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def mux_audio(video_path, audio_path, output_path):
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        video_path,
        "-i",
        audio_path,
        "-c:v",
        "copy",
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-shortest",
        output_path,
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def transcribe_segments(audio_path):
    model = load_model()
    result = model.transcribe(audio_path, language="ja", fp16=False)
    return result.get("segments", [])


def process_audio(input_path, output_path, output_format):
    segments = transcribe_segments(input_path)
    hit_segments = [seg for seg in segments if contains_hate_speech(seg.get("text", ""))]

    audio = AudioSegment.from_file(input_path)
    censored = censor_audio(audio, hit_segments)
    censored.export(output_path, format=output_format)

    return hit_segments


def process_video(input_path, output_path):
    with tempfile.TemporaryDirectory() as tmp_dir:
        wav_in = os.path.join(tmp_dir, "input.wav")
        wav_out = os.path.join(tmp_dir, "censored.wav")

        extract_audio(input_path, wav_in)
        hit_segments = process_audio(wav_in, wav_out, "wav")
        mux_audio(input_path, wav_out, output_path)

    return hit_segments


def run():
    st.title("誹謗中傷検出 + ピー音化")
    st.caption("動画/音声をアップロードして、誹謗中傷区間をピー音に置換します。")
    st.info("動画処理には ffmpeg が必要です。")

    uploaded = st.file_uploader("動画または音声をアップロード", type=list(VIDEO_EXTS | AUDIO_EXTS))

    if uploaded is not None:
        ext = uploaded.name.split(".")[-1].lower()
        is_video = ext in VIDEO_EXTS

        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = os.path.join(tmp_dir, uploaded.name)
            with open(input_path, "wb") as f:
                f.write(uploaded.getbuffer())

            if is_video:
                output_path = os.path.join(tmp_dir, "output_beep.mp4")
                with st.spinner("処理中..."):
                    try:
                        hit_segments = process_video(input_path, output_path)
                    except FileNotFoundError:
                        st.error("ffmpeg が見つかりません。インストールしてください。")
                        st.stop()
                    except subprocess.CalledProcessError:
                        st.error("ffmpeg の処理に失敗しました。")
                        st.stop()

                st.success("完了しました")
                st.video(output_path)
                with open(output_path, "rb") as f:
                    st.download_button("動画をダウンロード", f, file_name="output_beep.mp4")
            else:
                output_path = os.path.join(tmp_dir, "output_beep.mp3")
                with st.spinner("処理中..."):
                    hit_segments = process_audio(input_path, output_path, "mp3")

                st.success("完了しました")
                st.audio(output_path)
                with open(output_path, "rb") as f:
                    st.download_button("音声をダウンロード", f, file_name="output_beep.mp3")

            if hit_segments:
                st.subheader("検出内容(先頭10件)")
                for seg in hit_segments[:10]:
                    start = seg.get("start", 0)
                    end = seg.get("end", 0)
                    text = seg.get("text", "").strip()
                    st.write(f"{start:.2f}s - {end:.2f}s: {text}")
            else:
                st.subheader("検出結果")
                st.write("誹謗中傷ワードは検出されませんでした。")