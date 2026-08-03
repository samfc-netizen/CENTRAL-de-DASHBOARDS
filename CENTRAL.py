import html
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import requests
import streamlit as st

st.set_page_config(
    page_title="Portal de Dashboards | Grupo Dauto",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="collapsed",
)

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "dashboards.json"

st.markdown("""
<style>
    #MainMenu, footer, header {visibility: hidden;}
    .stApp {
        background:
            radial-gradient(circle at 90% 0%, rgba(186, 27, 45, .12), transparent 30rem),
            #f4f6f9;
    }
    .block-container {
        max-width: 1480px;
        padding: 1.3rem 2.2rem 4rem;
    }
    .topbar {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 18px;
        padding: 16px 22px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 5px 18px rgba(16,24,40,.05);
        margin-bottom: 18px;
    }
    .brand {
        font-size: 1.12rem;
        font-weight: 900;
        color: #9c1725;
        letter-spacing: .01em;
    }
    .brand-sub {
        font-size: .78rem;
        color: #667085;
        margin-top: 1px;
    }
    .top-status {
        font-size: .78rem;
        font-weight: 750;
        color: #027a48;
        background: #ecfdf3;
        padding: 7px 12px;
        border-radius: 999px;
    }
    .hero {
        position: relative;
        overflow: hidden;
        background: linear-gradient(125deg, #8d111e 0%, #bf2132 58%, #df4353 100%);
        border-radius: 26px;
        padding: 38px 42px;
        color: white;
        box-shadow: 0 20px 48px rgba(143,20,32,.20);
        margin-bottom: 20px;
    }
    .hero:after {
        content: "";
        position: absolute;
        width: 330px;
        height: 330px;
        border: 52px solid rgba(255,255,255,.08);
        border-radius: 50%;
        right: -90px;
        top: -120px;
    }
    .eyebrow {
        font-size: .76rem;
        font-weight: 800;
        letter-spacing: .15em;
        text-transform: uppercase;
        opacity: .8;
        margin-bottom: 12px;
    }
    .hero h1 {
        font-size: 2.55rem;
        line-height: 1.04;
        margin: 0 0 12px 0;
        max-width: 760px;
    }
    .hero p {
        font-size: 1rem;
        line-height: 1.55;
        max-width: 760px;
        opacity: .9;
        margin: 0;
    }
    .section-head {
        display:flex;
        justify-content:space-between;
        align-items:end;
        margin: 26px 0 12px;
    }
    .section-title {
        font-size: 1.28rem;
        font-weight: 900;
        color: #101828;
    }
    .section-note {
        font-size: .82rem;
        color: #667085;
    }
    [data-testid="stMetric"] {
        background: #fff;
        border: 1px solid #e5e7eb;
        padding: 14px 17px;
        border-radius: 16px;
        box-shadow: 0 5px 16px rgba(16,24,40,.04);
    }
    .portal-card {
        background: #fff;
        border: 1px solid #e4e7ec;
        border-radius: 20px;
        padding: 22px;
        min-height: 280px;
        box-shadow: 0 7px 20px rgba(16,24,40,.055);
        transition: all .18s ease;
        position: relative;
        overflow: hidden;
    }
    .portal-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 14px 30px rgba(16,24,40,.10);
        border-color: #d0d5dd;
    }
    .portal-card.featured:before {
        content: "";
        position: absolute;
        left: 0;
        top: 0;
        width: 5px;
        height: 100%;
        background: #bd2031;
    }
    .card-head {
        display:flex;
        justify-content:space-between;
        gap:10px;
        align-items:flex-start;
    }
    .icon-box {
        width: 45px;
        height: 45px;
        border-radius: 13px;
        background: #fff1f3;
        display:flex;
        align-items:center;
        justify-content:center;
        font-size: 1.35rem;
    }
    .tag {
        font-size: .7rem;
        font-weight: 850;
        color:#9f1726;
        background:#fff1f3;
        padding:5px 9px;
        border-radius:999px;
    }
    .tag-access {
        color:#344054;
        background:#f2f4f7;
    }
    .tag-dev {
        color:#b54708;
        background:#fffaeb;
    }
    .card-title {
        font-size: 1.15rem;
        font-weight: 900;
        line-height: 1.2;
        color:#101828;
        margin: 18px 0 8px;
    }
    .card-description {
        font-size: .89rem;
        line-height: 1.5;
        color:#667085;
        min-height: 80px;
    }
    .card-meta {
        border-top:1px solid #eaecf0;
        margin-top:15px;
        padding-top:13px;
        min-height:73px;
        font-size:.78rem;
        line-height:1.55;
        color:#475467;
    }
    .status-online {color:#027a48;font-weight:850;}
    .status-access {color:#475467;font-weight:800;}
    div[data-testid="stLinkButton"] a,
    div[data-testid="stButton"] button {
        width:100%;
        justify-content:center;
        border-radius:11px;
    }
    .footer-site {
        text-align:center;
        color:#667085;
        padding-top:20px;
        font-size:.78rem;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=300)
def load_data():
    if not DATA_FILE.exists():
        return []
    with DATA_FILE.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


@st.cache_data(ttl=900, show_spinner=False)
def github_last_commit(repo):
    if not repo or "/" not in repo:
        return {}
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "grupo-dauto-dashboard-portal",
    }
    try:
        token = st.secrets.get("GITHUB_TOKEN", "")
    except Exception:
        token = ""
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        r = requests.get(
            f"https://api.github.com/repos/{repo}/commits",
            params={"per_page": 1},
            headers=headers,
            timeout=8,
        )
        if r.status_code != 200:
            return {}
        commits = r.json()
        if not commits:
            return {}
        item = commits[0]
        commit = item.get("commit", {})
        author = commit.get("author", {}) or {}
        return {
            "date": author.get("date", ""),
            "author": author.get("name", ""),
            "message": (commit.get("message", "") or "").splitlines()[0],
        }
    except requests.RequestException:
        return {}


def format_date(value):
    if not value:
        return ""
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone()
        return dt.strftime("%d/%m/%Y às %H:%M")
    except ValueError:
        return value


def whatsapp_link(name, url):
    text = f"Olá! Segue o acesso ao {name}:\n\n{url}"
    return f"https://wa.me/?text={quote(text)}"


def searchable(item):
    return " ".join(str(item.get(k, "")) for k in
                    ("nome", "descricao", "categoria", "tipo")).lower()


data = load_data()

st.markdown("""
<div class="topbar">
    <div>
        <div class="brand">GRUPO DAUTO</div>
        <div class="brand-sub">Portal de inteligência e acessos corporativos</div>
    </div>
    <div class="top-status">● Portal disponível</div>
</div>
<div class="hero">
    <div class="eyebrow">Central corporativa</div>
    <h1>Dashboards, sistemas e documentos em um único lugar.</h1>
    <p>Consulte informações comerciais, financeiras e operacionais e compartilhe os acessos com rapidez.</p>
</div>
""", unsafe_allow_html=True)

dash_count = sum(x.get("tipo") == "Dashboard" for x in data)
access_count = len(data) - dash_count
categories = sorted({x.get("categoria", "Outros") for x in data})

m1, m2, m3, m4 = st.columns(4)
m1.metric("Dashboards", dash_count)
m2.metric("Sistemas e acessos", access_count)
m3.metric("Áreas", len(categories))
m4.metric("Total disponível", len(data))

st.markdown("""
<div class="section-head">
    <div>
        <div class="section-title">Explore o portal</div>
        <div class="section-note">Pesquise por nome ou filtre por área e tipo.</div>
    </div>
</div>
""", unsafe_allow_html=True)

f1, f2, f3 = st.columns([2.2, 1, 1])
with f1:
    search = st.text_input(
        "Pesquisar",
        placeholder="Pesquisar dashboard, sistema ou documento...",
        label_visibility="collapsed",
    )
with f2:
    category = st.selectbox("Categoria", ["Todas"] + categories, label_visibility="collapsed")
with f3:
    types = sorted({x.get("tipo", "Outro") for x in data})
    item_type = st.selectbox("Tipo", ["Todos"] + types, label_visibility="collapsed")

query = search.strip().lower()
filtered = [
    x for x in data
    if (not query or query in searchable(x))
    and (category == "Todas" or x.get("categoria") == category)
    and (item_type == "Todos" or x.get("tipo") == item_type)
]

st.caption(f"{len(filtered)} item(ns) disponível(is).")

for start in range(0, len(filtered), 3):
    cols = st.columns(3, gap="large")
    for col, item in zip(cols, filtered[start:start+3]):
        name = str(item.get("nome", "Acesso"))
        description = str(item.get("descricao", ""))
        category_name = str(item.get("categoria", "Outros"))
        kind = str(item.get("tipo", "Acesso"))
        url = str(item.get("url", ""))
        repo = str(item.get("repositorio", "")).strip()
        icon = str(item.get("icone", "◆"))
        featured = bool(item.get("destaque", False))
        development = bool(item.get("em_desenvolvimento", False))

        commit = github_last_commit(repo) if repo else {}
        updated = format_date(commit.get("date", ""))

        if repo:
            status_text = '<span class="status-online">● Dashboard integrado</span>'
            update_text = html.escape(updated or "Consulta ao GitHub indisponível")
            message = html.escape(commit.get("message", "")[:78])
            extra = f"<br><strong>Última alteração:</strong> {message}" if message else ""
        else:
            status_text = '<span class="status-access">● Acesso externo</span>'
            update_text = "Não utiliza repositório Streamlit"
            extra = ""

        tag_class = "tag-dev" if development else ("tag-access" if not repo else "")
        tag_label = "Em desenvolvimento" if development else kind
        card_class = "portal-card featured" if featured else "portal-card"

        with col:
            st.markdown(f"""
            <div class="{card_class}">
                <div class="card-head">
                    <div class="icon-box">{html.escape(icon)}</div>
                    <span class="tag {tag_class}">{html.escape(tag_label)}</span>
                </div>
                <div class="card-title">{html.escape(name)}</div>
                <div class="card-description">{html.escape(description)}</div>
                <div class="card-meta">
                    {status_text}<br>
                    <strong>Área:</strong> {html.escape(category_name)}<br>
                    <strong>Atualização:</strong> {update_text}{extra}
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.link_button("Acessar", url, type="primary", use_container_width=True)
            b1, b2 = st.columns(2)
            with b1:
                st.link_button("WhatsApp", whatsapp_link(name, url), use_container_width=True)
            with b2:
                with st.popover("Copiar link", use_container_width=True):
                    st.code(url, language=None, wrap_lines=True)

st.markdown("""
<div class="footer-site">
    Grupo Dauto · Portal de Dashboards e Acessos Corporativos
</div>
""", unsafe_allow_html=True)
