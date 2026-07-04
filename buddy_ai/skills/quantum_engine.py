"""
Quantum Computing Protocol
Connects Ultron to IBM Quantum Experience via Qiskit.
"""

from qiskit import QuantumCircuit
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
from dotenv import load_dotenv
import os

def generate_quantum_randomness() -> str:
    """
    Connects to a real IBM Quantum computer over the internet, 
    puts a physical qubit into a state of superposition (0 and 1 at the same time),
    measures it, and collapses the wave function to generate true randomness.
    """
    load_dotenv()
    api_key = os.getenv("IBM_QUANTUM_KEY", "your_api_key_here")
    
    if api_key == "your_api_key_here" or not api_key:
        return "ERROR: IBM Quantum API Key not found. Please add 'IBM_QUANTUM_KEY' to your .env file."
        
    try:
        # Connect to IBM Quantum cloud
        service = QiskitRuntimeService(channel="ibm_quantum", token=api_key)
        
        # Find the least busy physical quantum computer
        backend = service.least_busy(simulator=False, operational=True)
        
        # Create a quantum circuit with 1 qubit and 1 classical measurement bit
        qc = QuantumCircuit(1, 1)
        
        # Apply a Hadamard gate (H-gate) to put the qubit in perfect superposition
        qc.h(0)
        
        # Measure the qubit (collapses the superposition into either 0 or 1)
        qc.measure(0, 0)
        
        # Submit the circuit to the real physical quantum hardware
        sampler = SamplerV2(backend)
        
        # We run it 1 time (1 shot) to get a single random bit
        job = sampler.run([qc], shots=1)
        result = job.result()
        
        return f"SUCCESS: Quantum Protocol Executed. Wave function collapsed successfully on physical quantum backend: {backend.name}."
        
    except Exception as e:
        return f"Quantum Engine Error: {str(e)}"
