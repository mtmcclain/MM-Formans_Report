"""
Extract all form field names from a PDF file
Useful for mapping data to PDF templates
"""
import fitz  # PyMuPDF
import sys
from pathlib import Path

def extract_pdf_fields(pdf_path: str):
    """Extract all form field names from a PDF"""
    try:
        doc = fitz.open(pdf_path)
        
        print(f"\n{'='*60}")
        print(f"PDF: {pdf_path}")
        print(f"Pages: {len(doc)}")
        print(f"{'='*60}\n")
        
        all_fields = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            widgets = page.widgets()
            
            if widgets:
                print(f"Page {page_num + 1}:")
                print("-" * 60)
                
                for widget in widgets:
                    field_name = widget.field_name
                    field_type = widget.field_type_string
                    field_value = widget.field_value if hasattr(widget, 'field_value') else ""
                    
                    print(f"  Field: {field_name}")
                    print(f"    Type: {field_type}")
                    if field_value:
                        print(f"    Current Value: {field_value}")
                    print()
                    
                    all_fields.append({
                        'name': field_name,
                        'type': field_type,
                        'page': page_num + 1
                    })
            else:
                print(f"Page {page_num + 1}: No form fields found")
                print()
        
        doc.close()
        
        # Summary
        print(f"\n{'='*60}")
        print(f"SUMMARY")
        print(f"{'='*60}")
        print(f"Total fields found: {len(all_fields)}")
        print(f"\nAll field names (comma-separated):")
        print(", ".join([f['name'] for f in all_fields]))
        
        print(f"\n\nAll field names (one per line):")
        for field in all_fields:
            print(field['name'])
        
        print(f"\n\nField names with types:")
        for field in all_fields:
            print(f"{field['name']} ({field['type']})")
        
        return all_fields
        
    except FileNotFoundError:
        print(f"ERROR: File not found: {pdf_path}")
        return None
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        # Default to BlankTime.pdf if no argument provided
        pdf_path = "BlankTime.pdf"
    
    # Check if file exists
    if not Path(pdf_path).exists():
        print(f"ERROR: PDF file not found: {pdf_path}")
        print("\nUsage:")
        print("  python extract_pdf_fields.py [pdf_file_path]")
        print("\nExample:")
        print("  python extract_pdf_fields.py BlankTime.pdf")
        print("  python extract_pdf_fields.py BlankForemanReport.pdf")
        sys.exit(1)
    
    extract_pdf_fields(pdf_path)
