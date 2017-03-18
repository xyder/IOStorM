"""
This module contains classes and methods for certificate creation and signing.
"""

import logging
import os
import random

from OpenSSL import crypto

from core.libs.config_controller import get_config
from core.libs.exceptions import CertificateNotGeneratedException


class SSLEntity:
    def __init__(self, subject_dict, default_days_valid=3652, sign_digest='sha512'):
        """ Create a SSL entity which can be used to create and manage SSL certificates.

        :param dict subject_dict: a dict with values which will be used
        as subject for certificates.\n
            possible key-values:\n
                C               - country name\n
                ST              - state or province name\n
                L               - locality name\n
                O               - organization name\n
                OU              - organizational unit name\n
                CN              - common name\n
                emailAddress    - e-mail address\n
        :param int default_days_valid: number of days the certificate will be valid
        :param str sign_digest: digest algorithm used to sign the certificate
        """

        self.subject = subject_dict
        self.key = None
        self.certificate = None
        self.request = None

        self.days_valid = default_days_valid
        self.sign_digest = sign_digest

        self.create_private_key()

    # noinspection PyTypeChecker
    def create_certificate(self, issuer=None):
        """ Creates an X509 Certificate.

        :param SSLEntity issuer: the CA used to sign this certificate.
            If this is missing, the certificate will be self-signed.
        """

        self.certificate = crypto.X509()

        # set subject
        self._fill_subject(self.certificate, self.subject)
        # set serial
        self.certificate.set_serial_number(random.randint(2 ** 127, 2 ** 128 - 1))
        # set validity start time
        self.certificate.gmtime_adj_notBefore(0)
        # set validity end time
        self.certificate.gmtime_adj_notAfter(self.days_valid * 24 * 60 * 60)
        # set the public key
        self.certificate.set_pubkey(self.key)
        # set the issuer and sign the certificate
        if issuer:
            if not issuer.certificate:
                exception = CertificateNotGeneratedException('CA')
                logging.error(exception.args[0])
                raise exception

            self.certificate.set_issuer(issuer.certificate.get_subject())
            self.certificate.sign(issuer.key, digest=self.sign_digest)
        else:
            self.certificate.set_issuer(self.certificate.get_subject())
            self.certificate.sign(self.key, digest=self.sign_digest)

    def create_certificate_request(self):
        """ Create a certificate request for this entity. """

        self.request = crypto.X509Req()
        self._fill_subject(self.request, self.subject)
        self.request.set_pubkey(self.key)

        # noinspection PyTypeChecker
        self.request.sign(self.key, self.sign_digest)

    def create_private_key(self, digest_type=crypto.TYPE_RSA, size=2048):
        """ Create a private key object.

        :param digest_type: the digest algorithm used to created this key.
        :param int size: the size of the key to be created
        """

        self.key = crypto.PKey()
        self.key.generate_key(digest_type, size)

    def save_to_file(self, directory_path, file_name, only_certificate=False):
        """ Save the key and certificate to files at the specified combined path.

        :param str directory_path: the directory where the files will be saved
        :param str file_name: the file name that will be used for the files
        :param bool only_certificate: if set to True, only the certificate will be saved to file
        """

        # save the key if needed
        if not only_certificate:
            self._save_crypto_object(
                self.key,
                os.path.join(
                    os.path.normpath(directory_path),
                    os.path.normpath('{}.key.pem'.format(file_name))),
                crypto.dump_privatekey)

        # save the certificate
        self._save_crypto_object(
            self.certificate,
            os.path.join(
                os.path.normpath(directory_path),
                os.path.normpath('{}.cert.pem'.format(file_name))),
            crypto.dump_certificate)

    @staticmethod
    def _fill_subject(x509_object, target_subject):
        """ Fills the fields on a X509 object using the values in the given dictionary.

        :param any x509_object: the object that will be filled
        :param dict target_subject: the dictionary that will be used as source
        """

        if type(target_subject) is not dict:
            x509_object.set_subject(target_subject)
            return

        object_subject = x509_object.get_subject()

        for k, v in target_subject.items():
            try:
                setattr(object_subject, k, v)
            except AttributeError:
                pass

    @staticmethod
    def _save_crypto_object(obj, path, save_function):
        """ Saves a x509 object to a file at the specified path.

        :param any obj: the x509* object
        :param str path: the path where the file will be saved.
        :param function save_function: the function to use
        :return:
        """

        with open(path, 'wb+') as f:
            f.write(save_function(crypto.FILETYPE_PEM, obj))


def main():
    # setting up for a trusted-peer setup for TLS
    # - a local self-signed CA is used
    # - server/clients use certificates signed with this CA
    # - certificates that are not signed by this CA are rejected

    # create CA subject
    config = get_config('../../config.yml')

    # create CA entity
    cert_ca = SSLEntity(config.certificates.certificates['cert_authority'])
    cert_ca.create_certificate()

    # save CA certificate to file
    cert_ca.save_to_file(
        config.certificates.certificates['cert_authority']['dir_path'],
        config.certificates.certificates['cert_authority']['file_name']
    )

    # create remaining certificates
    for cert_key, cert_data in config.certificates.certificates.items():
        # skip already created CA
        if cert_key == 'cert_authority':
            continue

        # create certificate and save to file
        cert = SSLEntity(cert_data)
        cert.create_certificate(cert_ca)
        cert.save_to_file(cert_data['dir_path'], cert_data['file_name'])


if __name__ == '__main__':
    main()
