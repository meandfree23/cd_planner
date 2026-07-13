## 📛 Genre Name
[NAME: Modern_Branding]

## 💡 Core Concept & Killer Points
- **메인 컨셉 (Main Concept):** 깔끔하고 세련된 브랜드 아이덴티티
- **킬러 포인트 (Killer Points):**
  1. 강렬한 레드와 화이트의 대비
  2. 직선적이고 명확한 레이아웃
  3. 일관된 타이포그래피와 그리드 시스템

## 📌 Design Rules
- **무드 & 페르소나:** 미니멀리즘과 현대적 브랜딩
- **동적 구글 폰트 (Dynamic Fonts):**
  ```css
  @import url('https://fonts.googleapis.com/css2?family=Metropolis:wght@400;700&display=swap');
  ```
- **컬러 매핑:**
  - 배경: #FFFFFF
  - 텍스트: #000000
  - 포인트 컬러: #E30613
  - 테두리: #CCCCCC
- **타이포그래피 위계:**
  - 헤드라인: 'Metropolis', sans-serif; font-weight: 700;
  - 본문: 'Metropolis', sans-serif; font-weight: 400;
  - 데이터(숫자): 'Metropolis', sans-serif; font-weight: 700;
- **이미지 연출:** 
  - 필터: 없음
  - 형태: border-radius: 0;
- **장식 요소:** 
  - 밑줄: 포인트 컬러로 강조
- **레퍼런스 특화 시그니처 (Signature Details):** 
  - 컬러 매트 레이어링: .color-matte
  - 극단적인 폰트 크기: .large-text
  - 이미지와 텍스트의 겹침: .overlapping
- **마이크로 인터랙션 모션 (Micro-interactions):**
  - 호버 시 텍스트 컬러 변화
  - 페이드인 효과
  ```css
  @keyframes fade-in-up {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
  }
  ```
- **의미 단위 행간 분리:** `word-break: keep-all;`

## 🧩 Component Usage Guide
- 컬러 매트 레이어링을 구현하려면 반드시 `<div class='matte-wrapper'><div class='color-matte'></div><img class='hero-img'></div>` 구조로 작성하세요.
- 텍스트와 이미지의 겹침을 위해 `<div class='overlapping'><img class='img'><h1 class='large-text'></h1></div>` 구조를 사용하세요.

## 💻 Custom CSS
```css
/* 1. Dynamic Google Fonts Import */
@import url('https://fonts.googleapis.com/css2?family=Metropolis:wght@400;700&display=swap');

:root { 
  --bg: #FFFFFF; 
  --text: #000000; 
  --accent: #E30613; 
  --border: #CCCCCC; 
}

body { 
  background: var(--bg); 
  color: var(--text); 
  font-family: 'Metropolis', sans-serif; 
}

h1, h2, h3 { 
  font-weight: 700; 
  color: var(--accent); 
}

p, li { 
  word-break: keep-all; 
  font-weight: 400; 
}

.huge-number { 
  font-size: 2em; 
  font-weight: 700; 
}

.fact-label { 
  font-weight: 400; 
  color: var(--text); 
}

/* 이미지 필터링 필수 부여 */
.brutal-img, .img-hero, .img-float-right, .circle-img { 
  filter: none; 
  border-radius: 0; 
}

/* 장식 요소 및 마이크로 인터랙션 모션 */
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

.slide-page { 
  animation: fade-in-up 0.8s ease-out forwards; 
}
```