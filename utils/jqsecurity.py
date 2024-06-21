from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import utils as crypto_utils
import base64

import os
import secrets

def generate_symmetric_key_as_urlsafe_base64(keygen_password):
    password = keygen_password.encode()  # Convert to type bytes

    salt = secrets.token_bytes(16)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(password)) 
    return key

def encrypt_bytes_symmetric_to_bytes(plain_bytes, key):
    f = Fernet(key)
    cipher_bytes = f.encrypt(plain_bytes) 
    return cipher_bytes
    
def decrypt_bytes_symmetric_to_bytes(ciphered_bytes, key):
    f = Fernet(key)
    plain_text_bytes = f.decrypt(ciphered_bytes) 
    return plain_text_bytes

def write_bytes_key_to_file(key_bytes, file_name):
    file = open(file_name, 'wb')  
    file.write(key_bytes)
    file.close()
    return 'done'

def write_symmetric_key_to_file(key, file_name):
    file = open(file_name, 'wb')
    file.write(key)
    file.close()

def read_symmetric_key_from_file(file_name):
    file = open(file_name, 'rb')
    key = file.read()
    file.close()
    return key

def read_key_bytes_from_file(file_name):
    file = open(file_name, 'rb') 
    key = file.read()
    file.close()
    return key

def generate_secret(secret_length):
    one_secret = secrets.token_urlsafe(secret_length)
    return one_secret

def generate_rsa_keypair_as_bytes(public_exponent_in=655537, key_size_in=4096):
    private_key = rsa.generate_private_key(
    public_exponent=public_exponent_in,
    key_size=key_size_in,
    backend=default_backend()
    )
    private_key_bytes = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
    )
    public_key = private_key.public_key()

    public_key_bytes = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return private_key_bytes, public_key_bytes

def get_rsa_private_key_bytes(private_key):
    private_key_bytes = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
    )
    return private_key_bytes

def get_rsa_public_key_bytes(public_key):
    public_key_bytes = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return public_key_bytes

def write_rsa_private_key_bytes_to_file(private_key_bytes, file_name):
    write_bytes_key_to_file(private_key_bytes, file_name)

def write_rsa_public_key_bytes_to_file(public_key_bytes, file_name):
    write_bytes_key_to_file(public_key_bytes, file_name)

def read_rsa_private_key_bytes_from_file_to_key(file_name):
    with open(file_name, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,
            backend=default_backend()
        )
    return private_key

def read_rsa_public_key_bytes_from_file_to_key(file_name):    
    with open(file_name, "rb") as key_file:
        public_key = serialization.load_pem_public_key(
            key_file.read(),
            backend=default_backend()
        )
    return public_key


def encrypt_bytes_rsa_as_bytes(plain_text_bytes, public_key):
    cipher_bytes = public_key.encrypt(
        plain_text_bytes,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return cipher_bytes

def decrypt_bytes_rsa_to_bytes(cipher_text_bytes, private_key):
    plain_text_bytes = private_key.decrypt(
        cipher_text_bytes,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return plain_text_bytes

def string_to_rsa_private_key(private_key_string_bytes):
    private_key = serialization.load_pem_private_key(
        private_key_string_bytes,
        password=None,
        backend=default_backend()
    )
    return private_key

def read_key_bytes_from_file(file_name):
    file = open(file_name, 'rb')
    key = file.read() 
    file.close()
    return key


def rsa_private_key_bytes__to_key(private_key_bytes):
    private_key = serialization.load_pem_private_key(
        private_key_bytes,
        password=None,
        backend=default_backend()
    )
    return private_key

def rsa_public_key_bytes_to_key(public_key_bytes):    
    public_key = serialization.load_pem_public_key(
        public_key_bytes,
        backend=default_backend()
    )
    return public_key
    
def crypto_sign(private_key, payload_bytes, chosen_hash):
    hasher = hashes.Hash(chosen_hash)
    hasher.update(payload_bytes)
    # hasher.update(b"some data")
    digest = hasher.finalize()
    sign = private_key.sign(digest, padding.PSS(
    mgf=padding.MGF1(hashes.SHA256()),
    salt_length=padding.PSS.MAX_LENGTH), crypto_utils.Prehashed(chosen_hash))

    return sign, digest
