import React, { useRef, useState, useEffect } from 'react';

export function LandingCard3D() {
    const cardRef = useRef<HTMLDivElement>(null);
    const [rotation, setRotation] = useState({ x: 0, y: 0 });

    const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
        if (!cardRef.current) return;
        const rect = cardRef.current.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;
        
        const rotateY = ((x - centerX) / centerX) * 10;
        const rotateX = ((centerY - y) / centerY) * 10;
        
        setRotation({ x: rotateX, y: rotateY });
    };

    const handleMouseLeave = () => {
        setRotation({ x: 0, y: 0 });
    };

    return (
        <div className="hero-visual flex-0-0-auto flex justify-center items-center relative z-10">
            <div className="scene relative w-[370px] h-[420px] perspective-[1200px]">
                <div 
                    ref={cardRef}
                    className="card-3d w-full h-full relative transition-transform duration-200 ease-out"
                    style={{ 
                        transformStyle: 'preserve-3d',
                        transform: `rotateX(${rotation.x}deg) rotateY(${rotation.y}deg)`,
                        animation: rotation.x === 0 && rotation.y === 0 ? 'float3d 6s ease-in-out infinite' : 'none'
                    }}
                    onMouseMove={handleMouseMove}
                    onMouseLeave={handleMouseLeave}
                >
                    <div className="card-face absolute inset-0 bg-gradient-to-br rounded-[22px] border p-7 overflow-hidden transition-all" style={{ background: 'linear-gradient(135deg, var(--surface) 0%, var(--bg2) 100%)', borderColor: 'var(--border)', boxShadow: '0 25px 50px -12px rgba(0,0,0,0.5)' }}>
                        {/* Highlights */}
                        <div className="absolute -top-[50px] -right-[50px] w-[180px] h-[180px] bg-[radial-gradient(circle,rgba(16,185,129,0.12)_0%,transparent_70%)] pointer-events-none" />
                        <div className="absolute -bottom-[30px] -left-[30px] w-[160px] h-[160px] bg-[radial-gradient(circle,rgba(77,122,255,0.1)_0%,transparent_70%)] pointer-events-none" />

                        {/* Content */}
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="font-['Syne'] text-lg font-bold text-[var(--text)]">Tax summary 2024</h3>
                             <div className="w-8 h-8 rounded-full flex items-center justify-center border" style={{ background: 'var(--bg)', borderColor: 'var(--border)' }}>
                                <span className="text-[var(--text3)] text-xs opacity-40">•••</span>
                             </div>
                        </div>

                        <div className="mb-6">
                            <div className="text-[var(--text3)] text-xs uppercase tracking-wider mb-1 font-bold">Total Liability</div>
                            <div className="font-['Syne'] text-4xl font-black text-[var(--text)] tracking-tight">$12,840</div>
                            <div className="flex items-center gap-2 mt-1">
                                <span className="w-2 h-2 rounded-full bg-brand-green-500"></span>
                                <span className="text-[var(--text2)] text-xs font-medium">Due Apr 15, 2025</span>
                            </div>
                        </div>

                        <div className="space-y-4">
                            <div className="flex justify-between items-center bg-white/5 rounded-xl p-3 border" style={{ background: 'var(--bg2)', borderColor: 'var(--border)' }}>
                                <div className="flex items-center gap-3">
                                    <div className="w-2 h-2 rounded-full bg-brand-green-500"></div>
                                    <span className="text-xs font-semibold text-[var(--text2)]">Short-term gains</span>
                                </div>
                                <span className="text-xs font-bold text-[var(--text)]">$8,210</span>
                            </div>
                            <div className="flex justify-between items-center bg-white/5 rounded-xl p-3 border" style={{ background: 'var(--bg2)', borderColor: 'var(--border)' }}>
                                <div className="flex items-center gap-3">
                                    <div className="w-2 h-2 rounded-full bg-brand-blue-500"></div>
                                    <span className="text-xs font-semibold text-[var(--text2)]">Long-term gains</span>
                                </div>
                                <span className="text-xs font-bold text-[var(--text)]">$5,480</span>
                            </div>
                        </div>

                        <div className="mt-8">
                            <div className="h-1.5 w-full rounded-full overflow-hidden flex border" style={{ background: 'var(--bg)', borderColor: 'var(--border)' }}>
                                <div className="h-full bg-brand-green-500 shadow-[0_0_8px_var(--accent)]" style={{ width: '60%' }}></div>
                                <div className="h-full bg-brand-blue-500 shadow-[0_0_8px_var(--accent2)]" style={{ width: '40%' }}></div>
                            </div>
                        </div>
                    </div>

                    {/* Floating chips */}
                    <div className="float-chip float-chip-1 absolute top-0 -left-[80px] bg-[var(--surface)] border border-[var(--border)] rounded-[12px] p-2.5 flex items-center gap-2.5 shadow-2xl backdrop-blur-md animate-[chipfloat_5s_ease-in-out_infinite] z-20">
                        <div className="chip-icon green w-[30px] h-[30px] rounded-lg bg-brand-green-500/15 flex items-center justify-center text-sm">₿</div>
                        <div className="chip-text">
                            <div className="chip-label text-[10px] text-[var(--text3)] uppercase font-bold">BTC GAIN</div>
                            <div className="chip-val font-['Syne'] text-sm font-bold text-[var(--text)]">+$18,420</div>
                        </div>
                    </div>

                    <div className="float-chip float-chip-2 absolute bottom-[50px] -right-[80px] bg-[var(--surface)] border border-[var(--border)] rounded-[12px] p-2.5 flex items-center gap-2.5 shadow-2xl backdrop-blur-md animate-[chipfloat_5s_ease-in-out_infinite_delay-1500ms] z-20">
                        <div className="chip-icon blue w-[30px] h-[30px] rounded-lg bg-brand-blue-500/15 flex items-center justify-center text-sm">Ξ</div>
                        <div className="chip-text">
                            <div className="chip-label text-[10px] text-[var(--text3)] uppercase font-bold">ETH LOSS</div>
                            <div className="chip-val font-['Syne'] text-sm font-bold text-[var(--text)]">-$3,240</div>
                        </div>
                    </div>
                </div>

                {/* Background Orbs */}
                <div className="orb orb-1 absolute w-[280px] h-[280px] rounded-full blur-[40px] pointer-events-none -top-[50px] -right-[60px] bg-[radial-gradient(circle,rgba(16,185,129,0.16)_0%,transparent_70%)]" />
                <div className="orb orb-2 absolute w-[280px] h-[280px] rounded-full blur-[40px] pointer-events-none -bottom-[30px] -left-[40px] bg-[radial-gradient(circle,rgba(77,122,255,0.16)_0%,transparent_70%)]" />
            </div>
        </div>
    );
}
