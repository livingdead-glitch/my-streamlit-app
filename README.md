# AIVLE School 학습 도우미

PDF 기반 RAG 채팅, 초급·중급·고급 AI 학습 코치, 문서 기반 4지선다 이해도 문제를 제공합니다. [기능 설명](learning_assistant/README.md)을 참고하세요.

## 기존 Streamlit Cloud 앱 전환 준비

현재 변경은 `feature/aivle-project4` 작업 트리에 준비한 상태입니다. main에 반영하지 않았으므로 기존 배포 앱은 바뀌지 않습니다.

기존 앱을 삭제하거나 새로 생성하지 않고 향후 검토된 변경을 main에 반영합니다. 배포 설정과 웹주소는 유지합니다.

| 항목 | 유지할 설정 |
| --- | --- |
| Repository | `livingdead-glitch/my-streamlit-app` |
| Branch | `main` |
| Main file path | `app.py` |
| App URL | 기존 URL 유지 |
| Secrets | 기존 최상위 `OPENAI_API_KEY` 사용 |
| Python | 기존 Cloud 설정 유지; 검증 한계는 아래 기록 참고 |

루트 `app.py`는 `runpy.run_path`로 `learning_assistant/app.py`를 매번 실행합니다. Streamlit 재실행마다 화면 코드를 실행하며 인덱스·검색기·채팅·코치·문제 상태는 `st.session_state`에서 유지합니다. 메뉴 전환이나 같은 PDF에 대한 후속 질문으로 다시 벡터화하지 않습니다. PDF 교체·제거 시 관련 학습 상태를 초기화합니다.

루트 `requirements.txt`는 `-r learning_assistant/requirements.txt`를 참조합니다. 기존 고정 버전과 `python-dotenv`를 포함한 하위 앱의 의존성을 설치합니다. [Streamlit 의존성 탐색 규칙](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies).

기존 Cloud Secrets의 최상위 `OPENAI_API_KEY`를 사용합니다. 환경변수를 우선 확인하고 이후 `st.secrets`를 읽습니다. 로컬에서는 선택적으로 `learning_assistant/.env`를 사용하며 기존 환경변수를 덮어쓰지 않습니다. 실제 키나 `.env`, `.streamlit/secrets.toml`은 Git에 추가하지 않습니다. 키 재발급이나 Secrets 복사는 필요하지 않습니다. 실제 Cloud 설정 내용은 이번에 조회하거나 변경하지 않았습니다.

Cloud는 저장소 루트에서 실행하므로 루트 `.streamlit/config.toml`을 그대로 사용합니다. 하위 앱의 설정 파일은 그 폴더에서 로컬 실행할 때 적용됩니다. PDF 합계 30MB 제한은 앱 코드에서 적용됩니다.

## 기존 환경에서 실행

이미 패키지가 준비된 Python 환경에서 저장소 루트를 작업 디렉터리로 사용합니다.

```powershell
python -m streamlit run app.py
```

하위 진입점 `python -m streamlit run learning_assistant/app.py`도 계속 사용할 수 있습니다. 이번 배포 준비에서는 Python 설치나 추가 환경 구축을 하지 않습니다.

## 복구와 검증

기존 루트 파일은 [legacy/main-73ba927](legacy/main-73ba927/)에 원본 그대로 보존했습니다. [복구 절차](legacy/main-73ba927/RECOVERY.md)에 기준 커밋과 복구 명령을 기록했습니다. `chroma_db`, `data`, 기존 테스트·스타일·설정은 보존하며 새 앱은 기존 DB를 변경하지 않습니다.

[검증 기록](learning_assistant/VALIDATION.md)을 참고하세요. 이번에는 실행 진입점의 위임 동작, 소스 구문, 의존성 참조 경로와 원본 백업을 검사합니다. 실제 Cloud 재배포·Secrets 인증·OpenAI 응답은 수행하지 않습니다. 기존 `tests/test_app.py`는 과거 대시보드용이며 새 앱의 인수 검증으로 간주하지 않습니다.

이번 준비 작업에는 commit, main 병합, push 또는 Cloud 설정 변경이 포함되지 않습니다. 향후 main 반영 시 기존 앱 재배포와 사용자 세션 초기화가 발생할 수 있습니다.
