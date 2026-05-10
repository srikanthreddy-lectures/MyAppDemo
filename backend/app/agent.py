import re
from . import rag, llm, cache

# Regex allows: digits, decimal point, spaces, + - * / ( ) ^, and letters (for variables/number words)
# We will further validate if it's a math expression or a natural language question.
ARITH_ALLOWED = re.compile(r'^[a-zA-Z0-9.\s+\-*/()^]*$')

NUMBER_MAP = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
    "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16, 
    "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, 
    "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90
}

SYSTEM_PROMPT = """Answer ONLY from provided context.
Do not hallucinate.
Do not speculate.
Keep answers concise.
No filler intros like "Based on the notes..." or "According to the document...".
If answer not found: "The notes don't cover that."
"""

def is_arithmetic(question: str) -> bool:
    """
    Returns True if the question is a mathematical expression.
    It allows digits, operators, variables, and number words, 
    but excludes natural language questions.
    """
    q = question.strip().lower()
    if not q:
        return False
    
    # Basic character check
    if not ARITH_ALLOWED.match(q):
        return False
    
    # Exclude common natural language starters to avoid routing "What is 2+2" to calculator
    forbidden_starters = ("what", "how", "why", "can", "could", "please", "calculate", "find")
    if q.startswith(forbidden_starters):
        return False
        
    return True

def text_to_digits(text: str) -> str:
    """
    Converts number words (e.g., 'seven', 'twenty two') to digits.
    """
    words = text.lower().split()
    result = []
    i = 0
    while i < len(words):
        word = words[i]
        if word in NUMBER_MAP:
            val = NUMBER_MAP[word]
            # Handle cases like "twenty two" -> 20 + 2
            if val >= 20 and i + 1 < len(words) and words[i+1] in NUMBER_MAP and NUMBER_MAP[words[i+1]] < 10:
                val += NUMBER_MAP[words[i+1]]
                i += 1
            result.append(str(val))
        else:
            result.append(word)
        i += 1
    return " ".join(result)

def expand_algebra(expr: str) -> str:
    """
    Performs very basic symbolic expansion for specific patterns.
    Example: (a+b)*(a-b) -> a^2 - b^2
    Since we cannot use external libraries like sympy, we handle a few common identities.
    """
    expr = expr.replace(" ", "")
    # Difference of squares: (a+b)(a-b) or (a-b)(a+b)
    # Using a simple regex for the identity (x+y)(x-y) = x^2 - y^2
    pattern = r'\(([a-zA-Z])\s*([\+\-])\s*([a-zA-Z])\)\s*\*\s*\(([a-zA-Z])\s*([\+\-])\s*([a-zA-Z])\)'
    match = re.match(pattern, expr)
    if match:
        x1, op1, y1, x2, op2, y2 = match.groups()
        if x1 == x2 and y1 == y2 and op1 != op2:
            return f"{x1}^2 - {y1}^2"
    
    return f"Could not expand symbolically: {expr}"

def calculator(question: str) -> str:
    """
    Safely evaluate a mathematical expression, including number words and basic algebra.
    """
    try:
        # 1. Convert number words to digits
        expr = text_to_digits(question)
        
        # 2. Check if it's symbolic (contains variables)
        if re.search(r'[a-zA-Z]', expr.replace(" ", "")):
            # Clean expression for algebra
            clean_expr = expr.replace(" ", "")
            # Handle symbolic expansion
            res = expand_algebra(clean_expr)
            if "Could not expand" in res:
                return res
            return f"= {res}"

        # 3. Standard numeric evaluation
        expr = expr.replace('^', '**')
        result = eval(expr, {"__builtins__": {}})
        return f"= {result}"
    except Exception as e:
        return f"Could not compute: {e}"

async def draw_diagram(question: str) -> tuple[str, list[str]]:
    """
    Use the LLM to generate a Mermaid.js diagram based on the user request.
    """
    prompt = f"""The user wants a diagram: {question}
    
    Generate a valid Mermaid.js diagram code.
    
    CRITICAL SYNTAX RULES:
    1. ALWAYS use 'flowchart TD' as the header (more stable than graph TD).
    2. Every node MUST have a unique alphanumeric ID.
    3. Use brackets for labels: [Label] for square, (Label) for rounded, {{Label}} for diamonds.
    4. DO NOT add empty brackets [] at the end of lines or nodes.
    5. For edges with text, use: ID1 -- "Label" --> ID2
    6. Return ONLY the Mermaid code. No markdown blocks, no intro, no outro.
    
    Example:
    flowchart TD
      A[Start] --> B{{Decision}}
      B -- Yes --> C[Success]
      B -- No --> D[Failure]
      C --> E[End]
      D --> E
    """
    
    try:
        diagram_code = await llm.generate(prompt, system_prompt="You are a Mermaid.js expert. Output ONLY valid Mermaid syntax. No conversational text. Use alphanumeric IDs for nodes and labels in brackets. Use 'flowchart TD' for better stability.")
        
        diagram_code = diagram_code.strip()
        
        # Remove markdown wraps if present
        if diagram_code.startswith("```mermaid"):
            diagram_code = diagram_code[10:]
        elif diagram_code.startswith("```"):
            diagram_code = diagram_code[3:]
        if diagram_code.endswith("```"):
            diagram_code = diagram_code[:-3]
        
        diagram_code = diagram_code.strip()

        # Fix: Remove trailing empty brackets that cause layout conflicts (e.g., H[End][] -> H[End])
        diagram_code = re.sub(r'([\]\}\)])\[\]', r'\1', diagram_code)
        
        # Validation: Ensure it starts with a valid Mermaid header
        valid_headers = ('graph', 'flowchart', 'sequenceDiagram', 'classDiagram', 'stateDiagram', 'erDiagram', 'gantt')
        if not diagram_code.lower().startswith(valid_headers):
            # Attempt to fix if it looks like a list of nodes but missing header
            if '-->' in diagram_code:
                diagram_code = "flowchart TD\n" + diagram_code
            else:
                return f"Error: LLM failed to provide a valid diagram header. Output was: {diagram_code[:50]}...", []
        
        return diagram_code, []
    except Exception as e:
        raise e

async def search_notes(question: str) -> tuple[str, list[str]]:
    """
    Retrieve chunks from RAG and generate an answer using Groq.
    """
    if rag.count() == 0:
        return "No notes uploaded yet. Upload a PDF first.", []

    # Retrieve top-3 chunks
    hits = rag.search(question, k=3)
    
    # Format chunks as [Chunk N] text
    formatted_chunks = []
    for i, hit in enumerate(hits, 1):
        formatted_chunks.append(f"[Chunk {i}]\n{hit['text']}")
    
    context_text = "\n\n".join(formatted_chunks)
    
    prompt = f"Context:\n{context_text}\n\nQuestion:\n{question}\n\nAnswer:"
    
    try:
        answer = await llm.generate(prompt, system_prompt=SYSTEM_PROMPT)
        chunks = [hit["text"] for hit in hits]
        return answer, chunks
    except Exception as e:
        # Re-raise to be handled by main.py
        raise e

async def route(question: str) -> tuple[str, str, list[str]]:
    """
    Route request to either calculator, draw_diagram, or search_notes.
    """
    # Check cache first
    cached = cache.get_cached_response(question)
    if cached:
        return cached
        
    q_lower = question.lower()
    if any(keyword in q_lower for keyword in ["draw", "diagram", "image"]):
        answer, chunks = await draw_diagram(question)
        tool = "draw_diagram"
    elif is_arithmetic(question):
        answer = calculator(question)
        chunks = []
        tool = "calculator"
    else:
        answer, chunks = await search_notes(question)
        tool = "search_notes"
    
    # Cache the result before returning
    cache.set_cached_response(question, tool, answer, chunks)
    
    return tool, answer, chunks
