import streamlit as st
import json
import io
import zipfile
from datetime import datetime
from pypdf import PdfReader, PdfWriter
import dropbox_sign
from dropbox_sign.apis import SignatureRequestApi
from dropbox_sign.models import SignatureRequestSendRequest

# 1. CONFIGURATION ET DESIGN
st.set_page_config(page_title="LE FAUX SOIR - Admin", page_icon="🎬", layout="centered")

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
    </style>
    """, unsafe_allow_html=True)

# Initialisation de la session
if 'prepret' not in st.session_state: st.session_state.prepret = False

def reset_app():
    for key in ['pdf_data', 'pdf_name', 'prepret', 'request_id']:
        if key in st.session_state: del st.session_state[key]
    st.rerun()

# --- HEADER ---
st.title("🎬 LE FAUX SOIR")
st.markdown("<p style='font-size: 1.2em; color: #FF4B4B; margin-top: -20px; font-weight: bold;'>Gestionnaire de Production</p>", unsafe_allow_html=True)

# --- FENÊTRE D'ENVOI DROPBOX SIGN ---
@st.dialog("🚀 Envoyer pour signature")
def popup_dropbox(pdf_data, pdf_name):
    st.write(f"Document : `{pdf_name}`")
    email = st.text_input("Email du signataire (Directeur.rice de Prod)", placeholder="exemple@prod.com")
    nom = st.text_input("Nom du signataire", placeholder="Prénom Nom")
    
    if st.button("Confirmer l'envoi", use_container_width=True, type="primary"):
        if email and nom:
            try:
                # Récupération de la clé depuis les secrets Streamlit
                api_key = st.secrets["DROPBOX_SIGN_API_KEY"]
                configuration = dropbox_sign.Configuration(username=api_key)
                
                with dropbox_sign.ApiClient(configuration) as api_client:
                    signature_api = SignatureRequestApi(api_client)
                    
                    # Création d'un fichier temporaire pour l'API
                    with open("temp_to_sign.pdf", "wb") as f:
                        f.write(pdf_data)

                    request = SignatureRequestSendRequest(
                        title=f"LFS - Signature - {datetime.now().strftime('%d/%m/%Y')}",
                        subject="Documents de production à signer - Le Faux Soir",
                        message=f"Bonjour {nom}, merci de signer la liasse ci-jointe.",
                        signers=[{"email_address": email, "name": nom}],
                        files=[open("temp_to_sign.pdf", "rb")],
                        test_mode=True # À passer sur False quand tout est prêt
                    )

                    response = signature_api.signature_request_send(request)
                    st.session_state.request_id = response.signature_request.signature_request_id
                    st.success(f"✅ Envoyé avec succès ! ID : {st.session_state.request_id}")
                    st.balloons()
            except Exception as e:
                st.error(f"Erreur API : {e}")
        else:
            st.error("Veuillez remplir tous les champs.")

tab1, tab2 = st.tabs(["➕ PRÉPARER (Fusion)", "✂️ EXTRAIRE (Signature)"])

# --- ONGLET 1 : FUSION ---
with tab1:
    st.subheader("1. Préparer la liasse")
    st.markdown("<p style='color: gray;'>Fichiers sources : dossier <b>\"OK Laurie\"</b></p>", unsafe_allow_html=True)
    
    files = st.file_uploader("uploader_1", type="pdf", accept_multiple_files=True, label_visibility="collapsed")
    
    if files:
        fichiers_tries = sorted(files, key=lambda x: x.name)
        st.divider()
        m1, m2 = st.columns(2)
        total_p = sum([len(PdfReader(f).pages) for f in fichiers_tries])
        m1.metric("Documents", len(files))
        m2.metric("Total Pages", total_p)

        with st.expander("👁️ Voir le détail", expanded=False):
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
                st.success("Fusion terminée !")
        
        with col_btn2:
            if st.button("🗑️ VIDER LA LISTE", use_container_width=True): reset_app()

    if st.session_state.prepret:
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            st.download_button("⬇️ TÉLÉCHARGER (Local)", st.session_state.pdf_data, st.session_state.pdf_name, use_container_width=True)
        with c2:
            if st.button("✍️ ENVOYER EN SIGNATURE", use_container_width=True, type="primary"):
                popup_dropbox(st.session_state.pdf_data, st.session_state.pdf_name)

# --- ONGLET 2 : EXTRACTION ---
with tab2:
    st.subheader("2. Extraire les documents")
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
                        for p in range(current_page, current_page + item["p"]): sw.add_page(reader.pages[p])
                        sw.add_page(last_page)
                        current_page += item["p"]
                        buf = io.BytesIO()
                        sw.write(buf)
                        zf.writestr(item["n"].replace(".pdf", " (signed).pdf"), buf.getvalue())
                st.balloons()
                st.download_button("⬇️ TÉLÉCHARGER LE PACK ZIP", zip_out.getvalue(), f"LFS - Archive - {datetime.now().strftime('%d-%m-%Y')}.zip", use_container_width=True)
            except: st.error("Erreur : Ce PDF ne provient pas de ce logiciel.")

st.markdown("---")
st.markdown("<div style='text-align: center; color: #555; font-size: 0.85em;'>🎬 LE FAUX SOIR - PRODUCTION</div>", unsafe_allow_html=True)
