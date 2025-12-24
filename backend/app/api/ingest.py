"""
Document ingestion API endpoint.
Handles document upload, chunking, embedding, and KG extraction.
"""
import base64
from fastapi import APIRouter, HTTPException, Request
from app.models.schemas import DocumentIngestRequest, DocumentIngestResponse
from app.core.logging import logger
from app.utils.chunking import chunk_document
from app.utils.entity_extraction import extract_entities_and_relations
from uuid import uuid4
import PyPDF2
import io


router = APIRouter(prefix="/ingest", tags=["ingestion"])


@router.post("/document", response_model=DocumentIngestResponse)
async def ingest_document(
    request_body: DocumentIngestRequest,
    http_request: Request
):
    """
    Ingest a document into the system.
    
    Process:
    1. Decode file content
    2. Extract text (PDF or plain text)
    3. Chunk document
    4. Generate embeddings
    5. Store in vector store
    6. Extract entities and relations
    7. Store in knowledge graph
    
    Args:
        request: Document ingestion request
        app_request: FastAPI Request object to access app state
        
    Returns:
        DocumentIngestResponse with ingestion results
    """
    try:
        # Get services from app state
        vector_store = http_request.app.state.get_vector_store()
        embedding_service = http_request.app.state.get_embedding_service()
        kg_service = http_request.app.state.get_kg_service()
        
        document_id = str(uuid4())
        
        # Extract text based on file type
        text_content = ""
        if request_body.file_type.lower() == "pdf":
            # Decode base64 and parse PDF
            try:
                file_bytes = base64.b64decode(request_body.file_content)
                pdf_file = io.BytesIO(file_bytes)
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                
                for page in pdf_reader.pages:
                    text_content += page.extract_text() + "\n"
            except Exception as e:
                logger.error(f"Error parsing PDF: {e}")
                raise HTTPException(status_code=400, detail=f"Failed to parse PDF: {str(e)}")
        else:
            # Plain text - decode base64 or use as-is
            try:
                text_content = base64.b64decode(request_body.file_content).decode('utf-8')
            except:
                # If decoding fails, assume it's already plain text
                text_content = request_body.file_content
        
        if not text_content.strip():
            raise HTTPException(status_code=400, detail="Document is empty or could not extract text")
        
        logger.info(f"Ingesting document {document_id}: {request_body.file_name}")
        
        # Step 1: Chunk document
        chunks = chunk_document(
            document_id=document_id,
            text=text_content,
            metadata={
                "file_name": request_body.file_name,
                "file_type": request_body.file_type
            }
        )
        
        if not chunks:
            raise HTTPException(status_code=400, detail="No chunks created from document")
        
        # Step 2: Generate embeddings
        chunk_texts = [chunk["content"] for chunk in chunks]
        embeddings = embedding_service.get_embeddings(chunk_texts)
        
        if len(embeddings) != len(chunks):
            raise HTTPException(status_code=500, detail="Embedding generation failed")
        
        # Step 3: Store in vector store
        chunk_ids = vector_store.add_vectors(embeddings, chunks)
        
        # Step 4: Extract entities and relations
        entities, relations = extract_entities_and_relations(text_content)
        
        # Step 5: Store in knowledge graph
        kg_results = kg_service.store_document_entities(entities, relations)
        
        logger.info(
            f"Successfully ingested document {document_id}: "
            f"{len(chunks)} chunks, {kg_results['entities_stored']} entities, "
            f"{kg_results['relations_stored']} relations"
        )
        
        return DocumentIngestResponse(
            success=True,
            document_id=document_id,
            chunks_created=len(chunks),
            entities_extracted=kg_results['entities_stored'],
            relations_extracted=kg_results['relations_stored'],
            message=f"Document {request_body.file_name} ingested successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ingesting document: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
