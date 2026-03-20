/**
 * Calming Interactive Starfield
 * Creates a serene starfield background that responds to mouse gestures
 */

class Starfield {
    constructor(canvas, options = {}) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        
        // Configuration
        this.starCount = options.starCount || 200;
        this.starSpeed = options.starSpeed || 0.02;
        this.mouseInfluence = options.mouseInfluence || 0.05;
        this.fadeSpeed = options.fadeSpeed || 0.005;
        
        // Mouse state
        this.mouseX = window.innerWidth / 2;
        this.mouseY = window.innerHeight / 2;
        this.targetMouseX = this.mouseX;
        this.targetMouseY = this.mouseY;
        
        // Stars array
        this.stars = [];
        
        // Initialize
        this.resize();
        this.createStars();
        this.bindEvents();
        this.animate();
    }
    
    createStars() {
        this.stars = [];
        for (let i = 0; i < this.starCount; i++) {
            this.stars.push(this.createStar());
        }
    }
    
    createStar() {
        const x = Math.random() * this.canvas.width;
        const y = Math.random() * this.canvas.height;
        const z = Math.random() * this.canvas.width; // Depth
        
        return {
            x: x,
            y: y,
            z: z,
            originalX: x,
            originalY: y,
            size: Math.random() * 1.5 + 0.5,
            brightness: Math.random(),
            twinkleSpeed: Math.random() * 0.02 + 0.01,
            twinklePhase: Math.random() * Math.PI * 2,
            color: this.getStarColor()
        };
    }
    
    getStarColor() {
        // Mix of warm white, cool white, and slight blue/yellow tints
        const colors = [
            '255, 255, 255',      // Pure white
            '255, 254, 228',      // Warm white
            '224, 247, 255',      // Cool blue-white
            '255, 248, 220',      // Cream
            '200, 220, 255',      // Slight blue
        ];
        return colors[Math.floor(Math.random() * colors.length)];
    }
    
    resize() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    }
    
    bindEvents() {
        window.addEventListener('resize', () => this.resize());
        
        // Track mouse position with smooth interpolation
        window.addEventListener('mousemove', (e) => {
            this.targetMouseX = e.clientX;
            this.targetMouseY = e.clientY;
        });
        
        // Handle touch for mobile
        window.addEventListener('touchmove', (e) => {
            if (e.touches.length > 0) {
                this.targetMouseX = e.touches[0].clientX;
                this.targetMouseY = e.touches[0].clientY;
            }
        });
    }
    
    update() {
        // Smooth mouse interpolation
        this.mouseX += (this.targetMouseX - this.mouseX) * this.mouseInfluence;
        this.mouseY += (this.targetMouseY - this.mouseY) * this.mouseInfluence;
        
        // Calculate mouse offset from center
        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height / 2;
        const mouseOffsetX = (this.mouseX - centerX) / centerX;
        const mouseOffsetY = (this.mouseY - centerY) / centerY;
        
        this.stars.forEach(star => {
            // Update twinkle
            star.twinklePhase += star.twinkleSpeed;
            
            // Apply depth-based movement (parallax effect)
            const depthFactor = star.z / this.canvas.width;
            
            // Calculate star position with mouse influence
            star.x = star.originalX - (mouseOffsetX * 50 * depthFactor);
            star.y = star.originalY - (mouseOffsetY * 50 * depthFactor);
            
            // Wrap around screen
            if (star.x < 0) star.x += this.canvas.width;
            if (star.x > this.canvas.width) star.x -= this.canvas.width;
            if (star.y < 0) star.y += this.canvas.height;
            if (star.y > this.canvas.height) star.y -= this.canvas.height;
            
            // Slow drift for more dynamism
            star.originalX += Math.sin(star.twinklePhase * 0.5) * 0.1;
            star.originalY += Math.cos(star.twinklePhase * 0.3) * 0.1;
        });
    }
    
    draw() {
        // Clear with slight fade for smooth animation
        this.ctx.fillStyle = 'rgba(9, 10, 15, 0.3)';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        this.stars.forEach(star => {
            // Calculate brightness with twinkle
            const twinkle = (Math.sin(star.twinklePhase) + 1) / 2;
            const alpha = 0.3 + (twinkle * 0.7);
            
            // Size based on depth
            const size = star.size * (star.z / this.canvas.width) * 2;
            
            // Draw star
            this.ctx.beginPath();
            this.ctx.arc(star.x, star.y, size, 0, Math.PI * 2);
            this.ctx.fillStyle = `rgba(${star.color}, ${alpha})`;
            this.ctx.fill();
            
            // Add glow for larger stars
            if (size > 1.5) {
                this.ctx.beginPath();
                this.ctx.arc(star.x, star.y, size * 2, 0, Math.PI * 2);
                const gradient = this.ctx.createRadialGradient(
                    star.x, star.y, 0,
                    star.x, star.y, size * 2
                );
                gradient.addColorStop(0, `rgba(${star.color}, ${alpha * 0.3})`);
                gradient.addColorStop(1, `rgba(${star.color}, 0)`);
                this.ctx.fillStyle = gradient;
                this.ctx.fill();
            }
        });
    }
    
    animate() {
        this.update();
        this.draw();
        requestAnimationFrame(() => this.animate());
    }
}

// Initialize starfield when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('starfield-canvas');
    if (canvas) {
        new Starfield(canvas, {
            starCount: 200,
            starSpeed: 0.02,
            mouseInfluence: 0.08,
            fadeSpeed: 0.005
        });
    }
});
