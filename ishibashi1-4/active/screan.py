# -*- coding: utf-8 -*-
import streamlit as st
from PIL import Image
import io
import os
import hashlib
import stats_db
stats_db.init_db()

username = "test_user"   # 今は仮（後でGoogleログイン）

CENSOR_IMAGE_PATH = "kyushi.jpg" # 放送休止画像
MAINTENANCE_IMAGE_PATH = "maintenance.jpg" # エラー（電波障害）用画像（任意）

LOCAL_HARMFUL_LABELS = [
    "harassment",
    "hate",
    "insult",
    "abuse",
    "offensive",
    "threat",
    "toxic",
    "bullying",
    "racist",
    "sexist",
    "offensive text",
    "insulting text",
    "harassing message",
    "hate speech",
    "slander",
    "defamation",
    "暴言",
    "侮辱",
    "誹謗中傷",
    "差別",
    "脅迫",
]
LOCAL_SAFE_LABELS = [
    "safe",
    "benign",
    "neutral",
    "non-offensive",
    "friendly",
    "positive message",
    "calm scene",
    "穏やか",
    "無害",
]
LOCAL_ALERT_THRESHOLD = 0.25


@st.cache_resource(show_spinner=False)

def _load_local_clip():
    try:
        import torch
        from transformers import CLIPModel, CLIPProcessor
    except Exception as e:  # pragma: no cover - runtime dependency check
        raise RuntimeError(
            "ローカル判定には 'torch' と 'transformers' が必要です。"
        ) from e

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
    processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    model.eval()
    return model, processor, device


def _local_classify(image_bytes: bytes, threshold: float) -> tuple[bool, float, str, float]:
    try:
        import torch
    except Exception as e:  # pragma: no cover
        raise RuntimeError(
            "ローカル判定には 'torch' と 'transformers' が必要です。"
        ) from e

    model, processor, device = _load_local_clip()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    labels = LOCAL_HARMFUL_LABELS + LOCAL_SAFE_LABELS
    inputs = processor(text=labels, images=image, return_tensors="pt", padding=True)
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)
        probs = outputs.logits_per_image.softmax(dim=1)[0].detach().cpu().tolist()

    harmful_probs = probs[: len(LOCAL_HARMFUL_LABELS)]
    safe_probs = probs[len(LOCAL_HARMFUL_LABELS):]
    max_harmful = max(harmful_probs)
    max_safe = max(safe_probs)
    best_label = labels[probs.index(max(probs))]

    is_toxic = (max_harmful >= threshold) or (best_label in LOCAL_HARMFUL_LABELS)
    return is_toxic, max_harmful, best_label, max_safe

def run():
    st.title("SNS誹謗中傷シールド（放送休止Ver.）")

    uploaded_file = st.file_uploader("画像をアップロード（検証用）", type=['jpg', 'jpeg', 'png'])
    strict_mode = st.checkbox("判定を厳しくする", value=True)
    threshold = st.slider("有害スコアしきい値", 0.05, 0.80, LOCAL_ALERT_THRESHOLD, 0.05)

    if uploaded_file is not None:
        # ファイル名に日本語が含まれても安全なように読み込む
        image_bytes = uploaded_file.read()
        image_hash = hashlib.sha256(image_bytes).hexdigest()
        force_recheck = st.checkbox("同じ画像でも再判定する", value=False)
        
        if st.button('解析を実行'):
            with st.spinner('放送倫理規定に基づき審査中...'):
                try:
                    effective_threshold = min(threshold, 0.25) if strict_mode else threshold
                    is_toxic, score, best_label, safe_score = _local_classify(image_bytes, effective_threshold)
                    response_text = (
                        f"LOCAL:{best_label} (harmful_score={score:.2f}, safe_score={safe_score:.2f}, "
                        f"threshold={effective_threshold:.2f})"
                    )

                    if is_toxic:
                        stats_db.increment_toxic(username)   # ←これ追加！
                        st.error("🚫 放送事故発生！不適切なコンテンツを検知しました。")
                        if os.path.exists(CENSOR_IMAGE_PATH):
                            st.image(CENSOR_IMAGE_PATH, caption="※放送倫理規定により映像を差し替えました。", use_container_width=True)
                        st.info(f"【判定理由】\n{response_text}")
                    else:
                        st.success(" 放送倫理上、問題ありません。")
                        st.image(image_bytes, caption="安全なコンテンツ", use_container_width=True)

                except RuntimeError as e:
                    st.error(str(e))

                st.divider()
                count = stats_db.get_count(username)
                st.metric("🚫 検知された誹謗中傷回数", count)