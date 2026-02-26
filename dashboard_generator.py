# -*- coding: utf-8 -*-

import os
import json
from datetime import datetime

def generate_html_dashboard(results, business_name, csv_path):
    """
    Generates a premium HTML dashboard for review analysis.
    """
    positives = results.get('positives', [])
    negatives = results.get('negatives', [])
    review_data = results.get('review_data', [])
    
    total_pos_mentions = results.get('total_positive_mentions', 0)
    total_neg_mentions = results.get('total_negative_mentions', 0)
    total_mentions = total_pos_mentions + total_neg_mentions
    
    pos_pct = (total_pos_mentions / total_mentions * 100) if total_mentions > 0 else 0
    neg_pct = (total_neg_mentions / total_mentions * 100) if total_mentions > 0 else 0

    # Data for JS
    review_lookup = {i: r for i, r in enumerate(review_data)}
    
    # Pre-render cards to avoid backslashes in f-string
    pos_cards = "".join([f'<div class="category-card" style="color: var(--accent-pos)" onclick="showReviews(\'{cat}\', {ids})"><span>{cat}</span><span class="count-badge">{count}</span></div>' for cat, count, ids in positives])
    neg_cards = "".join([f'<div class="category-card" style="color: var(--accent-neg)" onclick="showReviews(\'{cat}\', {ids})"><span>{cat}</span><span class="count-badge">{count}</span></div>' for cat, count, ids in negatives])
    reviews_json = json.dumps(review_lookup)

    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{business_name} - Review Analysis</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg: #0f172a;
            --card-bg: #1e293b;
            --accent-pos: #10b981;
            --accent-neg: #ef4444;
            --text-main: #f8fafc;
            --text-dim: #94a3b8;
            --glass: rgba(255, 255, 255, 0.03);
            --glass-border: rgba(255, 255, 255, 0.1);
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Outfit', sans-serif;
        }}

        body {{
            background-color: var(--bg);
            color: var(--text-main);
            line-height: 1.6;
            padding: 2rem;
            min-height: 100vh;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        header {{
            text-align: center;
            margin-bottom: 3rem;
        }}

        h1 {{
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            background: linear-gradient(to right, #60a5fa, #a855f7);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .stats-bar {{
            display: flex;
            gap: 1rem;
            margin-bottom: 3rem;
        }}

        .stat-card {{
            flex: 1;
            background: var(--card-bg);
            padding: 1.5rem;
            border-radius: 1rem;
            border: 1px solid var(--glass-border);
            text-align: center;
        }}

        .stat-value {{
            font-size: 2rem;
            font-weight: 700;
            display: block;
        }}

        .stat-label {{
            color: var(--text-dim);
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .sentiment-track {{
            height: 12px;
            background: #334155;
            border-radius: 6px;
            overflow: hidden;
            display: flex;
            margin: 1rem 0;
        }}

        .pos-bar {{ background: var(--accent-pos); transition: width 1s ease; }}
        .neg-bar {{ background: var(--accent-neg); transition: width 1s ease; }}

        .grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 2rem;
        }}

        .section-title {{
            font-size: 1.5rem;
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .category-card {{
            background: var(--glass);
            border: 1px solid var(--glass-border);
            padding: 1.25rem;
            border-radius: 0.75rem;
            margin-bottom: 1rem;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .category-card:hover {{
            background: rgba(255,255,255,0.07);
            transform: translateX(10px);
        }}

        .category-card.active {{
            border-color: currentColor;
            background: rgba(255,255,255,0.1);
        }}

        .count-badge {{
            background: rgba(255,255,255,0.1);
            padding: 0.25rem 0.75rem;
            border-radius: 2rem;
            font-size: 0.85rem;
            font-weight: 600;
        }}

        #review-details {{
            position: fixed;
            right: -450px;
            top: 0;
            width: 450px;
            height: 100vh;
            background: var(--card-bg);
            box-shadow: -10px 0 30px rgba(0,0,0,0.5);
            padding: 2rem;
            overflow-y: auto;
            transition: right 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            z-index: 1000;
            border-left: 1px solid var(--glass-border);
        }}

        #review-details.open {{
            right: 0;
        }}

        .close-btn {{
            position: absolute;
            top: 1rem;
            right: 1rem;
            background: none;
            border: none;
            color: var(--text-dim);
            font-size: 1.5rem;
            cursor: pointer;
        }}

        .side-title {{
            font-size: 1.25rem;
            margin-bottom: 2rem;
            color: var(--text-main);
        }}

        .review-item {{
            background: var(--glass);
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
            border: 1px solid var(--glass-border);
        }}

        .review-meta {{
            display: flex;
            justify-content: space-between;
            font-size: 0.8rem;
            color: var(--text-dim);
            margin-bottom: 0.5rem;
        }}

        .rating {{ color: #fbbf24; font-weight: 600; }}

        .overlay {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            display: none;
            z-index: 999;
        }}

        .overlay.open {{ display: block; }}
    </style>
</head>
<body>

<div class="container">
    <header>
        <h1>{business_name}</h1>
        <p class="stat-label">Review Analysis Dashboard • {datetime.now().strftime('%b %d, %Y')}</p>
    </header>

    <div class="stats-bar">
        <div class="stat-card">
            <span class="stat-value" style="color: var(--accent-pos)">{pos_pct:.1f}%</span>
            <span class="stat-label">Positive</span>
        </div>
        <div class="stat-card">
            <span class="stat-value" style="color: var(--accent-neg)">{neg_pct:.1f}%</span>
            <span class="stat-label">Negative</span>
        </div>
        <div class="stat-card">
            <span class="stat-value" style="color: #60a5fa">{total_mentions}</span>
            <span class="stat-label">Total Mentions</span>
        </div>
    </div>

    <div class="sentiment-track">
        <div class="pos-bar" style="width: {pos_pct}%"></div>
        <div class="neg-bar" style="width: {neg_pct}%"></div>
    </div>

    <div class="grid">
        <div class="col">
            <h2 class="section-title"><span style="color: var(--accent-pos)">●</span> Positives</h2>
            <div id="pos-categories">
                {pos_cards}
            </div>
        </div>
        <div class="col">
            <h2 class="section-title"><span style="color: var(--accent-neg)">●</span> Negatives</h2>
            <div id="neg-categories">
                {neg_cards}
            </div>
        </div>
    </div>
</div>

<div class="overlay" id="overlay" onclick="closeReviews()"></div>
<div id="review-details">
    <button class="close-btn" onclick="closeReviews()">×</button>
    <h3 class="side-title" id="side-title">Category Details</h3>
    <div id="reviews-container"></div>
</div>

<script>
    const reviewsData = {reviews_json};

    function showReviews(category, ids) {{
        const container = document.getElementById('reviews-container');
        const sideTitle = document.getElementById('side-title');
        sideTitle.innerText = category;
        container.innerHTML = '';

        ids.forEach(id => {{
            const r = reviewsData[id];
            if (!r) return;
            const card = document.createElement('div');
            card.className = 'review-item';
            card.innerHTML = `
                <div class="review-meta">
                    <span class="rating">★ ${{r.rating}}</span>
                    <span>${{r.date}}</span>
                </div>
                <p style="font-weight: 600; margin-bottom: 0.25rem;">${{r.name}}</p>
                <p style="font-size: 0.9rem; color: var(--text-dim)">${{r.review}}</p>
            `;
            container.appendChild(card);
        }});

        document.getElementById('review-details').classList.add('open');
        document.getElementById('overlay').classList.add('open');
    }}

    function closeReviews() {{
        document.getElementById('review-details').classList.remove('open');
        document.getElementById('overlay').classList.remove('open');
    }}
</script>

</body>
</html>
    """
    
    dashboard_path = csv_path.replace('.csv', '_dashboard.html')
    with open(dashboard_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    return dashboard_path
