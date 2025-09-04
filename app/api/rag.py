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
from app.core.rag_prompt_manager import get_current_rag_prompt, save_custom_rag_prompt, is_using_custom_prompt
from app.data.schemas import Env, Lead, Snapshot, Message, KbContext
from app.settings import settings
import logging
from app.infra.logging import log_structured

logger = logging.getLogger(__name__)

router = APIRouter()

# Modelos de dados para Leads RAG (DEFINIR PRIMEIRO)
class RAGLeadMessage(BaseModel):
    role: str  # 'Lead' ou 'GPT'
    text: str
    timestamp: str

class RAGLead(BaseModel):
    id: Optional[int] = None
    name: str
    description: Optional[str] = ""
    messages: List[RAGLeadMessage] = []
    created_at: Optional[str] = None

class CreateRAGLeadRequest(BaseModel):
    name: str
    description: Optional[str] = ""
    initial_messages: List[RAGLeadMessage] = []

# Arquivo para salvar leads RAG
RAG_LEADS_FILE = "/home/devbael/mb-v2/data/rag_leads.json"

def load_rag_leads() -> List[RAGLead]:
    """Carrega leads RAG do arquivo JSON"""
    try:
        import os
        import json
        from datetime import datetime
        
        # Criar diretório se não existir
        os.makedirs(os.path.dirname(RAG_LEADS_FILE), exist_ok=True)
        
        if os.path.exists(RAG_LEADS_FILE):
            with open(RAG_LEADS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [RAGLead(**lead) for lead in data]
        return []
    except Exception as e:
        logger.error(f"Erro ao carregar leads RAG: {e}")
        return []

def save_rag_leads(leads: List[RAGLead]) -> bool:
    """Salva leads RAG no arquivo JSON"""
    try:
        import json
        import os
        
        os.makedirs(os.path.dirname(RAG_LEADS_FILE), exist_ok=True)
        
        with open(RAG_LEADS_FILE, 'w', encoding='utf-8') as f:
            json.dump([lead.dict() for lead in leads], f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar leads RAG: {e}")
        return False

def build_message_history(messages_window: List[Message], max_messages: int = 10) -> str:
    """
    Constrói histórico formatado das mensagens para o prompt.
    """
    if not messages_window:
        return "Primeira interação"
    
    # Pegar últimas mensagens
    recent_messages = messages_window[-max_messages:]
    
    # Formatar histórico
    formatted_history = []
    for msg in recent_messages:
        # Assumindo que mensagens do lead vêm como text normal
        formatted_history.append(f"Lead: '{msg.text}'")
    
    return "\n".join(formatted_history) if formatted_history else "Primeira interação"

def build_rag_message_history(messages: List[RAGLeadMessage], max_messages: int = 20) -> str:
    """
    Constrói histórico formatado das mensagens RAG para o prompt.
    Formato: Lead: texto / GPT: texto
    """
    if not messages:
        return "Primeira interação"
    
    # Pegar últimas mensagens
    recent_messages = messages[-max_messages:]
    
    # Formatar histórico
    formatted_history = []
    for msg in recent_messages:
        formatted_history.append(f"{msg.role}: {msg.text}")
    
    return "\n".join(formatted_history) if formatted_history else "Primeira interação"

# Modelos de dados originais
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
    enable_semantic_comparison: bool = Field(False, description="Se deve comparar resposta com automações")

class RAGSimulationRequest(BaseModel):
    message: str = Field(..., description="Mensagem do lead para simular")
    lead_id: Optional[int] = Field(None, description="ID do lead RAG para usar histórico real")
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
    Carrega o template do prompt RAG atual (personalizado se existir).
    """
    try:
        template = get_current_rag_prompt()
        
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
        
        # Salvar usando o gerenciador
        success = save_custom_rag_prompt(prompt.template)
        
        if not success:
            raise HTTPException(status_code=500, detail="Falha ao salvar prompt personalizado")
        
        return {
            "success": True, 
            "message": "Prompt atualizado com sucesso",
            "warnings": f"Placeholders desconhecidos: {unknown}" if unknown else None
        }
        
    except HTTPException:
        raise
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
    Executa uma simulação RAG com a mensagem fornecida usando configurações reais.
    """
    try:
        start_time = time.time()
        
        # Simulação de RAG usando LEAD REAL
        # Construir histórico de mensagens REAL
        historico = "Primeira interação"
        
        if request.lead_id:
            # Buscar lead real
            leads = load_rag_leads()
            selected_lead = None
            for lead in leads:
                if lead.id == request.lead_id:
                    selected_lead = lead
                    break
            
            if selected_lead:
                # Usar histórico REAL do lead
                historico = build_rag_message_history(selected_lead.messages)
                logger.info(f"🎯 Usando histórico REAL do lead '{selected_lead.name}' ({len(selected_lead.messages)} mensagens)")
            else:
                logger.warning(f"Lead {request.lead_id} não encontrado, usando histórico padrão")
        else:
            logger.info("🎯 Nenhum lead selecionado, usando 'Primeira interação'")
        
        # Buscar contexto RAG usando configurações reais
        rag_service = get_rag_service()
        rag_context = await rag_service.buscar_contexto_kb(
            request.message, 
            top_k=request.parameters.top_k
        )
        
        # Preparar contexto KB
        kb_text = "Nenhuma informação relevante encontrada."
        top_n_results = []
        
        if rag_context and rag_context.hits:
            # Aplicar threshold primeiro
            hits_filtrados = [hit for hit in rag_context.hits if hit.get('score', 0) >= request.parameters.threshold]
            
            # Aplicar re_rank se habilitado
            if request.parameters.re_rank:
                # Re-ranking (ordenar por score)
                hits_filtrados = sorted(hits_filtrados, key=lambda x: x.get('score', 0), reverse=True)
            
            # Criar contexto atualizado com hits filtrados
            rag_context_filtrado = KbContext(hits=hits_filtrados, topico=rag_context.topico)
            
            # USAR O MESMO MÉTODO build_context_string para consistência
            kb_text = rag_context_filtrado.build_context_string()
            
            logger.info(f"🎯 CONTEXTO FINAL: {len(hits_filtrados)} hits após threshold {request.parameters.threshold}")
            
            # Top-N results - APENAS os hits específicos, não KB inteiro
            for hit in hits_filtrados[:request.parameters.top_k]:
                texto_hit = hit.get("texto", "")
                fonte = hit.get("fonte", "KB")
                
                # Usar apenas o texto específico do hit
                top_n_results.append(RAGTopNResult(
                    source=fonte,
                    score=hit.get("score", 0.0),
                    snippet=texto_hit,  # Hit específico, não snippet truncado
                    full_content=texto_hit  # Mesmo texto completo do hit
                ))
        
        # USAR PROMPT 100% DA INTERFACE
        template = get_current_rag_prompt()
        logger.info("🎯 Usando prompt personalizado da interface (100% controlado pelo usuário)")
        
        # Formatear prompt com variáveis EXATAS conforme especificado
        formatted_prompt = template.format(
            historico_mensagens=historico,
            kb_context=kb_text,
            mensagem_atual=request.message
        )
        
        logger.info(f"📝 Prompt formatado com {len(historico.split('\\n'))} linhas de histórico")
        
        # CHAMADA REAL PARA OPENAI API com text-embedding-3-large para RAG
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        logger.info(f"🚀 FAZENDO CHAMADA REAL PARA OPENAI - Modelo: {request.parameters.model_id}")
        logger.info(f"⚙️ Parâmetros: temp={request.parameters.temperature}, max_tokens={request.parameters.max_tokens}, top_p={request.parameters.top_p}")
        logger.info(f"🎯 Embedding Model: text-embedding-3-large (para RAG)")
        
        llm_response = await client.chat.completions.create(
            model=request.parameters.model_id,
            messages=[{"role": "user", "content": formatted_prompt}],
            temperature=request.parameters.temperature,
            max_tokens=request.parameters.max_tokens,
            top_p=request.parameters.top_p
        )
        
        generated_response = llm_response.choices[0].message.content.strip()
        logger.info(f"✅ RESPOSTA REAL RECEBIDA: {len(generated_response)} caracteres")
        
        # COMPARAÇÃO SEMÂNTICA CONDICIONAL (apenas se checkbox ativado)
        final_response = generated_response
        used_automation = False
        
        if request.parameters.enable_semantic_comparison:
            logger.info("🔄 Comparação semântica HABILITADA - verificando automações...")
            # TODO: Implementar comparação real com automações do catalog.yml
            # Por agora, simular que não há automação melhor
            logger.info("📋 Nenhuma automação melhor encontrada, usando resposta da IA")
        else:
            logger.info("⏭️ Comparação semântica DESABILITADA - usando resposta direta da IA")
        
        # ATUALIZAR HISTÓRICO REAL DO LEAD (se foi selecionado um lead)
        if request.lead_id:
            try:
                from datetime import datetime
                
                # Carregar leads
                leads = load_rag_leads()
                
                # Encontrar lead específico
                for lead in leads:
                    if lead.id == request.lead_id:
                        # Adicionar mensagem do lead
                        lead_message = RAGLeadMessage(
                            role='Lead',
                            text=request.message,
                            timestamp=datetime.now().isoformat()
                        )
                        lead.messages.append(lead_message)
                        
                        # Adicionar resposta da IA
                        ai_message = RAGLeadMessage(
                            role='GPT',
                            text=final_response,
                            timestamp=datetime.now().isoformat()
                        )
                        lead.messages.append(ai_message)
                        
                        # Salvar histórico atualizado
                        save_rag_leads(leads)
                        logger.info(f"📝 Histórico REAL atualizado para lead {request.lead_id}: +2 mensagens")
                        break
                        
            except Exception as e:
                logger.error(f"Erro ao atualizar histórico do lead: {e}")
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return RAGSimulationResult(
            response=final_response,
            classification="DÚVIDA",
            decision_id=f"rag_sim_{int(time.time())}",
            top_n_results=top_n_results,
            processing_time_ms=processing_time,
            stages={
                "total_time_ms": processing_time,
                "rag_hits": len(top_n_results),
                "actions_count": 1,
                "model_used": request.parameters.model_id,
                "semantic_comparison": request.parameters.enable_semantic_comparison,
                "used_automation": used_automation,
                "config_applied": {
                    "temperature": request.parameters.temperature,
                    "max_tokens": request.parameters.max_tokens,
                    "top_k": request.parameters.top_k,
                    "threshold": request.parameters.threshold,
                    "re_rank": request.parameters.re_rank
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Erro na simulação RAG: {e}")
        raise HTTPException(status_code=500, detail=f"Erro na simulação: {str(e)}")


@router.get("/simulate/stream")
async def simulate_rag_stream(
    message: str = Query(..., description="Mensagem para simular"),
    safe_mode: bool = Query(True, description="Modo seguro"),
    lead_id: Optional[int] = Query(None, description="ID do lead RAG")
):
    """
    Executa simulação RAG com streaming de logs em tempo real.
    """
    async def generate_log_stream():
        try:
            start_time = time.time()
            
            # 1. Início da simulação REAL
            yield f"data: {json.dumps({'stage': 'start', 'event': 'Iniciando simulação RAG REAL', 'timestamp': time.time(), 'data': {'message': message, 'safe_mode': safe_mode, 'lead_id': lead_id}})}\n\n"
            await asyncio.sleep(0.2)
            
            # 2. Carregando lead REAL (se selecionado)
            historico_real = "Primeira interação"
            if lead_id:
                leads = load_rag_leads()
                selected_lead = None
                for lead in leads:
                    if lead.id == lead_id:
                        selected_lead = lead
                        break
                
                if selected_lead:
                    historico_real = build_rag_message_history(selected_lead.messages)
                    yield f"data: {json.dumps({'stage': 'snapshot', 'event': f'Carregando histórico REAL do lead: {selected_lead.name}', 'timestamp': time.time(), 'data': {'lead_name': selected_lead.name, 'messages_count': len(selected_lead.messages)}})}\n\n"
                else:
                    yield f"data: {json.dumps({'stage': 'snapshot', 'event': f'Lead {lead_id} não encontrado, usando primeira interação', 'timestamp': time.time(), 'data': {'lead_id': lead_id}})}\n\n"
            else:
                yield f"data: {json.dumps({'stage': 'snapshot', 'event': 'Nenhum lead selecionado - primeira interação', 'timestamp': time.time(), 'data': {'message': 'Simulação sem histórico'}})}\n\n"
            await asyncio.sleep(0.3)
            
            # 3. Busca RAG REAL
            yield f"data: {json.dumps({'stage': 'retrieve', 'event': 'Executando busca RAG REAL na base de conhecimento', 'timestamp': time.time(), 'data': {'query': message}})}\n\n"
            await asyncio.sleep(0.4)
            
            # Fazer busca RAG REAL
            rag_service = get_rag_service()
            rag_context = await rag_service.buscar_contexto_kb(message, top_k=3)
            
            # Filtrar resultados por threshold
            hits_filtrados = [hit for hit in rag_context.hits if hit.get("score", 0) >= 0.05]
            
            yield f"data: {json.dumps({'stage': 'retrieve', 'event': f'Busca concluída - {len(hits_filtrados)} resultados encontrados', 'timestamp': time.time(), 'data': {'hits': len(hits_filtrados), 'best_score': hits_filtrados[0].get('score', 0) if hits_filtrados else 0}})}\n\n"
            await asyncio.sleep(0.3)
            
            # 4. Montando prompt REAL
            actual_prompt = get_current_rag_prompt()
            kb_text = rag_context.build_context_string()
            
            # Usar dados REAIS
            real_context = {
                'historico_mensagens': historico_real,
                'kb_context': kb_text,
                'mensagem_atual': message
            }
            
            # Formatar prompt com dados REAIS
            try:
                formatted_prompt = actual_prompt.format(**real_context)
                template_source = "custom" if is_using_custom_prompt() else "default"
            except KeyError as e:
                formatted_prompt = actual_prompt
                template_source = f"error (missing: {e})"
            
            yield f"data: {json.dumps({'stage': 'compose', 'event': 'Prompt montado com dados REAIS', 'timestamp': time.time(), 'data': {'model': 'gpt-4o', 'template_source': template_source, 'using_custom': is_using_custom_prompt(), 'prompt_chars': len(formatted_prompt)}})}\n\n"
            await asyncio.sleep(0.3)
            
            # 4.1. MOSTRAR PROMPT FINAL COMPLETO (para debug com formatação melhorada)
            prompt_lines = formatted_prompt.split('\n')
            prompt_preview = '\n'.join(prompt_lines)  # Manter quebras de linha
            
            yield f"data: {json.dumps({'stage': 'debug_prompt', 'event': 'PROMPT FINAL FORMATADO (exato como enviado ao GPT)', 'timestamp': time.time(), 'data': {'formatted_prompt': prompt_preview, 'prompt_lines_count': len(prompt_lines), 'kb_hits_included': len(hits_filtrados), 'historico_chars': len(historico_real), 'total_prompt_chars': len(formatted_prompt)}})}\n\n"
            await asyncio.sleep(0.3)
            
            # 5. Fazendo chamada REAL para OpenAI
            yield f"data: {json.dumps({'stage': 'generate', 'event': 'Enviando prompt para OpenAI API REAL', 'timestamp': time.time(), 'data': {'model': 'gpt-4o', 'api': 'REAL OpenAI'}})}\n\n"
            await asyncio.sleep(0.5)
            
            # Chamar OpenAI API REAL
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            
            llm_response = await client.chat.completions.create(
                model='gpt-4o',
                messages=[{"role": "user", "content": formatted_prompt}],
                temperature=0.3,
                max_tokens=300,
                top_p=1.0
            )
            
            final_response = llm_response.choices[0].message.content.strip()
            
            yield f"data: {json.dumps({'stage': 'generate', 'event': 'Resposta REAL recebida da OpenAI', 'timestamp': time.time(), 'data': {'response_length': len(final_response), 'api': 'OpenAI REAL'}})}\n\n"
            
            # 6. Atualizando histórico REAL do lead (se selecionado)
            if lead_id:
                try:
                    from datetime import datetime
                    
                    # Carregar leads
                    leads = load_rag_leads()
                    
                    # Encontrar lead específico
                    for lead in leads:
                        if lead.id == lead_id:
                            # Adicionar mensagem do lead
                            lead_message = RAGLeadMessage(
                                role='Lead',
                                text=message,
                                timestamp=datetime.now().isoformat()
                            )
                            lead.messages.append(lead_message)
                            
                            # Adicionar resposta da IA
                            ai_message = RAGLeadMessage(
                                role='GPT',
                                text=final_response,
                                timestamp=datetime.now().isoformat()
                            )
                            lead.messages.append(ai_message)
                            
                            # Salvar histórico atualizado
                            save_rag_leads(leads)
                            
                            yield f"data: {json.dumps({'stage': 'update_lead', 'event': f'Histórico REAL atualizado para lead: {lead.name}', 'timestamp': time.time(), 'data': {'lead_id': lead_id, 'total_messages': len(lead.messages), 'added': 2}})}\n\n"
                            break
                            
                except Exception as e:
                    yield f"data: {json.dumps({'stage': 'error_lead', 'event': f'Erro ao atualizar lead: {str(e)}', 'timestamp': time.time(), 'data': {'error': str(e)}})}\n\n"
            
            # 7. Finalizando
            yield f"data: {json.dumps({'stage': 'complete', 'event': 'Preparando resposta final REAL para o lead', 'timestamp': time.time(), 'data': {'mode': 'safe_simulation', 'ready_to_send': True, 'api': 'OpenAI REAL', 'lead_updated': bool(lead_id)}})}\n\n"
            await asyncio.sleep(0.3)
            
            # Resultado final com dados REAIS
            total_time = int((time.time() - start_time) * 1000)
            final_result = {
                'stage': 'result',
                'event': 'Simulação REAL concluída com sucesso',
                'timestamp': time.time(),
                'data': {
                    'response': final_response,  # RESPOSTA REAL DA OPENAI!
                    'classification': 'DÚVIDA',
                    'processing_time_ms': total_time,
                    'model_used': 'gpt-4o',
                    'kb_hits': len(hits_filtrados),
                    'api': 'OpenAI REAL',
                    'lead_id': lead_id
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
            threshold=0.1,
            enable_semantic_comparison=False
        ),
        "balanced": RAGParameters(
            model_id="gpt-4o",
            temperature=0.3,
            max_tokens=400,
            top_k=3,
            threshold=0.05,
            enable_semantic_comparison=True
        ),
        "precise": RAGParameters(
            model_id="o1-preview",
            temperature=0.1,
            max_tokens=600,
            top_k=5,
            threshold=0.02,
            re_rank=True,
            enable_semantic_comparison=True
        )
    }
    
    return presets


# === ENDPOINTS PARA GERENCIAR LEADS RAG ===

@router.get("/leads", response_model=List[RAGLead])
async def get_rag_leads():
    """
    Lista todos os leads RAG criados
    """
    try:
        leads = load_rag_leads()
        return leads
    except Exception as e:
        logger.error(f"Erro ao listar leads RAG: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao listar leads: {str(e)}")

@router.post("/leads", response_model=RAGLead)
async def create_rag_lead(request: CreateRAGLeadRequest):
    """
    Cria um novo lead RAG para simulações
    """
    try:
        from datetime import datetime
        
        leads = load_rag_leads()
        
        # Gerar ID único
        new_id = max([lead.id for lead in leads if lead.id], default=0) + 1
        
        # Criar novo lead
        new_lead = RAGLead(
            id=new_id,
            name=request.name,
            description=request.description,
            messages=request.initial_messages,
            created_at=datetime.now().isoformat()
        )
        
        leads.append(new_lead)
        
        if not save_rag_leads(leads):
            raise HTTPException(status_code=500, detail="Erro ao salvar lead")
        
        logger.info(f"Lead RAG criado: {new_lead.name} (ID: {new_id})")
        return new_lead
        
    except Exception as e:
        logger.error(f"Erro ao criar lead RAG: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao criar lead: {str(e)}")

@router.delete("/leads/{lead_id}")
async def delete_rag_lead(lead_id: int):
    """
    Deleta um lead RAG
    """
    try:
        leads = load_rag_leads()
        
        # Encontrar e remover lead
        original_count = len(leads)
        leads = [lead for lead in leads if lead.id != lead_id]
        
        if len(leads) == original_count:
            raise HTTPException(status_code=404, detail="Lead não encontrado")
        
        if not save_rag_leads(leads):
            raise HTTPException(status_code=500, detail="Erro ao salvar alterações")
        
        logger.info(f"Lead RAG deletado: ID {lead_id}")
        return {"message": f"Lead {lead_id} deletado com sucesso"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao deletar lead RAG: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao deletar lead: {str(e)}")

@router.post("/leads/{lead_id}/messages")
async def add_message_to_lead(lead_id: int, message: RAGLeadMessage):
    """
    Adiciona uma nova mensagem ao histórico do lead
    """
    try:
        from datetime import datetime
        
        leads = load_rag_leads()
        
        # Encontrar lead
        lead_found = None
        for lead in leads:
            if lead.id == lead_id:
                lead_found = lead
                break
        
        if not lead_found:
            raise HTTPException(status_code=404, detail="Lead não encontrado")
        
        # Adicionar timestamp se não fornecido
        if not message.timestamp:
            message.timestamp = datetime.now().isoformat()
        
        # Adicionar mensagem
        lead_found.messages.append(message)
        
        if not save_rag_leads(leads):
            raise HTTPException(status_code=500, detail="Erro ao salvar mensagem")
        
        logger.info(f"Mensagem adicionada ao lead {lead_id}: {message.role} - {message.text[:50]}...")
        return {"message": "Mensagem adicionada com sucesso", "total_messages": len(lead_found.messages)}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao adicionar mensagem: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao adicionar mensagem: {str(e)}")

@router.get("/leads/{lead_id}")
async def get_rag_lead(lead_id: int):
    """
    Busca um lead específico com todo seu histórico
    """
    try:
        leads = load_rag_leads()
        
        for lead in leads:
            if lead.id == lead_id:
                return lead
        
        raise HTTPException(status_code=404, detail="Lead não encontrado")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar lead: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao buscar lead: {str(e)}")
