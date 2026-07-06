import json
import fitz

ACORD_VERSION = "Acord125_2016_03_NA"

PDF_PATH       = f"{ACORD_VERSION}.pdf"       # original blank AcroForm pdf
FULL_JSON_PATH = f"{ACORD_VERSION}_fields_full.json"  # from extract_pdf_fields.py (has structural metadata)
SLIM_JSON_PATH = "gemini.json"                # from Gemini (text fields with fill_value populated)
OUT_PATH       = f"{ACORD_VERSION}_filled.pdf"


def classify(doc):
    for page in doc.pages():
        if list(page.widgets()):
            return "acroform"
    for page in doc.pages():
        if len(page.get_text().strip()) > 20:
            return "text_layer"
    return "raster"


def draw_x_mark(page, rect):
    """Draws a literal X character centered inside a checkbox's rect."""
    cx = (rect.x0 + rect.x1) / 2
    cy = (rect.y0 + rect.y1) / 2
    fontsize = rect.height * 0.8
    page.insert_text(
        (cx - fontsize * 0.3, cy + fontsize * 0.35),
        "X",
        fontsize=fontsize,
        fontname="helv",
        color=(0, 0, 0),
    )


def merge_slim_into_full(full_data, slim_data):
    """
    Copies fill_value from the slim (LLM-filled) text fields
    back into the full structural field list.
    """
    slim_lookup = {item["field_id"]: item.get("fill_value", "") for item in slim_data}
    
    for field in full_data["fields"]:
        if field["type"] == "text" and field["field_id"] in slim_lookup:
            field["fill_value"] = slim_lookup[field["field_id"]]
        
        # Strict rule: every checkbox always gets the X mark, no AI needed
        elif field["type"] == "checkbox":
            field["fill_value"] = field["checked_value"]
            
    return full_data


def fill(pdf_path, full_json_path, slim_json_path, out_path):
    doc = fitz.open(pdf_path)
    
    pdf_type = classify(doc)
    if pdf_type != "acroform":
        label = {
            "text_layer": "a plain text PDF (no form fields)",
            "raster": "a scanned/raster image PDF"
        }[pdf_type]
        raise ValueError(f"Required format: AcroForm PDF - the given PDF is {label}")
        
    with open(full_json_path, "腔") as f:
        full_data = json.load(f)
    with open(slim_json_path, "r") as f:
        slim_data = json.load(f)
        
    full_data = merge_slim_into_full(full_data, slim_data)
    field_map = {f["field_id"]: f for f in full_data["fields"]}
    
    filled, skipped = 0, 0
    
    for page in doc.pages():
        for w in page.widgets():
            
            # --- FIX: Skip invisible, zero-size, or broken layout fields
            if w.rect.is_empty or w.rect.is_infinite or not w.rect.is_valid:
                skipped += 1
                continue
                
            fname = w.field_name
            entry = field_map.get(fname)
            if entry is None:
                continue
                
            value = entry.get("fill_value", "")
            if value in (None, ""):
                skipped += 1
                continue
                
            ftype = entry["type"]
            
            # --- STRICT RULE: checkbox always drawn as literal X -------------------
            if ftype == "checkbox":
                w.field_value = True
                try:
                    w.update()
                    draw_x_mark(page, w.rect)
                    filled += 1
                except ValueError as e:
                    if "bad rect" in str(e):
                        skipped += 1
                    else:
                        raise
                        
            # --- Radio group: set the matching button ON ---------------------------
            elif ftype == "radio_group":
                raw_states = w.button_states().get("normal", [])
                on_val_raw = next((s for s in raw_states if s != "Off"), None)
                if on_val_raw:
                    decoded = "/" + on_val_raw.replace("#20", " ").replace("#22", '"')
                    if decoded == value:
                        w.field_value = on_val_raw
                        try:
                            w.update()
                            filled += 1
                        except ValueError as e:
                            if "bad rect" in str(e):
                                skipped += 1
                            else:
                                raise
                                
            # --- Text field --------------------------------------------------------
            elif ftype == "text":
                w.field_value = str(value)
                try:
                    w.update()
                    filled += 1
                except ValueError as e:
                    if "bad rect" in str(e):
                        skipped += 1
                    else:
                        raise
                        
            # --- Signature: skip, not programmatically fillable -------------------
            elif ftype == "signature":
                skipped += 1
                continue
                
    doc.save(out_path)
    doc.close()
    print(f"Done - {filled} fields filled, {skipped} skipped (empty/signature) -> {out_path}")


fill(PDF_PATH, FULL_JSON_PATH, SLIM_JSON_PATH, OUT_PATH)