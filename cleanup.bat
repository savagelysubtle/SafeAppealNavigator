@echo off
if exist "tests\test_ceo_agent_tools.py" (
    powershell -Command "(Get-Content 'tests\test_ceo_agent_tools.py') -replace 'AIzaSyCWqhIIWHj8i5qDbo-Y3L1-jszF4-9O97M', 'YOUR_API_KEY_HERE' | Set-Content 'tests\test_ceo_agent_tools.py'"
)