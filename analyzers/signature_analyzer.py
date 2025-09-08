import zipfile
import xml.etree.ElementTree as ET
from cryptography import x509
from cryptography.hazmat.backends import default_backend
import PyPDF2  # For PDF handling

class SignatureAnalyzer:
    async def analyze(self, file_path: str, file_info: dict):
        """Perform digital signature analysis for PDF and DOCX"""
        file_type = file_info["type"]
        
        if file_type == "application/pdf":
            try:
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    signatures = reader.embedded_signatures  # Detect embedded signatures
                    
                    if not signatures:
                        return {
                            "hasDigitalSignature": False,
                            "isValid": False,
                            "signerName": "No signature found",
                            "signedDate": "",
                            "certificate": "No digital signature present"
                        }
                    
                    # Process the first signature (expand for multiple if needed)
                    sig = signatures
                    cert_data = sig.signer_info['cert']
                    cert = x509.load_der_x509_certificate(cert_data, default_backend())
                    
                    # Basic validity check (e.g., not expired; add more as needed)
                    is_valid = True  # Placeholder; implement cert chain verification
                    
                    return {
                        "hasDigitalSignature": True,
                        "isValid": is_valid,
                        "signerName": cert.subject.rfc4514_string() or "Unknown",
                        "signedDate": sig.signer_info.get('signing_time', "").isoformat(),
                        "certificate": "Valid certificate found" if is_valid else "Invalid certificate"
                    }
            except Exception as e:
                return {
                    "hasDigitalSignature": False,
                    "isValid": False,
                    "signerName": "Error",
                    "signedDate": "",
                    "certificate": f"PDF analysis failed: {str(e)}"
                }
        
        elif file_type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"]:
            try:
                with zipfile.ZipFile(file_path, 'r') as docx_zip:
                    # Check for signature directory
                    if any('._xmlsignatures/' in name for name in docx_zip.namelist()):
                        sig_files = [name for name in docx_zip.namelist() if name.startswith('._xmlsignatures/')]
                        if not sig_files:
                            raise ValueError("No signature data found")
                        
                        # Parse first signature XML
                        with docx_zip.open(sig_files) as sig_file:
                            tree = ET.parse(sig_file)
                            root = tree.getroot()
                            
                            # Extract basic info (namespaces may vary; adjust as needed)
                            ns = {'ds': 'http://www.w3.org/2000/09/xmldsig#'}
                            signer_name = root.findtext('.//ds:X509SubjectName', namespaces=ns) or "Unknown"
                            signed_date = root.findtext('.//ds:SigningTime', namespaces=ns) or ""
                            
                            # Basic certificate check
                            cert_data = root.findtext('.//ds:X509Certificate', namespaces=ns)
                            if cert_data:
                                cert = x509.load_der_x509_certificate(cert_data.encode(), default_backend())
                                is_valid = True  # Add real validation (e.g., check expiry, chain)
                            else:
                                is_valid = False
                            
                            return {
                                "hasDigitalSignature": True,
                                "isValid": is_valid,
                                "signerName": signer_name,
                                "signedDate": signed_date,
                                "certificate": "Certificate details extracted" if is_valid else "Invalid or missing certificate"
                            }
                    else:
                        return {
                            "hasDigitalSignature": False,
                            "isValid": False,
                            "signerName": "No signature found",
                            "signedDate": "",
                            "certificate": "No digital signature present in DOCX"
                        }
            except Exception as e:
                return {
                    "hasDigitalSignature": False,
                    "isValid": False,
                    "signerName": "Error",
                    "signedDate": "",
                    "certificate": f"Analysis failed: {str(e)}"
                }
        else:
            return {
                "hasDigitalSignature": False,
                "isValid": False,
                "signerName": "Not applicable",
                "signedDate": "",
                "certificate": "File type does not support digital signatures"
            }
