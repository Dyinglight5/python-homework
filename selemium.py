from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# 使用Service对象来设置ChromeDriver
service = Service(ChromeDriverManager().install())
browser = webdriver.Chrome(service=service)
browser.get('https://www.baidu.com')
browser.quit()
