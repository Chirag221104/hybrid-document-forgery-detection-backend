# docx_analyzer.py
from docx import Document
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime
import os
import mimetypes

class DOCXAnalyzer:
    async def extract_metadata(self, file_path: str):
        """Extract real metadata from DOCX file"""
        try:
            return await self._extract_with_docx(file_path)
        except Exception as e:
            print(f"DOCX extraction failed: {e}")
            return await self._get_basic_info(file_path)
    
    async def _extract_with_docx(self, file_path: str):
        """Extract metadata using python-docx"""
        doc = Document(file_path)
        core_props = doc.core_properties

        mime, _ = mimetypes.guess_type(file_path)
        metadata = {
            "type": mime or "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "author": core_props.author or "Not specified",
            "title": core_props.title or "Not specified",
            "subject": core_props.subject or "Not specified",
            "creator": core_props.author or "Not specified",
            "keywords": core_props.keywords or "Not specified",
            "lastModifiedBy": getattr(core_props, "last_modified_by", None) or "Not specified",
            "createdDate": core_props.created.isoformat() if core_props.created else None,
            "modifiedDate": core_props.modified.isoformat() if core_props.modified else None,
        }

        # Rough page estimate
        paragraph_count = len(doc.paragraphs)
        estimated_pages = max(1, paragraph_count // 25)
        metadata["pageCount"] = estimated_pages

        return metadata
    
    async def _get_basic_info(self, file_path: str):
        """Get basic file information when metadata extraction fails"""
        stat = os.stat(file_path)
        mime, _ = mimetypes.guess_type(file_path)
        return {
            "type": mime or "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "author": "Could not extract",
            "title": "Could not extract",
            "pageCount": "Unknown",
            "createdDate": None,
            "modifiedDate": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "lastModifiedBy": "Unknown",
        }
