import streamlit as st
import json
import io
import os
import zipfile
from datetime import datetime
from pypdf import PdfReader, PdfWriter

st.set_page_config(page_title="PDF Manager Prod", page_icon="🎬")

st.title("🎬 PDF Manager - Admin Production")
st.write("Outil de fusion et découpage des factures pour signature.")

tab1, tab2 = st.tabs(["➕ Fusionner (Avant signature)", "✂️ Découper (Après signature)"])

# --- FUSION ---
with tab1:
    files = st.file_uploader("Glissez les PDF à combiner", type="pdf", accept_multiple_files=True)
    if files:
        if st.button("Générer le PDF pour le DP"):
            writer = PdfWriter()
            carte = []
            page_cursor = 1
            for f in sorted(files, key=lambda x: x.name):
                reader = PdfReader(f)
                writer.append(f)
                n_pages = len(reader.pages)
                carte.append({"nom": f.name, "debut": page_cursor, "fin": page_cursor + n_pages - 1})
                page_cursor += n_pages
            
            pdf_out = io.BytesIO()
            writer.write(pdf_out)
            ts = datetime.now().strftime("%Y%m%d_%H%M")
            
            st.success("Fusion terminée !")
            st.download_button("⬇️ Télécharger le PDF", data=pdf_out.getvalue(), file_name=f"POUR_SIGNATURE_{ts}.pdf")
            st.download_button("⬇️ Télécharger le fichier JSON (IMPORTANT)", data=json.dumps(carte), file_name=f"CARTE_{ts}.json")

# --- DECOUPAGE ---
with tab2:
    signed_pdf = st.file_uploader("Le PDF signé par le DP", type="pdf")
    json_file = st.file_uploader("Le fichier JSON correspondant", type="json")
    if signed_pdf and json_file:
        if st.button("Extraire les factures individuelles"):
            carte = json.load(json_file)
            reader = PdfReader(signed_pdf)
            last_page = reader.pages[-1]
            zip_out = io.BytesIO()
            with zipfile.ZipFile(zip_out, "w") as zf:
                for e in carte:
                    sw = PdfWriter()
                    for i in range(e["debut"]-1, e["fin"]):
                        sw.add_page(reader.pages[i])
                    sw.add_page(last_page)
                    buf = io.BytesIO()
                    sw.write(buf)
                    zf.writestr(e["nom"].replace(".pdf", " (signed).pdf"), buf.getvalue())
            
            st.success("Extraction terminée !")
            st.download_button("⬇️ Télécharger toutes les pièces (ZIP)", data=zip_out.getvalue(), file_name="factures_signees.zip")
