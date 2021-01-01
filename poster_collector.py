import requests 
import os
import urllib.request
import re
 
import PIL
from PIL import Image

posters_dir = 'posters'

api_key = 'bf41c278b93f331151c6d37080b8b284'
api_v4_key = 'eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJiZjQxYzI3OGI5M2YzMzExNTFjNmQzNzA4MGI4YjI4NCIsInN1YiI6IjVlODRkNWFkZGExMGYwMDAxNmVjYjcxMCIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.d71jrPRyr7WFONDP5djWHjbvo10iV01kgcSFnLINcAI'

# Create output directory if necessary
try:
    os.mkdir(posters_dir)
    print(f"Directory \"{posters_dir}\" created ")
except FileExistsError:
    print(f"Directory \"{posters_dir}\" already exists")
print()

def get_imdb_img(title, output_filename):
    print("\tSearching for: " + title)

    response = requests.get(f"https://api.themoviedb.org/3/search/movie?api_key={api_key}", params = {'query':title})
    response_json_results = response.json()['results']

    if (len(response_json_results) == 0) or ('poster_path' not in response_json_results[0]):
        print(f"\tCouldn't find {title}")
        return False

    poster_path = response_json_results[0]['poster_path']

    if poster_path is None:
        print(f"\tCouldn't find {title}")
        return False

    #w500_base_url = 'https://image.tmdb.org/t/p/w500'
    original_base_url = 'https://image.tmdb.org/t/p/original'

    urllib.request.urlretrieve(original_base_url + poster_path, output_filename)

    img = Image.open(output_filename)
    img = img.resize((600, 900), PIL.Image.ANTIALIAS)
    img.save(output_filename)

    return True


directory = 'D:\MOVIES'
fetched_titles = []
skipped_titles = []
failed_titles = []

for filename in os.listdir(directory):
    if filename.endswith(".mp4") or filename.endswith(".mkv"): 
        #print(os.path.join(directory, filename))
        title = filename[:-4]
        output_filename = posters_dir + "/" + title + ".jpg"
        
        if os.path.exists(output_filename):
            skipped_titles.append(title)
            #print("\tSkipping " + output_filename)
            continue

        print("Fetching " + title + "...")
        if get_imdb_img(title, output_filename):
            fetched_titles.append(title)
            print("...Successfully fetched " + title)
        else:
            print("...Failed to fetch " + title)
            failed_titles.append(title)

    elif os.path.isdir(os.path.join(directory, filename)):
        #print(os.path.join(directory, filename))
        title = filename
        output_filename = posters_dir + "/" + title + ".jpg"

        if os.path.exists(output_filename):
            skipped_titles.append(title)
            #print("\tSkipping " + output_filename)
            continue
        
        print("Fetching " + title + "...")
        if get_imdb_img(title, output_filename):
            fetched_titles.append(title)
            print("Sucessfully fetched " + title)
        else:
            print("Failed to fetch " + title)
            failed_titles.append(title)

print()
print("===============================================")
print()
print("Fetched {} new posters.".format(len(fetched_titles)))
print("Skipped {} existing posters.".format(len(skipped_titles)))
print("Failed on {} posters.".format(len(failed_titles)))

if len(fetched_titles) > 0:
    print()
    print("Successful titles:")
    for fetched_title in fetched_titles:
        print(fetched_title)
if len(failed_titles) > 0:
    print()
    print("Failed titles:")
    for failed_title in failed_titles:
        print(failed_title)


