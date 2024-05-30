import json
import requests
from talabna_management import talabna_ninja
from bs4 import BeautifulSoup


cookie = 'AWSALB=suLC45NN1bpWBaPCI7ZHb0hb8Dqm6oLh6dPJksuqSOl8BiTHlPIYi8bXVoj9CryN7VQrp1QvnblE/zHn1+mhg4OdLyu5fVu4lK0lYm3RvJ328WNOab6wChMB7XRf; AWSALBCORS=suLC45NN1bpWBaPCI7ZHb0hb8Dqm6oLh6dPJksuqSOl8BiTHlPIYi8bXVoj9CryN7VQrp1QvnblE/zHn1+mhg4OdLyu5fVu4lK0lYm3RvJ328WNOab6wChMB7XRf; AWSALBTG=5CEvaig7cWXf1tu5t34oHk7t9nS7SoL1R4JV60d2mckIWoFgZ0YRVNIdreYoYC5kBENbHjJOGFeJiyyoBGZ0asMJDlV6il/CrTTD7OocxEYF65a823NvEdpSA9qwRC9QmClqNqIUmu6j73DttplSs4MTOuCj9U6tYqU1Fr1J3TQ3YnBn3E8=; AWSALBTGCORS=5CEvaig7cWXf1tu5t34oHk7t9nS7SoL1R4JV60d2mckIWoFgZ0YRVNIdreYoYC5kBENbHjJOGFeJiyyoBGZ0asMJDlV6il/CrTTD7OocxEYF65a823NvEdpSA9qwRC9QmClqNqIUmu6j73DttplSs4MTOuCj9U6tYqU1Fr1J3TQ3YnBn3E8=; XSRF-TOKEN=eyJpdiI6InhyaUZ3NktPWG8vdWdwWlJndDhiTmc9PSIsInZhbHVlIjoiSzdvSFArMGU1Lzg4Z1pYN3FXaVhUS3kxeVlpWmdtZkt5Z05meFR5RVR0WFpGOWoyc0t1M0JtWTJ0NmoyVURGcUJwLzlhQVBQM1M4Z1VzVWh0NHJRREM4aitWQURHU1Jkcll5RDBvYjZzTE9acUpGdFovUXNmY2tuRVR2MmxEeTgiLCJtYWMiOiJmNTRjNmE0ZTQ4ZmY4MTVlMjQ0ZDVlNDE5OWEyZDZiMDBkMmQ5NTg1YjAxYjc4ZmNlZDc2YjIxZjk0YWQ1Y2EzIiwidGFnIjoiIn0%3D; talabna_session=eyJpdiI6IldZdHFIaDZwcjdGODJFTldTbTd5MFE9PSIsInZhbHVlIjoiTjY1S2loZ2Uxb3B6V0pzVTJkMzE5TzkwdGVBaVJWdWtORVdURjFzbDZjcGd3RTVCcmVsRDdJZE5IVGY4ZmFjdWlCNWtIRFN3WFh2c25Mb3loTU1JMjNBOXdpZTl4U1MyL0hyaDN6MDF6alIvWUZ3MGYwQ3JTcndhWldJZDNjVUEiLCJtYWMiOiI3MzIyNDZiOGE3MTczZjMwNmU4NjBjYzYyNjI2ZjgxNzk0Zjk5MzZiMTQyZWMzZmFiOTk1MmQwMDdkMWQwMjViIiwidGFnIjoiIn0%3D'
cookies = {
    "XSRF-TOKEN": "eyJpdiI6Ikc3L3NLbXdRRjhZdGZ6L0Z2ZG5QNFE9PSIsInZhbHVlIjoiK2ZpdE5qeEhXU29IMTNYMmJCdGFGMXZGcDhTM3VxWC9nNUNWdDF2RlNWZkx4WXFYblFyZU9FT2VxMTN0MTJTdCtWbThOLzFSaXBwSmxoWk1zcG1DTlkvU25mNDVRRjc0VXZ0NW85V2UvZ21GR1VxTDRkVVE3cWtyZDBveGpxOTgiLCJtYWMiOiJkMmQ1Njc4MWMwZTg5YzIyN2JkY2U1NTdkZjFlMDE0ZGY5ZGJmYjcwMDgzNjlkN2IxYTQzYzgzMGU0ZGFiNGQzIiwidGFnIjoiIn0%3D; Path=/; Expires=Fri, 09 Feb 2024 13:14:11 GMT;",
    "talabna_session": "eyJpdiI6IlB5V2xGWWc1SGNmTk5iZEVSQVV0SUE9PSIsInZhbHVlIjoid1RQbWtBTUxsaUtOZWl3U3VUMkl0b3VMTVErNVZjYUNQeE1qbUZEN0pKeEpDV1RlS1hzajJNQzFnQ29aWWZId3FPSXdYeDdwbVRhNzZUTzhJd2hZeFlmZHBBSC9tdHh5Wi80Qk1CZW9GWDlvdWNVU2krbkZBQUFKbWZHUzdyZW4iLCJtYWMiOiI5YzU5ZWMwYTBiNjc0MTAyZTA0MDRlNWEzOTA5NmFkNGJlMzA0ZGNkYWY5YWYxYmUyYzNjM2U0NjNjODU3OGI3IiwidGFnIjoiIn0%3D; Path=/; HttpOnly; Expires=Fri, 09 Feb 2024 13:14:11 GMT;",
    "AWSALBTG": "UORRkVD8slb5OKleTMIbQsa9LQr+hMv4GCDAB35a2E7mLuXYgP0jxkCSX6dg5FJ2YuVw18qt4Rx9X4boyH+LECmGHqd3sNrtqUVSztMvMEidD4Sy1ID+QcmYDhYQYi7dXBmDtheuZt73cVVEK/iRkiXLWHFcqMbVTfZPYiMXtBzm8AAMJj0=; Path=/; Expires=Fri, 16 Feb 2024 11:14:13 GMT;",
    "AWSALBTGCORS": "UORRkVD8slb5OKleTMIbQsa9LQr+hMv4GCDAB35a2E7mLuXYgP0jxkCSX6dg5FJ2YuVw18qt4Rx9X4boyH+LECmGHqd3sNrtqUVSztMvMEidD4Sy1ID+QcmYDhYQYi7dXBmDtheuZt73cVVEK/iRkiXLWHFcqMbVTfZPYiMXtBzm8AAMJj0=; Path=/; Secure; Expires=Fri, 16 Feb 2024 11:14:13 GMT;",
    "AWSALB": "uXcd0YJDbtHYoL1nqsxi3Blw0qIQbjnLdwsaCxthYIogpyxW1x391a8u1KqLSaRUBJZELyXWBDmeAaaZNl1+pskhIb+/VUloCiz1uJdPAwoSmoL3Ki5M7+UJG/CU; Path=/; Expires=Fri, 16 Feb 2024 11:14:13 GMT;",
    "AWSALBCORS": "uXcd0YJDbtHYoL1nqsxi3Blw0qIQbjnLdwsaCxthYIogpyxW1x391a8u1KqLSaRUBJZELyXWBDmeAaaZNl1+pskhIb+/VUloCiz1uJdPAwoSmoL3Ki5M7+UJG/CU; Path=/; Secure; Expires=Fri, 16 Feb 2024 11:14:13 GMT;"
}
def test_parse_menu():
    
    next_page = 'https://talabna.ae/chains/food/list?page=1'
    menu_items = []
    category_dict = {}
    index = 1
    while next_page:
        
        if index == 1:
            with open('tests/testdata/samples/talabna_menu_html/first_page.html', encoding = "utf-8") as f:
                html = f.read()
                index += 1
        else:
            with open('tests/testdata/samples/talabna_menu_html/last_page.html', encoding = "utf-8") as f:
                html = f.read()

        soup = BeautifulSoup(html, "html.parser")        
        results = soup.find(id = 'datatable')
        
        headers = results.find_all("th")
        headers = [ele.text.strip() for ele in headers]
        
        rows = results.select("tbody > tr")
    
        for row in rows:
            cols = row.find_all("td")
            input_element = cols[9].find(id=f"stocksCheckbox{cols[1].text.strip()}")

            cols = [ele.text.strip() for ele in cols]
            if input_element and input_element.has_attr('checked'):
                cols[9] = 1
            else:
                cols[9] = 0
            menu_items.append(dict(zip(headers, cols)))
            
        pagination_links = soup.select('ul.pagination > li > a.page-link[rel="next"]')
        
        next_page = None
        if len(pagination_links) > 0:
            next_page = pagination_links[0]['href']
            # print(next_page)

    for menu_item in menu_items:
        category = menu_item['Category']
        if category not in category_dict:
            category_dict[category] = []
        category_dict[category].append(menu_item)
        
    categories_list = []
    for category, items in category_dict.items():
        category_dict = {'name': category, 'items': items}
        categories_list.append(category_dict)

    menu_dict = {'categories': categories_list}
        
            
    