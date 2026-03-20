'use client';

import React from 'react';

interface GradientButtonProps {
  children: React.ReactNode;
  variant?: 'primary' | 'secondary';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  onClick?: () => void;
  href?: string;
}

export function GradientButton({
  children,
  variant = 'primary',
  size = 'md',
  className = '',
  onClick,
  href,
}: GradientButtonProps) {
  const baseStyles = 'inline-flex items-center justify-center font-bold rounded-2xl transition-all duration-300 hover:scale-[1.02]';
  
  const variantStyles = {
    primary: 'btn-primary text-white shadow-lg shadow-primary/25',
    secondary: 'btn-secondary text-white shadow-lg shadow-secondary/25',
  };
  
  const sizeStyles = {
    sm: 'px-5 py-2.5 text-sm',
    md: 'px-7 py-3.5 text-base',
    lg: 'px-8 py-4 text-lg',
  };

  const combinedClassName = `${baseStyles} ${variantStyles[variant]} ${sizeStyles[size]} ${className}`;

  if (href) {
    return (
      <a href={href} className={combinedClassName}>
        {children}
      </a>
    );
  }

  return (
    <button onClick={onClick} className={combinedClassName}>
      {children}
    </button>
  );
}
