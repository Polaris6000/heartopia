// 공통 컴포넌트 로더
async function loadComponent(elementId, filePath) {
    try {
        const response = await fetch(filePath);
        if (!response.ok) throw new Error(`${filePath} 로드 실패`);
        const html = await response.text();
        document.getElementById(elementId).innerHTML = html;
    } catch (error) {
        console.error('컴포넌트 로드 오류:', error);
    }
}

// 페이지 로드 시 실행
document.addEventListener('DOMContentLoaded', function() {
    const path = window.location.pathname;

    // 컴포넌트 파일 경로 자동 설정
    let componentBase;

    if (path.includes('/pages/fish/')) {
        // fish 폴더: src/pages/fish/
        componentBase = '../../components/';
    } else if (path.includes('/pages/')) {
        // 기타 pages 폴더: src/pages/
        componentBase = '../components/';
    } else {
        // 루트 (index.html)
        componentBase = './src/components/';
    }

    loadComponent('header-placeholder', componentBase + 'header.html');
    loadComponent('footer-placeholder', componentBase + 'footer.html');
});