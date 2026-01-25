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
    /* Masquer la liste par défaut de Streamlit */
    [data-testid="stFileUploaderFileList"] { display: none !important; }
    
    /* Bouton Parcourir personnalisé */
    div[data-testid="stFileUploaderDropzone"]::after {
        content: "📁 Parcourir les fichiers";
        display: inline-block; background-color: #FF4B4B; color: white;
        padding: 10px 20px; border-radius: 8px; cursor: pointer;
        position: absolute; right: 20px; top: 20px; font-weight: bold;
    }

    /* Texte de la zone de dépôt */
    div[data-testid="stFileUploaderDropzone"] section > div > div::before {
        content: "🎬 Déposez les documents ici";
        display: block; font-size: 1.2rem; font-weight: bold; color: #FAFAFA;
    }
    
    /* Sous-titre zone de dépôt */
    div[data-testid="stFileUploaderDropzone"] section > div > div::after {
        content: "PDF uniquement • dossier 'OK Laurie'";
        display: block; font-size: 0.85rem; color: #808495; margin-top: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialisation de la session
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
    st.subheader("1. Fusionner les documents pour signature")
    st.markdown("<p style='color: gray; margin-top:-15px;'>Ajouter les pdfs qui sont placés dans \"OK Laurie\"</p>", unsafe_allow_html=True)
    
    files = st.file_uploader("uploader_1", type="pdf", accept_multiple_files=True, label_visibility="collapsed")
    
    if files:
        fichiers_tries = sorted(files, key=lambda x: x.name)
        st.divider()
        
        # Statistiques rapides
        m1, m2 = st.columns(2)
        total_p = sum([len(PdfReader(f).pages) for f in fichiers_tries])
        m1.metric("Documents", len(files))
        m2.metric("Total Pages", total_p)

        with st.expander(f"👁️ Voir la liste des fichiers ({len(files)})", expanded=True):
            for idx, f in enumerate(fichiers_tries, 1):
                st.markdown(f"✅ **{idx}.** {f.name}")
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🚀 GÉNÉRER LE PDF UNIQUE", use_container_width=True, type="primary"):
                writer = PdfWriter()
                carte = []
                for f in fichiers_tries:
                    reader = PdfReader(f)
                    writer.append(f)
                    carte.append({"n": f.name, "p": len(reader.pages)})
                
                # Injection de la structure invisible pour le futur découpage
                writer.add_metadata({"/StructureProd": json.dumps(carte)})
                pdf_out = io.BytesIO()
                writer.write(pdf_out)
                
                st.session_state.pdf_data = pdf_out.getvalue()
                st.session_state.pdf_name = f"LFS - à signer - {datetime.now().strftime('%d-%m-%Y')}.pdf"
                st.success("Fusion réussie !")
        
        with c2:
            if st.button("🗑️ VIDER LA LISTE", use_container_width=True):
                reset_app()

    if st.session_state.pdf_data:
        st.divider()
        st.download_button(
            label="📥 TÉLÉCHARGER LE PDF POUR DROPBOX SIGN",
            data=st.session_state.pdf_data,
            file_name=st.session_state.pdf_name,
            mime="application/pdf",
            use_container_width=True
        )

# --- ONGLET 2 : EXTRACTION ---
with tab2:
    st.subheader("2. Extraire les pièces pour BOB")
    st.markdown("""
        <p style='color: gray; margin-top:-15px;'>
        Déposer le pdf global signé par le.la directeur.rice de production.<br>
        Les pdfs signés seront séparés et prêts à être encodés.
        </p>
        """, unsafe_allow_html=True)
    
    pdf_signe = st.file_uploader("uploader_2", type="pdf", label_visibility="collapsed")
    
    if pdf_signe:
        if st.button("⚡ LANCER L'EXTRACTION", use_container_width=True, type="primary"):
            try:
                reader = PdfReader(pdf_signe)
                # Vérification de la présence de nos métadonnées personnalisées
                if "/StructureProd" not in reader.metadata:
                    st.error("Erreur : Ce PDF ne contient pas les données de structure 'Le Faux Soir'.")
                else:
                    carte = json.loads(reader.metadata["/StructureProd"])
                    last_page = reader.pages[-1] # La page de signature Dropbox
                    zip_out = io.BytesIO()
                    current_page = 0
                    
                    with zipfile.ZipFile(zip_out, "w") as zf:
                        for item in carte:
                            sw = PdfWriter()
                            # Extraire les pages d'origine
                            for p in range(current_page, current_page + item["p"]):
                                sw.add_page(reader.pages[p])
                            # Ajouter la page de signature à la fin de chaque document
                            sw.add_page(last_page)
                            
                            current_page += item["p"]
                            buf = io.BytesIO()
                            sw.write(buf)
                            zf.writestr(item["n"].replace(".pdf", " (signed).pdf"), buf.getvalue())
                    
                    st.balloons()
                    st.download_button(
                        label="⬇️ TÉLÉCHARGER LE PACK ZIP (BOB)",
                        data=zip_out.getvalue(),
                        file_name=f"LFS - BOB - {datetime.now().strftime('%d-%m-%Y')}.zip",
                        use_container_width=True
                    )
            except Exception as e:
                st.error(f"Une erreur est survenue lors du découpage : {e}")

st.markdown("---")
st.markdown("<div style='text-align: center; color: #555; font-size: 0.85em;'>🎬 LE FAUX SOIR - PRODUCTION</div>", unsafe_allow_html=True)
