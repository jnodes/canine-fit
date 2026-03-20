'use client';

import React from 'react';
import { LucideIcon } from 'lucide-react';

interface StatsCardProps {
  icon: LucideIcon;
  label: string;
  value: string;
  color?: string;
}

export function StatsCard({ icon: Icon, label, value, color = '#FF6B00' }: StatsCardProps) {
  return (
    <div className="flex-1 bg-card rounded-2xl p-4 text-center border border-border/50">
      <div 
        className="w-10 h-10 rounded-xl flex items-center justify-center mx-auto mb-3"
        style={{ backgroundColor: `${color}20` }}
      >
        <Icon size={20} style={{ color }} />
      </div>
      <p className="text-white font-bold text-base mb-1">{value}</p>
      <p className="text-text-secondary text-xs">{label}</p>
    </div>
  );
}
