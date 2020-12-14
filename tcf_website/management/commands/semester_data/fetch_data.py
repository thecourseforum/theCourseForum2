import requests

"""
This script downloads data from Lou's List and converts it into
a usable CSV file. However, in its current state we have to
manually hardcode the year/season of the semester(s) we want to
download.

Potential todo: create a cron job that runs this script and
`load_semester` every now and then so we don't have to do this.
"""


def download_semester(year, season):
    # local_filename = url.split('/')[-1]
    # NOTE the stream=True parameter below

    season_numbers = {
        'fall': 8,
        'summer': 6,
        'spring': 2,
        'january': 1
    }

    year_code = str(year)[-2:]  # 2019 -> '19'

    semester_code = f"1{year_code}{season_numbers[season]}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36',
        'origin': 'https://louslist.org',
        'referer': f'https://louslist.org/requestData.php?Semester={semester_code}&Type=Group&Group=CS'}

    try:

        with requests.post('https://louslist.org/deliverData.php', data={
            'Group': 'CS',
            'Semester': semester_code,
            'Description': 'Yes',
            'Extended': 'Yes',
        }, stream=True, headers=headers) as r:
            r.raise_for_status()
            with open(f'csv/{year}_{season}.csv', 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:  # filter out keep-alive new chunks
                        f.write(chunk)
                        # f.flush()
        # return local_filename
    except Exception as e:
        print(e)


# if __name__ == '__main__':

#     for year in range(2009, 2020 + 1):
#         for season in ['january', 'spring', 'summer', 'fall']:
#             download_semester(year, season)

print('hi')
download_semester(2020, 'fall')
download_semester(2021, 'january')
download_semester(2021, 'spring')
print('bye')
