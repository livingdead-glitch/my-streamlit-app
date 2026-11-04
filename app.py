
import os, base64, json, requests
import streamlit as st
from openai import OpenAI

# OpenAI 클라이언트 생성
client = OpenAI()

# 페이지 설정 - 웹 브라우저에 표시할 제목, 아이콘, 화면 너비 지정
st.set_page_config(page_title="음성 AI 서비스", page_icon="🤖", layout="wide")

# AI 개인비서 에이블 화면 디자인 - 추가
st.markdown("""
<style>
    .stApp {
        background-color: #F4F7FC;
    }

    h1, h2, h3 {
        color: #17365D;
    }

    div.stButton > button {
        background-color: #2563EB;
        color: white;
        border-radius: 10px;
        border: none;
    }

    div.stButton > button:hover {
        background-color: #1D4ED8;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# AI 개인비서 에이블의 제목 및 소개 문구 변경
# 기존 '음성 인식 AI 서비스'를 프로젝트 이름에 맞게 수정
st.title("AI 개인비서 에이블")
st.write("당신의 칼퇴 도움이, AI 비서 에이블이 도와드립니다.")

# 역할 지정
sys_role = """
당신은 다양한 업무를 처리하는 AI 서비스입니다.
개인 비서처럼 친절하게 응대합니다.
"""

# 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

# 음성 비서 기능을 구분하기 위한 탭 생성 - 추가
tab1, tab2 = st.tabs(["🎙️ 음성 비서", "📅 업무 관리"])


# 음성 비서 기능을 첫 번째 탭에 배치
with tab1:

      # 지시 영역
      with st.form("task_form"):
        uploaded_file = st.file_uploader("텍스트 파일 업로드", type=["txt"])
        audio_value = st.audio_input("무엇을 도와드릴까요?")
        submitted = st.form_submit_button("실행", type="primary")

  # 버튼을 눌렀을 때만 실행
      if submitted:
      # 업로드 된 파일이 있으면 디코딩
        text = ""
      if uploaded_file is not None:
          text = uploaded_file.read().decode("utf-8")

      # 녹음이 없으면 녹음 요청
      if audio_value is None:
          st.warning("음성을 녹음해주세요.")
          st.stop()

      # 시스템 메세지
      system_content = sys_role
      if text:
          system_content += f"\n\n다음 내용을 참고하세요:\n{text}"
      input_messages = [{"role": "system", "content": system_content}]

      # STT: 음성 → 텍스트
      transcript = client.audio.transcriptions.create(
          model="whisper-1",
          file=("audio.wav", audio_value, "audio/wav"))

      # STT 음성 인식 결과 출력 - 사용자가 음성으로 질문했을 때 AI가 인식한 문장을 화면에서 확인 - 추가
      st.subheader("🎙️ 음성 인식 결과")
      st.info(transcript.text)



      # 멀티턴 대화 - 사용자 질문을 대화 기록에 저장 - 교체
      st.session_state.messages.append({"role": "user","content": transcript.text})

      # 이전 대화 기록을 AI에게 전달 - 교체
      input_messages.extend(st.session_state.messages)


      # LLM 호출 및 응답 듣기
      with st.spinner("답변을 준비하고 있습니다..."):
          # LLM 호출
          response = client.responses.create(
              model="gpt-4o-mini",
              input=input_messages
          )
          answer = response.output_text

          # 멀티턴 대화 - AI 답변을 대화 기록에 저장 - 교체
          st.session_state.messages.append({"role": "assistant","content": answer})

          # 최근 대화 기록 10개만 유지 - 추가
          st.session_state.messages = st.session_state.messages[-10:]

          # 응답 출력
          st.subheader("AI 답변")
          st.write(answer)

          # TTS: AI 답변을 음성으로 변환 - AI가 생성한 텍스트 답변을 음성으로 변환 - 추가
          with st.spinner("음성 답변을 생성하고 있습니다..."):
              speech = client.audio.speech.create(
                  model="tts-1",
                  voice="alloy",
                  input=answer
              )

          # 음성 답변 재생 - 생성된 음성을 사용자가 재생할 수 있도록 오디오 플레이어 제공 - 추가
          st.subheader("🔊 AI 음성 답변")
          st.audio(speech.content, format="audio/mpeg")

          # 업무 관리 탭 화면 구성 - 추가
with tab2:
    st.subheader("📅 에이블 업무 관리")
    st.write("회의록을 분석하여 담당 업무와 마감일을 관리합니다.")

     # 업무 분석을 위한 회의록 TXT 파일 업로드 - 추가
    meeting_file = st.file_uploader("📄 회의록을 업로드하세요", type=["txt"], key="meeting_file")

    # 업로드한 회의록을 텍스트로 변환
    if meeting_file is not None:
        meeting_text = meeting_file.getvalue().decode("utf-8")
        st.success("✅ 회의록 업로드 완료!")
