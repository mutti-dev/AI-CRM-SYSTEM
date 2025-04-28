import json

file_path = "json.txt"  # Update this with the path to your text file containing JSON

def recursive_json_parse(s):
    # Recursively parse s while it is a JSON-encoded string
    try:
        data = s
        while isinstance(data, str):
            parsed = json.loads(data)
            if not isinstance(parsed, str):
                data = parsed
            else:
                break
        return data
    except json.JSONDecodeError as e:
        # Get a snippet of the JSON where the error occurred (20 characters before and after error position)
        snippet = s[max(0, e.pos-20): e.pos+20]
        print(f"Warning: unable to recursively parse JSON: {e.msg} at line {e.lineno} column {e.colno} (char {e.pos}).")
        print(f"Field snippet around error: '{snippet}'")
        return s
    except Exception as e:
        print(f"Warning: unable to recursively parse JSON: {e}")
        return s

try:
    # Read the raw JSON string from the file
    with open(file_path, "r", encoding="utf-8") as f:
        raw_json = f.read()

    # Load the JSON (outer level)
    outer = json.loads(raw_json)
    if isinstance(outer, str):
        outer = recursive_json_parse(outer)

    # If there is a nested 'config' field, decode it as JSON too
    if "config" in outer:
        if isinstance(outer["config"], str):
            outer["config"] = recursive_json_parse(outer["config"])
        else:
            print("Warning: 'config' is not a string, skipping nested parsing.")

    components = outer.get("config", {}).get("components", [])
    if len(components) > 1:
        second_component = components[1]
        
        
    else:
        print("Second component not found or components list is too short.")


    # Prettify the JSON with indentations
    pretty_json = json.dumps(second_component, indent=4)

    # Write the formatted JSON back to the same file
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(pretty_json)

    print(f"Formatted JSON has been written to {file_path}")
except Exception as e:
    print(f"Error processing JSON: {e}")