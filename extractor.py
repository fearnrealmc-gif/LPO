import pdfplumber
import pandas as pd
import io

def extract_from_excel(uploaded_file):
    try:
        df = pd.read_excel(uploaded_file)
        
        # Heuristic to map columns
        column_mapping = {
            'Description': ['Description', 'Item', 'البيان', 'الوصف'],
            'Unit': ['Unit', 'UOM', 'الوحدة'],
            'QTY': ['QTY', 'Quantity', 'الكمية'],
            'Price': ['Price', 'Rate', 'Unit Price', 'السعر']
        }
        
        new_columns = {}
        used_targets = set()
        for target, aliases in column_mapping.items():
            for col in df.columns:
                if col not in new_columns and any(alias.lower() in str(col).lower() for alias in aliases):
                    if target not in used_targets:
                        new_columns[col] = target
                        used_targets.add(target)
                        break
        
        df = df.rename(columns=new_columns)
        
        # Keep only the columns we need
        required_cols = ['Description', 'Unit', 'QTY', 'Price']
        available_cols = [c for c in required_cols if c in df.columns]
        
        # If there's a duplicate column name now (very unlikely with above logic but safe), 
        # pandas might still fail if we subset but the index isn't unique.
        df = df.loc[:, ~df.columns.duplicated()]
        df = df[available_cols]
        
        df = df.dropna(subset=['Description'])
        return df, None
    except Exception as e:
        return f"Error reading Excel: {str(e)}", None

def extract_from_pdf(uploaded_file):
    try:
        with pdfplumber.open(uploaded_file) as pdf:
            # 1. Extract Supplier Name (Heuristic)
            supplier_name = None
            first_page_text = pdf.pages[0].extract_text()
            if first_page_text:
                lines = [l.strip() for l in first_page_text.split('\n') if l.strip()]
                for i, line in enumerate(lines):
                    # Look for keywords
                    if any(key in line.upper() for key in ["SUPPLIER:", "VENDOR:", "M/S:", "TO:"]):
                        # Try to get the next part of the line or the next line
                        parts = line.split(':')
                        if len(parts) > 1 and parts[1].strip():
                            supplier_name = parts[1].strip()
                        elif i + 1 < len(lines):
                            supplier_name = lines[i+1]
                        break
                
                # If not found by keywords, try first line (often company name) if it's not the user's company
                if not supplier_name and lines:
                    if "MODEL HOUSE" not in lines[0].upper():
                        supplier_name = lines[0]

            all_data = []
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    if not table or len(table) < 2: continue
                    # Sanitize headers: remove None, unify to string
                    headers = [str(h).strip() if h is not None else "" for h in table[0]]
                    temp_df = pd.DataFrame(table[1:], columns=headers)
                    all_data.append(temp_df)
            
            if not all_data:
                return "No tables found in PDF", supplier_name
            
            # Combine all tables
            df = pd.concat(all_data, ignore_index=True)
            
            # Remove any columns that are entirely duplicate or empty-named
            df = df.loc[:, ~df.columns.duplicated()]
            
            column_mapping = {
                'Description': ['Description', 'Item', 'البيان', 'الوصف'],
                'Unit': ['Unit', 'UOM', 'الوحدة'],
                'QTY': ['QTY', 'Quantity', 'الكمية'],
                'Price': ['Price', 'Rate', 'Unit Price', 'السعر']
            }
            
            new_columns = {}
            used_targets = set()
            for target, aliases in column_mapping.items():
                for col in df.columns:
                    if col and col not in new_columns and any(alias.lower() in str(col).lower() for alias in aliases):
                        if target not in used_targets:
                            new_columns[col] = target
                            used_targets.add(target)
                            break
            
            df = df.rename(columns=new_columns)
            
            # Filter unique columns before selecting required ones
            df = df.loc[:, ~df.columns.duplicated()]
            
            required_cols = ['Description', 'Unit', 'QTY', 'Price']
            available_cols = [c for c in required_cols if c in df.columns]
            df = df[available_cols]
            
            df = df.dropna(subset=['Description'])
            
            for col in ['QTY', 'Price']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
            
            return df, supplier_name
    except Exception as e:
        return f"Error reading PDF: {str(e)}", None
