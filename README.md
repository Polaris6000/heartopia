heartopia/
├── index.html                    # 메인 진입점
├── 404.html
├── .htaccess
│
├── src/
│   ├── components/
│   │   ├── header.html
│   │   ├── footer.html
│   │   └── nav.html             # [추가] 네비게이션 분리
│   │
│   ├── css/
│   │   ├── common.css
│   │   ├── variables.css        # [추가] CSS 변수 관리
│   │   └── responsive.css       # [추가] 반응형 스타일
│   │
│   ├── js/
│   │   ├── common.js
│   │   ├── api.js               # [추가] API/데이터 로드 로직
│   │   └── utils.js             # [추가] 유틸리티 함수
│   │
│   ├── pages/
│   │   ├── main/
│   │   │   └── main.html
│   │   │
│   │   ├── fish/
│   │   │   ├── fish_list.html
│   │   │   └── fish_finder.html
│   │   │
│   │   ├── bug/
│   │   │   ├── bug_list.html
│   │   │   └── bug_finder.html  # [추가] 일관성 위해
│   │   │
│   │   ├── bird/
│   │   │   ├── bird_list.html
│   │   │   └── bird_finder.html # [추가] 일관성 위해
│   │   │
│   │   └── stats/               # [추가] 통계 페이지
│   │       ├── overview.html
│   │       └── comparison.html
│   │
│   ├── data/                    # [추가] 게임 데이터
│   │   ├── fish.json
│   │   ├── bug.json
│   │   ├── bird.json
│   │   └── locale/              # 다국어 지원
│   │       ├── ko.json
│   │       └── en.json
│   │
│   └── assets/                  # [추가] 정적 리소스
│       ├── images/
│       │   ├── fish/
│       │   ├── bug/
│       │   ├── bird/
│       │   └── ui/
│       ├── icons/
│       └── fonts/
│
└── README.md                    # [추가] 프로젝트 문서