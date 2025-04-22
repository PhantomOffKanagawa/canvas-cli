import unittest
from unittest.mock import patch, MagicMock, mock_open
from io import BytesIO
import sys
import os
from pathlib import Path
from canvas_cli.command_clone import _convert_to_markdown

"""
Tests for the command_clone module's _convert_to_markdown function
"""



class ConvertToMarkdownTests(unittest.TestCase):
    """Tests for the _convert_to_markdown function in command_clone module"""

    def setUp(self):
        """Set up test environment"""
        self.html_content = {
            'html': {
                'description': '<p>This is a test description</p>',
                'page1': '<p>This is page 1 content</p>'
            },
            'fetched': set(['https://example.com/test'])
        }
        self.pdfs = ['test.pdf']
        self.docs = ['document.docx']
        self.params = {
            'convert_to_markdown': True,
            'integrate_together': False
        }

    @patch('markitdown.MarkItDown')
    def test_convert_to_markdown_basic(self, mock_markitdown_class):
        """Test basic markdown conversion functionality"""
        # Setup mock
        mock_markitdown = mock_markitdown_class.return_value
        mock_result_description = MagicMock()
        mock_result_description.text_content = "This is a test description"
        mock_result_page = MagicMock()
        mock_result_page.text_content = "This is page 1 content"
        
        mock_markitdown.convert_stream.side_effect = [mock_result_description, mock_result_page]
        
        # Call function
        result = _convert_to_markdown(self.html_content, [], [], self.params)
        
        # Assertions
        self.assertEqual(result["readme"], "This is a test description")
        self.assertEqual(result["markdown"]["page1"], "#page1\nThis is page 1 content")
        self.assertEqual(mock_markitdown_class.call_count, 1)
        self.assertEqual(mock_markitdown.convert_stream.call_count, 2)

    def test_convert_to_markdown_disabled(self):
        """Test when markdown conversion is disabled"""
        self.params['convert_to_markdown'] = False
        result = _convert_to_markdown(self.html_content, [], [], self.params)
        
        # Should just return the description HTML without conversion
        self.assertEqual(result, {"readme": self.html_content['html']['description']})

    @patch('markitdown.MarkItDown')
    def test_convert_to_markdown_with_integration(self, mock_markitdown_class):
        """Test markdown conversion with content integration"""
        # Setup mock
        mock_markitdown = mock_markitdown_class.return_value
        mock_result_description = MagicMock()
        mock_result_description.text_content = "This is a test description"
        mock_result_page = MagicMock()
        mock_result_page.text_content = "This is page 1 content"
        
        mock_markitdown.convert_stream.side_effect = [mock_result_description, mock_result_page]
        
        # Enable integration
        self.params['integrate_together'] = True
        
        # Call function
        result = _convert_to_markdown(self.html_content, [], [], self.params)
        
        # Assertions
        expected_readme = "This is a test description\n\n# page1\n#page1\nThis is page 1 content"
        self.assertEqual(result["readme"], expected_readme)
        self.assertEqual(result.get("markdown", {}), {})  # Should be empty with integration

    @patch('markitdown.MarkItDown')
    def test_convert_to_markdown_with_pdfs(self, mock_markitdown_class):
        """Test markdown conversion with PDF files"""
        # Setup mocks
        mock_markitdown = mock_markitdown_class.return_value
        mock_result_description = MagicMock()
        mock_result_description.text_content = "This is a test description"
        mock_result_page = MagicMock()
        mock_result_page.text_content = "This is page 1 content"
        mock_result_pdf = MagicMock()
        mock_result_pdf.text_content = "This is PDF content"
        
        mock_markitdown.convert_stream.side_effect = [mock_result_description, mock_result_page]
        mock_markitdown.convert.return_value = mock_result_pdf
        
        # Call function
        result = _convert_to_markdown(self.html_content, self.pdfs, [], self.params)
        
        # Assertions
        self.assertEqual(result["readme"], "This is a test description")
        self.assertEqual(result["markdown"]["page1"], "#page1\nThis is page 1 content")
        self.assertEqual(result["markdown"]["test.pdf"], "#test.pdf\nThis is PDF content")
        mock_markitdown.convert.assert_called_once()

    @patch('markitdown.MarkItDown')
    def test_convert_to_markdown_with_docx(self, mock_markitdown_class):
        """Test markdown conversion with DOCX files"""
        # Setup mocks
        mock_markitdown = mock_markitdown_class.return_value
        mock_result_description = MagicMock()
        mock_result_description.text_content = "This is a test description"
        mock_result_page = MagicMock()
        mock_result_page.text_content = "This is page 1 content"
        mock_result_doc = MagicMock()
        mock_result_doc.text_content = "This is DOCX content"
        
        mock_markitdown.convert_stream.side_effect = [mock_result_description, mock_result_page]
        mock_markitdown.convert.return_value = mock_result_doc
        
        # Call function
        result = _convert_to_markdown(self.html_content, [], self.docs, self.params)
        
        # Assertions
        self.assertEqual(result["readme"], "This is a test description")
        self.assertEqual(result["markdown"]["document.docx"], "#document.docx\nThis is DOCX content")

    @patch('markitdown.MarkItDown')
    def test_convert_to_markdown_with_all_file_types(self, mock_markitdown_class):
        """Test markdown conversion with PDF and DOCX files"""
        # Setup mocks
        mock_markitdown = mock_markitdown_class.return_value
        mock_result_description = MagicMock()
        mock_result_description.text_content = "This is a test description"
        mock_result_page = MagicMock()
        mock_result_page.text_content = "This is page 1 content"
        mock_result_pdf = MagicMock()
        mock_result_pdf.text_content = "This is PDF content"
        mock_result_doc = MagicMock()
        mock_result_doc.text_content = "This is DOCX content"
        
        mock_markitdown.convert_stream.side_effect = [mock_result_description, mock_result_page]
        mock_markitdown.convert.side_effect = [mock_result_pdf, mock_result_doc]
        
        # Call function
        result = _convert_to_markdown(self.html_content, self.pdfs, self.docs, self.params)
        
        # Assertions
        self.assertEqual(result["readme"], "This is a test description")
        self.assertEqual(result["markdown"]["page1"], "#page1\nThis is page 1 content")
        self.assertEqual(result["markdown"]["test.pdf"], "#test.pdf\nThis is PDF content")
        self.assertEqual(result["markdown"]["document.docx"], "#document.docx\nThis is DOCX content")

    @patch('builtins.print')
    def test_convert_to_markdown_import_error(self, mock_print):
        """Test handling of ImportError when markitdown is not installed"""
        with patch('markitdown.MarkItDown', side_effect=ImportError("No module named 'markitdown'")):
            result = _convert_to_markdown(self.html_content, [], [], self.params)
            
            # Should return the original content
            self.assertEqual(result, {"readme": self.html_content['html']['description']})
            mock_print.assert_called_once()
            
    @patch('markitdown.MarkItDown')
    def test_convert_to_markdown_skips_non_matching_files(self, mock_markitdown_class):
        """Test that non-matching file types are skipped"""
        # Setup mocks
        mock_markitdown = mock_markitdown_class.return_value
        mock_result_description = MagicMock()
        mock_result_description.text_content = "This is a test description"
        mock_result_page = MagicMock()
        mock_result_page.text_content = "This is page 1 content"
        
        mock_markitdown.convert_stream.side_effect = [mock_result_description, mock_result_page]
        
        # Include non-PDF file in PDFs list
        pdfs_with_invalid = ['test.pdf', 'not-a-pdf.txt']
        
        # Call function
        result = _convert_to_markdown(self.html_content, pdfs_with_invalid, [], self.params)
        
        # The convert method should only be called once for the valid PDF
        self.assertEqual(mock_markitdown.convert.call_count, 1)
        

if __name__ == '__main__':
    unittest.main()