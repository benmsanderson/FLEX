import json

nb = json.load(open("outputs/vl-frankenstein-configs/notebooks/5191_extension.ipynb"))
code_count = 0
for cell in nb["cells"]:
    if cell["cell_type"] == "code":
        code_count += 1
        ec = cell.get("execution_count")
        src = "".join(cell["source"])[:80].replace("\n", " ")
        has_error = any(o.get("output_type") == "error" for o in cell.get("outputs", []))
        marker = "ERROR" if has_error else ""
        if ec and ec >= 8:
            print(f"Cell #{code_count} (exec={ec}): {src}  {marker}")
