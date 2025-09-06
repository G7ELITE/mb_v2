"""
API endpoints para tela EQUIPE
Sistema RAG dedicado para equipe de atendimento com histórico de interações
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.rag_service import get_rag_service
from app.core.fallback_kb import load_knowledge_base
from app.core.comparador_semantico import TEMPLATE_GERACAO_RESPOSTA
from app.core.orchestrator import decide_and_plan
from app.core.rag_prompt_manager import get_current_rag_prompt
from app.data.models import EquipeInteracao
from app.infra.db import get_db
from app.settings import settings
from app.infra.logging import log_structured

logger = logging.getLogger(__name__)
router = APIRouter()

# Modelos de dados para a API da EQUIPE
# IMPORTAR RAGParameters da API RAG para garantir consistência 100%
class RAGParameters(BaseModel):
    """Parâmetros idênticos aos da API RAG"""
    model_id: str = Field(..., description="ID do modelo selecionado")
    temperature: float = Field(0.3, ge=0, le=1, description="Temperatura da geração")
    max_tokens: int = Field(300, ge=50, le=2000, description="Máximo de tokens")
    top_p: float = Field(1.0, ge=0, le=1, description="Top-p sampling")
    top_k: int = Field(3, ge=1, le=10, description="Top-K retrieval")
    threshold: float = Field(0.65, ge=0, le=1, description="Threshold de similaridade")
    re_rank: bool = Field(False, description="Se deve re-rankear resultados")
    enable_semantic_comparison: bool = Field(False, description="Se deve comparar resposta com automações")

class EquipeSimulationRequest(BaseModel):
    """Requisição de simulação para equipe - IDÊNTICA à RAG"""
    message: str = Field(..., description="Mensagem do funcionário para simular")
    parameters: RAGParameters = Field(..., description="Parâmetros da simulação (MESMOS da RAG)")
    safe_mode: bool = Field(False, description="Modo seguro (sem efeitos colaterais)")
    session_id: Optional[str] = None
    funcionario_id: Optional[str] = None

class EquipeSimulationResult(BaseModel):
    """Resultado de simulação para equipe"""
    response: str
    kb_hits: List[Dict[str, Any]] = []
    parameters_used: Dict[str, Any] = {}
    execution_time: float = 0.0
    session_id: str
    interaction_id: int
    created_at: str

class EquipeInteractionHistory(BaseModel):
    """Histórico de interação da equipe"""
    id: int
    pergunta_funcionario: str
    resposta_gerada: str
    parametros_rag: Optional[Dict[str, Any]]
    fontes_kb: Optional[Dict[str, Any]]
    funcionario_id: Optional[str]
    sessao_id: Optional[str]
    criado_em: str

@router.get("/parameters", response_model=Dict[str, Any])
async def get_equipe_parameters():
    """
    Retorna configurações de parâmetros disponíveis (mesmo da RAG)
    """
    try:
        # Reutilizar configurações da RAG existente
        rag_service = get_rag_service()
        
        return {
            "presets": {
                "conservative": {
                    "model_id": "gpt-4o-mini",
                    "temperature": 0.1,
                    "max_tokens": 500,
                    "top_p": 0.8,
                    "top_k": 3,
                    "threshold": 0.85,
                    "re_rank": True
                },
                "balanced": {
                    "model_id": "gpt-4o-mini",
                    "temperature": 0.3,
                    "max_tokens": 800,
                    "top_p": 0.9,
                    "top_k": 5,
                    "threshold": 0.75,
                    "re_rank": True
                },
                "creative": {
                    "model_id": "gpt-4o-mini", 
                    "temperature": 0.7,
                    "max_tokens": 1000,
                    "top_p": 0.95,
                    "top_k": 7,
                    "threshold": 0.65,
                    "re_rank": False
                }
            },
            "models": [
                {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "description": "Modelo padrão otimizado"},
                {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "description": "Modelo rápido"}
            ]
        }
    except Exception as e:
        logger.error(f"Erro ao obter parâmetros da equipe: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/knowledge-base", response_model=Dict[str, Any])
async def get_equipe_knowledge_base():
    """
    Retorna informações sobre a knowledge base (mesmo da RAG)
    """
    try:
        kb = load_knowledge_base()
        return {
            "status": "loaded" if kb else "empty",
            "topics": len(kb) if kb else 0,
            "last_updated": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Erro ao obter knowledge base da equipe: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/prompt", response_model=Dict[str, Any])
async def get_equipe_prompt():
    """
    Retorna o prompt atual (mesmo da RAG)
    """
    try:
        from app.core.rag_prompt_manager import is_using_custom_prompt
        
        prompt_content = get_current_rag_prompt()
        is_custom = is_using_custom_prompt()
        
        return {
            "content": prompt_content,
            "is_custom": is_custom,
            "last_modified": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Erro ao obter prompt da equipe: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.post("/simulate", response_model=EquipeSimulationResult)
async def simulate_equipe_response(
    request: EquipeSimulationRequest,
    db: Session = Depends(get_db)
):
    """
    Simula resposta RAG para a equipe e salva no banco
    """
    start_time = time.time()
    
    try:
        # Gerar session_id se não fornecido
        session_id = request.session_id or str(uuid.uuid4())
        
        # Obter serviço RAG
        rag_service = get_rag_service()
        
        # USAR EXATAMENTE OS MESMOS PARÂMETROS DA API RAG
        # Não mais presets - usar request.parameters diretamente como na API RAG
        logger.info(f"🎯 EQUIPE: Usando parâmetros idênticos à API RAG")
        logger.info(f"⚙️ EQUIPE: Modelo: {request.parameters.model_id}, Temp: {request.parameters.temperature}, Threshold: {request.parameters.threshold}")
        
        # Executar simulação RAG usando o mesmo fluxo da API RAG original
        prompt_template = get_current_rag_prompt()
        
        # Buscar contexto na knowledge base - IDÊNTICO à API RAG
        rag_context = await rag_service.buscar_contexto_kb(
            request.message, 
            top_k=request.parameters.top_k
        )
        
        # Preparar contexto KB - USANDO O MESMO MÉTODO DA API RAG
        kb_text = "Nenhuma informação relevante encontrada."
        kb_hits = []
        
        if rag_context and hasattr(rag_context, 'hits') and rag_context.hits:
            # Aplicar threshold primeiro - IDÊNTICO à API RAG
            hits_filtrados = [hit for hit in rag_context.hits if hit.get('score', 0) >= request.parameters.threshold]
            
            # Aplicar re_rank se habilitado - IDÊNTICO à API RAG
            if request.parameters.re_rank:
                # Re-ranking (ordenar por score)
                hits_filtrados = sorted(hits_filtrados, key=lambda x: x.get('score', 0), reverse=True)
            
            # Criar contexto atualizado com hits filtrados - IGUAL À API RAG
            from app.data.schemas import KbContext
            topico = getattr(rag_context, 'topico', 'consulta')
            rag_context_filtrado = KbContext(hits=hits_filtrados, topico=topico)
            
            # USAR O MESMO MÉTODO build_context_string para consistência
            kb_text = rag_context_filtrado.build_context_string()
            
            # Preparar kb_hits para retorno
            if hits_filtrados:
                kb_hits = hits_filtrados
                
            logger.info(f"🎯 CONTEXTO EQUIPE FINAL: {len(hits_filtrados)} hits após threshold {request.parameters.threshold}")
        
        # Formatar prompt com contextos
        formatted_prompt = prompt_template.format(
            historico_mensagens="Primeira interação",
            kb_context=kb_text,
            mensagem_atual=request.message
        )
        
        # Gerar resposta usando OpenAI - ALINHADO COM API RAG
        from openai import AsyncOpenAI
        from app.settings import settings
        
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        logger.info(f"🚀 EQUIPE: Fazendo chamada para OpenAI - Modelo: {request.parameters.model_id}")
        logger.info(f"⚙️ EQUIPE: Parâmetros - temp={request.parameters.temperature}, max_tokens={request.parameters.max_tokens}, top_p={request.parameters.top_p}")
        
        llm_response = await client.chat.completions.create(
            model=request.parameters.model_id,
            messages=[{"role": "user", "content": formatted_prompt}],
            temperature=request.parameters.temperature,
            max_tokens=request.parameters.max_tokens,
            top_p=request.parameters.top_p
        )
        
        response = llm_response.choices[0].message.content.strip()
        logger.info(f"✅ EQUIPE: Resposta recebida - {len(response)} caracteres")
        
        execution_time = time.time() - start_time
        created_at = datetime.now().isoformat()
        
        logger.info(f"⏱️ EQUIPE: Simulação executada em {execution_time:.2f}s")
        
        # Salvar interação no banco
        interacao = EquipeInteracao(
            pergunta_funcionario=request.message,
            resposta_gerada=response,
            parametros_rag={
                "model_id": request.parameters.model_id,
                "temperature": request.parameters.temperature,
                "max_tokens": request.parameters.max_tokens,
                "top_p": request.parameters.top_p,
                "top_k": request.parameters.top_k,
                "threshold": request.parameters.threshold,
                "re_rank": request.parameters.re_rank,
                "enable_semantic_comparison": request.parameters.enable_semantic_comparison
            },
            fontes_kb={"hits": kb_hits, "total": len(kb_hits)},
            resultado_simulacao={
                "execution_time": execution_time,
                "safe_mode": request.safe_mode
            },
            funcionario_id=request.funcionario_id,
            sessao_id=session_id
        )
        
        db.add(interacao)
        db.commit()
        db.refresh(interacao)
        
        logger.info(f"Simulação equipe executada com sucesso - ID: {interacao.id}")
        
        return EquipeSimulationResult(
            response=response,
            kb_hits=kb_hits,
            parameters_used={
                "model_id": request.parameters.model_id,
                "temperature": request.parameters.temperature,
                "max_tokens": request.parameters.max_tokens,
                "top_p": request.parameters.top_p,
                "top_k": request.parameters.top_k,
                "threshold": request.parameters.threshold,
                "re_rank": request.parameters.re_rank
            },
            execution_time=execution_time,
            session_id=session_id,
            interaction_id=interacao.id,
            created_at=created_at
        )
        
    except Exception as e:
        logger.error(f"Erro na simulação da equipe: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro na simulação: {str(e)}")

@router.get("/history", response_model=List[EquipeInteractionHistory])
async def get_equipe_history(
    limit: int = Query(50, ge=1, le=200),
    session_id: Optional[str] = Query(None),
    funcionario_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Retorna histórico de interações da equipe
    """
    try:
        query = db.query(EquipeInteracao)
        
        # Filtros opcionais
        if session_id:
            query = query.filter(EquipeInteracao.sessao_id == session_id)
        
        if funcionario_id:
            query = query.filter(EquipeInteracao.funcionario_id == funcionario_id)
        
        # Ordenar por mais recente e limitar
        interacoes = query.order_by(EquipeInteracao.criado_em.desc()).limit(limit).all()
        
        return [
            EquipeInteractionHistory(
                id=i.id,
                pergunta_funcionario=i.pergunta_funcionario,
                resposta_gerada=i.resposta_gerada,
                parametros_rag=i.parametros_rag,
                fontes_kb=i.fontes_kb,
                funcionario_id=i.funcionario_id,
                sessao_id=i.sessao_id,
                criado_em=i.criado_em.isoformat() if hasattr(i.criado_em, 'isoformat') else str(i.criado_em)
            )
            for i in interacoes
        ]
        
    except Exception as e:
        logger.error(f"Erro ao obter histórico da equipe: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.delete("/history/{interaction_id}")
async def delete_equipe_interaction(
    interaction_id: int,
    db: Session = Depends(get_db)
):
    """
    Remove uma interação específica do histórico
    """
    try:
        interacao = db.query(EquipeInteracao).filter(EquipeInteracao.id == interaction_id).first()
        
        if not interacao:
            raise HTTPException(status_code=404, detail="Interação não encontrada")
        
        db.delete(interacao)
        db.commit()
        
        logger.info(f"Interação {interaction_id} removida do histórico da equipe")
        
        return {"message": "Interação removida com sucesso"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao remover interação da equipe: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/sessions", response_model=List[Dict[str, Any]])
async def get_equipe_sessions(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Retorna lista de sessões da equipe
    """
    try:
        # Buscar sessões únicas com contagem de interações
        from sqlalchemy import func, desc
        
        sessions = (
            db.query(
                EquipeInteracao.sessao_id,
                func.count(EquipeInteracao.id).label('total_interactions'),
                func.max(EquipeInteracao.criado_em).label('last_activity'),
                func.min(EquipeInteracao.criado_em).label('first_activity')
            )
            .filter(EquipeInteracao.sessao_id.isnot(None))
            .group_by(EquipeInteracao.sessao_id)
            .order_by(desc('last_activity'))
            .limit(limit)
            .all()
        )
        
        return [
            {
                "session_id": s.sessao_id,
                "total_interactions": s.total_interactions,
                "last_activity": s.last_activity.isoformat() if hasattr(s.last_activity, 'isoformat') else str(s.last_activity),
                "first_activity": s.first_activity.isoformat() if hasattr(s.first_activity, 'isoformat') else str(s.first_activity)
            }
            for s in sessions
        ]
        
    except Exception as e:
        logger.error(f"Erro ao obter sessões da equipe: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/consultas", response_model=List[EquipeInteractionHistory])
async def get_equipe_consultas(
    search: Optional[str] = Query(None, description="Filtro por texto em pergunta ou resposta"),
    date_from: Optional[str] = Query(None, description="Data inicial (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Data final (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Retorna consultas da equipe com filtros avançados para administração
    """
    try:
        from sqlalchemy import func, or_
        
        query = db.query(EquipeInteracao)
        
        # Filtro por texto (busca em pergunta ou resposta)
        if search:
            search_filter = f"%{search.lower()}%"
            query = query.filter(
                or_(
                    func.lower(EquipeInteracao.pergunta_funcionario).like(search_filter),
                    func.lower(EquipeInteracao.resposta_gerada).like(search_filter)
                )
            )
        
        # Filtros por data
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, "%Y-%m-%d")
                query = query.filter(EquipeInteracao.criado_em >= date_from_obj)
            except ValueError:
                raise HTTPException(status_code=400, detail="Formato de data inválido para date_from. Use YYYY-MM-DD")
        
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, "%Y-%m-%d")
                # Adicionar 23:59:59 para incluir todo o dia
                date_to_obj = date_to_obj.replace(hour=23, minute=59, second=59)
                query = query.filter(EquipeInteracao.criado_em <= date_to_obj)
            except ValueError:
                raise HTTPException(status_code=400, detail="Formato de data inválido para date_to. Use YYYY-MM-DD")
        
        # Ordenar por mais recente e aplicar paginação
        consultas = query.order_by(EquipeInteracao.criado_em.desc()).offset(offset).limit(limit).all()
        
        return [
            EquipeInteractionHistory(
                id=c.id,
                pergunta_funcionario=c.pergunta_funcionario,
                resposta_gerada=c.resposta_gerada,
                parametros_rag=c.parametros_rag,
                fontes_kb=c.fontes_kb,
                funcionario_id=c.funcionario_id,
                sessao_id=c.sessao_id,
                criado_em=c.criado_em.isoformat() if hasattr(c.criado_em, 'isoformat') else str(c.criado_em)
            )
            for c in consultas
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter consultas da equipe: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.put("/consultas/{interaction_id}")
async def update_equipe_consulta(
    interaction_id: int,
    pergunta: str = Query(..., description="Nova pergunta"),
    resposta: str = Query(..., description="Nova resposta"),
    db: Session = Depends(get_db)
):
    """
    Atualiza pergunta e resposta de uma consulta da equipe
    """
    try:
        interacao = db.query(EquipeInteracao).filter(EquipeInteracao.id == interaction_id).first()
        
        if not interacao:
            raise HTTPException(status_code=404, detail="Consulta não encontrada")
        
        # Atualizar campos
        interacao.pergunta_funcionario = pergunta.strip()
        interacao.resposta_gerada = resposta.strip()
        
        db.commit()
        db.refresh(interacao)
        
        logger.info(f"Consulta {interaction_id} atualizada pela equipe")
        
        return {
            "message": "Consulta atualizada com sucesso",
            "id": interaction_id,
            "pergunta": interacao.pergunta_funcionario,
            "resposta": interacao.resposta_gerada
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar consulta da equipe: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.delete("/consultas/bulk")
async def delete_equipe_consultas_bulk(
    interaction_ids: List[int] = Query(..., description="Lista de IDs para deletar"),
    db: Session = Depends(get_db)
):
    """
    Remove múltiplas consultas da equipe
    """
    try:
        if not interaction_ids:
            raise HTTPException(status_code=400, detail="Lista de IDs não pode estar vazia")
        
        # Buscar interações existentes
        interacoes = db.query(EquipeInteracao).filter(EquipeInteracao.id.in_(interaction_ids)).all()
        
        if not interacoes:
            raise HTTPException(status_code=404, detail="Nenhuma consulta encontrada para os IDs fornecidos")
        
        deleted_count = len(interacoes)
        
        # Deletar todas
        for interacao in interacoes:
            db.delete(interacao)
        
        db.commit()
        
        logger.info(f"{deleted_count} consultas removidas em lote pela equipe")
        
        return {
            "message": f"{deleted_count} consultas removidas com sucesso",
            "deleted_ids": [i.id for i in interacoes],
            "deleted_count": deleted_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao remover consultas em lote: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.post("/consultas/export-finetuning")
async def export_equipe_finetuning(
    interaction_ids: List[int] = Query(..., description="Lista de IDs para exportar"),
    db: Session = Depends(get_db)
):
    """
    Exporta consultas selecionadas no formato fine-tuning da OpenAI
    """
    try:
        if not interaction_ids:
            raise HTTPException(status_code=400, detail="Lista de IDs não pode estar vazia")
        
        # Buscar interações existentes
        interacoes = db.query(EquipeInteracao).filter(EquipeInteracao.id.in_(interaction_ids)).all()
        
        if not interacoes:
            raise HTTPException(status_code=404, detail="Nenhuma consulta encontrada para os IDs fornecidos")
        
        # Gerar dados no formato JSONL da OpenAI para fine-tuning
        finetuning_data = []
        for interacao in interacoes:
            # Formato OpenAI: cada linha é um objeto JSON com messages
            line = {
                "messages": [
                    {
                        "role": "user",
                        "content": interacao.pergunta_funcionario.strip()
                    },
                    {
                        "role": "assistant", 
                        "content": interacao.resposta_gerada.strip()
                    }
                ]
            }
            finetuning_data.append(line)
        
        # Criar conteúdo JSONL (cada linha é um JSON separado)
        jsonl_content = "\n".join([json.dumps(item, ensure_ascii=False) for item in finetuning_data])
        
        # Gerar nome do arquivo com timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"equipe_finetuning_{timestamp}.jsonl"
        
        logger.info(f"Exportando {len(interacoes)} consultas para fine-tuning")
        
        return {
            "message": f"{len(interacoes)} consultas exportadas para fine-tuning",
            "filename": filename,
            "content": jsonl_content,
            "format": "OpenAI JSONL",
            "total_samples": len(finetuning_data),
            "exported_ids": interaction_ids
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao exportar para fine-tuning: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")
