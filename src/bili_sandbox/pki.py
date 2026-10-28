"""Per-run certificate authority for the sandbox network.

Inside the sandbox, `api.deepseek.com` resolves to the gateway and the Bilibili hostnames resolve to
the simulator. Both serve TLS with leaf certificates signed by a CA generated for that run. Agent
containers trust only that CA in addition to the system store; the CA key never leaves the run's
`pki/` directory on the host, so nothing inside a container can mint certificates.
"""
from __future__ import annotations

import datetime as dt
import ipaddress
from dataclasses import dataclass
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

from .util import write_private

VALIDITY = dt.timedelta(days=60)
# Docker Desktop's VM clock can lag the host after the Mac sleeps; certificates are backdated so a lagging
# container clock never sees them as not-yet-valid (observed: curl error 60 after an overnight sleep).
BACKDATE = dt.timedelta(days=1)


@dataclass(frozen=True)
class CertPair:
    cert: Path
    key: Path


def _write_key(key: ec.EllipticCurvePrivateKey, path: Path) -> None:
    pem = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
    write_private(path, pem.decode())


def create_ca(directory: Path, run_id: str) -> CertPair:
    key = ec.generate_private_key(ec.SECP256R1())
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, f"bili-sandbox CA {run_id}"),
                      x509.NameAttribute(NameOID.ORGANIZATION_NAME, "bili-sandbox (offline research sandbox)")])
    now = dt.datetime.now(dt.timezone.utc)
    cert = (x509.CertificateBuilder()
            .subject_name(name).issuer_name(name).public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - BACKDATE).not_valid_after(now + VALIDITY)
            .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
            .add_extension(x509.KeyUsage(digital_signature=True, key_cert_sign=True, crl_sign=True,
                                         content_commitment=False, key_encipherment=False, data_encipherment=False,
                                         key_agreement=False, encipher_only=False, decipher_only=False), critical=True)
            .add_extension(x509.SubjectKeyIdentifier.from_public_key(key.public_key()), critical=False)
            .sign(key, hashes.SHA256()))
    directory.mkdir(parents=True, exist_ok=True)
    pair = CertPair(directory / "ca.crt", directory / "ca.key")
    pair.cert.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    _write_key(key, pair.key)
    return pair


def issue_leaf(ca: CertPair, directory: Path, stem: str, dns_names: list[str], ips: list[str] = ()) -> CertPair:
    ca_cert = x509.load_pem_x509_certificate(ca.cert.read_bytes())
    ca_key = serialization.load_pem_private_key(ca.key.read_bytes(), password=None)
    key = ec.generate_private_key(ec.SECP256R1())
    now = dt.datetime.now(dt.timezone.utc)
    sans: list[x509.GeneralName] = [x509.DNSName(n) for n in dns_names]
    sans += [x509.IPAddress(ipaddress.ip_address(i)) for i in ips]
    cert = (x509.CertificateBuilder()
            .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, dns_names[0])]))
            .issuer_name(ca_cert.subject).public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - BACKDATE).not_valid_after(now + VALIDITY)
            .add_extension(x509.SubjectAlternativeName(sans), critical=False)
            .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
            .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), critical=False)
            .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()), critical=False)
            .sign(ca_key, hashes.SHA256()))
    pair = CertPair(directory / f"{stem}.crt", directory / f"{stem}.key")
    # Leaf files carry the chain (leaf + CA) so servers present a complete chain.
    pair.cert.write_bytes(cert.public_bytes(serialization.Encoding.PEM) + ca.cert.read_bytes())
    _write_key(key, pair.key)
    return pair
