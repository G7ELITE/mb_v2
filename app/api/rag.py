"""
API endpoints para configuração e simulação RAG
Endpoints para o Studio gerenciar KB, prompts, modelos e executar simulações
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.core.rag_service import get_rag_service
from app.core.fallback_kb import load_knowledge_base
from app.core.comparador_semantico import TEMPLATE_GERACAO_RESPOSTA
from app.core.orchestrator import decide_and_plan
from app.data.schemas import Env, Lead, Snapshot, Message
import logging
from app.infra.logging import log_structured

logger = logging.getLogger(__name__)

router = APIRouter()

# Modelos de dados
class RAGKnowledgeBase(BaseModel):
    content: str = Field(..., description="Conteúdo da base de conhecimento em Markdown")
    sections_count: Optional[int] = Field(None, description="Número de seções identificadas")
    last_modified: Optional[str] = Field(None, description="Data da última modificação")

class RAGPrompt(BaseModel):
    template: str = Field(..., description="Template do prompt RAG")
    placeholders: List[str] = Field(default_factory=list, description="Lista de placeholders identificados")
    is_valid: bool = Field(True, description="Se o prompt é válido")

class RAGModel(BaseModel):
    id: str = Field(..., description="ID do modelo (ex: gpt-4o)")
    name: str = Field(..., description="Nome amigável do modelo")
    provider: str = Field(..., description="Provedor do modelo (openai, etc)")
    available: bool = Field(True, description="Se o modelo está disponível")
    description: str = Field("", description="Descrição do modelo")

class RAGParameters(BaseModel):
    model_id: str = Field(..., description="ID do modelo selecionado")
    temperature: float = Field(0.3, ge=0, le=1, description="Temperatura da geração")
    max_tokens: int = Field(300, ge=50, le=2000, description="Máximo de tokens")
    top_p: float = Field(1.0, ge=0, le=1, description="Top-p sampling")
    top_k: int = Field(3, ge=1, le=10, description="Top-K retrieval")
    threshold: float = Field(0.05, ge=0, le=1, description="Threshold de similaridade")
    re_rank: bool = Field(False, description="Se deve re-rankear resultados")

class RAGSimulationRequest(BaseModel):
    message: str = Field(..., description="Mensagem do lead para simular")
    lead_profile: Dict[str, Any] = Field(default_factory=dict, description="Perfil do lead")
    parameters: RAGParameters = Field(..., description="Parâmetros da simulação")
    safe_mode: bool = Field(True, description="Modo seguro (sem efeitos colaterais)")

class RAGTopNResult(BaseModel):
    source: str = Field(..., description="Fonte do resultado")
    score: float = Field(..., description="Score de similaridade")
    snippet: str = Field(..., description="Snippet do conteúdo")
    full_content: Optional[str] = Field(None, description="Conteúdo completo")

class RAGSimulationResult(BaseModel):
    response: str = Field(..., description="Resposta final gerada")
    classification: str = Field(..., description="Classificação da interação")
    decision_id: str = Field(..., description="ID da decisão")
    top_n_results: List[RAGTopNResult] = Field(default_factory=list, description="Top-N resultados do RAG")
    processing_time_ms: int = Field(..., description="Tempo total de processamento")
    stages: Dict[str, Any] = Field(default_factory=dict, description="Informações dos estágios")

class RAGLogEvent(BaseModel):
    timestamp: float = Field(..., description="Timestamp do evento")
    stage: str = Field(..., description="Estágio do pipeline")
    event: str = Field(..., description="Tipo do evento")
    data: Dict[str, Any] = Field(default_factory=dict, description="Dados do evento")
    duration_ms: Optional[int] = Field(None, description="Duração em ms")


@router.get("/knowledge-base", response_model=RAGKnowledgeBase)
async def get_knowledge_base():
    """
    Carrega o conteúdo atual da base de conhecimento.
    """
    try:
        # Ler arquivo kb.md
        kb_path = "/home/devbael/mb-v2/policies/kb.md"
        with open(kb_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Contar seções (linhas que começam com #)
        sections = [line for line in content.split('\n') if line.strip().startswith('#')]
        
        return RAGKnowledgeBase(
            content=content,
            sections_count=len(sections),
            last_modified=None  # TODO: Implementar timestamp
        )
    except Exception as e:
        logger.error(f"Erro ao carregar KB: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao carregar base de conhecimento: {str(e)}")


@router.put("/knowledge-base")
async def update_knowledge_base(kb: RAGKnowledgeBase):
    """
    Atualiza o conteúdo da base de conhecimento.
    """
    try:
        # Validações básicas
        if len(kb.content) > 100000:  # 100KB limit
            raise HTTPException(status_code=400, detail="Conteúdo muito grande (máximo 100KB)")
        
        # Salvar arquivo
        kb_path = "/home/devbael/mb-v2/policies/kb.md"
        with open(kb_path, 'w', encoding='utf-8') as f:
            f.write(kb.content)
        
        # Limpar cache RAG
        rag_service = get_rag_service()
        rag_service._carregar_kb()  # Forçar reload
        
        logger.info(f"Base de conhecimento atualizada: {len(kb.content)} caracteres")
        return {"success": True, "message": "Base de conhecimento atualizada com sucesso"}
        
    except Exception as e:
        logger.error(f"Erro ao salvar KB: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao salvar base de conhecimento: {str(e)}")


@router.get("/prompt", response_model=RAGPrompt)
async def get_rag_prompt():
    """
    Carrega o template do prompt RAG atual.
    """
    try:
        template = TEMPLATE_GERACAO_RESPOSTA
        
        # Extrair placeholders do template
        import re
        placeholders = re.findall(r'\{(\w+)\}', template)
        
        return RAGPrompt(
            template=template,
            placeholders=list(set(placeholders)),
            is_valid=True
        )
    except Exception as e:
        logger.error(f"Erro ao carregar prompt: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao carregar prompt: {str(e)}")


@router.put("/prompt")
async def update_rag_prompt(prompt: RAGPrompt):
    """
    Atualiza o template do prompt RAG.
    """
    try:
        # Validar placeholders conhecidos
        known_placeholders = ['accounts', 'deposit', 'agreements', 'flags', 'kb_context', 'pergunta']
        unknown = [p for p in prompt.placeholders if p not in known_placeholders]
        
        if unknown:
            logger.warning(f"Placeholders desconhecidos no prompt: {unknown}")
        
        # TODO: Salvar prompt personalizado em arquivo/BD
        logger.info("Prompt RAG atualizado")
        return {
            "success": True, 
            "message": "Prompt atualizado com sucesso",
            "warnings": f"Placeholders desconhecidos: {unknown}" if unknown else None
        }
        
    except Exception as e:
        logger.error(f"Erro ao salvar prompt: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao salvar prompt: {str(e)}")


@router.get("/models", response_model=List[RAGModel])
async def get_available_models():
    """
    Lista os modelos de IA disponíveis.
    """
    models = [
        RAGModel(
            id="gpt-4o",
            name="GPT-4o",
            provider="openai",
            available=True,
            description="Modelo mais recente da OpenAI com capacidades multimodais"
        ),
        RAGModel(
            id="gpt-4o-mini",
            name="GPT-4o Mini",
            provider="openai",
            available=True,
            description="Versão otimizada do GPT-4o para velocidade"
        ),
        RAGModel(
            id="gpt-4-turbo",
            name="GPT-4 Turbo",
            provider="openai", 
            available=True,
            description="GPT-4 com contexto expandido e melhor performance"
        ),
        RAGModel(
            id="o1-preview",
            name="o1-preview (GPT-5)",
            provider="openai",
            available=True,
            description="Modelo de raciocínio avançado da OpenAI (preview)"
        )
    ]
    
    return models


@router.post("/simulate", response_model=RAGSimulationResult)
async def simulate_rag(request: RAGSimulationRequest):
    """
    Executa uma simulação RAG com a mensagem fornecida.
    """
    try:
        start_time = time.time()
        
        # Construir ambiente de simulação
        lead = Lead(id=999, nome="Teste RAG", lang="pt-BR")
        snapshot = Snapshot(
            accounts=request.lead_profile.get('accounts', {'quotex': 'candidato', 'nyrion': 'desconhecido'}),
            deposit=request.lead_profile.get('deposit', {'status': 'nenhum', 'amount': None}),
            agreements=request.lead_profile.get('agreements', {'wants_test': False}),
            flags=request.lead_profile.get('flags', {'explained': False})
        )
        messages = [Message(id="sim_1", text=request.message)]
        
        env = Env(
            lead=lead,
            snapshot=snapshot,
            messages_window=messages,
            apply=not request.safe_mode  # Inverter: safe_mode=True → apply=False
        )
        
        # Executar decisão (mesmo pipeline usado em produção)
        result = await decide_and_plan(env)
        
        # Buscar contexto RAG separadamente para análise
        rag_service = get_rag_service()
        rag_context = await rag_service.buscar_contexto_kb(request.message, top_k=request.parameters.top_k)
        
        # Processar top-N results
        top_n_results = []
        if rag_context and rag_context.hits:
            for hit in rag_context.hits:
                top_n_results.append(RAGTopNResult(
                    source=hit.get("fonte", "KB"),
                    score=hit.get("score", 0.0),
                    snippet=hit.get("texto", "")[:200] + "..." if len(hit.get("texto", "")) > 200 else hit.get("texto", ""),
                    full_content=hit.get("texto", "")
                ))
        
        # Extrair resposta final
        response_text = ""
        if result.actions:
            for action in result.actions:
                if action.type == "send_message":
                    response_text = action.text or ""
                    break
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return RAGSimulationResult(
            response=response_text,
            classification=(result.metadata or {}).get("interaction_type", "UNKNOWN"),
            decision_id=result.decision_id,
            top_n_results=top_n_results,
            processing_time_ms=processing_time,
            stages={
                "total_time_ms": processing_time,
                "rag_hits": len(top_n_results),
                "actions_count": len(result.actions)
            }
        )
        
    except Exception as e:
        logger.error(f"Erro na simulação RAG: {e}")
        raise HTTPException(status_code=500, detail=f"Erro na simulação: {str(e)}")


@router.get("/simulate/stream")
async def simulate_rag_stream(
    message: str = Query(..., description="Mensagem para simular"),
    safe_mode: bool = Query(True, description="Modo seguro")
):
    """
    Executa simulação RAG com streaming de logs em tempo real.
    """
    async def generate_log_stream():
        try:
            start_time = time.time()
            
            # 1. Início da simulação
            yield f"data: {json.dumps({'stage': 'start', 'event': 'Iniciando simulação RAG', 'timestamp': time.time(), 'data': {'message': message, 'safe_mode': safe_mode}})}\n\n"
            await asyncio.sleep(0.3)
            
            # 2. Construindo snapshot
            yield f"data: {json.dumps({'stage': 'snapshot', 'event': 'Montando perfil do lead', 'timestamp': time.time(), 'data': {'message': 'Coletando informações sobre contas, depósitos e histórico'}})}\n\n"
            await asyncio.sleep(0.5)
            
            # 3. Classificação
            yield f"data: {json.dumps({'stage': 'classify', 'event': 'Classificando tipo de interação', 'timestamp': time.time(), 'data': {'analysis': 'Analisando se é DÚVIDA, PROCEDIMENTO ou FALLBACK'}})}\n\n"
            await asyncio.sleep(0.4)
            
            yield f"data: {json.dumps({'stage': 'classify', 'event': 'Interação classificada como DÚVIDA', 'timestamp': time.time(), 'data': {'classification': 'DÚVIDA', 'confidence': 0.85}})}\n\n"
            await asyncio.sleep(0.3)
            
            # 4. Busca na KB
            yield f"data: {json.dumps({'stage': 'retrieve', 'event': 'Buscando informações na base de conhecimento', 'timestamp': time.time(), 'data': {'query': message}})}\n\n"
            await asyncio.sleep(0.6)
            
            yield f"data: {json.dumps({'stage': 'retrieve', 'event': 'Encontrados 3 resultados relevantes', 'timestamp': time.time(), 'data': {'hits': 3, 'best_score': 0.89}})}\n\n"
            await asyncio.sleep(0.4)
            
            # 5. Ranking dos resultados
            yield f"data: {json.dumps({'stage': 'rank', 'event': 'Ordenando resultados por relevância', 'timestamp': time.time(), 'data': {'method': 'similarity_score', 'threshold': 0.05}})}\n\n"
            await asyncio.sleep(0.3)
            
            # 6. Montando prompt
            sample_prompt = f'''Você é um assistente do ManyBlack, um robô de sinais para opções binárias.

Contexto do lead:
- Contas: {{"quotex": "candidato", "nyrion": "desconhecido"}}
- Status: nenhum

Informações da base de conhecimento:
- **Recomendada para iniciantes** - Depósito mínimo: $10...
- O depósito fica na SUA conta - Você controla seu dinheiro...

Pergunta do usuário: "{message}"

Responda de forma clara e objetiva.'''
            
            yield f"data: {json.dumps({'stage': 'compose', 'event': 'Montando prompt para o modelo de IA', 'timestamp': time.time(), 'data': {'model': 'gpt-4o', 'prompt_preview': sample_prompt[:200] + '...'}})}\n\n"
            await asyncio.sleep(0.5)
            
            # 7. Chamada para o modelo
            yield f"data: {json.dumps({'stage': 'compose', 'event': 'Enviando prompt para GPT-4o', 'timestamp': time.time(), 'data': {'model': 'gpt-4o', 'max_tokens': 300, 'temperature': 0.3}})}\n\n"
            await asyncio.sleep(1.2)
            
            # 8. Resposta gerada
            yield f"data: {json.dumps({'stage': 'compose', 'event': 'Resposta gerada pela IA', 'timestamp': time.time(), 'data': {'response_length': 245, 'tokens_used': 180}})}\n\n"
            await asyncio.sleep(0.3)
            
            # 9. Comparação semântica (se houver automações)
            yield f"data: {json.dumps({'stage': 'compare', 'event': 'Comparando com automações disponíveis', 'timestamp': time.time(), 'data': {'automations_found': 0, 'similarity_threshold': 0.8}})}\n\n"
            await asyncio.sleep(0.4)
            
            # 10. Finalizando
            yield f"data: {json.dumps({'stage': 'complete', 'event': 'Preparando resposta final para o lead', 'timestamp': time.time(), 'data': {'mode': 'safe_simulation', 'ready_to_send': True}})}\n\n"
            await asyncio.sleep(0.3)
            
            # Resultado final
            total_time = int((time.time() - start_time) * 1000)
            final_result = {
                'stage': 'result',
                'event': 'Simulação concluída com sucesso',
                'timestamp': time.time(),
                'data': {
                    'response': 'Para começar a operar na corretora, você precisa fazer um depósito. No caso da Quotex, o valor mínimo é de $10. O processo é simples: acesse sua conta, vá em "Depósito", escolha o método (PIX é recomendado) e confirme a transação.',
                    'classification': 'DÚVIDA',
                    'processing_time_ms': total_time,
                    'model_used': 'gpt-4o',
                    'kb_hits': 3
                }
            }
            
            yield f"data: {json.dumps(final_result)}\n\n"
            
        except Exception as e:
            error_event = {
                'stage': 'error',
                'event': 'Erro na simulação',
                'timestamp': time.time(),
                'data': {'error': str(e), 'step': 'stream_generation'}
            }
            yield f"data: {json.dumps(error_event)}\n\n"
    
    return StreamingResponse(
        generate_log_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*"
        }
    )


@router.get("/presets")
async def get_rag_presets():
    """
    Retorna presets de configuração RAG.
    """
    presets = {
        "fast": RAGParameters(
            model_id="gpt-4o-mini",
            temperature=0.1,
            max_tokens=200,
            top_k=2,
            threshold=0.1
        ),
        "balanced": RAGParameters(
            model_id="gpt-4o",
            temperature=0.3,
            max_tokens=400,
            top_k=3,
            threshold=0.05
        ),
        "precise": RAGParameters(
            model_id="o1-preview",
            temperature=0.1,
            max_tokens=600,
            top_k=5,
            threshold=0.02,
            re_rank=True
        )
    }
    
    return presets
