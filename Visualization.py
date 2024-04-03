import os
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import seaborn as sns
import re
import openpyxl
import streamlit as st
import time
from dataclasses import dataclass
import locale
from abc import ABC, abstractmethod # abstract class

class Tester:
    # Consts
    DEFAULT_ORDER_LEADTIME : int = 8
    
    # Datas
    _uploadedJiwonFile = None
    _uploadedOrderVersusBaljuFile = None
    _jiwonDf : pd.DataFrame = None
    _orderVersusBaljuDf : pd.DataFrame = None
    
    # Elements
    _sidebar = st.empty()
    _uploadTab = None
    _summaryTab = None
    _horizontalAnalysisTab = None
    _verticalAnalysisTab = None
    _rawDataJiwonTab = None
    _rawDataOrderVersusBaljuTab = None

    
    def __init__(self):
        locale.setlocale(locale.LC_ALL, '')
            
        self._uploadTab, self._summaryTab, self._horizontalAnalysisTab, self._verticalAnalysisTab, self._rawDataJiwonTab, self._rawDataOrderVersusBaljuTab = st.tabs(["파일업로드", "요약", "수평분석", "수직분석", "로데이터(지원판단서)", "로데이터(오더대비발주현황)"])
        
        with self._uploadTab:
            with st.expander("파일업로드", expanded=True):
                self._uploadedJiwonFile = st.file_uploader("**암호해제 필수!!** 지원판단서 가공파일을 업로드하세요.")
                self._uploadedOrderVersusBaljuFile = st.file_uploader("**암호해제 필수!!** 오더대비발주현황 가공파일을 업로드하세요.")
        
        # 파일 업로드 완료 체크
        for i in range(0,100):
            if (self._uploadedJiwonFile is not None) and (self._uploadedOrderVersusBaljuFile is not None) :
                self.OnFileUploaded()
                break
            else:
                time.sleep(3)
        
        
    def OnFileUploaded(self):
        if self._uploadedJiwonFile is None:
            raise Exception("지원판단서 파일이 없습니다.")
        if self._uploadedOrderVersusBaljuFile is None:
            raise Exception("오더대비발주현황 파일이 없습니다.")

        self._jiwonDf = pd.read_excel(self._uploadedJiwonFile)
        self._orderVersusBaljuDf = pd.read_excel(self._uploadedOrderVersusBaljuFile)
        
        availableWeeks = [item for item in list(self._jiwonDf.columns) if "WK" in item] # "WK"가 들어간 놈들만 걸러내기
        (minWeek, maxWeek) = self.GetMinMaxWeek(availableWeeks)
        
        availablePartNumbers = self._jiwonDf["PART_NO"].unique().tolist()
    
        (startWeekSelected, endWeekSelected) = ("", "")
        partsListSelected = ""
        submitBtn = ""
        
        with self._uploadTab:        
            with st.form("조회조건 설정"):
                st.title("조회조건 설정")
                (startWeekSelected, endWeekSelected) = st.select_slider("데이터 조회 시작, 종료주차 선택", 
                                                                        options = availableWeeks,
                                                                        value = (minWeek, maxWeek))
                partsListSelected = st.multiselect("품번 선택", 
                                                    options = availablePartNumbers)
                
                orderLeadTime = st.text_input("오더 리드타임 (주 수) 입력",
                                              value = self.DEFAULT_ORDER_LEADTIME,
                                              max_chars=2,
                                              help="이번주에 오더를 내면 몇 주 뒤에 현지에 도착하는지")
                
                submitted = st.form_submit_button("지원판단서 <=> 오더물량 비교분석")

                if submitted:
                    time.sleep(2)
                    self.ShowDataWithCondition(startWeekSelected=startWeekSelected,
                                               endWeekSelected=endWeekSelected,
                                               orderLeadTime=orderLeadTime,
                                               #searchMode=searchMode,
                                               #vdrCodeAndName=vdrCodeAndName,
                                               partsListSelected=partsListSelected)
                    
        

    
    
    def ShowDataWithCondition(self, **kwargs):
        startWeekSelected:str = kwargs.get("startWeekSelected")
        endWeekSelected:str = kwargs.get("endWeekSelected")
        orderLeadTime:int = int(kwargs.get("orderLeadTime"))
        #searchMode:str = kwargs.get("searchMode")
        #vdrCodesAndNames:list = kwargs.get("vdrCodeAndName")
        partsListSelected:list = kwargs.get("partsListSelected")

        
        
        weeks:list[str] = self.GetConsecutiveWeeks(startWeekSelected, endWeekSelected)
        
        resultDict = {}
        for part in partsListSelected:
            jiwon = self._jiwonDf[self._jiwonDf["PART_NO"] == part]
            orderVersusBalju = self._orderVersusBaljuDf[self._orderVersusBaljuDf["PART_NO"] == part]
            
            # 주차별로 소요량, 발주량 산출
            orderVersusBaljuLabels = ["CUSTOMER", "PART_NO", "PART_NAME"]
            orderVersusBaljuWeeksAvailable = [self.AddOrSubtractWeeks(item, -orderLeadTime) for item in self._orderVersusBaljuDf.columns if item in weeks]
            orderVersusBaljuFianlColumnsList = orderVersusBaljuLabels + orderVersusBaljuWeeksAvailable
            
            orderVersusBaljuFiltered = orderVersusBalju[orderVersusBaljuFianlColumnsList]
            orderVersusBaljuFiltered.insert(1, "WEEK", "발주")
            orderVersusBaljuFiltered.reset_index(drop=True, inplace=True)
            
            jiwonLabels = ["CUSTOMER", "WEEK", "PART_NO", "PART_NAME"]
            jiwonWeeksAvailable = [item for item in self._jiwonDf.columns if item in weeks]
            jiwonFianlColumnsList = jiwonLabels + jiwonWeeksAvailable
            
            jiwonWeekFiltered = jiwon[jiwonFianlColumnsList]
            jiwonWeekFiltered.reset_index(drop=True, inplace=True)
            
            # 결과값 딕셔너리에 넣기
            resultDict[part+"발주량"] = orderVersusBaljuFiltered
            resultDict[part+"소요량"] = jiwonWeekFiltered
        
        # TEMP : 일단 hAnal 탭에 넣어놨음
        with self._horizontalAnalysisTab:
            for part in partsListSelected:
                orders = resultDict[part+"발주량"]
                st.write(f"{part} 발주량 (리드타임 {orderLeadTime} 주 고려 시)")
                st.dataframe(orders)
                
                requirements = resultDict[part+"소요량"]
                st.write(f"{part} 소요량")
                st.dataframe(requirements)
            
                #region BarChart 그리기
                cols = ["WEEK"] + self.GetItemsWithWK(requirements.columns)
                tempDfForGraphDrawing = requirements[cols]
                tempDfForGraphDrawing.set_index("WEEK", inplace=True)
                dfForGraphDrawning = tempDfForGraphDrawing.swapaxes('index', 'columns') # WEEK(지원판단서주차)이 컬럼, 각 주차별 수량이 인덱스인 df
                subCategory = dfForGraphDrawning.columns
                
                weeksList = [item[-2:] for item in list(requirements["WEEK"])]
                
                bar_type = 'vertical' # 함수화 할 때 대비용 인수
                betweenBarPadding = 0.8
                withinBarPadding = 0.9
                
                categories = self.GetItemsWithWK(requirements.columns)
                subCategoryCount = jiwonWeekFiltered.shape[0] ## 서브 카테고리 개수
                
                width = 30
                height = 10
                fig = plt.figure(figsize = (width, height))
                fig.set_facecolor('white') ## 캔버스 색상 지정    
                ax = fig.add_subplot() ## 그림이 그려질 축을 생성        
                
                colors = sns.color_palette('hls', subCategoryCount) ## 막대기 색상 지정
                
                tick_label = list(self.GetItemsWithWK(requirements.columns)) ## 메인 카테고리 라벨 생성    
                tick_number = len(tick_label) ## 메인 카테고리 눈금 개수
                
                tick_coord = np.arange(tick_number) ## 메인 카테고리안에서 첫번째 서브 카테고리 막대기가 그려지는 x좌표
                
                width = 1/subCategoryCount*betweenBarPadding ## 막대기 폭 지정
                
                
                config_tick = dict()    
                config_tick['ticks'] = [t + width*(subCategoryCount-1)/2 for t in tick_coord] ## 메인 카테고리 라벨 x좌표    
                config_tick['labels'] = tick_label 
                
                if bar_type == 'vertical': ## 수직 바 차트를 그린다.        
                    plt.xticks(**config_tick) ## x축 눈금 라벨 생성
                    
                    for i in range(subCategoryCount):            
                        ax.bar(tick_coord+width*i, dfForGraphDrawning[subCategory[i]], \
                               width*withinBarPadding, label=f"Jiwon Issued at WK{weeksList[i]}", \
                               color=colors[i]) ## 수직 바 차트 생성        
                        
                        plt.legend() ## 범례 생성        
                        plt.savefig('fig03.png',format='png',dpi=300)        
                #endregion
                
                st.pyplot(plt)
                
        with self._rawDataJiwonTab:
            st.header("로데이터_지원판단서")
            st.dataframe(self._jiwonDf)
            
        with self._rawDataOrderVersusBaljuTab:
            st.header("로데이터_오더대비발주현황")
            st.dataframe(self._orderVersusBaljuDf)
            
        
        
        
    
    #region Helpers
    def GetMinMaxWeek(self, weeks:list[str]) -> tuple[str, str]:
        weeksSorted = sorted(weeks)
        return (weeksSorted[0], weeksSorted[-1])
    
    def AddOrSubtractWeeks(self, initialWeek: str, weeks: int) -> str:
        # initialWeek를 연도와 주차로 분리
        year, week_str = initialWeek.split("_")
        week = int(week_str[2:])  # 주차에서 'WK'를 제외하고 정수로 변환
        # initialWeek의 시작일을 구함
        initial_date = datetime.strptime(f"{year}-W{week}-1", "%Y-W%W-%w")

        # weeks 값에 따라 주차를 더하거나 빼줌
        adjusted_date = initial_date + timedelta(weeks=weeks)

        # 연도와 주차를 다시 조합하여 문자열로 반환
        adjusted_week = adjusted_date.strftime("%G_WK%V")

        return adjusted_week

    def GetConsecutiveWeeks(self, startWeek: str, endWeek: str) -> list:
        # 시작 주차와 끝 주차에서 연도와 주차를 추출
        start_year, start_week_str = startWeek.split("_")
        start_week = int(start_week_str[2:])  # 주차에서 'WK'를 제외하고 정수로 변환

        end_year, end_week_str = endWeek.split("_")
        end_week = int(end_week_str[2:])  # 주차에서 'WK'를 제외하고 정수로 변환

        # 시작 주차의 시작일을 구함
        start_date = datetime.strptime(f"{start_year}-W{start_week}-1", "%Y-W%W-%w")
        # 끝 주차의 시작일을 구함
        end_date = datetime.strptime(f"{end_year}-W{end_week}-1", "%Y-W%W-%w")

        # 연속적인 주차를 저장할 리스트 초기화
        consecutive_weeks = []

        # 시작 주차부터 끝 주차까지 반복하여 연속적인 주차를 구함
        current_date = start_date
        while current_date <= end_date:
            # 현재 주차를 연도와 주차로 변환하여 리스트에 추가
            current_week = current_date.strftime("%G_WK%V")
            consecutive_weeks.append(current_week)
            # 다음 주차로 이동
            current_date += timedelta(weeks=1)

        return consecutive_weeks
    
    def GetItemsWithWK(self, inputList:list) -> list:
        return [item for item in inputList if "WK" in item]
    
    #endregion
        
            
            
do = Tester()

