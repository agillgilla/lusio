import os
import re

def rename_file(filepath):
    title_spaced = os.path.basename(filepath[:-4])
    file_ext = filepath[-4:]
    
    title_spaced = re.sub("([a-z])([A-Z])","\g<1> \g<2>", title_spaced)
    title_spaced = re.sub(r"([0-9]+(\.[0-9]+)?)", r" \1 ", title_spaced).strip()

    output_filename = os.path.join(os.path.dirname(filepath), title_spaced) + file_ext
    
    if os.path.exists(output_filename):
        print("Skipping " + output_filename)
    else:
        print("Renaming " + filepath + " to " + output_filename)
        os.rename(filepath, output_filename) 

    return True


directory = 'D:\VIDEOS\MOVIES'
failed_files = []

for filename in os.listdir(directory):
    if filename.endswith(".mp4") or filename.endswith(".mkv"): 
        print(os.path.join(directory, filename))

        filepath = os.path.join(directory, filename)
        
        if rename_file(filepath):
            print("Sucessfully renamed " + filepath)
        else:
            print("Failed to rename " + filepath)
            failed_files.append(title)

print("===============================================")
print("Failed files:")
for failed_file in failed_files:
    print(failed_file)
