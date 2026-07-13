import os
import re
import glob

reports_dir = os.path.join(os.path.dirname(__file__), "reports")
if not os.path.exists(reports_dir):
    print("Reports dir not found")
    exit()

files = os.listdir(reports_dir)
for f in files:
    # Match xxx_<10-digit-timestamp>.ext
    match = re.match(r'^(.*?)_(\d{10})(.*)$', f)
    if match:
        base_name = match.group(1)
        ext = match.group(3)
        
        # If it's a timestamp
        new_name = f"{base_name}{ext}"
        old_path = os.path.join(reports_dir, f)
        
        # Handle duplicates during renaming
        new_path = os.path.join(reports_dir, new_name)
        counter = 1
        while os.path.exists(new_path) and new_path != old_path:
            name_without_ext = new_name.rsplit('.', 1)[0]
            if name_without_ext.endswith('_eval'):
                # special handling for eval files if base conflicts
                base = base_name.replace('_eval', '')
                new_path = os.path.join(reports_dir, f"{base}_{counter}_eval.md")
            else:
                new_path = os.path.join(reports_dir, f"{base_name}_{counter}{ext}")
            counter += 1
            
        os.rename(old_path, new_path)
        print(f"Renamed {f} -> {os.path.basename(new_path)}")
