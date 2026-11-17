# AIVLE School 학습 도우미

기존 노트북의 RAG 흐름을 유지한 Streamlit 앱입니다. 원본 노트북은 수정하지 않았습니다.

## 실행 (Windows PowerShell)

Python 3.11 또는 3.12를 설치하고 PATH에 등록한 뒤 프로젝트 폴더에서 실행합니다.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

`.env`의 `OPENAI_API_KEY=` 뒤에 본인의 키를 입력합니다. `.env`는 Git에서 제외됩니다.
이미 시스템 환경변수에 키가 있다면 `.env` 없이 사용할 수 있습니다.

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

브라우저에서 http://localhost:8501 에 접속합니다. 노트북을 먼저 실행하거나 기존 `chroma_db`를 복사할 필요는 없습니다.

## 기능 확인 순서

1. 키 없이 실행해도 화면이 표시되고 설정 안내가 나오는지 확인합니다.
2. 키 설정 후 텍스트가 있는 PDF를 업로드합니다. `검색 준비 완료`와 청크 수를 확인합니다.
3. 문서에 답이 있는 질문 또는 FAQ 버튼으로 질문하고 스트리밍 답변과 근거를 확인합니다.
4. 문서에 없는 내용을 물어보고 확인할 수 없다는 답변을 확인합니다. 모델 특성상 문서 근거를 직접 검토하세요.
5. 후속 질문을 하고 사이드바의 기록 확인·JSON 저장·삭제를 확인합니다. 삭제해도 문서 인덱스는 유지됩니다.
6. PDF를 교체하거나 제거하면 이전 인덱스와 대화가 초기화되고, 새 문서만 검색되는지 확인합니다.

## 구성 및 동작

- `app.py`: 사이드바 업로드, 자동 처리, FAQ, 채팅, 기록 관리, 오류 안내
- `rag.py`: PyMuPDF4LLMLoader → RecursiveCharacterTextSplitter(500/100) → text-embedding-3-small → Chroma(k=3) → gpt-4o-mini
- 업로드 목록이 바뀔 때만 자동으로 벡터화합니다. 업로드 목록 전체를 현재 문서로 사용합니다.
- 사용자 세션마다 별도의 Chroma 컬렉션을 사용합니다. 디스크에 문서나 대화를 영구 저장하지 않으며, 서버 재시작 시 사라집니다. 세션 종료 후 메모리는 서버 종료까지 남을 수 있습니다.
- 답변 근거는 검색된 원문 조각입니다. 로더에서 페이지 정보를 제공할 때만 페이지를 표시합니다.
- 총 업로드는 30MB로 제한합니다. 이미지 전용·암호화 PDF는 텍스트 PDF로 변환해 주세요. OCR 설정은 포함하지 않았습니다.
- 문서와 질문이 OpenAI로 전송되며 API 비용이 발생합니다. PDF 분량에 따라 초기 처리 시간이 달라집니다.
- `.env` 변경 후에는 Streamlit 프로세스를 종료하고 재실행합니다.

## 검증 환경

구현 시점의 터미널에서는 Python 실행 파일을 찾을 수 없어 의존성 설치, Streamlit 실행 및 실제 OpenAI API 응답은 검증하지 못했습니다. 위 순서로 로컬 확인이 필요합니다. 의존성 버전은 제공된 노트북을 따릅니다.

## 이 저장소에서 독립 실행

기존 루트 앱과 별도로 실행합니다. 아래 명령은 저장소 루트에서 시작합니다.

```powershell
cd learning_assistant
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
# .env에 본인의 키를 입력한 뒤 실행
.\.venv\Scripts\python.exe -m streamlit run app.py --server.port=8502
```

기존 앱은 기존 환경에서 저장소 루트의 `app.py`를 실행합니다. 두 앱을 동시에 실행할 때 학습 도우미는 8502 포트를 사용합니다. 기존 파일과 영구 저장된 `chroma_db`, `data`는 사용하거나 변경하지 않습니다. 노트북은 `notebooks/`에 원본 그대로 보관하며 앱 실행에 필요하지 않습니다.

`.env`는 작업 디렉터리에 관계없이 이 앱 폴더의 파일만 읽으며, 기존 환경변수를 덮어쓰지 않습니다. 키는 환경변수(또는 로컬 `.env`)를 먼저 확인한 뒤 Streamlit Secrets에서 읽습니다. 실제 키를 저장소에 추가하지 마세요. `.env.example`에는 빈 자리표시자만 포함됩니다.

## Streamlit Community Cloud 별도 앱 배포

- Repository: 이 저장소
- Branch: `feature/aivle-project4`
- Main file path: `learning_assistant/app.py`
- Python: 3.12 선택 권장 (설치·실행 검증 필요)
- Advanced settings의 Secrets에 다음 형식으로 본인의 키 설정:

```toml
OPENAI_API_KEY = "여기에 본인의 키 입력"
```

의존성은 진입점과 같은 폴더의 `learning_assistant/requirements.txt`가 루트 파일보다 우선합니다. 원본의 버전 고정과 `python-dotenv`를 유지했습니다. 별도 Cloud 앱은 기존 앱과 독립된 실행 환경을 사용합니다.

Cloud는 저장소 루트를 작업 디렉터리로 사용하므로 이 폴더의 `.streamlit/config.toml`은 자동 적용되지 않습니다. Cloud에서는 기존 루트 설정이 적용됩니다. 학습 도우미의 화면 CSS와 코드 내 PDF 합계 30MB 검사는 계속 적용됩니다. 로컬에서 이 폴더로 이동해 실행하면 전용 테마와 파일 업로드 제한도 적용됩니다.

공식 참고: [의존성 탐색 순서](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies), [Cloud 실행 디렉터리](https://docs.streamlit.io/deploy/streamlit-community-cloud/status), [설정 파일](https://docs.streamlit.io/develop/api-reference/configuration/config.toml).

이번 이전에서는 Python 실행 파일을 찾지 못해 패키지 설치, 앱 실행, 실제 API 호출 및 Cloud 배포를 수행하지 않았습니다. 이 코드를 GitHub에서 배포하려면 추후 별도의 commit/push가 필요합니다. 이번 작업에서는 수행하지 않습니다.
