import csv


def csv_eee():

    with open("output.csv", "w", newline="") as f:
        csv_writer = csv.writer(f)
        csv_writer.writerow(
            ["common_data_cad_number", "common_data_code", "common_data_value", "category_code", "category_value", "permitted_use_by_document", "address_fias_okato"]
        )
        csv_writer.writerow(["", ""])