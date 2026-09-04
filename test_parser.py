from src.parser import analyze_pasted_python

def test_parser_detects_imports():
    result = analyze_pasted_python("import json\n\ndef f():\n    return 1")
    assert "json" in result["dependencies"]
