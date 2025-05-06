import os
import shutil
import ftplib
import sys
import logging
import platform
from datetime import datetime
import configparser
#=== SETING ===#
global_platform = platform.system()
OBSDOY = False
OBSSAMPLE = 0
PURPOSE = "bncTropRnx"
PPPMODEL = "IF"
global_sigPos,global_noisePos,global_sigTrop,global_noiseTrop = 0.1,100,0.1,3e-6
global_year = int(sys.argv[1])
if global_platform == "Windows":
    global_configFile = r"D:\Tools\bncConfig\baseConfig\tropRnxFilePPP.bnc"
    global_ssrPath = r"E:\PhD_1\4.RTZTD\Data\SSR"
    global_navPath = r"E:\PhD_1\4.RTZTD\Data\NAV"
    global_obsPath = r"E:\PhD_1\4.RTZTD\Data\OBS"
    global_crdFile = r"E:\PhD_1\4.RTZTD\BNC\Model\bnc_16sites.crd"
    global_atxFile = r"E:\PhD_1\4.RTZTD\BNC\Model\igs20.atx"
    global_workDir = r"E:\PhD_1\4.RTZTD\BNC\BCN_RINEX"
cur_time = datetime.now()
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

def setInputNav(configName,year,doy,count,AC):
    navFile = ""
    count = count + 1
    doy = doy - 1
    while count!=0:
        count = count - 1
        doy = doy + 1
        if not os.path.exists(os.path.join(global_navPath,"BRDC00{}_S_{:0>4}{:0>3}0000_01D_MN.rnx".format(AC,year,doy))):
            logging.warning("This Nav file doesn't exist: {}".format(os.path.join(global_navPath,"BRDC00{}_S_{:0>4}{:0>3}0000_01D_MN.rnx".format(AC,year,doy))))
            continue
        navFile = navFile + os.path.join(global_navPath,"BRDC00{}_S_{:0>4}{:0>3}0000_01D_MN.rnx".format(AC,year,doy)) + ","
    if (len(navFile) == 0):
        logging.error("All the Nav Files DO NOT EXIST!!!")
        return False
    _changeValue(configName,"PPP","rinexNav","\"" + navFile[0:-1].replace("\\","/") + "\"")
    return True

def setInputSSR(configName,year,doy,count,AC):
    ssrFile = ""
    filePath = os.path.join(global_ssrPath,"SSRA00{}_S_{:0>4}{:0>3}0000_{:0>2}D_MC.ssr".format(AC,year,doy,count))
    if not os.path.exists(filePath):
        logging.error("This SSR File DOES NOT EXIST!!: {}".format(filePath))
        return False
    ssrFile = filePath
    _changeValue(configName,"PPP","corrFile",ssrFile.replace("\\","/"))
    return True

def setInputObs(configName,year,doy,count,siteList,source,sampling):
    count = count + 1
    doy = doy - 1
    obsFile = ""
    while count!=0:
        count = count - 1
        doy = doy + 1
        for curSite in siteList:
            curObsPath = os.path.join(global_obsPath,"{}_{}_{:0>4}{:0>3}0000_01D_{:0>2}S_MO.rnx".format(curSite,source,year,doy,sampling))
            if OBSDOY:
                curObsPath = os.path.join(global_obsPath,"{:0>3}".format(doy),"{}_{}_{:0>4}{:0>3}0000_01D_{:0>2}S_MO.rnx".format(curSite,source,year,doy,sampling))
            if OBSSAMPLE:
                curObsPath = os.path.join(global_obsPath+"_{:0>2}S".format(sampling),"{}_{}_{:0>4}{:0>3}0000_01D_{:0>2}S_MO.rnx".format(curSite,source,year,doy,sampling))
            if OBSSAMPLE and OBSDOY:
                curObsPath = os.path.join(global_obsPath+"_{:0>2}S".format(sampling),"{:0>3}".format(doy),"{}_{}_{:0>4}{:0>3}0000_01D_{:0>2}S_MO.rnx".format(curSite,source,year,doy,sampling))
            if not os.path.exists(curObsPath):
                logging.warning("This Obs file doesn't exist: {}".format(curObsPath))
                continue
            obsFile = obsFile + "\"" + curObsPath + "\"" + ","
    if (len(obsFile) == 0):
        logging.error("All the Obs Files DO NOT EXIST!!!")
        return False
    _changeValue(configName,"PPP","rinexObs",obsFile[0:-1].replace("\\","/"))
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

def setOutputlogFile(configName,curPath,year,doy,count,ac,system):
    logPath = os.path.join(curPath,"Log")
    if not os.path.exists(logPath):
        os.mkdir(logPath)
    logFile = os.path.join(logPath,"{}_{}_{:>4}{:0>3}_{:0>2}D".format(ac,system,year,doy,count))
    _changeValue(configName,"General","logFile",logFile.replace("\\","/"))

def setOutputPPPFile(configName,curPath,year,doy,count,ac,system):
    PPPPath = os.path.join(curPath,"PPP_{}_{}_{:>4}{:0>3}_{:0>2}D".format(ac,system,year,doy,count))
    if not os.path.exists(PPPPath):
        os.mkdir(PPPPath)
    _changeValue(configName,"Modify","PPPFile",PPPPath.replace("\\","/"))

def setOutputTropFile(configName,curPath,year,doy,count,ac,system):
    TropPath = os.path.join(curPath,"Trop_{}_{}_{:>4}{:0>3}_{:0>2}D".format(ac,system,year,doy,count))
    if not os.path.exists(TropPath):
        os.mkdir(TropPath)
    _changeValue(configName,"PPP","snxtroPath",TropPath.replace("\\","/"))
    _changeValue(configName,"PPP","snxtroCampId",ac)

def setstaTable(configName,siteList):
    staTable = ""
    for cur_site in siteList:
        cur_table = "{},{:.2f},{:.2f},{:.2f},{},{},{},{},{},7777,G:1&C G:2&W R:1&C R:2&P E:1&C E:5&Q C:26&I".format(\
            cur_site,global_sigPos,global_sigPos,global_sigPos*1.5,global_noisePos,global_noisePos,global_noisePos,
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
    year = int(sys.argv[1])
    doy = int(sys.argv[2])
    count = int(sys.argv[3])
    interval = int(sys.argv[4])
    siteList = sys.argv[5].split("_")
    if len(sys.argv) > 6:
        ac = sys.argv[6]
    else:
        ac = "CNE"
    if len(sys.argv) > 7:
        system = sys.argv[7]
    else:
        system = "GEC"
    if len(sys.argv) > 9:
        startTime = sys.argv[8].replace("_"," ")
        endTime = sys.argv[9].replace("_"," ")
    else:
        startTime = ""
        endTime = ""

    os.chdir(global_workDir)
    curDir = os.path.join(global_workDir,"{:0>4}".format(year) + "{:0>3}".format(doy) + "_{:0>2}D".format(count))
    if not os.path.exists(curDir):
        os.mkdir(curDir)
    os.chdir(curDir)
    curConfig = "bncTropRnxFilePPP_{}_{}_{:0>4}{:0>3}_{:0>2}D_{:0>2}S.bnc".format(ac,system,year,doy,count,len(siteList))
    shutil.copy(global_configFile,curConfig)

    #=== INPUTS ===#
    #Nav
    if not setInputNav(curConfig,year,doy,count,"WRD"):
        sys.exit()
    #SSR
    if not setInputSSR(curConfig,year,doy,count,ac+"0"):
        sys.exit()
    #Obs
    if not setInputObs(curConfig,year,doy,count,siteList,"S",5):
        sys.exit()
    #Crd
    if not setInputModel(curConfig):
        sys.exit()
    #=== OUTPUTS ===#
    setOutputlogFile(curConfig,curDir,year,doy,count,ac,system)
    setOutputPPPFile(curConfig,curDir,year,doy,count,ac,system)
    setOutputTropFile(curConfig,curDir,year,doy,count,ac,system)
    #=== PROCESS SETTINGS ===#
    _changeValue(curConfig,"Modify","intervalProcess","{} sec".format(interval))
    _changeValue(curConfig,"Modify","resetInterval","{} sec".format(2*interval))
    _changeValue(curConfig,"Modify","startTime",startTime)
    _changeValue(curConfig,"Modify","endTime",endTime)
    setstaTable(curConfig,siteList)
    setSystem(curConfig,system)
