## 📛 Genre Name
[NAME: Corporate_Modern]

## 💡 Core Concept & Killer Points
- **메인 컨셉 (Main Concept):** 전문적이고 현대적인 비즈니스 프레젠테이션.
- **킬러 포인트 (Killer Points):**
  1. 대각선으로 분할된 레이아웃.
  2. 블루와 그레이의 세련된 컬러 조합.
  3. 깔끔하고 직관적인 아이콘 및 데이터 시각화.

## 📐 Component Mapping Blueprint
1. **Diagonal Layout:**
   - `.grid-2-col`과 `.bg-diagonal`을 조합하여 대각선 분할을 구현.
2. **Team Section:**
   - `.grid-asymmetric`와 `.glass-card`를 사용하여 팀 멤버 소개.
3. **Data Visualization:**
   - `.brutal-card`와 `.text-massive`를 사용하여 데이터 강조.

## 📌 Design Rules
- **무드 & 페르소나:** 현대적이고 전문적인 비즈니스.
- **동적 구글 폰트 (Dynamic Fonts):** 
  - `@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');`
- **컬러 매핑:**
  - 배경: #FFFFFF
  - 텍스트: #333333
  - 포인트 컬러: #007BFF
  - 테두리: #DDDDDD
- **타이포그래피 위계:**
  - 헤드라인: Roboto, Bold, 32px
  - 본문: Roboto, Regular, 16px
  - 데이터(숫자): Roboto, Bold, 24px
- **시그니처 디테일:** 
  - 그림자: `box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);`
  - 이미지 필터: `filter: grayscale(100%);`

## 🧩 Component & Blueprint Usage Guide
- **Diagonal Layout 사용법:**
  ```html
  <div class='slide-page layout-diagonal'>
    <div class='diagonal-bg'></div>
    <div class='content-box'>
      <h1>Business Presentation</h1>
      <p>Lorem ipsum dolor sit amet...</p>
    </div>
  </div>
  ```
- **Team Section 사용법:**
  ```html
  <div class='grid-asymmetric'>
    <div class='glass-card'>
      <img src='team-member.jpg' alt='Team Member'>
      <h3>John Doe</h3>
      <p>Position</p>
    </div>
  </div>
  ```
- **Data Visualization 사용법:**
  ```html
  <div class='brutal-card'>
    <div class='text-massive'>99%</div>
    <p>Success Rate</p>
  </div>
  ```

## 💻 Custom CSS
```css
/* 1. Dynamic Google Fonts Import */
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');

:root { --bg: #FFFFFF; --text: #333333; --accent: #007BFF; --border: #DDDDDD; }
body { background: var(--bg); color: var(--text); font-family: 'Roboto', sans-serif; }
h1, h2, h3 { font-weight: 700; }
p, li { word-break: keep-all; font-weight: 400; }
.huge-number { font-size: 24px; font-weight: 700; }
.fact-label { font-size: 16px; font-weight: 400; }
/* 이미지 필터링 필수 부여 */
.brutal-img, .img-hero, .img-float-right, .circle-img { filter: grayscale(100%); border-radius: 8px; }
/* 장식 요소 및 마이크로 인터랙션 모션 */
.marker-underline { text-decoration: underline; color: var(--accent); }
.hand-drawn-circle { border: 2px solid var(--accent); border-radius: 50%; }
.card { background: transparent !important; border: none !important; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1) !important; transition: all 0.3s ease; }
.card:hover { transform: translateY(-5px); }
@keyframes fade-in-up { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
.slide-page { animation: fade-in-up 0.8s ease-out forwards; }
```