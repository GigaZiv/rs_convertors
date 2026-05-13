from pprint import pprint


from xml_prog import process_file

if __name__ == '__main__':
    pprint(process_file("F:\\Fias\\report-60baa8df-2923-4a2e-8ed7-38ce26b6affb-OfSite-2025-12-02-767077-45-01[0].xml"))
    #pprint(process_file("F:\\Fias\\report-66afd373-138d-4050-a345-8326cb251a79-OfSite-2025-12-03-662322-45-01[0].xml"))

    #extract_fias_contents('F:\\Fias\\gar_xml.zip')

    #asyncio.run(xml_gar.import_fias(clean_start=True))
