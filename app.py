import streamlit as st
import json
import io
import zipfile
import time
from datetime import datetime
from pypdf import PdfReader, PdfWriter

# 1. CONFIGURATION ET DESIGN "APP MOBILE"
st.set_page_config(page_title="© Le Faux Soir - PDF Manager", page_icon="🎬", layout="centered")

st.markdown("""
    <style>
    /* STYLISATION DES TABS */
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

    button[data-baseweb="tab"][aria-selected="true"] {
        background-color: #FF4B4B !important;
        color: white !important;
        box-shadow: 0 4px 15px rgba(255, 75, 75, 0.3) !important;
    }

    /* Zone d'upload style App */
    [data-testid="stFileUploaderFileList"] { display: none !important; }
    div[data-testid="stFileUploaderDropzone"] {
        border: 2px dashed #FF4B4B !important;
        border-radius: 20px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialisation des états
if 'uploader_key' not in st.session_state: st.session_state.uploader_key = 0

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.title("📖 Guide")
    with st.container(border=True):
        st.markdown("**🚀 1. Préparation**")
        st.markdown("Fusionnez les PDFs. La nomenclature d'origine (MAJUSCULES) est conservée dans les métadonnées.")
    
    with st.container(border=True):
        st.markdown("**📦 3. Split & BOB**")
        st.markdown("L'extraction restaure exactement le nom de fichier initial avec le suffixe (signed).")
    
    st.markdown("### 📞 Contact")
    st.info("**Une question ou suggestion ?** [📩 Envoyez moi un mail!✌🏻](mailto:corentin.pilar@icloud.com)")
    st.caption("🎬 LE FAUX SOIR - FRAKAS PRODUCTIONS")

# --- CONTENU PRINCIPAL ---
st.title("🎬 LE FAUX SOIR")

tab1, tab2 = st.tabs(["➕ PRÉPARER", "✂️ EXTRAIRE"])

# --- ONGLET 1 : FUSION ---
with tab1:
    st.markdown("### 📂 Fusionner pour signature")
    files = st.file_uploader("uploader_1", type="pdf", accept_multiple_files=True, label_visibility="collapsed", key=f"up_{st.session_state.uploader_key}")
    
    if files:
        fichiers_tries = sorted(files, key=lambda x: x.name)
        st.divider()
        st.markdown(f"**Fichiers prêts ({len(files)}) :**")
        for f in fichiers_tries:
            st.markdown(f"✅ {f.name}")
        
        col1, col2 = st.columns(2)
        with col1:
            writer = PdfWriter()
            # On stocke le nom EXACT (avec majuscules)
            carte = [{"n": f.name, "p": len(PdfReader(f).pages)} for f in fichiers_tries]
            for f in fichiers_tries: writer.append(f)
            writer.add_metadata({"/StructureProd": json.dumps(carte)})
            
            PDF_out = io.BytesIO()
            writer.write(PDF_out)
            nom_fichier = f"LFS - à signer - {datetime.now().strftime('%d-%m-%Y')}.pdf"
            
            st.download_button(
                label="🚀 GÉNÉRER & TÉLÉCHARGER",
                data=PDF_out.getvalue(),
                file_name=nom_fichier,
                mime="application/pdf",
                use_container_width=True,
                type="primary"
            )
        with col2:
            if st.button("🗑️ VIDER TOUT", key="reset_1", use_container_width=True):
                st.session_state.uploader_key += 1
                st.rerun()

# --- ONGLET 2 : EXTRACTION ---
with tab2:
    st.markdown("### ✂️ Découper le PDF signé")
    PDF_signe = st.file_uploader("uploader_2", type="pdf", label_visibility="collapsed", key=f"split_{st.session_state.uploader_key}")
    
    if PDF_signe:
        try:
            reader = PdfReader(PDF_signe)
            if "/StructureProd" not in reader.metadata:
                st.error("⚠️ Erreur : Ce PDF ne contient pas les informations de nomenclature.")
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
                        
                        # --- CORRECTION NOMENCLATURE ---
                        # On garde le nom item["n"] tel quel (SANS .lower())
                        nom_origine = item["n"]
                        if nom_origine.lower().endswith('.pdf'):
                            nom_final = nom_origine[:-4] + " (SIGNED).pdf"
                        else:
                            nom_final = nom_origine + " (SIGNED).pdf"
                        
                        zf.writestr(nom_final, buf.getvalue())
                
                st.success(f"✅ Prêt ! Nomenclature conservée pour {len(carte)} fichiers.")
                col_ex_1, col_ex_2 = st.columns(2)
                with col_ex_1:
                    st.download_button(
                        label="⚡ TÉLÉCHARGER LE ZIP (MAJ)",
                        data=zip_out.getvalue(),
                        file_name=f"LFS_SPLIT_{datetime.now().strftime('%d-%m-%Y')}.zip",
                        mime="application/zip",
                        use_container_width=True,
                        type="primary"
                    )
                with col_ex_2:
                    if st.button("🗑️ VIDER TOUT", key="reset_2", use_container_width=True):
                        st.session_state.uploader_key += 1
                        st.rerun()
        except Exception as e:
            st.error(f"Erreur : {e}")

st.markdown("---")
st.markdown("<div style='text-align: center; color: #888; font-size: 0.8em;'>© Copyright - Corentin Pilarczyk</div>", unsafe_allow_html=True)
