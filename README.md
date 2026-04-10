# travel_recommendation_260408

Streamlit 기반 여행 추천 시스템 대시보드입니다.

## 실행 방법

1. 가상환경을 활성화합니다.
2. 의존성을 설치합니다:
   ```bash
   pip install -r requirements.txt
   ```
3. Streamlit 앱을 실행합니다:
   ```bash
   streamlit run app.py
   ```

## 설명

- `app.py`: Streamlit 대시보드 메인 앱
- `utils.py`: 데이터 로드, 전처리, 추천 엔진 준비 함수
- `recommender.py`: 하이브리드 추천 로직
- `analytics.py`: 시각화 및 분석 대시보드 렌더링
- `styles.py`: 앱 테마 및 CSS

> `data` 폴더 안에 필요한 CSV/GZ 파일들이 있어야 정상 동작합니다.
