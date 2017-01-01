# -*- coding:utf-8 -*-

# 需要安装chardet, selenium，下载phantomjs并复制到当前目录下

from urllib import request
from selenium import webdriver
import threading, random, urllib, time, os, codecs, shutil, sys

from _downloader import *
from _decoder import *
from _parser import *
from _extender import *

phantomjs_path = 'phantomjs/bin/phantomjs'
root = 'E:/Android/'
url_prefix = {
'yingyongbao': 'http://sj.qq.com/myapp/detail.htm?apkName=',
'baidu': 'http://shouji.baidu.com/software/',
'360': 'http://zhushou.360.cn/detail/index/soft_id/'
}

def page_invalid(market, data):
	if market == 'yingyongbao':
		return False
	elif market == 'baidu':
		return "<p>请检查您所输入的URL地址是否有误。</p>" in data
	elif market == '360':
		return '<span class="t">获取应用内容失败，请尝试ctrl+f5刷新</span>' in data
	return False	

def check_response(market, result):
	if not len(result): return False
	if market == 'yingyongbao':
		if not 'Name' in result[0]: return False
		if not 'Download' in result[0]: return False
		if not 'Size' in result[0]: return False
		if not 'Rating' in result[0]: return False
		if not 'Rating_Num' in result[0]: return False
		if not 'Category' in result[0]: return False
		if not 'Edition' in result[0]: return False
		if not 'Developer' in result[0]: return False
		if not 'Update_Time' in result[0]: return False
		if not len(result[1]): return False
		if not len(result[2]): return False
	elif market == 'baidu':
		if not 'Name' in result[0]: return False
		if not 'Download' in result[0]: return False
		if not 'Size' in result[0]: return False
		if not 'Rating' in result[0]: return False
		if not 'Category' in result[0]: return False
		if not 'Edition' in result[0]: return False
		if not len(result[2]): return False
	elif market == '360':
		if not 'Name' in result[0]: return False
		if not 'Download' in result[0]: return False
		if not 'Size' in result[0]: return False
		if not 'Rating' in result[0]: return False
		if not 'Rating_Num' in result[0]: return False
		if not 'Edition' in result[0]: return False
		if not 'Developer' in result[0]: return False
		if not 'Update_Time' in result[0]: return False
		if not '5-Star_Rating_Num' in result[0]: return False
		if not '4-Star_Rating_Num' in result[0]: return False
		if not '3-Star_Rating_Num' in result[0]: return False
		if not '2-Star_Rating_Num' in result[0]: return False
		if not '1-Star_Rating_Num' in result[0]: return False
		if not 'Comment_Num' in result[0]: return False
		if not 'Best_Comment_Num' in result[0]: return False
		if not 'Good_Comment_Num' in result[0]: return False
		if not 'Bad_Comment_Num' in result[0]: return False
		if not 'System' in result[0]: return False
		if not len(result[2]): return False
	return True
	
def open_url(market, url):
	for i in range(10):
		if market == 'baidu':
			try:
				web = request.urlopen(url)
				charset = str(web.headers.get_content_charset())
				if charset == "None": charset = "utf-8"
				data = web.read().decode(charset)
			except:
				data = ""
		else:
			driver = webdriver.PhantomJS(executable_path=phantomjs_path)
			driver.get(url)
			data = driver.page_source
			driver.quit()
		if page_invalid(market, data): return ()
		dict = get_app_basic_info(market, data)				
		permission_list = get_app_permission(market, data)
		description = get_app_description(market, data)
		release_note = get_app_release_note(market, data)
		download_link = get_app_download_link(market, data)
		extend_urls = get_extend_urls(market, data, url_prefix[market])
		similar_apps = get_similar_apps(market, data, url_prefix[market])
		icon_link = get_icon_download_link(market, data)
		result = (dict, permission_list, description, release_note, download_link, extend_urls, similar_apps, icon_link)
		if not check_response(market, result):
			continue
		else:
			break
	return result

def read_url(market):
	result = set()
	if os.path.isfile(root+market+"/~url_list.txt"):
		shutil.move(root+market+"/~url_list.txt", root+market+"/url_list.txt")
	elif os.path.isfile(root+market+"/url_list.txt"):
		pass
	else:
		return result
	fin = open(root+market+"/url_list.txt", "r")
	for line in fin:
		result.add(line.replace('\r', "").replace('\n', ""))
	fin.close()
	return result
			
def main_loop(threadidstr):
	iteration = 0
	update = 0
	hold_lock_pool = False
	hold_lock_set = False
	while len(url_set):
		iteration += 1
		lock_set.acquire()
		hold_lock_set = True
		url_list = random.sample(url_set, (int)(len(url_set)*rate_per_iteration))
		lock_set.release()
		hold_lock_set = False
		random.shuffle(url_list)
		for short_url in url_list:
			try:
				url = url_prefix[market]+short_url
				lock_pool.acquire()
				hold_lock_pool = True
				if short_url in url_pool:
					lock_pool.release()
					hold_lock_pool = False
					continue
				else:
					url_pool.add(short_url)
					lock_pool.release()
					hold_lock_pool = False
				print (market+threadidstr+"：开始连接（"+url+"）")
				if os.path.exists("~"+market+"tmp"+threadidstr): shutil.rmtree("~"+market+"tmp"+threadidstr, ignore_errors=True)
				response = open_url(market, url)
				if not len(response):
					print (market+threadidstr+"：无效的链接（"+url+"）")
					lock_set.acquire()
					hold_lock_set = True
					url_set.discard(short_url)
					lock_set.release()
					hold_lock_set = False
					update += 1
					if (update % (thread_num*2) == 0):
						update = 0
						lock_set.acquire()
						hold_lock_set = True
						shutil.move(root+market+"/url_list.txt", root+market+"/~url_list.txt")
						fout = codecs.open(root+market+"/url_list.txt", "w", "utf-8")
						for temp_url in url_set:
							fout.write(temp_url+"\n")
						fout.close()
						os.remove(root+market+"/~url_list.txt")
						lock_set.release()
						hold_lock_set = False
						print (market+threadidstr+"：更新链接列表")
					lock_pool.acquire()
					hold_lock_pool = True
					url_pool.remove(short_url)
					lock_pool.release()
					hold_lock_pool = False
					continue
				if not len(response[0]):
					print (market+threadidstr+"：访问链接失败（"+url+"）")
					lock_pool.acquire()
					hold_lock_pool = True
					url_pool.remove(short_url)
					lock_pool.release()
					hold_lock_pool = False
					continue
				lock_set.acquire()
				hold_lock_set = True
				for extend_url in response[5]:					
					url_set.add(extend_url)
				lock_set.release()
				hold_lock_set = False
				if not download_apk(market, response[4], "~"+market+"tmp"+threadidstr+".apk"):
					print (market+threadidstr+"：下载APK失败（"+url+"）")
					lock_pool.acquire()
					hold_lock_pool = True
					url_pool.remove(short_url)
					lock_pool.release()
					hold_lock_pool = False
					continue
				extract_dir = unzip_apk("~"+market+"tmp"+threadidstr+".apk")
				if len(extract_dir):
					manifest_file = binxml2strxml(extract_dir+"/AndroidManifest.xml")
					if len(manifest_file):
						apk_key = get_apk_key(market, "~"+market+"tmp"+threadidstr+".apk", manifest_file)
						if len(apk_key) == 3:
							update += 1
							cur_time = str(int(time.time()))
							if os.path.exists(root+market+"/"+apk_key[1]):
								if not os.path.exists(root+market+"/"+apk_key[1]+"/{"+apk_key[2]+"}"):
									download_icon(market, response[7], "~"+market+"tmp"+threadidstr+".png")
									fout = codecs.open(extract_dir+"/Index.txt", "w", "utf-8")
									fout.write("Market\n\t"+apk_key[0]+"\nPackage_Name\n\t"+apk_key[1]+"\nMD5\n\t"+apk_key[2]+"\nTime\n\t"+cur_time+"\nLink\n\t"+url+"\nDownload_Link\n\t"+response[4]+"\n")
									fout.close()
									shutil.move("~"+market+"tmp"+threadidstr+".apk", extract_dir+"/"+apk_key[1]+".apk")
									if os.path.isfile("~"+market+"tmp"+threadidstr+".png"): shutil.move("~"+market+"tmp"+threadidstr+".png", extract_dir+"/icon.png")
									shutil.copytree(extract_dir, root+market+"/"+apk_key[1]+"/{"+apk_key[2]+"}", symlinks=True)
									print (apk_key[0]+threadidstr+"：更新"+apk_key[1]+"版本和信息")
									# 数据库添加
								else:
									print (apk_key[0]+threadidstr+"：更新"+apk_key[1]+"信息。无版本更新")
									# 数据库更新
							else:
								os.makedirs(root+market+"/"+apk_key[1])
								download_icon(market, response[7], "~"+market+"tmp"+threadidstr+".png")
								fout = codecs.open(extract_dir+"/Index.txt", "w", "utf-8")
								fout.write("Market\n\t"+apk_key[0]+"\nPackage_Name\n\t"+apk_key[1]+"\nMD5\n\t"+apk_key[2]+"\nTime\n\t"+cur_time+"\nLink\n\t"+url+"\nDownload_Link\n\t"+response[4]+"\n")
								fout.close()
								shutil.move("~"+market+"tmp"+threadidstr+".apk", extract_dir+"/"+apk_key[1]+".apk")
								if os.path.isfile("~"+market+"tmp"+threadidstr+".png"): shutil.move("~"+market+"tmp"+threadidstr+".png", extract_dir+"/icon.png")
								shutil.copytree(extract_dir, root+market+"/"+apk_key[1]+"/{"+apk_key[2]+"}", symlinks=True)
								print (apk_key[0]+threadidstr+"：新增"+apk_key[1])
								# 数据库添加
							if not os.path.exists(root+market+"/"+apk_key[1]+"/["+cur_time+"]"):
								os.makedirs(root+market+"/"+apk_key[1]+"/["+cur_time+"]")
							fout = codecs.open(root+market+"/"+apk_key[1]+"/["+cur_time+"]/Information.txt", "w", "utf-8")
							for key, value in response[0].items():
								if len(value): fout.write(key+"\n\t"+value+"\n")
							if len(response[6]):
								fout.write("Similar_Apps\n")
								for urls in response[6]:
									fout.write("\t"+urls+"\n")
							fout.close()
							if len(response[1]):
								fout = codecs.open(root+market+"/"+apk_key[1]+"/["+cur_time+"]/Permission.txt", "w", "utf-8")
								for permission in response[1]:
									fout.write(permission+"\n")
								fout.close()
							if len(response[2]):
								fout = codecs.open(root+market+"/"+apk_key[1]+"/["+cur_time+"]/Description.txt", "w", "utf-8")
								fout.write(response[2])
								fout.close()
							if len(response[3]):
								fout = codecs.open(root+market+"/"+apk_key[1]+"/["+cur_time+"]/Release_Note.txt", "w", "utf-8")
								fout.write(response[3])
								fout.close()
							fout = codecs.open(root+market+"/"+apk_key[1]+"/["+cur_time+"]/Index.txt", "w", "utf-8")
							fout.write("Market\n\t"+apk_key[0]+"\nPackage_Name\n\t"+apk_key[1]+"\nMD5\n\t"+apk_key[2]+"\nTime\n\t"+cur_time+"\nLink\n\t"+url+"\nDownload_Link\n\t"+response[4]+"\n")
							fout.close()
							if (update % (thread_num*2) == 0):
								update = 0
								lock_set.acquire()
								hold_lock_set = True
								shutil.move(root+market+"/url_list.txt", root+market+"/~url_list.txt")
								fout = codecs.open(root+market+"/url_list.txt", "w", "utf-8")
								for temp_url in url_set:
									fout.write(temp_url+"\n")
								fout.close()
								os.remove(root+market+"/~url_list.txt")
								lock_set.release()
								hold_lock_set = False
								print (market+threadidstr+"：更新链接列表")
						else:
							print (market+threadidstr+"：解析XML失败（"+url+"）")
					else:
						print (market+threadidstr+"：读取二进制XML失败（"+url+"）")
				else:
					print (market+threadidstr+"：解压缩APK失败（"+url+"）")
				lock_pool.acquire()
				hold_lock_pool = True
				url_pool.remove(short_url)
				lock_pool.release()
				hold_lock_pool = False
			except:
				print (market+threadidstr+"：未知错误（"+url+"）")
				if hold_lock_pool: lock_pool.release()
				if hold_lock_set: lock_set.release()

if __name__ == '__main__':
	if len(sys.argv) < 4: exit()
	market = sys.argv[1]
	thread_num = int(sys.argv[2])
	if thread_num < 1: exit()
	rate_per_iteration = float(sys.argv[3])
	if rate_per_iteration <= 0 or rate_per_iteration > 1: exit()
	lock_pool = threading.Lock()
	url_pool = set()
	lock_set = threading.Lock()
	url_set = read_url(market)
	if not len(url_set): exit()
	for i in range(1, thread_num):
		t = threading.Thread(target=main_loop, args=(str(i)))
		t.start()
	main_loop('0')