import py_compile
import sys

files_to_check = [
    'src/agents/Pain_point_humanizer.py',
    'src/agents/Reddit_scraper.py',
    'src/agents/Pain_point_extractor.py'
]

for file in files_to_check:
    try:
        py_compile.compile(file, doraise=True)
        print(f"✅ {file} - OK")
    except py_compile.PyCompileError as e:
        print(f"❌ {file}")
        print(e)
