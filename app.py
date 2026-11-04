"""예시 업무 대시보드와 OpenAI 음성 비서."""
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="에이블 | AI 개인비서", page_icon="✦", layout="wide")
st.markdown(f"<style>{Path(__file__).with_name('style.css').read_text()}</style>", unsafe_allow_html=True)
MENUS = ["대시보드", "나의 업무", "일정 관리", "음성 비서", "회의록", "설정"]
TASKS = [
    {"업무": "신규 서비스 기획안 작성", "프로젝트": "서비스 기획", "상태": "진행 중", "마감": "오늘 18:00", "긴급": True},
    {"업무": "주간 성과 보고서 제출", "프로젝트": "운영 관리", "상태": "진행 중", "마감": "내일 12:00", "긴급": True},
    {"업무": "대시보드 디자인 검토", "프로젝트": "디자인", "상태": "진행 중", "마감": "이번 주 금요일", "긴급": False},
    {"업무": "팀 회의 자료 정리", "프로젝트": "운영 관리", "상태": "완료", "마감": "오늘 09:00", "긴급": False},
    {"업무": "고객 피드백 분류", "프로젝트": "서비스 기획", "상태": "완료", "마감": "오늘 10:00", "긴급": False},
    {"업무": "개발팀 요구사항 전달", "프로젝트": "개발 협업", "상태": "완료", "마감": "오늘 11:00", "긴급": False},
]
SCHEDULE = [("09:30", "팀 데일리 미팅", "회의실 A · 30분", "완료"), ("14:00", "신규 서비스 기획 회의", "회의실 B · 1시간", "예정"), ("16:30", "디자인 리뷰", "온라인 · 30분", "예정")]
SYSTEM_ROLE = "당신은 다양한 업무를 처리하는 AI 서비스입니다. 개인 비서처럼 친절하게 응대합니다."


def navigate(menu):
    st.session_state.menu = menu


def api_key():
    """키는 읽기만 하며 UI, 로그, 세션 상태에 노출하지 않는다."""
    if os.environ.get("OPENAI_API_KEY"):
        return os.environ["OPENAI_API_KEY"]
    try:
        return st.secrets.get("OPENAI_API_KEY")
    except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        return None


def schedule():
    for time, title, detail, status in SCHEDULE:
        st.markdown(f'<div class="schedule-row"><span class="time">{time}</span><div><strong>{title}</strong><p>{detail}</p></div><span class="badge">{status}</span></div>', unsafe_allow_html=True)


def task_rows(tasks):
    # HTML에는 개발자가 정의한 예시 데이터만 사용한다.
    for task in tasks:
        badge = "badge urgent" if task["긴급"] else "badge"
        st.markdown(f'<div class="task-row"><div><strong>{task["업무"]}</strong><p>{task["프로젝트"]}</p></div><span class="{badge}">{task["마감"]}</span></div>', unsafe_allow_html=True)


def dashboard():
    st.caption("WORKSPACE OVERVIEW")
    st.title("좋은 하루예요, 에이블님 👋")
    st.write("오늘의 업무를 한눈에 확인하고, 중요한 일에 집중해 보세요.")
    st.caption("예시 데이터 · 실제 업무 및 일정과 연동되지 않은 데모 화면입니다.")
    counts = [len(TASKS), sum(t["상태"] == "완료" for t in TASKS), sum(t["상태"] == "진행 중" for t in TASKS), sum(t["긴급"] for t in TASKS)]
    for col, title, value, detail, icon in zip(st.columns(4), ["전체 업무", "완료 업무", "진행 중", "마감 임박"], counts, ["등록된 모든 업무", "차근차근 잘하고 있어요", "집중하고 있는 업무", "우선 확인이 필요해요"], ["▦", "✓", "◷", "!"]):
        with col:
            st.markdown(f'<div class="stat-card"><span class="stat-icon">{icon}</span><p>{title}</p><div class="stat-value">{value}<small>건</small></div><span class="muted">{detail}</span></div>', unsafe_allow_html=True)
    left, right = st.columns([1.15, 1], gap="large")
    with left:
        with st.container(border=True, key="today_panel"):
            st.subheader("오늘의 일정")
            st.caption("오늘도 여유 있게, 하나씩 준비해요.")
            schedule()
            st.button("전체 일정 보기 →", on_click=navigate, args=("일정 관리",), width="stretch")
    with right:
        with st.container(border=True, key="urgent_panel"):
            st.subheader("마감 임박 업무")
            st.caption("놓치지 않도록 에이블이 챙겨드려요.")
            task_rows([t for t in TASKS if t["긴급"]])
            st.button("전체 업무 보기 →", on_click=navigate, args=("나의 업무",), width="stretch")
    left, right = st.columns([1.15, 1], gap="large")
    with left:
        st.markdown('<div class="briefing"><span class="eyebrow">✦ ABLE BRIEFING</span><h3>오늘의 AI 업무 브리핑</h3><p>오늘은 일정 3건과 마감 임박 업무 2건이 있어요.<br>오후 기획 회의 전, 기획안의 주요 내용을 정리해 보세요.</p><small>예시 브리핑 · AI가 생성한 실시간 분석이 아닙니다.</small></div>', unsafe_allow_html=True)
    with right:
        with st.container(border=True, key="quick_panel"):
            st.subheader("빠른 실행")
            a, b = st.columns(2)
            a.button("🎙️ 음성 비서", on_click=navigate, args=("음성 비서",), width="stretch")
            b.button("📄 회의록 업로드", on_click=navigate, args=("회의록",), width="stretch")
            a.button("＋ 업무 추가", on_click=navigate, args=("나의 업무",), width="stretch")
            b.button("📅 일정 확인", on_click=navigate, args=("일정 관리",), width="stretch")


def voice_assistant():
    st.title("음성 비서")
    st.write("목소리로 질문하면 에이블이 듣고, 답하고, 읽어드려요.")
    key = api_key()
    if not key:
        st.info("음성 비서를 사용하려면 환경변수 또는 Streamlit Secrets에 OPENAI_API_KEY를 설정해 주세요. 대시보드는 키 없이 이용할 수 있습니다.")
    with st.form("task_form"):
        uploaded_file = st.file_uploader("참고할 텍스트 파일", type=["txt"])
        audio_value = st.audio_input("무엇을 도와드릴까요?")
        submitted = st.form_submit_button("실행", type="primary", disabled=not bool(key))
    if submitted and key:
        if audio_value is None:
            st.warning("음성을 녹음해 주세요.")
        else:
            try:
                text = uploaded_file.getvalue().decode("utf-8-sig") if uploaded_file else ""
            except UnicodeDecodeError:
                st.error("UTF-8로 저장한 텍스트 파일을 업로드해 주세요.")
                return
            try:
                # 생성도 호출도 명시적인 폼 제출 이후에만 수행한다.
                with OpenAI(api_key=key) as client:
                    with st.spinner("음성을 듣고 답변을 준비하고 있어요..."):
                        transcript = client.audio.transcriptions.create(model="whisper-1", file=("audio.wav", audio_value.getvalue(), "audio/wav"))
                        system = SYSTEM_ROLE + (f"\n\n다음 내용을 참고하세요:\n{text}" if text else "")
                        pending = [*st.session_state.messages, {"role": "user", "content": transcript.text}]
                        response = client.responses.create(model="gpt-4o-mini", input=[{"role": "system", "content": system}, *pending])
                        answer = response.output_text
                        st.session_state.messages = [*pending, {"role": "assistant", "content": answer}][-10:]
                        st.session_state.speech = None
                    try:
                        with st.spinner("음성 답변을 생성하고 있어요..."):
                            speech = client.audio.speech.create(model="tts-1", voice="alloy", input=answer)
                            st.session_state.speech = speech.content
                    except Exception:
                        st.warning("음성 출력에 실패했습니다. 아래 텍스트 답변은 확인할 수 있습니다.")
            except Exception:
                # SDK 오류 원문에 인증 정보가 포함될 수 있으므로 노출하지 않는다.
                st.error("음성 처리 또는 답변 생성에 실패했습니다. 인증 설정과 연결 상태를 확인한 뒤 다시 시도해 주세요.")
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    if st.session_state.get("speech"):
        st.audio(st.session_state.speech, format="audio/mpeg")
    if st.button("대화 초기화"):
        st.session_state.messages = []
        st.session_state.speech = None
        st.rerun()


def main():
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("menu", "대시보드")
    with st.sidebar:
        st.markdown('<div class="brand">✦ able<span>AI PERSONAL ASSISTANT</span></div>', unsafe_allow_html=True)
        st.caption("WORKSPACE")
        st.radio("메뉴", MENUS, key="menu", label_visibility="collapsed")
        st.divider()
        st.markdown("**당신의 하루에, 여유를 더하다.**")
        st.caption("복잡한 업무는 정리하고, 중요한 일에 집중하세요.")
        st.markdown('<div class="sidebar-footer">● 에이블 워크스페이스<br><small>개인 워크스페이스 · 데모</small></div>', unsafe_allow_html=True)
    date = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y.%m.%d")
    st.markdown(f'<div class="topbar"><strong>AI 개인비서 에이블</strong><span>{date} &nbsp; | &nbsp; <b>에이블님</b> · 데모 사용자</span></div>', unsafe_allow_html=True)
    menu = st.session_state.menu
    if menu == "대시보드":
        dashboard()
    elif menu == "음성 비서":
        voice_assistant()
    elif menu == "나의 업무":
        st.title("나의 업무")
        st.caption("예시 데이터 · 업무 추가 및 편집 기능은 준비 중입니다.")
        status = st.selectbox("상태 필터", ["전체", "진행 중", "완료"])
        rows = [t for t in TASKS if status == "전체" or t["상태"] == status]
        st.dataframe([{k: v for k, v in t.items() if k != "긴급"} for t in rows], hide_index=True, width="stretch")
    elif menu == "일정 관리":
        st.title("일정 관리")
        st.caption("예시 데이터 · 일정 추가 및 편집 기능은 준비 중입니다.")
        with st.container(border=True, key="schedule_panel"):
            schedule()
    elif menu == "회의록":
        st.title("회의록")
        st.info("회의록 파일 미리보기를 제공합니다. AI 분석 및 업무 추출 기능은 준비 중입니다.")
        meeting = st.file_uploader("회의록 TXT 업로드", type=["txt"], key="meeting_file")
        if meeting is not None:
            try:
                st.text_area("회의록 내용", meeting.getvalue().decode("utf-8-sig"), height=300)
                st.success("회의록 업로드 완료")
            except UnicodeDecodeError:
                st.error("UTF-8로 저장한 텍스트 파일을 업로드해 주세요.")
    else:
        st.title("설정")
        st.info("사용자 정보 및 알림 설정은 준비 중입니다.")


main()
