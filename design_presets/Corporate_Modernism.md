## 📛 Genre Name
[NAME: Corporate_Modernism]

## 💡 Core Concept & Killer Points
- **메인 컨셉 (Main Concept):** 세련되고 전문적인 비즈니스 신뢰감
- **킬러 포인트 (Killer Points):**
  1. 대각선 분할을 통한 시각적 긴장감
  2. 블루와 그레이의 차분한 컬러 대비
  3. 깔끔한 아이콘과 그래픽 요소의 사용

## 📌 Design Rules
- **무드 & 페르소나:** 모던 브루탈리즘
- **동적 구글 폰트 (Dynamic Fonts):**
  ```css
  @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');
  ```
- **컬러 매핑:**
  - 배경: #FFFFFF
  - 텍스트: #333333
  - 포인트 컬러: #007BFF
  - 테두리: #CCCCCC
- **타이포그래피 위계:**
  - 헤드라인: 'Roboto', sans-serif; font-weight: 700;
  - 본문: 'Roboto', sans-serif; font-weight: 400;
  - 데이터(숫자): 'Roboto', sans-serif; font-weight: 700; color: #007BFF;
- **이미지 연출:**
  - 필터: 흑백
  - 형태: border-radius: 8px;
- **장식 요소:**
  - 선: 두께 2px의 단색 선
  - 오프셋 그림자: 없음
  - 밑줄: 포인트 컬러로 강조
- **레퍼런스 특화 시그니처 (Signature Details):**
  - 대각선 레이어링
  - 극단적인 폰트 크기 조정
  - 이미지와 텍스트의 겹침
- **마이크로 인터랙션 모션 (Micro-interactions):**
  - 호버 시 포인트 컬러로 전환
  - 페이드인 효과
  - 슬라이드 인 애니메이션
- **의미 단위 행간 분리:**
  - CSS `word-break: keep-all;` 사용

## 🧩 Component Usage Guide
- 대각선 레이어링을 구현하려면 반드시 `<div class='diagonal-wrapper'><div class='diagonal-layer'></div><img class='hero-img'></div>` 구조로 작성하세요.

## 💻 Custom CSS
```css
/* 1. Dynamic Google Fonts Import */
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');

:root {
  --bg: #FFFFFF;
  --text: #333333;
  --accent: #007BFF;
  --border: #CCCCCC;
}

body {
  background: var(--bg);
  color: var(--text);
  font-family: 'Roboto', sans-serif;
}

h1, h2, h3 {
  font-weight: 700;
  color: var(--text);
}

p, li {
  word-break: keep-all;
  font-weight: 400;
}

.huge-number {
  font-weight: 700;
  color: var(--accent);
}

.fact-label {
  color: var(--text);
}

.brutal-img, .img-hero, .img-float-right, .circle-img {
  filter: grayscale(100%);
  border-radius: 8px;
}

.marker-underline {
  text-decoration: underline;
  text-decoration-color: var(--accent);
}

.hand-drawn-circle {
  border: 2px solid var(--accent);
  border-radius: 50%;
}

.card {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  transition: all 0.3s ease;
}

.card:hover {
  transform: translateY(-5px);
}

@keyframes fade-in-up {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.slide-page {
  animation: fade-in-up 0.8s ease-out forwards;
}
```