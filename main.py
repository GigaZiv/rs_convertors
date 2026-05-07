import asyncio
from datetime import  datetime

import xml_gar, db
from xml_prog import parseXmlMy, downloadD
from zip_var_fias import extract_fias_contents

if __name__ == '__main__':
    #parseXmlMy("report-457d4979-2776-4439-8e52-a1fd71bcd207-OfSite-2025-12-02-159910-45-01[0].xml")

    #extract_fias_contents('F:\\Fias\\gar_xml.zip')

    asyncio.run(xml_gar.import_fias(clean_start=True))
