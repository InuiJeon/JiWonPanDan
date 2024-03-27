import os
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import datetime as dt
import seaborn as sns
import re
import streamlit as st
import time
from dataclasses import dataclass
import locale
from abc import ABC, abstractmethod # abstract class


class Tester:
    # Datas
    _uploadedFileA = None
    _uploadedFileB = None
    _df:pd.DataFrame = None
    
    # Elements
    _sidebar = None

    
    def __init__(self):
        locale.setlocale(locale.LC_ALL, '')
        self._uploadedFileA = st.file_uploader("지원판단서 가공파일을 업로드하세요.")
        self._uploadedFileB = st.file_uploader("Order Status 가공파일을 업로드하세요.")
        
        # 파일 업로드 완료 체크
        for i in range(0,100):
            if self._uploadedFileA is not None and self._uploadedFileB is not None :
                self.OnFileUploaded()
                break
            else:
                time.sleep(3)
        
        
    def OnFileUploaded(self):
        if self._uploadedFileA is None:
            raise Exception("UploadedFile 이 None 입니다.")

        self._df = pd.read_excel(self._uploadedFileA, engine='openpyxl')
        self.OnDataReadComplete()
        
                
    def OnDataReadComplete(self):
        self._sidebar = st.sidebar
        with self._sidebar:
            st.form_submit_button("파일 리딩 테스트",
                                  on_click=self.ShowData)                                 
    
    def ShowData(self):
        st.dataframe(self._df)
            
            
do = Tester()
