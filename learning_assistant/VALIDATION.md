# 실행 준비 검증 (2026-11-17)

대상 브랜치: `feature/aivle-project4`. 배포 준비 단계에서는 루트 앱·의존성·README를 변경하고 원본을 `legacy/main-73ba927/`에 보존합니다. 기존 데이터·테스트·설정은 유지합니다.

## 현재 확인된 결과와 중단 범위

- 이전 단계에서 별도 Windows Python 3.14.0 런타임에 패키지 설치와 `pip check`가 성공했습니다. Linux wheel 대상 의존성 해결도 성공했습니다.
- Python 3.14에서 업로드 식별·임시 파일 관련 테스트 5개가 통과했습니다.
- 실제 PDF·Chroma 연결과 스트리밍 화면 검증은 Windows 앱 제어 정책의 DLL 차단으로 완료하지 못했습니다. 샌드박스 밖 테스트 요청은 거절됐고, 이후 사용자 요청으로 환경 검증을 중단했습니다. 이 결과를 Python 또는 패키지의 비호환으로 단정하지 않습니다.
- 아래 환경 재현 명령은 참고용입니다. 기능 추가 단계에서는 다운로드·설치·보안 우회 테스트를 실행하지 않습니다.
- 기능 추가 단계에서는 표준 라이브러리만 사용하는 문제 형식·문서 인용 검사 테스트 4개와 Python 소스 구문 검사를 통과했습니다. 실제 모델 기반 코치·문제 생성과 브라우저 화면 흐름은 아직 실행 검증하지 않았습니다.

## 재현 명령

저장소 루트에서 Python 3.14 가상환경을 사용합니다.

```powershell
python -m venv learning_assistant/.venv
learning_assistant/.venv/Scripts/python.exe -m pip install -r learning_assistant/requirements.txt
learning_assistant/.venv/Scripts/python.exe -m pip check
learning_assistant/.venv/Scripts/python.exe -m unittest discover -s learning_assistant/tests -v
learning_assistant/.venv/Scripts/python.exe -m streamlit run learning_assistant/app.py --server.port=8502
```

테스트는 OpenAI 모델을 대체합니다. API 키를 입력하거나 비용이 발생하는 API 요청을 보내지 않습니다. 임시 파일의 수명, 업로드 내용 식별, 업로드 교체/제거/실패/재시도, 후속 질문 시 자원 재사용, 환경변수와 Secrets 우선순위, 실제 PDF 로딩과 Chroma 검색을 검사합니다.

## Python 3.14 / Linux 의존성 검사

`pip install --dry-run --ignore-installed --only-binary=:all: --python-version 3.14 --implementation cp --abi cp314 --abi abi3`에 다음 플랫폼을 지정해 원본 requirements를 검사했습니다.

- `manylinux_2_28_x86_64`
- `manylinux_2_27_x86_64`
- `manylinux2014_x86_64`

의존성 122개 해결에 성공했습니다. Streamlit 1.64.0, LangChain의 기존 고정 버전, Chroma 1.5.9, PyMuPDF 1.28.0을 유지합니다. NumPy, PyArrow, ONNX Runtime에는 CPython 3.14/Linux wheel이 선택됐고 Chroma·PyMuPDF는 stable ABI wheel이 선택됐습니다. requirements 변경은 필요하지 않았습니다.

이 검사는 Linux wheel 제공과 의존성 해결 확인이며 실제 Cloud 컨테이너 실행 보장은 아닙니다. 일부 조건부 의존성은 검사를 수행한 호스트의 영향을 받을 수 있습니다. 전이 의존성은 완전히 고정되어 있지 않으므로 추후 재설치 시 선택 버전이 달라질 수 있습니다.

검사에 사용한 임시 런타임과 상세 pip 보고서는 Git 제외된 `.venv/validation/`에만 저장합니다. 기존 Anaconda 환경에는 패키지를 설치하지 않습니다.

## 배포 전 남은 확인

- 실제 Streamlit Community Cloud Python 3.14/Linux 환경의 설치·시작·메모리 사용량
- 실제 OpenAI 인증, PDF 임베딩, 질문 임베딩, 스트리밍 답변과 근거 품질
- 다중 사용자 동시 접속과 세션 종료 시 메모리 회수
- 준비된 루트 실행 진입점과 의존성을 사용한 실제 Cloud 재배포 (이번 작업에서 수행하지 않음)

실제 Cloud 앱의 Python 버전과 Secrets 설정은 이번 로컬 검증에서 변경하거나 조회하지 않습니다. Cloud에서 직접 이 앱을 시험할 때 실행 경로는 `learning_assistant/app.py`이고, 기존 앱은 여전히 `main`의 루트 `app.py`를 사용합니다.

## 루트 배포 진입점 준비

루트 `app.py`는 절대 경로와 `runpy.run_path(..., run_name="__main__")`로 하위 앱을 매번 실행합니다. 루트 requirements는 하위 파일을 참조합니다. `test_entrypoint.py`는 외부 패키지를 로딩하지 않고 반복 위임·참조 경로·소스 구문을 검사합니다. 이 테스트는 Streamlit 브라우저 동작이나 실제 RAG 응답을 보장하지 않습니다.
