from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, KeepTogether
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import os

def generate_lpo_pdf(lpo_data, items_df, output_path, assets):
    doc = SimpleDocTemplate(output_path, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        alignment=TA_CENTER,
        fontSize=16,
        spaceAfter=10
    )
    
    normal_left = ParagraphStyle('NormalLeft', parent=styles['Normal'], alignment=TA_LEFT)
    normal_right = ParagraphStyle('NormalRight', parent=styles['Normal'], alignment=TA_RIGHT)
    bold_left = ParagraphStyle('BoldLeft', parent=styles['Normal'], alignment=TA_LEFT, fontName='Helvetica-Bold')
    
    # 1. Header: Logo (Left) and Company Name (Center)
    logo_path = assets.get('logo')
    header_data = []
    
    if os.path.exists(logo_path):
        logo_img = Image(logo_path, width=1.0*inch, height=0.5*inch)
        header_data.append([logo_img, Paragraph("<b>MODEL HOUSE BUILDING CONTRACTING LLC</b>", title_style), ""])
    else:
        header_data.append(["", Paragraph("<b>MODEL HOUSE BUILDING CONTRACTING LLC</b>", title_style), ""])
        
    header_table = Table(header_data, colWidths=[1.5*inch, 4.0*inch, 1.5*inch])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (0,0), 'LEFT'),
        ('ALIGN', (1,0), (1,0), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    
    elements.append(header_table)
    elements.append(Spacer(1, 15))
    
    # 2. Metadata Table
    # Left: Purchase Order, To: [Supplier], Dubai, UAE
    # Right: No: [Number], Date: [Date], TRN: ..., Project: ...
    
    left_meta = [
        [Paragraph("<b>Purchase Order</b>", styles['Heading3'])],
        [Paragraph(f"<b>To :</b> {lpo_data.get('supplier_name', '')}", normal_left)],
        [Paragraph("Dubai, UAE", normal_left)]
    ]
    left_table = Table(left_meta, colWidths=[2.5*inch])
    left_table.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'LEFT'), ('VALIGN', (0,0), (-1,-1), 'TOP')]))
    
    right_meta = [
        [Paragraph(f"<b>no :</b> {lpo_data['number']}", normal_right)],
        [Paragraph(f"<b>Date :</b> {lpo_data['date']}", normal_right)],
        [Paragraph("<b>TRN :</b> 100542243900003", normal_right)],
        [Paragraph(f"<b>Project :</b> {lpo_data['site_name']}", normal_right)]
    ]
    right_table = Table(right_meta, colWidths=[3.5*inch])
    right_table.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'RIGHT'), ('VALIGN', (0,0), (-1,-1), 'TOP')]))
    
    meta_main_table = Table([[left_table, right_table]], colWidths=[2.5*inch, 4.5*inch])
    meta_main_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    
    elements.append(meta_main_table)
    elements.append(Spacer(1, 20))
    
    # 3. Product Table
    data = [["Description", "Unit", "QTY", "Price", "Total"]]
    for _, row in items_df.iterrows():
        data.append([
            row['Description'],
            row['Unit'],
            f"{row['QTY']}",
            f"{row['Price']:.2f}",
            f"{row['Total']:.2f}"
        ])
    
    # Totals
    data.append(["", "", "", "Net Amount:", f"{lpo_data['net_amount']:.2f}"])
    data.append(["", "", "", "VAT (5%):", f"{lpo_data['vat']:.2f}"])
    data.append(["", "", "", "Total Amount:", f"{lpo_data['total_amount']:.2f}"])
    
    # Table Styling
    row_count = len(items_df) + 1
    t = Table(data, colWidths=[3.2*inch, 0.7*inch, 0.7*inch, 1.1*inch, 1.1*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f2f2f2")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -4), 0.5, colors.grey),
        ('ALIGN', (0, -3), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, -3), (-1, -1), 'Helvetica-Bold'),
        ('LINEBELOW', (3, -1), (-1, -1), 1, colors.black),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 40))
    
    # 4. Footer Table
    # Left: Delivery Point, Payment Terms, Contact Person
    # Right: Management, Stamp/Signature
    
    footer_left = [
        [Paragraph(f"<b>Delivery Point :</b> {lpo_data.get('delivery_point', 'As per Project')}", bold_left)],
        [Paragraph("Payment Terms to be agreed", normal_left)],
        [Paragraph(f"<b>Contact Person :</b> {lpo_data['engineer']} ({lpo_data['phone']})", normal_left)]
    ]
    fl_table = Table(footer_left, colWidths=[3.5*inch])
    fl_table.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'LEFT')]))
    
    # "Mixed" Stamp and Signature
    # We can try to put them in a nested table or just stack them. 
    # To truly mix (overlap), we'd need Canvas drawing, but for Platypus, we can use a small table or stacked images.
    
    sig_elements = []
    sig_elements.append(Paragraph("<b>Management</b>", normal_right))
    
    # To overlap, we could use a single cell with both images if we had a multi-image flow,
    # but here we'll just put them side by side or one above other very closely.
    # The user wants "mix", let's try to put them in a 1x1 table with padding to look integrated.
    
    stamp_path = assets.get('stamp')
    sig_path = assets.get('signature')
    
    images_row = []
    if os.path.exists(sig_path):
        images_row.append(Image(sig_path, width=80, height=40))
    if os.path.exists(stamp_path):
        images_row.append(Image(stamp_path, width=80, height=40))
    
    if images_row:
        sig_img_table = Table([images_row], colWidths=[1.2*inch]*len(images_row))
        sig_img_table.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'RIGHT'), ('VALIGN', (0,0), (-1,-1), 'BOTTOM')]))
        sig_elements.append(sig_img_table)
    else:
        sig_elements.append(Paragraph("(Seal & Signature Required)", normal_right))

    fr_table = Table([[sig_elements]], colWidths=[3.5*inch])
    fr_table.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'RIGHT')]))
    
    footer_main_table = Table([[fl_table, fr_table]], colWidths=[3.5*inch, 3.5*inch])
    footer_main_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'BOTTOM')]))
    
    elements.append(footer_main_table)
    
    doc.build(elements)
