"""
SpyService — Serviço de Inteligência Competitiva (v1.2)

Analisa presença digital de concorrentes identificados via Lead Discovery.
Simula coleta de dados SEO / Ads e indexa insights na memória RAG
para uso pelo Agency Brain em reuniões estratégicas.
"""
import hashlib
import logging
import random
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from app import models
from app.services import generate_embedding

log = logging.getLogger("vyron.spy_service")

# ── Dados simulados para análise inicial ───────────────────────
_TECH_STACKS = [
    "WordPress + WooCommerce",
    "Shopify",
    "React + Next.js (Vercel)",
    "HTML/CSS puro",
    "Wix",
    "Squarespace",
    "Magento 2",
    "Laravel + Vue.js",
    "Django + HTMX",
    "Webflow",
]

_ADS_PLATFORMS = [
    "Google Ads",
    "Meta Ads",
    "LinkedIn Ads",
    "TikTok Ads",
    "Google Ads, Meta Ads",
    "Nenhum detectado",
]

_TRAFFIC_TIERS = ["low", "medium", "high", "very_high"]


def _deterministic_seed(name: str, url: str | None) -> int:
    """Gera seed determinística para manter consistência entre análises."""
    raw = f"{name}|{url or ''}".lower()
    return int(hashlib.md5(raw.encode()).hexdigest()[:8], 16)


class SpyService:
    """
    Serviço responsável por análise de presença digital de concorrentes.

    Fase 1 (atual): dados simulados com distribuição determinística.
    Fase 2 (futura): integração com APIs reais (SimilarWeb, SEMrush, BuiltWith).
    """

    @staticmethod
    async def analyze_competitor_presence(
        db: Session,
        lead: models.LeadDiscovery,
        website_url: Optional[str] = None,
        force_refresh: bool = False,
    ) -> models.CompetitorIntel:
        """
        Analisa presença digital do concorrente associado a um lead.

        Args:
            db: Sessão SQLAlchemy.
            lead: Registro LeadDiscovery alvo.
            website_url: URL opcional para análise (sobrescreve derivação).
            force_refresh: Se True, refaz análise mesmo se já existir.

        Returns:
            CompetitorIntel persistido no banco.
        """
        # 1. Verifica análise existente (skip se force_refresh)
        if not force_refresh:
            existing = (
                db.query(models.CompetitorIntel)
                .filter(models.CompetitorIntel.lead_id == lead.id)
                .order_by(models.CompetitorIntel.last_spy_at.desc())
                .first()
            )
            if existing:
                log.info("Intel existente para lead '%s' — retornando cache.", lead.name)
                return existing

        # 2. Resolve URL do alvo
        resolved_url = website_url or f"https://{lead.name.lower().replace(' ', '')}.com.br"

        # 3. Simulação de análise de presença digital
        seed = _deterministic_seed(lead.name, resolved_url)
        rng = random.Random(seed)

        tech_stack = rng.choice(_TECH_STACKS)
        ads_platform = rng.choice(_ADS_PLATFORMS)
        traffic_tier = rng.choices(
            _TRAFFIC_TIERS, weights=[40, 35, 20, 5], k=1
        )[0]
        market_sentiment = round(rng.uniform(-0.3, 0.9), 2)

        # 4. Monta sumário analítico
        summary_lines = [
            f"🔍 Análise de Presença Digital — {lead.name}",
            f"🌐 URL: {resolved_url}",
            f"🛠️ Tech Stack: {tech_stack}",
            f"📢 Ads: {ads_platform}",
            f"📊 Tráfego Estimado: {traffic_tier}",
            f"📈 Sentimento de Mercado: {market_sentiment}",
            "",
            "💡 Insights:",
        ]

        if ads_platform != "Nenhum detectado":
            summary_lines.append(
                f"  • Concorrente investe em {ads_platform} — considere segmentação oposta."
            )
        else:
            summary_lines.append(
                "  • Sem presença paga detectada — oportunidade de domínio via Ads."
            )

        if traffic_tier in ("high", "very_high"):
            summary_lines.append(
                "  • Tráfego alto indica marca consolidada. Estratégia recomendada: diferenciação."
            )
        else:
            summary_lines.append(
                "  • Tráfego baixo/moderado — possível brecha para captura de mercado."
            )

        analysis_summary = "\n".join(summary_lines)

        # 5. Persiste CompetitorIntel
        intel = models.CompetitorIntel(
            id=uuid4(),
            lead_id=lead.id,
            competitor_name=lead.name,
            website_url=resolved_url,
            ads_platform=ads_platform,
            estimated_traffic_tier=traffic_tier,
            tech_stack=tech_stack,
            market_sentiment=market_sentiment,
            analysis_summary=analysis_summary,
            last_spy_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
        )
        db.add(intel)
        db.flush()

        # 6. Indexa no RAG (DocumentChunk) para Agency Brain
        rag_indexed = await SpyService._index_intel_rag(db, lead, intel, analysis_summary)

        db.commit()
        db.refresh(intel)

        log.info(
            "Intel criada para '%s' — tráfego=%s, ads=%s, rag=%s",
            lead.name, traffic_tier, ads_platform, rag_indexed,
        )
        return intel

    @staticmethod
    async def _index_intel_rag(
        db: Session,
        lead: models.LeadDiscovery,
        intel: models.CompetitorIntel,
        content: str,
    ) -> bool:
        """
        Salva o insight de inteligência competitiva como DocumentChunk
        para que o Agency Brain possa acessar via busca semântica.

        Returns:
            True se o embedding foi gerado e salvo com sucesso.
        """
        try:
            embedding = await generate_embedding(content)

            chunk = models.DocumentChunk(
                id=uuid4(),
                filename=f"spy_intel/{lead.name.lower().replace(' ', '_')}_{intel.id}",
                chunk_index=0,
                content=content,
                embedding=embedding,
                metadata_json={
                    "source_type": "competitor_intel",
                    "lead_id": str(lead.id),
                    "intel_id": str(intel.id),
                    "competitor_name": intel.competitor_name,
                    "ads_platform": intel.ads_platform,
                    "traffic_tier": intel.estimated_traffic_tier,
                    "market_sentiment": float(intel.market_sentiment) if intel.market_sentiment else None,
                    "analyzed_at": intel.last_spy_at.isoformat(),
                },
                created_at=datetime.utcnow(),
            )
            db.add(chunk)
            log.info("RAG chunk indexado para intel '%s'.", intel.competitor_name)
            return True

        except Exception as exc:
            log.warning("Falha ao indexar intel no RAG: %s", exc)
            return False
