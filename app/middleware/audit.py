"""
Audit Middleware — Registra toda ação de alteração de dados no banco.

Intercepta requisições POST, PATCH, PUT e DELETE, armazenando:
- Quem (IP, User-Agent)
- O quê (método, path, body resumido)
- Quando (timestamp)
- Resultado (status code, duração)
"""

import time
import json
from uuid import uuid4
from datetime import datetime

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.database import SessionLocal
from app.models import AuditLog


# Métodos que representam alteração de dados
_WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

# Paths que NÃO devem ser auditados (health-checks, GET-only, etc.)
_SKIP_PATHS = {"/", "/docs", "/openapi.json", "/redoc", "/db-test"}


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware que intercepta requisições de escrita e grava um registro
    na tabela audit_logs com detalhes da ação.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # Só audita métodos de escrita
        if request.method not in _WRITE_METHODS:
            return await call_next(request)

        # Ignora paths de infraestrutura
        if request.url.path in _SKIP_PATHS:
            return await call_next(request)

        # Captura dados da request
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "")[:500]
        path = request.url.path

        # Tenta ler o body (para POST/PUT/PATCH)
        request_body = None
        try:
            body_bytes = await request.body()
            if body_bytes:
                body_text = body_bytes.decode("utf-8", errors="replace")
                # Tenta parsear como JSON, limitando tamanho
                try:
                    body_json = json.loads(body_text)
                    # Remove campos sensíveis
                    for sensitive_key in ("password", "password_hash", "token", "secret", "image"):
                        if sensitive_key in body_json:
                            body_json[sensitive_key] = "***REDACTED***"
                    request_body = body_json
                except (json.JSONDecodeError, ValueError):
                    # Não é JSON (multipart upload, etc.) — guarda resumo
                    request_body = {"_raw_preview": body_text[:200]}
        except Exception:
            pass  # Se não conseguir ler, segue sem body

        # Executa a requisição real
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = int((time.perf_counter() - start) * 1000)

        # Grava no banco de forma assíncrona (em thread separada para não bloquear)
        try:
            db = SessionLocal()
            try:
                log_entry = AuditLog(
                    id=uuid4(),
                    timestamp=datetime.utcnow(),
                    method=request.method,
                    path=path,
                    status_code=response.status_code,
                    user_agent=user_agent,
                    client_ip=client_ip,
                    request_body=request_body,
                    response_summary=f"{response.status_code} in {duration_ms}ms",
                    duration_ms=duration_ms,
                )
                db.add(log_entry)
                db.commit()
            except Exception as exc:
                db.rollback()
                # Log silencioso — middleware não deve derrubar a requisição
                print(f"⚠️ Audit log falhou: {exc}")
            finally:
                db.close()
        except Exception:
            pass  # Pool exausto ou DB offline — ignora silenciosamente

        return response
