# -*- coding: utf-8 -*-

import xlwt


class MapDataExporter:
    """Exports scraped Google Maps data to an Excel file."""

    def __init__(self, filename, path, places_list):
        self.filename = filename
        self.path = path
        self.places_list = places_list

    def export_excel(self):
        workbook = xlwt.Workbook(encoding='utf-8')
        sheet = workbook.add_sheet("document", cell_overwrite_ok=True)

        sheet.write(0, 0, 'KEYWORD')
        sheet.write(0, 1, 'NAME')
        sheet.write(0, 2, 'CATEGORY')
        sheet.write(0, 3, 'ADDRESS')
        sheet.write(0, 4, 'PHONE')
        sheet.write(0, 5, 'WEB')
        sheet.write(0, 6, 'PLUS CODE')
        sheet.write(0, 7, 'OPEN HOURS')
        sheet.write(0, 8, 'STARS')
        sheet.write(0, 9, 'REVIEWS')

        row = 1
        for place in self.places_list:
            sheet.write(row, 0, place.keyword)
            sheet.write(row, 1, place.name)
            sheet.write(row, 2, place.category)
            sheet.write(row, 3, place.address)
            sheet.write(row, 4, place.phone)
            sheet.write(row, 5, place.web)
            sheet.write(row, 6, place.pluscode)
            sheet.write(row, 7, place.hours)
            sheet.write(row, 8, place.stars)
            sheet.write(row, 9, place.reviews)
            row += 1

        workbook.save(self.path + self.filename)
