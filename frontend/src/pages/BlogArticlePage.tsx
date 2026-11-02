import React, { useMemo } from 'react';
import { useParams, Link, Navigate } from 'react-router-dom';
import { ChevronLeft, Calendar, Clock, User, Share2, ArrowRight, Sun, Moon } from 'lucide-react';
import { BLOG_POSTS } from '../data/blogPosts';
import { ThemeToggle } from '../components/ThemeToggle';
import { LanguageSwitcher } from '../components/LanguageSwitcher';

export function BlogArticlePage() {
  const { slug } = useParams<{ slug: string }>();
  const post = useMemo(() => BLOG_POSTS.find(p => p.slug === slug), [slug]);

  if (!post) return <Navigate to="/blog" replace />;

  const relatedPosts = BLOG_POSTS.filter(p => post.relatedSlugs.includes(p.slug));

  return (
    <div className="min-h-screen bg-[var(--bg)] text-[var(--text)] selection:bg-brand-green-500 selection:text-brand-dark">
      {/* Article Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-[100] bg-[var(--nav-bg)] backdrop-blur-xl border-b border-[var(--border)] px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <Link to="/blog" className="flex items-center gap-2 text-sm font-bold text-[var(--text2)] hover:text-brand-green-500 transition-colors">
            <ChevronLeft size={18} /> Back to Blog
          </Link>
          <div className="flex items-center gap-4">
             <div className="hidden sm:flex items-center gap-2 mr-2">
                <LanguageSwitcher />
                <ThemeToggle />
             </div>
             <div className="hidden md:flex items-center gap-3">
                <span className="text-[10px] font-black text-[var(--text3)] uppercase tracking-widest">Share:</span>
                <button className="w-8 h-8 rounded-lg border border-[var(--border)] flex items-center justify-center hover:border-brand-green-500 transition-colors"><Share2 size={14} /></button>
             </div>
          </div>
        </div>
      </nav>

      <main className="pt-32 pb-24 px-6">
        <article className="max-w-4xl mx-auto">
          {/* Header */}
          <header className="mb-12">
            <div className="flex items-center gap-3 mb-6">
               <span className="px-3 py-1 rounded-lg bg-brand-green-500/10 border border-brand-green-500/20 text-[10px] font-black text-brand-green-500 uppercase tracking-widest">
                 #{post.category}
               </span>
               <span className="text-[10px] font-bold text-[var(--text3)] uppercase tracking-widest">
                 {post.language === 'en' ? 'English' : 'Português'}
               </span>
            </div>
            <h1 className="font-syne text-4xl md:text-6xl font-extrabold tracking-tight mb-8 leading-tight">
              {post.title}
            </h1>
            
            <div className="flex flex-wrap items-center gap-8 py-8 border-y border-[var(--border)]">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-brand-green-500/10 flex items-center justify-center font-bold text-brand-green-500">
                  {post.author.name[0]}
                </div>
                <div>
                  <div className="text-sm font-bold">{post.author.name}</div>
                  <div className="text-[10px] text-[var(--text3)] font-bold uppercase">{post.author.role}</div>
                </div>
              </div>
              <div className="flex items-center gap-2 text-[var(--text3)]">
                <Calendar size={14} />
                <span className="text-xs font-bold uppercase tracking-tighter">{post.date}</span>
              </div>
              <div className="flex items-center gap-2 text-[var(--text3)]">
                <Clock size={14} />
                <span className="text-xs font-bold uppercase tracking-tighter">{post.readTime}</span>
              </div>
            </div>
          </header>

          {/* Hero Image */}
          <div className="rounded-[2.5rem] overflow-hidden border border-[var(--border)] mb-16 shadow-2xl">
            <img src={post.heroImage} alt={post.title} className="w-full h-full object-cover" />
          </div>

          {/* Content */}
          <div 
            className="prose prose-invert prose-green max-w-none 
              prose-h2:font-syne prose-h2:text-3xl prose-h2:font-bold prose-h2:tracking-tight prose-h2:mt-16 prose-h2:mb-8
              prose-h3:font-syne prose-h3:text-2xl prose-h3:font-bold prose-h3:mt-12
              prose-p:text-[var(--text2)] prose-p:text-lg prose-p:leading-relaxed prose-p:mb-8
              prose-li:text-[var(--text2)] prose-li:text-lg
              prose-strong:text-[var(--text)] prose-strong:font-bold
              prose-a:text-brand-green-500 prose-a:no-underline hover:prose-a:underline
              prose-img:rounded-3xl prose-img:border prose-img:border-[var(--border)]"
            dangerouslySetInnerHTML={{ __html: post.content }}
          />

          {/* Post CTA */}
          <div className="mt-20 p-12 rounded-[3rem] bg-gradient-to-br from-[var(--card)] to-[var(--card2)] border border-[var(--border)] text-center relative overflow-hidden group">
            <div className="absolute top-0 right-0 w-64 h-64 bg-brand-green-500/5 blur-[80px] rounded-full group-hover:bg-brand-green-500/10 transition-all" />
            <h3 className="font-syne text-3xl font-bold mb-4 relative z-10">Done reading? Let's fix your taxes.</h3>
            <p className="text-[var(--text2)] mb-10 max-w-lg mx-auto relative z-10">
              Join 250,000+ investors using Declairo to automate their crypto reporting.
            </p>
            <Link to="/register" className="inline-flex items-center gap-3 bg-brand-green-500 hover:bg-brand-green-600 text-brand-dark px-10 py-4 rounded-2xl font-bold transition-all shadow-xl shadow-brand-green-500/20 hover:scale-105 relative z-10">
              Get Started for Free <ArrowRight size={18} />
            </Link>
          </div>

          {/* Related Posts */}
          {relatedPosts.length > 0 && (
            <section className="mt-24 border-t border-[var(--border)] pt-20">
              <h3 className="font-syne text-2xl font-bold mb-10">Continue Reading</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {relatedPosts.map(p => (
                  <Link key={p.slug} to={`/blog/${p.slug}`} className="group flex flex-col rounded-3xl overflow-hidden border border-[var(--border)] bg-[var(--card)] hover:border-brand-green-500/30 transition-all">
                    <div className="h-40 overflow-hidden">
                      <img src={p.heroImage} className="w-full h-full object-cover transition-transform group-hover:scale-105" alt={p.title} />
                    </div>
                    <div className="p-6">
                      <h4 className="font-syne font-bold group-hover:text-brand-green-500 transition-colors line-clamp-2">{p.title}</h4>
                    </div>
                  </Link>
                ))}
              </div>
            </section>
          )}
        </article>
      </main>

      {/* Mini Footer */}
      <footer className="py-12 border-t border-[var(--border)] text-center text-[var(--text3)] text-[10px] font-bold uppercase tracking-widest">
         © 2026 Declairo · Knowledge is Power
      </footer>
    </div>
  );
}
