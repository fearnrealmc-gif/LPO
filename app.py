import streamlit as st
import pandas as pd
import os
import io
from database import init_db, add_site, get_sites, update_site, delete_site

# Constants
ASSETS_DIR = "assets"
LOGO_PATH = os.path.join(ASSETS_DIR, "logo.png")
STAMP_PATH = os.path.join(ASSETS_DIR, "stamp.png")
SIGNATURE_PATH = os.path.join(ASSETS_DIR, "signature.png")

# Page Config
st.set_page_config(page_title="LPO Automation System", layout="wide")

# Custom UI Styling
def apply_custom_css():
    st.markdown("""
        <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@300;400;500;700&display=swap" rel="stylesheet">
        <style>
            /* Main Font */
            * {
                font-family: 'Tajawal', sans-serif !important;
            }
            
            /* Sidebar Styling */
            [data-testid="stSidebar"] {
                background-color: #f8f9fa;
                border-right: 1px solid #e0e0e0;
            }
            
            /* Header Styling */
            .main h1 {
                color: #2c3e50;
                font-weight: 700;
                border-bottom: 2px solid #3498db;
                padding-bottom: 10px;
                margin-bottom: 30px;
            }
            
            /* Metric Styling */
            [data-testid="stMetricValue"] {
                font-size: 2rem !important;
                color: #3498db !important;
            }
            
            /* Button Styling */
            .stButton>button {
                width: 100%;
                border-radius: 8px;
                height: 3em;
                background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
                color: white;
                border: none;
                transition: transform 0.2s;
            }
            .stButton>button:hover {
                transform: scale(1.02);
                color: #fff;
            }
            
            /* Card Effect for Forms */
            .stForm {
                background-color: white;
                padding: 20px;
                border-radius: 12px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                border: 1px solid #eee;
            }
            
            /* RTL Support for Arabic Text */
            .rtl {
                direction: rtl;
                text-align: right;
            }
        </style>
    """, unsafe_allow_html=True)

def save_uploaded_file(uploaded_file, save_path):
    # Ensure the directory exists
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.success(f"Saved {uploaded_file.name} successfully!")

def settings_page():
    st.title("⚙️ الإعدادات (Settings)")
    
    # Description
    st.markdown('<p class="rtl">قم بتخصيص هوية الشركة وإدارة مواقع العمل من هنا.</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        with st.container():
            st.subheader("🖼️ هوية الشركة (Company Identity)")
            
            # Logo Upload
            st.write("---")
            logo_file = st.file_uploader("رفع لوجو الشركة (Logo)", type=["png", "jpg", "jpeg"])
            if logo_file:
                save_uploaded_file(logo_file, LOGO_PATH)
            if os.path.exists(LOGO_PATH):
                st.image(LOGO_PATH, width=150, caption="المعاينه الحالية للوجو")
                
            # Stamp Upload
            st.write("---")
            stamp_file = st.file_uploader("رفع الختم (Stamp - PNG Transparent)", type=["png"])
            if stamp_file:
                save_uploaded_file(stamp_file, STAMP_PATH)
            if os.path.exists(STAMP_PATH):
                st.image(STAMP_PATH, width=150, caption="المعاينه الحالية للختم")
                
            # Signature Upload
            st.write("---")
            sig_file = st.file_uploader("رفع التوقيع (Signature - PNG Transparent)", type=["png"])
            if sig_file:
                save_uploaded_file(sig_file, SIGNATURE_PATH)
            if os.path.exists(SIGNATURE_PATH):
                st.image(SIGNATURE_PATH, width=150, caption="المعاينه الحالية للتوقيع")

    with col2:
        with st.container():
            st.subheader("🏗️ إدارة مواقع العمل (Sites Management)")
            
            # Form to add new site
            with st.form("add_site_form", clear_on_submit=True):
                st.markdown('<div class="rtl">إضافة موقع جديد</div>', unsafe_allow_html=True)
                new_site_name = st.text_input("اسم الموقع (Site Name)")
                new_engineer = st.text_input("اسم المهندس المسؤول (Engineer Name)")
                new_phone = st.text_input("رقم هاتف المهندس (Phone Number)")
                new_delivery = st.text_input("نقطة التوصيل (Delivery Point)")
                submit_button = st.form_submit_button("➕ حفظ الموقع")
                
                if submit_button:
                    if new_site_name and new_engineer and new_phone:
                        add_site(new_site_name, new_engineer, new_phone, new_delivery)
                        st.success("تم إضافة الموقع بنجاح!")
                        st.rerun()
                    else:
                        st.error("يرجى ملء جميع الحقول")

            st.write("### المواقع المسجلة")
            sites = get_sites()
            if sites:
                df_sites = pd.DataFrame(sites, columns=["ID", "Site Name", "Engineer", "Phone", "Delivery Point"])
                st.dataframe(df_sites.set_index("ID"), use_container_width=True)
                
                # Delete site option with a refined UI
                with st.expander("إجراءات متقدمة"):
                    delete_id = st.number_input("أدخل ID الموقع للحذف", min_value=1, step=1)
                    if st.button("🗑️ حذف الموقع المختار"):
                        delete_site(delete_id)
                        st.warning(f"تم حذف الموقع ذو المعرف {delete_id}")
                        st.rerun()

from extractor import extract_from_excel, extract_from_pdf
from pdf_gen import generate_lpo_pdf
from datetime import datetime

def main_dashboard():
    st.title("📄 لوحة التحكم الرئيسية (LPO Dashboard)")
    
    col1, col2 = st.columns([1, 1])
    
    sites = get_sites()
    site_options = {s[1]: {"engineer": s[2], "phone": s[3], "delivery_point": s[4]} for s in sites}
    
    with col1:
        lpo_number = st.text_input("رقم الـ LPO (LPO Number)")
        
        # Supplier Name with automatic extraction support
        if 'extracted_supplier' not in st.session_state:
            st.session_state.extracted_supplier = ""
            
        supplier_name = st.text_input("اسم المورد (Supplier Name)", key="extracted_supplier")
        selected_site_name = st.selectbox("اختار موقع العمل (Site)", options=[""] + list(site_options.keys()))
        
        contact_person = ""
        contact_phone = ""
        delivery_point = ""
        
        if selected_site_name:
            contact_person = site_options[selected_site_name]["engineer"]
            contact_phone = site_options[selected_site_name]["phone"]
            delivery_point = site_options[selected_site_name].get("delivery_point", "")
            
        st.text_input("المهندس المسؤول (Contact Person)", value=contact_person, disabled=True)
        st.text_input("رقم الهاتف (Phone)", value=contact_phone, disabled=True)
        st.text_input("نقطة التوصيل (Delivery Point)", value=delivery_point, disabled=True)

    with col2:
        st.subheader("📤 رفع ملف المنتجات")
        uploaded_file = st.file_uploader("ارفع ملف المورد (PDF, Excel, CSV)", type=["pdf", "xlsx", "xls", "csv"])
        
    if uploaded_file:
        if uploaded_file.name.endswith('.pdf'):
            df, ext_supplier = extract_from_pdf(uploaded_file)
        else:
            df, ext_supplier = extract_from_excel(uploaded_file)
            
        # Update supplier name if extracted and different from current
        if ext_supplier and ext_supplier != st.session_state.extracted_supplier:
            st.session_state.extracted_supplier = ext_supplier
            st.rerun()
            
        if isinstance(df, pd.DataFrame):
            st.write("### معاينة البيانات المستخرجة (Preview)")
            
            # Ensure required columns exist
            for col in ['Description', 'Unit', 'QTY', 'Price']:
                if col not in df.columns:
                    df[col] = ""
            
            # Ensure numeric
            df['QTY'] = pd.to_numeric(df['QTY'], errors='coerce').fillna(0)
            df['Price'] = pd.to_numeric(df['Price'], errors='coerce').fillna(0)
            
            # Edit the data
            edited_df = st.data_editor(df[['Description', 'Unit', 'QTY', 'Price']], num_rows="dynamic", use_container_width=True)
            
            # Calculations
            edited_df['Total'] = edited_df['QTY'] * edited_df['Price']
            net_amount = edited_df['Total'].sum()
            vat_amount = net_amount * 0.05
            total_amount = net_amount + vat_amount
            
            # Display Summary
            st.divider()
            c1, c2, c3 = st.columns(3)
            c1.metric("إجمالي الصافي (Net)", f"{net_amount:,.2f}")
            c2.metric("الضريبة (VAT 5%)", f"{vat_amount:,.2f}")
            c3.metric("المجموع الكلي (Total)", f"{total_amount:,.2f}")
            
            if st.button("🚀 إصدار LPO"):
                if not lpo_number or not selected_site_name:
                    st.error("يرجى إدخال رقم الـ LPO واختيار الموقع")
                else:
                    lpo_data = {
                        "number": lpo_number,
                        "supplier_name": supplier_name,
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "site_name": selected_site_name,
                        "engineer": contact_person,
                        "phone": contact_phone,
                        "delivery_point": delivery_point,
                        "net_amount": net_amount,
                        "vat": vat_amount,
                        "total_amount": total_amount
                    }
                    assets = {
                        "logo": LOGO_PATH,
                        "stamp": STAMP_PATH,
                        "signature": SIGNATURE_PATH
                    }
                    
                    pdf_filename = f"LPO_{lpo_number}.pdf"
                    generate_lpo_pdf(lpo_data, edited_df, pdf_filename, assets)
                    
                    with open(pdf_filename, "rb") as f:
                        st.download_button("📥 تحميل PDF", f, file_name=pdf_filename)
                        
                    # Excel Download
                    excel_filename = f"LPO_{lpo_number}.xlsx"
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        edited_df.to_excel(writer, index=False)
                    st.download_button("📥 تحميل Excel", buffer.getvalue(), file_name=excel_filename)
                    
                    st.success("تم إنشاء الملفات بنجاح!")
        else:
            st.error(df)

def main():
    apply_custom_css()
    # Initialize DB
    if not os.path.exists("lpo_app.db"):
        init_db()
    
    # Sidebar
    st.sidebar.title("LPO System")
    page = st.sidebar.radio("انتقل إلى:", ["لوحة التحكم", "الإعدادات"])
    
    if page == "لوحة التحكم":
        main_dashboard()
    else:
        settings_page()

if __name__ == "__main__":
    main()
