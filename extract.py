import ast
import os
import glob

def extract_info(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
        tree = ast.parse(source)
    except Exception as e:
        return f"Error parsing: {e}"

    info = []
    doc = ast.get_docstring(tree)
    if doc:
        info.append(f"Module docstring: {doc}")
        
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            info.append(f"Class: {node.name}")
            doc = ast.get_docstring(node)
            if doc:
                info.append(f"  Docstring: {doc}")
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    info.append(f"  Method: {item.name}")
        elif isinstance(node, ast.FunctionDef):
            info.append(f"Function: {node.name}")
            doc = ast.get_docstring(node)
            if doc:
                info.append(f"  Docstring: {doc}")
    return "\n".join(info)

with open("summary.txt", "w", encoding='utf-8') as out:
    for file in glob.glob("*.py"):
        out.write(f"--- {file} ---\n")
        out.write(extract_info(file) + "\n\n")
