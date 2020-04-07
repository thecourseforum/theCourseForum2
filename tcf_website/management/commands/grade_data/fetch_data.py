import requests
import os


def download_grade_data(
        course=None,
        path='tcf_website/management/commands/grade_data/json'):
    # local_filename = url.split('/')[-1]
    # NOTE the stream=True parameter below
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36',
        'origin': 'https://vagrades.com',
        'referer': f"https://vagrades.com/uva{'/' + course if course else ''}"}

    if not course:
        url = 'https://vagrades.com/api/uvaclasses'
        course = 'all_classes'
    else:
        url = f'https://vagrades.com/api/uvaclass/{course}'
    fname = f"{course}.json"
    try:
        with requests.get(url, stream=True, headers=headers) as r:
            r.raise_for_status()
            with open(os.path.join(path, fname), 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:  # filter out keep-alive new chunks
                        f.write(chunk)
                        # f.flush()
        # return local_filename
    except Exception as e:
        print(e)


if __name__ == '__main__':

    for year in range(2009, 2020 + 1):
        for season in ['january', 'spring', 'summer', 'fall']:
            download_semester(year, season)
