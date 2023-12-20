from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
import datetime
import uuid
import logging
from pathlib import Path


class ez_rsa():
    def __init__(self):
        pass

    def get_netcrave_certificate(self):
        key = serialization.load_pem_private_key(
            open("/etc/netcrave/ssl/_netcrave.key").read(),
            password=None)

        cert = x509.load_pem_x509_certificate(
            open("/etc/netcrave/ssl/_netcrave.pem").read(),
            default_backend())

        return key, cert

    async def netcrave_certificate(self):
        if not (Path("/etc/netcrave/ssl/ca.key").exists()
                and not Path("/etc/netcrave/ssl/ca.pem").exists()):
            await self.create_default_ca()
        if not (Path("/etc/netcrave/ssl/_netcrave.key").exists()
                and not Path("/etc/netcrave/ssl/_netcrave.pem").exists()):
            return await self.create_server_certificate(
                domain="netcrave.local",
                country="US",
                state="WA",
                locality="Seattle",
                org="Netcrave Communications",
                key_file_dest="/etc/netcrave/ssl/_netcrave.key",
                cert_file_dest="/etc/netcrave/ssl/_netcrave.pem")
        else:
            return self

    async def create_server_certificate(self, domain, country, state, locality, org, key_file_dest, cert_file_dest):
        log = logging.getLogger(__name__)
        if Path(key_file_dest).exists() or Path(cert_file_dest).exists():
            log.info("netcrave-docker certificate already exists, not creating")
            return self

        root_key = serialization.load_pem_private_key(
            open("/etc/netcrave/ssl/ca.key", 'rb').read(),
            password=None,
            backend=default_backend())

        root_cert = x509.load_pem_x509_certificate(
            open("/etc/netcrave/ssl/ca.pem", 'rb').read(),
            default_backend())

        cert_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend())

        new_subject = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, country),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, state),
            x509.NameAttribute(NameOID.LOCALITY_NAME, locality),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, org)])

        cert = (
            x509.CertificateBuilder()
            .subject_name(new_subject)
            .issuer_name(root_cert.issuer)
            .public_key(cert_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.datetime(1950, 1, 1))
            .not_valid_after(datetime.datetime.max)
            .add_extension(
                x509.SubjectAlternativeName([x509.DNSName(domain)]),
                critical=False)
            .sign(root_key, hashes.SHA512(), default_backend()))

        with open(key_file_dest, "wb") as f:
            f.write(cert_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()))

        with open(cert_file_dest, "wb") as f:
            f.write(cert.public_bytes(
                encoding=serialization.Encoding.PEM))

        return self

    async def create_default_ca(self):
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
            backend=default_backend())

        public_key = private_key.public_key()
        builder = x509.CertificateBuilder()

        builder = builder.subject_name(
            x509.Name(
                [x509.NameAttribute(NameOID.COMMON_NAME, u'Netcrave CA'),
                 x509.NameAttribute(
                     NameOID.ORGANIZATION_NAME, u'_netcrave'),
                 x509.NameAttribute(
                     NameOID.ORGANIZATIONAL_UNIT_NAME,
                    u'Netcrave internal CA')]))

        builder = builder.issuer_name(x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, u'netcrave')]))

        builder = builder.not_valid_before(datetime.datetime(1950, 1, 1))
        builder = builder.not_valid_after(datetime.datetime.max)
        builder = builder.serial_number(int(uuid.uuid4()))
        builder = builder.public_key(public_key)

        builder = builder.add_extension(
            x509.BasicConstraints(ca=True, path_length=None), critical=True)

        certificate = builder.sign(
            private_key=private_key, algorithm=hashes.SHA512(),
            backend=default_backend())

        with open("/etc/netcrave/ssl/ca.key", "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()))

        with open("/etc/netcrave/ssl/ca.pem", "wb") as f:
            f.write(certificate.public_bytes(
                encoding=serialization.Encoding.PEM))

        return self
