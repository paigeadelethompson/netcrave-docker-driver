from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
import josepy as jose
import OpenSSL

from acme import challenges
from acme import client
from acme import crypto_util
from acme import messages


class crypto():
    def __init(self):
        pass

    def get_certificate_signing_request_and_private_key(
            self, domain_name, pkey_pem=None):
        """Create certificate signing request."""
        if pkey_pem is None:
            pkey = OpenSSL.crypto.PKey()
            pkey.generate_key(OpenSSL.crypto.TYPE_RSA, CERT_PKEY_BITS)
            pkey_pem = OpenSSL.crypto.dump_privatekey(
                OpenSSL.crypto.FILETYPE_PEM, pkey)

        csr_pem = crypto_util.make_csr(pkey_pem, [domain_name])
        return pkey_pem, csr_pem

    def select_http01_challenge_from_order(self, orderr):
        authz_list = orderr.authorizations

        for authz in authz_list:
            for i in authz.body.challenges:
                if isinstance(i.chall, challenges.HTTP01):
                    return i

        raise Exception('HTTP-01 challenge was not offered by the CA server.')

    def create_account_key(self):
        acc_key = jose.JWKRSA(
            key=rsa.generate_private_key(
                public_exponent=65537,
                key_size=os.environ.get("ACME_KEY_SIZE"),
                backend=default_backend()))

    def staging_register_account_and_accept_TOS(
            self, acc_key, which="ACME_STAGING_URL"):
        net = client.ClientNetwork(
            acc_key, user_agent=os.environ.get("ACME_USER_AGENT"))
        directory = client.ClientV2.get_directory(
            os.environ.get("ACME_STAGING_URL"), net)
        client_acme = client.ClientV2(directory, net=net)
        regr = client_acme.new_account(
            messages.NewRegistration.from_data(
                email=os.environ.get("ACME_EMAIL"),
                terms_of_service_agreed=os.environ.get("ACME_TOS_AGREE")))

        return client_acme

    def order_new_certificate(self, client_acme, csr):
        raise NotImplementedError()
