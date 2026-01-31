/**
 * 공통 컴포넌트 로더
 * @param {string} elementId - HTML을 삽입할 요소의 ID
 * @param {string} fileName - 불러올 파일 이름 (예: 'header.html')
 */
async function loadComponent(elementId, fileName) {
    try {
        // 닷홈 환경에서는 /heartopia/를 포함해야 루트(/)부터 제대로 찾아감.
        // 만약 로컬과 서버 모두 대응하고 싶다면 상대 경로인 '../components/'가 나을 수도 있음.
        const path = `/heartopia/src/components/${fileName}`;

        const response = await fetch(path);

        if (!response.ok) {
            // 실패했을 때 이유를 출력. (공부용)
            throw new Error(`파일 로드 실패! 상태 코드: ${response.status} (경로: ${path})`);
        }

        const html = await response.text();
        const el = document.getElementById(elementId);

        if (el) {
            el.innerHTML = html;
            console.log(`${fileName} 로드 완료!`);
        } else {
            console.warn(`ID가 '${elementId}'인 요소를 찾을 수 없어 '${fileName}'을 넣지 못했습니다.`);
        }
    } catch (e) {
        console.error('컴포넌트 로드 중 오류 발생:', e);
    }
}

// 페이지가 로드되면 실행
document.addEventListener('DOMContentLoaded', () => {
    // 여기서 첫 번째 인자는 HTML에 만든 id값, 두 번째는 실제 파일 이름.
    loadComponent('header-placeholder', 'header.html');
    loadComponent('footer-placeholder', 'footer.html');
});