# AIVLE School 학습 도우미

기존 노트북의 RAG 흐름을 유지한 Streamlit 앱입니다. 원본 노트북은 수정하지 않았습니다.

## 학습 메뉴

- **RAG 채팅**: 업로드한 문서 검색, 후속 질문, 스트리밍 답변과 원문 근거를 제공합니다.
- **AI 맞춤형 학습 코치**: 사이드바에서 초급·중급·고급을 선택하고 개념을 입력하면 수준에 맞게 설명합니다. 초급은 쉬운 용어와 단계별 설명, 중급은 개념의 관계와 차이, 고급은 문서에 명시된 조건과 세부 원리를 다룹니다. 문서에 없는 내용은 확인할 수 없다고 안내하도록 지시합니다.
- **이해도 확인 문제**: 선택한 수준과 주제로 4지선다 문제 하나를 생성합니다. 주제를 비우면 핵심 개념으로 출제합니다. 보기를 선택하고 답안을 제출하면 정답 여부·정답·해설·원문 인용을 표시합니다. 새 문제는 버튼을 눌러 생성합니다.

세 메뉴는 같은 세션의 PDF 인덱스와 검색기를 공유합니다. 코치·출제 체인도 최초 사용 후 재사용하며 메뉴 전환이나 답안 제출만으로 문서를 재벡터화하거나 문제를 다시 생성하지 않습니다. PDF 교체·제거 시 채팅, 코치 설명, 문제와 채점 상태를 초기화합니다. 같은 문서에 대한 새 질문·설명·출제에는 검색 및 생성 API 비용이 발생할 수 있습니다.

문제는 구조화된 응답으로 생성하고 보기 4개·정답 인덱스·중복 보기·해설 유무를 검사합니다. 인용 원문이 검색된 문서 조각에 실제 포함되는지도 확인하며, 근거가 불충분하거나 검증에 실패하면 문제를 표시하지 않습니다. 인용 검사는 정답의 의미적 정확성을 보장하지 않으므로 AI 해설과 원문을 함께 확인해 주세요.

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

현재 검증 결과와 재현 명령은 [VALIDATION.md](VALIDATION.md)를 참고하세요. 의존성의 기존 버전 고정은 유지합니다.

## 이 저장소에서 독립 실행

하위 진입점으로도 실행할 수 있습니다. 배포 준비 이후 루트 `app.py`도 같은 학습 도우미를 실행합니다. 아래 명령은 저장소 루트에서 시작합니다.

```powershell
cd learning_assistant
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
# .env에 본인의 키를 입력한 뒤 실행
.\.venv\Scripts\python.exe -m streamlit run app.py --server.port=8502
```

기존 루트 앱의 원본은 `legacy/main-73ba927/`에 보존했습니다. 기존 `chroma_db`, `data`는 사용하거나 변경하지 않습니다. 노트북은 `notebooks/`에 원본 그대로 보관하며 앱 실행에 필요하지 않습니다.

`.env`는 작업 디렉터리에 관계없이 이 앱 폴더의 파일만 읽으며, 기존 환경변수를 덮어쓰지 않습니다. 키는 환경변수(또는 로컬 `.env`)를 먼저 확인한 뒤 Streamlit Secrets에서 읽습니다. 실제 키를 저장소에 추가하지 마세요. `.env.example`에는 빈 자리표시자만 포함됩니다.

## Streamlit Community Cloud 별도 앱 배포

기존 앱 URL을 유지하는 전환은 [루트 README](../README.md)의 `main` + 루트 `app.py` 설정을 사용합니다. 아래는 별도 시험 앱을 만드는 경우의 설정입니다.

- Repository: 이 저장소
- Branch: `feature/aivle-project4`
- Main file path: `learning_assistant/app.py`
- Python: 3.14 대상 검증 범위는 [VALIDATION.md](VALIDATION.md) 참고
- Advanced settings의 Secrets에 다음 형식으로 본인의 키 설정:

```toml
OPENAI_API_KEY = "여기에 본인의 키 입력"
```

의존성은 진입점과 같은 폴더의 `learning_assistant/requirements.txt`가 루트 파일보다 우선합니다. 원본의 버전 고정과 `python-dotenv`를 유지했습니다. 별도 Cloud 앱은 기존 앱과 독립된 실행 환경을 사용합니다.

Cloud는 저장소 루트를 작업 디렉터리로 사용하므로 이 폴더의 `.streamlit/config.toml`은 자동 적용되지 않습니다. Cloud에서는 기존 루트 설정이 적용됩니다. 학습 도우미의 화면 CSS와 코드 내 PDF 합계 30MB 검사는 계속 적용됩니다. 로컬에서 이 폴더로 이동해 실행하면 전용 테마와 파일 업로드 제한도 적용됩니다.

공식 참고: [의존성 탐색 순서](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies), [Cloud 실행 디렉터리](https://docs.streamlit.io/deploy/streamlit-community-cloud/status), [설정 파일](https://docs.streamlit.io/develop/api-reference/configuration/config.toml).

Cloud 배포와 실제 OpenAI API 응답 검증은 별도 단계입니다. 이번 실행 준비 변경은 feature 브랜치 작업 트리에만 적용하며 main 병합이나 push를 하지 않습니다.

## 문서별 자원 재사용

- 파일 이름과 내용 해시로 업로드 집합을 식별합니다. 업로드 순서만 바뀌면 다시 벡터화하지 않습니다.
- 새 업로드 집합을 처리할 때 임시 PDF 파일을 만들고 `(원본 이름, 임시 경로)` 목록을 `build_index`에 전달합니다. 로딩과 인덱스 생성이 끝나거나 오류가 나면 임시 파일을 삭제합니다.
- 인덱스, 검색기, 답변 체인은 사용자 세션에 보관합니다. 같은 문서에 대한 후속 질문은 이 자원을 재사용하며 검색과 답변 생성만 실행합니다. 질문의 임베딩과 답변 생성에는 API 호출이 계속 필요합니다.
- PDF 교체·제거 시 이전 체인과 대화를 비우고 이전 컬렉션을 삭제합니다. 새 PDF 처리가 실패하면 이전 문서로 답변하지 않습니다. 실패한 업로드는 재시도 버튼을 눌러 다시 처리합니다.
- 대화 기록만 삭제하는 경우에는 인덱스와 체인을 유지합니다. 브라우저 세션이 초기화되거나 문서를 교체 후 다시 올리면 재처리합니다. 세션 간 전역 캐시는 사용하지 않습니다.
- `app.py`의 패키지 import 경로를 명시해 저장소 루트에서 `streamlit run learning_assistant/app.py`로도 실행할 수 있습니다. 루트 `app.py`는 이 하위 앱을 매 재실행마다 호출하는 배포 진입점입니다.
