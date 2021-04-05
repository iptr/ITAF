from selenium import webdriver
import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
import commonlib

ONEIPMODE = 1
IPRANGEMODE = 2
IPANYMODE = 3
ACCESS = 1
DENY = 2
DRIVEPATH = "/home/seong/다운로드/chrome/chromedriver"
DCCONFPATH = "DC.conf"
WAITTIME = 3
ALL = 1
KERNEL = 2
APIANDAGENT=3

class WebControl:
    def __init__(self):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('ignore-certificate-errors')
        chrome_options.add_argument('--disable-dev-shm-usage')
        # 크롬 드라이버 경로 설정 및 세팅
        self.driver = webdriver.Chrome(executable_path=DRIVEPATH,chrome_options=chrome_options)
        # 페이지 로딩 최대 대기 시간 설정
        self.wait = WebDriverWait(self.driver,WAITTIME)

    def login(self):
        """
        DC LogIn

        ID, PASSWORD기준으로 DC 매니저 로그인
        """
        #TODO : password 처리 - 암호화해서 config 파일에 저장하는 방향 고민

        conf = commonlib.readDCConfFile(DCCONFPATH)
        self.driver.get(conf["URL"])
        self.driver.find_element_by_id('loginId').send_keys(conf["ID"])
        self.driver.find_element_by_id("loginPassword").send_keys(conf["PASSWD"])
        self.driver.find_element_by_class_name("loginCenterBottom").click()

    def setObjectView(self):
        '''
        DC 매니저 로그인 후 객체 화면 출력

        '''
        try:
            time.sleep(1)
            self.wait.until(EC.element_to_be_clickable((By.XPATH,"//*[@id=\"mainHeader\"]/div[2]/ul/li[3]/span"))).click()
        except Exception as e:
            # TODO : LOGGING
            print("TimeOut!!")
            return False

        return True

    def addObject(self,name):
        '''
        객체 추가

        @param
            name - 객체 이름

        @return
            True - 정상적으로 객체 추가
            False - 추가할 객체가 중복 될 경우
        '''
        # 중복 검사
        if WebControl.checkDuplicateObject(self,name) == True:
            return False

        try:
            # add button click
            self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/article/div[4]/div/div[1]/div[1]/div[3]"))).click()
            # account name box click
            self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/div[4]/div[2]/div/div[1]/div[2]/input"))).click()
            # input account name
            self.wait.until(EC.visibility_of_element_located((By.NAME,"account"))).send_keys(name)
            self.driver.find_element_by_xpath("/html/body/div[4]/div[2]/div/div[3]/div[2]/textarea").click()
            # ok button
            self.driver.find_element_by_xpath("/html/body/div[4]/div[3]/div/button[1]").click()
            self.wait.until(EC.element_to_be_clickable((By.XPATH,"//*[@id=\"confirmMessageOk\"]"))).click()
            self.wait.until(EC.element_to_be_clickable((By.XPATH,"//*[@id=\"alertMessageOk\"]"))).click()
        except Exception as e:
            # TODO : LOGGING
            self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/div[4]/div[3]/div/button[2]"))).click()
            print("TimeOut!!")

        return True

    def getObject(self):
        '''
        객체 계정 가져오기

        @return
            계정의 갯수 반환 - 계정이 존재할 경우
            길이가 0인 array 반환 - 계정이 존재하지 않을 경우
        '''
        object_list = []
        try:
            # 계정 가져오기
            row = self.driver.find_elements(By.XPATH,"/html/body/article/div[4]/div/div[2]/div[2]/div/table/tbody/tr/td[2]")

            # 가져온 계정을 저장
            object_list = [i.text for i in row]
        except Exception as e:
            #TODO: logging
            pass
        return object_list

    def checkDuplicateObject(self,name):
        '''
        계정 중복 유무 확인

        @parma
            name - 계정 이름
        @return
            True - 중복
            False - 중복이 없을 경우
        '''
        # 계정 가져오기
        account_list = WebControl.getObject(self)

        # 객체가 없을 경우
        if len(account_list) == 0:
            return False

        # 존재 여부 확인
        if account_list.count(name) == 0:
            return False

        return True

    def deleteObject(self,name=[]):
        '''
        계정 지우기

        @parmam
            name - 지우고자 하는 계정 리스트

        @return
            True - 성공
            False - 실패
        '''

        # 객체 리스트 받아오기
        object_list = WebControl.getObject(self)
        try:
            # 기본 설정 - 전체 제거
            if len(name) == 0:
                time.sleep(1)
                self.driver.find_element_by_xpath("/ html / body / article / div[4] / div / div[2] / div[1] / div / table / tbody / tr / td[1] / input").click()
            else:
                for i in range(len(name)):
                    try:
                        index = object_list.index(name[i]) + 1
                        self.wait.until(EC.element_to_be_clickable((By.XPATH,
                                                                    "/html/body/article/div[4]/div/div[2]/div[2]/div/table/tbody/tr[%d]/td[1]" % (
                                                                        index)))).click()
                    except Exception as e:
                        # todo:logging
                        return False

            self.wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "/ html / body / article / div[4] / div / div[1] / div[1] / div[4]"))).click()

                # 엔터 입력 (확인 처리)
            if len(WebControl.getObject(self)) > 0:
                self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, "/html/body/div/div[2]/div/button[1]")))
                ActionChains(self.driver).send_keys(Keys.ENTER).perform()

            time.sleep(1)
            ActionChains(self.driver).send_keys(Keys.ENTER).perform()
        except Exception as e:
            #TODO : logging
            print("삭제 실패")
            ActionChains(self.driver).send_keys(Keys.ENTER).perform()

        return True

    def closeDrive(self):
        '''
        DC 매니저 종료
        '''
        self.driver.quit()

    def addObjectGroup(self,name):
        '''
        객체 그룹 추가
        '''
        # TODO : 기본 기능 추가 이후 그룹 수행
        # 그룹 이름 중복 여부 확인
        if WebControl.checkDuplicateGroupList(self,name) == False:
            return False
        try:
            # 그룹 위치
            right_click = self.driver.find_element_by_xpath("/html/body/aside/div[2]/ul/li/a")
            action = ActionChains(self.driver)
            # 그룹 추가를 위해 마우스 오른쪽 클릭
            action.context_click(self.driver.find_element_by_id("all_anchor")).perform()
            self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/ul"))).click()
            time.sleep(2)
            self.wait.until(EC.visibility_of_element_located((By.XPATH,"//input[@id=\"accountGroupDialogName\"]"))).send_keys(name)
            #self.wait.until(EC.presence_of_all_elements_located((By.XPATH,"//input[@id=\"accountGroupDialogName\"]"))).send_keys(name)
            self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/div[4]/div[3]/div/button[1]"))).click()
            self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/div[7]/div[2]/div/button[1]"))).click()
        finally:
            self.driver.quit()

    def setIPView(self):
        '''
        IP 객체 화면 출력

        @return
            True - 정상 출력
            False - 출력 실패
        '''
        # 객체 카테고리 선택
        if WebControl.setObjectView(self) == False:
            return False
        # 객체 카테고리 밑 IP 주소 버튼 클릭
        try:
            self.wait.until(EC.element_to_be_clickable((By.XPATH,"//html/body/header/div[2]/ul/li[3]/div/ul/li[2]"))).click()
        except Exception as e:
            #TODO:LOGGING
            return False

        return True

    def validateIP(self,ip):
        '''
        IPv4 기준 유효성 검사

        @param
            ip - IPv4 주소
        @return
            True - 정상 범주 IP
            False - 정상 범주 IP 가 아닐 경우
        '''
        # IPv4 검증 패턴
        regex = "^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])$"

        # IPv4 패턴 적용 후 검증
        if re.search(regex,ip) is not None:
            return True

        return False

    def checkDuplicateIP(self,condition,ip_addr=[]):
        '''
        IP 객체 중복 여부 확인

        @parmam
            ip_addr - 확인하고자 하는 ip 객체 리스트

        @return
            True - 중복일 경우
            False - 중복이 없을 경우
        '''
        # IP 객체 확인
        ip_list = WebControl.getIPObjetList(self)

        # 객체가 하나도 없는 경우
        if len(ip_list) == 0:
            return False

        # 하나의 아이피만 설정 할 경우
        if condition == ONEIPMODE:
            for i in range(len(ip_addr)):
                if ip_list.count(ip_addr[i]) == 0:
                    return False
        # 아이피 범위 설정 할 경우
        elif condition == IPRANGEMODE:
            split_result = []
            for i in range(len(ip_list)):
                if ip_list[i].count("~") > 0:
                    split_result.append(str(ip_list[i]).replace(" ","").split("~"))

            for i in range(len(split_result)):
                 if split_result[i] == ip_addr:
                     return True
        # Any 설정
        elif condition == IPANYMODE:
            if ip_list.count("Any") == 0:
                return False
        else:
            return True

        return False

    def addIPObject(self,condition,ip_list=[]):
        '''
        IP 객체 추가

        @parmam
            ip_list - 추가하고자 하는 ip 객체 리스트

        @return
            True - 객체 추가 성공
            False - 객체 추가 실패
        '''
        # Any 가 아닌데 입력 IP 가 없을 경우
        if len(ip_list) == 0 and condition != IPANYMODE:
            return False
        # IPv4 검증
        for i in range(len(ip_list)):
            if WebControl.validateIP(self, ip_list[i]) == False:
                return False
        # IP 중복 검사
        if WebControl.checkDuplicateIP(self,condition,ip_list) == True:
            return False

        try:
            # IP 객체 추가 버튼 클릭
            self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/article/div[4]/div/div[1]/div[1]/div[3]"))).click()
            # 단일 IP 추가
            if condition == ONEIPMODE:
                self.wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "/html/body/div[4]/div[2]/div/div[1]/div[2]/input[1]"))).click()
                self.wait.until(EC.visibility_of_element_located((By.XPATH,"/html/body/div[4]/div[2]/div/div[1]/div[2]/input[1]"))).send_keys(
                    ip_list[0])

            # IP 범위 추가
            elif condition == IPRANGEMODE:
                self.wait.until(EC.element_to_be_clickable((By.XPATH,"/ html / body / div[4] / div[2] / div / div[1] / div[2] / div / input[1]"))).click()
                self.wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "/html/body/div[4]/div[2]/div/div[1]/div[2]/input[1]"))).click()
                self.wait.until(EC.visibility_of_element_located((By.XPATH,"/html/body/div[4]/div[2]/div/div[1]/div[2]/input[1]"))).send_keys(
                    ip_list[0])
                self.wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "/html/body/div[4]/div[2]/div/div[1]/div[2]/input[2]"))).click()
                self.wait.until(EC.visibility_of_element_located((By.XPATH,"/html/body/div[4]/div[2]/div/div[1]/div[2]/input[2]"))).send_keys(ip_list[1])

            # 모든 IP일 경우
            elif condition == IPANYMODE:
                self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/div[4]/div[2]/div/div[3]/div[2]/textarea"))).click()
                self.wait.until(EC.element_to_be_clickable((By.XPATH,"/ html / body / div[4] / div[2] / div / div[1] / div[2] / div / input[2]"))).click()
            else:
                return False
            # IP 추가 적용
            time.sleep(1)
            self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/div[4]/div[3]/div/button[1]"))).click()
            time.sleep(1)
            ActionChains(self.driver).send_keys(Keys.ENTER).perform()
            time.sleep(1)
            ActionChains(self.driver).send_keys(Keys.ENTER).perform()
        except Exception as e:
            #TODO:logging
            self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/div[4]/div[3]/div/button[2]"))).click()
            print("객체 추가 실패")
            pass

        return True

    def getIPObjetList(self):
        '''
        IP 객체 반환

        @return
            ip_list 반환 - 객체 가 있을 경우
            길이가 0인 ip_list 반환 - 객체가 없을 경우
        '''
        ip_list = []
        try:
            # IP 객체 위치 설정
            row = self.driver.find_elements(By.XPATH,
                                            "/html/body/article/div[4]/div/div[2]/div[2]/div/table/tbody/tr/td[2]/span")
            # IP 객체 받아오기
            ip_list = [i.get_attribute("title") for i in row]
        except Exception as e:
            #TODO:logging
            pass

        return ip_list

    def removeIPObject(self,ip_list=[]):
        '''
        IP 객체 삭제

        @parmam
            ip_list - 삭제하고자 하는 ip 객체 리스트

        @return
            True - 정상적으로 객체 리스트 반환
            False - 객체 리스트가 존재 하지 않을 때
        '''
        # 객체 리스트 받아 오기
        ip_object = WebControl.getIPObjetList(self)

        index = -1
        if len(ip_object) == 0:
            return False

        try:
            # default 전체 제거
            if len(ip_list) == 0:
                self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/article/div[4]/div/div[2]/div[1]/div/table/tbody/tr/td[1]/input"))).click()
            # 범위 설정 된 IP 객체일 경우
            elif len(ip_list) == 1:
                try:
                    # 지정된 객체의 인덱스 번호 확인
                    index = ip_object.index(ip_list[0]) + 1
                except Exception as e:
                    print(e)
                    return False
            elif len(ip_list) == 2:
                split_result = {}
                # 범위로 지정된 IP 객체 확인
                for i in range(len(ip_object)):
                    if ip_object[i].count("~") > 0:
                        split_result[i]=(str(ip_object[i]).replace(" ","").split("~"))

                # 지우고자 하는 IP 범위가 있는지 확인
                for i in range(len(split_result)):
                    # 해당 IP 객체 인덱스 확인
                     if list(split_result.values())[i] == ip_list:
                         index = int(list(split_result.keys())[i]) + 1

            else:
                print("wrong remove Setting ip")
                return False

            # 전체 삭제가 아닐 경우
            if len(ip_list) != 0:
                self.wait.until(EC.element_to_be_clickable((By.XPATH,
                                                            "/html/body/article/div[4]/div/div[2]/div[2]/div/table/tbody/tr[%d]/td[1]" % (
                                                                index)))).click()

            # 삭제 버튼
            self.wait.until(EC.element_to_be_clickable((By.XPATH,"/ html / body / article / div[4] / div / div[1] / div[1] / div[4]"))).click()
            time.sleep(1)
            ActionChains(self.driver).send_keys(Keys.ENTER).perform()
            time.sleep(1)
            ActionChains(self.driver).send_keys(Keys.ENTER).perform()
            time.sleep(1)
        except Exception as e:
            #TODO:logging
            print("아이피 객체 삭제 실패")
            ActionChains(self.driver).send_keys(Keys.ENTER).perform()

        return True

    def addIPGroup(self,name):
        #TODO:TBD
        pass

    def removeIPGroup(self,name=[]):
        #TODO:TBD
        pass

    def setProcessView(self):
        '''
        프로세스 객체 화면 설정

        @return
            True - 정상 출력
            False - 출력 실패
        '''
        if WebControl.setObjectView(self) == True:
            try:
                self.driver.find_element_by_xpath("/html/body/header/div[2]/ul/li[3]/div/ul/li[3]").click()
            except Exception as e:
                # TODO: Logging
                return False

        return True

    def checkDuplicateProcess(self,name):
        '''
        프로세스 객체들의 객체명 중복 확인

        @parma
            name - 프로세스 객체 이름

        @return
            True - 중복이 없는 경우
            False - 중복, 예외
        '''
        # 현재 등록된 프로세스 리스트 받기
        process_list = WebControl.getProcessList(self)

        # 등록된 프로세스가 없는 경우
        if len(process_list) == 0:
            return True

        # 현재 등록된 프로세스와 추가할 프로세스 비교
        try:
            if process_list.count(name) != 0:
                return False
        except Exception as e:
            return False

        return True

    def getProcessList(self):
        '''
        프로세스 리스트 확인

        @return
            프로세스 리스트 반환 - 요소가 존재 할 경우
            크기가 0인 리스트 반환 - 요소가 존재 하지 않을 경우
        '''
        process_list = []

        try:
            self.wait.until(EC.visibility_of_element_located((By.XPATH,"/html/body/article/div/div/div[2]/div[2]/div/table/tbody/tr/td[2]/span")))

            row = self.driver.find_elements(By.XPATH,"/html/body/article/div/div/div[2]/div[2]/div/table/tbody/tr/td[2]/span")

            process_list = [i.get_attribute("title") for i in row]

        except Exception as e:
            print("프로세스 리스트 못 찾았다!")
            pass

        return process_list

    def addProcess(self,name):
        '''
        프로세스 객체 추가

        @param
            name - 추가하고자 하는 프로세스 객체 이름

        @return
            True - 성공
            False - 실패
        '''
        # 중복 검사
        if WebControl.checkDuplicateProcess(self,name) == False:
            return False
        try:
            # 프로세스 추가
            self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/article/div/div/div[1]/div[1]/div[3]"))).click()

            # 프로세스 명 입력
            self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/div[4]/div[2]/div/div[1]/div[2]/input"))).send_keys(name)

            time.sleep(1)
            self.driver.find_element_by_xpath("/html/body/div[4]/div[3]/div/button[1]").click()
            time.sleep(1)
            ActionChains(self.driver).send_keys(Keys.ENTER).perform()
            time.sleep(1)
            ActionChains(self.driver).send_keys(Keys.ENTER).perform()
        except Exception as e:
            #TODO:logging
            self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/div[4]/div[3]/div/button[2]"))).click()
            print("프로세스 객체 추가 실패")
            pass

    def removeProcess(self,name=[]):
        '''
        프로세스 객체 제거

        @param
            name - 제거하고자 하는 프로세스 객체 리스트

        @return
            True - 성공
            False - 실패
        '''
        process_list = WebControl.getProcessList(self)
        # 프로세스 리스트 존재 여부 확인
        if len(process_list) == 0:
            return False
        try:
            # 삭제할 프로세스를 지정하지 않은 경우
            if len(name) == 0:
                self.wait.until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "/html/body/article/div/div/div[2]/div[1]/div/table/tbody/tr/td[1]/input"))).click()
            # 특정 프로세스를 삭제하는 경우
            else:
                for i in range(len(name)):
                    try:
                        index = process_list.index(name[i]) + 1
                        self.wait.until(EC.element_to_be_clickable((By.XPATH,
                                                                    "/html/body/article/div/div/div[2]/div[2]/div/table/tbody/tr[%d]/td[1]/input" % (
                                                                        index)))).click()
                    except Exception as e:
                        #TODO:logging
                        print("index Error")
                        pass

            self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, "/html/body/article/div/div/div[1]/div[1]/div[4]"))).click()
            time.sleep(1)
            ActionChains(self.driver).send_keys(Keys.ENTER).perform()
            time.sleep(1)
            ActionChains(self.driver).send_keys(Keys.ENTER).perform()
        except Exception as e:
            # todo:logging
            print("프로세스 객체 제거 실패")
            ActionChains(self.driver).send_keys(Keys.ENTER).perform()
            pass

        return True

    def checkDuplicateGroupList(self,name):
        # TODO : 기본 기능 완성 후 그룹 기능 추가
        self.driver.find_element_by_xpath("//*[@id=\"all_anchor\"]")
        row = self.driver.find_elements(By.XPATH, "/ html / body / aside / div[2] / ul / li / ul /li")

        group_list = [(str(i.text).split("(")[0])[:-1] for i in row]


        if group_list.count(name) == 0:
            return True

        return False

    def setPolicyView(self):
        '''
        정책 화면 출력

        @return
            True -정상 출력
            False - 출력 실패
        '''
        try:
            self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/header/div[2]/ul/li[1]/span"))).click()
        except Exception as e:
            #TODO: LOGGING
            return False

        return True

    def getDecryptPolicyObject(self):
        '''
        복호화 정책 객체 확인

        @return
            복호화 정책 객체 리스트
        '''
        policy_list = []

        try:
            self.wait.until(EC.visibility_of_element_located((By.XPATH,"/html/body/article/div[3]/div/div[2]/div[1]/div/table/tbody/tr/td[2]")))
            row = self.driver.find_elements(By.XPATH, "/html/body/article/div[3]/div/div[2]/div[2]/div/table/tbody/tr/td[2]/span")

            policy_list = [i.get_attribute("title") for i in row]
        except Exception as e:
            pass


        return policy_list

    def checkDecryptObject(self,name):
        '''
        복호화 정책 중복 검사

        @return
            True - 중복 없음
            False - 중복,예외
        '''
        #if WebControl.setPolicyView(self) == False:
        #    return False

        try:
            self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/header/div[2]/ul/li[1]/div/ul/li[2]/span"))).click()
        except Exception as e:
            pass

        policy_list = WebControl.getDecryptPolicyObject(self)

        if len(policy_list) == 0:
            return True

        if policy_list.count(name) != 0:
            return False

        return True

    def addDecryptPolicy(self,name,encrypt=1,use_log=1,read_mode=1,account=None,ip_addr=None,process=None,file_path=None,dir=None):
        '''
        복호화 정책 추가(복호화 리스트)

        @param
            name - 정책 이름
            encrypt - 암복호화 허용 여부
            use_log - 로그 기록 사용 여부
            read_mode - 읽기 권한
            account - 계정 명
            ip_addr - IP 주소
            process - 프로세스 객체
            file_path - 대상 경로
            dir - 디렉토리 여부 확인

        @return
            True - 성공
            False - 실패
        '''
        if WebControl.setPolicyView(self) == False:
            return False

        if WebControl.checkDecryptObject(self, name) == False:
            return False

        try:
            self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/header/div[2]/ul/li[1]/div/ul/li[2]/span"))).click()

            self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/article/div/div/div[1]/div[1]/div[3]"))).click()
            # 정책명 설정
            self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/div/div[2]/div/div[2]/div[2]/input"))).send_keys(name)
            # 동작 설정

            if encrypt == ACCESS:
                if use_log == DENY:
                    self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/div[4]/div[2]/div/div[6]/div[2]/label[2]/input"))).click()
                else:
                    pass
            elif encrypt == DENY:
                self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/div[4]/div[2]/div/div[5]/div[2]/label[2]/input"))).click()
                if read_mode == ACCESS:
                    self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/div[4]/div[2]/div/div[7]/div[2]/label[2]/input"))).click()
                else:
                    pass
            else:
                pass
            WebControl.setDecryptPolicyTarget(self,account,ip_addr,process,file_path,dir)
            self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/div[4]/div[3]/div/button[1]"))).click()
            ActionChains(self.driver).send_keys(Keys.ENTER).perform()
            time.sleep(1)
            ActionChains(self.driver).send_keys(Keys.ENTER).perform()
        except Exception as e:
            self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/div[4]/div[3]/div/button[2]"))).click()
            return False

        return True

    def addAccessPolicy(self,name,read_mode = True,write_mode = True, create_mode = True, delete_mode = True,account=None,ip_addr=None,process=None,file_path=None,dir=None):
        '''
        접근 통제 정책 추가(접근 통제 리스트)

        @param
            name - 접근 통제 정책 이름

        @return
            True - 성공
            False - 실패
        '''
        if WebControl.setPolicyView(self) == False:
            return False

        if WebControl.checkAccessObject(self, name) == False:
            return False

        try:
            self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/header/div[2]/ul/li[1]/div/ul/li[3]"))).click()

            self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/article/div/div/div[1]/div[1]/div[3]"))).click()
            # 정책명 설정
            self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/div/div[2]/div/div[2]/div[2]/input"))).send_keys(name)
            # 제어 유형 설정
            if read_mode == False:
                self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/div[4]/div[2]/div/div[9]/div[2]/input[1]"))).click()
            if write_mode == False:
                self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/div[4]/div[2]/div/div[9]/div[2]/input[2]"))).click()
            if create_mode == False:
                self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/div[4]/div[2]/div/div[9]/div[2]/input[3]"))).click()
            if delete_mode == False:
                self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/div[4]/div[2]/div/div[9]/div[2]/input[4]"))).click()

            # 대상 설정
            WebControl.setAccessPolicyTarget(self,account,ip_addr,process,file_path,dir)
            self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/div[4]/div[3]/div/button[1]"))).click()
            ActionChains(self.driver).send_keys(Keys.ENTER).perform()
            time.sleep(1)
            ActionChains(self.driver).send_keys(Keys.ENTER).perform()
        except Exception as e:
            self.wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[4]/div[3]/div/button[2]"))).click()
            return False

        return True

    def checkAccessObject(self,name):
        '''
        접근 통제 정책 중복 검사

        @param
            name - 중복 검사를 실시하는 객체 명

        @return
            True - 중복 없음
            False - 중복,예외
        '''
        try:
            self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/header/div[2]/ul/li[1]/div/ul/li[3]/span"))).click()
        except Exception as e:
            pass


        policy_list = WebControl.getAccessPolicyObject(self)

        if len(policy_list) == 0:
            return True

        if policy_list.count(name) != 0:
            return False

        return True

    def getAccessPolicyObject(self):
        '''
        접근 통제 정책 리스트 확인 (정책 적용 x)

        @return
            접근 통제 정책 객체 리스트
        '''
        policy_list = []

        try:
            self.wait.until(EC.visibility_of_element_located(
                (By.XPATH, "/html/body/article/div[3]/div/div[2]/div[2]/div/table/tbody/tr/td[2]")))
            row = self.driver.find_elements(By.XPATH,
                                            "/html/body/article/div[3]/div/div[2]/div[2]/div/table/tbody/tr/td[2]/span")

            policy_list = [i.get_attribute("title") for i in row]
        except Exception as e:
            pass
        print(policy_list)
        return policy_list

    def setDecryptPolicyTarget(self,account=None,ip_addr=None,process=None,file_path=None,dir=None):
        '''
        복호화 대상 선택

        @param
            account - 계정 명
            ip_addr - IP 주소
            process - 프로세스 객체
            file_path - 대상 경로
            dir - 디렉토리 여부 확인

        @return
            성공 - True
            실패 - False
        '''
        try:
            if account is not None:
                account_list = []
                # 클릭
                self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/div/div[2]/div/div[9]/div[2]/button"))).click()
                # 리스트 업
                try:
                    self.wait.until(EC.visibility_of_element_located((By.XPATH,"/html/body/div[7]/div[2]/div[4]/div/div[2]/div[1]/div/table/tbody/tr/td[2]")))
                    row = self.driver.find_elements(By.XPATH,"/html/body/div/div[2]/div[4]/div/div[2]/div[2]/div/table/tbody/tr/td[2]/span")
                    account_list = [i.get_attribute("title") for i in row]
                except Exception as e:
                    #TODO: logging
                    pass

                # 리스트 compare
                try:
                    index = account_list.index(account) + 1
                    # 해당 인덱스 선택
                    self.wait.until(EC.element_to_be_clickable((By.XPATH,
                                                                "/ html / body / div[7] / div[2] / div[4] / div / div[2] / div[2] / div / table / tbody / tr[%d] / td[1] / input" % (
                                                                    index)))).click()
                    self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, "/html/body/div[7]/div[3]/div/button[1]"))).click()
                except Exception as e:
                    #TODO:logging
                    self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, "/html/body/div[7]/div[3]/div/button[2]"))).click()
                    pass

            # IP 주소를 사용하는 경우
            if ip_addr is not None:
                ip_list = []
                # 클릭
                self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "/html/body/div/div[2]/div/div[10]/div[2]/button"))).click()
                # 리스트 업
                try:
                    self.wait.until(EC.visibility_of_element_located(
                        (By.XPATH, "/html/body/div[7]/div[2]/div[4]/div/div[2]/div[1]/div/table/tbody/tr/td[2]")))
                    row = self.driver.find_elements(By.XPATH,
                                                    "/html/body/div[7]/div[2]/div[4]/div/div[2]/div[2]/div/table/tbody/tr/td[2]/span")
                    ip_list = [i.get_attribute("title") for i in row]
                except Exception as e:
                    # TODO: logging
                    pass

                # 리스트 compare
                try:
                    index = ip_list.index(ip_addr) + 1
                    # 해당 인덱스 선택
                    self.wait.until(EC.element_to_be_clickable((By.XPATH,
                                                                "/ html / body / div[7] / div[2] / div[4] / div / div[2] / div[2] / div / table / tbody / tr[%d] / td[1] / input" % (
                                                                    index)))).click()
                    self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, "/html/body/div[7]/div[3]/div/button[1]"))).click()
                except Exception as e:
                    # TODO:logging
                    print("ip 타겟 설정 실패!")
                    self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, "/html/body/div[7]/div[3]/div/button[2]"))).click()
                    pass

            # 프로세스를 사용하는 경우
            if process is not None:
                process_list = []
                # 클릭
                self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "/html/body/div/div[2]/div/div[11]/div[2]/button"))).click()
                # 리스트 업
                try:
                    self.wait.until(EC.visibility_of_element_located((By.XPATH,"/html/body/div[7]/div[2]/div[4]/div/div[2]/div[1]/div/table/tbody/tr/td[2]")))
                    row = self.driver.find_elements(By.XPATH,
                                                    "/html/body/div/div[2]/div[4]/div/div[2]/div[2]/div/table/tbody/tr/td[2]/span")
                    process_list = [i.get_attribute("title") for i in row]
                except Exception as e:
                    # TODO: logging
                    pass
                # 리스트 compare
                try:
                    index = process_list.index(process) + 1
                    # 해당 인덱스 선택
                    self.wait.until(EC.element_to_be_clickable((By.XPATH,
                                                                "/ html / body / div[7] / div[2] / div[4] / div / div[2] / div[2] / div / table / tbody / tr[%d] / td[1] / input" % (
                                                                    index)))).click()
                    self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, "/html/body/div[7]/div[3]/div/button[1]"))).click()
                except Exception as e:
                    # TODO:logging
                    self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, "/html/body/div[7]/div[3]/div/button[2]"))).click()
                    pass


            # 경로가 지정된 경우
            if file_path is not None:
                try:
                    self.wait.until(EC.element_to_be_clickable(
                        (By.XPATH, "/html/body/div/div[2]/div/div[12]/div[2]/input"))).send_keys(file_path)
                except Exception as e:
                    # TODO:logging
                    pass
                if dir is not None:
                    try:
                        self.wait.until(EC.element_to_be_clickable(
                            (By.XPATH, "/html/body/div/div[2]/div/div[12]/div[2]/div/input"))).click()
                    except Exception as e:
                        # TODO:logging
                        pass
            else:
                pass
        except Exception as e:
            #todo:logging
            print("타겟 설정 실패")
            pass

        return True

    def setAccessPolicyTarget(self,account=None,ip_addr=None,process=None,file_path=None,dir=None):
        '''
        접근통제 대상 선택

        @param
            account - 계정 명
            ip_addr - IP 주소
            process - 프로세스 객체
            file_path - 대상 경로
            dir - 디렉토리 여부 확인

        @return
            성공 - True
            실패 - False
        '''
        try:
            if account is not None:
                account_list = []
                # 클릭
                self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/div/div[2]/div/div[5]/div[2]/button"))).click()
                # 리스트 업
                try:
                    self.wait.until(EC.visibility_of_element_located((By.XPATH,"/html/body/div[7]/div[2]/div[4]/div/div[2]/div[1]/div/table/tbody/tr/td[2]")))
                    row = self.driver.find_elements(By.XPATH,"/html/body/div/div[2]/div[4]/div/div[2]/div[2]/div/table/tbody/tr/td[2]/span")
                    account_list = [i.get_attribute("title") for i in row]
                except Exception as e:
                    #TODO: logging
                    pass

                # 리스트 compare
                try:
                    index = account_list.index(account) + 1
                    # 해당 인덱스 선택
                    self.wait.until(EC.element_to_be_clickable((By.XPATH,
                                                                "/ html / body / div[7] / div[2] / div[4] / div / div[2] / div[2] / div / table / tbody / tr[%d] / td[1] / input" % (
                                                                    index)))).click()
                    self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, "/html/body/div[7]/div[3]/div/button[1]"))).click()
                except Exception as e:
                    #TODO:logging
                    self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, "/html/body/div[7]/div[3]/div/button[2]"))).click()
                    pass

            # IP 주소를 사용하는 경우
            if ip_addr is not None:
                ip_list = []
                # 클릭
                self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "/html/body/div/div[2]/div/div[6]/div[2]/button"))).click()
                # 리스트 업
                try:
                    self.wait.until(EC.visibility_of_element_located(
                        (By.XPATH, "/html/body/div[7]/div[2]/div[4]/div/div[2]/div[1]/div/table/tbody/tr/td[2]")))
                    row = self.driver.find_elements(By.XPATH,
                                                    "/html/body/div[7]/div[2]/div[4]/div/div[2]/div[2]/div/table/tbody/tr/td[2]/span")
                    ip_list = [i.get_attribute("title") for i in row]
                except Exception as e:
                    # TODO: logging
                    pass

                # 리스트 compare
                try:
                    index = ip_list.index(ip_addr) + 1
                    # 해당 인덱스 선택
                    self.wait.until(EC.element_to_be_clickable((By.XPATH,
                                                                "/ html / body / div[7] / div[2] / div[4] / div / div[2] / div[2] / div / table / tbody / tr[%d] / td[1] / input" % (
                                                                    index)))).click()
                    self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, "/html/body/div[7]/div[3]/div/button[1]"))).click()
                except Exception as e:
                    # TODO:logging
                    print("ip 타겟 설정 실패!")
                    self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, "/html/body/div[7]/div[3]/div/button[2]"))).click()
                    pass

            # 프로세스를 사용하는 경우
            if process is not None:
                process_list = []
                # 클릭
                self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "/html/body/div/div[2]/div/div[7]/div[2]/button"))).click()
                # 리스트 업
                try:
                    self.wait.until(EC.visibility_of_element_located((By.XPATH,"/html/body/div[7]/div[2]/div[4]/div/div[2]/div[1]/div/table/tbody/tr/td[2]")))
                    row = self.driver.find_elements(By.XPATH,
                                                    "/html/body/div/div[2]/div[4]/div/div[2]/div[2]/div/table/tbody/tr/td[2]/span")
                    process_list = [i.get_attribute("title") for i in row]
                except Exception as e:
                    # TODO: logging
                    pass
                # 리스트 compare
                try:
                    index = process_list.index(process) + 1
                    # 해당 인덱스 선택
                    self.wait.until(EC.element_to_be_clickable((By.XPATH,
                                                                "/ html / body / div[7] / div[2] / div[4] / div / div[2] / div[2] / div / table / tbody / tr[%d] / td[1] / input" % (
                                                                    index)))).click()
                    self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, "/html/body/div[7]/div[3]/div/button[1]"))).click()
                except Exception as e:
                    # TODO:logging
                    self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, "/html/body/div[7]/div[3]/div/button[2]"))).click()
                    pass


            # 경로가 지정된 경우
            if file_path is not None:
                try:
                    self.wait.until(EC.element_to_be_clickable(
                        (By.XPATH, "/html/body/div/div[2]/div/div[8]/div[2]/input"))).send_keys(file_path)
                except Exception as e:
                    # TODO:logging
                    pass
                if dir is not None:
                    try:
                        self.wait.until(EC.element_to_be_clickable(
                            (By.XPATH, "/html/body/div[4]/div[2]/div/div[8]/div[2]/div/input"))).click()
                    except Exception as e:
                        # TODO:logging
                        pass
            else:
                pass
        except Exception as e:
            #todo:logging
            print("타겟 설정 실패")
            pass

        return True

    def removeDecryptPolicy(self,name=[]):
        '''
        복호화 정책 제거

        @param
            name - 복호화 정책 중 제거 하고자 하는 객체 리스트

        @return
            True - 성공
            False - 실패
        '''
        # 정책 리스트 확인
        policy_list = WebControl.getDecryptPolicyObject(self)
        try:
            # 제거할 정책을 지정하지 않은 경우 전체 정책 삭제
            if len(name) == 0:
                self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/article/div/div/div[2]/div[1]/div/table/tbody/tr/td[1]"))).click()
            # 해당 정책에서 제거 하고자 하는 값의 인덱스 추출
            else :
                try:
                    for i in range(len(name)):
                        index = policy_list.index(name[i]) + 1
                        self.wait.until(EC.element_to_be_clickable((By.XPATH,"/ html / body / article / div / div / div[2] / div[2] / div / table / tbody / tr[%d] / td[1] / input"%(index)))).click()
                except Exception as e:
                    #TODO:logging
                    pass
            # 제거
            self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/article/div/div/div[1]/div[1]/div[4]"))).click()
            time.sleep(1)
            ActionChains(self.driver).send_keys(Keys.ENTER).perform()
            time.sleep(1)
            ActionChains(self.driver).send_keys(Keys.ENTER).perform()
        except Exception as e:
            #TODO:logging
            print("정책 제거 실패")
            ActionChains(self.driver).send_keys(Keys.ENTER).perform()

        return True

    def removeAccessPolicy(self,name=[]):
        '''
        접근 통제 정책 제거

        @param
            name - 접근 통제 정책 중 제거 하고자하는 객체 리스트

        @return
            True - 성공
            False - 실패
        '''
        # 정책 리스트 확인
        policy_list = WebControl.getAccessPolicyObject(self)
        try:
            # 제거할 정책을 지정하지 않은 경우 전체 정책 삭제
            if len(name) == 0:
                self.wait.until(EC.element_to_be_clickable((By.XPATH,"/ html / body / article / div[3] / div / div[2] / div[1] / div / table / tbody / tr / td[1] / input"))).click()
            # 해당 정책에서 제거 하고자 하는 값의 인덱스 추출
            else :
                for i in range(len(name)):
                    index = policy_list.index(name[i]) + 1
                    self.wait.until(EC.element_to_be_clickable((By.XPATH,
                                                                "/ html / body / article / div / div / div[2] / div[2] / div / table / tbody / tr[%d] / td[1] / input"%(index)))).click()
            # 제거
            self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/article/div/div/div[1]/div[1]/div[4]"))).click()
            time.sleep(1)
            ActionChains(self.driver).send_keys(Keys.ENTER).perform()
            time.sleep(1)
            ActionChains(self.driver).send_keys(Keys.ENTER).perform()

        except Exception as e:
            #TODO:logging
            ActionChains(self.driver).send_keys(Keys.ENTER).perform()
            print("접근 통제 정책 제거 실패")

        return True
    def setDecryptPolicy(self,name=[]):
        '''
        정책 추가(복호화 정책 대상)

        @param
            name - 정책 추가 시 선택해야 하는 복호화 정책 리스트

        @return
            True - 추가 성공
            False - 추가 실패
        '''
        try:
            # 추가 버튼 클릭
            self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/article/div[3]/div/div[1]/div[1]/div[3]"))).click()

            # 정책 리스트 반환
            policy_list = WebControl.getDecryptPolicyList(self)

            # 추가 가능한 정책이 없는 경우
            if len(policy_list) == 0:
                return False

            # 전체 선택
            if len(name) == 0:
                self.wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "/html/body/div/div[2]/div/div[3]/div/div[2]/div[1]/div/table/tbody/tr/td[1]/input"))).click()
            # 전체 선택이 아닌 경우
            else:
                for i in range(len(name)):
                    try:
                        index = policy_list.index(name[i]) + 1
                        self.wait.until(EC.element_to_be_clickable((By.XPATH,
                                                                    "/ html / body / div[4] / div[2] / div / div[3] / div / div[2] / div[2] / div / table / tbody / tr[%d] / td[1]" % (
                                                                        index)))).click()

                    except Exception as e:
                        print(e)
                        return False

            self.wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div/div[3]/div/button[1]"))).click()
            self.wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/article/div/div/div[1]/div[1]/div[11]"))).click()
            ActionChains(self.driver).send_keys(Keys.ENTER).perform()
            time.sleep(1)
            ActionChains(self.driver).send_keys(Keys.ENTER).perform()

        except Exception as e:
            #TODO:LOGGING
            self.wait.until(EC.element_to_be_clickable((By.XPATH,"/ html / body / div[4] / div[3] / div / button[2]"))).click()
            pass

        return True

    def setAccessPolicy(self,name=[]):
        '''
        접근 통제 정책 추가

        @param
            name - 정책 추가 시 선택해야 하는 접근 통제 정책 리스트

        @return
            True - 추가 성공
            False - 추가 실패
        '''
        try:
            self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/article/div[3]/div/div[1]/div[1]/div[3]"))).click()
            self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/div[3]/div[2]/div/div[1]/ul/li[2]"))).click()

            policy_list = WebControl.getAccessPolicyList(self)

            # 추가 가능한 정책이 없는 경우
            if len(policy_list) == 0:
                return False
            # 전체 선택
            if len(name) == 0:
                self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/div[3]/div[2]/div/div[2]/div/div[2]/div[1]/div/table/tbody/tr/td[1]/input"))).click()
            # 특정 정책 선택
            else:
                for i in range(len(name)):
                    try:
                        index = policy_list.index(name[i]) + 1
                        self.wait.until(EC.element_to_be_clickable((By.XPATH, "/ html / body / div / div[2] / div / div[2] / div / div[2] / div[2] / div / table / tbody / tr[%d] / td[1]"%(index)))).click()
                    except Exception as e:
                        #todo:logging
                        print(e)
                        return False


            self.wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div/div[3]/div/button[1]"))).click()
            self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/article/div/div/div[1]/div[1]/div[11]"))).click()
            ActionChains(self.driver).send_keys(Keys.ENTER).perform()
            time.sleep(1)
            ActionChains(self.driver).send_keys(Keys.ENTER).perform()
        except Exception as e:
            #TODO:LOGGING
            self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "/ html / body / div[4] / div[3] / div / button[2]"))).click()
            pass

        return True

    def removePolicy(self,name=[]):
        '''
        정책 제거 (정책 적용)

        @param
            name - 제거 하고자 하는 정책 리스트
        @return
            True - 성공
            False - 실패
        '''
        try:
            policy_list = WebControl.getPolicyList(self)

            # 전체 선택
            if len(name) == 0:
                self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "/html/body/article/div[3]/div/div[2]/div[1]/div/table/tbody/tr/td[1]"))).click()
            # 특정 정책 선택
            else:
                for i in range(len(name)):
                    index = policy_list.index(name[i]) + 1
                    self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/article/div[3]/div/div[2]/div[2]/div/table/tbody/tr[%d]/td[1]"%(index)))).click()

            self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/article/div[3]/div/div[1]/div[1]/div[4]"))).click()
            self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/article/div[3]/div/div[1]/div[1]/div[11]"))).click()
            time.sleep(1)
            ActionChains(self.driver).send_keys(Keys.ENTER).perform()
            time.sleep(1)
            ActionChains(self.driver).send_keys(Keys.ENTER).perform()
        except Exception as e:
            #todo:logging
            ActionChains(self.driver).send_keys(Keys.ENTER).perform()
            print("policy remove fail")
            pass

        return True

    def getDecryptPolicyList(self):
        '''
        복호화 정책 리스트 확인 (정책 적용)

        @return
            정책 리스트 반환 - 정책 리스트가 존재 할 때
            크기가 0인 정책 리스트 반환 - 정책 리스트가 존재 하지 않을 때
        '''
        policy_list = []
        try:
            self.wait.until(EC.visibility_of_element_located((By.XPATH,"/html/body/div/div[2]/div/div[3]/div/div[2]/div[2]/div/table/tbody/tr/td[2]/span")))
            row = self.driver.find_elements(By.XPATH, "/html/body/div/div[2]/div/div[3]/div/div[2]/div[2]/div/table/tbody/tr/td[2]/span")

            policy_list = [i.get_attribute("title") for i in row]
        except Exception as e:
            pass
        print(policy_list)
        return policy_list

    def getAccessPolicyList(self):
        '''
        접근 통제 정책 리스트 확인 (정책 적용)

        @return
            정책 리스트 반환 - 정책 리스트가 존재 할 때
            크기가 0인 정책 리스트 반환 - 정책 리스트가 존재 하지 않을 때
        '''

        try:
            self.wait.until(EC.visibility_of_element_located((By.XPATH,"/html/body/div/div[2]/div/div[2]/div/div[2]/div[2]/div/table/tbody/tr/td[2]/span")))
            row = self.driver.find_elements(By.XPATH,
                                            "/html/body/div/div[2]/div/div[2]/div/div[2]/div[2]/div/table/tbody/tr/td[2]/span")

            policy_list = [i.get_attribute("title") for i in row]


        except Exception as e:
            return False

        return policy_list

    def getPolicyList(self):
        '''
        정책 객체 확인

        @return
            정책 리스트 반환 - 정책 리스트가 존재 할 때
            크기가 0인 정책 리스트 반환 - 정책 리스트가 존재 하지 않을 때
        '''
        policy_list = []
        try:
            # 정책 객체 리스트 위치 설정
            row = self.driver.find_elements(By.XPATH,"/html/body/article/div[3]/div/div[2]/div[2]/div/table/tbody/tr/td[3]/span")

            # 정책 객체 리스트 받기
            policy_list = [i.get_attribute("title") for i in row]

        except Exception as e:
            #TODO:logging
            pass

        return policy_list

    def setPriority(self,name,order = 1):
        '''
        정책 우선 순위 변경

        @param
            name - 우선 순위를 변경하고자 하는 객체 이름
            order - 우선 순위

        @return
            True - 성공
            False - 실패
        '''
        try:
            # 정책 객체 리스트 받아오기
            policy_list = WebControl.getPolicyList(self)

            # 지정된 객체의 인덱스 번호 확인
            index = policy_list.index(name) + 1
            # 변화 시켜야 할 값 확인
            changed_index = index - order

            # 인덱스 값에 해당하는 객체를 선택
            self.driver.find_element_by_xpath("/ html / body / article / div[3] / div / div[2] / div[2] / div / table / tbody / tr[%d] / td[1]"%(index)).click()
            # 우선순위를 제일 위로 올릴 경우
            if order == 1:
                self.driver.find_element_by_xpath("/html/body/article/div[3]/div/div[1]/div[1]/div[6]").click()
            # 우선순위를 제일 밑으로 내릴 경우
            elif order == len(policy_list):
                self.driver.find_element_by_xpath("/html/body/article/div[3]/div/div[1]/div[1]/div[9]").click()

            # 우선 순위를 낮추는 경우
            elif changed_index < 0:
                for _ in range(abs(changed_index)):
                    self.driver.find_element_by_xpath("/html/body/article/div[3]/div/div[1]/div[1]/div[8]").click()
            # 우선 순위를 올리는 경우
            elif changed_index > 0:
                for _ in range(changed_index):
                    self.driver.find_element_by_xpath("/html/body/article/div[3]/div/div[1]/div[1]/div[7]").click()
            self.driver.find_element_by_xpath("/html/body/article/div[3]/div/div[1]/div[1]/div[11]").click()
            time.sleep(1)
            ActionChains(self.driver).send_keys(Keys.ENTER).perform()
            time.sleep(1)
            ActionChains(self.driver).send_keys(Keys.ENTER).perform()
        except Exception as e:
            #TODO:logging
            print("우선순위 에러")
            pass

        return True

    def setSeverView(self):
        '''
        서버 목록 확인

        @return
            True - 성공
            False - 실패
        '''
        try:
            self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/header/div[2]/ul/li[2]/span"))).click()
        except Exception as e:
            #TODO:logging
            return False
        return True

    def getServerList(self):
        '''
        등록되어 있는 서버 목록 획득

        @return
            현재 등록된 서버 목록 리스트
        '''
        server_list = []

        try:
            self.wait.until(EC.visibility_of_element_located((By.XPATH,"/html/body/article/div[3]/div[2]/div/div[2]/div[1]/div/table/tbody/tr/td[2]")))

            row = self.driver.find_elements(By.XPATH,"/html/body/article/div[3]/div[2]/div/div[2]/div[2]/div/table/tbody/tr/td[2]/span")

            server_list = [i.get_attribute("title") for i in row]

        except Exception as e:
            #todo:logging
            pass

        return server_list

    def getKeyMangerList(self):
        server_list = []

        try:
            self.wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div/div[2]/div[2]/div/div[2]/div[1]/div/table/tbody/tr/td[1]/input")))

            row = self.driver.find_elements(By.XPATH,
                                            "/html/body/div/div[2]/div[2]/div/div[2]/div[2]/div/table/tbody/tr/td[2]/input")

            server_list = [i.get_attribute("value") for i in row]

        except Exception as e:
            # todo:logging
            print("키 관리 시스템 목록 read 실패!")
            print(e)
            pass

        return server_list

    def removeServerObject(self,name=[]):
        '''
        삭제하고자 하는 서버 목록 삭제

        @param
            name - 삭제를 원하는 객체 리스트

        @return
            True - 성공
            False - 실패
        '''
        if WebControl.setSeverView(self) == False:
            return False

        server_list = WebControl.getServerList(self)

        if len(server_list) == 0:
            return False

        try:
            if len(name) == 0:
                self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/article/div[3]/div[2]/div/div[2]/div[1]/div/table/tbody/tr/td[1]/input"))).click()
            else:
                for i in range(len(name)):
                    index = server_list.index(name[i]) + 1

                    self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/article/div[3]/div[2]/div/div[2]/div[2]/div/table/tbody/tr[%d]/td[1]/input"%(index)))).click()

            self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/article/div[3]/div[2]/div/div[1]/div[1]/div[4]"))).click()
            time.sleep(1)
            ActionChains(self.driver).send_keys(Keys.ENTER).perform()
            time.sleep(1)
            ActionChains(self.driver).send_keys(Keys.ENTER).perform()

        except Exception as e:
            #todo:logging
            return False

        return True

    def startServer(self, name=[], condition = 1):
        '''
        원하는 서버를 실행

        @param
            name - 실행을 원하는 객체 리스트
            condition - 모듈 실행 플래그 ( 1 - 전체, 2 - 커널, 3 - API/Agent)

        @return
            True - 성공
            False - 실패
        '''
        if WebControl.setSeverView(self) == False:
            return False

        server_list = WebControl.getServerList(self)

        if len(server_list) == 0:
            return False

        try:
            if len(name) == 0:
                self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/article/div[3]/div[2]/div/div[2]/div[1]/div/table/tbody/tr/td[1]/input"))).click()
            else:
                for i in range(len(name)):
                    index = server_list.index(name[i]) + 1

                    self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/article/div[3]/div[2]/div/div[2]/div[2]/div/table/tbody/tr[%d]/td[1]/input"%(index)))).click()

            # 실행
            self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/article/div[3]/div[2]/div/div[1]/div[1]/div[6]"))).click()
            # 전체 모듈 실행
            if condition == ALL:
                self.wait.until(EC.element_to_be_clickable((By.XPATH,"/ html / body / ul[1] / li[3]"))).click()
            # 커널 모듈 실행
            elif condition == KERNEL:
                self.wait.until(EC.element_to_be_clickable((By.XPATH,"/ html / body / ul[1] / li[4]"))).click()
            # API/Agent 모듈 실행
            elif condition == APIANDAGENT:
                self.wait.until(EC.element_to_be_clickable((By.XPATH,"/ html / body / ul[1] / li[5]"))).click()
            else:
                #todo: 해당 객체를 실행시키지 못하였다고 logging
                self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/div[8]"))).click()

            time.sleep(1)
            ActionChains(self.driver).send_keys(Keys.ENTER).perform()
            time.sleep(1)
            ActionChains(self.driver).send_keys(Keys.ENTER).perform()

        except Exception as e:
            #todo:logging
            print("server start fail")
            pass

    def stopServer(self,name=[],condition = 1):
        '''
        원하는 서버를 정지

        @param
            name - 정지를 원하는 객체 리스트

        @return
            True - 성공
            False - 실패
        '''
        if WebControl.setSeverView(self) == False:
            return False

        server_list = WebControl.getServerList(self)

        if len(server_list) == 0:
            return False

        try:
            if len(name) == 0:
                self.wait.until(EC.element_to_be_clickable((By.XPATH,
                                                            "/html/body/article/div[3]/div[2]/div/div[2]/div[1]/div/table/tbody/tr/td[1]/input"))).click()
            else:
                for i in range(len(name)):
                    index = server_list.index(name[i]) + 1

                    self.wait.until(EC.element_to_be_clickable((By.XPATH,
                                                                "/html/body/article/div[3]/div[2]/div/div[2]/div[2]/div/table/tbody/tr[%d]/td[1]/input" % (index)))).click()
                # 실행
                self.wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "/html/body/article/div[3]/div[2]/div/div[1]/div[1]/div[7]"))).click()
                # 전체 모듈 실행
                if condition == ALL:
                    self.wait.until(EC.element_to_be_clickable((By.XPATH, "/ html / body / ul[2] / li[3]"))).click()
                # 커널 모듈 실행
                elif condition == KERNEL:
                    self.wait.until(EC.element_to_be_clickable((By.XPATH, "/ html / body / ul[2] / li[4]"))).click()
                # API/Agent 모듈 실행
                elif condition == APIANDAGENT:
                    self.wait.until(EC.element_to_be_clickable((By.XPATH, "/ html / body / ul[2] / li[5]"))).click()
                else:
                    # todo: 해당 객체를 실행시키지 못하였다고 logging
                    self.wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[8]"))).click()

                time.sleep(1)
                ActionChains(self.driver).send_keys(Keys.ENTER).perform()
                time.sleep(1)
                ActionChains(self.driver).send_keys(Keys.ENTER).perform()

        except Exception as e:
            #todo:logging
            print("server stop fail")
            pass

    def addServerObject(self,name=[],protocol=[],module_info = []):
        '''
        서버 객체 추가

        @return
            True - 성공
            False - 실패
        '''
        if WebControl.setSeverView(self) == False:
            return False

        try:
            # 키 관리 서버 에서 값 확인
            self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/article/div[3]/div[2]/div/div[1]/div[1]/div[9]"))).click()

            # 서버 리스트 확인
            server_list = WebControl.getKeyMangerList(self)

            if len(server_list) == 0:
                return False

            # 이름 없을 시 전체 선택
            if len(name) == 0:
                self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/div/div[2]/div[2]/div/div[2]/div[1]/div/table/tbody/tr/td[1]/input"))).click()
                for i in range(len(server_list)):
                    self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/div/div[2]/div[2]/div/div[2]/div[2]/div/table/tbody/tr[%d]/td[6]/div/label[2]"%(i+1)))).click()
                    self.wait.until(EC.element_to_be_clickable((By.XPATH,
                                                                "/html/body/div/div[2]/div[2]/div/div[2]/div[2]/div/table/tbody/tr[%d]/td[7]/div/label[1]" % (
                                                                            i + 1)))).click()
            # 이름 값 확인 및 선택
            else:
                for i in range(len(name)):
                    index = server_list.index(name[i]) + 1

                    self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/div/div[2]/div[2]/div/div[2]/div[2]/div/table/tbody/tr[%d]/td[1]/input"%(index)))).click()
                    protocol = commonlib.adjustLength(name,protocol)

                    # 통신 프로토콜(TCP(0),UDP(1)) 선택
                    if protocol[i] == 0:
                        self.wait.until(EC.element_to_be_clickable((By.XPATH,
                                                                    "/html/body/div/div[2]/div[2]/div/div[2]/div[2]/div/table/tbody/tr[%d]/td[6]/div/label[2]/input"%(index)))).click()
                    elif protocol[i] == 1:
                        self.wait.until(EC.element_to_be_clickable((By.XPATH,
                                                                    "/html/body/div/div[2]/div[2]/div/div[2]/div[2]/div/table/tbody/tr[%d]/td[6]/div/label[1]/input"%(index)))).click()
                    else:
                        raise Exception("프로토콜 선택 실패")
                    module_info = commonlib.adjustLength(name,module_info)
                    # 모듈 정보(커널(0), API(1), Agent(2) ,커널과 API(3), 커널과 Agent(4), API 와 Agent(5), 모두 선택 (6)) 선택
                    if module_info[i] == 0:
                        self.driver.find_element_by_xpath("/html/body/div/div[2]/div[2]/div/div[2]/div[2]/div/table/tbody/tr[%d]/td[7]/div/label[1]/input"%(index)).click()
                    elif module_info[i] == 1:
                        self.driver.find_element_by_xpath("/html/body/div/div[2]/div[2]/div/div[2]/div[2]/div/table/tbody/tr[%d]/td[7]/div/label[2]/input"%(index)).click()
                    elif module_info[i] == 2:
                        self.driver.find_element_by_xpath("/html/body/div/div[2]/div[2]/div/div[2]/div[2]/div/table/tbody/tr[%d]/td[7]/div/label[3]/input"%(index)).click()
                    elif module_info[i] == 3:
                        self.driver.find_element_by_xpath("/html/body/div/div[2]/div[2]/div/div[2]/div[2]/div/table/tbody/tr[%d]/td[7]/div/label[1]/input"%(index)).click()
                        self.driver.find_element_by_xpath(
                            "/html/body/div/div[2]/div[2]/div/div[2]/div[2]/div/table/tbody/tr[%d]/td[7]/div/label[2]/input" % (
                                index)).click()
                    elif module_info[i] == 4:
                        self.driver.find_element_by_xpath("/html/body/div/div[2]/div[2]/div/div[2]/div[2]/div/table/tbody/tr[%d]/td[7]/div/label[1]/input"%(index)).click()
                        self.driver.find_element_by_xpath("/html/body/div/div[2]/div[2]/div/div[2]/div[2]/div/table/tbody/tr[%d]/td[7]/div/label[3]/input"%(index)).click()
                    elif module_info[i] == 5:
                        self.driver.find_element_by_xpath("/html/body/div/div[2]/div[2]/div/div[2]/div[2]/div/table/tbody/tr[%d]/td[7]/div/label[2]/input"%(index)).click()
                        self.driver.find_element_by_xpath("/html/body/div/div[2]/div[2]/div/div[2]/div[2]/div/table/tbody/tr[%d]/td[7]/div/label[3]/input"%(index)).click()
                    elif module_info[i] == 6:
                        self.driver.find_element_by_xpath(
                            "/html/body/div/div[2]/div[2]/div/div[2]/div[2]/div/table/tbody/tr[%d]/td[7]/div/label[1]/input" % (
                                index)).click()
                        self.driver.find_element_by_xpath(
                            "/html/body/div/div[2]/div[2]/div/div[2]/div[2]/div/table/tbody/tr[%d]/td[7]/div/label[2]/input" % (
                                index)).click()
                        self.driver.find_element_by_xpath("/html/body/div/div[2]/div[2]/div/div[2]/div[2]/div/table/tbody/tr[%d]/td[7]/div/label[3]/input"%(index)).click()
                    else:
                        raise Exception("모듈 선택 실패")

            # 저장 버튼 클릭
            self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/div/div[3]/div/button[1]"))).click()
            time.sleep(1)
            self.wait.until(EC.visibility_of_element_located((By.XPATH,"/ html / body / div / div[1]")))
            response_text = self.driver.find_element(By.XPATH,"/ html / body / div / div[1]").text
            ActionChains(self.driver).send_keys(Keys.ENTER).perform()
            if response_text == "모듈이 선택되지 않았습니다.":
                raise Exception("대상 저장 실패")
            # 엔터
            time.sleep(1)
            ActionChains(self.driver).send_keys(Keys.ENTER).perform()

        except Exception as e:
            #todo:logging
            print(e)
            # 실패 시 해당 창 닫기
            self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/div/div[3]/div/button[2]"))).click()
            pass

        return True

    def serverBasicInfo(self):
        pass

    def encryptDirectory(self,path):
        ####test code
        self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/article/div[3]/div[2]/div/div[2]/div[2]/div/table/tbody/tr[1]/td[1]/input"))).click()
        # 추가 버튼
        self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/article/div[4]/div[2]/div/div[1]/div[1]/div[3]"))).click()
        self.wait.until(EC.element_to_be_clickable((By.XPATH,"/html/body/div/div[2]/div[2]/div[5]/div[2]/button"))).click()
        self.driver.find_element_by_id(path).click()
        time.sleep(1)
        pass

if __name__ == '__main__':
    c = WebControl()
    c.login()
    c.setSeverView()
    # c.addServerObject(name=["linux","jy","windows","asdf"],protocol=[1,0,1],module_info=[2,3,6])
    # c.startServer(["linux","windows"],1)
    # c.stopServer(["linux"], 1)
    # c.stopServer(["windows"], 2)
    # c.startServer(["windows"], 2)
    # c.startServer(["linux"], 3)
    # c.stopServer(["linux"], 3)
    # c.removeServerObject(["asdf","linux"])
    # c.removeServerObject()
    c.encryptDirectory("C:\home\ENC0")
    # c.encryptDirectory("C:\home\ENC0")
    # c.setPolicyView()
    # c.addAccessPolicy("test1")
    # c.addAccessPolicy("test2",read_mode=False)
    # c.addAccessPolicy("test3",write_mode=False)
    # c.addAccessPolicy("test4",create_mode=False)
    # c.addAccessPolicy("test5", delete_mode=False)
    # c.addAccessPolicy("test6",read_mode=False,delete_mode=False)
    # c.addAccessPolicy("test7",account="jycho",ip_addr="10.77.161.167",process="vi",file_path="/home/seong",dir=1)
    # c.removeAccessPolicy(["test2","test4"])
    # c.removeAccessPolicy()
    # c.addDecryptPolicy("test1")
    # c.addDecryptPolicy("test2",use_log=2)
    # c.addDecryptPolicy("test3",encrypt=2)
    # c.addDecryptPolicy("test4",encrypt=2,read_mode=2)
    # c.addDecryptPolicy("test5",account="jycho",ip_addr="10.77.161.167",process="vi",file_path="/home/seong",dir=1)
    # c.removeDecryptPolicy(["test2","test4"])
    # c.removeDecryptPolicy()
    # c.addAccessPolicy("ddddd",read_mode=False,create_mode=False,account="test123111",process="vi")
    # c.addDecryptPolicy("ddd123112123213",dir=1,ip_addr="192.168.4.190",process="tail")
    # c.setObjectView()
    # c.addObject("jyjyjy23")
    #
    # c.setIPView()
    # c.addIPObject(2,["10.77.161.121","10.77.161.123"])
    # c.addIPObject(1,["192.168.3.221"])
    # c.addIPObject(3)
    # c.removeIPObject(["10.77.161.121","10.77.161.123"])
    # c.removeIPObject(["192.168.3.221"])
    # c.addIPObject(1,["192.168.3.221"])
    # c.removeIPObject()
    # #c.removeIPObject(["192.168.3.221","192.168.3.254"])
    # #print(c.checkDuplicateIP(2,["192.168.3.221","192.168.3.254"]))
    # #c.setIPCondition(3)
    # #ip = ["192.168.3.221","192.168.3.224"]
    # #c.setIPCondition(2,ip)
    # #c.setIPCondition(1,ip)
    #
    # c.setObjectView()
    # c.addObject("test")
    # c.deleteObject(["test"])
    # c.addObject("test1")
    # c.addObject("test2")
    # c.addObject("test3")
    # c.deleteObject()

    # c.addObject("test2")
    # c.addObject("test3")
    # c.deleteObject(["jyjyjy23"])
    # c.deleteObject(["absfcsawefdse6","absfcsawefdse5"])
    # c.deleteObject(["jyjyjy23","test123111"])
    # #c.addObjectGroup("asdfasdf")
    #
    # c.setPolicyView()
    # test = ['test1','test2']
    # c.setDecryptPolicy(test)
    # test = ["test3","test4","test5"]
    # c.setAccessPolicy(test)
    # c.setDecryptPolicy()
    # c.setAccessPolicy()
    # c.setPriority("test4")
    # c.setPriority("test1",3)
    # c.setPriority("test4",5)
    # c.setPriority("test5",2)
    # c.setPriority("test3")
    # c.removePolicy(["test3","test1"])
    # c.removePolicy()
    # #t = ["d"]
    # c.removePolicy()
    #
    #
    # c.setProcessView()
    # c.addProcess("vi")
    # c.addProcess("cd")
    # c.addProcess("pwd")
    # c.addProcess("tcpdump")
    # c.addProcess("netstat")
    #
    # c.removeProcess(["cd","tcpdump"])
    # c.removeProcess()
    # #time.sleep(3)
    # #c.addPolicy()
    # #time.sleep(2)
    # #c.getDecryptPolicyList()
    c.closeDrive()

