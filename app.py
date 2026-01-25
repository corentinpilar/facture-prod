import streamlit as st
import json
import io
import zipfile
from datetime import datetime
from pypdf import PdfReader, PdfWriter

# 1. CONFIGURATION ET DESIGN
st.set_page_config(page_title="LE FAUX SOIR - Production", page_icon="🎬", layout="centered")

st.markdown("""
    <style>
    [data-testid="stFileUploaderFileList"] { display: none !important; }
    div[data-testid="stFileUploaderDropzone"]::after {
        content: "📁 Parcourir les fichiers";
        display: inline-block; background-color: #FF4B4B; color: white;
        padding: 10px 20px; border-radius: 8px; cursor: pointer;
        position: absolute; right: 20px; top: 20px; font-weight: bold;
    }
    div[data-testid="stFileUploaderDropzone"] section > div > div::before {
        content: "🎬 Déposez les documents ici";
        display: block; font-size: 1.2rem; font-weight: bold; color: #FAFAFA;
    }
    div[data-testid="stFileUploaderDropzone"] section > div > div::after {
        content: "PDF uniquement • dossier 'OK Laurie'";
        display: block; font-size: 0.85rem; color: #808495; margin-top: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

if 'pdf_data' not in st.session_state: st.session_state.pdf_data = None

def reset_app():
    st.session_state.pdf_data = None
    st.rerun()

# --- HEADER ---
st.title("🎬 LE FAUX SOIR")
st.markdown("<p style='font-size: 1.2em; color: #FF4B4B; margin-top: -20px; font-weight: bold;'>Gestionnaire de Production</p>", unsafe_allow_html=True)

# --- NAVIGATION ---
tab1, tab2 = st.tabs(["➕ 1. PRÉPARER (Fusion)", "✂️ 2. EXTRAIRE (BOB)"])

# --- ONGLET 1 : FUSION ---
with tab1:
    st.subheader("1. Fusionner pour signature")
    files = st.file_uploader("uploader_1", type="pdf", accept_multiple_files=True, label_visibility="collapsed")
    
    if files:
        fichiers_tries = sorted(files, key=lambda x: x.name)
        st.divider()
        
        with st.expander(f"👁️ Liste des fichiers ({len(files)})", expanded=True):
            for idx, f in enumerate(fichiers_tries, 1):
                st.markdown(f"✅ **{idx}.** {f.name}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚀 GÉNÉRER LE PDF", use_container_width=True, type="primary"):
                writer = PdfWriter()
                carte = []
                for f in fichiers_tries:
                    reader = PdfReader(f)
                    writer.append(f)
                    carte.append({"n": f.name, "p": len(reader.pages)})
                
                writer.add_metadata({"/StructureProd": json.dumps(carte)})
                pdf_out = io.BytesIO()
                writer.write(pdf_out)
                
                st.session_state.pdf_data = pdf_out.getvalue()
                st.session_state.pdf_name = f"LFS - à signer - {datetime.now().strftime('%d-%m-%Y')}.pdf"
                st.success("Fusion réussie !")
        
        with col2:
            if st.button("🗑️ VIDER TOUT", use_container_width=True):
                reset_app()

    if st.session_state.pdf_data:
        st.divider()
        st.download_button(
            label="📥 TÉLÉCHARGER LE PDF POUR SIGNATURE",
            data=st.session_state.pdf_data,
            file_name=st.session_state.pdf_name,
            mime="application/pdf",
            use_container_width=True
        )

# --- ONGLET 2 : EXTRACTION ---
with tab2:
    st.subheader("2. Extraire pour encodage BOB")
    st.markdown("<p style='color: gray; margin-top:-15px;'>Déposez ici le PDF global une fois qu'il a été signé sur Dropbox.</p>", unsafe_allow_html=True)
    
    pdf_signe = st.file_uploader("uploader_2", type="pdf", label_visibility="collapsed")
    
    if pdf_signe:
        if st.button("⚡ LANCER L'EXTRACTION", use_container_width=True, type="primary"):
            try:
                reader = PdfReader(pdf_signe)
                if "/StructureProd" not in reader.metadata:
                    st.error("Erreur : Ce PDF ne provient pas de l'étape 1.")
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
                            sw.add_page(last_page) # Ajout page signature
                            current_page += item["p"]
                            buf = io.BytesIO()
                            sw.write(buf)
                            zf.writestr(item["n"].replace(".pdf", " (signed).pdf"), buf.getvalue())
                    
                    # Nomenclature demandée : LFS - à encoder + date et heure
                    nom_archive = f"LFS - à encoder - {datetime.now().strftime('%d-%m-%Y_%Hh%M')}.zip"
                    
                    st.balloons()
                    st.download_button(
                        label=f"⬇️ TÉLÉCHARGER : {nom_archive}",
                        data=zip_out.getvalue(),
                        file_name=nom_archive,
                        use_container_width=True
                    )
            except Exception as e:
                st.error(f"Erreur : {e}")

st.markdown("---")
st.markdown("<div style='text-align: center; color: #555; font-size: 0.85em;'>🎬 LE FAUX SOIR - PRODUCTION</div>", unsafe_allow_html=True)
