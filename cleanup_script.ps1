# Git filter-branch script to remove exposed API key
if (Test-Path 'tests/test_ceo_agent_tools.py') {
    (Get-Content 'tests/test_ceo_agent_tools.py') -replace 'AIzaSyCWqhIIWHj8i5qDbo-Y3L1-jszF4-9O97M', 'YOUR_API_KEY_HERE' | Set-Content 'tests/test_ceo_agent_tools.py'
}