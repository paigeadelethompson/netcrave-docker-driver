from netcrave_docker_certificatemgr.database import docker_network_certificatemgr_database_client
from netcrave_docker_certificatemgr.crypt import crypto
import docker

def initiate_lets_encrypt_staging_request(container, message_queue):
    c = crypto()
    acc_key = c.create_account_key()
    cli = c.staging_register_account_and_accept_TOS(acc_key)
    pkey_pem, csr_pem = c.get_certificate_signing_request_and_private_key("domain.com")
    order = c.order_new_certificate(cli, csr_pem)
    challenge = c.select_http01_challenge_from_order(order)

    challenge = {
        'container': container,
        'kind': 'staging',
        'acc_key': acc_key,
        'client': cli,
        'challenge': challenge,
        'order': order,
        'private_key': pkey_pem,
        'csr': csr_pem}

    docker_network_certificatemgr_database_client().save_challenge(challenge)
    message_queue.put(challenge)

def verify_existing_certificates(containers, message_queue):
    verify_containers_certificates([c for c in containers if len(
        [l for l in c.labels.keys() if l.startswith("netcrave.certficatemgr")])])
    db = docker_network_certificatemgr_database_client()
    raise NotImplementedError()

def run(message_queue_out):
    client = docker.DockerClient(base_url = 'unix://run/docker/sock')
    containers = cli.containers.list(all = True)
    verify_existing_certificates(client, message_queue_out)

    while True:
        try:
            for evt in client.events():
                if evt.get("Type") == "Container":
                    container = client.containers.get(evt.get("id"))
                    verify_existing_certificates([container], message_queue)
        except:
            pass
