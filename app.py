import streamlit as st
import json
import io
import zipfile
import time
from datetime import datetime
from pypdf import PdfReader, PdfWriter

# 1. CONFIGURATION ET DESIGN
st.set_page_config(page_title="© Le Faux Soir - PDF Manager", page_icon="🎬", layout="centered")

st.markdown("""
    <style>
    /* Masquer la liste de fichiers par défaut */
    [data-testid="stFileUploaderFileList"] { display: none !important; }
    
    /* Bouton personnalisé */
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

    /* RÉDUCTION DE L'ESPACE DANS LA SIDEBAR */
    section[data-testid="stSidebar"] div.stMarkdown {
        line-height: 1.2;
    }
    section[data-testid="stSidebar"] hr {
        margin-top: 0.5rem !important;
        margin-bottom: 0.5rem !important;
    }
    section[data-testid="stSidebar"] h3 {
        margin-top: -10px !important;
        padding-top: 0 !important;
        font-size: 1.1rem !important;
    }
    section[data-testid="stSidebar"] p {
        margin-bottom: 5px !important;
        font-size: 0.9rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialisation
if 'PDF_data' not in st.session_state: st.session_state.PDF_data = None

# --- BARRE LATÉRALE : GUIDE D'UTILISATION FIXE ---
with st.sidebar:
    st.title("📖 Guide")
    st.markdown("---")
    
    st.markdown("### 🚀 Étape 1 : Préparation")
    st.write("""
    1. Dossier **'OK Laurie'**.
    2. Glissez les PDFs validés.
    3. Cliquez sur **Générer**.
    4. Téléchargez le PDF unique.
    """)
    
    st.markdown("---")
    st.markdown("### ✍️ Étape 2 : Signature")
    st.write("""
    1. Compte **Dropbox Sign** Frakas.
    2. Envoyez pour signature.
    """)
    
    st.markdown("---")
    st.markdown("### 📦 Étape 3 : Split pour BOB")
    st.write("""
    1. Onglet **EXTRAIRE**.
    2. Déposez le PDF signé.
    3. Système sépare les factures.
    4. Téléchargez l'archive.
    5. Encodez dans **BOB**.
    """)
    
    st.markdown("---")
    st.caption("LE FAUX SOIR - FRAKAS PRODUCTIONS")

# --- CONTENU PRINCIPAL ---
st.title("🎬 LE FAUX SOIR")
st.markdown("<p style='font-size: 1.2em; color: #FF4B4B; margin-top: -20px; font-weight: bold;'>Gestionnaire des pièces comptables</p>", unsafe_allow_html=True)

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
                carte = [{"n": f.name, "p": len(PdfReader(f).pages)} for f in fichiers_tries]
                for f in fichiers_tries: writer.append(f)
                writer.add_metadata({"/StructureProd": json.dumps(carte)})
                PDF_out = io.BytesIO()
                writer.write(PDF_out)
                st.session_state.PDF_data = PDF_out.getvalue()
                st.session_state.PDF_name = f"LFS - à signer - {datetime.now().strftime('%d-%m-%Y')}.pdf"
                st.success("Fusion réussie !")
        with col2:
            if st.button("🗑️ VIDER TOUT", use_container_width=True):
                st.session_state.PDF_data = None
                st.rerun()

    if st.session_state.PDF_data:
        st.download_button("📥 TÉLÉCHARGER LE PDF POUR SIGNATURE", st.session_state.PDF_data, st.session_state.PDF_name, use_container_width=True)

# --- ONGLET 2 : EXTRACTION ---
with tab2:
    st.subheader("2. Extraire pour encodage BOB")
    PDF_signe = st.file_uploader("uploader_2", type="pdf", label_visibility="collapsed")
    
    if PDF_signe:
        if st.button("⚡ LANCER L'EXTRACTION", use_container_width=True, type="primary"):
            try:
                reader = PdfReader(PDF_signe)
                if "/StructureProd" not in reader.metadata:
                    st.error("Erreur : Ce PDF ne provient pas de l'étape 1.")
                else:
                    carte = json.loads(reader.metadata["/StructureProd"])
                    last_page = reader.pages[-1]
                    zip_out = io.BytesIO()
                    current_page = 0
                    
                    progress_bar = st.progress(0)
                    total_items = len(carte)
                    
                    with zipfile.ZipFile(zip_out, "w") as zf:
                        for i, item in enumerate(carte):
                            progress_bar.progress((i + 1) / total_items)
                            sw = PdfWriter()
                            for p in range(current_page, current_page + item["p"]):
                                sw.add_page(reader.pages[p])
                            sw.add_page(last_page)
                            current_page += item["p"]
                            buf = io.BytesIO()
                            sw.write(buf)
                            nom_final = item["n"].lower().replace(".pdf", " (signed).pdf")
                            zf.writestr(nom_final, buf.getvalue())
                            time.sleep(0.05)
                    
                    progress_bar.empty()
                    nom_archive = f"LFS - à encoder - {datetime.now().strftime('%d-%m-%Y_%Hh%M')}.zip"
                    st.success(f"✅ {total_items} documents extraits avec succès.")
                    st.download_button(f"⬇️ TÉLÉCHARGER : {nom_archive}", zip_out.getvalue(), nom_archive, use_container_width=True)
            except Exception as e:
                st.error(f"Erreur : {e}")

st.markdown("---")
st.markdown("<div style='text-align: center; color: #555; font-size: 0.85em;'>© Copyright - Corentin Pilarczyk</div>", unsafe_allow_html=True)
