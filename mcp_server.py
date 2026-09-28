from pydantic import Field
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base

mcp = FastMCP("DocumentMCP", log_level="ERROR")


docs = {
    "deposition.md": "This deposition covers the testimony of Angela Smith, P.E.",
    "report.pdf": "The report details the state of a 20m condenser tower.",
    "financials.docx": "These financials outline the project's budget and expenditures.",
    "outlook.pdf": "This document presents the projected future performance of the system.",
    "plan.md": "The plan outlines the steps for the project's implementation.",
    "spec.txt": "These specifications define the technical requirements for the equipment.",
}

# TODO: Write a tool to read a doc
@mcp.tool(
    name="read_doc_contents",
    description="Reads the contents of document and returns it as string"
)
def read_document(
    doc_id:str=Field(description="Id of the document to be read")
):
    if doc_id not in docs:
        raise ValueError(f"doc with id {doc_id} not found")
    return docs[doc_id]

 
# TODO: Write a tool to edit a doc
@mcp.tool(
    name="edit_document",
    description="Edits an existing document with the provided content"
)
def edit_document(
doc_id:str=Field(description="Id of the document to be edited"),
old_str:str=Field(description="contents to be replaced. Must match exactly including whitespace"),
new_str:str=Field(description="new text to insert in place of the old")
):
    if doc_id not in docs:
        raise ValueError(f"doc with id {doc_id} not found")
    docs[doc_id]=docs[doc_id].replace(old_str,new_str)



# TODO: Write a resource to return all doc id's
@mcp.resource(
    "docs://documents",
    mime_type="application/json"
)
def list_docs()->list[str]:
    return list(docs.keys())
# TODO: Write a resource to return the contents of a particular doc
@mcp.resource(
    "docs://documents/{doc_id}",
    mime_type="text/plain"
)
def fetch_doc(doc_id:str)->str:
    if doc_id not in docs:
        raise ValueError(f"Doc with id {doc_id} not found")
    return docs[doc_id]

# TODO: Write a prompt to rewrite a doc in markdown format
@mcp.prompt(
    name="format",
    description="rewrites the contents of the document in markdown format"
)
def format_document(
    doc_id:str=Field(description="id of the document to format")
)->list[base.Message]:
    prompt=f"""your goal is to reformat a document to be written with markdown syntex
    
    The id of the document you need to reformat is:
    <document_id>
    {doc_id}
    </document_id>
    Add in headers,bullet points, tables, etc as necessary. 
    Use the 'edit_document' tool to edit the document. after document has been formatted.
    
    
    """
    return[base.UserMessage(prompt)]
# TODO: Write a prompt to summarize a doc


if __name__ == "__main__":
    mcp.run(transport="stdio")
