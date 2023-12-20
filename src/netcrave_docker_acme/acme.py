from netcrave_docker_acme.crypt import crypto


def initiate_lets_encrypt_request(container, request):
    c = crypto()
    acc_key = c.create_account_key()
    cli = c.staging_register_account_and_accept_TOS(acc_key)
    pkey_pem, csr_pem = c.get_certificate_signing_request_and_private_key(
        request.get("domain"))
    order = c.order_new_certificate(cli, csr_pem)
    challenge = c.select_http01_challenge_from_order(order)
    return {
        'kind': request.get("kind"),
        'acc_key': acc_key,
        'client': cli,
        'challenge': challenge,
        'order': order,
        'private_key': pkey_pem,
        'csr': csr_pem}
