import re
from pydub import AudioSegment
from pydub.generators import Sine

BEEP_FREQ = 1000
BEEP_DB = -6

# voice.py の修正案
NEGATIVE_HINTS = [
    "バカ", "ばか", "馬鹿",
    "無能",
    "死ね", "しね", "シネ", # 表記ゆれを追加
    "消えろ", "きえろ",
    "クズ", "くず",
    "きも", "キモ",
    "頭おかしい",
    "最悪", "嫌い", "ムカつく",
]

def normalize(text):
    text = text.lower()
    text = re.sub(r"\s+", "", text)
    return text


def feels_hate_speech(text, threshold=1):
    text = normalize(text)

    score = 0
    for w in NEGATIVE_HINTS:
        if w in text:
            score += 1

    if "!" in text or "？" in text:
        score += 1

    return score >= threshold


def contains_hate_speech(text):
    return feels_hate_speech(text)


def censor_audio(audio: AudioSegment, segments):
    """
    検知されたセグメント（区間）だけをピー音に置換する
    """
    # 元の音声をコピー（加工用）
    processed_audio = audio

    for seg in segments:
        # ミリ秒単位に変換
        start_ms = int(seg.get("start", 0) * 1000)
        end_ms = int(seg.get("end", 0) * 1000)
        duration_ms = end_ms - start_ms

        if duration_ms <= 0:
            continue

        # その区間用のピー音を生成
        beep = (
            Sine(BEEP_FREQ)
            .to_audio_segment(duration=duration_ms)
            .apply_gain(BEEP_DB)
        )

        # 指定区間をピー音で上書き（overlay または切って繋げる）
        # overlayだと元の声が後ろで聞こえる場合があるので、完全に置き換えます
        before = processed_audio[:start_ms]
        after = processed_audio[end_ms:]
        processed_audio = before + beep + after

    return processed_audio