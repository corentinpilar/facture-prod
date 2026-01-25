import streamlit as st
import json
import io
import zipfile
from datetime import datetime
from pypdf import PdfReader, PdfWriter

# Configuration de la page
st.set_page_config(page_title="LE FAUX SOIR - Pdf manager", page_icon="🎬")

# Titre en police plus petite
st.markdown("### 🎬 LE FAUX SOIR - Pdf manager")

tab1, tab2 = st.tabs(["➕ PRÉPARER (Fusion)", "✂️ EXTRAIRE (Signature)"])

# --- ONGLET 1 : FUSION ---
with tab1:
    st.header("1. Préparer le PDF unique")
    files = st.file_uploader("Glissez les PDF à combiner", type="pdf", accept_multiple_files=True)
    
    if files:
        if st.button("🚀 Générer le fichier de fusion"):
            writer = PdfWriter()
            carte = []
            
            fichiers_tries = sorted(files, key=lambda x: x.name)
            
            for f in fichiers_tries:
                reader = PdfReader(f)
                writer.append(f)
                n_pages = len(reader.pages)
                carte.append({"n": f.name, "p": n_pages})
            
            # Stockage des infos dans les métadonnées
            metadata = {"/StructureProd": json.dumps(carte)}
            writer.add_metadata(metadata)
            
            pdf_out = io.BytesIO()
            writer.write(pdf_out)
            ts = datetime.now().strftime("%d-%m-%Y_%Hh%M")
            
            st.session_state.fusion_ok = True
            st.session_state.pdf_data = pdf_out.getvalue()
            st.session_state.pdf_name = f"DOC_A_SIGNER_{ts}.pdf"

    if 'fusion_ok' in st.session_state:
        # Message de succès avec l'émoji main qui signe
        st.success("✅ Fusion terminée ! Le document est prêt à être signé ✍🏻")
        st.download_button("⬇️ Télécharger le PDF pour signature", 
                           data=st.session_state.pdf_data, 
                           file_name=st.session_state.pdf_name)

# --- ONGLET 2 : DECOUPAGE ---
with tab2:
    st.header("2. Extraire les pièces signées")
    pdf_signe = st.file_uploader("Déposez le PDF signé ici", type="pdf")
    
    if pdf_signe:
        if st.button("⚡ Extraire les factures"):
            try:
                reader = PdfReader(pdf_signe)
                if "/StructureProd" not in reader.metadata:
                    st.error("Erreur : Ce PDF ne provient pas de l'onglet PRÉPARER.")
                else:
                    carte = json.loads(reader.metadata["/StructureProd"])
                    last_page = reader.pages[-1]
                    
                    zip_out = io.BytesIO()
                    current_page = 0
                    ts_now = datetime.now().strftime("%d-%m-%Y_%Hh%M")
                    
                    with zipfile.ZipFile(zip_out, "w") as zf:
                        for item in carte:
                            sw = PdfWriter()
                            nb_pages = item["p"]
                            nom_origine = item["n"]
                            for i in range(current_page, current_page + nb_pages):
                                sw.add_page(reader.pages[i])
                            sw.add_page(last_page)
                            current_page += nb_pages
                            buf = io.BytesIO()
                            sw.write(buf)
                            # Nom avec (signed)
                            zf.writestr(nom_origine.replace(".pdf", " (signed).pdf"), buf.getvalue())
                    
                    st.success("✅ Extraction terminée ✍🏻")
                    st.download_button(
                        label="⬇️ Télécharger l'archive ZIP", 
                        data=zip_out.getvalue(), 
                        file_name=f"FACTURES_SIGNEES_{ts_now}.zip"
                    )
            except Exception as e:
                st.error(f"Erreur : {e}")

st.markdown("---")
st.caption("LE FAUX SOIR - Outil interne de production")
