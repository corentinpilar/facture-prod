import dropbox_sign
from dropbox_sign.apis import SignatureRequestApi
from dropbox_sign.models import SignatureRequestSendRequest

def envoyer_pour_signature(pdf_data, email_signataire, nom_signataire):
    # Configuration avec ta clé API
    configuration = dropbox_sign.Configuration(username="TA_CLE_API_ICI")
    
    with dropbox_sign.ApiClient(configuration) as api_client:
        signature_api = SignatureRequestApi(api_client)

        # Création de la requête
        request = SignatureRequestSendRequest(
            title="Signature documents de production - LFS",
            subject="Documents de production à signer",
            message="Bonjour, merci de signer la liasse ci-jointe.",
            signers=[{"email_address": email_signataire, "name": nom_signataire}],
            files=[pdf_data], # Ton PDF fusionné
            test_mode=True    # Garder à True pendant tes tests (gratuit)
        )

        response = signature_api.signature_request_send(request)
        return response.signature_request.signature_request_id
