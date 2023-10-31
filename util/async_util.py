import asyncio

from util.config import (
    deletime_enable,
    deletime_num,
    deletime_time,
)

async def deletime_tasks(tasks):
    if deletime_enable and len(tasks) > deletime_num:
        results = []
        results_2 = [tasks[i:i + deletime_num]
                     for i in range(0, len(tasks), deletime_num)]
        for tasks_ in results_2:
            results += await asyncio.gather(*tasks_)
            await asyncio.sleep(deletime_time)
        return results
    else:
        return await asyncio.gather(*tasks)

