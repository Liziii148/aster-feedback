"""Broad corpus screening; candidate only, never an automatic sentiment approval."""
import re
SIGNAL=re.compile(r'系统|升级|更新|车机|紫菀|aster|ota|2[.．]1|210|lumo|gpt|语音|导航|地图|快捷|账户|账号|记忆|k歌|ktv|有麦|音乐|播客|音源|小萤|发光小队|车模|问候|露营|尾门|能量回收|动能回收|续航提醒|续航风险|守卫|哨兵|热点|换电|软件|蓝牙|投屏|许愿|功能|空调|屏幕',re.I)
def screen(text):
 hits=list(dict.fromkeys(m.group() for m in SIGNAL.finditer(text)))
 return bool(hits),('命中：'+'、'.join(hits[:12])) if hits else '尚无明确系统信号；保留全部语料，不自动排除'
