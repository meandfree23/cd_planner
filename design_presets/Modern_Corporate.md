## 📛 Genre Name
[NAME: Modern_Corporate]

## 💡 Core Concept & Killer Points
- **메인 컨셉 (Main Concept):** 세련되고 전문적인 브랜드 아이덴티티
- **킬러 포인트 (Killer Points):** 
  1. 강렬한 레드와 화이트의 대비
  2. 간결하고 명확한 타이포그래피
  3. 정교한 레이아웃과 여백 활용

## 📌 Design Rules
- **무드 & 페르소나:** 미니멀리즘, 코퍼레이트
- **동적 구글 폰트 (Dynamic Fonts):** 
  - 폰트: Metropolis
  - `@import url('https://fonts.googleapis.com/css2?family=Metropolis:wght@400;700&display=swap');`
- **컬러 매핑:**
  - 배경: #FFFFFF
  - 텍스트: #333333
  - 포인트 컬러: #D32F2F
  - 테두리: #E0E0E0
- **타이포그래피 위계:**
  - 헤드라인: Metropolis, Bold, #D32F2F
  - 본문: Metropolis, Regular, #333333
  - 데이터(숫자): Metropolis, Bold, #333333
- **이미지 연출:** 
  - 필터: 없음
  - 형태: Border-radius 0
- **장식 요소:** 
  - 밑줄: 포인트 컬러로 강조
- **레퍼런스 특화 시그니처 (Signature Details):**
  - 컬러 매트 레이어링
  - 극단적인 폰트 크기
  - 이미지와 텍스트의 겹침
- **마이크로 인터랙션 모션 (Micro-interactions):**
  - 호버 시 텍스트 컬러 변화
  - 페이드인 효과
- **의미 단위 행간 분리:** `word-break: keep-all;` 유지

## 🧩 Component Usage Guide
- "컬러 매트 레이어링을 구현하려면 반드시 `<div class='matte-wrapper'><div class='color-matte'></div><img class='hero-img'></div>` 구조로 작성하세요."

## 💻 Custom CSS
```css
/* 1. Dynamic Google Fonts Import */
@import url('https://fonts.googleapis.com/css2?family=Metropolis:wght@400;700&display=swap');

:root { 
  --bg: #FFFFFF; 
  --text: #333333; 
  --accent: #D32F2F; 
  --border: #E0E0E0; 
}

body { 
  background: var(--bg); 
  color: var(--text); 
  font-family: 'Metropolis', sans-serif; 
}

h1, h2, h3 { 
  font-family: 'Metropolis', sans-serif; 
  font-weight: bold; 
  color: var(--accent); 
}

p, li { 
  word-break: keep-all; 
  font-family: 'Metropolis', sans-serif; 
}

.huge-number { 
  font-size: 2.5rem; 
  font-weight: bold; 
  color: var(--text); 
}

.fact-label { 
  font-size: 1rem; 
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
  color: var(--accent); 
}

@keyframes fade-in-up { 
  from { opacity: 0; transform: translateY(20px); } 
  to { opacity: 1; transform: translateY(0); } 
}

.slide-page { 
  animation: fade-in-up 0.8s ease-out forwards; 
}
```