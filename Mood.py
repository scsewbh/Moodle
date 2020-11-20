import requests
from bs4 import BeautifulSoup as bs
import os
import re

moodle_url = 'https://lms.manhattan.edu/my/'

#Have to been signed in
course_base_link = 'https://lms.manhattan.edu/course/view.php?id='  # append course codes at end of url to get course page (5-digits code) (data-keys)
download_link_addon = '&redirect=1'
profile_link = 'https://lms.manhattan.edu/user/profile.php?id=&showallcourses=1'

class Moodle:
    def __init__(self):
        #Username and Password for Moodle
        self.session = requests.Session()
        self.session.get(moodle_url)
        self.course_title = ''
        self.dictCourseSel = {}

    def login(self, Username, Password):
        self.login_page = 'https://auth.manhattan.edu/idp/profile/cas/login?execution=e1s1&j_username='+ Username +'&j_password='+ Password +'&_eventId_proceed='
        r = self.session.get(self.login_page)
        if r.status_code == 200 and r.url == moodle_url:
            print("Successful Login")
            return True
        else:
            print("Failed Login")
            return False

    def gatherAllCourses(self):
        course_details_prof = self.session.get(profile_link)
        soup = bs(course_details_prof.text, 'html.parser')
        r = soup.find(string='Course profiles').find_parent('li')
        a_Attribs = r.findAll('a')
        for elem in a_Attribs:
            m = re.search('(?<=course=).*(?=&)', str(elem))
            val = m.group(0)
            self.dictCourseSel[elem.text] = val

    def findCourses(self, courseKey):
        course_link = course_base_link + courseKey
        courseUnparsed = self.session.get(course_link)
        return courseUnparsed

    def parsingCourseData(self, dataUnparsed, path_start):
        soup = bs(dataUnparsed.text, 'html.parser')
        # for all activity instances check title name for File
        self.course_title = soup.find('div', {'class': 'page-header-headings'}).text
        self.course_title = re.sub(':', '-', self.course_title)
        if os.path.isdir(path_start + '/MoodleDL'):
            pass
        else:
            os.mkdir(path_start + '/MoodleDL')
        if os.path.isdir(path_start + '/MoodleDL/' + self.course_title):
            pass
        else:
            os.mkdir(path_start + '/MoodleDL/' + self.course_title)
        self.path = path_start + '/MoodleDL/' + self.course_title
        activityInstances = soup.findAll('div', {'class': 'activityinstance'})
        course_data = {}
        for ai in activityInstances:   #Can change into a dictionary to match title to href instead of two separate arrays
            hrefInstance = ai.find('a', href=True).get('href')
            title = ai.find('span', {'class': 'instancename'})
            try:
                fileType = (title.find('span').text).strip()
            except AttributeError:
                fileType = 'Other'
            if fileType == 'File':
                course_data[title.text] = [hrefInstance, fileType]
        return course_data
        # Forum, File (ppt,pdf,etc.), if none just a link, Assignment (HW), Page (Intructions)
        # Resources - ppt and docs and pdfs
        # Assignments/Project/Quiz
    
    def downloadFiles(self, course_data):
        for key in course_data:
            downloadURL = course_data[key][0] + download_link_addon
            r = self.session.get(downloadURL, allow_redirects=True)
            redirect_url = r.url
            if redirect_url.find('/'):
                filename = redirect_url.split('/')[-1]
                filename = re.sub('%20', ' ', filename)
                new_filename = self.path + '/' + filename
                open(new_filename, 'wb').write(r.content)

    def assignments(self, dataUnparsed):
        homeworks = {}
        assign = 'assignment'
        soup = bs(dataUnparsed.text, 'html.parser')
        # for all activity instances check title name for File
        activityInstances = soup.findAll('div', {'class': 'activityinstance'})
        for ai in activityInstances:
            titleName = ai.find('span', {'class': 'instancename'}).text
            if assign in titleName.lower(): #or hw in titleName.lower():
                hrefInstance = ai.find('a', href=True).get('href') #30 DAYs after due date dont include
                hwUnparsed = self.session.get(hrefInstance)
                soup = bs(hwUnparsed.text, 'html.parser')
                statusTable = soup.find('table', {'class': 'generaltable'})
                dueDate = statusTable.find('th', text='Due date')
                if dueDate is not None:
                    dd = dueDate.parent
                    due = dd.find('td').text
                    homeworks[titleName] = due, hrefInstance
                else:
                    homeworks[titleName] = "Friday, October 16, 2025, 11:00 PM", hrefInstance
        return homeworks
    

#instant.assignments(courseData)

