import streamlit as st
import json
import io
import zipfile
from datetime import datetime
from pypdf import PdfReader, PdfWriter

# Configuration de l'onglet du navigateur
st.set_page_config(page_title="LE FAUX SOIR - Pdf manager", page_icon="🎬")

# Titre personnalisé plus petit
st.markdown("### 🎬 LE FAUX SOIR - Pdf manager")
st.write("Gestion simplifiée des signatures de production.")

tab1, tab2 = st.tabs(["➕ PRÉPARER (Fusion)", "✂️ EXTRAIRE (Signature)"])

# --- ONGLET 1 : FUSION ---
with tab1:
    st.header("1. Préparer le PDF unique")
    files = st.file_uploader("Glissez les PDF à combiner", type="pdf", accept_multiple_files=True)
    
    if files:
        if st.button("🚀 Créer le PDF pour signature"):
            writer = PdfWriter()
            carte = []
            page_cursor = 0
            
            fichiers_tries = sorted(files, key=lambda x: x.name)
            
            for f in fichiers_tries:
                reader = PdfReader(f)
                writer.append(f)
                n_pages = len(reader.pages)
                carte.append({"n": f.name, "p": n_pages})
            
            # Stockage des infos dans les métadonnées cachées
            metadata = {"/StructureProd": json.dumps(carte)}
            writer.add_metadata(metadata)
            
            pdf_out = io.BytesIO()
            writer.write(pdf_out)
            ts = datetime.now().strftime("%d-%m-%Y_%Hh%M")
            
            st.success("✅ PDF créé avec succès.")
            st.download_button("⬇️ Télécharger le PDF", data=pdf_out.getvalue(), file_name=f"DOC_A_SIGNER_{ts}.pdf")

# --- ONGLET 2 : DECOUPAGE ---
with tab2:
    st.header("2. Extraire les pièces signées")
    pdf_signe = st.file_uploader("Importez le PDF signé", type="pdf")
    
    if pdf_signe:
        if st.button("⚡ Extraire les factures"):
            try:
                reader = PdfReader(pdf_signe)
                if "/StructureProd" not in reader.metadata:
                    st.error("Ce PDF ne contient pas les informations de découpage.")
                else:
                    carte = json.loads(reader.metadata["/StructureProd"])
                    last_page = reader.pages[-1] # Le certificat de signature
                    
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
                            # Nom du document avec (signed)
                            zf.writestr(nom_origine.replace(".pdf", " (signed).pdf"), buf.getvalue())
                    
                    st.success("✅ Extraction terminée.")
                    # Nom du ZIP avec date et heure
                    st.download_button(
                        label="⬇️ Télécharger l'archive ZIP", 
                        data=zip_out.getvalue(), 
                        file_name=f"FACTURES_SIGNEES_{ts_now}.zip"
                    )
            except Exception as e:
                st.error(f"Erreur : {e}")

st.markdown("---")
st.caption("Fait pour l'administration de production.")
