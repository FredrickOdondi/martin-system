from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, AsyncGenerator
import uuid
import asyncio
import json
import logging

logger = logging.getLogger(__name__)

from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.models.models import User
from app.schemas.schemas import AgentChatRequest, AgentChatResponse, AgentTaskRequest, AgentStatus
from app.schemas.chat_messages import (
    EnhancedChatRequest,
    EnhancedChatResponse,
    ChatMessage,
    ChatMessageType,
    AgentSuggestion,
    ToolExecution
)
# Use LangGraph supervisor via API adapter
from app.agents.supervisor_api_adapter import SupervisorWithTools
from app.services.command_parser import CommandParser, MessageParseType
from app.services.email_approval_service import get_email_approval_service
from app.services.resend_service import get_resend_service
from app.schemas.email_approval import (
    EmailApprovalRequest,
    EmailApprovalResponse,
    EmailApprovalResult
)
from app.services.audit_service import audit_service
from datetime import datetime

router = APIRouter(prefix="/agents", tags=["Agents"])

# Initialize the supervisor agent (singleton)
supervisor_agent = None
command_parser = CommandParser()

def get_supervisor() -> SupervisorWithTools:
    """Get or create the supervisor agent instance."""
    global supervisor_agent
    if supervisor_agent is None:
        supervisor_agent = SupervisorWithTools()
    return supervisor_agent


# Command and Mention Handlers (Phase 2)

async def handle_command(supervisor: SupervisorWithTools, parsed: dict, original_message: str) -> str:
    """Handle slash command execution."""
    command = parsed["command"]
    params = parsed["parameters"]
    clean_query = parsed["clean_query"]

    # Map commands to supervisor methods
    if command == "/search":
        query = params.get("query", clean_query)
        return await supervisor.chat_with_tools(f"Search the knowledge base for: {query}")

    elif command == "/email":
        # Check if it's a send or search operation
        if "to" in params:
            # Send email
            to = params.get("to")
            subject = params.get("subject", "Message from ECOWAS TWG System")
            body = params.get("body", clean_query)
            cc = params.get("cc")
            return await supervisor.chat_with_tools(
                f"Send an email to {to} with subject '{subject}' and message: {body}" +
                (f" and CC {cc}" if cc else "")
            )
        else:
            # Search emails
            search_term = params.get("search", clean_query)
            return await supervisor.chat_with_tools(f"Search my emails for: {search_term}")

    elif command == "/schedule":
        return await supervisor.chat_with_tools(f"Help me with scheduling: {clean_query}")

    elif command == "/draft":
        doc_type = params.get("type", "document")
        topic = params.get("topic", clean_query)
        return await supervisor.chat_with_tools(f"Draft a {doc_type} about: {topic}")

    elif command == "/analyze":
        target = params.get("target", clean_query)
        return await supervisor.chat_with_tools(f"Analyze: {target}")

    elif command == "/broadcast":
        message = params.get("message", clean_query)
        return await supervisor.chat_with_tools(f"Broadcast this message to all TWGs: {message}")

    elif command == "/summarize":
        target = params.get("target", clean_query)
        return await supervisor.chat_with_tools(f"Summarize: {target}")

    else:
        return f"Command {command} recognized but handler not implemented yet. Query: {clean_query}"


async def handle_mention(supervisor: SupervisorWithTools, parsed: dict) -> str:
    """Handle @mention routing to specific agents."""
    agent_ids = parsed["agent_mentions"]
    clean_query = parsed["clean_query"]

    if not clean_query:
        # No query, just return info about mentioned agents
        agent_names = [command_parser.AGENT_MENTIONS[f"@{aid.title()}Agent"]["name"]
                      for aid in agent_ids if f"@{aid.title()}Agent" in command_parser.AGENT_MENTIONS]
        return f"You mentioned: {', '.join(agent_names)}. How can they help you?"

    # For now, route to supervisor with context about which agent was mentioned
    # TODO: Implement actual agent delegation in supervisor_with_tools.py
    if len(agent_ids) == 1:
        agent_id = agent_ids[0]
        return await supervisor.chat_with_tools(
            f"[ROUTING TO {agent_id.upper()} TWG AGENT] {clean_query}"
        )
    else:
        return await supervisor.chat_with_tools(
            f"[ROUTING TO MULTIPLE AGENTS: {', '.join(agent_ids)}] {clean_query}"
        )


@router.post("/chat", response_model=AgentChatResponse)
async def chat_with_martin(
    chat_in: AgentChatRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Chat with the Supervisor AI agent.

    Uses the actual LLM-powered supervisor with tool execution capabilities.
    """
    from langgraph.errors import GraphInterrupt
    
    conv_id = chat_in.conversation_id or uuid.uuid4()

    try:
        # Get the supervisor agent
        supervisor = get_supervisor()

        # Chat with the supervisor using tools (Pass TWG Context for strict RBAC)
        twg_context = str(chat_in.twg_id) if chat_in.twg_id else None
        response_text = await supervisor.chat_with_tools(chat_in.message, twg_id=twg_context)

        return {
            "response": response_text,
            "conversation_id": conv_id,
            "citations": [],  # Citations will be extracted from the response in future
            "agent_id": "supervisor_v1"
        }
    except GraphInterrupt as gi:
        # Graph was interrupted for human approval
        # Extract the interrupt payload - GraphInterrupt stores it in args[0]
        interrupt_value = gi.args[0] if gi.args else {}
        
        logger.info(f"[CHAT] GraphInterrupt caught - gi.args: {gi.args}")
        logger.info(f"[CHAT] Extracted interrupt_value: {interrupt_value}")

        # SPECIAL HANDLING: If interrupt is just a string (e.g. "Duplicate detected"), 
        # return it as a final response to the user and Halt.
        if isinstance(interrupt_value, str):
            # Humanize the error message using LLM
            try:
                from app.services.llm_service import get_llm_service
                llm = get_llm_service()
                humanized_msg = llm.chat(
                    system_prompt="You are a helpful assistant. The user's request was stopped by the system with the following error. "
                                "Rewrite this error message to be polite, concise, and helpful to the user. "
                                "Explain clearly why the action was blocked. Do not mention 'system error' or 'tools'.",
                    prompt=f"System Error: {interrupt_value}"
                )
                response_content = f"🛑 {humanized_msg}"
            except Exception as e:
                logger.error(f"Failed to humanize interrupt message: {e}")
                response_content = f"🛑 {interrupt_value}"

            return {
                "response": response_content, 
                "conversation_id": conv_id,
                "citations": [],
                "agent_id": "supervisor_v1",
                # We do NOT set interrupted=True here because we don't need UI approval.
                # We just want to halt and show the message.
            }
        
        # Extract draft details for the response message
        draft_preview = ""
        if isinstance(interrupt_value, dict) and "draft" in interrupt_value:
            draft = interrupt_value["draft"]
            to_list = draft.get("to", [])
            subject = draft.get("subject", "No Subject")
            draft_preview = f"\n\n**To:** {', '.join(to_list)}\n**Subject:** {subject}"
            
            # Link this thread context to the approval request so we can resume later
            if "request_id" in interrupt_value:
                req_id = interrupt_value["request_id"]
                approval_service = get_email_approval_service()
                if approval_service.update_approval_request_thread(req_id, str(conv_id)):
                    logger.info(f"[CHAT] Linked thread {conv_id} to approval request {req_id}")
        
        response_dict = {
            "response": "",  # Empty - frontend will handle the message display
            "conversation_id": conv_id,
            "citations": [],
            "agent_id": "supervisor_v1",
            "interrupted": True,
            "interrupt_payload": interrupt_value,
            "thread_id": str(conv_id)  # Used to resume the graph
        }
        
        logger.info(f"[CHAT] Returning interrupt response: {response_dict}")
        return response_dict
    except Exception as e:
        # Log the error and return a helpful message
        import traceback
        traceback.print_exc()

        return {
            "response": f"I apologize, but I encountered an error processing your request: {str(e)}",
            "conversation_id": conv_id,
            "citations": [],
            "agent_id": "supervisor_v1"
        }

@router.post("/chat/enhanced", response_model=EnhancedChatResponse)
async def enhanced_chat(
    chat_in: EnhancedChatRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Enhanced chat with rich message support, suggestions, and tool visibility.

    This endpoint provides:
    - Rich message types (actions, requests, tool execution status)
    - Proactive suggestions
    - Tool execution visibility
    - File attachment support
    """
    conv_id = chat_in.conversation_id or uuid.uuid4()

    try:
        # Get the supervisor agent
        supervisor = get_supervisor()

        # Parse message for commands and mentions (Phase 2)
        parsed = command_parser.parse_message(chat_in.message)

        # Handle based on parse type
        if parsed["type"] == MessageParseType.COMMAND:
            # Command execution
            response_text = await handle_command(supervisor, parsed, chat_in.message)
            message_type = ChatMessageType.COMMAND_RESULT
        elif parsed["type"] == MessageParseType.MENTION:
            # Route to specific agent(s)
            response_text = await handle_mention(supervisor, parsed)
            message_type = ChatMessageType.AGENT_TEXT
        elif parsed["type"] == MessageParseType.MIXED:
            # Both command and mention - prioritize command
            response_text = await handle_command(supervisor, parsed, chat_in.message)
            message_type = ChatMessageType.COMMAND_RESULT
        else:
            # Natural language - regular chat
            response_text = await supervisor.chat_with_tools(chat_in.message)
            message_type = ChatMessageType.AGENT_TEXT

        # Create the agent response message
        agent_message = ChatMessage(
            message_id=uuid.uuid4(),
            conversation_id=conv_id,
            message_type=message_type,
            content=response_text,
            sender="agent",
            timestamp=datetime.utcnow(),
            metadata={"parsed": parsed} if parsed["type"] != MessageParseType.NATURAL else None
        )

        # TODO: Implement suggestion generation in Phase 3
        suggestions = []

        # TODO: Implement tool execution tracking in Phase 6
        tool_executions = []

        return EnhancedChatResponse(
            message=agent_message,
            suggestions=suggestions,
            tool_executions=tool_executions,
            conversation_id=conv_id
        )

    except Exception as e:
        import traceback
        traceback.print_exc()

        # Return error as agent message
        error_message = ChatMessage(
            message_id=uuid.uuid4(),
            conversation_id=conv_id,
            message_type=ChatMessageType.AGENT_TEXT,
            content=f"I apologize, but I encountered an error processing your request: {str(e)}",
            sender="agent",
            timestamp=datetime.utcnow()
        )

        return EnhancedChatResponse(
            message=error_message,
            suggestions=[],
            tool_executions=[],
            conversation_id=conv_id
        )


@router.post("/chat/stream")
async def stream_chat(
    chat_in: EnhancedChatRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Streaming chat endpoint that provides real-time updates on agent thinking and tool execution.

    Returns Server-Sent Events (SSE) stream with:
    - Agent thinking status
    - Tool execution progress
    - Intermediate results
    - Final response
    """

    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events for streaming."""
        # Ensure conv_id is always a string for JSON serialization
        conv_id = str(chat_in.conversation_id) if chat_in.conversation_id else str(uuid.uuid4())

        try:
            # Send initial event
            yield f"data: {json.dumps({'type': 'start', 'conversation_id': conv_id})}\n\n"

            # Create a new supervisor instance with isolated session for this conversation
            # This prevents conversation history accumulation causing context length errors
            supervisor = SupervisorWithTools()
            supervisor.supervisor.session_id = conv_id

            # Clear any existing history for this session to start fresh
            if hasattr(supervisor.supervisor, 'supervisor_agent'):
                supervisor.supervisor.supervisor_agent.clear_history()

            # Parse message for commands and mentions
            parsed = command_parser.parse_message(chat_in.message)

            # Send parsing event
            yield f"data: {json.dumps({'type': 'parsing', 'result': {'message_type': str(parsed['type']), 'command': parsed.get('command'), 'mentions': parsed.get('agent_mentions', [])}})}\n\n"

            # Determine what to execute
            if parsed["type"] == MessageParseType.COMMAND:
                # Send command execution event
                yield f"data: {json.dumps({'type': 'command_detected', 'command': parsed['command'], 'params': parsed['parameters']})}\n\n"

                # Stream tool execution
                command = parsed["command"]
                if command == "/search":
                    yield f"data: {json.dumps({'type': 'tool_start', 'tool': 'knowledge_search', 'status': 'Searching knowledge base...'})}\n\n"
                elif command == "/email":
                    if "to" in parsed["parameters"]:
                        yield f"data: {json.dumps({'type': 'tool_start', 'tool': 'email_send', 'status': 'Composing email...'})}\n\n"
                    else:
                        yield f"data: {json.dumps({'type': 'tool_start', 'tool': 'email_search', 'status': 'Searching inbox...'})}\n\n"
                elif command == "/schedule":
                    yield f"data: {json.dumps({'type': 'tool_start', 'tool': 'scheduler', 'status': 'Checking schedules...'})}\n\n"
                elif command == "/draft":
                    yield f"data: {json.dumps({'type': 'tool_start', 'tool': 'document_drafter', 'status': 'Drafting document...'})}\n\n"
                elif command == "/analyze":
                    yield f"data: {json.dumps({'type': 'tool_start', 'tool': 'analyzer', 'status': 'Analyzing data...'})}\n\n"

                # Execute command
                response_text = await handle_command(supervisor, parsed, chat_in.message)
                message_type = ChatMessageType.COMMAND_RESULT

            elif parsed["type"] == MessageParseType.MENTION:
                # Send agent routing event
                agent_ids = parsed["agent_mentions"]
                agents_joined = ", ".join(agent_ids)
                routing_status = f"Routing to {agents_joined} agent(s)..."
                yield f"data: {json.dumps({'type': 'agent_routing', 'agents': agent_ids, 'status': routing_status})}\n\n"

                # Execute with mentioned agent
                response_text = await handle_mention(supervisor, parsed)
                message_type = ChatMessageType.AGENT_TEXT

            elif parsed["type"] == MessageParseType.MIXED:
                yield f"data: {json.dumps({'type': 'mixed_execution', 'status': 'Processing command with agent mention...'})}\n\n"
                response_text = await handle_command(supervisor, parsed, chat_in.message)
                message_type = ChatMessageType.COMMAND_RESULT

            else:
                # Natural language - show thinking
                yield f"data: {json.dumps({'type': 'thinking', 'status': 'Processing your request...'})}\n\n"

                # Simulate LLM thinking
                await asyncio.sleep(0.5)
                yield f"data: {json.dumps({'type': 'thinking', 'status': 'Analyzing context...'})}\n\n"

                # Execute
                response_text = await supervisor.chat_with_tools(chat_in.message)
                message_type = ChatMessageType.AGENT_TEXT

            # Send completion event
            yield f"data: {json.dumps({'type': 'tool_complete', 'status': 'Completed'})}\n\n"

            # Create the final message
            agent_message = ChatMessage(
                message_id=uuid.uuid4(),
                conversation_id=conv_id,
                message_type=message_type,
                content=response_text,
                sender="agent",
                timestamp=datetime.utcnow(),
                metadata={"parsed": parsed} if parsed["type"] != MessageParseType.NATURAL else None
            )

            # Send final response - use model_dump with mode='json' to handle UUID serialization
            yield f"data: {json.dumps({'type': 'response', 'message': agent_message.model_dump(mode='json')})}\n\n"

            # Send done event
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            import traceback
            traceback.print_exc()

            # Send error event
            error_data = {
                'type': 'error',
                'error': str(e),
                'message': f'I apologize, but I encountered an error: {str(e)}'
            }
            yield f"data: {json.dumps(error_data)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/task", status_code=status.HTTP_202_ACCEPTED)
async def assign_agent_task(
    task_in: AgentTaskRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Assign a high-level task to the agent swarm (e.g., draft Communiqué).
    
    Returns a task ID for polling. (Currently Mocked)
    """
    task_id = uuid.uuid4()
    # In production, this would trigger a Celery task or a background agent flow
    return {
        "task_id": str(task_id),
        "status": "queued",
        "message": f"Task '{task_in.title}' has been dispatched to the agent swarm."
    }

@router.get("/status", response_model=AgentStatus)
async def get_agent_swarm_status(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get the current operational status of the agent swarm.
    """
    return {
        "status": "operational",
        "swarm_ready": True,
        "active_agents": ["Supervisor", "Energy Martin", "Minerals Martin", "Agribusiness Martin"],
        "version": "0.1.0-alpha"
    }


# Phase 2: Command Autocomplete Endpoints

@router.get("/commands/autocomplete")
async def get_command_autocomplete(
    query: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get command autocomplete suggestions for slash commands.

    Args:
        query: Partial command (e.g., "/em" or "/search")

    Returns:
        List of matching commands with descriptions and examples
    """
    suggestions = command_parser.get_command_suggestions(query)
    return {"suggestions": suggestions}


@router.get("/mentions/autocomplete")
async def get_mention_autocomplete(
    query: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get @mention autocomplete suggestions for TWG agents.

    Args:
        query: Partial mention (e.g., "@En" or "@Agri")

    Returns:
        List of matching agent mentions with metadata
    """
    suggestions = command_parser.get_mention_suggestions(query)
    return {"suggestions": suggestions}


@router.get("/commands/list")
async def get_all_commands(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all available commands with metadata.

    Returns:
        Dictionary of all commands with descriptions, examples, and parameters
    """
    commands = command_parser.get_all_commands()
    return {"commands": commands}


@router.get("/agents/list")
async def get_all_agent_mentions(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all available agent mentions.

    Returns:
        Dictionary of all TWG agent mentions with metadata
    """
    agents = command_parser.get_all_agents()
    return {"agents": agents}


# Email Approval Endpoints (Human-in-the-Loop)

@router.get("/email/pending-approvals")
async def get_pending_email_approvals(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all pending email approvals for the current user.

    Returns:
        List of pending email approval requests
    """
    approval_service = get_email_approval_service()
    # Clean up old requests first
    approval_service.cleanup_old_requests()

    pending = list(approval_service.pending_approvals.values())
    return {"pending_approvals": pending}


@router.get("/email/approval/{request_id}")
async def get_email_approval(
    request_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a specific email approval request.

    Args:
        request_id: The approval request ID

    Returns:
        EmailApprovalRequest details
    """
    approval_service = get_email_approval_service()
    approval_request = approval_service.get_approval_request(request_id)

    if not approval_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Approval request {request_id} not found"
        )

    return approval_request


@router.post("/email/approval/{request_id}/approve", response_model=EmailApprovalResult)
async def approve_email(
    request_id: str,
    approval_response: EmailApprovalResponse,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Approve and send an email.

    Args:
        request_id: The approval request ID
        approval_response: User's approval decision with optional modifications

    Returns:
        Result of email sending operation
    """
    approval_service = get_email_approval_service()
    approval_request = approval_service.get_approval_request(request_id)

    if not approval_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Approval request {request_id} not found"
        )

    if not approval_response.approved:
        # User declined - remove the request
        approval_service.remove_approval_request(request_id)
        return EmailApprovalResult(
            success=True,
            message="Email sending cancelled by user",
            email_sent=False
        )

    # Use modified draft if provided, otherwise use original
    draft = approval_response.modifications or approval_request.draft

    try:
        # Send the email using Resend service
        resend_service = get_resend_service()
        result = resend_service.send_message(
            to=draft.to,
            subject=draft.subject,
            body=draft.body,
            html_body=draft.html_body,
            cc=draft.cc,
            bcc=draft.bcc,
            attachments=draft.attachments
        )

        # Remove the approval request
        approval_service.remove_approval_request(request_id)

        # RESUME AGENT EXECUTION
        thread_id = approval_request.thread_id
        if thread_id:
            logger.info(f"Resuming agent execution for thread {thread_id}")
            # Prepare resumption value for the agent
            resume_value = {
                "approved": True, 
                "message_id": result.get('message_id'), 
                "status": "sent"
            }
            try:
                supervisor = get_supervisor()
                agent_response = await supervisor.resume_chat(thread_id, resume_value)
                logger.info(f"Agent resumed successfully. Response: {agent_response}")
            except Exception as e:
                logger.error(f"Failed to resume agent: {e}")
        else:
             logger.warning(f"No thread_id linked to approval request {request_id} - cannot resume agent")

        return EmailApprovalResult(
            success=True,
            message="Email sent successfully via Resend" + (" (Agent resumed)" if thread_id else ""),
            email_sent=True,
            message_id=result.get('message_id'),
            thread_id=thread_id
        )

        # Audit Log
        if result.get("status") == "success":
            await audit_service.log_activity(
                db=db,
                user_id=current_user.id,
                action="send_email",
                resource_type="email",
                resource_id=None,  # Could be message_id if we store emails as entities
                details={
                    "to": draft.to,
                    "subject": draft.subject,
                    "message_id": result.get('message_id'),
                    "request_id": request_id,
                    "provider": "resend"
                },
                ip_address=None # Could extract from request if available
            )
            # Commit the log
            await db.commit()
            
        return EmailApprovalResult(
            success=True,
            message="Email sent successfully via Resend",
            email_sent=True,
            message_id=result.get('message_id'),
            thread_id=None # Resend doesn't typically provide thread_id
        )

    except Exception as e:
        import traceback
        traceback.print_exc()

        return EmailApprovalResult(
            success=False,
            message=f"Failed to send email: {str(e)}",
            email_sent=False
        )


@router.post("/email/approval/{request_id}/decline", response_model=EmailApprovalResult)
async def decline_email(
    request_id: str,
    reason: str = None,
    current_user: User = Depends(get_current_active_user)
):
    """
    Decline an email approval request.

    Args:
        request_id: The approval request ID
        reason: Optional reason for declining

    Returns:
        Result of the decline operation
    """
    approval_service = get_email_approval_service()
    approval_request = approval_service.get_approval_request(request_id)

    if not approval_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Approval request {request_id} not found"
        )

    # Remove the approval request
    approval_service.remove_approval_request(request_id)

    return EmailApprovalResult(
        success=True,
        message=f"Email declined: {reason}" if reason else "Email sending cancelled",
        email_sent=False
    )


# Project Memo Email Endpoint

from pydantic import BaseModel, EmailStr

class SendMemoEmailRequest(BaseModel):
    to_email: EmailStr
    subject: str
    body: str
    memo_content: str
    project_id: str
    project_name: str


@router.post("/supervisor/send-email")
async def send_project_memo_email(
    request: SendMemoEmailRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Send a project investment memo via email using the supervisor agent's email tool.

    Args:
        request: Email request with memo content
        current_user: Current authenticated user

    Returns:
        Success status and message
    """
    try:
        logger.info(f"Using supervisor agent to send project memo email to {request.to_email}")

        # Import the send_email tool function
        from app.tools.email_tools import send_email

        # Format the email body with the memo content
        full_body = f"{request.body}\n\n{'='*80}\n\n{request.memo_content}"

        # Create HTML version
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <p>{request.body}</p>
                <hr style="border: 1px solid #ccc; margin: 20px 0;">
                <pre style="background-color: #f5f5f5; padding: 20px; border-radius: 5px; overflow-x: auto; white-space: pre-wrap;">
{request.memo_content}
                </pre>
                <hr style="border: 1px solid #ccc; margin: 20px 0;">
                <p style="font-size: 12px; color: #666;">
                    <em>This email was generated and sent by the ECOWAS TWG AI Agent System</em>
                </p>
            </body>
        </html>
        """

        # Use the supervisor agent's email tool to send the email
        result = await send_email(
            to=request.to_email,
            subject=request.subject,
            message=full_body,
            html_body=html_body,
            context=f"Sending investment memo for project {request.project_name} ({request.project_id})"
        )

        logger.info(f"Email tool result: {result}")

        # Check if it created an approval request or sent directly
        if result.get('status') == 'approval_required':
            approval_id = result.get('approval_request_id')
            logger.info(f"Email approval request created: {approval_id}")

            # Auto-approve for this endpoint since user already initiated the send
            approval_service = get_email_approval_service()
            approval_request = approval_service.get_approval_request(approval_id)

            if approval_request:
                # Send the email directly
                resend_service = get_resend_service()
                send_result = resend_service.send_message(
                    to=approval_request.draft.to,
                    subject=approval_request.draft.subject,
                    body=approval_request.draft.body,
                    html_body=approval_request.draft.html_body
                )

                # Remove the approval request
                approval_service.remove_approval_request(approval_id)

                logger.info(f"Project memo email sent successfully to {request.to_email}")

                # Audit Log
                await audit_service.log_activity(
                    db=db,
                    user_id=current_user.id,
                    action="send_project_memo_email",
                    resource_type="email",
                    resource_id=None,
                    details={
                        "to": [request.to_email],
                        "subject": request.subject,
                        "project_id": request.project_id,
                        "project_name": request.project_name
                    }
                )
                await db.commit()

                return {
                    "success": True,
                    "message": f"Investment memo sent successfully to {request.to_email}",
                    "email_sent": True,
                    "message_id": send_result.get('message_id'),
                    "thread_id": None
                }

        # Fallback response
        return {
            "success": True,
            "message": f"Email sent successfully to {request.to_email}",
            "email_sent": True,
            "result": result
        }

    except Exception as e:
        logger.error(f"Failed to send project memo email: {str(e)}")
        import traceback
        traceback.print_exc()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {str(e)}"
        )
