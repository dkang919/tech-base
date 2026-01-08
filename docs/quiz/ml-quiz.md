# 🧠 Repeat Threepeat

<div class="flashcard-container">
    <div class="card-wrapper" onclick="flipCard()">
        <div class="card" id="flashcard">
            <div class="card-face card-front">
                <div class="card-content">
                    <span class="category-badge" id="category-badge">Topic</span>
                    <span class="label">QUESTION</span>
                    <h3 id="question-text">Loading questions...</h3>
                    <p class="hint">(Click to flip)</p>
                </div>
            </div>
            <div class="card-face card-back">
                <div class="card-content">
                    <span class="label">ANSWER</span>
                    <p id="answer-text">Loading answers...</p>
                </div>
            </div>
        </div>
    </div>

    <div class="controls">
        <button class="btn" onclick="prevCard()">← Prev</button>
        <span id="counter">0 / 0</span>
        <button class="btn" onclick="nextCard()">Next →</button>
    </div>
</div>

<style>
    .flashcard-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        margin-top: 40px;
        perspective: 1000px;
    }
    .card-wrapper {
        width: 100%;
        max-width: 600px;
        height: 350px; /* 영어 텍스트 길이에 맞춰 높이 조정 */
        cursor: pointer;
        position: relative;
    }
    .card {
        width: 100%;
        height: 100%;
        position: relative;
        transform-style: preserve-3d;
        transition: transform 0.6s cubic-bezier(0.4, 0.2, 0.2, 1);
        border-radius: 15px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    .card.is-flipped { transform: rotateY(180deg); }
    .card-face {
        position: absolute;
        width: 100%;
        height: 100%;
        backface-visibility: hidden;
        border-radius: 15px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 30px;
        box-sizing: border-box;
        border: 1px solid #e0e0e0;
    }
    .card-front { background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%); color: #333; }
    .card-back { 
        background: linear-gradient(135deg, #2563EB 0%, #1E40AF 100%); /* Tech Blue */
        color: white; 
        transform: rotateY(180deg); 
    }
    
    /* 텍스트 스타일 */
    .card-content h3 { margin: 15px 0; font-size: 1.5rem; line-height: 1.4; }
    .card-content p { font-size: 1.15rem; line-height: 1.6; }
    
    .label {
        font-size: 0.75rem; text-transform: uppercase; letter-spacing: 2px; opacity: 0.6;
    }
    .category-badge {
        background: #eee; color: #555; padding: 4px 10px; border-radius: 20px;
        font-size: 0.8rem; font-weight: bold; margin-bottom: 10px; display: inline-block;
    }
    .card-back .label { opacity: 0.8; margin-bottom: 10px; }
    .hint { font-size: 0.8rem !important; color: #888; margin-top: auto !important; }

    /* 버튼 */
    .controls { margin-top: 30px; display: flex; align-items: center; gap: 20px; }
    .btn {
        padding: 10px 20px; border: none; background: #333; color: white;
        border-radius: 30px; cursor: pointer; font-weight: bold; transition: transform 0.2s;
    }
    .btn:hover { transform: scale(1.05); background: #555; }
    #counter { font-weight: bold; color: #555; }
</style>

<script>
    let quizData = [];
    let currentIdx = 0;
    
    const card = document.getElementById('flashcard');
    const qText = document.getElementById('question-text');
    const aText = document.getElementById('answer-text');
    const badge = document.getElementById('category-badge');
    const counter = document.getElementById('counter');

    // 🔀 셔플 알고리즘 (Fisher-Yates Shuffle)
    function shuffleArray(array) {
        for (let i = array.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [array[i], array[j]] = [array[j], array[i]]; // 두 요소를 맞바꿈
        }
    }

    async function loadQuizData() {
        try {
            // 상위 폴더로 나가서 data 찾기
            const response = await fetch('../data/ml_quiz.json');
            if (!response.ok) throw new Error("File not found");
            
            quizData = await response.json();
            
            // [핵심] 데이터 로드 직후에 무작위로 섞어버림
            shuffleArray(quizData);
            
            renderCard();
        } catch (error) {
            console.error("Load failed:", error);
            qText.innerText = "Error loading questions.\nPlease check console.";
        }
    }

    function renderCard() {
        if (quizData.length === 0) return;

        card.classList.remove('is-flipped');
        
        setTimeout(() => {
            const item = quizData[currentIdx];
            qText.innerHTML = item.q;
            aText.innerHTML = item.a;
            badge.innerText = item.category;
            counter.innerText = `${currentIdx + 1} / ${quizData.length}`;
        }, 200);
    }

    function flipCard() { card.classList.toggle('is-flipped'); }

    function nextCard() {
        if (currentIdx < quizData.length - 1) {
            currentIdx++;
            renderCard();
        } else {
            // 끝까지 가면 다시 섞어서 처음부터 시작 (무한 루프)
            if(confirm("모든 문제를 다 풀었습니다! 다시 섞어서 시작할까요?")) {
                shuffleArray(quizData);
                currentIdx = 0;
                renderCard();
            }
        }
    }

    function prevCard() {
        if (currentIdx > 0) {
            currentIdx--;
            renderCard();
        }
    }

    loadQuizData();
</script>