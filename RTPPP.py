import os
import shutil
import ftplib
import sys
import logging
import platform
from datetime import datetime
import configparser
import subprocess
#=== SETING ===#
global_platform = platform.system()
OBSDOY = False
OBSSAMPLE = 0
PURPOSE = "bncTropRnx"
PPPMODEL = "IF"
global_sigPos,global_noisePos,global_sigTrop,global_noiseTrop = 0.1,0.1,0.1,8e-4
global_year = datetime.now().year
global_stream_url = "ntrip.data.gnss.ga.gov.au:2101"
global_username,global_password = "yuyin","Upcee1211%2521"
if global_platform == "Windows":
    global_configFile = r"D:\Tools\bncConfig\baseConfig\tropRTPPP.bnc"
    global_ssrPath = r"E:\PhD_1\4.RTZTD\BNC\BCN_RINEX"
    global_navPath = r"E:\PhD_1\4.RTZTD\Data\NAV"
    global_obsPath = r"E:\PhD_1\4.RTZTD\Data\OBS"
    global_sp3Path = r"E:\PhD_1\4.RTZTD\Data\SP3"
    global_clkPath = r"E:\PhD_1\4.RTZTD\Data\CLK"
    global_biaPath = r"E:\PhD_1\4.RTZTD\Data\BIA"
    global_crdFile = r"E:\PhD_1\4.RTZTD\BNC\Model\bnc_16sites.crd"
    global_atxFile = r"E:\PhD_1\4.RTZTD\BNC\Model\igs20.atx"
    global_workDir = r"E:\PhD_1\4.RTZTD\BNC\BCN_RT"
elif global_platform == "Linux":
    global_configFile = "/D6/junjie/Tools/bncConfig/baseConfig/tropRnxFilePPP.bnc"
    global_ssrPath = "/D6/junjie/Data/{:0>4}/SSR".format(global_year)
    global_navPath = "/D6/junjie/Data/{:0>4}/NAV".format(global_year)
    global_obsPath = "/D6/junjie/Data/{:0>4}/OBS_30S".format(global_year)
    global_crdFile = "/D6/junjie/Project/A-RTZTD/BNC_RINEX/bnc_16sites.crd"
    global_atxFile = "/D6/junjie/Project/A-RTZTD/BNC_RINEX/igs20.atx"
    global_workDir = "/D6/junjie/Project/A-RTZTD/BNC_RINEX/TEST"
    global_software = "/D6/junjie/Software/BNC/BNC_250503/bnc"
    global_sp3Path = "/D6/junjie/Data/{:0>4}/SP3".format(global_year)
    global_clkPath = "/D6/junjie/Data/{:0>4}/CLK".format(global_year)
    global_biaPath = "/D6/junjie/Data/{:0>4}/BIA".format(global_year)
if not os.path.exists(global_ssrPath):
    os.mkdir(global_ssrPath)
if not os.path.exists(global_navPath):
    os.mkdir(global_navPath)
if not os.path.exists(global_obsPath):
    os.mkdir(global_obsPath)
if not os.path.exists(global_sp3Path):
    os.mkdir(global_ssrPath)
if not os.path.exists(global_clkPath):
    os.mkdir(global_clkPath)
if not os.path.exists(global_biaPath):
    os.mkdir(global_biaPath)
cur_time = datetime.now()
if not os.path.exists(global_workDir):
    os.mkdir(global_workDir)
global_logfile = os.path.join(global_workDir,"{}_{:0>4d}{:0>2d}{:0>2d}_{:0>2d}{:0>2d}{:0>2d}.pylog".format(PURPOSE,cur_time.year,cur_time.month,cur_time.day,cur_time.hour,cur_time.minute,cur_time.second))
logging.basicConfig(level=logging.DEBUG,filename=global_logfile,filemode="w",format="%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")

def _changeValue(configName,section,key,value):
    config = configparser.ConfigParser()
    config.optionxform = lambda option: option
    config.read(configName)
    config.set(section,key,value)
    with open(configName, 'w') as configfile:
        config.write(configfile)
    configfile.close()

def _appendValue(configName,section,key,value):
    config = configparser.RawConfigParser()
    config.optionxform = lambda option: option
    config.read(configName)
    curValue = config.get(section,key)
    config.set(section,key,curValue+" "+value)
    with open(configName, 'w') as configfile:
        config.write(configfile)
    configfile.close()

def setInputNav(configName,AC):
    mountPoints = "//{}:{}@{}/BCEP00BKG0 RTCM_3.3 DEU 50.0900 8.6600 no 2, ".format(global_username,\
                                                                                  global_password,global_stream_url)
    _appendValue(configName,"General","mountPoints",mountPoints)
    return True

def setInputSSR(configName,AC):
    mountPoints = "//{}:{}@{}/SSRA00{} RTCM_3.1 FRA 43.5600 1.4800 no 2, ".format(global_username,\
                                                                                  global_password,global_stream_url,
                                                                                  AC)
    _appendValue(configName,"General","mountPoints",mountPoints)
    _changeValue(configName,"PPP","corrMount","SSRA00{}".format(AC))
    return True

def setInputObs(configName,siteList):
    mountPoints = ""
    for curSite in siteList:
        mountPoints = mountPoints + "//{}:{}@{}/{}0 RTCM_3.3 {} 0.0000 0.0000 no 2, ".format(global_username,\
                                                                                  global_password,global_stream_url,
                                                                                  curSite,curSite[-3:])
    _appendValue(configName,"General","mountPoints",mountPoints)
    return True

def setInputModel(configName):
    if not os.path.exists(global_crdFile):
        logging.error("The CRD File DOES NOT EXIST!!!: {}".format(global_crdFile))
        return False
    if not os.path.exists(global_atxFile):
        logging.error("The ATX File DOES NOT EXIST!!!: {}".format(global_atxFile))
        return False
    _changeValue(configName,"PPP","crdFile",global_crdFile.replace("\\","/"))
    _changeValue(configName,"PPP","antexFile",global_atxFile.replace("\\","/"))
    return True

def setOutputlogFile(configName,curPath,year,month,day,ac,system):
    logPath = os.path.join(curPath,"Log")
    if not os.path.exists(logPath):
        os.mkdir(logPath)
    logFile = os.path.join(logPath,"{}_{}_{:>4}{:0>2}{:0>2}".format(ac,system,year,month,day))
    _changeValue(configName,"General","logFile",logFile.replace("\\","/"))

def setOutputPPPFile(configName,curPath,year,month,day,ac,system):
    PPPPath = os.path.join(curPath,"PPP_{}_{}_{:>4}{:0>2}{:0>2}".format(ac,system,year,month,day))
    if not os.path.exists(PPPPath):
        os.mkdir(PPPPath)
    _changeValue(configName,"Modify","PPPFile",PPPPath.replace("\\","/"))

def setOutputTropFile(configName,curPath,year,month,day,ac,system):
    TropPath = os.path.join(curPath,"Trop_{}_{}_{:>4}{:0>2}{:0>2}".format(ac,system,year,month,day))
    if not os.path.exists(TropPath):
        os.mkdir(TropPath)
    _changeValue(configName,"PPP","snxtroPath",TropPath.replace("\\","/"))
    _changeValue(configName,"PPP","snxtroCampId",ac)

def setOutputSaveFile(curConfig,isSaveFile = [0,0,0,0,0],ac = "HJJ0"):
    if isSaveFile[0]:
        _changeValue(curConfig,"General","rnxPath",global_obsPath.replace("\\","/"))
        _changeValue(curConfig,"General","rnxSampl","{} sec".format(1))
        _changeValue(curConfig,"General","rnxIntr","{} day".format(1))
        _changeValue(curConfig,"General","rnxVersion","{}".format(3))
    else:
        _changeValue(curConfig,"General","rnxPath","")
    if isSaveFile[1]:
        _changeValue(curConfig,"General","ephPath",global_navPath.replace("\\","/"))
        _changeValue(curConfig,"General","ephIntr","{} day".format(1))
        _changeValue(curConfig,"General","ephVersion","{}".format(3))
    else:
        _changeValue(curConfig,"General","ephPath","")
    if isSaveFile[2]:
        _changeValue(curConfig,"General","corrPath",global_ssrPath.replace("\\","/"))
        _changeValue(curConfig,"General","corrIntr","{} day".format(1))
    else:
        _changeValue(curConfig,"General","corrPath","")
    if isSaveFile[3]:
        uploadMountpointsOut = "\",,,2,,,IGS20,RTCM-SSR,2,{}.SP3,{}.CLK,{}.BIA,,,,0 byte(s),\"".format(\
            os.path.join(global_sp3Path,"{}MGXRTS$".format(ac) + "{" + "V3PROD" + "}"),
            os.path.join(global_clkPath,"{}MGXRTS$".format(ac) + "{" + "V3PROD" + "}"),
            os.path.join(global_biaPath,"{}MGXRTS$".format(ac) + "{" + "V3PROD" + "}"))
        _changeValue(curConfig,"General","uploadMountpointsOut",uploadMountpointsOut.replace("\\","/"))
        _changeValue(curConfig,"General","uploadAntexFile",global_atxFile.replace("\\","/"))
        _changeValue(curConfig,"General","cmbStreams","\"SSRA00{} {} 1  \"".format(ac,ac[0:-1]))
        _changeValue(curConfig,"General","cmbMethod","Kalman Filter")
        _changeValue(curConfig,"General","cmbBds","2")
        _changeValue(curConfig,"General","cmbGal","2")
        _changeValue(curConfig,"General","cmbGlo","2")
        _changeValue(curConfig,"General","cmbGps","2")
    else:
        _changeValue(curConfig,"General","uploadMountpointsOut","\"\"")
        _changeValue(curConfig,"General","cmbStreams","\"\"")
def setstaTable(configName,siteList):
    staTable = ""
    for cur_site in siteList:
        cur_table = "{}0,{:.2f},{:.2f},{:.2f},{:.2f},{:.2f},{:.2f},{},{},7777,G:12&CWPSLX R:12&CP E:1&CBX E:5&QIX C:26&IQX".format(\
            cur_site,global_sigPos,global_sigPos,global_sigPos*1.5,global_noisePos,global_noisePos,global_noisePos*1.5,
            global_sigTrop,global_noiseTrop)
        staTable = staTable + "\"" + cur_table + "\"" + ","
    _changeValue(configName,"PPP","staTable",staTable[0:-1])

def setSystem(configName,system):
    if PPPMODEL == "IF":
        if "G" in system:
            _changeValue(configName,"PPP","lcGPS","P3&L3")
        else:
            _changeValue(configName,"PPP","lcGPS","no")
        if "E" in system:
            _changeValue(configName,"PPP","lcGalileo","P3&L3")
        else:
            _changeValue(configName,"PPP","lcGalileo","no")
        if "C" in system:
            _changeValue(configName,"PPP","lcBDS","P3&L3")
        else:
            _changeValue(configName,"PPP","lcBDS","no")
    if PPPMODEL == "UDUC":
        if "G" in system:
            _changeValue(configName,"PPP","lcGPS","Pi&Li")
        else:
            _changeValue(configName,"PPP","lcGPS","no")
        if "E" in system:
            _changeValue(configName,"PPP","lcGalileo","Pi&Li")
        else:
            _changeValue(configName,"PPP","lcGalileo","no")
        if "C" in system:
            _changeValue(configName,"PPP","lcBDS","Pi&Li")
        else:
            _changeValue(configName,"PPP","lcBDS","no")

if __name__ == '__main__':
    siteList = sys.argv[1].split("_")
    interval = int(sys.argv[2])
    if len(sys.argv) > 3:
        ac = sys.argv[3]
    else:
        ac = "CNE"
    if len(sys.argv) > 4:
        system = sys.argv[4]
    else:
        system = "GEC"
    if len(sys.argv) > 5:
        calMode = sys.argv[5]
    else:
        calMode = "Static"
    if len(sys.argv) > 6:
        isSaveFile = [int(i) for i in sys.argv[6].split("_")] #OBS_NAV_SSR_SP3_CLK
    else:
        isSaveFile = 0
    
    os.chdir(global_workDir)
    curDir = os.path.join(global_workDir,"{:0>4}{:0>2}{:0>2}".format(cur_time.year,cur_time.month,cur_time.day))
    if not os.path.exists(curDir):
        os.mkdir(curDir)
    os.chdir(curDir)
    if siteList[0] != "NONE":
        curConfig = "bncTropRnxFilePPP_{}_{}_{:0>4}{:0>2}{:0>2}_{:0>2}S.bnc".format(ac,system,cur_time.year,cur_time.month,cur_time.day,len(siteList))
    else:
        curConfig = "bncTropRnxFilePPP_{}_{}_{:0>4}{:0>2}{:0>2}_SAVE_{:0>2}S.bnc".format(ac,system,cur_time.year,cur_time.month,cur_time.day,len(siteList)-1)
    shutil.copy(global_configFile,curConfig)
    _changeValue(curConfig,"General","mountPoints","")
    if siteList[0] == "NONE":
        _changeValue(curConfig,"PPP","dataSource"," ")
        siteList.remove("NONE")
    #=== INPUTS ===#
    #Nav
    if not setInputNav(curConfig,ac):
        sys.exit()
    #SSR
    if not setInputSSR(curConfig,ac+"0"):
        sys.exit()
    #Obs
    if len(siteList) != 0:
        if not setInputObs(curConfig,siteList):
            sys.exit()
    #Crd
    if not setInputModel(curConfig):
        sys.exit()
    #=== OUTPUTS ===#
    setOutputlogFile(curConfig,curDir,cur_time.year,cur_time.month,cur_time.day,ac,system)
    setOutputPPPFile(curConfig,curDir,cur_time.year,cur_time.month,cur_time.day,ac,system)
    setOutputTropFile(curConfig,curDir,cur_time.year,cur_time.month,cur_time.day,ac,system)
    setOutputSaveFile(curConfig,isSaveFile,ac+"0")
    #=== PROCESS SETTINGS ===#
    _changeValue(curConfig,"Modify","intervalProcess","{} sec".format(interval))
    if interval < 5:
        resetInterval = 10
    else:
        resetInterval = 2*interval
    _changeValue(curConfig,"Modify","resetInterval","{} sec".format(resetInterval))
    _changeValue(curConfig,"Modify","filterMode",calMode)
    if len(siteList) != 0:
        setstaTable(curConfig,siteList)
    setSystem(curConfig,system)
    #=== LAUNCH ===#
    cmd = "{} --conf ./{} --nw".format(global_software,curConfig)
    # try:
    #     subprocess.getstatusoutput(cmd)
    # except OSError:
    #     logging.error("RUN FAILED!!!: {}".format(cmd))
