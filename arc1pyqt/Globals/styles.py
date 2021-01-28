####################################

# (c) Radu Berdan
# ArC Instruments Ltd.

# This code is licensed under GNU v3 license (see LICENSE.txt for details)

####################################

import sys
import os

style1="background-color: rgb(245,245,245); \
 margin:0px; \
 padding: 2px; \
 border:1px solid rgb(0,32,87); \
 qproperty-alignment: AlignCenter;"

style1a="background-color: rgb(255,255,255); \
margin:0px; \
padding: 2px; \
border:1px solid rgb(128,128,2128); \
qproperty-alignment: AlignCenter;"

style2="background-color: rgb(255,255,255); \
 margin:1px; \
 border:2px solid rgb(0, 0, 255); \
 qproperty-alignment: AlignCenter;"

toolBtn="""\
QPushButton {\
	background-color: rgb(255,255,255); \
	border:2px solid rgb(0,32,87); \
	color: rgb(0,32,87); \
	height: 28px; \
	margin-left: 2px; \
	margin-right: 2px; \
	padding: 0 5px 0 5px; \
	font: bold; \
	} \
QPushButton:hover{\
	background-color: rgb(0,32,87); \
	color: rgb(255, 255, 255); \
	} \
QPushButton:pressed{\
	margin: 3px; \
	}"""

toolCombo="""\
QComboBox{\
	border: 2px solid rgb(0,32,87); \
	border-radius: 0px; \
	margin-left: 2px; \
	margin-right: 0px; \
	width: 100px; \
	padding: 0 0 0 0; \
	height: 28px; \
	} \
QComboBox:down-button { \
	background-color: rgb(255, 255, 255); \
	} \
"""

btnStyle="""\
QPushButton {\
	background-color: rgb(255,255,255); \
	border:1px solid rgb(226,90,41); \
	color: rgb(226,90,41); \
	height: 25px; \
	margin: 0px; \
	font: bold; \
	} \
QPushButton:hover{\
	background-color: rgb(226,90,41); \
	color: rgb(255, 255, 255); \
	} \
QPushButton:pressed{\
	margin: 3px; \
	} \
QPushButton:disabled{\
	background-color: rgb(244, 244, 244); \
    border: 1px solid rgb(180, 180, 180); \
	color: rgb(180, 180, 180); \
	}"""

btnLive="""\
QPushButton {\
	background-color: rgb(255,255,255); \
	border:1px solid rgb(255,0,0); \
	color: rgb(255,0,0); \
	height: 25px; \
	margin: 0px; \
	font: bold; \
	} \
QPushButton:hover{\
	background-color: rgb(255,0,0); \
	color: rgb(255, 255, 255); \
	} \
QPushButton:pressed{\
	margin: 3px; \
	}"""

btnStyle2="""\
QPushButton {\
	background-color: rgb(255,255,255); \
	border:1px solid rgb(0, 32, 87); \
	color: rgb(0, 32, 87); \
	height: 25px; \
	margin: 0px; \
	font: bold; \
	} \
QPushButton:hover{\
	background-color: rgb(0, 32, 87); \
	color: rgb(255, 255, 255);\
	} \
QPushButton:pressed{\
	margin: 3px; \
	}\
QPushButton:disabled{\
	background-color: rgb(244, 244, 244); \
    border: 1px solid rgb(180, 180, 180); \
	color: rgb(180, 180, 180); \
    }"""

groupStyle="""\
QGroupBox {\
	border: 1px solid rgb(0,32,87); \	
	border-radius: 5px; \
	margin-top: 3px; \
	padding: 0 0 0 0; \
	} \
QGroupBox:title{\
    subcontrol-origin: margin; \
    left: 0px; \
    color: rgb(0,32,87); \
    border: 1px solid rgb(0,32,87); \
    background-color: rgb(245,245,245); \
    margin-top: 3px\
	}"""

groupStyleDisplay="""\
QGroupBox {\
	border: 1px solid rgb(0,32,87); \	
	border-radius: 5px; \
	margin-top: 0px; \
	padding: 0 0 0 0; \
	} \
QGroupBox:title{\
    subcontrol-origin: margin; \
    left: 0px; \
    color: rgb(0,32,87); \
    border: 1px solid rgb(0,32,87); \
    background-color: rgb(245,245,245); \
    margin-top: 3px\
	}"""

groupStyleCB="""\
QGroupBox {\
	border: 1px solid rgb(0,32,87); \	
	border-radius: 5px; \
	margin-top: 3px; \
	padding: 0 0 0 0; \
	} \
QGroupBox:title{\
    subcontrol-origin: margin; \
    left: 0px; \
    color: rgb(0,32,87); \
    border: 1px solid rgb(0,32,87); \
    background-color: rgb(245,245,245); \
    margin-top: 3px\
	}"""

groupStyleProg="""\
QGroupBox {\
	border: 1px solid rgb(0,32,87); \	
	border-radius: 5px; \
	margin-top: 3px; \
	margin-right: 3px; \
	padding: 0 0 0 0; \
	} \
QGroupBox:title{\
    subcontrol-origin: margin; \
    left: 0px; \
    color: rgb(0,32,87); \
    border: 1px solid rgb(0,32,87); \
    background-color: rgb(245,245,245); \
    margin-top: 3px\
	}"""

entryStyle="""
QLineEdit{\
	border: 1px solid rgb(0,32,87); \
	height: 20px; \
	}"""

entryStyle2="""
QLineEdit{\
	border: 1px solid rgb(175,175,175); \
	height: 24px; \
	}"""

labelStyle="""
QLabel{\
	background-color: rgb(255,255,255); \
	color: rgb(0, 32,87); \
	padding-left: 2px; \
	}"""

comboStyle="""\
QComboBox{\
	border: 1px solid rgb(0,32,87); \
	border-radius: 0px; \
	padding: 0 0 0 2px; \
	height: 25px; \
	} \
QComboBox:down-button { \
	background-color: rgb(255, 255, 255); \
	}"""

comboStylePulse="""\
QComboBox{\
	border: 1px solid rgb(0,32,87); \
	border-radius: 0px; \
	padding: 0 0 0 2px; \
	height: 20px; \
	width: 20px; \
	} \
QComboBox:down-button { \
	background-color: rgb(255, 255, 255); \
	} \
"""

spinStyle="""\
QDoubleSpinBox{\
	border: 1px solid rgb(0,32,87); \
	border-radius: 0px; \
	padding: 3px 0 4px 2px; \
	} \
QSpinBox{\
	border: 1px solid rgb(0,32,87); \
	border-radius: 0px; \
	padding: 3px 0 4px 2px; \
	} \
"""

lineStyle="""\
QFrame{\
	color: rgb(0,32,87);}
	"""


groupStyleNewSession="""\
QGroupBox {\
	border-top: 1px solid rgb(0,32,87); \
	border-bottom: 0px; \
	border-left: 0px; \
	border-right: 0px; \
	margin-top: 20px; \
	} \
QGroupBox:title{\
    subcontrol-origin: margin; \
    left: 10px; \
    color: rgb(0,32,87); \
    background-color: rgb(245,245,245); \
    margin-top: 8px\
	}"""

arcStatus_disc="""
QLabel{\
	background-color: rgb(00,32,87); \
	color: rgb(255,255,255); \
	margin: 2px; \
	}"""

arcStatus_ready="""
QLabel{\
	background-color: rgb(10,107,0); \
	color: rgb(255,255,255); \
	margin: 2px; \
	}"""

arcStatus_busy="""
QLabel{\
	background-color: rgb(129,0,6); \
	color: rgb(255,255,255); \
	margin: 2px; \
	}"""

 #rgb(0,32,87) dark blue
 #rgb(226,90,41) orange
#QDoubleSpinBox:down-button { \
#	background-color: rgb(0, 255, 255); \
#	} \

selectedStyle="""
	font: bold; \
	"""

unselectedStyle="""
	font: normal; \
	"""

loop_style_top_selected="""\
QPushButton {\
    text-align: left; \
    border-left:0px solid rgb(0,32,87); \
    border-right:0px solid rgb(0,32,87); \
    border-top: 4px solid rgb(0,32,87); \
    border-bottom: 0px solid rgb(0,32,87); \
    color: rgb(0,32,87); \
	font: bold;\
    } """

loop_style_bot_selected="""\
QPushButton {\
    text-align: left; \
    border-left:0px solid rgb(0,32,87); \
    border-right:0px solid rgb(0,32,87); \
    border-top: 0px solid rgb(0,32,87); \
    border-bottom: 4px solid rgb(0,32,87); \
    color: rgb(0,32,87); \
    font: bold; \
    } """

EdgeBtn_style="""\
QPushButton {\
    border: 1px solid rgb(0,32,87); \
    border-radius: 5px; \
    background-color: rgb(0,32,87); \
    color: rgb(255,255,255); \
    padding: 0px; \
    padding-left:10px;\
    padding-right:10px;\
    font-size: 15px;\
    } """

btnLowPadding="""\
QPushButton {\
    color: rgb(0,32,87); \
    } """

dummy_style="""\
QPushButton {\
    border-left:2px solid rgb(0,32,87); \
    border-right:2px solid rgb(0,32,87); \
    border-top: 0px solid rgb(0,32,87); \
    border-bottom: 0px solid rgb(0,32,87); \
    color: rgb(0,32,87); \
    } """

loop_style_top="""\
QPushButton {\
    text-align: left; \
    border-left:0px solid rgb(0,32,87); \
    border-right:0px solid rgb(0,32,87); \
    border-top: 4px solid rgb(0,32,87); \
    border-bottom: 0px solid rgb(0,32,87); \
    color: rgb(0,32,87); \
    } """

loop_style_bot="""\
QPushButton {\
    text-align: left; \
    border-left:0px solid rgb(0,32,87); \
    border-right:0px solid rgb(0,32,87); \
    border-top: 0px solid rgb(0,32,87); \
    border-bottom: 4px solid rgb(0,32,87); \
    color: rgb(0,32,87); \
    } """

btnStyle_clearChain="""\
QPushButton {\
	background-color: rgb(255,255,255); \
	border:1px solid rgb(0, 32, 87); \
	color: rgb(0, 32, 87); \
	height: 18px; \
	margin: 0px; \
	font: bold; \
	} \
QPushButton:hover{\
	background-color: rgb(0, 32, 87); \
	color: rgb(255, 255, 255);\
	} \
QPushButton:pressed{\
	margin: 3px; \
	}"""

progressBarStyle = """
QProgressBar {
    border: 1px solid rgb(0, 32, 87);
    text-align: right;
    margin-right: 2.5em;
}

QProgressBar::chunk {
    background-color: rgb(0, 32, 87);
}"""
