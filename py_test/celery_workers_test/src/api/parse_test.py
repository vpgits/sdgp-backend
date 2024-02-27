import pytest
from celery_workers.src.api.parse import parse_pages

def test_parse_pages_success(mocker):
    # Mocking the necessary dependencies
    supabase_client_mock = mocker.Mock()
    download_file_mock = mocker.patch('api.parse.download_file')
    file_type_mock = mocker.patch('api.parse.file_type')
    add_pages_to_supabase_mock = mocker.patch('api.parse.add_pages_to_supabase')

    # Calling the function under test
    parse_pages('GitCheatSheet.pdf', supabase_client_mock, 'document_id')

    # Asserting the function calls
    download_file_mock.assert_called_once_with(supabase_client_mock, 'GitCheatSheet.pdf', 'document_id')
    file_type_mock.assert_called_once_with('GitCheatSheet.pdf')
    add_pages_to_supabase_mock.assert_called_once_with(supabase_client_mock, file_type_mock.return_value, 'document_id')

def test_parse_pages_file_not_found(mocker, caplog):
    # Mocking the necessary dependencies
    supabase_client_mock = mocker.Mock()
    download_file_mock = mocker.patch('api.parse.download_file')
    download_file_mock.side_effect = FileNotFoundError

    # Calling the function under test
    parse_pages('/path/to/nonexistent_file.pdf', supabase_client_mock, 'document_id')

    # Asserting the error message
    assert "File not found" in caplog.text

def test_parse_pages_exception(mocker, caplog):
    # Mocking the necessary dependencies
    supabase_client_mock = mocker.Mock()
    download_file_mock = mocker.patch('api.parse.download_file')
    download_file_mock.side_effect = Exception("Some error")

    # Calling the function under test
    with pytest.raises(Exception, match="Some error"):
        parse_pages('/path/to/filent_mock', 'document_id')

    # Asserting the error message
    assert "Some error" in caplog.text