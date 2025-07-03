import os
import json
import requests
import xmlrpc.client
from datetime import datetime
from dotenv import load_dotenv

def get_company_data(ehra_id):
  url = f"https://www.zefix.ch/ZefixREST/api/v1/firm/{ehra_id}/withoutShabPub.json"
  response = requests.request("GET", url)

  if response.status_code != 200:
    raise requests.exceptions.HTTPError(f"Expected 200, got {response.status_code}")

  return json.loads(response.text)

def get_contact_data(company_data, creation_date):
    contact_data =  {
        "name": company_data.get("name"),
        "is_company": True,
        "x_ehra_id": company_data.get("ehraid"),
        "x_uid": company_data.get("uidFormatted"),
        "x_ch_id": company_data.get("chidFormatted"),
        "x_purpose": company_data.get("purpose"),
        "x_company_creation_date": datetime.strptime(creation_date, "%d.%m.%Y").strftime("%Y-%m-%d"),
        "street": f"{company_data.get("address").get("street")} {company_data.get("address").get("houseNumber")}",
        "zip": company_data.get("address").get("swissZipCode"),
        "city": company_data.get("address").get("town"),
        "state_id": 1428,
        "country_id": 43,
        "category_id": [1]
    }

    if company_data.get("address").get("careOf") != "":
        contact_data["x_company_contact"] = company_data.get("address").get("careOf").removeprefix("c/o ")
    else:
        url = f"https://www.zefix.ch/ZefixREST/api/v1/firm/{company_data.get("ehraid")}/shabPub.json"
        response = requests.request("GET", url)

        if response.status_code != 200:
            raise requests.exceptions.HTTPError(f"Expected 200, got {response.status_code}")
        response = json.loads(response.text)
        message = None
        for single_response in response:
            mutation_type_list = single_response.get("mutationTypes")
            for single_mutation_type in mutation_type_list:
                if single_mutation_type.get("key") == "status.neu":
                    message = single_response.get("message")
                    break
        if message:
            name_list = message.split("Eingetragene Personen: ")[1]
            contact_data["x_company_contact"] = f"{name_list.split(", ")[1]} {name_list.split(", ")[0]}"
    return contact_data

def import_contact_to_odoo(contact_data):
    url = os.getenv('URL')
    db = os.getenv('DB')
    username = os.getenv('USERNAME')
    password = os.getenv('PASSWORD')

    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
    uid = common.authenticate(db, username, password, {})
    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")

    contact_id = models.execute_kw(db, uid, password, "res.partner", "create", [contact_data])
    return contact_id

def create_odoo_record(ehra_id, creation_date):
    company_data = get_company_data(ehra_id)
    contact_data = get_contact_data(company_data, creation_date)
    contact_id = import_contact_to_odoo(contact_data)

    print(company_data)
    print(contact_data)
    print(f"Contact ID: {contact_id}")

if __name__ == "__main__":
    load_dotenv()
    create_odoo_record("1692349", "12.05.2025")
