import asyncio
import httpx
import bs4
import re
import time
# import util.addPikpak
from util.mongo import save_data, compare_tid, filter_data
from util.log_util import log
from util.save_to_mysql import SaveToMysql
from util.sendTelegram import send_media_group, rec_message
from util.config import (
    domain,
    cookie,
    fid_list,
    page_num,
    page_start,
    date,
    mongodb_enable,
    mysql_enable,
    tg_enable,
    proxy,
    pikpak_enable,
    typeids,
    deletime_enable,
    deletime_num,
    deletime_time,
    exclude,
)

from util.addPikpak import PikPak
from util.async_util import *


class SeHuaData:
    number = None
    title = None
    date = None
    tid = None
    type_name = None
    fid = None


async def get_plate_info_main(fid: int, page: int, proxy: str, date_tim):
    if typeids and typeids.get(fid, None):
        keys = [key for key in typeids[fid]]
        tasks = [*(get_plate_info(fid, page, proxy, date_tim, type_id)
                   for type_id in keys)]
        # for type_id in keys:
        #     info_list_, tid_list_ = await get_plate_info(fid, page, proxy, date_tim, type_id)
        #     info_list = info_list + info_list_
        #     tid_list = tid_list + tid_list_
        #     await deletime()
        results = await deletime_tasks(tasks)
        result = []
        for value in results:
            result += value
        return result

    return await get_plate_info(fid, page, proxy, date_tim)


# 获取帖子的id(访问板块)
async def get_plate_info(fid: int, page: int, proxy: str, date_time, typeid: int = None):
    """
    :param fid: 板块id
    :param page: 页码
    :param proxy: 代理服务器地址
    :param date_time: 日期，格式: 2019-01-01

    :return: info_list
    """
    log.info("Crawl the plate " + str(fid) + " page number " + str(page))
    url = "https://{}/".format(domain)
    # headers
    headers = {
        "cookie": cookie,
    }
    # 参数
    params = {
        "mod": "forumdisplay",
        "fid": fid,
        "page": page,
    }

    # if not typeid and typeids[fid]:
    #     keys = [key for key in typeids[fid]]
    #     for type_id in keys:
    #         await get_plate_info(fid, page, proxy, date_tim, type_id)
    #     return
    if typeid:
        params['filter'] = 'typeid'
        params['typeid'] = typeid

    # 存放字典的列表
    info_list = []

    async with httpx.AsyncClient(proxies=proxy) as client:
        response = await client.get(url, params=params, headers=headers)
    # 使用bs4解析
    soup = bs4.BeautifulSoup(response.text, "html.parser")
    # print(soup)
    all = soup.find_all(id=re.compile("^normalthread_"))
    try:
        for i in all:
            data = SeHuaData()
            data.fid = fid
            title_list = i.find("a", class_="s xst").get_text().split(" ")
            number = title_list[0]
            title_list.pop(0)
            title = " ".join(title_list)
            # date = i.find("span", attrs={"title": re.compile("^" + date_time)})
            date_td_em = i.find("td", class_="by").find("em")
            date_span = date_td_em.find(
                "span", attrs={"title": re.compile("^" + date_time)}
            )
            if date_span is not None:
                date = date_span.attrs["title"]
            else:
                time_ = re.search("^" + date_time, date_td_em.get_text())
                if time_:
                    date = time_.group()
                else:
                    continue
            if date is None:
                continue
            id = i.find(class_="showcontent y").attrs["id"].split("_")[1]
            data.number = number
            data.title = title
            data.date = date
            data.tid = id
            if typeid:
                data.type_name = typeids[fid][typeid]
            info_list.append(data)
        log.debug("Crawl the plate " + str(fid) + " page number " + str(page))
    except Exception as e:
        log.error(e)
    return info_list


# 访问每个帖子的页面
async def get_page(tid, proxy, f_info, retry=0):
    """
    :param tid: 帖子id
    :param proxy: 代理服务器地址
    :param f_info: 帖子信息
    :param retry: 当前重试次数
    """
    tid = str(tid)
    data = {}
    url = "https://{}/?mod=viewthread&tid={}".format(domain, tid)
    # headers
    headers = {
        "cookie": cookie,
    }

    try:
        async with httpx.AsyncClient(proxies=proxy) as client:
            response = await client.get(url, headers=headers)

        soup = bs4.BeautifulSoup(response.text, "html.parser")
        # 获取帖子的标题
        title = soup.find("h1", class_="ts").find("span").get_text()
        for exc in exclude:
            if exc in title:
                raise Exception(f"排除文件{title} 包含{exc}")
        # 楼主发布的内容
        info = soup.find("td", class_="t_f")

        sizeStr = re.search('【影片(容量|大小)】：(\d+|(\d+.\d+))(G|M)', info.text)
        file_size = "0M"
        if sizeStr:
            temp_str = sizeStr.group()
            file_size = temp_str.split("：")[1]

        # 存放图片的列表
        img_list = []
        for i in info.find_all("img"):
            img_list.append(i.attrs["file"])
        # 磁力链接
        magnet = soup.find("div", class_="blockcode").find("li").get_text()
        # 查找下一个blockcode
        next_blockcode = soup.find("div", class_="blockcode").find_next(
            "div", class_="blockcode"
        )
        if next_blockcode is not None:
            magnet_115 = next_blockcode.find("li").get_text()
        else:
            magnet_115 = None

        post_time_em = soup.find("img", class_="authicn vm").parent.find("em")
        post_time_span = post_time_em.find("span")
        if post_time_span is not None:
            post_time = post_time_span.attrs["title"]
        else:
            post_time = post_time_em.get_text()[4:]

        data["title"] = title
        data["post_time"] = post_time
        data["img"] = img_list
        data["magnet"] = magnet
        data["magnet_115"] = magnet_115
        data["file_size"] = file_size
        data['url'] = url
        log.debug(f"Crawl the page {tid}")
        log.debug(data.values())
        return data, f_info
    except Exception as e:
        log.error("Crawl the page " + tid + " failed.")
        log.error(e)
        if 'object has no attribute' in e:
            if retry <= 10:
                await asyncio.sleep(3)
                return await get_page(tid, proxy, f_info, retry=(retry + 1))


async def crawler(fid):
    start_time = time.time()
    tasks = [
        *(get_plate_info_main(fid, page, proxy, date()) for page in range(page_start, page_num + page_start))
    ]
    # 开始执行协程
    results = await deletime_tasks(tasks)
    end_time = time.time()
    log.info("get_plate_info 执行时间：" + str(end_time - start_time))

    # 将结果拼接
    info_list_all = []
    for result in results:
        info_list_all += result

    log.info("即将开始爬取的页面 " + " ".join([data.tid for data in info_list_all]))
    if mongodb_enable:
        log.info("mongodb_enable is True")
        tid_list_new, info_list_new = compare_tid(fid, info_list_all)
    elif mysql_enable:
        mysql = SaveToMysql()
        tid_list_new, info_list_new = mysql.compare_tid(fid, info_list_all)
        mysql.close()
    else:
        info_list_new = info_list_all
    log.info("需要爬取的页面 " + " ".join([data.tid for data in info_list_new]))

    data_list = []
    start_time = time.time()
    tasks = [get_page(i.tid, proxy, i) for i in info_list_new]
    # results = await asyncio.gather(*tasks)
    results = await deletime_tasks(tasks)

    end_time = time.time()
    log.info("get_page 执行时间：" + str(end_time - start_time))
    results_new = [i for i in results if i is not None]
    for result in results_new:
        data, i = result
        data["number"] = i.number
        data["title"] = i.title
        data["date"] = i.date
        data["tid"] = i.tid
        data['type_name'] = i.type_name
        post_time = data["post_time"]
        # 再次匹配发布时间（因为上级页面获取的时间可能不准确）
        if re.match("^" + date(), post_time):
            data_list.append(data)
    log.info("本次抓取的数据条数为：" + str(len(data_list)))
    log.info("开始写入数据库")

    mysql = None
    if mysql_enable:
        mysql = SaveToMysql()
        data_list = mysql.filter_data(data_list, fid)

    if pikpak_enable:
        pikpak = PikPak()
        await pikpak.downloads(data_list, fid)

    if mysql_enable:
        mysql.save_data(data_list, fid)
        mysql.close()

    # if mongodb_enable:
    #     data_list_new = filter_data(data_list, fid)
    #     save_data(data_list_new, fid)

    if tg_enable:
        send_media_group(data_list, fid)

    if len(data_list) > 0:
        return rec_message(data_list, fid)
    else:
        return "没有新的数据"


async def main():
    log.debug("日期: {}".format(time.strftime("%Y-%m-%d", time.localtime())))

    for fid in fid_list:
        await crawler(fid)

    log.debug("完毕：：日期: {}".format(time.strftime("%Y-%m-%d", time.localtime())))


if __name__ == "__main__":
    # asyncio.run(main())
    # while True:
    #     pass;
    asyncio.run(get_page(778060, None, None))
