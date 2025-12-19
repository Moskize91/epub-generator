from typing import Literal


class I18N:
    def __init__(self, lan: Literal["zh", "en"]):
        if lan == "zh":
            self.unnamed: str = "未命名"
            self.cover: str = "封面"
            self.table_of_contents: str = "目录"
            self.landmarks: str = "路标"
            self.start_of_content: str = "正文开始"
            self.preface: str = "前言"
        elif lan == "en":
            self.unnamed: str = "Unnamed"
            self.cover: str = "Cover"
            self.table_of_contents: str = "Table of Contents"
            self.landmarks: str = "Landmarks"
            self.start_of_content: str = "Start of Content"
            self.preface: str = "Preface"
