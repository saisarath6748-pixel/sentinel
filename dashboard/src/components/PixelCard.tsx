"use client";

import React, { useEffect, useRef } from 'react';

interface PixelCardProps {
  className?: string;
  colors?: string; // Comma separated colors
  gap?: number;
  speed?: number;
  noFocus?: boolean;
}

const PixelCard: React.FC<React.PropsWithChildren<PixelCardProps>> = ({
  className = '',
  colors = '#0D94FB,#012652,#EBF5FF',
  gap = 5,
  speed = 35,
  noFocus = false,
  children
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let width = 0;
    let height = 0;
    let pixels: { x: number; y: number; color: string; speed: number; opacity: number }[] = [];

    const colorArray = colors.split(',');

    const initPixels = () => {
      pixels = [];
      const cols = Math.floor(width / gap);
      const rows = Math.floor(height / gap);
      for (let i = 0; i < cols; i++) {
        for (let j = 0; j < rows; j++) {
          if (Math.random() > 0.9) {
            pixels.push({
              x: i * gap,
              y: j * gap,
              color: colorArray[Math.floor(Math.random() * colorArray.length)],
              speed: (Math.random() * speed) / 100 + 0.01,
              opacity: Math.random()
            });
          }
        }
      }
    };

    const handleResize = () => {
      const rect = container.getBoundingClientRect();
      width = rect.width;
      height = rect.height;
      canvas.width = width;
      canvas.height = height;
      initPixels();
    };

    const draw = () => {
      ctx.clearRect(0, 0, width, height);
      pixels.forEach(p => {
        p.opacity += p.speed;
        if (p.opacity > 1 || p.opacity < 0) {
          p.speed *= -1;
        }
        ctx.fillStyle = p.color;
        ctx.globalAlpha = Math.max(0, Math.min(1, p.opacity));
        ctx.fillRect(p.x, p.y, gap * 0.8, gap * 0.8);
      });
      ctx.globalAlpha = 1;
      animationFrameId = requestAnimationFrame(draw);
    };

    handleResize();
    const observer = new ResizeObserver(handleResize);
    observer.observe(container);

    draw();

    return () => {
      cancelAnimationFrame(animationFrameId);
      observer.disconnect();
    };
  }, [colors, gap, speed]);

  return (
    <div
      ref={containerRef}
      className={`relative overflow-hidden rounded-2xl border border-white/20 shadow-xl bg-white/5 backdrop-blur-md group ${className}`}
    >
      <canvas
        ref={canvasRef}
        className={`absolute inset-0 z-0 transition-opacity duration-500 ${
          noFocus ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'
        }`}
      />
      <div className="relative z-10 h-full">{children}</div>
    </div>
  );
};

export default PixelCard;
