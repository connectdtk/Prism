# -*- coding: utf-8 -*-
#
####################################################
#
# PRISM - Pipeline for animation and VFX projects
#
# www.prism-pipeline.com
#
# contact: contact@prism-pipeline.com
#
####################################################
#
#
# Copyright (C) 2016-2019 Richard Frangenberg
#
# Licensed under GNU GPL-3.0-or-later
#
# This file is part of Prism.
#
# Prism is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Prism is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Prism.  If not, see <https://www.gnu.org/licenses/>.



try:
	from PySide2.QtCore import *
	from PySide2.QtGui import *
	from PySide2.QtWidgets import *
	psVersion = 2
except:
	from PySide.QtCore import *
	from PySide.QtGui import *
	psVersion = 1

import os, sys
import traceback, time, platform, shutil, socket
from functools import wraps

if platform.system() == "Windows":
	if sys.version[0] == "3":
		import winreg as _winreg
	else:
		import _winreg


class Prism_Blender_Integration(object):
	def __init__(self, core, plugin):
		self.core = core
		self.plugin = plugin

		if platform.system() == "Windows":
			self.examplePath = self.getBlenderPath()
		elif platform.system() == "Linux":
			self.examplePath = "/usr/local/blender-2.79b-linux-glibc219-x86_64/2.79"
		elif platform.system() == "Darwin":
			self.examplePath = "/Applications/blender/blender.app/Resources/2.79"


	def err_decorator(func):
		@wraps(func)
		def func_wrapper(*args, **kwargs):
			exc_info = sys.exc_info()
			try:
				return func(*args, **kwargs)
			except Exception as e:
				exc_type, exc_obj, exc_tb = sys.exc_info()
				erStr = ("%s ERROR - Prism_Plugin_Blender_Integration %s:\n%s\n\n%s" % (time.strftime("%d/%m/%y %X"), args[0].plugin.version, ''.join(traceback.format_stack()), traceback.format_exc()))
				if hasattr(args[0].core, "writeErrorLog"):
					args[0].core.writeErrorLog(erStr)
				else:
					QMessageBox.warning(args[0].core.messageParent, "Prism Integration", erStr)

		return func_wrapper


	@err_decorator
	def getExecutable(self):
		execPath = ""
		if platform.system() == "Windows":
			execPath = os.path.join(os.path.dirname(self.examplePath), "blender.exe")

		return execPath

	@err_decorator
	def integrationAdd(self, origin):
		path = QFileDialog.getExistingDirectory(self.core.messageParent, "Select Blender folder", self.examplePath)

		if path == "":
			return False

		result = self.writeBlenderFiles(path)

		if result:
			QMessageBox.information(self.core.messageParent, "Prism Integration", "Prism integration was added successfully")
			return path

		return result


	@err_decorator
	def integrationRemove(self, origin, installPath):
		result = self.removeIntegration(installPath)

		if result:
			QMessageBox.information(self.core.messageParent, "Prism Integration", "Prism integration was removed successfully")

		return result


	@err_decorator
	def getBlenderPath(self):
		try:
			key = _winreg.OpenKey(
				_winreg.HKEY_LOCAL_MACHINE,
				"SOFTWARE\\Classes\\blendfile\\shell\\open\\command",
				0,
				_winreg.KEY_READ | _winreg.KEY_WOW64_64KEY
			)
			blenderPath = (_winreg.QueryValueEx(key, "" ))[0].split(" \"%1\"")[0].replace("\"", "")

			vpath = os.path.join(os.path.dirname(blenderPath), "2.79")

			if os.path.exists(vpath):
				return vpath
			else:
				return ""

		except:
			return ""


	def writeBlenderFiles(self, blenderPath):
		try:
			if not os.path.exists(os.path.join(blenderPath, "scripts", "startup")):
				QMessageBox.warning(self.core.messageParent, "Prism Integration", "Invalid Blender path: %s.\n\nThe path has to be the Blender version folder in the installation folder, which usually looks like this: (with your Blender version):\n\n%s" % (blenderPath, self.examplePath), QMessageBox.Ok)
				return False

			integrationBase = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Integration")

			# prismInit
			initpath = os.path.join(blenderPath, "scripts", "startup", "PrismInit.py")
			saveRenderPath = os.path.join(blenderPath, "scripts", "startup", "PrismAutoSaveRender.py")
			addedFiles = []

			if os.path.exists(initpath):
				os.remove(initpath)

			if os.path.exists(initpath + "c"):
				os.remove(initpath + "c")

			if os.path.exists(saveRenderPath):
				os.remove(saveRenderPath)

			if os.path.exists(saveRenderPath + "c"):
				os.remove(saveRenderPath + "c")

			baseinitfile = os.path.join(integrationBase, "PrismInit.py")
			shutil.copy2(baseinitfile, initpath)
			addedFiles.append(initpath)

			with open(initpath, "r") as init:
				initStr = init.read()

			with open(initpath, "w") as init:
				initStr = initStr.replace("PRISMROOT", "\"%s\"" % self.core.prismRoot.replace("\\", "/"))
				init.write(initStr)

			topbarPath = os.path.join(blenderPath, "scripts", "startup", "bl_ui", "space_topbar.py")
			hMenuStr = 'layout.menu("TOPBAR_MT_help")'
			fClassStr = 'class TOPBAR_MT_file(Menu):'
			hClassName = "TOPBAR_MT_help,"
			baseTopbarFile1 = os.path.join(integrationBase, "space_topbar1.py")

			with open(baseTopbarFile1, "r") as init:
				bTbStr1 = init.read()

			baseTopbarFile2 = os.path.join(integrationBase, "space_topbar2.py")

			with open(baseTopbarFile2, "r") as init:
				bTbStr2 = init.read()

			if not os.path.exists(topbarPath):
				topbarPath = os.path.join(blenderPath, "scripts", "startup", "bl_ui", "space_info.py")
				hMenuStr = 'layout.menu("INFO_MT_help")'
				fClassStr = 'class INFO_MT_file(Menu):'
				hClassName = "INFO_MT_help,"

			if os.path.exists(topbarPath):
				with open(topbarPath, "r") as init:
					tbStr = init.read()

				for i in range(2):
					if "#>>>PrismStart" in tbStr and "#<<<PrismEnd" in tbStr:
						tbStr = tbStr[:tbStr.find("#>>>PrismStart")] + tbStr[tbStr.find("#<<<PrismEnd")+len("#<<<PrismEnd"):]
				tbStr = tbStr.replace("    TOPBAR_MT_prism,", "")

				tbStr = tbStr.replace(hMenuStr, hMenuStr + bTbStr1)
				tbStr = tbStr.replace(fClassStr, bTbStr2 + fClassStr)
				tbStr = tbStr.replace(hClassName, hClassName + '\n    TOPBAR_MT_prism,')

				if not os.path.exists(topbarPath + ".bak"):
					shutil.copy2(topbarPath, topbarPath + ".bak")

				with open(topbarPath, "w") as init:
					init.write(tbStr)

			baseRenderfile = os.path.join(integrationBase, "PrismAutoSaveRender.py")
			shutil.copy2(baseRenderfile, saveRenderPath)
			addedFiles.append(saveRenderPath)

			if platform.system() == "Windows":
				baseWinfile = os.path.join(integrationBase, "qminimal.dll")
				winPath = os.path.join(os.path.dirname(blenderPath), "platforms", "qminimal.dll")

				if not os.path.exists(os.path.dirname(winPath)):
					os.mkdir(os.path.dirname(winPath))

				if not os.path.exists(winPath):
					shutil.copy2(baseWinfile, winPath)

				baseWinfile = os.path.join(integrationBase, "qoffscreen.dll")
				winPath = os.path.join(os.path.dirname(blenderPath), "platforms", "qoffscreen.dll")

				if not os.path.exists(winPath):
					shutil.copy2(baseWinfile, winPath)

				baseWinfile = os.path.join(integrationBase, "qwindows.dll")
				winPath = os.path.join(os.path.dirname(blenderPath), "platforms", "qwindows.dll")

				if not os.path.exists(winPath):
					shutil.copy2(baseWinfile, winPath)

				baseWinfile = os.path.join(integrationBase, "python3.dll")
				winPath = os.path.join(os.path.dirname(blenderPath), "python3.dll")

				if not os.path.exists(winPath):
					shutil.copy2(baseWinfile, winPath)

			if platform.system() in ["Linux", "Darwin"]:
				for i in addedFiles:
					os.chmod(i, 0o777)

			return True

		except Exception as e:
			exc_type, exc_obj, exc_tb = sys.exc_info()
			msgStr = "Errors occurred during the installation of the Blender integration.\nThe installation is possibly incomplete.\n\n%s\n%s\n%s" % (str(e), exc_type, exc_tb.tb_lineno)
			msgStr += "\n\nRunning this application as administrator could solve this problem eventually."

			QMessageBox.warning(self.core.messageParent, "Prism Integration", msgStr)
			return False


	def removeIntegration(self, installPath):
		try:
			initPy = os.path.join(installPath, "scripts", "startup", "PrismInit.py")
			saveRenderPy = os.path.join(installPath, "scripts", "startup", "PrismAutoSaveRender.py")

			for i in [initPy, saveRenderPy]:
				if os.path.exists(i):
					os.remove(i)

			topbarPath = os.path.join(installPath, "scripts", "startup", "bl_ui", "space_topbar.py")

			if not os.path.exists(topbarPath):
				topbarPath = os.path.join(installPath, "scripts", "startup", "bl_ui", "space_info.py")

			if os.path.exists(topbarPath):
				with open(topbarPath, "r") as init:
					tbStr = init.read()

				for i in range(2):
					if "#>>>PrismStart" in tbStr and "#<<<PrismEnd" in tbStr:
						tbStr = tbStr[:tbStr.find("#>>>PrismStart")] + tbStr[tbStr.find("#<<<PrismEnd")+len("#<<<PrismEnd"):]

				tbStr = tbStr.replace('\n    TOPBAR_MT_prism,', "")

				with open(topbarPath, "w") as init:
					init.write(tbStr)

			return True

		except Exception as e:
			exc_type, exc_obj, exc_tb = sys.exc_info()
			msgStr = "Errors occurred during the removal of the Blender integration.\n\n%s\n%s\n%s" % (str(e), exc_type, exc_tb.tb_lineno)
			msgStr += "\n\nRunning this application as administrator could solve this problem eventually."

			QMessageBox.warning(self.core.messageParent, "Prism Integration", msgStr)
			return False


	def updateInstallerUI(self, userFolders, pItem):
		try:
			bldItem = QTreeWidgetItem(["Blender"])
			pItem.addChild(bldItem)

			if platform.system() == "Windows":
				blenderPath = self.getBlenderPath()
			elif platform.system() == "Linux":
				blenderPath = "/usr/local/blender-2.79b-linux-glibc219-x86_64/2.79"
			elif platform.system() == "Darwin":
				blenderPath = "/Applications/blender/blender.app/Resources/2.79"

			if blenderPath != "":
				bldItem.setCheckState(0, Qt.Checked)
				bldItem.setText(1, blenderPath)
				bldItem.setToolTip(0, blenderPath)
			else:
				bldItem.setCheckState(0, Qt.Unchecked)
		except Exception as e:
			exc_type, exc_obj, exc_tb = sys.exc_info()
			msg = QMessageBox.warning(self.core.messageParent, "Prism Installation", "Errors occurred during the installation.\n The installation is possibly incomplete.\n\n%s\n%s\n%s\n%s" % (__file__, str(e), exc_type, exc_tb.tb_lineno))
			return False


	def installerExecute(self, bldItem, result, locFile):
		try:
			installLocs = []

			if bldItem.checkState(0) == Qt.Checked and os.path.exists(bldItem.text(1)):
				result["Blender integration"] = self.writeBlenderFiles(bldItem.text(1))
				if result["Blender integration"]:
					installLocs.append(bldItem.text(1))

			return installLocs
		except Exception as e:
			exc_type, exc_obj, exc_tb = sys.exc_info()
			msg = QMessageBox.warning(self.core.messageParent, "Prism Installation", "Errors occurred during the installation.\n The installation is possibly incomplete.\n\n%s\n%s\n%s\n%s" % (__file__, str(e), exc_type, exc_tb.tb_lineno))
			return False