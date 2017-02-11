###############################################################################
#                                                                             #
# Crawler.py works by curling the Chalmers course webpage for all possible    #
# courses in a given study period. The resulting html-data is then parsed     #
# using BeautifulSoup and stored into a dictionary (code, name, credits,      #
# inst., period).                                                             #
#                                                                             #
###############################################################################

from bs4 import BeautifulSoup
from io import BytesIO
import re
import pycurl
import json
import csv

###### Parameters ######

search_year = "2016%2F2017"                             # change to the correct year.
print_csv = False                                       # do you want to print the result as a csv?
csv_path = "/home/erik/git/coursecrawler/kurser.csv"    # path

######

codeMap = {}
courseMap = {}

# For each period (1 through 4) we curl the course webpage for all courses in
# that period.
# For each iteration of the loop we curl for period i, parse the result and
# store it in the dictionary courseMap.
for i in range(1,4+1):

    buffer = BytesIO()
    c = pycurl.Curl()
    c.setopt(pycurl.URL, "https://www.student.chalmers.se/sp/course_list")

    # POST parameters to send with the curl. (Corresponds to -d.)
    # We care particurarly much about:"search_ac_year" and
    # "field_search_start_sp".
    postreq = "search_ac_year="+search_year+"&" + \
               "search_course_code=&" + \
               "search_course_name_sv=&" + \
               "search_course_name_en=&" + \
               "field_search_course_owner=&" + \
               "field_search_dept=&" + \
               "field_search_start_sp=LP"+str(i)+"&" + \
               "field_search_edu_level=&" + \
               "field_search_credit_min=&" + \
               "field_search_credit_max=&" + \
               "field_search_lang=&" + \
               "field_search_grade=&" + \
               "button_search_course=S%F6k&" + \
               "query_start=1&" + \
               "batch_size=10000"

    c.setopt(pycurl.POST, 1)
    c.setopt(pycurl.POSTFIELDS, postreq)
    c.setopt(c.WRITEDATA, buffer)
    c.perform()
    c.close

    body = buffer.getvalue()
    datadump = body.decode("ISO-8859-14")

    soup = BeautifulSoup(datadump, "html.parser")

    # For each option-tag that is not None, see if it matches the regex (filters
    # out code - institution) and map the code to the institution in a dictionary.
    for option in soup.find_all("option"):
        if option.string is not None:
            match = re.match(r'(([0-9]{2})|([0-9]{4}))\s-\s', option.string)
            if match:
                codeAndInst = option.string.split(" - ")
                codeMap[codeAndInst[0].strip()] = codeAndInst[1].strip()

    # For each tag which has a course_id, check that it is not None and matches the
    # regex for a course code. If so, retrieve the name, credits and owner of the
    # course and store it in a dictionary.
    for c in soup.find_all(href=re.compile("course_id")):
        if c.string is not None:
            match = re.match(r'[a-zA-Z]{3}[0-9]{3}', c.string)
            if match:
                name = c.parent.next_sibling.next_sibling.a
                hp = c.parent.next_sibling.next_sibling.next_sibling.next_sibling
                owner = c.parent.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling
                if owner is not None:
                    courseMap[c.string+"lp"+str(i)] = [c.string, name.string,
                                                       hp.string,
                                                       codeMap[owner.string],
                                                       "LP"+str(i)]

if print_csv:
    with open(csv_path, 'w') as csvfile:
        fieldnames = ['code', 'name', 'credits', 'institution', 'study period']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for k, v in courseMap.items():
            writer.writerow({'code'         : v[0],
                             'name'         : v[1],
                             'credits'      : float(v[2].replace(',','.')),
                             'institution'  : v[3],
                             'study period' : v[4]})
