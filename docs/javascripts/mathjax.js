// docs/javascripts/mathjax.js
//
// MathJax 3 설정.
// mkdocs.yml의 extra_javascript가 이 파일을 참조하고 있었지만 파일이 없어서
// 모든 페이지에서 404가 발생하고 있었음 (2026-08-09 추가).
//
// pymdownx.arithmatex(generic: true)는 수식을 \(...\) / \[...\] 로 출력하고
// .arithmatex 클래스를 붙여준다. 아래 설정은 그 규약에 맞춘 것.

window.MathJax = {
    tex: {
        inlineMath: [["\\(", "\\)"]],
        displayMath: [["\\[", "\\]"]],
        processEscapes: true,
        processEnvironments: true
    },
    options: {
        // Why: 기본값은 문서 전체를 훑기 때문에 코드 블록 안의 $ 기호를
        //      수식으로 오인할 수 있다. arithmatex가 표시한 부분만 처리하도록 제한.
        ignoreHtmlClass: ".*|",
        processHtmlClass: "arithmatex"
    }
};
