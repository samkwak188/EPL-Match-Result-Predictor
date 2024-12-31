document.addEventListener('DOMContentLoaded', function() {
    const images = [
        '/static/images/football1.jpg',
        '/static/images/football2.jpg',
        '/static/images/football3.jpg',
        '/static/images/football4.jpg',
        '/static/images/football5.jpg'
    ];

    const backgroundSlideshow = document.querySelector('.background-slideshow');
    
    // Create image elements
    images.forEach((src, index) => {
        const img = document.createElement('div');
        img.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: url(${src}) center center/cover no-repeat;
            animation: backgroundSlideshow 20s linear infinite;
            animation-delay: ${index * 4}s;
            opacity: 0;
        `;
        backgroundSlideshow.appendChild(img);
    });
}); 