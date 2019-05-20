# -*- coding: utf-8 -*-
"""
Created on Wed Apr 11 13:39:08 2018

@author: zhangj
"""

from selenium.webdriver.common.keys import Keys
import os, errno
from selenium import webdriver
import pandas as pd
from bs4 import BeautifulSoup
from googletrans import Translator
from pypac import PACSession
translator = Translator()
from time import sleep
from datetime import datetime, timedelta
import http.client, urllib.parse, uuid, json
from Azure_translation_example import msft_translate
import glob

# get the path of ChromeDriverServer
dir = os.path.dirname('C:\Chromedriver\chromedriver.exe')
chrome_driver_path = dir + '\chromedriver.exe'
driver = webdriver.Chrome(chrome_driver_path)
driver.implicitly_wait(30)

#Organization
org = 'ROSZ'
region = 'EU'

#Pagination scheme click next button

#Initialize URL
url_list = ['http://www.roszdravnadzor.ru/services/lssearch']

#Initialize results list
outlist = [['Recall #', 'Class #', 'HC Start Date', 'Posting Date', 'Product', 'Company', 'Parent Company2', 'Location',
            'Reason', 'Unique ID', 'Type', 'Agency', 'New', 'Deep Dive (Y or N)', 'Event',
            'Product Category', 'Reason Category', 'Div', 'Site_ID', 'ID Number', 'Region', 'link']]

# Get most recent recall file
def read_last_recall():
    cwd = os.getcwd()
    file_list = []
    datelist = []
    for name in glob.glob(cwd+'/1_Generated_Recalls/*.*'):
        file_list.append(name)
    
    for f in file_list:
        split = f.split('\\')
        split2 = split[-1].split('.')
        split3 = split2[0].split('_')
        
        dateString = split3[-1]
        
        dateDt = datetime.strptime(dateString, '%Y-%m-%d')
        
        datelist.append(dateDt)
        
        maxdate = dateDt
        for d in datelist:
            if d > dateDt:
                maxdate = d
        
        maxString = datetime.strftime(maxdate, '%Y-%m-%d')
        
        for f in file_list:
            if maxString in f: maxfile = f
        
    df= pd.read_excel(maxfile)
    
    return(df)

# What year are we interested in?
try: 
    from __main__ import yl, lastdf
except:
    now = datetime.now()
    yl = [str(now.year)]
    try:
        lastdf = read_last_recall()
        lastdf = lastdf.replace(r'^\s*$', 'NA', regex=True)
        lastdf.fillna('NA', inplace=True)
    except: pass

# Test if lastdf exists
uselastdf = True
try:
    lastdf
except NameError:
    lastdf = None
    uselastdf = False

# Use a list of recall numbers to check if recall was already retrieved
if uselastdf:
    orgdf = lastdf.loc[lastdf['Agency'].str.contains(org)]
    checklist = list(orgdf['Recall #'])
    checklist1 = list(orgdf['Posting Date'])
    checklist2 = list(orgdf['Product'])

yints = map(int, yl)
ymax = max(yints)

########### End globals ################################################################

try: from __main__ import limit_pages
except: limit_pages = True

def scrape_main(url): 
    results = []
    dl_links = []
    dl_names = []
    
    pagenum = 0
    if limit_pages == True: page_limit = 40
    else: page_limit = 10000
    
    # today - 90 days, only look at recalls in last 45 days
    d90 = datetime.today() - timedelta(days=45)
    y = str(d90.year)
    d = str(d90.day)
    if len(d) == 1: d = '0'+d
    m = str(d90.month)
    if len(m) == 1: m = '0'+m
    
    driver.get(url)
    sleep(1)
    expand_search = driver.find_elements_by_xpath("//*[contains(text(), 'Расширенный поиск')]")
    expand_search[1].click()
    sleep(1)
    start_date = driver.find_element_by_id("id_let-start")
    start_date.send_keys(y[-1]) #FORMATTING FOR 01/01/2018 for this search box 45.67.8123
    sleep(1)
    start_date.send_keys(d[0])
    sleep(1)
    start_date.send_keys(d[1])
    sleep(1)
    start_date.send_keys(m[0])
    sleep(1)
    start_date.send_keys(m[1])
    sleep(1)
    start_date.send_keys(y[-4])
    sleep(1)
    start_date.send_keys(y[-3])
    sleep(1)
    start_date.send_keys(y[-2])
    sleep(1)
    search_button = driver.find_element_by_xpath("//button[@class='search-form-extended-submit']")
    search_button.click()
    sleep(3)
    
    link_running_list = [] # Running list of recalls to ignore duplicates.
    recall_running_list = [] # Running list of recalls to ignore duplicates.
    while(pagenum < page_limit):
            #Get page source
        try:
            driver_html = driver.page_source
            soup = BeautifulSoup(driver_html, 'lxml')
            main_table = soup.find_all("table", {"class": "data-table search-result table-type-2 dataTable no-footer"})
            row_table = main_table[1].find_all("tbody")
            row_entries = row_table[0].find_all("tr")
            
            cols = row_entries[0].find_all("td")
            
            #Used to check if reached end of table
            indices = soup.find_all("div", {"class": "dataTables_info"})
            numbers = indices[0].find_all("strong")
            numlist = []
            for n in numbers:
                numlist.append(n.text)            
     
        except: break
    
        
        for row in row_entries:
            
            try:
                cols = row.find_all("td")
                #recall number, date , and link
                cur_date = 'NA'
                cur_recall = 'NA'
                cur_link = 'NA'
                
                field_text = cols[8].text
                googtrans = msft_translate(field_text)
                field_text = googtrans
                if 'of' in field_text:
                    field_split = field_text.split('of')
                    cur_recall = field_split[0].rstrip().lstrip()
                    cur_date = field_split[-1].rstrip().lstrip()
                elif 'from' in field_text:
                    field_split = field_text.split('from')
                    cur_recall = field_split[0].rstrip().lstrip()
                    cur_date = field_split[-1].rstrip().lstrip()
                else:
                    field_split = field_text.split(' ')
                    cur_recall = field_text.rstrip().lstrip()
                    cur_date = field_split[-1].rstrip().lstrip()
                    
                hrefs = cols[8].find_all("a", href=True) #LINK
                for a in hrefs:
                    cur_link = a['href']
                    cur_link = 'http://www.roszdravnadzor.ru/services/lssearch'+cur_link
                
                # Check if recall is already downloaded
                new_recall = True
                if uselastdf:
                    print ('checking recall: ' + cur_recall)
                    if (cur_recall in checklist):
                        print ('Recall already downloaded! '+cur_recall)
                        new_recall = False
                        
                if (cur_recall in recall_running_list):
                    print ('Recall already downloaded! '+cur_recall)
                    new_recall = False
                if (cur_link in link_running_list):
                    print ('Recall already downloaded! '+cur_recall)
                    new_recall = False
                
                if new_recall:
                    cds = cur_date.split(' ')
                    cds = cds[:-2]
                    cur_date = ''
                    for c in cds:
                        cur_date = cur_date + ' ' + c
                    cur_date = cur_date.lstrip().rstrip()
                    
                    #Original format 23.03.2018
                    try:
                        cur_date = datetime.strptime(cur_date, '%d.%m.%Y')
                        cur_date = datetime.strftime(cur_date, '%m/%d/%Y')
                    except: pass
                
                    #Original format 09/01/2018
                    try:
                        cur_date = datetime.strptime(cur_date, '%d/%m/%Y')
                        cur_date = datetime.strftime(cur_date, '%m/%d/%Y')
                    except: pass
                
                    #Original format March 19, 2018
                    try:
                        cur_date = datetime.strptime(cur_date, '%B %d, %Y')
                        cur_date = datetime.strftime(cur_date, '%m/%d/%Y')
                    except: pass
                
                    #Original format 03.23.2018
                    try:
                        cur_date = datetime.strptime(cur_date, '%m.%d.%Y')
                        cur_date = datetime.strftime(cur_date, '%m/%d/%Y')
                    except: pass
                    
                    #Product
                    cur_product = 'NA'
                    try:
                        cur_product = cols[0].text + ', ' + cols[1].text + ', ' + cols[2].text
                        googtrans = msft_translate(cur_product)
                        cur_product = googtrans
                    except: pass
                    
                    #Company
                    cur_company = 'NA'
                    try:
                        cur_company = cols[3].text
                        googtrans = msft_translate(cur_company)
                        cur_company = googtrans
                    except: pass
                    
                    #cols[4] has location info?
                    
                    #Reason
                    cur_reason = 'NA'
                    try:
                        cur_reason = cols[5].text
                        googtrans = msft_translate(cur_reason)
                        cur_reason = googtrans
                    except: pass
                    
                    #recall status
                    isrecall = True
                    try:
                        recall_status = cols[6].text
                        googtrans = msft_translate(recall_status)
                        recall_status = googtrans
                        if ('Suspension' in recall_status) or ('Termination' in recall_status) or ('Withdrawal' in recall_status):
                            isrecall = True
                        else:
                            isrecall = False
                    except: pass
                
                    if 'counter' in cur_reason.lower():
                        isrecall = False
                        
                    if(isrecall):
                        cur_class = 'NA'
                        cur_type = 'NA'
                        cur_location = 'Russia'
                        recall_running_list.append(cur_recall) # Running list to avoid duplicates
                        link_running_list.append(cur_link) # Running list to avoid duplicates
                        results.append([cur_recall, cur_class, 'NA', cur_date, cur_product, cur_company, 'NA', cur_location,
                                        cur_reason, '1', cur_type, org, 'NA', 'NA', 'NA',
                                        'NA', 'NA', 'NA', 'NA', 'NA', region, cur_link])
        
                    #download links PDFS
                    dl_links.append(cur_link)
                    split = cur_link.split('/')
                    name = split[-1]
                    name = name[-5:]+'.pdf'
                    dl_names.append(name)
            except: pass
        
        print('Current list length: ' + str(len(numlist)))
        print('Current list length unique: ' + str(len(set(numlist))))
        #Next button
        if len(numlist) == len(set(numlist)):
            try:
                driver.find_element_by_id("DataTables_Table_1_next").click()
                sleep(10)
                pagenum += 1
            except: break
        else: break
    driver.quit()
#    if len(dl_links)>0:
#        download_files(dl_links, dl_names)
    return(results)
    
def download_files(url_list, filenames): #Download files
    session = PACSession()
    #Check directory exists
    try:
        os.makedirs('C://download/pdf-'+org+'/')
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    #Check files and names are the same length:
    if len(url_list) == len(filenames):
        for i in range(0, len(url_list)):
            sleep(1)
            try:
                print('Downloading: ' + filenames[i] + '@ ' + url_list[i])
                resp = session.get(url_list[i], verify=False)
                filepath = 'C://download/pdf-'+org+'/'+filenames[i]
                with open (filepath, 'wb') as f:
                    f.write(resp.content)
            except: print("too many connections: "+ filenames[i] + '@ ' + url_list[i])
    else:
        print('Files and names are not of equal length!')
    session.close()
    
#Activate
for url in url_list:
    details = scrape_main(url)
    for row in details:
        outlist.append(row)
df_out = pd.DataFrame(outlist)
df_out.columns = df_out.iloc[0]

# remove any unwanted rows.
df_out = df_out.loc[df_out['Recall #'] != 'Recall #']

# Output
df_out.to_csv('Parsed_'+org+'.csv', index=False, header=False)

driver.quit()
