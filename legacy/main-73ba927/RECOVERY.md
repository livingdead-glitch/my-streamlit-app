# 기존 main 복구 기준

- 저장소: `livingdead-glitch/my-streamlit-app`
- 원본 main 커밋: `73ba927e6c8bc2249e5776e6b51010c64699a27b`
- `app.py`, `requirements.txt`, `README.md`: 전환 준비 전 루트 원본
- `manifest.json`: 각 원본의 SHA256
- `chroma_db`, `data`, `.streamlit/config.toml`, 기존 테스트·스타일 파일은 기존 위치 그대로 보존

백업 앱은 기존 상대 경로 `chroma_db`를 사용하므로 이 폴더를 작업 디렉터리로 실행하지 마세요. 복구할 때 원본 루트 파일을 되돌립니다.

## 이번 준비 작업

현재 main은 변경하지 않았습니다. 향후 실제 전환 직전에 최신 원격 main과 이 기준 커밋이 같은지 다시 확인합니다. main이 달라졌다면 최신 main 기준으로 복구 자료를 갱신한 뒤 전환합니다. 복구 태그는 아직 만들지 않았습니다.

## 배포 이후 복구가 필요한 경우

전환 변경을 독립된 커밋으로 남긴 뒤 문제가 생기면 해당 커밋을 `git revert`하는 방법을 권장합니다. 병합 커밋을 되돌리는 경우에는 부모 확인 후 `git revert -m 1 <병합커밋>`을 사용합니다. 공유 main을 reset하거나 force push하지 않습니다.

루트 실행 파일·의존성·문서만 원본으로 돌리는 대안은 다음과 같습니다. **아래 명령은 설명이며 이번 작업에서 실행하지 않습니다.**

```powershell
git restore --source=73ba927e6c8bc2249e5776e6b51010c64699a27b -- app.py requirements.txt README.md
git diff -- app.py requirements.txt README.md
# 확인 후 별도 복구 commit과 main 반영 절차 진행
```

현재 저장소의 백업 파일로도 세 루트 파일을 복원할 수 있습니다. 복원 전 `manifest.json`의 SHA256과 백업 파일을 비교합니다. 기존 DB와 데이터는 삭제하거나 덮어쓰지 않습니다.

Cloud의 기존 앱·URL·`main` 브랜치·루트 `app.py`·Secrets 설정을 유지한 채 복구 변경을 main에 반영하면 기존 코드로 재배포됩니다. 소스 복구는 일시적인 채팅·업로드 세션을 복구하지 않습니다. 이번 작업은 서버의 실시간 DB나 Cloud Secrets 백업을 수행하지 않습니다.
