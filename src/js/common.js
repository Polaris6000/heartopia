// ============================================================
// 공통 설정
// ============================================================

// 사이트 루트 URL (도메인이 바뀌어도 여기 한 줄만 수정하면 됨)
// window.location.origin 을 사용하면 localhost / GitHub Pages 양쪽에서 자동으로 동작함
const BASE = window.location.origin + '/heartopia';


// ============================================================
// 공통 컴포넌트 로더
// ============================================================
async function loadComponent(elementId, fileName) {
    try {
        const response = await fetch(`../../components/${fileName}`);
        if (!response.ok) return;

        let html = await response.text();

        // header.html 내 {{BASE}} 플레이스홀더를 실제 BASE URL로 치환
        // → 새 페이지가 추가되어도 이 로직은 수정할 필요 없음
        html = html.replaceAll('{{BASE}}', BASE);

        const el = document.getElementById(elementId);
        if (el) el.innerHTML = html;
    } catch (e) {
        console.error('컴포넌트 로드 오류:', e);
    }
}


// ============================================================
// DOMContentLoaded: 헤더·푸터 주입
// ============================================================
document.addEventListener('DOMContentLoaded', () => {
    loadComponent('header-placeholder', 'header.html');
    loadComponent('footer-placeholder', 'footer.html');
});
