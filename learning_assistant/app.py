import hashlib
import json
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from openai import APIConnectionError, AuthenticationError, RateLimitError

from rag import build_index, rag_pipeline

load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")
st.set_page_config(page_title="AIVLE School 학습 도우미", page_icon="📘", layout="wide")


def get_api_key():
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if key:
        return key
    try:
        return str(st.secrets.get("OPENAI_API_KEY", "")).strip()
    except FileNotFoundError:
        return ""


api_key = get_api_key()
st.markdown("""<style>
.stApp {background: #f7f9fc;}
[data-testid="stSidebar"] {background: #edf2fa;}
.block-container {max-width: 1100px; padding-top: 2.5rem;}
[data-testid="stChatMessage"] {background: white; border: 1px solid #e4eaf3; border-radius: 16px;}
h1, h2, h3 {color: #15345c;}
.hero {color: #52729a; letter-spacing: .18em; font-size: .8rem; font-weight: 700;}
</style>""", unsafe_allow_html=True)

for key, default in {"messages": [], "store": None, "signature": None,
                     "chunks": 0, "failed_signature": None}.items():
    if key not in st.session_state:
        st.session_state[key] = default


def clear_index():
    if st.session_state.store is not None:
        st.session_state.store.delete_collection()
    st.session_state.store = None
    st.session_state.signature = None
    st.session_state.chunks = 0


def show_sources(sources):
    if sources:
        with st.expander("📎 답변에 사용한 문서 근거"):
            for i, source in enumerate(sources, 1):
                st.text(f"[{i}] {source['label']}")
                st.text(source["text"])


def show_error(exc):
    if isinstance(exc, AuthenticationError):
        st.error("OpenAI 인증에 실패했습니다. 환경변수 OPENAI_API_KEY를 확인해 주세요.")
    elif isinstance(exc, RateLimitError):
        st.error("API 사용 한도 또는 요청 제한에 도달했습니다. 계정 한도를 확인한 뒤 다시 시도해 주세요.")
    elif isinstance(exc, APIConnectionError):
        st.error("OpenAI에 연결하지 못했습니다. 네트워크를 확인한 뒤 다시 시도해 주세요.")
    elif isinstance(exc, ValueError):
        st.error(str(exc))
    else:
        st.error("처리를 완료하지 못했습니다. PDF의 손상·암호화 여부와 실행 환경을 확인해 주세요.")


with st.sidebar:
    st.header("📘 AIVLE School")
    st.caption("문서와 함께하는 나만의 학습 도우미")
    st.divider()
    st.subheader("학습 자료")
    uploads = st.file_uploader("PDF 업로드", type=["pdf"], accept_multiple_files=True,
                               help="총 30MB까지 업로드할 수 있습니다. 문서를 바꾸면 대화가 초기화됩니다.")
    st.caption("PDF 내용은 답변 생성을 위해 OpenAI API로 전송됩니다. API 사용료가 발생할 수 있습니다.")
    has_key = bool(api_key)
    if not has_key:
        st.warning("환경변수, learning_assistant/.env 또는 Streamlit Secrets에 OPENAI_API_KEY를 설정해 주세요.")
    files = [(f.name, f.getvalue()) for f in uploads]
    signature = hashlib.sha256(b"".join(
        name.encode() + hashlib.sha256(data).digest() for name, data in files
    )).hexdigest() if files else None
    if signature != st.session_state.signature:
        # Never answer using a previous document while new uploads are pending.
        if st.session_state.store is not None:
            clear_index()
            st.session_state.messages = []
        if files and has_key:
            retry = False
            if signature == st.session_state.failed_signature:
                retry = st.button("문서 처리 다시 시도", use_container_width=True)
            if signature != st.session_state.failed_signature or retry:
                try:
                    if sum(len(data) for _, data in files) > 30 * 1024 * 1024:
                        raise ValueError("PDF 합계가 30MB를 넘습니다. 파일 수나 크기를 줄여 주세요.")
                    with st.spinner("PDF를 읽고 검색 인덱스를 만드는 중…"):
                        store, chunks = build_index(files, api_key=api_key)
                    st.session_state.store = store
                    st.session_state.chunks = chunks
                    st.session_state.signature = signature
                    st.session_state.failed_signature = None
                except Exception as exc:
                    st.session_state.failed_signature = signature
                    show_error(exc)
    ready = st.session_state.store is not None and has_key
    if ready:
        st.success(f"검색 준비 완료 · {len(files)}개 문서")
        st.caption(f"텍스트 조각 {st.session_state.chunks:,}개 · 동일 문서는 재처리하지 않습니다.")
    st.divider()
    st.subheader("대화 기록")
    st.caption(f"현재 대화 {len(st.session_state.messages) // 2}건")
    with st.expander("기록 확인"):
        if not st.session_state.messages:
            st.caption("아직 대화가 없습니다.")
        for message in st.session_state.messages:
            st.text(("나: " if message["role"] == "user" else "도우미: ") + message["content"])
    st.download_button("대화 기록 저장", json.dumps(st.session_state.messages, ensure_ascii=False, indent=2),
                       file_name="aivle_chat.json", mime="application/json",
                       disabled=not st.session_state.messages, use_container_width=True)
    if st.button("🗑 대화 기록 삭제", use_container_width=True,
                 disabled=not st.session_state.messages):
        st.session_state.messages = []
        st.rerun()
    st.caption("문서와 대화는 현재 세션에서 사용됩니다. 새로고침하면 초기화될 수 있습니다.")

st.markdown('<div class="hero">AIVLE SCHOOL · LEARNING ASSISTANT</div>', unsafe_allow_html=True)
st.title("배움의 다음 단계, 함께 찾아요")
st.write("학습 자료를 업로드하고 궁금한 내용을 물어보세요. 문서 속 근거와 함께 답해 드립니다.")
if not ready:
    st.info("시작하려면 왼쪽에서 PDF를 업로드하세요. API 키 설정도 필요합니다.")
st.subheader("자주 묻는 질문")
questions = ["AIVLE School의 교육 과정을 알려줘.", "지원 자격과 선발 절차는 어떻게 되나요?",
             "학습 지원과 취업 지원 내용을 정리해 줘."]
selected = None
for column, question in zip(st.columns(3), questions):
    if column.button(question, disabled=not ready, use_container_width=True):
        selected = question
st.divider()
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        show_sources(message.get("sources", []))

typed = st.chat_input("업로드한 문서에 대해 질문해 주세요", disabled=not ready, max_chars=4000)
question = typed or selected
if question and ready:
    st.chat_message("user").write(question)
    with st.chat_message("assistant"):
        try:
            with st.spinner("문서에서 근거를 찾고 있어요…"):
                stream, sources = rag_pipeline(st.session_state.store, question, st.session_state.messages, api_key=api_key)
            response = st.write_stream(stream)
            if not response:
                raise ValueError("답변을 받지 못했습니다. 다시 시도해 주세요.")
            st.session_state.messages.extend([
                {"role": "user", "content": question},
                {"role": "assistant", "content": response, "sources": sources},
            ])
            st.rerun()
        except Exception as exc:
            show_error(exc)
