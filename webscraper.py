import requests
from bs4 import BeautifulSoup
import pandas as pd

def get_company_summary(company_url):
    response = requests.get(company_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    summary_data = {}
    summary_section = soup.find('div', class_='col-md-4')
    
    if summary_section:
        table = summary_section.find('table', class_='table')
        if table:
            rows = table.find_all('tr')
            for row in rows:
                th = row.find('th')
                td = row.find('td')
                if th and td:
                    key = th.text.strip()
                    value = ' '.join(td.stripped_strings)
                    if key.lower() in ['operating state', 'operating states']:
                        key = 'Operating State(s)'
                        if key in summary_data:
                            summary_data[key] += ', ' + value
                        else:
                            summary_data[key] = value
                    else:
                        summary_data[key] = value

    # Extract contact information
    contact_section = soup.find('div', class_='card card-block')
    if contact_section:
        contact_table = contact_section.find('table', class_='table-grey-head')
        if contact_table:
            rows = contact_table.find('tbody').find_all('tr')
            for i, row in enumerate(rows, start=1):
                tds = row.find_all('td')
                if len(tds) == 2:
                    address = tds[0].text.strip()
                    phone = tds[1].text.strip()
                    summary_data[f'Address {i}'] = address
                    summary_data[f'Phone {i}'] = phone

    return summary_data

def get_companies_from_page(page_url):
    response = requests.get(page_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    companies = []
    table_rows = soup.find_all('tr')
    for row in table_rows:
        columns = row.find_all('td')
        if len(columns) > 1:
            link = columns[1].find('a')
            if link:
                company_name = link.text.strip()
                company_url = link['href']
                companies.append((company_name, company_url))
    
    return companies

county = input("What County do you want to scan? Do not include the word 'County'. (e.g. Harris, Fort Bend, Wharton, etc.)\n")
county = county.lower().replace(' ', '-')
base_url = f'https://www.shalexp.com/texas/{county}-county/companies'
companies_data = []

print("How many pages do you want to scan? Will only scan the first x pages, where x is your input")
pagerange = int(input())

totCompanies = 0
for page in range(1, pagerange+1):
    if page == 1:
        page_url = base_url
    else:
        page_url = f'{base_url}?page={page}'
    
    companies = get_companies_from_page(page_url)
    totCompanies += len(companies)
    
x = 1
company_names_set = set()
for page in range(1, pagerange+1):
    if page == 1:
        page_url = base_url
    else:
        page_url = f'{base_url}?page={page}'
    
    companies = get_companies_from_page(page_url)
    for company_index, (company_name, company_url) in enumerate(companies, start=1):
        if company_name in company_names_set:
            print(f"Skipping duplicate company: {company_name}")
        else:
            company_names_set.add(company_name)
            summary = get_company_summary(company_url)
            summary['Company Name'] = company_name
            companies_data.append(summary)
            print(f"Processed company rank #{x}/{totCompanies}, {company_name}")
            x += 1

# Combine 'Operating States' and 'Operating State' into 'Operating State(s)'
for company_data in companies_data:
    if 'Operating States' in company_data and 'Operating State' in company_data:
        company_data['Operating State(s)'] = ', '.join(
            filter(None, [company_data.get('Operating States'), company_data.get('Operating State')])
        )
        del company_data['Operating States']
        del company_data['Operating State']

df = pd.DataFrame(companies_data)

# Ensure 'Company Name' is the first column and 'Operating State(s)' is the second column
cols = df.columns.tolist()
cols = ['Company Name', 'Operating State(s)'] + [col for col in cols if col not in ['Company Name', 'Operating State(s)']]

# Rearrange to put estimated daily production columns before Address 1
production_columns = ['Estimated Daily Oil Prod.', 'Estimated Daily Gas Prod.', 'Estimated Daily Water Prod.']
address_columns = [col for col in cols if 'Address' in col or 'Phone' in col]
other_columns = [col for col in cols if col not in production_columns + address_columns]

# Reorder columns
columns_order = ['Company Name', 'Operating State(s)']
columns_order.extend(production_columns)
columns_order.extend(other_columns)
columns_order.extend(address_columns)
df = df[columns_order]

try:
    df.to_csv(f'companies_summary_{county.replace("-", "_")}_county.csv', index=False)
    print(f"Saved {len(companies_data)} companies to companies_summary_{county}.csv")
except PermissionError:
    for i in range (1,4):
        print("!!!Cannot output data as the file is being used by another application!!!")
    print("Please close any running instance of the spreadsheet and re-run the code.")
