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

base_url = 'https://www.shalexp.com/texas/fort-bend-county/companies'
companies_data = []

for page in range(1, 2):
    if page == 1:
        page_url = base_url
    else:
        page_url = f'{base_url}?page={page}'
    
    companies = get_companies_from_page(page_url)
    for company_index, (company_name, company_url) in enumerate(companies, start=1):
        summary = get_company_summary(company_url)
        summary['Company Name'] = company_name
        companies_data.append(summary)
        print(f"Processed company #{company_index} out of {len(companies)}: {company_name}")

for company_data in companies_data:
    if 'Operating States' in company_data and 'Operating State' in company_data:
        company_data['Operating State(s)'] = ', '.join(
            filter(None, [company_data.get('Operating States'), company_data.get('Operating State')])
        )
        del company_data['Operating States']
        del company_data['Operating State']

df = pd.DataFrame(companies_data)

cols = df.columns.tolist()
cols = ['Company Name'] + [col for col in cols if col != 'Company Name']
df = df[cols]

df.to_csv('companies_summary.csv', index=False)
print(f"Saved {len(companies_data)} companies to companies_summary.csv")
