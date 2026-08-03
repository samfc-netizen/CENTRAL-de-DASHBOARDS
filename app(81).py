import html
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests
import streamlit as st


st.set_page_config(
    page_title="Central de Dashboards | Grupo Dauto",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

BASE_DIR = Path(__file__).resolve().parent
JSON_PATH = BASE_DIR / "dashboards.json"


st.markdown(
    """
    <style>
        :root {
            --vermelho: #c51f2f;
            --vermelho-escuro: #8f1420;
            --cinza-fundo: #f5f6f8;
            --cinza-texto: #667085;
            --borda: #e4e7ec;
            --branco: #ffffff;
        }

        .stApp {
            background:
                radial-gradient(circle at top right, rgba(197,31,47,.08), transparent 28rem),
                var(--cinza-fundo);
        }

        .block-container {
            max-width: 1450px;
            padding-top: 2rem;
            padding-bottom: 4rem;
        }

        .hero {
            background: linear-gradient(135deg, #9e1623, #cf2b3d);
            border-radius: 24px;
            padding: 32px;
            color: white;
            margin-bottom: 20px;
            box-shadow: 0 16px 40px rgba(143,20,32,.18);
        }

        .hero-title {
            font-size: 2.35rem;
            line-height: 1.1;
            font-weight: 850;
            margin-bottom: 8px;
        }

        .hero-subtitle {
            font-size: 1rem;
            opacity: .92;
            max-width: 820px;
        }

        .section-title {
            font-size: 1.35rem;
            font-weight: 800;
            color: #101828;
            margin-top: 10px;
            margin-bottom: 6px;
        }

        .dashboard-card {
            background: white;
            border: 1px solid var(--borda);
            border-radius: 18px;
            padding: 22px;
            min-height: 265px;
            box-shadow: 0 6px 18px rgba(16,24,40,.06);
            transition: .2s ease;
        }

        .dashboard-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 26px rgba(16,24,40,.10);
            border-color: #d0d5dd;
        }

        .card-top {
            display: flex;
            justify-content: space-between;
            gap: 10px;
            align-items: flex-start;
        }

        .badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            border-radius: 999px;
            padding: 5px 10px;
            font-size: .75rem;
            font-weight: 750;
            background: #fff1f3;
            color: #a11524;
        }

        .badge-dev {
            background: #fffaeb;
            color: #b54708;
        }

        .card-title {
            font-size: 1.18rem;
            font-weight: 850;
            color: #101828;
            margin-top: 16px;
            margin-bottom: 8px;
        }

        .card-description {
            color: var(--cinza-texto);
            font-size: .92rem;
            line-height: 1.48;
            min-height: 68px;
        }

        .meta-box {
            margin-top: 16px;
            padding-top: 13px;
            border-top: 1px solid #eaecf0;
            font-size: .80rem;
            line-height: 1.55;
            color: #475467;
            min-height: 68px;
        }

        .online {
            color: #027a48;
            font-weight: 800;
        }

        .unknown {
            color: #667085;
            font-weight: 700;
        }

        div[data-testid="stLinkButton"] a {
            width: 100%;
            justify-content: center;
            border-radius: 10px;
        }

        div[data-testid="stButton"] button {
            width: 100%;
            border-radius: 10px;
        }

        [data-testid="stMetric"] {
            background: white;
            border: 1px solid var(--borda);
            padding: 13px 16px;
            border-radius: 14px;
            box-shadow: 0 4px 14px rgba(16,24,40,.04);
        }

        .footer {
            color: #667085;
            text-align: center;
            padding-top: 10px;
            font-size: .82rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=300)
def carregar_itens() -> list[dict]:
    if not JSON_PATH.exists():
        return []

    with JSON_PATH.open("r", encoding="utf-8") as arquivo:
        dados = json.load(arquivo)

    return dados if isinstance(dados, list) else []


@st.cache_data(ttl=900, show_spinner=False)
def consultar_github(repositorio: str) -> dict:
    """
    repositorio deve ser informado como usuario/nome-do-repositorio.
    Para repositórios privados, configure GITHUB_TOKEN nos Secrets do Streamlit.
    """
    if not repositorio or "/" not in repositorio:
        return {}

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "central-dashboards-dauto",
    }

    token = st.secrets.get("GITHUB_TOKEN", "")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    url = f"https://api.github.com/repos/{repositorio}/commits"
    resposta = requests.get(
        url,
        params={"per_page": 1},
        headers=headers,
        timeout=8,
    )

    if resposta.status_code != 200:
        return {}

    commits = resposta.json()
    if not commits:
        return {}

    ultimo = commits[0]
    commit = ultimo.get("commit", {})
    autor = commit.get("author", {}) or {}

    return {
        "data": autor.get("date", ""),
        "autor": autor.get("name", ""),
        "mensagem": (commit.get("message", "") or "").splitlines()[0],
        "html_url": ultimo.get("html_url", ""),
    }


@st.cache_data(ttl=300, show_spinner=False)
def verificar_url(url: str) -> bool | None:
    """
    Retorna True se o endereço responder.
    Retorna None quando a verificação não for conclusiva.
    Alguns apps Streamlit em repouso podem demorar para despertar.
    """
    try:
        resposta = requests.get(
            url,
            timeout=5,
            allow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        return resposta.status_code < 500
    except requests.RequestException:
        return None


def formatar_data_github(data_iso: str) -> str:
    if not data_iso:
        return ""

    try:
        data = datetime.fromisoformat(data_iso.replace("Z", "+00:00"))
        data_local = data.astimezone()
        return data_local.strftime("%d/%m/%Y às %H:%M")
    except ValueError:
        return data_iso


def link_whatsapp(nome: str, url: str) -> str:
    mensagem = f"Olá! Segue o acesso ao {nome}:\n\n{url}"
    return f"https://wa.me/?text={quote(mensagem)}"


def texto_pesquisa(item: dict) -> str:
    return " ".join(
        str(item.get(chave, ""))
        for chave in ("nome", "descricao", "categoria", "tipo")
    ).lower()


itens = carregar_itens()

st.markdown(
    """
    <div class="hero">
        <div class="hero-title">Central de Dashboards</div>
        <div class="hero-subtitle">
            Acesse os painéis, sistemas e documentos do Grupo Dauto em um único lugar.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

categorias = sorted({item.get("categoria", "Outros") for item in itens})
dashboards_total = sum(item.get("tipo") == "Dashboard" for item in itens)

c1, c2, c3 = st.columns(3)
c1.metric("Acessos cadastrados", len(itens))
c2.metric("Dashboards", dashboards_total)
c3.metric("Categorias", len(categorias))

st.markdown('<div class="section-title">Localizar acesso</div>', unsafe_allow_html=True)

f1, f2, f3 = st.columns([2.2, 1, 1])
with f1:
    busca = st.text_input(
        "Pesquisar",
        placeholder="Digite o nome do dashboard, área ou finalidade...",
        label_visibility="collapsed",
    )
with f2:
    categoria = st.selectbox(
        "Categoria",
        ["Todas"] + categorias,
        label_visibility="collapsed",
    )
with f3:
    tipo = st.selectbox(
        "Tipo",
        ["Todos"] + sorted({item.get("tipo", "Outro") for item in itens}),
        label_visibility="collapsed",
    )

busca_normalizada = busca.strip().lower()

filtrados = [
    item for item in itens
    if (not busca_normalizada or busca_normalizada in texto_pesquisa(item))
    and (categoria == "Todas" or item.get("categoria") == categoria)
    and (tipo == "Todos" or item.get("tipo") == tipo)
]

st.caption(f"{len(filtrados)} acesso(s) encontrado(s).")

if not filtrados:
    st.info("Nenhum acesso corresponde aos filtros selecionados.")
else:
    for inicio in range(0, len(filtrados), 3):
        colunas = st.columns(3, gap="large")

        for coluna, item in zip(colunas, filtrados[inicio:inicio + 3]):
            nome = str(item.get("nome", "Acesso"))
            descricao = str(item.get("descricao", ""))
            categoria_item = str(item.get("categoria", "Outros"))
            tipo_item = str(item.get("tipo", "Acesso"))
            url = str(item.get("url", ""))
            repositorio = str(item.get("repositorio", "")).strip()
            manual = str(item.get("ultima_atualizacao_manual", "")).strip()
            em_desenvolvimento = bool(item.get("em_desenvolvimento", False))

            github = consultar_github(repositorio)
            data_atualizacao = (
                formatar_data_github(github.get("data", ""))
                or manual
                or "Repositório ainda não informado"
            )

            status = verificar_url(url)
            if status is True:
                status_html = '<span class="online">● Disponível</span>'
            else:
                status_html = '<span class="unknown">● Verificação inconclusiva</span>'

            badge_class = "badge badge-dev" if em_desenvolvimento else "badge"
            badge_text = "Em desenvolvimento" if em_desenvolvimento else html.escape(tipo_item)

            detalhe_commit = ""
            if github.get("mensagem"):
                detalhe_commit = (
                    f"<br><strong>Última alteração:</strong> "
                    f"{html.escape(github['mensagem'][:90])}"
                )

            with coluna:
                st.markdown(
                    f"""
                    <div class="dashboard-card">
                        <div class="card-top">
                            <span class="{badge_class}">{badge_text}</span>
                            <span class="badge">{html.escape(categoria_item)}</span>
                        </div>
                        <div class="card-title">{html.escape(nome)}</div>
                        <div class="card-description">{html.escape(descricao)}</div>
                        <div class="meta-box">
                            {status_html}<br>
                            <strong>Atualização:</strong> {html.escape(data_atualizacao)}
                            {detalhe_commit}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.link_button(
                    "Abrir acesso",
                    url,
                    type="primary",
                    use_container_width=True,
                )

                st.link_button(
                    "Compartilhar no WhatsApp",
                    link_whatsapp(nome, url),
                    use_container_width=True,
                )

                with st.expander("Copiar link"):
                    st.code(url, language=None, wrap_lines=True)

st.divider()

with st.expander("Como ativar a atualização automática pelo GitHub"):
    st.markdown(
        """
        No arquivo `dashboards.json`, preencha o campo `repositorio` no formato:

        ```json
        "repositorio": "usuario/nome-do-repositorio"
        ```

        Exemplo:

        ```json
        "repositorio": "samuelcarvalho/dashboard-vendas"
        ```

        A Central passará a exibir automaticamente a data, o autor e a mensagem
        do último commit. Para repositórios privados, cadastre um token no
        Streamlit Secrets com o nome `GITHUB_TOKEN`.
        """
    )

st.markdown(
    '<div class="footer">Central de Dashboards — Grupo Dauto</div>',
    unsafe_allow_html=True,
)
