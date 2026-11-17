import json
import os
from pathlib import Path
import sys

import streamlit as st
from dotenv import load_dotenv
from openai import APIConnectionError, AuthenticationError, RateLimitError

# Resolve our package consistently for direct Streamlit and future root launches.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from learning_assistant.rag import build_index, build_rag_chain, rag_pipeline
from learning_assistant.uploads import document_signature, temporary_pdfs

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
                     "chunks": 0, "failed_signature": None,
                     "retriever": None, "chain": None,
                     "coach_chain": None, "quiz_chain": None,
                     "coach_result": None, "quiz": None,
                     "quiz_submission": None, "quiz_version": 0}.items():
    if key not in st.session_state:
        st.session_state[key] = default


def clear_index():
    old_store = st.session_state.store
    st.session_state.store = None
    st.session_state.retriever = None
    st.session_state.chain = None
    st.session_state.signature = None
    st.session_state.chunks = 0
    st.session_state.messages = []
    st.session_state.failed_signature = None
    st.session_state.coach_chain = None
    st.session_state.quiz_chain = None
    st.session_state.coach_result = None
    st.session_state.quiz = None
    st.session_state.quiz_submission = None
    st.session_state.quiz_version += 1
    if old_store is not None:
        old_store.delete_collection()


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
    level = st.selectbox("학습 수준", ["초급", "중급", "고급"], key="learning_level")
    st.divider()
    st.subheader("학습 자료")
    uploads = st.file_uploader("PDF 업로드", type=["pdf"], accept_multiple_files=True,
                               help="총 30MB까지 업로드할 수 있습니다. 문서를 바꾸면 대화가 초기화됩니다.")
    st.caption("PDF 내용은 답변 생성을 위해 OpenAI API로 전송됩니다. API 사용료가 발생할 수 있습니다.")
    has_key = bool(api_key)
    if not has_key:
        st.warning("환경변수, learning_assistant/.env 또는 Streamlit Secrets에 OPENAI_API_KEY를 설정해 주세요.")
    files = [(f.name, f.getvalue()) for f in uploads]
    signature = document_signature(files)
    if signature != st.session_state.signature:
        # Never answer using a previous document while new uploads are pending.
        if st.session_state.signature is not None:
            clear_index()
        if not files:
            st.session_state.failed_signature = None
        if files and has_key:
            retry = False
            if signature == st.session_state.failed_signature:
                retry = st.button("문서 처리 다시 시도", use_container_width=True)
            if signature != st.session_state.failed_signature or retry:
                try:
                    with st.spinner("PDF를 읽고 검색 인덱스를 만드는 중…"):
                        with temporary_pdfs(files) as pdf_paths:
                            store, chunks = build_index(pdf_paths, api_key=api_key)
                        try:
                            retriever, chain = build_rag_chain(store, api_key=api_key)
                        except Exception:
                            store.delete_collection()
                            raise
                    st.session_state.store = store
                    st.session_state.retriever = retriever
                    st.session_state.chain = chain
                    st.session_state.chunks = chunks
                    st.session_state.signature = signature
                    st.session_state.failed_signature = None
                except Exception as exc:
                    st.session_state.failed_signature = signature
                    show_error(exc)
    ready = (st.session_state.store is not None
             and st.session_state.chain is not None and has_key)
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

def render_chat():
    st.subheader("RAG 채팅")
    st.caption("업로드한 문서에서 근거를 찾아 질문에 답합니다.")
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
                    stream, sources = rag_pipeline(
                        st.session_state.retriever, st.session_state.chain,
                        question, st.session_state.messages,
                    )
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


def render_coach():
    st.subheader("AI 맞춤형 학습 코치")
    st.caption(f"현재 수준: {level} · 설명할 개념이나 어려운 부분을 입력해 주세요.")
    with st.form("coach_request"):
        topic = st.text_input("설명받고 싶은 개념", max_chars=2000,
                              placeholder="예: 이 문서의 핵심 개념을 단계별로 설명해 줘")
        explain = st.form_submit_button("수준에 맞게 설명받기", disabled=not ready)
    if explain and ready:
        if not topic.strip():
            st.warning("설명받고 싶은 개념을 입력해 주세요.")
        else:
            st.session_state.coach_result = None
            try:
                from learning_assistant.learning import build_coach_chain, coach_pipeline
                if st.session_state.coach_chain is None:
                    st.session_state.coach_chain = build_coach_chain(api_key=api_key)
                with st.spinner("학습 수준에 맞춰 문서를 풀어 설명하는 중…"):
                    stream, sources = coach_pipeline(
                        st.session_state.retriever, st.session_state.coach_chain,
                        topic.strip(), level,
                    )
                    response = "".join(stream)
                if not response.strip():
                    raise ValueError("설명을 생성하지 못했습니다. 다시 시도해 주세요.")
                st.session_state.coach_result = {
                    "topic": topic.strip(), "level": level,
                    "response": response, "sources": sources,
                }
            except Exception as exc:
                show_error(exc)
    result = st.session_state.coach_result
    if result:
        st.caption(f"생성된 설명 · {result['level']} · {result['topic']}")
        st.markdown(result["response"])
        show_sources(result["sources"])


def render_quiz():
    st.subheader("이해도 확인 문제")
    st.caption(f"현재 수준: {level} · 문서 기반 4지선다 문제를 한 문제씩 풀어 보세요.")
    with st.form("quiz_request"):
        topic = st.text_input("출제 주제 (선택)", max_chars=2000,
                              placeholder="비워 두면 문서의 핵심 개념으로 출제합니다")
        create = st.form_submit_button("새 문제 만들기", disabled=not ready)
    if create and ready:
        st.session_state.quiz = None
        st.session_state.quiz_submission = None
        st.session_state.quiz_version += 1
        try:
            from learning_assistant.learning import build_quiz_chain, generate_quiz
            if st.session_state.quiz_chain is None:
                st.session_state.quiz_chain = build_quiz_chain(api_key=api_key)
            with st.spinner("문서 근거를 확인하며 문제를 만드는 중…"):
                quiz = generate_quiz(
                    st.session_state.retriever, st.session_state.quiz_chain,
                    topic.strip() or "업로드 문서의 핵심 개념과 정의",
                    level, st.session_state.quiz_version,
                )
            quiz["level"] = level
            st.session_state.quiz = quiz
        except Exception as exc:
            show_error(exc)
    quiz = st.session_state.quiz
    if not quiz:
        st.info("PDF를 준비한 뒤 새 문제 만들기를 눌러 주세요. 답을 제출하면 해설과 근거를 볼 수 있습니다.")
        return
    st.caption(f"출제 수준: {quiz['level']}")
    st.markdown(quiz["question"])
    submitted = st.session_state.quiz_submission
    with st.form(f"quiz_answer_form_{st.session_state.quiz_version}"):
        choice = st.radio(
            "정답을 선택해 주세요", options=list(range(4)), index=submitted,
            format_func=lambda i: f"{i + 1}. {quiz['options'][i]}",
            key=f"quiz_answer_{st.session_state.quiz_version}",
            disabled=submitted is not None,
        )
        grade = st.form_submit_button("답안 제출", disabled=not ready or submitted is not None)
    if grade and ready and submitted is None:
        if choice is None:
            st.warning("보기를 선택한 뒤 제출해 주세요.")
        else:
            st.session_state.quiz_submission = choice
            st.rerun()
    if submitted is not None:
        if submitted == quiz["correct_index"]:
            st.success("정답입니다!")
        else:
            st.error("아쉽지만 오답입니다. 문서 근거와 함께 다시 확인해 보세요.")
        answer = quiz["correct_index"]
        st.write(f"정답: {answer + 1}. {quiz['options'][answer]}")
        st.markdown(quiz["explanation"])
        show_sources(quiz["sources"])
        st.caption("AI가 생성한 문제입니다. 해설과 원문 근거를 함께 확인해 주세요.")


mode = st.radio("학습 메뉴", ["RAG 채팅", "AI 맞춤형 학습 코치", "이해도 확인 문제"],
                horizontal=True, key="learning_mode")
if mode == "RAG 채팅":
    render_chat()
elif mode == "AI 맞춤형 학습 코치":
    render_coach()
else:
    render_quiz()
