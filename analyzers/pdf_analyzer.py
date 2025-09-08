import PyPDF2
import pikepdf
from datetime import datetime
import re
import os

class PDFAnalyzer:
    def __init__(self):
        self.pdf_date_pattern = re.compile(r'D:(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})')
    
    async def extract_metadata(self, file_path: str):
        """Extract real metadata from PDF file"""
        try:
            # Try pikepdf first (more reliable)
            return await self._extract_with_pikepdf(file_path)
        except Exception as e:
            print(f"Pikepdf extraction failed: {e}")
            try:
                # Fallback to PyPDF2
                return await self._extract_with_pypdf2(file_path)
            except Exception as e2:
                print(f"PyPDF2 extraction failed: {e2}")
                return await self._get_basic_info(file_path)
    
    async def _extract_with_pikepdf(self, file_path: str):
        """Extract metadata using pikepdf"""
        with pikepdf.Pdf.open(file_path) as pdf:
            metadata = {}
            
            # Get document info
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
                
                # Parse dates
                creation_date = docinfo.get('/CreationDate')
                mod_date = docinfo.get('/ModDate')
                
                if creation_date:
                    metadata["createdDate"] = self._parse_pdf_date(str(creation_date))
                if mod_date:
                    metadata["modifiedDate"] = self._parse_pdf_date(str(mod_date))
            
            # Get page count
            metadata["pageCount"] = len(pdf.pages)
            
            return metadata
    
    async def _extract_with_pypdf2(self, file_path: str):
        """Extract metadata using PyPDF2"""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            metadata = {}
            
            # Get document info
            if pdf_reader.metadata:
                doc_info = pdf_reader.metadata
                metadata.update({
                    "author": doc_info.get('/Author', 'Not specified'),
                    "title": doc_info.get('/Title', 'Not specified'),
                    "subject": doc_info.get('/Subject', 'Not specified'),
                    "creator": doc_info.get('/Creator', 'Not specified'),
                    "producer": doc_info.get('/Producer', 'Not specified'),
                })
                
                # Parse dates
                if '/CreationDate' in doc_info:
                    metadata["createdDate"] = self._parse_pdf_date(doc_info['/CreationDate'])
                if '/ModDate' in doc_info:
                    metadata["modifiedDate"] = self._parse_pdf_date(doc_info['/ModDate'])
            
            # Get page count
            metadata["pageCount"] = len(pdf_reader.pages)
            
            return metadata
    
    async def _get_basic_info(self, file_path: str):
        """Get basic file information when metadata extraction fails"""
        stat = os.stat(file_path)
        return {
            "author": "Could not extract",
            "title": "Could not extract",
            "pageCount": "Unknown",
            "createdDate": None,
            "modifiedDate": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        }
    
    def _parse_pdf_date(self, date_str: str) -> str:
        """Parse PDF date format to ISO string"""
        if not date_str:
            return None
            
        # Remove 'D:' prefix if present
        if date_str.startswith('D:'):
            date_str = date_str[2:]
        
        # Extract date components using regex
        match = self.pdf_date_pattern.match(date_str)
        if match:
            year, month, day, hour, minute, second = match.groups()
            try:
                dt = datetime(int(year), int(month), int(day), int(hour), int(minute), int(second))
                return dt.isoformat()
            except ValueError:
                pass
        
        return None
