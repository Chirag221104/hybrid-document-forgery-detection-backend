# pdf_analyzer.py (patch)
import PyPDF2
import pikepdf
from datetime import datetime
import re
import os
import mimetypes  # add

class PDFAnalyzer:
    def __init__(self):
        self.pdf_date_pattern = re.compile(r'D:(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})')
    
    async def extract_metadata(self, file_path: str):
        """Extract real metadata from PDF file"""
        try:
            return await self._extract_with_pikepdf(file_path)
        except Exception as e:
            print(f"Pikepdf extraction failed: {e}")
            try:
                return await self._extract_with_pypdf2(file_path)
            except Exception as e2:
                print(f"PyPDF2 extraction failed: {e2}")
                return await self._get_basic_info(file_path)
    
    async def _extract_with_pikepdf(self, file_path: str):
        """Extract metadata using pikepdf"""
        with pikepdf.Pdf.open(file_path) as pdf:
            metadata = {}
            # Base docinfo fields
            if pdf.docinfo:
                docinfo = pdf.docinfo
                metadata.update({
                    "author": str(docinfo.get('/Author', 'Not specified')),
                    "title": str(docinfo.get('/Title', 'Not specified')),
                    "subject": str(docinfo.get('/Subject', 'Not specified')),
                    "creator": str(docinfo.get('/Creator', 'Not specified')),
                    "producer": str(docinfo.get('/Producer', 'Not specified')),
                    "keywords": str(docinfo.get('/Keywords', 'Not specified')),
                })
                # Dates
                creation_date = docinfo.get('/CreationDate')
                mod_date = docinfo.get('/ModDate')
                if creation_date:
                    metadata["createdDate"] = self._parse_pdf_date(str(creation_date))
                if mod_date:
                    metadata["modifiedDate"] = self._parse_pdf_date(str(mod_date))
            # XMP: get last modified by if available
            last_modified_by = None
            try:
                meta = pdf.open_metadata()  # dict-like XMP access
                for key in ("xmpMM:LastModifiedBy", "xmpMM:LastModifier", "pdfx:LastModifiedBy"):
                    if key in meta and meta[key]:
                        last_modified_by = str(meta[key])
                        break
                # If XMP has ModifyDate/MetadataDate but no person, we still keep timestamps from Info
            except Exception:
                pass
            # Nonstandard Info fallbacks
            if not last_modified_by and pdf.docinfo:
                for key in ("/LastModifiedBy", "/LastSavedBy"):
                    if key in pdf.docinfo and pdf.docinfo.get(key):
                        last_modified_by = str(pdf.docinfo.get(key))
                        break
            metadata["lastModifiedBy"] = last_modified_by or "Not specified"
            # Page count
            metadata["pageCount"] = len(pdf.pages)
            # Type for UI logic
            mime, _ = mimetypes.guess_type(file_path)
            metadata["type"] = mime or "application/pdf"
            return metadata
    
    async def _extract_with_pypdf2(self, file_path: str):
        """Extract metadata using PyPDF2"""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            metadata = {}
            if pdf_reader.metadata:
                doc_info = pdf_reader.metadata
                metadata.update({
                    "author": doc_info.get('/Author', 'Not specified'),
                    "title": doc_info.get('/Title', 'Not specified'),
                    "subject": doc_info.get('/Subject', 'Not specified'),
                    "creator": doc_info.get('/Creator', 'Not specified'),
                    "producer": doc_info.get('/Producer', 'Not specified'),
                })
                if '/CreationDate' in doc_info:
                    metadata["createdDate"] = self._parse_pdf_date(doc_info['/CreationDate'])
                if '/ModDate' in doc_info:
                    metadata["modifiedDate"] = self._parse_pdf_date(doc_info['/ModDate'])
            # XMP fallback using PyPDF2 / pypdf API
            lmb = None
            xmp = getattr(pdf_reader, "xmp_metadata", None)
            if xmp:
                try:
                    # Generic access to arbitrary XMP elements
                    # pypdf exposes a get_element(namespace_uri, local_name)
                    lmb = xmp.get_element("http://ns.adobe.com/xap/1.0/mm/", "LastModifiedBy")
                except Exception:
                    # Some builds might expose convenience properties; keep defensive
                    for attr in ("xmpmm_last_modified_by", "xmpmm_lastmodifiedby"):
                        if hasattr(xmp, attr) and getattr(xmp, attr):
                            lmb = getattr(xmp, attr)
                            break
            if not lmb and pdf_reader.metadata:
                for key in ("/LastModifiedBy", "/LastSavedBy"):
                    if key in pdf_reader.metadata:
                        lmb = pdf_reader.metadata.get(key)
                        if lmb:
                            break
            metadata["lastModifiedBy"] = str(lmb) if lmb else "Not specified"
            metadata["pageCount"] = len(pdf_reader.pages)
            # Type for UI logic
            mime, _ = mimetypes.guess_type(file_path)
            metadata["type"] = mime or "application/pdf"
            return metadata
    
    async def _get_basic_info(self, file_path: str):
        """Get basic file information when metadata extraction fails"""
        stat = os.stat(file_path)
        mime, _ = mimetypes.guess_type(file_path)
        return {
            "author": "Could not extract",
            "title": "Could not extract",
            "pageCount": "Unknown",
            "createdDate": None,
            "modifiedDate": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "lastModifiedBy": "Unknown",
            "type": mime or "application/pdf",
        }

    def _parse_pdf_date(self, date_str: str) -> str:
        """Parse PDF date format to ISO string"""
        if not date_str:
            return None
        if date_str.startswith('D:'):
            date_str = date_str[2:]
        match = self.pdf_date_pattern.match(date_str)
        if match:
            year, month, day, hour, minute, second = match.groups()
            try:
                dt = datetime(int(year), int(month), int(day), int(hour), int(minute), int(second))
                return dt.isoformat()
            except ValueError:
                pass
        return None
