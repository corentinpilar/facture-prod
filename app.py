import streamlit as st
import json
import io
import zipfile
import os
from datetime import datetime
from pypdf import PdfReader, PdfWriter
import dropbox_sign
from dropbox_sign.apis import SignatureRequestApi
from dropbox_sign.models import SignatureRequestSendRequest

# 1. CONFIGURATION ET DESIGN "STUDIO"
st.set_page_config(page_title="LE FAUX SOIR - Admin", page_icon="🎬", layout="centered")

# CSS pour la francisation et l'esthétique
st.markdown("""
    <style>
    [data-testid="stFileUploaderFileList"] { display: none !important; }
    div[data-testid="stFileUploaderDropzone"] button { display: none !important; }
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
        content: "Documents PDF uniquement • Max 200 Mo";
        display: block; font-size: 0.85rem; color: #808495; margin-top: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialisation
if 'prepret' not in st.session_state: st.session_state.prepret = False

def reset_app():
    for key in ['pdf_data', 'pdf_name', 'prepret']:
        if key in st.session_state: st.session_state[key] = False
    st.rerun()

# --- HEADER ---
st.title("🎬 LE FAUX SOIR")
st.markdown("<p style='font-size: 1.2em; color: #FF4B4B; margin-top: -20px; font-weight: bold;'>Gestionnaire de Production</p>", unsafe_allow_html=True)

# --- FENÊTRE D'ENVOI DROPBOX SIGN ---
@st.dialog("🚀 Envoyer pour signature")
def popup_dropbox(pdf_data, pdf_name):
    st.markdown("### Destinataire")
    email = st.text_input("Email (Directeur.rice de Prod)", placeholder="exemple@prod.com")
    nom = st.text_input("Nom complet", placeholder="Prénom Nom")
    
    if st.button("Confirmer l'envoi", use_container_width=True, type="primary"):
        if email and nom:
            try:
                # Utilisation des Secrets Streamlit
                api_key = st.secrets["DROPBOX_SIGN_API_KEY"]
                configuration = dropbox_sign.Configuration(username=api_key)
                
                with dropbox_sign.ApiClient(configuration) as api_client:
                    signature_api = SignatureRequestApi(api_client)
                    
                    # Fichier temporaire sécurisé
                    temp_path = "to_sign.pdf"
                    with open(temp_path, "wb") as f:
                        f.write(pdf_data)

                    request = SignatureRequestSendRequest(
                        title=f"LFS - Signature - {datetime.now().strftime('%d/%m/%Y')}",
                        subject="Documents de production à signer - Le Faux Soir",
                        message=f"Bonjour {nom}, merci de signer la liasse ci-jointe.",
                        signers=[{"email_address": email, "name": nom}],
                        files=[open(temp_path, "rb")],
                        test_mode=True # À passer sur False pour une signature réelle
                    )

                    signature_api.signature_request_send(request)
                    st.success(f"✅ Document envoyé à {nom} !")
                    st.balloons()
                    if os.path.exists(temp_path): os.remove(temp_path)
            except Exception as e:
                st.error(f"Erreur d'envoi : {e}")
        else:
            st.warning("Veuillez remplir les informations de contact.")

tab1, tab2 = st.tabs(["➕ PRÉPARER (Fusion)", "✂️ EXTRAIRE (Signature)"])

# --- ONGLET 1 : FUSION ---
with tab1:
    st.subheader("1. Préparer la liasse")
    st.markdown("<p style='color: gray; margin-top:-15px;'>Fichiers sources : dossier <b>\"OK Laurie\"</b></p>", unsafe_allow_html=True)
    
    files = st.file_uploader("uploader_1", type="pdf", accept_multiple_files=True, label_visibility="collapsed")
    
    if files:
        fichiers_tries = sorted(files, key=lambda x: x.name)
        st.divider()
        
        # Statistiques
        m1, m2 = st.columns(2)
        total_p = 0
        for f in fichiers_tries:
            try: total_p += len(PdfReader(f).pages)
            except: pass
        
        m1.metric("Documents", len(files))
        m2.metric("Total Pages", total_p)

        # Liste complète sans pagination
        with st.expander("👁️ Liste des fichiers chargés", expanded=True):
            for idx, f in enumerate(fichiers_tries, 1):
                st.markdown(f"✅ **{idx}.** {f.name}")
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("🚀 GÉNÉRER LA FUSION", use_container_width=True, type="primary"):
                writer = PdfWriter()
                carte = []
                for f in fichiers_tries:
                    reader = PdfReader(f)
                    writer.append(f)
                    carte.append({"n": f.name, "p": len(reader.pages)})
                
                metadata = {"/StructureProd": json.dumps(carte)}
                writer.add_metadata(metadata)
                pdf_out = io.BytesIO()
                writer.write(pdf_out)
                
                st.session_state.pdf_name = f"LFS - à signer - {datetime.now().strftime('%d-%m-%Y - %Hh%M')}.pdf"
                st.session_state.pdf_data = pdf_out.getvalue()
                st.session_state.prepret = True
                st.success("Liasse fusionnée !")
        
        with col_btn2:
            if st.button("🗑️ VIDER LA LISTE", use_container_width=True): reset_app()

    if st.session_state.prepret:
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            st.download_button("⬇️ TÉLÉCHARGER LE PDF", st.session_state.pdf_data, st.session_state.pdf_name, use_container_width=True)
        with c2:
            if st.button("✍️ ENVOYER EN SIGNATURE", use_container_width=True, type="primary"):
                popup_dropbox(st.session_state.pdf_data, st.session_state.pdf_name)

# --- ONGLET 2 : EXTRACTION ---
with tab2:
    st.subheader("2. Extraire les documents")
    st.markdown("""
        <p style='color: gray; margin-top:-15px;'>
        Déposer le pdf global signé par le.la directeur.rice de production ou post-production.
        </p>
        <p style='color: gray; margin-top: -10px;'>
        Les pdfs signés seront prêts à être encodés.
        </p>
        """, unsafe_allow_html=True)
    
    pdf_signe = st.file_uploader("uploader_2", type="pdf", label_visibility="collapsed")
    
    if pdf_signe:
        if st.button("⚡ LANCER L'EXTRACTION", use_container_width=True, type="primary"):
            try:
                reader = PdfReader(pdf_signe)
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
                        zf.writestr(item["n"].replace(".pdf", " (signed).pdf"), buf.getvalue())
                st.balloons()
                st.download_button("⬇️ TÉLÉCHARGER LE PACK ZIP", zip_out.getvalue(), f"LFS - Archive - {datetime.now().strftime('%d-%m-%Y')}.zip", use_container_width=True)
            except:
                st.error("Ce fichier ne contient pas les données de structure nécessaires.")

st.markdown("---")
st.markdown("<div style='text-align: center; color: #555; font-size: 0.85em;'>🎬 LE FAUX SOIR - PRODUCTION</div>", unsafe_allow_html=True)
