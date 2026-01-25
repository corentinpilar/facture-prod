import streamlit as st
import json
import io
import zipfile
from datetime import datetime
from pypdf import PdfReader, PdfWriter

st.set_page_config(page_title="PDF Manager Prod", page_icon="🎬")

st.title("🎬 PDF Manager - Admin Production")
st.write("Interface simplifiée : plus besoin de fichier JSON.")

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
                # On stocke le nom et le nombre de pages
                carte.append({"n": f.name, "p": n_pages})
            
            # ASTUCE : On cache la structure dans les métadonnées du PDF
            metadata = {"/StructureProd": json.dumps(carte)}
            writer.add_metadata(metadata)
            
            pdf_out = io.BytesIO()
            writer.write(pdf_out)
            ts = datetime.now().strftime("%d-%m-%Y_%Hh%M")
            
            st.success("✅ PDF créé ! Envoyez ce fichier unique à la signature.")
            st.download_button("⬇️ Télécharger le PDF", data=pdf_out.getvalue(), file_name=f"DOC_A_SIGNER_{ts}.pdf")

# --- ONGLET 2 : DECOUPAGE ---
with tab2:
    st.header("2. Extraire les pièces signées")
    pdf_signe = st.file_uploader("Importez uniquement le PDF signé", type="pdf")
    
    if pdf_signe:
        if st.button("⚡ Extraire les factures"):
            try:
                reader = PdfReader(pdf_signe)
                # On récupère la carte cachée dans le PDF
                if "/StructureProd" not in reader.metadata:
                    st.error("Ce PDF n'a pas été créé avec cette application ou les données ont été perdues.")
                else:
                    carte = json.loads(reader.metadata["/StructureProd"])
                    last_page = reader.pages[-1] # Le certificat
                    
                    zip_out = io.BytesIO()
                    current_page = 0
                    
                    with zipfile.ZipFile(zip_out, "w") as zf:
                        for item in carte:
                            sw = PdfWriter()
                            nb_pages = item["p"]
                            nom_origine = item["n"]
                            
                            # On extrait les pages correspondantes
                            for i in range(current_page, current_page + nb_pages):
                                sw.add_page(reader.pages[i])
                            
                            # On ajoute le certificat
                            sw.add_page(last_page)
                            current_page += nb_pages
                            
                            # Sauvegarde dans le ZIP
                            buf = io.BytesIO()
                            sw.write(buf)
                            zf.writestr(nom_origine.replace(".pdf", " (signé).pdf"), buf.getvalue())
                    
                    st.success("✅ Toutes les factures ont été extraites avec leurs noms d'origine !")
                    st.download_button("⬇️ Télécharger l'archive ZIP", data=zip_out.getvalue(), file_name="FACTURES_SIGNEES.zip")
            except Exception as e:
                st.error(f"Erreur lors de l'extraction : {e}")
