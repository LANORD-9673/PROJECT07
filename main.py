from pathlib import Path
exec(compile((Path(__file__).parent/'streamlit_app.py').read_text(encoding='utf-8'),str(Path(__file__).parent/'streamlit_app.py'),'exec'))
