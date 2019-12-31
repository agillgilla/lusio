import requests 
import os
import urllib.request
import re

titles_folder = "titles"

try:
    # Create target Directory
    os.mkdir(titles_folder)
    print("Directory " , titles_folder ,  " created ")
except FileExistsError:
    print("Directory " , titles_folder ,  " already exists")

def get_imdb_img(title, camel_case=True):
    title_spaced = title
    if camel_case:
        title_spaced = re.sub("([a-z])([A-Z])","\g<1> \g<2>", title_spaced)
        title_spaced = re.sub(r"([0-9]+(\.[0-9]+)?)", r" \1 ", title_spaced).strip()

    output_filename = titles_folder + "/" + title_spaced + ".jpg"
    
    if os.path.exists(output_filename):
        print("Skipping " + output_filename)
        return True

    print("Searching for: " + title_spaced)

    search_url = "https://www.themoviedb.org/search"
    search_params = {'query':title_spaced, 'language':'en-US'}
      
    search_response = requests.get(url=search_url, params=search_params)

    try:
        title_url = search_response.content.split(b"class=\"result\" href=\"", 1)[1]
        title_url = title_url.split(b"?language")[0]
        title_url = "https://www.themoviedb.org" + title_url.decode() + "/"
    except IndexError:
        return False
    #print(title_url)


    title_params = {'language':'en-US'}

    title_response = requests.get(url=title_url, params=title_params)
    #print(title_response.content)

    try:
        title_img_src = title_response.content.split(b"<a class=\"no_click progressive replace\" href=\"", 1)[1]
        title_img_src = title_img_src.split(b"1x, ", 1)[1]
        title_img_src = title_img_src.split(b"2x", 1)[0]
        title_img_src = title_img_src.strip()
    except IndexError:
        return False
    
    img_src_url = title_img_src.decode()
    print(img_src_url)
    

    urllib.request.urlretrieve(img_src_url, output_filename)

    return True


directory = 'D:\VIDEOS\MOVIES'
failed_titles = []

for filename in os.listdir(directory):
    if filename.endswith(".mp4") or filename.endswith(".mkv"): 
        print(os.path.join(directory, filename))
        title = filename[:-4]
        
        print("Fetching " + title + "...")
        if get_imdb_img(title):
            print("Sucessfully fetched " + title)
        else:
            print("Failed to fetch " + title)
            failed_titles.append(title)

    elif os.path.isdir(os.path.join(directory, filename)):
        print(os.path.join(directory, filename))
        title = filename
        
        print("Fetching " + title + "...")
        if get_imdb_img(title, camel_case=False):
            print("Sucessfully fetched " + title)
        else:
            print("Failed to fetch " + title)
            failed_titles.append(title)

print("===============================================")
print("Failed titles:")
for failed_title in failed_titles:
    print(failed_title)
