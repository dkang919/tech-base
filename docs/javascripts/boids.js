// docs/javascripts/boids.js

document.addEventListener("DOMContentLoaded", function () {
    // 1. 메인 페이지인지 확인 (URL이 / 또는 /tech-base/ 로 끝나는지)
    // 주의: 로컬 테스트와 배포 환경(GitHub Pages) 경로를 모두 고려해야 함
    const path = window.location.pathname;
    const isHome = path === "/" || path === "/tech-base/" || path.endsWith("/index.html");

    // 메인 페이지가 아니면 실행하지 않음 (원한다면 이 부분을 지워서 모든 페이지에 적용 가능)
    if (!isHome) return;

    // 2. 캔버스 생성 및 스타일 설정 (배경으로 깔기 위한 설정)
    const canvas = document.createElement('canvas');
    canvas.id = 'boidCanvas';
    canvas.style.position = 'fixed'; // 화면에 고정
    canvas.style.top = '0';
    canvas.style.left = '0';
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    canvas.style.zIndex = '-1'; // 글씨 뒤로 보내기
    canvas.style.pointerEvents = 'none'; // 마우스 클릭이 캔버스를 통과해 글씨에 닿게 함
    
    // 배경색 설정 (사용자가 원한 심해 색상)
    // MkDocs 테마 배경을 덮어쓰기 위해 캔버스 뒤 body 배경색도 조정 필요할 수 있음
    document.body.style.backgroundColor = "#0d1b2a"; 
    
    document.body.appendChild(canvas);

    const ctx = canvas.getContext('2d');

    // --- 기존 로직 시작 ---
    let width = canvas.width = window.innerWidth;
    let height = canvas.height = window.innerHeight;

    let mouse = { x: null, y: null };

    window.addEventListener('mousemove', function(e) {
        mouse.x = e.x;
        mouse.y = e.y;
    });

    window.addEventListener('mouseout', function() {
        mouse.x = null;
        mouse.y = null;
    });

    window.addEventListener('resize', function() {
        width = canvas.width = window.innerWidth;
        height = canvas.height = window.innerHeight;
    });

    const CONFIG = {
        count: 100,           // 마릿수 조절 (배경이니 너무 많으면 산만할 수 있음)
        visualRange: 100,
        speedLimit: 1,
        separationFactor: 0.05,
        alignmentFactor: 0.005,
        cohesionFactor: 0.005,
        mouseRepelDist: 150,
        mouseRepelForce: 0.05,
    };

    class Boid {
        constructor() {
            this.x = Math.random() * width;
            this.y = Math.random() * height;
            this.dx = (Math.random() - 0.5) * 4; 
            this.dy = (Math.random() - 0.5) * 4;
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

            if (mouse.x !== null) {
                let distMouse = Math.hypot(this.x - mouse.x, this.y - mouse.y);
                if (distMouse < CONFIG.mouseRepelDist) {
                    let repelDx = this.x - mouse.x;
                    let repelDy = this.y - mouse.y;
                    this.dx += repelDx * CONFIG.mouseRepelForce;
                    this.dy += repelDy * CONFIG.mouseRepelForce;
                }
            }

            let speed = Math.hypot(this.dx, this.dy);
            if (speed > CONFIG.speedLimit) {
                this.dx = (this.dx / speed) * CONFIG.speedLimit;
                this.dy = (this.dy / speed) * CONFIG.speedLimit;
            }

            this.x += this.dx;
            this.y += this.dy;

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
            
            // 색상: 배경이 어두우므로 약간 밝게 조정
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
        // 배경을 지울 때 투명도를 주어 잔상 효과를 줄 수도 있음, 여기선 완전 삭제
        ctx.clearRect(0, 0, width, height); 
        
        for (let boid of boids) {
            boid.update(boids);
            boid.draw();
        }
        requestAnimationFrame(animate);
    }

    animate();
});