import streamlit as st
import pandas as pd
import time
from io import BytesIO

st.set_page_config(page_title="피드백 분류", layout="centered")
st.title("고객 피드백 분류 리포터")

with st.popover("도움말"):
    st.markdown("- CSV는 최소 `text` 컬럼을 포함\n- 예시 문장: '배송이 너무 느려요'")

with st.expander("파라미터 설명"):
    st.code("""# 간단 규칙 예:
if '느려' in text or '지연' in text: label = '불만'
elif '좋' in text or '감사' in text: label = '칭찬'
else: label = '요청/기타'""", language="python")

with st.form("cfg"):
    model = st.radio("분류 방식", ["규칙기반", "키워드+가중치"], horizontal=True)
    do_lower = st.checkbox("소문자 변환", value=True)
    keep_neutral = st.checkbox("중립/기타 유지", value=True)
    submitted = st.form_submit_button("분석 실행")

uploaded = st.file_uploader("CSV 업로드", type=["csv"])

result_df = None
placeholder = st.empty()

def rule_based_label(t: str) -> str:
    txt = t.lower()
    if ("느려" in txt) or ("지연" in txt) or ("불만" in txt):
        return "불만"
    if ("좋" in txt) or ("만족" in txt) or ("감사" in txt):
        return "칭찬"
    return "요청/기타"

if submitted:
    if uploaded is None:
        st.warning("CSV 파일을 업로드해줘.")
    else:
        df = pd.read_csv(uploaded)
        if "text" not in df.columns:
            st.error("CSV에 'text' 컬럼이 필요해.")
        else:
            bar = st.progress(0, text="분석 중...")
            texts = df["text"].astype(str)
            if do_lower:
                texts = texts.str.lower()
            labels = []
            for i, t in enumerate(texts):
                labels.append(rule_based_label(t))
                if i % max(1, len(texts)//100) == 0:
                    bar.progress(min(100, int((i+1)/len(texts)*100)), text="분석 중...")
            bar.empty()
            df["label"] = labels
            if not keep_neutral:
                df = df[df["label"] != "요청/기타"]
            result_df = df

if result_df is not None:
    tab_raw, tab_report = st.tabs(["Raw 데이터", "리포트"])
    with tab_raw:
        st.dataframe(result_df, use_container_width=True)
        # 다운로드
        csv_bytes = result_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button("CSV 다운로드", data=csv_bytes, file_name="feedback_labeled.csv", mime="text/csv")
    with tab_report:
        agg = result_df["label"].value_counts().rename_axis("label").reset_index(name="count")
        st.dataframe(agg)
        st.markdown("**라벨별 예시 샘플**")
        for lbl in ["불만","칭찬","요청/기타"]:
            subset = result_df[result_df["label"]==lbl].head(3)["text"].tolist()
            st.markdown(f"- **{lbl}**: " + (" / ".join(subset) if subset else "샘플 없음"))
