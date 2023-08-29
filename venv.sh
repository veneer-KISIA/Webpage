#!/bin/bash
# 사용법: 다운받을 라이브러리 인자로 넘기기 (가상환경에서 라이브러리 관리)

# venv 활성화
source ./venv/bin/activate
echo venv가 활성화 됨

for lib in "$@"; do
  pip install "$lib"
done

# venv 비활성화
deactivate
echo venv가 비활성화 됨

