import React, { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { Search, ChevronRight, Clock, User, ArrowRight, Mail, Sun, Moon } from 'lucide-react';
import { BLOG_POSTS, BlogPost } from '../data/blogPosts';
import { ThemeToggle } from '../components/ThemeToggle';
import { LanguageSwitcher } from '../components/LanguageSwitcher';

export function BlogPage() {
  const [activeCategory, setActiveCategory] = useState('All');
  const [visibleCount, setVisibleCount] = useState(6);

  const categories = ['All', ...Array.from(new Set(BLOG_POSTS.map(post => post.category)))];

  const filteredPosts = useMemo(() => {
    return activeCategory === 'All' 
      ? BLOG_POSTS 
      : BLOG_POSTS.filter(post => post.category === activeCategory);
  }, [activeCategory]);

  const featuredPost = BLOG_POSTS[0]; // First one is featured
  const gridPosts = filteredPosts.slice(0, visibleCount);

  return (
    <div className="min-h-screen bg-[var(--bg)] text-[var(--text)] transition-colors duration-300">
      {/* Navigation (Simplified from HomePage) */}
      <nav className="fixed top-0 left-0 right-0 z-[100] flex items-center justify-between px-6 md:px-12 py-4 bg-[var(--nav-bg)] backdrop-blur-xl border-b border-[var(--border)]">
        <Link to="/" className="logo flex items-center gap-2 text-[var(--text)] no-underline font-syne font-extrabold text-xl tracking-tight">
          <img src="/logo.webp" alt="Declairo Logo" className="w-[24px] h-[24px] object-contain" />
          Declairo
        </Link>
        <div className="flex items-center gap-4 md:gap-6">
          <div className="hidden sm:flex items-center gap-4">
            <LanguageSwitcher />
            <ThemeToggle />
          </div>
          <Link to="/" className="text-sm font-semibold text-[var(--text2)] hover:text-[var(--text)] transition-colors">Home</Link>
          <Link to="/register" className="bg-brand-green-500 hover:bg-brand-green-600 text-brand-dark text-xs font-bold px-4 py-2 rounded-xl transition-all">
            Get started
          </Link>
        </div>
      </nav>

      {/* Hero Section */}
      <header className="pt-32 pb-16 px-6 md:px-12 max-w-7xl mx-auto text-center relative overflow-hidden">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-brand-green-500/5 blur-[120px] rounded-full pointer-events-none" />
        
        <div className="badge inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-brand-green-500/10 border border-brand-green-500/20 text-brand-green-500 text-[10px] font-bold uppercase tracking-widest mb-6">
          #DECLAIRO BLOG
        </div>
        <h1 className="font-syne text-5xl md:text-7xl font-extrabold tracking-tight mb-6">
          Knowledge is <br />
          <span className="bg-gradient-to-r from-brand-green-400 to-brand-blue-500 bg-clip-text text-transparent">tax power</span>
        </h1>
        <p className="text-[var(--text2)] text-lg max-w-2xl mx-auto font-light">
          Latest crypto tax news, DeFi strategies, and country-specific guides to help you stay compliant and save money.
        </p>

        {/* Stats */}
        <div className="flex justify-center gap-12 mt-12 pb-12 border-b border-[var(--border)]">
          <div className="text-center">
            <div className="font-syne text-2xl font-bold text-brand-green-500">500+</div>
            <div className="text-[var(--text3)] text-[9px] font-bold uppercase tracking-wider">Articles</div>
          </div>
          <div className="text-center">
            <div className="font-syne text-2xl font-bold text-brand-green-500">12</div>
            <div className="text-[var(--text3)] text-[9px] font-bold uppercase tracking-wider">Categories</div>
          </div>
          <div className="text-center">
            <div className="font-syne text-2xl font-bold text-brand-green-500">Weekly</div>
            <div className="text-[var(--text3)] text-[9px] font-bold uppercase tracking-wider">Updates</div>
          </div>
        </div>
      </header>

      {/* Categories / Tags */}
      <div className="sticky top-[65px] z-[90] bg-[var(--bg)]/80 backdrop-blur-md border-b border-[var(--border)] py-4 mb-12">
        <div className="max-w-7xl mx-auto px-6 md:px-12 flex items-center gap-3 overflow-x-auto no-scrollbar">
          {categories.map(cat => (
            <button
              key={cat}
              onClick={() => { setActiveCategory(cat); setVisibleCount(6); }}
              className={`px-5 py-2 rounded-full text-xs font-bold whitespace-nowrap transition-all ${
                activeCategory === cat 
                  ? 'bg-brand-green-500 text-brand-dark shadow-lg shadow-brand-green-500/20' 
                  : 'bg-[var(--card2)] text-[var(--text2)] hover:bg-[var(--card3)] hover:text-[var(--text)]'
              }`}
            >
              {cat === 'All' ? cat : `#${cat.toUpperCase()}`}
            </button>
          ))}
        </div>
      </div>

      <main className="max-w-7xl mx-auto px-6 md:px-12 pb-24">
        {/* Featured Post */}
        {activeCategory === 'All' && (
          <Link to={`/blog/${featuredPost.slug}`} className="group block relative rounded-[2.5rem] overflow-hidden mb-16 border border-[var(--border)] bg-[var(--card)] hover:border-brand-green-500/30 transition-all shadow-2xl">
            <div className="flex flex-col lg:flex-row h-full lg:h-[450px]">
              <div className="lg:w-3/5 relative h-[250px] lg:h-full overflow-hidden">
                <img src={featuredPost.heroImage} alt={featuredPost.title} className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105" />
                <div className="absolute inset-0 bg-gradient-to-t from-[var(--card)] via-transparent to-transparent lg:bg-gradient-to-r lg:from-transparent lg:to-[var(--card)]" />
              </div>
              <div className="lg:w-2/5 p-10 flex flex-col justify-center">
                <div className="text-brand-green-500 text-[10px] font-black uppercase tracking-widest mb-4">Featured Article</div>
                <h2 className="font-syne text-3xl font-bold mb-6 leading-tight group-hover:text-brand-green-500 transition-colors">
                  {featuredPost.title}
                </h2>
                <p className="text-[var(--text2)] text-sm leading-relaxed mb-8 line-clamp-3">
                  {featuredPost.excerpt}
                </p>
                <div className="flex items-center gap-4 mt-auto">
                  <div className="w-8 h-8 rounded-full bg-brand-green-500/20 flex items-center justify-center font-bold text-xs text-brand-green-500">
                    {featuredPost.author.name[0]}
                  </div>
                  <div className="text-xs">
                    <div className="font-bold">{featuredPost.author.name}</div>
                    <div className="text-[var(--text3)]">{featuredPost.date} • {featuredPost.readTime}</div>
                  </div>
                </div>
              </div>
            </div>
          </Link>
        )}

        {/* Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {gridPosts.map((post, i) => (
            <Link key={post.slug} to={`/blog/${post.slug}`} className="group flex flex-col rounded-3xl overflow-hidden border border-[var(--border)] bg-[var(--card)] hover:border-brand-green-500/30 transition-all hover:-translate-y-2">
              <div className="h-48 overflow-hidden relative">
                <img src={post.heroImage} alt={post.title} className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110" />
                <div className="absolute top-4 left-4 px-3 py-1 rounded-lg bg-black/40 backdrop-blur-md border border-white/10 text-[9px] font-black text-brand-green-500 uppercase tracking-widest">
                  #{post.category}
                </div>
              </div>
              <div className="p-8 flex flex-col flex-1">
                <h3 className="font-syne text-xl font-bold mb-4 leading-snug group-hover:text-brand-green-500 transition-colors">
                  {post.title}
                </h3>
                <p className="text-[var(--text2)] text-xs leading-relaxed mb-6 line-clamp-2">
                  {post.excerpt}
                </p>
                <div className="flex items-center justify-between mt-auto pt-6 border-t border-[var(--border)]/50">
                   <div className="text-[10px] text-[var(--text3)] font-bold uppercase tracking-tighter">
                     {post.date}
                   </div>
                   <div className="flex items-center gap-1 text-[10px] font-bold text-brand-green-500 uppercase tracking-widest">
                     Read More <ChevronRight size={12} />
                   </div>
                </div>
              </div>
            </Link>
          ))}
        </div>

        {filteredPosts.length > visibleCount && (
          <div className="text-center mt-16">
            <button 
              onClick={() => setVisibleCount(prev => prev + 6)}
              className="px-10 py-4 rounded-xl border border-[var(--border)] hover:border-brand-green-500 hover:text-brand-green-500 font-bold text-sm transition-all"
            >
              Load more articles
            </button>
          </div>
        )}
      </main>

      {/* Newsletter Section */}
      <section className="bg-gradient-to-br from-brand-green-500 to-brand-blue-600 py-20 px-6">
        <div className="max-w-4xl mx-auto text-center text-brand-dark">
          <div className="w-16 h-16 bg-brand-dark/10 rounded-2xl flex items-center justify-center mx-auto mb-8">
            <Mail size={32} />
          </div>
          <h2 className="font-syne text-4xl font-bold mb-4">Stay ahead of the IRS</h2>
          <p className="font-medium opacity-80 mb-10 max-w-lg mx-auto">
            Get weekly crypto tax tips and regulation updates delivered straight to your inbox.
          </p>
          <form className="flex flex-col md:flex-row gap-3 max-w-md mx-auto" onSubmit={(e) => e.preventDefault()}>
            <input 
              type="email" 
              placeholder="Enter your email" 
              className="flex-1 px-6 py-4 rounded-xl bg-white/20 border border-white/30 text-brand-dark placeholder:text-brand-dark/50 outline-none focus:bg-white/40 transition-all font-bold"
            />
            <button className="bg-brand-dark text-white px-8 py-4 rounded-xl font-bold hover:scale-105 transition-all shadow-xl">
              Join Newsletter
            </button>
          </form>
        </div>
      </section>

      {/* Footer (Reused style) */}
      <footer className="py-12 px-6 border-t border-[var(--border)] text-center">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-6">
          <Link to="/" className="font-syne font-extrabold text-xl tracking-tight text-[var(--text)] no-underline flex items-center gap-2">
            <img src="/logo.webp" className="w-6 h-6" alt="logo" /> Declairo
          </Link>
          <p className="text-[var(--text3)] text-[11px] font-bold uppercase tracking-[0.2em]">
            © 2026 Declairo · Professional Crypto Tax Tools
          </p>
          <div className="flex gap-6 text-xs font-bold">
            <Link to="/terms" className="text-[var(--text3)] hover:text-brand-green-500">Terms</Link>
            <Link to="/privacy" className="text-[var(--text3)] hover:text-brand-green-500">Privacy</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
