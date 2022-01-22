# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'gui_logger.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(400, 300)
        self.verticalLayout_2 = QVBoxLayout(Form)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.text_2 = QLabel(Form)
        self.text_2.setObjectName(u"text_2")

        self.horizontalLayout.addWidget(self.text_2)

        self.clear = QPushButton(Form)
        self.clear.setObjectName(u"clear")
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.clear.sizePolicy().hasHeightForWidth())
        self.clear.setSizePolicy(sizePolicy)

        self.horizontalLayout.addWidget(self.clear)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.text = QPlainTextEdit(Form)
        self.text.setObjectName(u"text")

        self.verticalLayout.addWidget(self.text)


        self.verticalLayout_2.addLayout(self.verticalLayout)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.text_2.setText(QCoreApplication.translate("Form", u"Logging Console", None))
        self.clear.setText(QCoreApplication.translate("Form", u"Clear", None))
    # retranslateUi

