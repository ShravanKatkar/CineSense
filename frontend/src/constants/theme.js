export const C = {
  bg: "#1B151F",
  surface: "#251E2A",
  surfaceHigh: "#2E2435",
  accent: "#E3A34E",
  accentDim: "rgba(227,163,78,0.15)",
  teal: "#4F7C74",
  text: "#F2ECE4",
  muted: "#A79AB0",
  border: "#3A2F41",
  borderBright: "#4D3F58",
};

export const PALETTE = [
  "#4F7C74",
  "#9C6B3E",
  "#B0637A",
  "#6C5B8C",
  "#5B7C9C",
  "#7A5C4A",
  "#5C7A5C",
  "#8C5C6C",
];

export const GRAIN_SVG =
  "<svg xmlns='http://www.w3.org/2000/svg' width='120' height='120'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='3' stitchTiles='stitch'/></filter><rect width='100%' height='100%' filter='url(#n)'/></svg>";

export const GRAIN_URI = `url("data:image/svg+xml,${encodeURIComponent(GRAIN_SVG)}")`;

export const STYLES = `
  @import url('https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@600;700;800;900&family=Work+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap');

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: ${C.bg};
    color: ${C.text};
    font-family: 'Work Sans', sans-serif;
    min-height: 100vh;
    overflow-x: hidden;
    -webkit-font-smoothing: antialiased;
  }

  .font-display { font-family: 'Big Shoulders Display', sans-serif; }

  /* ── Scrollbars ── */
  ::-webkit-scrollbar { width: 7px; height: 7px; }
  ::-webkit-scrollbar-track { background: ${C.bg}; }
  ::-webkit-scrollbar-thumb { background: ${C.border}; border-radius: 99px; }
  ::-webkit-scrollbar-thumb:hover { background: ${C.accent}; }
  .no-scrollbar::-webkit-scrollbar { display: none; }
  .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }

  /* ── Film Perforation Strip ── */
  .perf-strip {
    height: 10px;
    background-image: radial-gradient(circle, rgba(0,0,0,0.55) 2.2px, transparent 2.6px);
    background-size: 14px 10px;
    background-repeat: repeat-x;
    background-position: center;
  }

  /* ── Film Grain Overlay ── */
  .grain-overlay {
    position: absolute; inset: 0; pointer-events: none; z-index: 1;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.06'/%3E%3C/svg%3E");
    opacity: 0.35;
    mix-blend-mode: overlay;
  }

  /* ── Animations ── */
  @keyframes heroFade    { from { opacity:0; transform:translateY(16px); } to { opacity:1; transform:translateY(0); } }
  @keyframes slideUp     { from { opacity:0; transform:translateY(24px);} to { opacity:1; transform:translateY(0); } }
  @keyframes slideRight  { from { opacity:0; transform:translateX(-16px);} to { opacity:1; transform:translateX(0); } }
  @keyframes heartPop    { 0%,100% { transform:scale(1); } 40% { transform:scale(1.4); } 70% { transform:scale(0.9); } }
  @keyframes shimmer     { 0% { background-position:-400px 0; } 100% { background-position:400px 0; } }
  @keyframes accentPulse { 0%,100% { opacity:0.6; } 50% { opacity:1; } }
  @keyframes rotateSlow  { from { transform:rotate(0deg); } to { transform:rotate(360deg); } }
  @keyframes scanline    { 0% { top:-100%; } 100% { top:110%; } }
  @keyframes marquee     { 0% { transform:translateX(0); } 100% { transform:translateX(-50%); } }
  @keyframes fadeIn      { from { opacity:0; } to { opacity:1; } }
  @keyframes drawerSlide { from { transform:translateX(100%) scale(0.98); } to { transform:translateX(0) scale(1); } }

  .hero-reveal      { animation: heroFade 0.75s cubic-bezier(0.16,1,0.3,1) both; }
  .slide-up         { animation: slideUp 0.55s cubic-bezier(0.16,1,0.3,1) both; }
  .slide-right      { animation: slideRight 0.55s cubic-bezier(0.16,1,0.3,1) both; }
  .fade-in          { animation: fadeIn 0.4s ease both; }
  .drawer-open      { animation: drawerSlide 0.42s cubic-bezier(0.16,1,0.3,1) both; }

  /* ── Shimmer Skeleton ── */
  .shimmer {
    background: linear-gradient(90deg, ${C.surface} 0%, ${C.surfaceHigh} 50%, ${C.surface} 100%);
    background-size: 400px 100%;
    animation: shimmer 1.4s infinite linear;
  }

  /* ── Movie Card ── */
  .movie-card {
    transition: transform 0.28s cubic-bezier(0.34,1.56,0.64,1), box-shadow 0.28s ease;
    cursor: pointer;
  }
  .movie-card:hover { transform: translateY(-6px) scale(1.018); }
  .movie-card:hover .card-poster { box-shadow: 0 18px 40px -8px rgba(0,0,0,0.7), 0 0 0 1px ${C.borderBright}; }
  .movie-card:hover .card-shine { opacity: 1; }

  .card-poster { position: relative; overflow: hidden; transition: box-shadow 0.28s ease; }
  .card-shine {
    position: absolute; inset: 0; opacity: 0; pointer-events: none; z-index: 2;
    background: linear-gradient(135deg, rgba(255,255,255,0.06) 0%, transparent 60%);
    transition: opacity 0.28s ease;
  }

  /* ── Poster Image Fade ── */
  .poster-img { transition: opacity 0.5s ease, transform 0.4s ease; }
  .movie-card:hover .poster-img { transform: scale(1.04); }

  /* ── Heart Button ── */
  .heart-btn { transition: transform 0.2s ease, background 0.2s ease; }
  .heart-btn:hover { transform: scale(1.15); }
  .heart-btn.liked { animation: heartPop 0.4s cubic-bezier(0.36,0.07,0.19,0.97); }

  /* ── Genre Chip ── */
  .genre-chip {
    position: relative; padding: 3px 10px 3px; border-radius: 2px;
    transition: color 0.2s ease, background 0.2s ease;
    font-size: 0.78rem; letter-spacing: 0.02em;
  }
  .genre-chip::after {
    content:''; position:absolute; bottom:0; left:0; right:0; height:2px;
    background: ${C.accent}; transform:scaleX(0); transform-origin:left;
    transition: transform 0.25s cubic-bezier(0.34,1.56,0.64,1);
  }
  .genre-chip.active::after, .genre-chip:hover::after { transform:scaleX(1); }

  /* ── CTA Button ── */
  .cta-btn {
    position: relative; overflow: hidden;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
  }
  .cta-btn::before {
    content:''; position:absolute; inset:0;
    background: linear-gradient(135deg, rgba(255,255,255,0.15) 0%, transparent 100%);
    opacity:0; transition:opacity 0.25s ease;
  }
  .cta-btn:hover { transform:translateY(-2px); box-shadow:0 8px 24px -4px rgba(227,163,78,0.4); }
  .cta-btn:hover::before { opacity:1; }
  .cta-btn:active { transform:translateY(0); }

  /* ── Ghost Button ── */
  .ghost-btn {
    position:relative; overflow:hidden;
    transition: color 0.2s ease, border-color 0.2s ease, transform 0.2s ease;
  }
  .ghost-btn:hover { transform:translateY(-1px); }

  /* ── Header ── */
  .nav-link {
    position:relative; padding-bottom:4px;
    transition: color 0.2s ease;
  }
  .nav-link::after {
    content:''; position:absolute; bottom:0; left:0; width:100%; height:2px;
    background:${C.accent}; transform:scaleX(0); transform-origin:center;
    transition:transform 0.25s cubic-bezier(0.34,1.56,0.64,1);
  }
  .nav-link.active::after { transform:scaleX(1); }
  .nav-link.active { color:${C.text}; }

  /* ── Logo glow on hover ── */
  .logo:hover .logo-icon { filter: drop-shadow(0 0 6px ${C.accent}); }
  .logo-icon { transition: filter 0.3s ease; }

  /* ── Scanline on Hero Poster ── */
  .scanline-poster::after {
    content:''; position:absolute; left:0; width:100%; height:40%;
    background: linear-gradient(to bottom, transparent, rgba(227,163,78,0.04), transparent);
    animation: scanline 4s ease-in-out infinite;
    pointer-events:none; z-index:3;
  }

  /* ── Accent line decoration ── */
  .accent-line {
    display:inline-block; height:3px; width:32px; background:${C.accent};
    margin-bottom:6px; border-radius:2px;
  }

  /* ── AI Drawer ── */
  .ai-drawer {
    overflow:hidden;
    transition: max-height 0.45s cubic-bezier(0.16,1,0.3,1), opacity 0.3s ease;
  }
  .ai-drawer.open { max-height:260px; opacity:1; }
  .ai-drawer.closed { max-height:0; opacity:0; }

  /* ── Scrolling Ticker ── */
  .ticker-wrap { overflow:hidden; white-space:nowrap; }
  .ticker-inner { display:inline-block; animation: marquee 28s linear infinite; }
  .ticker-inner:hover { animation-play-state:paused; }

  /* ── Range Input ── */
  input[type=range].rating-range {
    -webkit-appearance:none; appearance:none; height:2px; background:#4a3f52; outline:none; cursor:pointer;
  }
  input[type=range].rating-range::-webkit-slider-thumb {
    -webkit-appearance:none; width:14px; height:14px; border-radius:50%;
    background:${C.accent}; cursor:pointer; margin-top:-6px;
    box-shadow:0 0 0 3px rgba(227,163,78,0.2);
    transition: box-shadow 0.2s ease, transform 0.2s ease;
  }
  input[type=range].rating-range::-webkit-slider-thumb:hover {
    box-shadow:0 0 0 5px rgba(227,163,78,0.3); transform:scale(1.1);
  }
  input[type=range].rating-range::-moz-range-thumb {
    width:14px; height:14px; border-radius:50%; background:${C.accent}; border:none; cursor:pointer;
  }

  /* ── Focus ── */
  *:focus-visible { outline:2px solid ${C.accent}; outline-offset:3px; }

  /* ── Star Rating Fill Animation ── */
  @keyframes starFill { 0%{transform:scale(0.5) rotate(-20deg);opacity:0;} 70%{transform:scale(1.3) rotate(5deg);} 100%{transform:scale(1) rotate(0);opacity:1;} }
  .star-pop { animation: starFill 0.35s cubic-bezier(0.36,0.07,0.19,0.97); }

  /* ── Staggered grid cards ── */
  .grid-card { opacity:0; animation: slideUp 0.5s cubic-bezier(0.16,1,0.3,1) forwards; }

  /* ── Ken Burns ── */
  .ken-burns { animation: kenBurns 18s ease-in-out infinite alternate; }
  @keyframes kenBurns { from { transform: scale(1); } to { transform: scale(1.08) translate(-1%, -1%); } }

  /* ── Letter-by-letter Title ── */
  @keyframes letterIn { from { opacity: 0; transform: translateY(14px); } to { opacity: 1; transform: translateY(0); } }

  /* ── Intro Countdown Overlay ── */
  .intro-overlay {
    position: fixed; inset: 0; z-index: 100; background: #08060a;
    animation: irisOut 0.8s ease-in 1.5s forwards;
  }
  .intro-num {
    position: absolute; top: 50%; left: 50%;
    font-family: 'Big Shoulders Display', sans-serif; font-size: 6rem;
    color: ${C.accent}; opacity: 0;
  }
  .intro-num.n3 { animation: numFade 0.5s ease-out 0s forwards; }
  .intro-num.n2 { animation: numFade 0.5s ease-out 0.5s forwards; }
  .intro-num.n1 { animation: numFade 0.5s ease-out 1s forwards; }
  @keyframes numFade {
    0% { opacity: 0; transform: translate(-50%, -50%) scale(1.3); }
    15% { opacity: 1; transform: translate(-50%, -50%) scale(1); }
    85% { opacity: 1; transform: translate(-50%, -50%) scale(1); }
    100% { opacity: 0; transform: translate(-50%, -50%) scale(0.85); }
  }
  @keyframes irisOut {
    from { clip-path: circle(150% at 50% 50%); }
    to { clip-path: circle(0% at 50% 50%); }
  }

  /* ── Fixed Grain Overlay ── */
  .grain-fixed {
    position: fixed; inset: 0; z-index: 70; pointer-events: none;
    opacity: 0.05; mix-blend-mode: overlay; background-repeat: repeat;
    animation: grainShift 1s steps(1) infinite;
  }
  @keyframes grainShift {
    0%,100% { background-position: 0 0; }
    10% { background-position: -3% -1%; } 20% { background-position: 2% 3%; }
    30% { background-position: -2% 2%; } 40% { background-position: 3% -3%; }
    50% { background-position: -3% 3%; } 60% { background-position: 2% -2%; }
    70% { background-position: -2% -3%; } 80% { background-position: 3% 2%; }
    90% { background-position: -3% -2%; }
  }

  /* ── Vignette Overlay ── */
  .vignette-overlay {
    position: fixed; inset: 0; z-index: 69; pointer-events: none;
    background: radial-gradient(ellipse at center, transparent 45%, rgba(10,8,12,0.5) 100%);
  }

  /* ── Spotlight Cursor ── */
  .spotlight {
    position: fixed; top: 0; left: 0;
    width: 260px; height: 260px; margin-left: -130px; margin-top: -130px;
    border-radius: 50%; pointer-events: none; z-index: 65;
    background: radial-gradient(circle, rgba(227,163,78,0.16) 0%, rgba(227,163,78,0.05) 40%, transparent 70%);
    transform: translate(-9999px, -9999px); will-change: transform;
  }
  @media (pointer: coarse) { .spotlight { display: none; } }

  /* ── 3D Card Tilt ── */
  .tilt-card { perspective: 700px; }

  /* ── Drawer poster flip ── */
  .drawer-poster-in { animation: drawerFlip 0.5s ease; }
  @keyframes drawerFlip { from { opacity: 0; transform: rotateY(30deg) scale(0.96); } to { opacity: 1; transform: rotateY(0) scale(1); } }

  @media (prefers-reduced-motion: reduce) {
    *, *::before, *::after { animation:none!important; transition:none!important; }
    .grain-fixed, .spotlight, .intro-overlay { display: none; }
  }
`;
