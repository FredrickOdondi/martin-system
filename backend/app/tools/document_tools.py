import json
from typing import Optional, List, Dict, Any
from app.models.models import User

# Tool Definition
REQUEST_DOCUMENT_APPROVAL_TOOL_DEF = {
    "type": "function",
    "function": {
        "name": "request_document_approval_tool",
        "description": "Request approval to create and save an official document (Minutes, Policy Draft, Brief, Memo). This MUST be used before saving files to the registry.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Title of the document"
                },
                "content": {
                    "type": "string",
                    "description": "Full Markdown content of the document"
                },
                "document_type": {
                    "type": "string",
                    "description": "Type of document (e.g., 'minutes', 'brief', 'policy', 'memo')"
                },
                "file_name": {
                    "type": "string",
                    "description": "Suggested filename (e.g., 'energy_policy_v1.md')"
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "searchable tags"
                }
            },
            "required": ["title", "content", "document_type", "file_name"]
        }
    }
}

def request_document_approval_tool(
    title: str,
    content: str,
    document_type: str,
    file_name: str,
    tags: List[str] = []
):
    """
    Stops execution and requests human approval for a document draft.
    Does NOT save to the database yet.
    """
    import uuid
    request_id = str(uuid.uuid4())
    
    # We return a specific structure that the Agent Loop will detect and trigger an Interrupt for.
    # The 'document_draft' object contains the payload the frontend needs.
    return json.dumps({
        "approval_request_id": request_id, 
        "type": "document_approval_required",
        "document_draft": {
            "title": title,
            "content": content,
            "document_type": document_type,
            "file_name": file_name,
            "tags": tags
        },
        "message": f"Document '{title}' requires approval before saving."
    })
