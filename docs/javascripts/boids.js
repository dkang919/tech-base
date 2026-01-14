// docs/javascripts/boids.js

document.addEventListener("DOMContentLoaded", function () {
    // 1. 메인 페이지인지 확인
    const path = window.location.pathname;
    const isHome = path === "/" || path === "/tech-base/" || path.endsWith("/index.html");

    // 메인 페이지가 아니면 실행하지 않음
    if (!isHome) return;

    // 중복 실행 방지 (이미 캔버스가 존재하면 중단)
    if (document.getElementById('boidCanvas')) return;

    // 2. 캔버스 생성 및 스타일 설정
    const canvas = document.createElement('canvas');
    canvas.id = 'boidCanvas';
    canvas.style.position = 'fixed'; 
    canvas.style.top = '0';
    canvas.style.left = '0';
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    canvas.style.zIndex = '-1'; 
    canvas.style.pointerEvents = 'none'; 
    
    // 심해 배경색 설정
    document.body.style.backgroundColor = "#0d1b2a"; 
    document.body.appendChild(canvas);

    const ctx = canvas.getContext('2d');

    // 캔버스 크기 초기화
    let width = canvas.width = window.innerWidth;
    let height = canvas.height = window.innerHeight;

    let mouse = { x: null, y: null };

    // 이벤트 리스너
    window.addEventListener('mousemove', (e) => {
        mouse.x = e.x;
        mouse.y = e.y;
    });

    window.addEventListener('mouseout', () => {
        mouse.x = null;
        mouse.y = null;
    });

    window.addEventListener('resize', () => {
        width = canvas.width = window.innerWidth;
        height = canvas.height = window.innerHeight;
    });

    // --- 최적화된 설정값 (Sea of Iteration 테마) ---
    const CONFIG = {
        count: 180,               // 마릿수
        visualRange: 100,        // 인식 거리
        speedLimit: 0.6,         // 최대 속도 (느릿하고 우아하게)
        separationFactor: 0.03,  // 서로 밀어내는 힘
        alignmentFactor: 0.001,  // 일관성 (낮을수록 방향 전환이 부드러움)
        cohesionFactor: 0.001,   // 응집력 (낮을수록 유유자적함)
        mouseRepelDist: 150,     // 마우스 회피 거리
        mouseRepelForce: 0.02,   // 마우스 회피 힘
    };

    class Boid {
        constructor() {
            this.x = Math.random() * width;
            this.y = Math.random() * height;
            this.dx = (Math.random() - 0.5) * 2; 
            this.dy = (Math.random() - 0.5) * 2;
        }

        update(boids) {
            let separationX = 0, separationY = 0;
            let alignmentX = 0, alignmentY = 0;
            let cohesionX = 0, cohesionY = 0;
            let neighbors = 0;
            let centerX = 0, centerY = 0;

            for (let other of boids) {
                if (other === this) continue;
                let dist = Math.hypot(this.x - other.x, this.y - other.y);
                if (dist < CONFIG.visualRange) {
                    if (dist < 20) { 
                        separationX += this.x - other.x;
                        separationY += this.y - other.y;
                    }
                    alignmentX += other.dx;
                    alignmentY += other.dy;
                    centerX += other.x;
                    centerY += other.y;
                    neighbors++;
                }
            }

            if (neighbors > 0) {
                alignmentX /= neighbors;
                alignmentY /= neighbors;
                this.dx += (alignmentX - this.dx) * CONFIG.alignmentFactor;
                this.dy += (alignmentY - this.dy) * CONFIG.alignmentFactor;
                centerX /= neighbors;
                centerY /= neighbors;
                this.dx += (centerX - this.x) * CONFIG.cohesionFactor;
                this.dy += (centerY - this.y) * CONFIG.cohesionFactor;
            }

            this.dx += separationX * CONFIG.separationFactor;
            this.dy += separationY * CONFIG.separationFactor;

            // 마우스 상호작용
            if (mouse.x !== null) {
                let distMouse = Math.hypot(this.x - mouse.x, this.y - mouse.y);
                if (distMouse < CONFIG.mouseRepelDist) {
                    let repelDx = this.x - mouse.x;
                    let repelDy = this.y - mouse.y;
                    this.dx += repelDx * CONFIG.mouseRepelForce;
                    this.dy += repelDy * CONFIG.mouseRepelForce;
                }
            }

            // 속도 제한
            let speed = Math.hypot(this.dx, this.dy);
            if (speed > CONFIG.speedLimit) {
                this.dx = (this.dx / speed) * CONFIG.speedLimit;
                this.dy = (this.dy / speed) * CONFIG.speedLimit;
            }

            this.x += this.dx;
            this.y += this.dy;

            // 화면 경계 처리 (Wrapping)
            if (this.x > width) this.x = 0;
            if (this.x < 0) this.x = width;
            if (this.y > height) this.y = 0;
            if (this.y < 0) this.y = height;
        }

        draw() {
            let angle = Math.atan2(this.dy, this.dx);
            ctx.save();
            ctx.translate(this.x, this.y);
            ctx.rotate(angle);
            ctx.beginPath();
            ctx.moveTo(10, 0);
            ctx.lineTo(-5, 5);
            ctx.lineTo(-5, -5);
            ctx.lineTo(10, 0);
            
            // 색상: 데이터 과학의 신뢰감을 주는 스카이블루 톤
            ctx.fillStyle = `rgba(100, 200, 255, 0.6)`; 
            ctx.fill();
            ctx.restore();
        }
    }

    const boids = [];
    for (let i = 0; i < CONFIG.count; i++) {
        boids.push(new Boid());
    }

    function animate() {
        // 캔버스 크기를 직접 참조하여 잔상 방지 및 전체 클리어
        ctx.clearRect(0, 0, canvas.width, canvas.height); 
        
        for (let boid of boids) {
            boid.update(boids);
            boid.draw();
        }
        requestAnimationFrame(animate);
    }

    animate();
});