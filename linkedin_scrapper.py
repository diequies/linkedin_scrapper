from selenium import webdriver
from bs4 import BeautifulSoup as bs
import time
import pandas as pd
import re as re
from webdriver_manager.chrome import ChromeDriverManager

page = input("Enter the URL")
name = page[28:-1]

username = input("username")
password = input('pass')

#accessing Chromedriver
browser = webdriver.Chrome(ChromeDriverManager().install())

#Open login page
browser.get('https://www.linkedin.com/login?fromSignIn=true&trk=guest_homepage-basic_nav-header-signin')

#Enter login info:
elementID = browser.find_element_by_id('username')
elementID.send_keys(username)

elementID = browser.find_element_by_id('password')
elementID.send_keys(password)
elementID.submit()

# Web scrapper for infinite scrolling page 
browser.get(page + 'detail/recent-activity/shares/')
browser.maximize_window()
time.sleep(2)  # Allow 2 seconds for the web page to open
scroll_pause_time = 2 # You can set your own pause time. My laptop is a bit slow so I use 1 sec
screen_height = browser.execute_script("return window.screen.height;")   # get the screen height of the web
i = 1

while True:
    # scroll one screen height each time
    browser.execute_script("window.scrollTo(0, {screen_height}*{i});".format(screen_height=screen_height, i=i))  
    i += 1
    time.sleep(scroll_pause_time)
    # update scroll height each time after scrolled, as the scroll height can change after we scrolled the page
    scroll_height = browser.execute_script("return document.body.scrollHeight;")  
    # Break the loop when the height we need to scroll to is larger than the total scroll height
    if (screen_height) * i > scroll_height:
        break

#Check out page source code
company_page = browser.page_source

#Use Beautiful Soup to get access tags
linkedin_soup = bs(company_page.encode("utf-8"), "html")
linkedin_soup.prettify()

#Find the post blocks
containers = linkedin_soup.findAll('div',{'class':'occludable-update ember-view'})

post_dates = []
post_texts = []
post_likes = []
post_comments = []
video_views = []
media_links = []
media_type = []

#Looping through the posts and appending them to the lists
for container in containers:

    #Try function to make sure its a post and a promotion
    try:
        posted_date = container.find('span', {'class':'visually-hidden'})
        text_box = container.find('div',{'class':'feed-shared-update-v2__description-wrapper'})
        text = text_box.find('span', {'dir':'ltr'})
        new_likes = container.findAll('li', {'class': 'social-details-social-counts__reactions social-details-social-counts__item social-details-social-counts__reactions--with-social-proof'})
        new_comments = container.findAll('li', {'class': 'social-details-social-counts__comments social-details-social-counts__item social-details-social-counts__item--with-social-proof'})

        #Appending date and text to lists
        post_dates.append(posted_date.text.strip())
        post_texts.append(text_box.text.strip())

        #Determining media type and collecting relevant info for each type
        try:
            video_box = container.findAll("div",{"class": "feed-shared-update-v2__content feed-shared-linkedin-video ember-view"})
            video_link = video_box[0].find("video", {"class":"vjs-tech"})
            media_links.append(video_link['src'])
            media_type.append("Video")
        except:
            try:
                image_box = container.findAll("div",{"class": "feed-shared-image__container"})
                image_link = image_box[0].find("img", {"class":"ivm-view-attr__img--centered feed-shared-image__image feed-shared-image__image--constrained lazy-image ember-view"})
                media_links.append(image_link['src'])
                media_type.append("Image")
            except:
                try:
                    image_box = container.findAll("div",{"class": "feed-shared-image__container"})
                    image_link = image_box[0].find("img", {"class":"ivm-view-attr__img--centered feed-shared-image__image lazy-image ember-view"})
                    media_links.append(image_link['src'])
                    media_type.append("Image")
                except:
                    try:
                        article_box = container.findAll("div",{"class": "feed-shared-article__description-container"})
                        article_link = article_box[0].find('a', href=True)
                        media_links.append(article_link['href'])
                        media_type.append("Article")
                    except:
                        try:
                            video_box = container.findAll("div",{"class": "feed-shared-external-video__meta"})          
                            video_link = video_box[0].find('a', href=True)
                            media_links.append(video_link['href'])
                            media_type.append("Youtube Video")
                        except:
                            try:
                                poll_box = container.findAll("div",{"class": "feed-shared-update-v2__content overflow-hidden feed-shared-poll ember-view"})
                                media_links.append("None")
                                media_type.append("Other: Poll, Shared Post, etc")
                            except:
                                media_links.append("None")
                                media_type.append("Unknown")

        #Getting Video Views. (The folling three lines prevents class name overlap)
        view_container2 = set(container.findAll("li", {'class':["social-details-social-counts__item"]}))
        view_container1 = set(container.findAll("li", {'class':["social-details-social-counts__reactions","social-details-social-counts__comments social-details-social-counts__item"]}))
        result = view_container2 - view_container1

        view_container = []
        for i in result:
            view_container += i

        try:
            video_views.append(view_container[1].text.strip().replace(' Views', ''))
        except:
            video_views.append('N/A')

        #Appending likes and comments if they exist
        try:
            post_likes.append(new_likes[0].text.strip())
        except:
            post_likes.append(0)
            pass

        try:
            post_comments.append(new_comments[0].text.strip())
        except:
            post_comments.append(0)
            pass
    except:
        pass

#Stripping non-numeric values
comment_count = []
for i in post_comments:
    s = str(i).replace('Comment','').replace('s','').replace(' ','')
    comment_count += [s]

data = {
    "Date Posted": post_dates,
    "Media Type": media_type,
    "Post Text": post_texts,
    "Post Likes": post_likes,
    "Post Comments": comment_count,
    "Video Views": video_views,
    "Media Links": media_links
}

df = pd.DataFrame(data)

df.to_csv('linkedIn_result.csv')