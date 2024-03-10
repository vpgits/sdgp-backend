import pytest
from celery_workers.src.api.parse import read_pdf
from celery_workers.src.api.parse import read_docx
from celery_workers.src.api.parse import read_pptx

def test_read_pdf():
    result = read_pdf('../tests/api_test/test.pdf')
    print(result)
    assert [' hi this a Pytest for PDF document to text! '] == result

def test_read_pdf_fail():
    with pytest.raises(Exception):
        read_pdf('../tests/api_test/test.txt')

def test_read_docx():
    result = read_docx('../tests/api_test/test.docx')
    print(result)
    assert['Hi, this is a Pytest for DOCX document to text!', '', '']== result

def test_read_docx_fail():
    with pytest.raises(Exception):
        read_docx('../tests/api_test/test.txt')

def test_read_pptx():
    result = read_pptx('../tests/api_test/test.pptx')
    print(result)
    assert['hi this a Pytest for PPTX document to text!', '']==result

def test_read_pptx_fail():
    with pytest.raises(Exception):
        read_pptx('../tests/api_test/test.txt')
        