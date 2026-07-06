import json
import fitz

# --- CONFIGURATION ---
# enter your ACORD version identifier here.
# this will be used to target the PDF and name the output files dynamically.
ACORD_VERSION = "Acord125_2016_03_NA"

PDF_PATH = "Demodata.pdf"
# PDF_PATH = f"{ACORD_VERSION}.pdf"
FULL_OUT_PATH = f"{ACORD_VERSION}_fields_full.json"
SLIM_OUT_PATH = f"{ACORD_VERSION}_fields_slim.json"


def classify(doc):
    """Classifies the PDF type based on its structural contents."""
    for page in doc.pages():
        if list(page.widgets()):
            return "acroform"
            
    for page in doc.pages():
        if len(page.get_text().strip()) > 20:
            return "text_layer"
            
    return "raster"


def extract(pdf_path):
    """Extracts form fields and handles radio groups/checkboxes from an AcroForm PDF."""
    doc = fitz.open(pdf_path)
    
    pdf_type = classify(doc)
    if pdf_type != "acroform":
        label = {"text_layer": "a plain text PDF (no form fields)", "raster": "a scanned/raster image PDF"}[pdf_type]
        raise ValueError(f"Required format: AcroForm PDF - the given PDF is {label}.")
        
    radio_groups, fields = {}, []
    
    for page_index, page in enumerate(doc.pages()):
        page_num = page_index + 1
        for w in page.widgets():
            ftype = w.field_type_string
            fname = w.field_name or f"unnamed_p{page_num}"
            rect = [round(v, 3) for v in w.rect]
            
            if ftype == "Text":
                fields.append({
                    "field_id": fname, 
                    "type": "text", 
                    "page": page_num, 
                    "rect": rect, 
                    "fill_value": ""
                })
                
            elif ftype == "CheckBox":
                states = w.button_states().get("normal", [])
                on_val = "/" + next((s for s in states if s != "Off"), "Yes")
                fields.append({
                    "field_id": fname, 
                    "type": "checkbox", 
                    "page": page_num, 
                    "rect": rect,
                    "checked_value": on_val, 
                    "unchecked_value": "/Off", 
                    "fill_value": ""
                })
                
            elif ftype == "RadioButton":
                raw = next((s for s in w.button_states().get("normal", []) if s != "Off"), None)
                if not raw: 
                    continue
                val = "/" + raw.replace("#20", " ").replace("#22", "")
                
                if fname not in radio_groups:
                    radio_groups[fname] = {
                        "field_id": fname, 
                        "type": "radio_group", 
                        "page": page_num,
                        "radio_options": [], 
                        "fill_value": ""
                    }
                radio_groups[fname]["radio_options"].append({"value": val, "rect": rect})
                
            elif ftype == "Signature":
                fields.append({
                    "field_id": fname, 
                    "type": "signature", 
                    "page": page_num, 
                    "rect": rect,
                    "fill_value": "", 
                    "note": "Requires a dedicated signing library."
                })
                
    doc.close()
    return fields + list(radio_groups.values())


def main():
    print(f"Processing PDF: {PDF_PATH}...")
    
    try:
        # 1. Run the full structural extraction
        all_fields = extract(PDF_PATH)
    except FileNotFoundError:
        print(f"Error: The file '{PDF_PATH}' was not found. Please check your ACORD_VERSION variable.")
        return
    except ValueError as e:
        print(f"Error: {e}")
        return
        
    # 2. Save the fully structural JSON file
    full_data = {"field_count": len(all_fields), "fields": all_fields}
    with open(FULL_OUT_PATH, "w") as f:
        json.dump(full_data, f, indent=2)
    print(f"Success: {len(all_fields)} total fields written to -> {FULL_OUT_PATH}")
    
    # 3. Create the slim text-only array directly from memory
    slim_fields = [
        {"field_id": f["field_id"], "fill_value": ""}
        for f in all_fields
        if f["type"] == "text"
    ]
    
    # 4. Save the slim text-only JSON file
    with open(SLIM_OUT_PATH, "w") as f:
        json.dump(slim_fields, f, indent=2)
    print(f"Success: {len(slim_fields)} text-only fields written to -> {SLIM_OUT_PATH}")
    
    print(f"\nPaste the contents of '{SLIM_OUT_PATH}' into Gemini and ask it to fill every fill_value with realistic data.")


if __name__ == "__main__":
    main()
