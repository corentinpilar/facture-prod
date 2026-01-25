import streamlit as st
import json
import io
import zipfile
from datetime import datetime
from pypdf import PdfReader, PdfWriter

# CONFIGURATION
st.set_page_config(page_title="LE FAUX SOIR - Production", page_icon="🎬")

# STYLE CSS (Francisation)
st.markdown("""
    <style>
    [data-testid="stFileUploaderFileList"] { display: none !important; }
    div[data-testid="stFileUploaderDropzone"]::after {
        content: "📁 Parcourir les fichiers";
        display: inline-block; background-color: #FF4B4B; color: white;
        padding: 10px 20px; border-radius: 8px; font-weight: bold;
    }
    div[data-testid="stFileUploaderDropzone"] section > div > div::before {
        content: "🎬 Déposez les documents ici";
        display: block; font-size: 1.2rem; font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

if 'pdf_data' not in st.session_state: st.session_state.pdf_data = None

st.title("🎬 LE FAUX SOIR")

tab1, tab2, tab3 = st.tabs(["➕ 1. FUSIONNER", "✍️ 2. SIGNER", "✂️ 3. EXTRAIRE (BOB)"])

# --- 1. FUSION ---
with tab1:
    st.subheader("Préparer le document global")
    files = st.file_uploader("Fichiers", type="pdf", accept_multiple_files=True, label_visibility="collapsed")
    if files:
        if st.button("🚀 GÉNÉRER LA FUSION", use_container_width=True, type="primary"):
            writer = PdfWriter()
            carte = []
            for f in sorted(files, key=lambda x: x.name):
                reader = PdfReader(f)
                writer.append(f)
                carte.append({"n": f.name, "p": len(reader.pages)})
            writer.add_metadata({"/StructureProd": json.dumps(carte)})
            pdf_out = io.BytesIO()
            writer.write(pdf_out)
            st.session_state.pdf_data = pdf_out.getvalue()
            st.session_state.pdf_name = f"LFS - à signer - {datetime.now().strftime('%d-%m')}.pdf"
            st.success("Fusion réussie ! Téléchargez le fichier ci-dessous.")
            st.download_button("⬇️ TÉLÉCHARGER LE PDF FUSIONNÉ", st.session_state.pdf_data, st.session_state.pdf_name, use_container_width=True)

# --- 2. SIGNER ---
with tab2:
    st.subheader("Envoi pour signature")
    st.info("Puisque l'API est verrouillée sur votre compte, utilisez l'envoi manuel (plus fiable).")
    st.markdown("""
    **Marche à suivre :**
    1. Téléchargez le PDF fusionné à l'étape 1.
    2. Cliquez sur le bouton ci-dessous pour ouvrir Dropbox Sign.
    3. Glissez votre fichier sur la zone pointillée de votre écran habituel.
    """)
    st.link_button("🌐 OUVRIR DROPBOX SIGN (Interface Standard)", "https://app.hellosign.com/home/index", use_container_width=True)

# --- 3. EXTRAIRE (BOB) ---
with tab3:
    st.subheader("Extraire pour encodage BOB")
    pdf_signe = st.file_uploader("Déposer le PDF signé ici", type="pdf", label_visibility="collapsed")
    if pdf_signe:
        if st.button("⚡ LANCER L'EXTRACTION", use_container_width=True, type="primary"):
            try:
                reader = PdfReader(pdf_signe)
                carte = json.loads(reader.metadata["/StructureProd"])
                zip_out = io.BytesIO()
                current_page = 0
                with zipfile.ZipFile(zip_out, "w") as zf:
                    for item in carte:
                        sw = PdfWriter()
                        for p in range(current_page, current_page + item["p"]): sw.add_page(reader.pages[p])
                        sw.add_page(reader.pages[-1]) # Page de signature
                        current_page += item["p"]
                        buf = io.BytesIO()
                        sw.write(buf)
                        zf.writestr(item["n"].replace(".pdf", " (signed).pdf"), buf.getvalue())
                st.download_button("⬇️ TÉLÉCHARGER LE PACK ZIP POUR BOB", zip_out.getvalue(), "LFS_BOB.zip", use_container_width=True)
                st.balloons()
            except: st.error("Fichier non compatible.")
