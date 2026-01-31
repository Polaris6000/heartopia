// 공통 컴포넌트 로더
async function loadComponent(elementId, fileName) {
    try {
        // 경로 계산 생략하고 루트(/) 기준으로 고정
        const response = await fetch(`../../components/${fileName}`);
        if (!response.ok) return; // 실패하면 조용히 종료 (불필요한 에러 노출 방지)

        const html = await response.text();
        const el = document.getElementById(elementId);
        if (el) el.innerHTML = html;
    } catch (e) {
        console.error('컴포넌트 로드 오류:', e);
    }
}

// DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
    loadComponent('header-placeholder', 'header.html');
    loadComponent('footer-placeholder', 'footer.html');
});