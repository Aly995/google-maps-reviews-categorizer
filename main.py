# -*- coding: utf-8 -*-

import os
import glob
from threading import Thread

from export_data import MapDataExporter
from maps_data_scraper import GoogleMapsDataScraper


def split_list(lst, n):
    """Split a list into n roughly equal parts."""
    k, m = divmod(len(lst), n)
    return list((lst[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n)))


def scrape_maps(language, keywords, output_folder, results, thread_id):
    scraper = GoogleMapsDataScraper(language, output_folder)
    scraper.init_driver()
    places = []

    count = 1
    for kw in keywords:
        place = scraper.scrape_place(kw)

        if place is not None:
            print(f'Thread #{thread_id}  {count}/{len(keywords)} - OK - {kw}')
            places.append(place)
        else:
            print(f'Thread #{thread_id}  {count}/{len(keywords)} - ERROR - {kw}')
        count += 1

    results[thread_id] = places
    scraper.quit_driver()


def analyze_all_reviews(output_folder, csv_files=None):
    """
    Automatically analyze review CSV files.
    If csv_files is provided, only those specific files are analyzed.
    Otherwise, all review CSV files in the output folder are found.
    """
    try:
        from review_analyzer import ReviewAnalyzer

        if csv_files is None:
            csv_pattern = os.path.join(output_folder, '*_reviews.csv')
            csv_files = glob.glob(csv_pattern)

        if not csv_files:
            print('\n[INFO] No review CSV files found to analyze.')
            return

        print(f'\n{"=" * 70}')
        print('STARTING AUTOMATIC REVIEW ANALYSIS')
        print(f'{"=" * 70}')
        print(f'Found {len(csv_files)} review file(s) to analyze\n')

        try:
            analyzer = ReviewAnalyzer()
        except ValueError as e:
            print(f'[WARNING] Could not initialize analyzer: {e}')
            print('[INFO] Skipping automatic analysis. You can run it manually later with:')
            print(f'       python analyze_reviews.py <csv_file_path>')
            return

        for csv_file in csv_files:
            print(f'\n[INFO] Analyzing: {os.path.basename(csv_file)}')
            print('-' * 70)

            try:
                analyzer.analyze_reviews_from_csv(csv_file)
                print(f'[SUCCESS] Analysis complete for {os.path.basename(csv_file)}')
            except Exception as e:
                print(f'[ERROR] Failed to analyze {os.path.basename(csv_file)}: {e}')
                continue

        print(f'\n{"=" * 70}')
        print('AUTOMATIC REVIEW ANALYSIS COMPLETE')
        print(f'{"=" * 70}\n')

    except ImportError:
        print('\n[WARNING] Review analyzer not found. Skipping automatic analysis.')
        print('[INFO] To enable automatic analysis, ensure review_analyzer.py is in the same directory.')


def run_google_maps_scraper(language, keywords_file, output_folder, auto_analyze=True):
    with open(keywords_file, 'r', encoding='utf-8') as f:
        keywords = f.read().splitlines()

    num_threads = 4
    threads = [None] * num_threads
    results = [None] * num_threads
    keyword_chunks = split_list(keywords, num_threads)

    for i in range(num_threads):
        threads[i] = Thread(target=scrape_maps, args=(language, keyword_chunks[i], output_folder, results, i,))
        threads[i].start()

    for i in range(num_threads):
        threads[i].join()

    all_places = []
    for i in range(num_threads):
        all_places += results[i]

    exporter = MapDataExporter('00_output.xls', output_folder, all_places)
    exporter.export_excel()

    if auto_analyze:
        session_csv_files = [p.csv_path for p in all_places if hasattr(p, 'csv_path') and p.csv_path]
        analyze_all_reviews(output_folder, csv_files=session_csv_files)


if __name__ == "__main__":
    while True:
        language = input('----------\n[1] Enter the language (ES or EN): ')
        if language not in ('ES', 'EN'):
            print("----------\n** Error ** Invalid language. Please enter ES or EN\n")
            continue
        else:
            break

    while True:
        output_folder = input('----------\n[2] Enter the path to save the output files: ')
        if not os.path.isdir(output_folder):
            print("----------\n** Error ** That is not a valid folder. Please enter a valid folder\n")
            continue
        else:
            last_char = output_folder[-1]
            if last_char not in ('/', '\\'):
                output_folder = output_folder.replace('/', '\\') + '\\'
            break

    while True:
        keywords_file = input('----------\n[3] Enter the path to the keywords txt file: ')
        if not os.path.isfile(keywords_file):
            print("----------\n** Error ** That is not a valid file. Please enter a valid txt file\n")
            continue
        else:
            break

    while True:
        analyze_choice = input('----------\n[4] Automatically analyze reviews with AI? (Y/N): ').upper()
        if analyze_choice in ('Y', 'N'):
            auto_analyze = (analyze_choice == 'Y')
            break
        else:
            print("----------\n** Error ** Please enter Y or N\n")

    run_google_maps_scraper(language, keywords_file, output_folder, auto_analyze)
