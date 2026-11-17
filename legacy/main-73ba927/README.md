# AI 개인비서 에이블

Streamlit 기반 개인 업무 대시보드와 음성 비서입니다. 업무·일정·사용자·브리핑은 **예시 데이터**이며 저장되거나 외부 서비스와 동기화되지 않습니다.

## 실행

Python 3.12 환경에서 저장소 루트를 작업 디렉터리로 사용합니다.

```bash
python3 -m venv /workspace/venvs/my-streamlit-app
/workspace/venvs/my-streamlit-app/bin/python -m pip install -r requirements.txt
/workspace/venvs/my-streamlit-app/bin/python -m streamlit run app.py --server.headless=true --browser.gatherUsageStats=false
```

API 키 없이 대시보드와 모든 메뉴를 열 수 있습니다. 음성 비서만 키가 필요합니다. `OPENAI_API_KEY` 환경변수 또는 Streamlit Secrets의 같은 이름 항목에서 읽습니다. 실제 키를 소스·로그·Git에 기록하지 마세요. 로컬 Secrets를 쓸 경우 `.streamlit/secrets.toml`은 Git에서 제외됩니다. 키 입력 UI는 제공하지 않습니다.

## 화면

- 대시보드: 업무 카드 4종, 오늘의 일정, 마감 임박 목록, 예시 브리핑, 빠른 실행
- 나의 업무: 예시 목록 및 상태 필터 (추가·편집은 준비 중)
- 일정 관리: 오늘의 예시 일정 (추가·편집은 준비 중)
- 음성 비서: 참고 TXT와 녹음 입력 → STT → 답변 → TTS, 최근 10개 메시지 유지, 대화 초기화
- 회의록: UTF-8 TXT 업로드 및 미리보기 (AI 분석은 준비 중)
- 설정: 준비 중

## 기존 코드 분석과 수정

기존 코드는 파일 최상단에서 OpenAI 클라이언트를 생성해 키가 없으면 화면 전체가 실패했습니다. 또한 제출 조건 밖에 놓인 음성 처리 코드와 `st.stop()` 때문에 첫 렌더링에서 실행이 중단되고 업무 관리 탭 내용이 표시되지 않았습니다. 참고 파일 처리도 제출 조건과 분리돼 변수가 초기화되지 않을 가능성이 있었습니다.

클라이언트와 API 호출을 음성 폼 제출 이후로 옮기고 들여쓰기 및 조건을 정리했습니다. 화면은 기능별 함수로 분리하고 사용하지 않는 base64/json/requests import와 중복 주석을 제거했습니다. 기존 모델(`whisper-1`, `gpt-4o-mini`, `tts-1` / `alloy`), 참고 TXT 전달, 멀티턴 대화, 음성 출력은 유지했습니다. 답변 생성 실패 시 대화 기록을 변경하지 않고, TTS만 실패하면 텍스트 답변을 보존합니다. SDK 오류 원문은 화면에 노출하지 않습니다.

## 테스트

```bash
/workspace/venvs/my-streamlit-app/bin/python -m unittest discover -s tests -v
/workspace/venvs/my-streamlit-app/bin/python -m pip check
```

UI 테스트는 키 없는 모든 메뉴, 빠른 이동, 업무 필터, 실행 비활성화, 녹음 누락, 회의록 미리보기와 인코딩 오류를 확인합니다. 음성 처리 테스트는 OpenAI 클라이언트를 모의 객체로 대체하여 STT·답변·TTS 연결, 멀티턴 이력 제한, TTS 실패 후 텍스트 보존을 검증합니다. **실제 API 요청은 보내지 않습니다.**

실제 마이크 권한/녹음, OpenAI 인증 및 모델 응답, 생성 음성 재생 품질은 별도 통합 검증 대상입니다. 첨부 디자인 이미지가 대화에 전달되지 않아 요청에 나열된 요소와 색상을 기준으로 구현했습니다.

## 변경 검토

```bash
git diff -- app.py README.md
git status --short
```

추가 파일 `style.css`, `.streamlit/config.toml`, `tests/test_app.py`, `.gitignore`도 함께 검토하세요. UI 변경은 `feature/able-dashboard-ui` 브랜치에서 검토합니다. 기존 `main` 코드는 유지합니다.
