import * as fs from 'fs';
import * as path from 'path';
import { BLOG_POSTS } from '../src/data/blogPosts';

import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PUBLIC_DIR = path.resolve(__dirname, '../public');
const BLOG_DIR = path.join(PUBLIC_DIR, 'blog');
const DOMAIN = 'https://declairo.com';

// Ensure directory exists
if (!fs.existsSync(BLOG_DIR)) {
  fs.mkdirSync(BLOG_DIR, { recursive: true });
}

function generateHTML(post: any) {
  const fullUrl = `${DOMAIN}/blog/${post.slug}`;
  
  return `<!DOCTYPE html>
<html lang="${post.language}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${post.title} | Declairo Blog</title>
    <meta name="description" content="${post.metaDescription}">
    <link rel="canonical" href="${fullUrl}">
    
    <!-- Open Graph -->
    <meta property="og:type" content="article">
    <meta property="og:title" content="${post.title}">
    <meta property="og:description" content="${post.metaDescription}">
    <meta property="og:url" content="${fullUrl}">
    <meta property="og:image" content="${DOMAIN}${post.heroImage}">
    <meta property="article:published_time" content="${post.isoDate}">
    <meta property="article:author" content="${post.author.name}">
    
    <!-- Site Icon for Google Search -->
    <link rel="icon" type="image/png" href="${DOMAIN}/logo_site.png">
    
    <!-- Structured Data -->
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "BlogPosting",
      "headline": "${post.title}",
      "description": "${post.metaDescription}",
      "image": "${DOMAIN}${post.heroImage}",
      "datePublished": "${post.isoDate}",
      "author": {
        "@type": "Person",
        "name": "${post.author.name}"
      },
      "publisher": {
        "@type": "Organization",
        "name": "Declairo",
        "logo": {
          "@type": "ImageObject",
          "url": "${DOMAIN}/logo_site.png"
        }
      },
      "mainEntityOfPage": {
        "@type": "WebPage",
        "@id": "${fullUrl}"
      }
    }
    </script>
    
    <style>
        body { font-family: sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 2rem; }
        h1 { font-size: 2.5rem; margin-bottom: 1rem; }
        img { max-width: 100%; height: auto; border-radius: 1rem; }
        .meta { color: #666; font-size: 0.9rem; margin-bottom: 2rem; }
        .content { font-size: 1.1rem; }
        .cta { background: #f4f4f4; padding: 2rem; border-radius: 1rem; margin-top: 3rem; text-align: center; }
        .cta a { background: #10b981; color: #fff; padding: 1rem 2rem; border-radius: 0.5rem; text-decoration: none; font-weight: bold; }
    </style>
</head>
<body>
    <nav><a href="/">← Back to Declairo</a> | <a href="/blog">Blog</a></nav>
    <article>
        <header>
            <h1>${post.title}</h1>
            <div class="meta">
                By ${post.author.name} • ${post.date} • ${post.readTime}
            </div>
            <img src="${post.heroImage}" alt="${post.title}">
        </header>
        <div class="content">
            ${post.content}
        </div>
        <div class="cta">
            <h3>Calculando impostos de cripto?</h3>
            <p>O Declairo automatiza tudo para você em minutos.</p>
            <a href="/register">Começar Grátis →</a>
        </div>
    </article>
    <p style="text-align:center; color:#999; margin-top:4rem;">
        This is an SEO-optimized static version. <a href="${fullUrl}">View the interactive version here</a>.
    </p>
</body>
</html>`;
}

// Generate Individual Pages
BLOG_POSTS.forEach(post => {
  const filePath = path.join(BLOG_DIR, `${post.slug}.html`);
  fs.writeFileSync(filePath, generateHTML(post));
  console.log(`Generated: ${filePath}`);
});

// Generate Sitemap.xml
const sitemap = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>${DOMAIN}/</loc><priority>1.0</priority></url>
  <url><loc>${DOMAIN}/blog</loc><priority>0.8</priority></url>
  ${BLOG_POSTS.map(post => `
  <url>
    <loc>${DOMAIN}/blog/${post.slug}</loc>
    <lastmod>${post.isoDate.split('T')[0]}</lastmod>
    <priority>0.7</priority>
  </url>`).join('')}
</urlset>`;

fs.writeFileSync(path.join(PUBLIC_DIR, 'sitemap.xml'), sitemap);
console.log('Generated: sitemap.xml');

// Generate Robots.txt
const robots = `User-agent: *
Allow: /
Sitemap: ${DOMAIN}/sitemap.xml`;

fs.writeFileSync(path.join(PUBLIC_DIR, 'robots.txt'), robots);
console.log('Generated: robots.txt');
