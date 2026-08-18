import os
import zipfile

def zip_project():
    project_dir = os.path.dirname(os.path.abspath(__file__))
    output_zip_path = os.path.join(project_dir, 'solariq_ai_power_system.zip')
    
    print(f"[+] Creating ZIP archive at: {output_zip_path}")
    
    # Also save a copy in parent scratch directory for easy access
    parent_scratch_zip = os.path.join(os.path.dirname(project_dir), 'solariq_ai_power_system.zip')
    
    zip_targets = [output_zip_path, parent_scratch_zip]
    
    for zip_path in zip_targets:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(project_dir):
                # Skip __pycache__ and venv directories
                if '__pycache__' in root or 'venv' in root or '.git' in root:
                    continue
                for file in files:
                    if file.endswith('.zip'):
                        continue # Don't nest zip inside zip
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, project_dir)
                    zipf.write(file_path, arcname)
                    
        print(f"[SUCCESS] Zip file written: {zip_path} ({os.path.getsize(zip_path)} bytes)")

if __name__ == '__main__':
    zip_project()
