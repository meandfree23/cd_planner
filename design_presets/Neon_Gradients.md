## 📛 Genre Name
[NAME: Neon_Gradients]

## 💡 Core Concept & Killer Points
- **메인 컨셉 (Main Concept):** 현대적이고 에너제틱한 느낌의 네온 그라데이션을 활용한 시각적 임팩트.
- **킬러 포인트 (Killer Points):**
  1. 네온 그라데이션 배경
  2. 대담한 타이포그래피
  3. 간결한 아이콘 사용

## 📐 Component Mapping Blueprint
1. **네온 그라데이션 배경:**
   - `.bg-gradient` 클래스를 사용하여 배경에 그라데이션 효과 적용.
2. **대담한 타이포그래피:**
   - `.text-bold`와 `.text-large`를 조합하여 타이틀 강조.
3. **간결한 아이콘 사용:**
   - `.icon-circle`을 사용하여 아이콘을 원형 배경에 배치.

## 📌 Design Rules
- **무드 & 페르소나:** 현대적, 에너제틱, 혁신적
- **동적 구글 폰트 (Dynamic Fonts):** 
  ```css
  @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@700&display=swap');
  ```
- **컬러 매핑:**
  - 배경: #e0f7fa
  - 텍스트: #000000
  - 포인트 컬러: #00e5ff
  - 테두리: #b2ebf2
- **타이포그래피 위계:**
  - 헤드라인: 'Montserrat', sans-serif
  - 본문: 'Arial', sans-serif
  - 데이터(숫자): 'Courier New', monospace
- **시그니처 디테일:** 
  - 네온 효과를 위한 그림자와 그라데이션 필터 적용

## 🧩 Component & Blueprint Usage Guide
- 네온 그라데이션 배경을 사용할 때는 `<div class='slide-page bg-gradient'><div class='content-box'>...</div></div>` 구조로 작성하세요.
- 대담한 타이포그래피는 `<h1 class='text-bold text-large'>...</h1>` 형태로 적용하세요.
- 아이콘은 `<div class='icon-circle'><i class='icon'></i></div>` 구조로 배치하세요.

## 💻 Custom CSS
```css
/* 1. Dynamic Google Fonts Import */
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@700&display=swap');

:root { --bg: #e0f7fa; --text: #000000; --accent: #00e5ff; --border: #b2ebf2; }
body { background: var(--bg); color: var(--text); font-family: 'Arial', sans-serif; }
h1, h2, h3 { font-family: 'Montserrat', sans-serif; font-weight: 700; }
p, li { word-break: keep-all; }
.huge-number { font-family: 'Courier New', monospace; }
.fact-label { font-weight: bold; }
/* 이미지 필터링 필수 부여 */
.brutal-img, .img-hero, .img-float-right, .circle-img { filter: brightness(1.1); border-radius: 8px; }
/* 장식 요소 및 마이크로 인터랙션 모션 */
.marker-underline { text-decoration: underline; text-decoration-color: var(--accent); }
.hand-drawn-circle { border: 2px dashed var(--accent); border-radius: 50%; }
.card { background: transparent !important; border: none !important; box-shadow: none !important; transition: all 0.3s ease; }
.card:hover { transform: translateY(-5px); }
@keyframes fade-in-up { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
.slide-page { animation: fade-in-up 0.8s ease-out forwards; }
.bg-gradient { background: linear-gradient(135deg, #00e5ff, #e0f7fa); }
.icon-circle { background-color: var(--accent); border-radius: 50%; padding: 10px; }
```