import streamlit as st
import json
import io
import zipfile
import time
from datetime import datetime
from pypdf import PdfReader, PdfWriter

# 1. CONFIGURATION ET DESIGN "APP MOBILE"
st.set_page_config(page_title="© PDF Manager", page_icon="🎬", layout="centered")

st.markdown("""
    <style>
    /* 1. STYLISATION DES TABS */
    button[data-baseweb="tab"] {
        background-color: transparent !important;
        border: none !important;
        border-radius: 12px !important;
        margin: 5px !important;
        padding: 10px 20px !important;
        transition: all 0.3s ease !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px !important;
    }

    button[data-baseweb="tab"]:hover {
        background-color: rgba(255, 75, 75, 0.1) !important;
        color: #FF4B4B !important;
    }

    button[data-baseweb="tab"][aria-selected="true"] {
        background-color: #FF4B4B !important;
        color: white !important;
        box-shadow: 0 4px 15px rgba(255, 75, 75, 0.3) !important;
    }

    div[data-baseweb="tab-list"] {
        gap: 10px !important;
        background-color: rgba(0,0,0,0.05) !important;
        padding: 8px !important;
        border-radius: 16px !important;
        border-bottom: none !important;
    }
    
    /* 2. BARRE LATÉRALE */
    [data-testid="stSidebar"] {
        background-color: #F8F9FB !important;
    }
    
    @media (prefers-color-scheme: dark) {
        [data-testid="stSidebar"] { background-color: #111111 !important; }
    }

    /* Zone d'upload */
    [data-testid="stFileUploaderFileList"] { display: none !important; }
    div[data-testid="stFileUploaderDropzone"] {
        border: 2px dashed #FF4B4B !important;
        border-radius: 20px !important;
        background-color: rgba(255, 75, 75, 0.02) !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialisation des états pour le reset
if 'uploader_key' not in st.session_state: st.session_state.uploader_key = 0

# --- BARRE LATÉRALE : GUIDE FIXE ---
with st.sidebar:
    st.title("📖 Guide")
    
    # Bloc 1
    with st.container(border=True):
        st.markdown("**🚀 1. Préparation**")
        st.markdown("Déposez les PDFs validés, générez et téléchargez le fichier unique sur votre ordinateur.")
    
    # Bloc 2
    with st.container(border=True):
        st.markdown("**✍️ 2. Signature**")
        st.markdown("Utilisez le compte YouSign pour faire signer le PDF unique.")
    
    # Bloc 3
    with st.container(border=True):
        st.markdown("**📦 3. Split & encodage**")
        st.markdown("Déposez le PDF signé dans l'onglet **EXTRAIRE**. Le système sépare les factures pour l'encodage dans HORUS.")
    
    # --- CONTACT ---
    st.markdown("### 📞 Contact")
    st.info("**Une question ou suggestion ?** [📩 Envoyez moi un mail!✌🏻](mailto:corentin.pilar@icloud.com)")
    
    st.markdown(" ")
    st.caption("🎬 Corentin Pilarczyk")

# --- CONTENU PRINCIPAL ---
st.title("🎬 PDF Manager")
st.markdown("<p style='font-size: 1.1em; color: gray; margin-top: -20px;'>Gestionnaire des pièces comptables</p>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["➕ PRÉPARER", "✂️ EXTRAIRE"])

# --- ONGLET 1 : FUSION ---
with tab1:
    st.markdown("### 📂 Fusionner pour signature")
    
    files = st.file_uploader(
        "uploader_1", 
        type="pdf", 
        accept_multiple_files=True, 
        label_visibility="collapsed",
        key=f"up1_{st.session_state.uploader_key}"
    )
    
    if files:
        fichiers_tries = sorted(files, key=lambda x: x.name)
        st.divider()
        st.markdown(f"**Fichiers prêts ({len(files)}) :**")
        for f in fichiers_tries:
            st.markdown(f"✅ {f.name}")
        
        st.markdown(" ")
        col1, col2 = st.columns(2)
        
        with col1:
            writer = PdfWriter()
            # On enregistre le nom exact tel quel (MAJUSCULES préservées)
            carte = [{"n": f.name, "p": len(PdfReader(f).pages)} for f in fichiers_tries]
            for f in fichiers_tries: writer.append(f)
            writer.add_metadata({"/StructureProd": json.dumps(carte)})
            
            PDF_out = io.BytesIO()
            writer.write(PDF_out)
            nom_fusion = f"LFS - à signer - {datetime.now().strftime('%d-%m-%Y')}.pdf"
            
            st.download_button(
                label="🚀 GÉNÉRER & TÉLÉCHARGER",
                data=PDF_out.getvalue(),
                file_name=nom_fusion,
                mime="application/pdf",
                use_container_width=True,
                type="primary"
            )
        
        with col2:
            if st.button("🗑️ VIDER TOUT", key="reset_tab1", use_container_width=True):
                st.session_state.uploader_key += 1
                st.rerun()

# --- ONGLET 2 : EXTRACTION ---
with tab2:
    st.markdown("### ✂️ Découper le PDF signé")
    PDF_signe = st.file_uploader("uploader_2", type="pdf", label_visibility="collapsed", key=f"up2_{st.session_state.uploader_key}")
    
    if PDF_signe:
        try:
            reader = PdfReader(PDF_signe)
            if "/StructureProd" not in reader.metadata:
                st.error("⚠️ Ce PDF ne contient pas les informations de structure nécessaires.")
            else:
                carte = json.loads(reader.metadata["/StructureProd"])
                last_page = reader.pages[-1]
                zip_out = io.BytesIO()
                current_page = 0
                
                with zipfile.ZipFile(zip_out, "w") as zf:
                    for item in carte:
                        sw = PdfWriter()
                        for p in range(current_page, current_page + item["p"]):
                            sw.add_page(reader.pages[p])
                        sw.add_page(last_page)
                        current_page += item["p"]
                        
                        buf = io.BytesIO()
                        sw.write(buf)
                        
                        # NOMENCLATURE : Nom d'origine (MAJ) + (signed) en minuscule
                        nom_origine = item["n"]
                        if nom_origine.lower().endswith('.pdf'):
                            # On retire l'extension .pdf (peu importe sa casse) et on ajoute le suffixe
                            nom_final = nom_origine[:-4] + " (signed).pdf"
                        else:
                            nom_final = nom_origine + " (signed).pdf"
                        
                        zf.writestr(nom_final, buf.getvalue())
                
                st.success(f"✅ {len(carte)} documents prêts avec nomenclature respectée.")
                
                col_ex1, col_ex2 = st.columns(2)
                with col_ex1:
                    st.download_button(
                        label="⚡ TÉLÉCHARGER LES DOCUMENTS SPLITÉS",
                        data=zip_out.getvalue(),
                        file_name=f"LFS - split - {datetime.now().strftime('%d-%m-%Y')}.zip",
                        mime="application/zip",
                        use_container_width=True,
                        type="primary"
                    )
                with col_ex2:
                    if st.button("🗑️ VIDER TOUT", key="reset_tab2", use_container_width=True):
                        st.session_state.uploader_key += 1
                        st.rerun()
                        
        except Exception as e:
            st.error(f"Erreur : {e}")

st.markdown("---")
st.markdown("<div style='text-align: center; color: #888; font-size: 0.8em;'>© Copyright - Corentin Pilarczyk</div>", unsafe_allow_html=True)
