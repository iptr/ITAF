from selenium import webdriver
import time
import re
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
import commonlib

DRIVEPATH = "/home/seong/다운로드/chrome/chromedriver"
WAITTIME = 3
KEYCONFPATH = "keyManager.conf"



class KeyManager:
    '''
    This class tests the keymanager web manager.

    This test is performed using Selenium and Chrome.
    '''
    def __init__(self):
        try:
            chrome_option = Options()
            chrome_option.add_argument('--no-sandbox')
            chrome_option.add_argument('ignore-certificate-errors')
            chrome_option.add_argument('--disable-dev-shm-usage')
            # 크롬 드라이버 경로 설정 및 세팅
            self.driver = webdriver.Chrome(executable_path=DRIVEPATH, chrome_options=chrome_option)
            # 페이지 로딩 최대 대기 시간 설정
            self.wait = WebDriverWait(self.driver, WAITTIME)
        except Exception as e:
            print("cccccc")
            print(e)

    def login(self):
        """
        KEYMANAGER LogIn

        ID, PASSWORD기준으로 KEYMANAGER 로그인
        """
        try:
            conf = commonlib.readConfFile(KEYCONFPATH)
            self.driver.get(conf["URL"])
            self.driver.find_element_by_id('loginId').send_keys(conf["ID"])
            self.driver.find_element_by_id("loginPassword").send_keys(conf["PASSWD"])
            self.driver.find_element_by_class_name("loginCenterBottom").click()
        except Exception as e:
            print("ddddddd")

#---------------------------------------- INIT

    def setKeyView(self):
        '''
        키 설정 화면으로 이동

        @return
            True - 성공
            False - 실패
        '''
        try:
            self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/header/div[2]/ul/li[1]"))).click()
        except Exception as e:
            print("View Error")
            return False

        return True

    def setServerView(self):
        '''
        서버 설정 화면으로 이동

        @return
            True - 성공
            False - 실패
        '''
        try:
            self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/header/div[2]/ul/li[2]"))).click()
        except Exception as e:
            print("View Error")
            return False

        return True

#----------------------------------------- VIEW

    def clickAddButton(self):
        '''
        추가 버튼 클릭

        @return
            True - 성공
            False - 실패
        '''
        try:
            # add button click
            self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/article/div[2]/div/div[1]/div[1]/div[3]"))).click()
        except Exception as e:
            # TODO : LOGGING
            print("ADD BUTTON ERROR")
            return False

        return True

    def clickRemoveButton(self):
        '''
        삭제 버튼 클릭

        @return
            True - 성공
            False - 실패
        '''
        try:
            # remove button click
            self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/article/div[2]/div/div[1]/div[1]/div[4]"))).click()
        except Exception as e:
            # TODO : LOGGING
            print("REMOVE BUTTON ERROR")
            return False

        return True

    def clickRefresh(self):
        '''
        새로고침 버튼 클릭

        @return
            True - 성공
            False - 실패

        '''
        try:
            # fresh button click
            self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/article/div[2]/div/div[1]/div[1]/div[1]"))).click()
        except Exception as e:
            # TODO : LOGGING
            print("FRESH BUTTON ERROR")
            return False

        return True

    def checkDuplicate(self,name,row):
        '''
        중복 검사

        @param
            name - 중복 검사를 원하는 객체 명
            row - 중복 검사의 기준이 되는 row
        @return
            True - 중복
            False - 예외, 중복아님
        '''
        # ROW 데이터 받기
        data_list = KeyManager.getRowData(self,row)

        # 등록된 프로세스가 없는 경우
        if len(data_list) == 0:
            return False

        # 현재 등록된 프로세스와 추가할 프로세스 비교
        try:
            if data_list.count(name) != 0:
                return False
        except Exception as e:
            return False

        return True

    def getRowData(self,row):
        '''
        row 데이터 확인

        @param
            row - 데이터를 얻을 기준이 되는 row
        @return
            해당 row의 데이터(실패, 없을 시 길이가 0인 리스트 반환)
        '''
        data_list = []
        try:
            self.wait.until(EC.visibility_of_element_located((By.XPATH,row)))

            data = self.driver.find_elements(By.XPATH,row)

            data_list = [i.get_attribute("title") for i in data]

        except Exception as e:
            print("프로세스 리스트 못 찾았다!")
            pass

        return data_list

    def inputDoubleEnter(self):
        '''
        변경 후 알림 종료를 위해 엔터를 두번 치는 기능

        @return
            True - 성공
            False - 실패
        '''
        try:
            ActionChains(self.driver).send_keys(Keys.ENTER).perform()
            time.sleep(1)
            ActionChains(self.driver).send_keys(Keys.ENTER).perform()
        except Exception as e:
            print("엔터 에러")
            return False

        return True

    def clickObjcet(self,row,name=[]):
        '''
        이름이 일치하는 객체 선택

        @param
            row - 이름이 있는 줄
            name - 선택하고자하는 객체 리스트
        @return
            True - 성공
            False - 실패
        '''
        # 객체 리스트 확인
        data_list = KeyManager.getRowData(self,row=row)

        if len(data_list) == 0:
            return False

        try:
            # 제거할 객체를 지정하지 않은 경우 전체 정책 삭제
            if len(name) == 0:
                self.wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "/html/body/article/div[2]/div/div[2]/div[1]/div/table/tbody/tr/td[1]/input"))).click()
            # 해당 객체에서 제거 하고자 하는 값의 인덱스 추출
            else:
                for i in range(len(name)):
                    index = data_list.index(name[i]) + 1
                    self.wait.until(EC.element_to_be_clickable((By.XPATH,
                                                                "/html/body/article/div[2]/div/div[2]/div[1]/div/table/tbody/tr[%d]/td[1]/input" % (
                                                                    index)))).click()
        except Exception as e:
            # TODO:logging
            return False

        return True

    def clickGroup(self):
        #TODO: 기본 기능 완성 후 그룹 기능 수행
        pass
#------------------------------------------ COMMON UTIL

    def inputKeyName(self,name):
        '''
        새로 만들 키 이름 입력
        @param
            name - 키 이름
        @return
            True - 성공
            False - 실패
        '''
        if KeyManager.checkDuplicate(self,name,row="/html/body/article/div[2]/div/div[2]/div[1]/div/table/tbody/tr/td[2]") == False:
            return False

        try:
            self.wait.until(EC.visibility_of_all_elements_located(
                (By.XPATH, "/html/body/div[6]/div[2]/div[3]/div/div[1]/div[2]/input")))
            self.driver.find_element_by_xpath("/html/body/div[6]/div[2]/div[3]/div/div[1]/div[2]/input").send_keys(name)
        except Exception as e:
            return False

        return True


    def inputKeyExplain(self,msg):
        '''
        새로 만들 키의 설명 추가
        @param
            msg - 설명 적을 메세지
        @return
            True - 성공
            False - 실패
        '''
        try:
            self.wait.until(EC.visibility_of_all_elements_located(
                (By.XPATH, "/html/body/div[6]/div[2]/div[3]/div/div[7]/div[2]/textarea")))
            self.driver.find_element_by_xpath("/html/body/div[6]/div[2]/div[3]/div/div[7]/div[2]/textarea").send_keys(msg)
        except Exception as e:
            return False

        return True

    def selectKeyGroup(self,name):
        '''
        선택한 이름의 그룹을 선택
        @param
            name: 그룹 이름
        @return
            True - 성공
            False - 실패
        '''
        try:
            select = Select(self.driver.find_element_by_xpath('/html/body/div[6]/div[2]/div[3]/div/div[3]/div[2]/select'))

            # 텍스트로 찾기
            select.select_by_visible_text(name)

            # 값으로 찾기
            # value = KeyManager.getRowData()
            # select.select_by_value('1')
        except Exception as e:
            return False

        return True


    def selectExpiration(self,mode = 0,date="",period = 0):
        '''
        기한 선택
        @param
            mode - 0 : 기본값 (2년)
                   1 : 기타 선택
            date - 기타 선택시 작성되는 기간
            period - 0 : 기본값 (일)
                     1 : 월
                     2 : 년
        @return
            True - 성공
            False - 실패
        '''
        try:
            if mode == 1:
                # 기타 선택
                self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/div[6]/div[2]/div[3]/div/div[6]/div[2]/input[2]"))).click()
                # 날짜 입력
                self.wait.until(EC.visibility_of_all_elements_located(
                    (By.XPATH, "/html/body/div[6]/div[2]/div[3]/div/div[6]/div[2]/input[3]")))
                self.driver.find_element_by_xpath("/html/body/div[6]/div[2]/div[3]/div/div[6]/div[2]/input[3]").send_key(date)
                # 일 선택
                if period == 0:
                    pass
                # 월 선택
                elif period == 1:
                    select = Select(
                        self.driver.find_element_by_xpath('/html/body/div[6]/div[2]/div[3]/div/div[6]/div[2]/select'))

                    # 텍스트로 찾기
                    select.select_by_visible_text("개월")
                # 년 선택
                elif period == 2:
                    select = Select(
                        self.driver.find_element_by_xpath('/html/body/div[6]/div[2]/div[3]/div/div[6]/div[2]/select'))

                    # 텍스트로 찾기
                    select.select_by_visible_text("년")
                else:
                    return False
            # 기본값 2년
            elif mode == 0:
                pass
            else:
                raise Exception("선택 못함")
        except Exception as e:
            return False

        return True

    def saveKeyClick(self):
        '''
        저장 버튼 클릭

        @return
            True - 성공
            False - 실패
        '''
        try:
            self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/div[6]/div[3]/div/button[1]"))).click()
        except Exception as e:
            return False

        return True

    def cancelKeyClick(self):
        '''
        닫기 버튼 클릭

        @return
            True - 성공
            False - 실패
        '''
        try:
            self.wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[6]/div[3]/div/button[2]"))).click()
        except Exception as e:
            return False

        return True

    def addKey(self,key_name,group = 0, expiration = 0, explain = False,group_name="",mode=0,date="",period=0,msg=""):
        '''
        키 추가 하는 함수

        @param
            name - 추가할 객체 이름
            group - 추가할 객체 그룹
            expiration - 유효기간(기본값 2년)
            explain - 설명 (사용시 True)
            group_name - 그룹 설정시 선택할 이름
            mode - 0 : 기본값 (2년)
                   1 : 기타 선택
            date - 기타 선택시 작성되는 기간
            period - 0 : 기본값 (일)
                     1 : 월
                     2 : 년
            msg - 설명 시 적을 문구
        @return
            True - 성공
            False - 실패
        '''
        rtn = True

        for i in range(1):
            # 뷰 띄우기
            if KeyManager.setKeyView(self) == False:
                rtn = False
                break
            # 이름 입력
            if KeyManager.inputKeyName(self,key_name) == False:
                rtn = False
                break
            # 그룹 지정
            if group != 0:
                if KeyManager.selectKeyGroup(self,group_name) == False:
                    rtn = False
                    break
            # 유효 기간 설정
            if expiration != 0:
                if KeyManager.selectExpiration(self,mode,date,period) == False:
                    rtn = False
                    break
            # 설명 추가
            if explain != False:
                if KeyManager.inputKeyExpain(self,msg) == False:
                    rtn = False
                    break

        # 비 정상
        if rtn == False:
            KeyManager.cancelKeyClick(self)
        # 정상
        else:
            KeyManager.saveKeyClick(self)

        return rtn

    def removeKey(self,name=[]):
        '''
        객체를 삭제

        @param
            name - 삭제를 원하는 객체 리스트
        @return
            True - 성공
            False - 실패
        '''
        if KeyManager.clickObjcet(self,"/html/body/article/div[2]/div/div[2]/div[1]/div/table/tbody/tr/td[2]",name) == False:
            return False

        if KeyManager.clickRemoveButton(self) == False:
            return False

        if KeyManager.inputDoubleEnter(self) == False:
            return False

        return True

#----------------------------------------- KEY
    def inputServerName(self,name):
        '''
        추가 등록할 서버 이름 입력

        @param
            name - 서버 이름
        @return
            True - 성공
            False - 실패
        '''
        # 중복 검사
        if KeyManager.checkDuplicate(self,name,row="/html/body/article/div[2]/div/div[2]/div[1]/div/table/tbody/tr/td[2]") == False:
            return False

        # 서버 최대 저장 5개
        if len(KeyManager.getRowData(self,row="/html/body/article/div[2]/div/div[2]/div[1]/div/table/tbody/tr/td[2]")) == 5:
            return False

        try:
            self.wait.until(EC.visibility_of_all_elements_located(
                (By.XPATH, "/html/body/div[8]/div[2]/div[3]/div[1]/div[2]/div[2]/input")))
            self.driver.find_element_by_xpath("/html/body/div[8]/div[2]/div[3]/div[1]/div[2]/div[2]/input").send_keys(name)
        except Exception as e:
            return False

        return True
    def inputServerAddr(self,addr):
        '''
        추가 등록할 서버 주소 입력

        @param
            name - 서버 주소
        @return
            True - 성공
            False - 실패
        '''
        try:
            self.wait.until(EC.visibility_of_all_elements_located(
                (By.XPATH, "/html/body/div[8]/div[2]/div[3]/div[1]/div[4]/div[2]/input")))
            self.driver.find_element_by_xpath("/html/body/div[8]/div[2]/div[3]/div[1]/div[4]/div[2]/input").send_keys(addr)
        except Exception as e:
            return False

        return True

    def selectServerGroup(self,name):
        '''
        추가 등록할 서버 그룹 선택

        @param
            name - 그룹 명
        @return
            True - 성공
            False - 실패
        '''
        select = Select(self.driver.find_element_by_xpath('/html/body/div[8]/div[2]/div[3]/div[1]/div[5]/div[2]/select'))

        # 이름으로 찾기
        select.select_by_visible_text(name)

    def selectKey(self,name):
        '''
        추가 등록할 서버 키 선택

        @param
            name - 키 이름
        @return
            True - 성공
            False - 실패
        '''
        select = Select(
            self.driver.find_element_by_xpath('/html/body/div[8]/div[2]/div[3]/div[1]/div[6]/div[2]/select'))

        select.select_by_visible_text(name)

    def inputAgentPass(self,passwd):
        '''
        추가 등록할 서버 에이전트 패스워드 입력

        @param
            passwd - 에이전트 패스워드
        @return
            True - 성공
            False - 실패
        '''
        try:
            # 비밀 번호 입력
            self.wait.until(EC.visibility_of_all_elements_located((By.XPATH,"/html/body/div[8]/div[2]/div[3]/div[2]/div[2]/div[2]/input")))
            self.driver.find_element_by_xpath("/html/body/div[8]/div[2]/div[3]/div[2]/div[2]/div[2]/input").send_keys(passwd)
            # 비밀 번호 재 입력
            self.wait.until(EC.visibility_of_all_elements_located(
                (By.XPATH, "/html/body/div[8]/div[2]/div[3]/div[2]/div[3]/div[2]/input")))
            self.driver.find_element_by_xpath("/html/body/div[8]/div[2]/div[3]/div[2]/div[3]/div[2]/input").send_keys(passwd)
        except Exception as e:
            return False

        return True

    def inputBackupKeyPass(self,passwd):
        '''
        추가 등록할 키 목록 백업 패스워드 입력

        @param
            passwd - 패스워드
        @return
            True - 성공
            False - 실패
        '''
        try:
            # 비밀 번호 입력
            self.driver.find_element_by_xpath("/html/body/div[8]/div[2]/div[3]/div[3]/div[3]/div[2]/input").send_keys(passwd)
            # 비밀 번호 재 입력
            self.driver.find_element_by_xpath("/html/body/div[8]/div[2]/div[3]/div[3]/div[4]/div[2]/input").send_keys(passwd)
        except Exception as e:
            return False

        return True

    def backupKey(self, mode = 0 , passwd = "" ):
        '''
        키 목록 백업 기능 관련 선택

        @param
            mode - 0 : 미사용(기본값)
                   1 : 사용
            passwd: 키 목록 백업 패스워드 입력
        @return
            True - 성공
            False - 실패
        '''
        try:
            if mode == 1:
                self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/div[8]/div[2]/div[3]/div[3]/div[2]/div[2]/input[1]"))).click()
                KeyManager.inputBackupKeyPass(self,passwd)
            elif mode == 0:
                pass
            else:
                raise Exception("mode 설정 실패!")
        except Exception as e:
            return False

        return True

    def saveServerClick(self):
        '''
        저장 버튼 클릭

        @return
            True - 성공
            False - 실패
        '''
        try:
            self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/div[8]/div[3]/div/button[1]"))).click()
        except Exception as e:
            return False

        return True

    def cancelServerClick(self):
        '''
        닫기 버튼 클릭

        @return
            True - 성공
            False - 실패
        '''
        try:
            self.wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[8]/div[3]/div/button[2]"))).click()
        except Exception as e:
            return False

        return True

    def addSever(self,server_name,server_addr,group_name = "",key_name = "",agent_passwd = "",mode = 0,backup_passwd = ""):
        '''
        서버 추가

        @param
            server_name - 등록할 서버 이름
            server_addr - 등록할 서버 주소
            group_name - 지정할 그룹 이름
            key_name - 지정할 키 이름
            agent_passwd - Agent 비밀번호
            mode - 0 : 백업 기능 미사용(기본값)
                   1 : 백업 기능 사용
            backup_passwd: 키 목록 백업 패스워드 입력
        @return
            True - 성공
            False - 실패
        '''
        rtn = True

        for i in range(1):
            if KeyManager.setServerView(self) == False:
                rtn = False
                break
            if KeyManager.clickAddButton(self) == False:
                rtn = False
                break
            if KeyManager.inputServerName(self,server_name) == False:
                rtn = False
                break
            if KeyManager.inputServerAddr(self,server_addr) == False:
                rtn = False
                break
            if KeyManager.selectServerGroup(self,group_name) == False:
                rtn = False
                break
            if KeyManager.selectKey(self,key_name) == False:
                rtn = False
                break
            if KeyManager.inputAgentPass(self,agent_passwd) == False:
                rtn = False
                break
            if KeyManager.backupKey(self,mode,backup_passwd) == False:
                rtn = False
                break

        # 비 정상
        if rtn == False:
            KeyManager.cancelKeyClick(self)
        # 정상
        else:
            KeyManager.saveKeyClick(self)

        return rtn

    def removeServer(self,name=[]):
        '''
        객체를 삭제

        @param
            name - 삭제를 원하는 객체 리스트
        @return
            True - 성공
            False - 실패
        '''
        if KeyManager.clickObjcet(self,"/html/body/article/div[2]/div/div[2]/div[1]/div/table/tbody/tr/td[2]",name) == False:
            return False

        if KeyManager.clickRemoveButton(self) == False:
            return False

        if KeyManager.inputDoubleEnter(self) == False:
            return False

        return True

#----------------------------------------- SERVER
    def showManagementLog(self):
        # 관리 로그 확인
            #키
            #서버
            #그룹
        # TODO : 관리 로그 DB 테이블 확인 및 조회로 해당 값 반환 예정
        # TODO : Key Manager 관련 DB 및 테이블 확인 필요
        pass

    def showKeyLog(self):
        pass

    def showServerLog(self):
        pass

    def showGroupLog(self):
        pass


    def showETCLog(self):
        # 기타 로그 확인
            #관리자 계정
            #방화벽 설정
            #라이센스
            #기타 설정
        # TODO : 관리 로그 DB 테이블 확인 및 조회로 해당 값 반환 예정
        pass

    def showAdminLog(self):
        pass

    def showFireWallLog(self):
        pass

    def showLicenseLog(self):
        pass

    def showETCSettingLog(self):
        pass

#---------------------------------------------------------------------- LOG

if __name__ == '__main__':
    a = KeyManager()
    a.addKey("Abc")