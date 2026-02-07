"""
Vyron System — Frontend v2.0 (Modular)

Interface Streamlit reorganizada por blocos funcionais:
  🏠 Boas-vindas (Dashboard resumido)
  🚀 Growth & Sales  — Radar de Vendas, Caçador de Leads, CRM
  🧠 Agency Brain     — RAG (PDF + Imagens) + Chat IA
  💰 Finance & Ops    — Dashboard Financeiro, Kanban, Lançamentos Manuais
  ⚙️  System Core      — Logs de Auditoria, Perfil
"""

import os
import json
import time
import base64
import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, date

# ─────────────────────────────────────────────────────────────
# CONFIGURAÇÃO DA PÁGINA
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Vyron System",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_BASE_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

# ─────────────────────────────────────────────────────────────
# ESTILOS GLOBAIS
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
.main-header  { font-size:2.4rem; font-weight:bold; color:#1f77b4; margin-bottom:.6rem; }
.section-hdr  { font-size:1.1rem; font-weight:600; color:#555; margin:0 0 .3rem 0; }
.block-label  { font-size:.85rem; color:#888; letter-spacing:.05rem; text-transform:uppercase; }
.metric-card  { background:#f0f2f6; padding:1rem; border-radius:.5rem; margin:.5rem 0; }
.sidebar-block-title { font-size:.75rem; color:#999; letter-spacing:.12rem;
                       text-transform:uppercase; margin:1.2rem 0 .3rem .2rem; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# FUNÇÃO CENTRALIZADA DE REQUISIÇÕES
# ═══════════════════════════════════════════════════════════════

def make_request(method: str, endpoint: str, **kwargs):
    """
    Executa requisição HTTP contra a API.
    Retorna (data, error_msg).
    """
    if "timeout" not in kwargs:
        kwargs["timeout"] = 60
    url = f"{API_BASE_URL}{endpoint}"
    try:
        resp = getattr(requests, method.lower())(url, **kwargs)
        resp.raise_for_status()
        try:
            return resp.json(), None
        except Exception:
            return resp.content, None
    except requests.exceptions.Timeout:
        return None, "⏱️ Timeout: a API demorou mais de 60 s."
    except requests.exceptions.ConnectionError:
        return None, "❌ Erro de Conexão: API não está respondendo."
    except requests.exceptions.HTTPError as e:
        try:
            detail = e.response.json().get("detail", "Erro desconhecido")
        except Exception:
            detail = f"Status {e.response.status_code}"
        return None, f"❌ {detail}"
    except Exception as e:
        return None, f"❌ {type(e).__name__}: {e}"


# ═══════════════════════════════════════════════════════════════
# AUTENTICAÇÃO
# ═══════════════════════════════════════════════════════════════

def check_auth():
    return st.session_state.get("authenticated", False)


def show_login_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("## 🔐 Vyron System")
        st.markdown("### Login")
        with st.form("login"):
            username = st.text_input("👤 Usuário", placeholder="admin")
            password = st.text_input("🔒 Senha", type="password")
            submit = st.form_submit_button("🚀 Entrar", use_container_width=True)
            if submit:
                if not username or not password:
                    st.error("Preencha usuário e senha")
                else:
                    with st.spinner("Autenticando..."):
                        data, err = make_request("POST", "/login",
                                                 json={"username": username, "password": password})
                    if data and not err:
                        st.session_state.update({
                            "authenticated": True,
                            "username": data.get("username"),
                            "user_role": data.get("user_role"),
                            "token": data.get("token"),
                        })
                        st.rerun()
                    else:
                        st.error(err)
        st.markdown("---")
        st.info("**Primeiro acesso?** Execute `python scripts/create_admin.py`")


def logout():
    for k in ("authenticated", "username", "user_role", "token"):
        st.session_state.pop(k, None)
    st.rerun()


# ── Tela de login se não autenticado ───────────────────────
if not check_auth():
    show_login_page()
    st.stop()


# ═══════════════════════════════════════════════════════════════
# HELPERS DE API (WRAPPERS)
# ═══════════════════════════════════════════════════════════════

def api_projects(limit=100):
    return make_request("GET", "/projects/", params={"limit": limit})

def api_clients(limit=200):
    return make_request("GET", "/clients", params={"limit": limit})

def api_interactions(limit=200):
    return make_request("GET", "/interactions/", params={"limit": limit})

def api_revenues(limit=200):
    return make_request("GET", "/revenues/", params={"limit": limit})

def api_expenses(limit=200):
    return make_request("GET", "/expenses/", params={"limit": limit})

def api_brain_status():
    return make_request("GET", "/brain/status", timeout=15)

def api_financial_dashboard(pid):
    return make_request("GET", f"/projects/{pid}/financial-dashboard")

def api_marketing_kpis(pid):
    return make_request("GET", f"/projects/{pid}/marketing-kpis")

def send_chat(query, image=None):
    payload = {"query": query}
    if image:
        payload["image"] = image
    data, err = make_request("POST", "/ai/chat", json=payload)
    if data and not err:
        return data.get("answer"), None
    return None, err


# ═══════════════════════════════════════════════════════════════
# SIDEBAR — NAVEGAÇÃO EM BLOCOS
# ═══════════════════════════════════════════════════════════════

st.sidebar.title("🚀 Vyron System")
st.sidebar.markdown("---")
st.sidebar.info(
    f"👤 **{st.session_state.get('username','N/A')}**  \n"
    f"🎭 {st.session_state.get('user_role','N/A').upper()}"
)
if st.sidebar.button("🚪 Sair", use_container_width=True):
    logout()
st.sidebar.markdown("---")

# Monta lista flat de páginas para o selectbox
PAGES = [
    "🏠 Boas-vindas",
    "── 🚀 Growth & Sales ──",
    "📡 Radar de Vendas",
    "🎯 Caçador de Leads",
    "👥 CRM — Clientes",
    "── 🧠 Agency Brain ──",
    "🧠 Vyron Agency Brain",
    "── 💰 Finance & Ops ──",
    "📊 Dashboard Financeiro",
    "📋 Gestão Visual (Kanban)",
    "✍️ Lançamentos Manuais",
    "── ⚙️ System Core ──",
    "📝 Logs de Auditoria",
    "⚙️ Configurações",
]

# Separadores não são selecionáveis — usamos disabled via index
SEPARATOR_INDICES = [i for i, p in enumerate(PAGES) if p.startswith("──")]

# Índice padrão
if "page_index" not in st.session_state:
    st.session_state.page_index = 0

selected = st.sidebar.selectbox(
    "Navegação",
    PAGES,
    index=st.session_state.page_index,
    label_visibility="collapsed",
)

# Se o usuário selecionou um separador, volta para a página anterior
if selected.startswith("──"):
    selected = PAGES[st.session_state.page_index]
else:
    st.session_state.page_index = PAGES.index(selected)

page = selected

# ── Health check ──
st.sidebar.markdown("---")
api_h, api_err = make_request("GET", "/", timeout=5)
if api_h and not api_err:
    st.sidebar.success("✅ API Online")
else:
    st.sidebar.error("❌ API Offline")
st.sidebar.caption("Vyron System v2.0 — Modular")


# ╔═══════════════════════════════════════════════════════════════╗
# ║                   🏠  BOAS-VINDAS                            ║
# ╚═══════════════════════════════════════════════════════════════╝

if page == "🏠 Boas-vindas":
    st.markdown('<p class="main-header">🏠 Boas-vindas ao Vyron System</p>', unsafe_allow_html=True)
    st.markdown(f"Olá, **{st.session_state.get('username','usuário')}**! Aqui está o resumo de hoje.")
    st.markdown("---")

    # Busca dados para as métricas resumidas
    col_sales, col_brain, col_finance = st.columns(3)

    # ── Bloco Vendas ──────────────────────────────────────
    with col_sales:
        with st.container(border=True):
            st.markdown("### 🚀 Growth & Sales")
            clients_data, _ = api_clients(limit=500)
            interactions_data, _ = api_interactions(limit=500)
            n_clients = len(clients_data) if clients_data else 0
            n_interactions = len(interactions_data) if interactions_data else 0
            # Leads prospectados hoje
            today_str = datetime.now().strftime("%Y-%m-%d")
            leads_today = 0
            if clients_data:
                for c in clients_data:
                    created = c.get("created_at", "")
                    if isinstance(created, str) and created[:10] == today_str:
                        leads_today += 1
            st.metric("👥 Clientes Totais", n_clients)
            st.metric("🎯 Leads Hoje", leads_today)
            st.metric("💬 Interações", n_interactions)

    # ── Bloco Brain ───────────────────────────────────────
    with col_brain:
        with st.container(border=True):
            st.markdown("### 🧠 Agency Brain")
            brain_data, brain_err = api_brain_status()
            if brain_data and not brain_err:
                st.metric("📦 Blocos Indexados", brain_data.get("total_chunks", 0))
                st.metric("📄 Documentos", brain_data.get("total_files", 0))
                st.metric("🟢 Status", "Online")
            else:
                st.metric("📦 Blocos Indexados", "—")
                st.metric("📄 Documentos", "—")
                st.metric("🔴 Status", "Offline")

    # ── Bloco Financeiro ──────────────────────────────────
    with col_finance:
        with st.container(border=True):
            st.markdown("### 💰 Finance & Ops")
            projects_data, _ = api_projects(limit=500)
            revenues_data, _ = api_revenues(limit=500)
            expenses_data, _ = api_expenses(limit=500)
            n_projects = len(projects_data) if projects_data else 0

            total_rev = sum(float(r.get("amount", 0)) for r in (revenues_data or []))
            total_exp = sum(float(e.get("amount", 0)) for e in (expenses_data or []))
            net = total_rev - total_exp
            roi_str = f"{((net / total_exp) * 100):.1f}%" if total_exp > 0 else "N/A"

            st.metric("📁 Projetos", n_projects)
            st.metric("💵 Fluxo de Caixa", f"R$ {net:,.2f}")
            st.metric("📈 ROI Geral", roi_str)

    # Atividade recente (últimas interações)
    st.markdown("---")
    st.markdown("### 📜 Atividade Recente")
    if interactions_data:
        recent = sorted(interactions_data, key=lambda x: x.get("date", ""), reverse=True)[:5]
        for i in recent:
            icons = {"meeting": "👥", "call": "📞", "email": "📧", "whatsapp": "💬", "system_log": "🤖"}
            icon = icons.get(i.get("type", ""), "📝")
            date_str = (i.get("date") or "")[:10]
            desc = (i.get("description") or "—")[:120]
            st.markdown(f"{icon} **{date_str}** — {desc}")
    else:
        st.info("Nenhuma atividade recente.")


# ╔═══════════════════════════════════════════════════════════════╗
# ║             🚀  GROWTH & SALES — RADAR DE VENDAS            ║
# ╚═══════════════════════════════════════════════════════════════╝

elif page == "📡 Radar de Vendas":
    st.markdown('<p class="main-header">📡 Radar de Vendas — Prospecção Ativa</p>', unsafe_allow_html=True)
    st.markdown("**Busque empresas no Google Maps e converta em leads.**")

    # ── Busca ──
    col1, col2, col3 = st.columns([3, 3, 1])
    with col1:
        search_query = st.text_input("🎯 Nicho", placeholder="Ex: Pizzaria, Academia")
    with col2:
        search_location = st.text_input("📍 Cidade", placeholder="Ex: Passos, MG")
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        search_btn = st.button("🔍 Escanear", type="primary", use_container_width=True)

    if "radar_results" not in st.session_state:
        st.session_state.radar_results = None
    if "radar_history" not in st.session_state:
        st.session_state.radar_history = []

    if search_btn:
        if not search_query or not search_location:
            st.error("Preencha nicho e localização.")
        else:
            with st.spinner(f"Escaneando '{search_query}' em '{search_location}'..."):
                data, err = make_request("GET", "/radar/search",
                                         params={"query": search_query, "location": search_location, "limit": 20})
            if data and not err:
                st.session_state.radar_results = data
                st.session_state.radar_history.insert(0, {
                    "query": search_query, "location": search_location,
                    "total": data["total"],
                    "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "data": data,
                })
                if len(st.session_state.radar_history) > 10:
                    st.session_state.radar_history = st.session_state.radar_history[:10]
                st.success(f"✅ {data['total']} empresa(s) encontrada(s)!")
            else:
                st.error(err)
                if "SERPAPI_KEY" in str(err):
                    st.info("Configure `SERPAPI_KEY` no `.env` e reinicie o backend.")

    # ── Histórico ──
    if st.session_state.radar_history:
        st.markdown("---")
        with st.expander("📜 Histórico de buscas", expanded=False):
            for idx, entry in enumerate(st.session_state.radar_history):
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.markdown(f"🔍 **{entry['query']}** em {entry['location']} — {entry['total']} resultado(s) — {entry['timestamp']}")
                with c2:
                    if st.button("Carregar", key=f"hist_{idx}"):
                        st.session_state.radar_results = entry["data"]
                        st.rerun()

    # ── Resultados ──
    if st.session_state.radar_results:
        results = st.session_state.radar_results
        businesses = results.get("businesses", [])
        if not businesses:
            st.warning("Nenhuma empresa encontrada.")
        else:
            st.markdown("---")
            st.markdown(f"### 📊 Resultados ({len(businesses)} empresas)")
            st.caption(f"Busca: **{results['query']}** em **{results['location']}**")

            for idx, biz in enumerate(businesses):
                with st.container(border=True):
                    ci, ca = st.columns([4, 1])
                    with ci:
                        st.markdown(f"### {biz['position']}. {biz['name']}")
                        st.caption(f"📂 {biz['type']}")
                        if biz.get("rating"):
                            stars = "⭐" * int(biz['rating'])
                            st.markdown(f"{stars} **{biz['rating']}/5** ({biz.get('reviews', 0)} avaliações)")
                        info = st.columns(3)
                        with info[0]:
                            st.markdown(f"📞 {biz.get('phone','—')}")
                        with info[1]:
                            w = biz.get("website")
                            st.markdown(f"🌐 [{w}]({w})" if w else "🌐 —")
                        with info[2]:
                            st.markdown(f"📍 {(biz.get('address','') or '')[:50]}")
                    with ca:
                        st.markdown("<br>", unsafe_allow_html=True)
                        pv = st.number_input("R$", min_value=0.0, value=5000.0, step=500.0,
                                             key=f"val_{idx}", label_visibility="collapsed")
                        if st.button("🎯 Capturar", key=f"cap_{idx}", type="primary", use_container_width=True):
                            with st.spinner("Capturando..."):
                                cd, ce = make_request("POST", "/radar/convert", json={
                                    "business_name": biz["name"], "business_type": biz["type"],
                                    "phone": biz.get("phone"), "website": biz.get("website"),
                                    "address": biz.get("address"), "rating": biz.get("rating"),
                                    "reviews": biz.get("reviews", 0), "project_value": pv,
                                })
                            if cd and not ce:
                                st.success(f"✅ {cd['message']}")
                                st.balloons()
                            else:
                                st.error(ce)

            # Estatísticas
            st.markdown("---")
            s1, s2, s3, s4 = st.columns(4)
            with s1:
                st.metric("Total", len(businesses))
            with s2:
                rated = [b["rating"] for b in businesses if b.get("rating")]
                st.metric("Avaliação Média", f"{(sum(rated)/len(rated)):.1f}⭐" if rated else "—")
            with s3:
                st.metric("Com Telefone", f"{len([b for b in businesses if b.get('phone')])}/{len(businesses)}")
            with s4:
                st.metric("Com Website", f"{len([b for b in businesses if b.get('website')])}/{len(businesses)}")

            # Export
            cc1, cc2 = st.columns([3, 1])
            with cc2:
                if st.button("📥 Exportar Excel", use_container_width=True):
                    with st.spinner("Gerando planilha..."):
                        xdata, xerr = make_request("GET", "/radar/export",
                                                   params={"query": results["query"], "location": results["location"],
                                                           "limit": results["total"]})
                    if xdata and not xerr:
                        b64 = base64.b64encode(xdata).decode()
                        fn = f"Radar_{results['query'].replace(' ','_')}_{results['location'].replace(' ','_')}.xlsx"
                        st.markdown(
                            f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{fn}">📥 Clique para baixar</a>',
                            unsafe_allow_html=True,
                        )
                    else:
                        st.error(xerr)


# ╔═══════════════════════════════════════════════════════════════╗
# ║             🚀  GROWTH & SALES — CAÇADOR DE LEADS           ║
# ╚═══════════════════════════════════════════════════════════════╝

elif page == "🎯 Caçador de Leads":
    st.markdown('<p class="main-header">🎯 Caçador de Leads</p>', unsafe_allow_html=True)
    st.markdown("**Qualifique e priorize seus leads com apoio da IA.**")

    st.markdown("---")
    clients_data, clients_err = api_clients(limit=500)
    if clients_err:
        st.error(clients_err)
    elif not clients_data:
        st.info("Nenhum lead no CRM. Capture empresas pelo **📡 Radar de Vendas** primeiro.")
    else:
        # Filtros
        st.markdown("### 🔍 Filtrar Leads")
        fc1, fc2 = st.columns(2)
        with fc1:
            status_filter = st.selectbox("Status", ["Todos", "lead", "prospect", "active", "inactive"])
        with fc2:
            sort_by = st.selectbox("Ordenar por", ["Mais recentes", "Nome A-Z"])

        filtered = clients_data
        if status_filter != "Todos":
            filtered = [c for c in filtered if c.get("status") == status_filter]
        if sort_by == "Nome A-Z":
            filtered.sort(key=lambda c: c.get("name", "").lower())
        else:
            filtered.sort(key=lambda c: c.get("created_at", ""), reverse=True)

        st.markdown(f"**{len(filtered)}** lead(s) encontrado(s)")
        st.markdown("---")

        for cli in filtered:
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 1, 1])
                with c1:
                    status_icon = {"lead": "🟡", "prospect": "🟠", "active": "🟢", "inactive": "⚫"}.get(cli.get("status"), "⚪")
                    st.markdown(f"### {status_icon} {cli['name']}")
                    st.caption(f"📧 {cli.get('email','—')} | 📞 {cli.get('phone','—')}")
                    if cli.get("company"):
                        st.markdown(f"🏢 {cli['company']}")
                with c2:
                    st.markdown(f"**Status:** {cli.get('status','—')}")
                    created = (cli.get("created_at") or "")[:10]
                    st.caption(f"Criado: {created}")
                with c3:
                    if st.button("🤖 Qualificar", key=f"qualify_{cli['id']}", use_container_width=True):
                        with st.spinner("Analisando com IA..."):
                            answer, err = send_chat(
                                f"Analise este lead e diga se é quente ou frio. "
                                f"Nome: {cli['name']}, Empresa: {cli.get('company','N/A')}, "
                                f"Status: {cli.get('status','N/A')}, Email: {cli.get('email','N/A')}"
                            )
                        if answer:
                            st.info(f"🤖 **IA:** {answer}")
                        else:
                            st.warning(f"Erro: {err}")


# ╔═══════════════════════════════════════════════════════════════╗
# ║             🚀  GROWTH & SALES — CRM                        ║
# ╚═══════════════════════════════════════════════════════════════╝

elif page == "👥 CRM — Clientes":
    st.markdown('<p class="main-header">👥 CRM — Gestão de Clientes</p>', unsafe_allow_html=True)
    st.markdown("**Visualize e gerencie seus clientes e suas interações.**")

    tab_list, tab_new, tab_interact = st.tabs(["📋 Clientes", "➕ Novo Cliente", "💬 Nova Interação"])

    # ── Lista de Clientes ──
    with tab_list:
        clients_data, clients_err = api_clients(limit=500)
        if clients_err:
            st.error(clients_err)
        elif not clients_data:
            st.info("Nenhum cliente cadastrado.")
        else:
            st.success(f"{len(clients_data)} cliente(s)")
            df = pd.DataFrame(clients_data)
            display_cols = [c for c in ["name", "email", "phone", "company", "status", "created_at"] if c in df.columns]
            if display_cols:
                st.dataframe(df[display_cols], use_container_width=True, hide_index=True)

            # Interações de um cliente
            st.markdown("---")
            st.markdown("### 📜 Interações do Cliente")
            client_map = {f"{c['name']} ({c.get('email','')})": c["id"] for c in clients_data}
            if client_map:
                sel_client = st.selectbox("Selecione o cliente", list(client_map.keys()))
                sel_id = client_map[sel_client]
                int_data, int_err = make_request("GET", f"/clients/{sel_id}/interactions", params={"limit": 20})
                if int_data and not int_err:
                    interactions = int_data.get("interactions", [])
                    if interactions:
                        for it in interactions:
                            icons = {"meeting": "👥", "call": "📞", "email": "📧", "whatsapp": "💬", "system_log": "🤖"}
                            icon = icons.get(it.get("type",""), "📝")
                            d = (it.get("date") or "")[:10]
                            with st.expander(f"{icon} {it.get('type','').upper()} — {d}"):
                                st.write(it.get("description", "—"))
                    else:
                        st.info("Nenhuma interação registrada.")
                elif int_err:
                    st.warning(int_err)

    # ── Novo cliente ──
    with tab_new:
        st.markdown("### Cadastrar Novo Cliente")
        with st.form("form_new_client"):
            nc1, nc2 = st.columns(2)
            with nc1:
                cli_name = st.text_input("Nome *")
                cli_email = st.text_input("E-mail")
                cli_phone = st.text_input("Telefone")
            with nc2:
                cli_company = st.text_input("Empresa")
                cli_segment = st.text_input("Segmento")
                cli_source = st.selectbox("Origem", ["referral", "organic", "ads", "radar", "other"])
            submitted = st.form_submit_button("💾 Salvar", type="primary")
            if submitted:
                if not cli_name:
                    st.error("Nome é obrigatório.")
                else:
                    with st.spinner("Salvando..."):
                        payload = {
                            "name": cli_name, "email": cli_email, "phone": cli_phone,
                            "company": cli_company, "segment": cli_segment, "source": cli_source,
                        }
                        d, e = make_request("POST", "/clients", json=payload)
                    if d and not e:
                        st.success("✅ Cliente cadastrado!")
                        st.balloons()
                    else:
                        st.error(e)

    # ── Nova interação ──
    with tab_interact:
        st.markdown("### Registrar Interação")
        clients_ia, _ = api_clients(limit=500)
        client_map_ia = {c["name"]: c["id"] for c in (clients_ia or [])}
        if not client_map_ia:
            st.warning("Cadastre um cliente primeiro.")
        else:
            with st.form("form_interaction"):
                sel = st.selectbox("Cliente", list(client_map_ia.keys()))
                i_type = st.selectbox("Tipo", ["meeting", "call", "email", "whatsapp", "other"])
                i_content = st.text_area("Descrição *")
                btn = st.form_submit_button("💬 Registrar", type="primary")
                if btn:
                    if not i_content:
                        st.error("Descrição obrigatória.")
                    else:
                        with st.spinner("Registrando..."):
                            d, e = make_request("POST", "/interactions/", json={
                                "client_id": client_map_ia[sel],
                                "content": i_content,
                                "interaction_type": i_type,
                            })
                        if d and not e:
                            st.success("✅ Interação registrada!")
                        else:
                            st.error(e)


# ╔═══════════════════════════════════════════════════════════════╗
# ║             🧠  AGENCY BRAIN                                 ║
# ╚═══════════════════════════════════════════════════════════════╝

elif page == "🧠 Vyron Agency Brain":
    st.markdown('<p class="main-header">🧠 Vyron Agency Brain</p>', unsafe_allow_html=True)
    st.markdown("**Central de Inteligência — Documentos, imagens e chat com IA em um só lugar.**")

    if "brain_chat_history" not in st.session_state:
        st.session_state.brain_chat_history = []

    # ── Status ──
    with st.container(border=True):
        st.markdown("### 📊 Base de Conhecimento")
        sdata, serr = api_brain_status()
        if sdata and not serr:
            s1, s2, s3 = st.columns(3)
            with s1:
                st.metric("📦 Blocos Indexados", sdata.get("total_chunks", 0))
            with s2:
                st.metric("📄 Documentos", sdata.get("total_files", 0))
            with s3:
                st.metric("🟢 Status", "Online")
            files = sdata.get("files", [])
            if files:
                with st.expander("📂 Detalhes por documento"):
                    for f in files:
                        st.markdown(f"- **{f['filename']}** — {f['chunks']} chunk(s)")
        else:
            st.warning(f"Não foi possível obter status: {serr}")

    # ── Upload ──
    with st.container(border=True):
        st.markdown("### 📤 Enviar Arquivo")
        tab_pdf, tab_img = st.tabs(["📄 Documento PDF", "🖼️ Imagem (Visão IA)"])

        with tab_pdf:
            uploaded_pdf = st.file_uploader("Selecione um PDF para indexar", type=["pdf"],
                                            key="brain_pdf_uploader")
            if uploaded_pdf:
                st.info(f"📄 **{uploaded_pdf.name}** ({uploaded_pdf.size / 1024:.1f} KB)")
                if st.button("🚀 Processar e Indexar", type="primary", use_container_width=True, key="btn_idx"):
                    with st.spinner("Extraindo texto, gerando embeddings..."):
                        try:
                            resp = requests.post(
                                f"{API_BASE_URL}/brain/upload",
                                files={"file": (uploaded_pdf.name, uploaded_pdf.getvalue(), "application/pdf")},
                                timeout=120,
                            )
                            resp.raise_for_status()
                            result = resp.json()
                        except requests.exceptions.Timeout:
                            result = None
                            st.error("⏱️ Timeout")
                        except requests.exceptions.ConnectionError:
                            result = None
                            st.error("❌ API offline.")
                        except Exception as exc:
                            result = None
                            st.error(f"❌ {exc}")
                    if result:
                        st.success(
                            f"✅ **{result['filename']}** indexado! "
                            f"({result['total_pages']} pág. → {result['total_chunks']} fragmentos)"
                        )
                        st.balloons()
                        st.rerun()

        with tab_img:
            uploaded_img = st.file_uploader("Anexe recibo, nota fiscal ou imagem", type=["jpg", "jpeg", "png"],
                                            key="brain_img_uploader")
            if uploaded_img:
                st.image(uploaded_img, caption=f"📎 {uploaded_img.name}", use_container_width=True)
                st.session_state["brain_image_b64"] = base64.b64encode(uploaded_img.getvalue()).decode("utf-8")
                st.session_state["brain_image_name"] = uploaded_img.name
                st.info("💡 Imagem carregada! Pergunte no chat abaixo para análise visual.")
            else:
                st.session_state.pop("brain_image_b64", None)
                st.session_state.pop("brain_image_name", None)

    st.markdown("---")

    # ── Chat ──
    st.markdown("### 💬 Chat com o Vyron Brain")
    has_image = "brain_image_b64" in st.session_state
    if has_image:
        st.caption(f"🖼️ Imagem anexada: **{st.session_state.get('brain_image_name','')}**")

    chat_area = st.container()
    with chat_area:
        for msg in st.session_state.brain_chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    brain_input = st.chat_input(
        "👁️ Pergunte sobre a imagem..." if has_image else "Pergunte sobre documentos ou peça comandos..."
    )

    if brain_input:
        st.session_state.brain_chat_history.append({"role": "user", "content": brain_input})
        with chat_area:
            with st.chat_message("user"):
                st.markdown(brain_input)

        image_b64 = st.session_state.get("brain_image_b64")

        # Caminho A: imagem → visão
        if image_b64:
            with st.spinner("👁️ Analisando imagem com GPT-4o..."):
                answer, err = send_chat(brain_input, image_b64)
            if err:
                answer = f"⚠️ Erro: {err}"
            elif not answer:
                answer = "⚠️ Não foi possível analisar."
            st.session_state.pop("brain_image_b64", None)
            st.session_state.pop("brain_image_name", None)

        # Caminho B: RAG
        else:
            with st.spinner("🔍 Buscando nos documentos..."):
                search_data, search_err = make_request("POST", "/brain/search",
                                                       json={"query": brain_input, "limit": 3}, timeout=30)

            if search_err:
                answer = f"⚠️ Erro: {search_err}"
            elif not search_data or search_data.get("total", 0) == 0:
                with st.spinner("🤔 Consultando a IA diretamente..."):
                    answer, ai_err = send_chat(brain_input)
                if ai_err:
                    answer = (
                        "🔍 Nenhum fragmento relevante encontrado.\n\n"
                        "💡 Envie um PDF acima para começar a indexar."
                    )
                elif not answer:
                    answer = "🔍 Nenhum resultado."
            else:
                results = search_data.get("results", [])
                ctx = "\n\n---\n\n".join(
                    f"[Fragmento {i} | {r['filename']} | {r['score']:.0%}]\n{r['content']}"
                    for i, r in enumerate(results, 1)
                )
                ai_data, ai_err = make_request("POST", "/ai/chat", json={
                    "query": (
                        f"Com base EXCLUSIVAMENTE nos documentos abaixo, responda.\n\n"
                        f"DOCUMENTOS:\n{ctx}\n\nPERGUNTA: {brain_input}\n\n"
                        f"Se não encontrar, diga que a informação não está nos documentos."
                    )
                }, timeout=60)
                if ai_data and not ai_err:
                    ai_ans = ai_data.get("answer", "")
                    sources = "\n".join(
                        f"- 📄 **{r['filename']}** (bloco {r['chunk_index']}, {r['score']:.0%})"
                        for r in results
                    )
                    answer = f"{ai_ans}\n\n---\n**📚 Fontes:**\n{sources}"
                else:
                    answer = "📄 **Fragmentos encontrados:**\n\n"
                    for i, r in enumerate(results, 1):
                        answer += (
                            f"**{i}. {r['filename']}** (bloco {r['chunk_index']}, {r['score']:.0%})\n"
                            f"> {r['content'][:500]}{'...' if len(r['content']) > 500 else ''}\n\n"
                        )

        st.session_state.brain_chat_history.append({"role": "assistant", "content": answer})
        with chat_area:
            with st.chat_message("assistant"):
                st.markdown(answer)
        st.rerun()

    if st.session_state.brain_chat_history:
        if st.button("🗑️ Limpar Conversa", key="clear_brain"):
            st.session_state.brain_chat_history = []
            st.rerun()

    if not st.session_state.brain_chat_history:
        st.markdown("---")
        st.markdown("**💡 Exemplos de perguntas:**")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown('- "Qual é o escopo do contrato?"\n- "Resuma o documento principal"\n- "Quais prazos definidos?"')
        with c2:
            st.markdown('- "Analise este recibo" *(imagem)*\n- "Qual o valor total?"\n- "Liste os serviços incluídos"')


# ╔═══════════════════════════════════════════════════════════════╗
# ║             💰  FINANCE & OPS — DASHBOARD                    ║
# ╚═══════════════════════════════════════════════════════════════╝

elif page == "📊 Dashboard Financeiro":
    st.markdown('<p class="main-header">📊 Dashboard Financeiro</p>', unsafe_allow_html=True)

    projects, err = api_projects(limit=100)
    if err:
        st.error(err)
    elif not projects:
        st.warning("Nenhum projeto encontrado. Crie um em **✍️ Lançamentos Manuais**.")
    else:
        st.success(f"{len(projects)} projeto(s)")
        proj_opts = {f"{p['name']} ({p['client_name']})": p["id"] for p in projects}
        sel = st.selectbox("📁 Projeto", list(proj_opts.keys()))
        project_id = proj_opts[sel]

        data, err2 = api_financial_dashboard(project_id)
        if err2:
            st.error(err2)
        elif data:
            # Resumo
            with st.container(border=True):
                st.markdown("### 💰 Resumo Financeiro")
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.metric("💵 Receita Total", f"R$ {data['total_revenue']:,.2f}")
                with c2:
                    st.metric("💸 Despesas", f"R$ {data['total_expense']:,.2f}")
                with c3:
                    st.metric("💎 Lucro Líquido", f"R$ {data['net_profit']:,.2f}", delta=data["margin_percentage"])
                with c4:
                    margin_val = float(data["margin_percentage"].replace("%", ""))
                    mc = "🟢" if margin_val > 50 else "🟡" if margin_val > 20 else "🔴"
                    st.metric(f"{mc} Margem", data["margin_percentage"])

                # Download PDF
                st.markdown("")
                _, dl_col, _ = st.columns([1, 2, 1])
                with dl_col:
                    pdf_data, pdf_err = make_request("GET", f"/projects/{project_id}/export/pdf")
                    if pdf_data and not pdf_err:
                        st.download_button("📄 Baixar PDF", data=pdf_data,
                                           file_name=f"relatorio_{project_id[:8]}.pdf",
                                           mime="application/pdf", type="primary", use_container_width=True)

            # Gráfico
            with st.container(border=True):
                st.markdown("### 📊 Distribuição Financeira")
                fig = go.Figure(data=[go.Pie(
                    labels=["Receitas", "Despesas", "Lucro"],
                    values=[data["total_revenue"], data["total_expense"], data["net_profit"]],
                    hole=.3, marker_colors=["#2ecc71", "#e74c3c", "#3498db"],
                )])
                fig.update_layout(height=380)
                st.plotly_chart(fig, use_container_width=True)

            # Análise
            with st.container(border=True):
                st.markdown("### 📈 Análise")
                if margin_val > 70:
                    st.success("🎉 Excelente! Margem muito saudável.")
                elif margin_val > 40:
                    st.info("👍 Boa margem. Projeto rentável.")
                elif margin_val > 0:
                    st.warning("⚠️ Margem baixa. Otimize custos.")
                else:
                    st.error("❌ Projeto no prejuízo!")

            # KPIs Marketing
            with st.container(border=True):
                st.markdown("### 📈 KPIs de Marketing")
                kpis, kpis_err = api_marketing_kpis(project_id)
                if kpis and not kpis_err and kpis.get("total_impressions", 0) > 0:
                    m1, m2, m3, m4 = st.columns(4)
                    with m1:
                        st.metric("👁️ Impressões", f"{kpis['total_impressions']:,}")
                    with m2:
                        st.metric("🖱️ Cliques", f"{kpis['total_clicks']:,}", delta=kpis["ctr"])
                    with m3:
                        st.metric("🎯 Leads", kpis["total_leads"], delta=kpis["conversion_rate"])
                    with m4:
                        st.metric("💰 Custo", f"R$ {kpis['total_cost']:,.2f}")

                    st.markdown("#### 📊 Performance")
                    k1, k2, k3, k4 = st.columns(4)
                    with k1:
                        cpc_v = float(kpis["cpc"].replace("R$ ", "").replace(",", "."))
                        st.metric("CPC", f"R$ {cpc_v:.2f}")
                    with k2:
                        st.metric("CPL", f"R$ {float(kpis['cpl']):.2f}")
                    with k3:
                        cr = float(kpis["conversion_rate"].replace("%", ""))
                        ic = "🟢" if cr > 5 else "🟡" if cr > 2 else "🔴"
                        st.metric(f"{ic} Conv. Rate", kpis["conversion_rate"])
                    with k4:
                        st.metric("✅ Conversões", kpis["total_conversions"])

                    st.markdown("#### 💎 ROI")
                    r1, r2 = st.columns(2)
                    with r1:
                        st.metric("💵 Faturamento Est.", f"R$ {kpis['estimated_revenue']:,.2f}")
                    with r2:
                        roi_v = float(kpis["roi"].replace("%", ""))
                        ri = "🟢" if roi_v > 100 else "🟡" if roi_v > 0 else "🔴"
                        st.metric(f"{ri} ROI", kpis["roi"],
                                  delta="Excelente" if roi_v > 100 else "Positivo" if roi_v > 0 else "Negativo")
                else:
                    st.info("Nenhuma métrica de marketing. Adicione em **✍️ Lançamentos Manuais**.")

            # Timeline
            with st.container(border=True):
                st.markdown("### 📜 Timeline do Projeto")
                if data.get("client_id"):
                    tl, tl_err = make_request("GET", f"/clients/{data['client_id']}/interactions", params={"limit": 10})
                    if tl and not tl_err:
                        interactions = tl.get("interactions", [])
                        if interactions:
                            st.success(f"Cliente: **{tl.get('client_name','N/A')}** | {tl.get('total',0)} interações")
                            for it in interactions:
                                icons = {"meeting": "👥", "call": "📞", "email": "📧", "whatsapp": "💬", "system_log": "🤖"}
                                icon = icons.get(it["type"], "📝")
                                d = (it.get("date") or "")[:10]
                                with st.expander(f"{icon} **{it['type'].upper()}** — {d}"):
                                    st.write(it.get("description", "—"))
                        else:
                            st.info("Nenhuma interação registrada.")
                    elif tl_err:
                        st.warning(tl_err)


# ╔═══════════════════════════════════════════════════════════════╗
# ║             💰  FINANCE & OPS — KANBAN                       ║
# ╚═══════════════════════════════════════════════════════════════╝

elif page == "📋 Gestão Visual (Kanban)":
    st.markdown('<p class="main-header">📋 Gestão Visual — Kanban de Projetos</p>', unsafe_allow_html=True)

    def update_status(pid, new_status):
        with st.spinner(f"Movendo para {new_status}..."):
            d, e = make_request("PATCH", f"/projects/{pid}/status", json={"status": new_status})
        if d and not e:
            st.success(f"✅ Movido para {new_status}!")
            time.sleep(0.8)
            st.rerun()
        else:
            st.error(e)

    projects, err = api_projects(limit=100)
    if err:
        st.error(err)
    elif not projects:
        st.warning("Nenhum projeto. Crie em **✍️ Lançamentos Manuais**.")
    else:
        st.success(f"{len(projects)} projeto(s)")
        fases = {"Negociação": [], "Em Produção": [], "Concluído": []}
        for p in projects:
            s = p.get("status", "Negociação")
            if s not in fases:
                s = "Negociação"
            fases[s].append(p)

        cn, cp, cc = st.columns(3)

        with cn:
            st.markdown("### 🟧 Negociação")
            st.caption(f"{len(fases['Negociação'])} projeto(s)")
            for p in fases["Negociação"]:
                with st.container(border=True):
                    st.markdown(f"**{p['name']}**")
                    st.caption(f"👤 {p.get('client_name','—')}")
                    v = p.get("value", 0)
                    if v:
                        st.markdown(f"💰 R$ {float(v):,.2f}")
                    if st.button("▶️ Produção", key=f"s_{p['id']}", use_container_width=True, type="primary"):
                        update_status(p["id"], "Em Produção")

        with cp:
            st.markdown("### 🟦 Em Produção")
            st.caption(f"{len(fases['Em Produção'])} projeto(s)")
            for p in fases["Em Produção"]:
                with st.container(border=True):
                    st.markdown(f"**{p['name']}**")
                    st.caption(f"👤 {p.get('client_name','—')}")
                    v = p.get("value", 0)
                    if v:
                        st.markdown(f"💰 R$ {float(v):,.2f}")
                    b1, b2 = st.columns(2)
                    with b1:
                        if st.button("⬅️", key=f"b_{p['id']}", use_container_width=True):
                            update_status(p["id"], "Negociação")
                    with b2:
                        if st.button("✅", key=f"c_{p['id']}", use_container_width=True, type="primary"):
                            update_status(p["id"], "Concluído")

        with cc:
            st.markdown("### 🟩 Concluído")
            st.caption(f"{len(fases['Concluído'])} projeto(s)")
            for p in fases["Concluído"]:
                with st.container(border=True):
                    st.markdown(f"**{p['name']}**")
                    st.caption(f"👤 {p.get('client_name','—')}")
                    st.success("✅ Finalizado")
                    if st.button("🔄 Reabrir", key=f"r_{p['id']}", use_container_width=True):
                        update_status(p["id"], "Em Produção")

        # Stats
        st.markdown("---")
        ss1, ss2, ss3, ss4 = st.columns(4)
        with ss1:
            st.metric("Total", len(projects))
        with ss2:
            st.metric("Negociação", len(fases["Negociação"]))
        with ss3:
            st.metric("Produção", len(fases["Em Produção"]))
        with ss4:
            st.metric("Concluídos", len(fases["Concluído"]))


# ╔═══════════════════════════════════════════════════════════════╗
# ║             💰  FINANCE & OPS — LANÇAMENTOS MANUAIS          ║
# ╚═══════════════════════════════════════════════════════════════╝

elif page == "✍️ Lançamentos Manuais":
    st.markdown('<p class="main-header">✍️ Lançamentos Manuais</p>', unsafe_allow_html=True)
    st.markdown("**Registre dados diretamente — memória RAG garantida.**")

    tab1, tab2, tab3 = st.tabs(["💼 Novo Projeto", "💸 Nova Despesa", "📊 Métricas de Marketing"])

    # ── Novo Projeto ──
    with tab1:
        st.markdown("### Criar Novo Projeto")
        st.info("O cliente será criado automaticamente se não existir.")
        with st.form("form_proj"):
            c1, c2 = st.columns(2)
            with c1:
                pn = st.text_input("Nome do Projeto *", placeholder="Ex: Campanha Black Friday")
                cn_name = st.text_input("Cliente *", placeholder="Ex: Loja ABC")
                po = st.number_input("Orçamento (R$) *", min_value=0.0, step=100.0, value=5000.0)
            with c2:
                pp = st.number_input("Preço do Produto (Ticket Médio)", min_value=0.0, step=10.0, value=0.0)
                pd_desc = st.text_area("Descrição", placeholder="Detalhes...")
            if st.form_submit_button("💼 Criar Projeto", type="primary"):
                if not pn or not cn_name or po <= 0:
                    st.error("Preencha campos obrigatórios!")
                else:
                    with st.spinner("Criando..."):
                        r, e = make_request("POST", "/manual/projects", params={
                            "project_name": pn, "client_name": cn_name,
                            "budget": po, "product_price": pp, "description": pd_desc,
                        })
                    if r and not e:
                        st.success(f"✅ {r['message']}")
                        st.balloons()
                        st.info(f"**ID:** `{r['project_id']}`")
                    else:
                        st.error(e)

    # ── Nova Despesa ──
    with tab2:
        st.markdown("### Registrar Despesa")
        projs, _ = api_projects(100)
        proj_map = {f"{p['name']} ({p['client_name']})": p["id"] for p in (projs or [])}
        with st.form("form_desp"):
            c1, c2 = st.columns(2)
            with c1:
                if proj_map:
                    sp = st.selectbox("Projeto", list(proj_map.keys()))
                    sp_id = proj_map[sp]
                else:
                    st.warning("Crie um projeto primeiro.")
                    sp_id = None
                dd = st.text_input("Descrição *", placeholder="Ex: Google Ads")
                dv = st.number_input("Valor (R$) *", min_value=0.01, step=10.0, value=500.0)
            with c2:
                dc = st.selectbox("Categoria", ["Publicidade", "Freelancer", "Software", "Infraestrutura", "Operacional", "Outros"])
                ddt = st.date_input("Data de Vencimento *")
                ds = st.selectbox("Status", ["pending", "paid"])
            if st.form_submit_button("💸 Lançar Despesa", type="primary"):
                if not sp_id or not dd:
                    st.error("Preencha campos obrigatórios!")
                else:
                    with st.spinner("Registrando..."):
                        r, e = make_request("POST", "/manual/expenses", json={
                            "project_id": sp_id, "category": dc, "description": dd,
                            "amount": dv, "due_date": ddt.isoformat(), "status": ds,
                        })
                    if r and not e:
                        st.success(f"✅ {r['message']}")
                        st.balloons()
                    else:
                        st.error(e)

    # ── Métricas Marketing ──
    with tab3:
        st.markdown("### Métricas de Marketing")
        projs_m, _ = api_projects(100)
        pm_map = {f"{p['name']} ({p['client_name']})": p["id"] for p in (projs_m or [])}
        with st.form("form_mkt"):
            c1, c2 = st.columns(2)
            with c1:
                if pm_map:
                    sm = st.selectbox("Projeto *", list(pm_map.keys()), key="mkt_p")
                    sm_id = pm_map[sm]
                else:
                    st.warning("Crie um projeto primeiro.")
                    sm_id = None
                md = st.date_input("Data *", key="mkt_d")
                mi = st.number_input("Impressões", min_value=0, step=100, value=1000)
                mk = st.number_input("Cliques", min_value=0, step=10, value=50)
            with c2:
                ml = st.number_input("Leads", min_value=0, step=1, value=5)
                mv = st.number_input("Conversões", min_value=0, step=1, value=0)
                mc_val = st.number_input("Custo (R$)", min_value=0.0, step=50.0, value=0.0)
                mp = st.selectbox("Plataforma", ["Google Ads", "Meta Ads", "TikTok Ads", "LinkedIn Ads", "Outro"])
            if st.form_submit_button("📊 Salvar Métricas", type="primary"):
                if not sm_id:
                    st.error("Selecione um projeto!")
                else:
                    with st.spinner("Salvando..."):
                        r, e = make_request("POST", "/manual/marketing-metrics", json={
                            "project_id": sm_id,
                            "date": datetime.combine(md, datetime.min.time()).isoformat(),
                            "impressions": mi, "clicks": mk, "leads": ml,
                            "conversions": mv,
                            "cost": mc_val if mc_val > 0 else None,
                            "platform": mp,
                        })
                    if r and not e:
                        st.success(f"✅ {r['message']}")
                        if "ctr" in r:
                            st.info(f"📈 CTR: {r['ctr']} | Conv: {r['conversion_rate']}")
                        st.balloons()
                    else:
                        st.error(e)

    st.markdown("---")
    st.info(
        "**Memória RAG**: Todos os lançamentos criam registros na memória da IA.\n\n"
        "**Auditoria**: Cada operação é registrada no log de auditoria."
    )


# ╔═══════════════════════════════════════════════════════════════╗
# ║             ⚙️  SYSTEM CORE — LOGS DE AUDITORIA              ║
# ╚═══════════════════════════════════════════════════════════════╝

elif page == "📝 Logs de Auditoria":
    st.markdown('<p class="main-header">📝 Logs de Auditoria</p>', unsafe_allow_html=True)
    st.markdown("**Registros automáticos de toda operação de escrita na API.**")

    st.markdown("---")

    # Tenta buscar logs
    audit_data, audit_err = make_request("GET", "/audit-logs", params={"limit": 50})

    if audit_data and not audit_err:
        if isinstance(audit_data, list) and len(audit_data) > 0:
            df = pd.DataFrame(audit_data)
            display_cols = [c for c in ["timestamp", "method", "path", "status_code", "duration_ms", "client_ip"] if c in df.columns]
            if display_cols:
                st.dataframe(df[display_cols], use_container_width=True, hide_index=True)
            else:
                st.dataframe(df, use_container_width=True, hide_index=True)

            # Métricas
            st.markdown("### 📊 Estatísticas")
            s1, s2, s3 = st.columns(3)
            with s1:
                st.metric("Total de Logs", len(audit_data))
            with s2:
                avg_dur = sum(r.get("duration_ms", 0) for r in audit_data) / len(audit_data)
                st.metric("Duração Média", f"{avg_dur:.0f} ms")
            with s3:
                errors = len([r for r in audit_data if r.get("status_code", 200) >= 400])
                st.metric("Erros (4xx/5xx)", errors)
        else:
            st.info("Nenhum log de auditoria registrado ainda. Faça uma operação POST/PUT/PATCH/DELETE para gerar logs.")
    else:
        # Endpoint não existe — mostra instrução
        st.warning("O endpoint `GET /audit-logs` ainda não foi criado no backend.")
        st.info(
            "**O middleware de auditoria já está ativo** e registrando todas as operações "
            "de escrita na tabela `audit_logs`.\n\n"
            "Para visualizar os logs aqui, adicione o endpoint `GET /audit-logs` no backend.\n\n"
            "**Enquanto isso**, consulte diretamente:\n"
            "```sql\n"
            "SELECT timestamp, method, path, status_code, duration_ms, client_ip\n"
            "FROM audit_logs ORDER BY timestamp DESC LIMIT 50;\n"
            "```"
        )


# ╔═══════════════════════════════════════════════════════════════╗
# ║             ⚙️  SYSTEM CORE — CONFIGURAÇÕES                  ║
# ╚═══════════════════════════════════════════════════════════════╝

elif page == "⚙️ Configurações":
    st.markdown('<p class="main-header">⚙️ Configurações de Perfil</p>', unsafe_allow_html=True)

    st.markdown("---")

    with st.container(border=True):
        st.markdown("### 👤 Informações do Usuário")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**Usuário:** {st.session_state.get('username', 'N/A')}")
            st.markdown(f"**Perfil:** {st.session_state.get('user_role', 'N/A').upper()}")
        with c2:
            st.markdown(f"**API:** `{API_BASE_URL}`")
            st.markdown(f"**Versão:** 2.0.0 (Modular)")

    with st.container(border=True):
        st.markdown("### 🔌 Conexão com API")
        health, herr = make_request("GET", "/", timeout=5)
        if health and not herr:
            st.success(f"✅ API Online — {health.get('service','')} v{health.get('version','')}")
        else:
            st.error(f"❌ API Offline: {herr}")

        db_test, db_err = make_request("GET", "/db-test", timeout=10)
        if db_test and not db_err:
            st.success(f"✅ Banco de dados OK — pgvector: {db_test.get('pgvector_extension','?')}")
        else:
            st.warning(f"⚠️ Teste de banco: {db_err}")

    with st.container(border=True):
        st.markdown("### 🏗️ Arquitetura Modular")
        st.markdown("""
        | Módulo | Router | Endpoints |
        |--------|--------|-----------|
        | 🚀 Growth & Sales | `sales_router` | `/clients/*`, `/interactions/*`, `/radar/*` |
        | 🧠 Agency Brain | `brain_router` | `/ai/*`, `/brain/*` |
        | 💰 Finance & Ops | `finance_router` | `/projects/*`, `/revenues/*`, `/expenses/*`, `/manual/*` |
        | 🔐 Auth | `auth_router` | `/login`, `/db-test` |
        | 📝 Auditoria | `AuditMiddleware` | Automático (POST/PUT/PATCH/DELETE) |
        """)

    with st.container(border=True):
        st.markdown("### ⚠️ Ações")
        if st.button("🚪 Logout", type="primary", use_container_width=True):
            logout()


# ═══════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════

st.markdown("---")
st.markdown("""
<div style='text-align:center; color:#666; padding:.8rem;'>
    <p>🚀 <strong>Vyron System</strong> v2.0 — Modular Architecture</p>
    <p><small>FastAPI + Streamlit + OpenAI | 2026</small></p>
</div>
""", unsafe_allow_html=True)
