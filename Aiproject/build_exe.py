import PyInstaller.__main__
import os
import shutil

# Dapatkan path Tesseract dari sistem
tesseract_path = r'C:\Program Files\Tesseract-OCR'

# Buat direktori untuk file temporary
if not os.path.exists('temp_build'):
    os.makedirs('temp_build')

# Copy file Tesseract yang diperlukan ke direktori temporary
shutil.copytree(tesseract_path, 'temp_build/Tesseract-OCR')

PyInstaller.__main__.run([
    'main.py',
    '--onefile',
    '--noconsole',
    '--add-data', 'temp_build/Tesseract-OCR;Tesseract-OCR',
    '--add-data', 'button_claim_game_over.json;.',
    '--add-data', 'modules/coordinates.json;modules',
    '--hidden-import', 'PIL._tkinter_finder',
    '--name', 'GameBot',
    '--clean',
    '--noconfirm',
    '--uac-admin'
])

# Hapus direktori temporary
shutil.rmtree('temp_build') 