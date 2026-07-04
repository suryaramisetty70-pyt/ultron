"""
Quantum Cryptography Engine (Protocol Zero)
Uses true quantum randomness to generate AES keys and encrypt files.
Includes the "Self-Destruct" mechanism to permanently delete the encryption key.
"""

import os
import base64
from cryptography.fernet import Fernet
from dotenv import load_dotenv

# Use standard os.urandom if Qiskit isn't configured, but try Quantum first
def get_quantum_key():
    try:
        from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
        from qiskit import QuantumCircuit
        import numpy as np
        
        load_dotenv()
        token = os.getenv("IBM_QUANTUM_KEY")
        if not token:
            print("[Quantum Crypto] No IBM token found. Falling back to OS randomness.")
            return Fernet.generate_key()
            
        print("[Quantum Crypto] Connecting to IBM Quantum for True Randomness...")
        QiskitRuntimeService.save_account(channel="ibm_quantum", token=token, set_as_default=True, overwrite=True)
        service = QiskitRuntimeService()
        backend = service.least_busy(simulator=False, operational=True)
        
        qc = QuantumCircuit(32, 32)
        qc.h(range(32))
        qc.measure(range(32), range(32))
        
        sampler = SamplerV2(backend)
        job = sampler.run([qc])
        result = job.result()
        
        # Extract binary string from quantum collapse
        pub_result = result[0].data
        bit_dict = getattr(pub_result, list(pub_result.keys())[0]).get_counts()
        most_frequent_bitstring = max(bit_dict, key=bit_dict.get)
        
        # Convert quantum bits to a 32-byte key for Fernet
        import hashlib
        q_hash = hashlib.sha256(most_frequent_bitstring.encode()).digest()
        key = base64.urlsafe_b64encode(q_hash)
        print("[Quantum Crypto] Quantum Key Generated Successfully.")
        return key
    except Exception as e:
        print(f"[Quantum Crypto] Quantum generation failed: {e}. Falling back to OS randomness.")
        return Fernet.generate_key()

def quantum_lock(target_directory: str):
    """
    Generates a true quantum key, encrypts all files in the directory, and saves the key locally.
    """
    key = get_quantum_key()
    
    with open("quantum.key", "wb") as key_file:
        key_file.write(key)
        
    f = Fernet(key)
    
    for root, dirs, files in os.walk(target_directory):
        for file in files:
            file_path = os.path.join(root, file)
            with open(file_path, "rb") as file_data:
                original_data = file_data.read()
            encrypted_data = f.encrypt(original_data)
            with open(file_path, "wb") as file_data:
                file_data.write(encrypted_data)
                
    return f"SUCCESS: {target_directory} is now Quantum Locked."

def quantum_unlock(target_directory: str):
    """
    Reads the local quantum.key and decrypts the directory.
    """
    if not os.path.exists("quantum.key"):
        return "FATAL ERROR: quantum.key not found. The files cannot be decrypted."
        
    with open("quantum.key", "rb") as key_file:
        key = key_file.read()
        
    f = Fernet(key)
    
    for root, dirs, files in os.walk(target_directory):
        for file in files:
            file_path = os.path.join(root, file)
            with open(file_path, "rb") as file_data:
                encrypted_data = file_data.read()
            try:
                decrypted_data = f.decrypt(encrypted_data)
                with open(file_path, "wb") as file_data:
                    file_data.write(decrypted_data)
            except:
                return "ERROR: Decryption failed. Key is invalid or file is corrupted."
                
    return f"SUCCESS: {target_directory} has been unlocked."

def initiate_protocol_zero():
    """
    JAMES BOND MODE: Permanently deletes the quantum encryption key from the hard drive.
    Any files locked with this key will become mathematically impossible to decrypt.
    """
    if os.path.exists("quantum.key"):
        # Secure delete: overwrite with random bytes before deleting
        with open("quantum.key", "wb") as f:
            f.write(os.urandom(32))
        os.remove("quantum.key")
        print("PROTOCOL ZERO EXECUTED. Quantum key destroyed.")
        return "PROTOCOL ZERO EXECUTED. Quantum key destroyed. Files are locked forever."
    return "Protocol Zero aborted. No quantum key found on the system."
