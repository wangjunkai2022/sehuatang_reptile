import os

from pikpakapi import PikPakApi, DownloadStatus
import asyncio
from util.log_util import log
from util.config import date, pikpak_enable, pikpak_username, pikpak_pw, pikpak_path_class, proxy_enable, proxy_url, \
    fid_json

from util.async_util import *

checkCount = 10

timeout_time = 5


class PikPak:
    client = PikPakApi(pikpak_username, pikpak_pw,
                       proxy_enable and proxy_url or None)

    get_path_id_count = {}

    async def get_path_id(self, parent_path):
        try:
            paths = await asyncio.wait_for(self.client.path_to_id(parent_path, True), timeout=timeout_time)
            path_id = paths[len(paths) - 1].get("id", None)
            return path_id
        except:
            count = self.get_path_id_count.get(parent_path, 0)
            self.get_path_id_count[parent_path] = count + 1
            if count > checkCount:
                raise Exception('已经重复获取path_id{}次'.format(checkCount))
            await asyncio.sleep(1)
            return await self.get_path_id(parent_path)

    parent_state = {}

    async def await_parent_path(self, path):
        parentState = self.parent_state.get(path, None)
        if parentState:
            if parentState == DownloadStatus.downloading:
                log.info("等待父文件{}创建完成".format(path))
                await asyncio.sleep(1)
                await self.await_parent_path(path)
            return

        self.parent_state[path] = DownloadStatus.downloading
        await self.get_path_id(path)
        self.parent_state[path] = DownloadStatus.done

    async def download(self, data, fid):
        try:
            if pikpak_path_class:
                parent_path = os.path.join(
                    "sehuatang", fid_json.get(fid, "other"))
                if data.get('type_name'):
                    parent_path = os.path.join(parent_path, data['type_name'])
                if '[无码破解]' in data['title']:
                    parent_path = os.path.join(parent_path, "无码破解")
            else:
                parent_path = "sehuatang"

            # 等待公共的父路径创建好
            await self.await_parent_path(parent_path)

            title = "{}___{}".format(data['number'], data['title'])

            # 最终保存位置
            seave_path = os.path.join(parent_path, title)

            path_id = await self.get_path_id(seave_path)
            # paths = await asyncio.wait_for(
            #     self.client.path_to_id(
            #         seave_path, True), timeout=timeout_time)
            # path_id = paths[len(paths) - 1].get("id", None)
            # paths = await asyncio.wait_for(self.client.create_folder(name=title, parent_id=path_id), timeout=timeout_time)
            # path_id = paths.get("file").get("id")

            log.info("pikpak 开启离线下载：\nmagnet:{}\ntitle:{}".format(
                data["magnet"], data["title"]))
            task = self.client.offline_download(
                data["magnet"],
                path_id,
            )
            result = await asyncio.wait_for(task, timeout=timeout_time)

            log.info("pikpak 保存中：{} 保存路径：{} \n 离线任务：{}".format(
                title, seave_path, result))
            task_id = result.get("task").get('id')
            file_id = result.get("task").get('file_id')
            status_count = 0
            while True:
                status_count += 1
                task = self.client.get_task_status(task_id, file_id)
                result = await asyncio.wait_for(task, timeout=timeout_time)
                print("{} 的 下载状态：{}".format(data["title"], result))
                if DownloadStatus.done == result or DownloadStatus.not_found == result:
                    break
                await asyncio.sleep(2)
                if status_count >= checkCount:
                    raise Exception(
                        "检测{}次 还是未完成下载 这里判断为下载失败。。。。。。。".format(checkCount))

            log.info("pikpak 保存完成：{} 保存路径：{}".format(
                title, seave_path))
            data['save_pikpak'] = parent_path
        except Exception as e:
            log.error("pikpak 离线下载失败 error:{}\ndata:{}".format(e, data))
            # datas.remove(data)
            return data

    async def downloads(self, datas, fid):
        if not pikpak_enable or len(datas) < 1:
            return
        try:
            await self.client.login()
        except Exception:
            log.error("pikpak 登陆失败")
            return

        # tasks = [
        #     self.download(data, fid) for data in datas
        # ]
        # results = await deletime_tasks(tasks)
        results = []
        for data in datas:
            result = await self.download(data, fid)
            results.append(result)
        for data in results:
            if data:
                datas.remove(data)
        # for index in range(len(datas) - 1, -1, -1):
        #     data = datas[index]
        # # for data in datas[:]:
        #     try:
        #         parent_path = os.path.join(
        #             "sehuatang", fid_json.get(fid, "other"))
        #         if data.get('type_name'):
        #             parent_path = os.path.join(parent_path, data['type_name'])
        #         if '[无码破解]' in data['title']:
        #             parent_path = os.path.join(parent_path, "无码破解")
        #         path_id = self.parent_paths.get(parent_path, None)
        #         if path_id:
        #             pass
        #         else:
        #             paths = await asyncio.wait_for(self.client.path_to_id(parent_path, True), timeout=timeout_time)
        #             path_id = paths[len(paths) - 1].get("id", None)
        #             self.parent_paths[parent_path] = path_id

        #         # paths = await asyncio.wait_for(
        #         #     self.client.path_to_id(
        #         #         os.path.join(parent_path, data['title']), True), timeout=timeout_time)
        #         # path_id = paths[len(paths) - 1].get("id", None)

        #         log.info("pikpak 开启离线下载：{}".format(data["magnet"], ))
        #         task = self.client.offline_download(
        #             data["magnet"],
        #             path_id,
        #             data['title'],
        #         )
        #         result = await asyncio.wait_for(task, timeout=timeout_time)

        #         log.info("pikpak 保存中：{} 保存路径：{} \n 离线任务：{}".format(
        #             data["title"], os.path.join(parent_path, data['title']), result))
        #         task_id = result.get("task").get('id')
        #         file_id = result.get("task").get('file_id')
        #         status_count = 0
        #         while True:
        #             status_count += 1
        #             task = self.client.get_task_status(task_id, file_id)
        #             result = await asyncio.wait_for(task, timeout=10000)
        #             print("{} 的 下载状态：{}".format(data["title"], result))
        #             if DownloadStatus.done == result or DownloadStatus.not_found == result:
        #                 break
        #             await asyncio.sleep(2)
        #             if status_count >= checkCount:
        #                 raise Exception(
        #                     "检测{}次 还是未完成下载 这里判断为下载失败。。。。。。。".format(checkCount))

        #         log.info("pikpak 保存完成：{} 保存路径：{}".format(
        #             data["title"], os.path.join(parent_path, data['title'])))
        #         data['save_pikpak'] = parent_path
        #     except Exception as e:
        #         log.error("pikpak 离线下载失败 error:{}\ndata:{}".format(e, data))
        #         # datas.remove(data)
        #         datas.pop(index)
        #         await asyncio.sleep(2)


if __name__ == "__main__":
    pikpak = PikPak()
    asyncio.run(pikpak.downloads([{
        'magnet': 'magnet:?xt=urn:btih:CBA071E8CCADC4C33263878A599AE000E26AA693'
    }], 36))
