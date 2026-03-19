/**
 * ============================================================
 * tracker.js - 두근두근타운 방문자 추적 스크립트
 * ============================================================
 * 사용법: 추적할 페이지의 <head> 안에 아래 한 줄 추가
 *   <script src="/heartopia/src/js/tracker.js"></script>
 *
 * 데이터 저장소: localStorage → 키 'dkdt_visits'
 * ※ 같은 브라우저에서의 방문만 기록됩니다.
 *   실제 다중 사용자 추적이 필요하면 Google Analytics 등 사용 권장.
 * ============================================================
 */
(function () {
    // ── 상수 ─────────────────────────────────────────────
    const STORAGE_KEY = 'dkdt_visits'; // localStorage 키
    const MAX_RECORDS = 5000;          // 최대 저장 레코드 수 (오래된 것부터 삭제)

    // ── 세션 ID 관리 ─────────────────────────────────────
    // sessionStorage 기반: 탭/브라우저 종료 시 초기화 = 새 세션(방문) 시작
    function getOrCreateSessionId() {
        let sid = sessionStorage.getItem('dkdt_sid');
        if (!sid) {
            // 타임스탬프 + 랜덤으로 충분히 고유한 ID 생성
            sid = Date.now().toString(36) + Math.random().toString(36).slice(2, 9);
            sessionStorage.setItem('dkdt_sid', sid);
        }
        return sid;
    }

    // ── 브라우저 감지 (간략 UA 파싱) ─────────────────────
    function detectBrowser() {
        const ua = navigator.userAgent;
        if (ua.includes('Edg/'))                            return 'Edge';
        if (ua.includes('Chrome/') && !ua.includes('Edg')) return 'Chrome';
        if (ua.includes('Firefox/'))                        return 'Firefox';
        if (ua.includes('Safari/') && !ua.includes('Chrome')) return 'Safari';
        if (ua.includes('OPR/') || ua.includes('Opera'))    return 'Opera';
        return 'Other';
    }

    // ── 디바이스 종류 감지 (화면 너비 기준) ─────────────
    function detectDevice() {
        const w = window.innerWidth || screen.width;
        if (w <= 480)  return 'Mobile';
        if (w <= 1024) return 'Tablet';
        return 'Desktop';
    }

    // ── 경로에서 페이지 이름 추출 ──────────────────────
    // /heartopia/src/pages/fish/fish-list.html → 'fish-list'
    function extractPageName() {
        const path = location.pathname;
        const fileMatch = path.match(/\/([^/]+)\.html$/);
        if (fileMatch) return fileMatch[1];
        // 루트 경로 처리
        if (path === '/' || path.endsWith('/heartopia') || path.endsWith('/heartopia/')) {
            return 'main';
        }
        return path;
    }

    // ── 방문 기록 저장 ───────────────────────────────────
    function recordVisit() {
        // 기존 기록 불러오기
        let records = [];
        try {
            const stored = localStorage.getItem(STORAGE_KEY);
            if (stored) {
                records = JSON.parse(stored);
                if (!Array.isArray(records)) records = [];
            }
        } catch (e) {
            records = []; // 파싱 실패 시 초기화
        }

        // 새 방문 객체
        const visit = {
            ts:      Date.now(),               // 유닉스 타임스탬프 (밀리초)
            sid:     getOrCreateSessionId(),   // 세션 ID (고유 방문 구분)
            path:    location.pathname,        // 전체 경로
            page:    extractPageName(),        // 짧은 페이지 이름
            ref:     document.referrer || '',  // 유입 경로 (레퍼러)
            browser: detectBrowser(),          // 브라우저 종류
            device:  detectDevice(),           // 디바이스 종류
        };

        records.push(visit);

        // 최대 개수 초과 시 오래된 레코드 제거 (FIFO)
        if (records.length > MAX_RECORDS) {
            records.splice(0, records.length - MAX_RECORDS);
        }

        // 저장
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(records));
        } catch (e) {
            // localStorage 용량 초과 등 예외 처리
            console.warn('[tracker] 저장 실패:', e.message);
        }
    }

    // DOM 준비 후 실행 (또는 이미 준비됐으면 즉시 실행)
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', recordVisit);
    } else {
        recordVisit();
    }
})();
