import streamlit as st
import json
import io
import zipfile
from datetime import datetime
from pypdf import PdfReader, PdfWriter

# Configuration de la page
st.set_page_config(page_title="LE FAUX SOIR - Pdf manager", page_icon="🎬")

# Style pour le titre
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
            
            # Sauvegarde en session pour l'affichage
            st.session_state.fusion_ok = True
            st.session_state.pdf_data = pdf_out.getvalue()
            st.session_state.pdf_name = f"DOC_A_SIGNER_{ts}.pdf"
            st.balloons() # Petite célébration

    if 'fusion_ok' in st.session_state:
        st.success("✅ Fusion terminée !")
        st.download_button("⬇️ Télécharger le PDF pour signature", 
                           data=st.session_state.pdf_data, 
                           file_name=st.session_state.pdf_name)
        
        st.markdown("---")
        # Le rappel avec l'émoji demandé
        st.warning("✍🏻 **RAPPEL :** N'oubliez pas d'envoyer ce document à signer via Dropbox Sign !")
        
        st.link_button("➡️ Ouvrir Dropbox Sign", "https://app.hellosign.com/home/login")

# --- ONGLET 2 : DECOUPAGE ---
with tab2:
    st.header("2. Extraire les pièces signées")
    st.write("Importez le document une fois qu'il a été signé sur Dropbox Sign.")
    pdf_signe = st.file_uploader("Déposez le PDF signé ici", type="pdf")
    
    if pdf_signe:
        if st.button("⚡ Extraire les factures"):
            try:
                reader = PdfReader(pdf_signe)
                if "/StructureProd" not in reader.metadata:
                    st.error("Erreur : Ce PDF ne contient pas les données de structure nécessaires.")
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
                            zf.writestr(nom_origine.replace(".pdf", " (signed).pdf"), buf.getvalue())
                    
                    st.success("✅ Extraction terminée avec succès.")
                    st.download_button(
                        label="⬇️ Télécharger l'archive ZIP", 
                        data=zip_out.getvalue(), 
                        file_name=f"FACTURES_SIGNEES_{ts_now}.zip"
                    )
            except Exception as e:
                st.error(f"Une erreur est survenue : {e}")

st.markdown("---")
st.caption("LE FAUX SOIR - Outil de gestion administrative")
