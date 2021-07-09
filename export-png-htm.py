#! /usr/bin/env python

import sys
import io
import inkex
import os
import subprocess
import shlex
import tempfile
import shutil
import copy
import logging
import math
import string

class Options():
	def __init__(self, htmjs_exporter):
		self.current_file = htmjs_exporter.options.input_file

#		# Controls page
#		self.export_type = htmjs_exporter.options.export_type
#		self.path = os.path.normpath(htmjs_exporter.options.path)
##		self.allLayers = self._str_to_bool(htmjs_exporter.options.allLayers)
##		self.createHtmlJsCss = self._str_to_bool(htmjs_exporter.options.createHtmlJsCss)
#		
#		#options
##		self.soloselez = self._str_to_bool(htmjs_exporter.options.soloselez)
#		
#		self.dpi = htmjs_exporter.options.dpi
#		self.space = htmjs_exporter.options.space
##		self.tagliopagina = self._str_to_bool(htmjs_exporter.options.tagliopagina)

#		# File naming page
#		self.sdoc = htmjs_exporter.options.sdoc
#		self.spre = htmjs_exporter.options.spre
##		self.nomeconind = self._str_to_bool(htmjs_exporter.options.nomeconind)
##		self.coordinate = self._str_to_bool(htmjs_exporter.options.coordinate)
##		self.dimensioni = self._str_to_bool(htmjs_exporter.options.dimensioni)
#		self.spost = htmjs_exporter.options.spost
#		
		# Help page
		self.use_logging = htmjs_exporter.options.use_logging
		if self.use_logging:
			self.log_path = os.path.expanduser(htmjs_exporter.options.log_path)
			self.overwrite_log = htmjs_exporter.options.overwrite_log
			log_file_name = os.path.join(self.log_path, 'batch_export.log')
			if self.overwrite_log and os.path.exists(log_file_name):
				logging.basicConfig(filename=log_file_name, filemode="w", level=logging.DEBUG)
			else:
				logging.basicConfig(filename=log_file_name, level=logging.DEBUG)


#	def __str__(self):
#		print =  "===> EXTENSION PARAMETERS\n"
#		print += "---------------------------------------\n"
#		return print

#	def _str_to_bool(self, str):
#		if str.lower() == 'true':
#			return True
#		return False

class HtmJsExporter(inkex.Effect):
	def __init__(self):
		inkex.Effect.__init__(self)
		
		# Controls page
		self.arg_parser.add_argument("--export-type", action="store", type=str, dest="export_type", default="png", help="")
		self.arg_parser.add_argument("--path", action="store", type=str, dest="path", default="", help="export path")
		self.arg_parser.add_argument("--allLayers", action="store", type=inkex.Boolean, dest="allLayers", default=False, help="")
		self.arg_parser.add_argument("--createHtmlJsCss", action="store", type=inkex.Boolean, dest="createHtmlJsCss", default=False, help="")
		
		#export
		self.arg_parser.add_argument("--soloselez", action="store", type=inkex.Boolean, dest="soloselez", default=True, help="")
		self.arg_parser.add_argument("--dpi", action="store", type=int, dest="dpi", default="96", help="")
		self.arg_parser.add_argument("--space", action="store", type=int, dest="space", default="96", help="")
		self.arg_parser.add_argument("--tagliopagina", action="store", type=inkex.Boolean, dest="tagliopagina", default=True, help="")

		# File naming page
		self.arg_parser.add_argument("--sdoc", action="store", type=str, dest="sdoc", default="#lay#", help="base file name")
		self.arg_parser.add_argument("--spre", action="store", type=str, dest="spre", default="", help="")
#		self.arg_parser.add_argument("--nomeconind", action="store", type=inkex.Boolean, dest="nomeconind", default=True, help="")
		self.arg_parser.add_argument("--coordinate", action="store", type=inkex.Boolean, dest="coordinate", default=True, help="")
		self.arg_parser.add_argument("--dimensioni", action="store", type=inkex.Boolean, dest="dimensioni", default=True, help="")
		self.arg_parser.add_argument("--spost", action="store", type=str, dest="spost", default="", help="")
		
		# Help page
		self.arg_parser.add_argument("--use-logging", action="store", type=inkex.Boolean, dest="use_logging", default=False, help="")
		self.arg_parser.add_argument("--overwrite-log", action="store", type=inkex.Boolean, dest="overwrite_log", default=False, help="")
		self.arg_parser.add_argument("--log-path", action="store", type=str, dest="log_path", default="", help="")

		# HACK - the script is called with a "--tab controls" option as an argument from the notebook param in the inx file.
		# This argument is not used in the script. It's purpose is to suppress an error when the script is called.
		self.arg_parser.add_argument("--tab", action="store", type=str, dest="tab", default="controls", help="")
		
#		<label appearance="header">Thank you!</label>
#		<param name="help" type="description" indent="1">If this extension has helped you please consider supporting it and give it a star on Github.</param>
#		<param name="help" type="description" indent="1">https://github.com/StefanTraistaru/batch-export</param>

	def effect(self):
		counter = 1
		self.pathexport = self.options.path
		self.export_type = self.options.export_type
		self.exportplainsvg = True
		self.export_pdf_version = 1.4
		self.spre = self.options.spre
		self.idid = True #deve esserci sempre l'id
#		self.nomeconind = self.options.nomeconind #True #self.options.dimensioni
		self.coordinate = self.options.coordinate #True #self.options.coordinate
		self.dimensioni = self.options.dimensioni #False #self.options.dimensioni
		self.spost = self.options.spost
		self.sdoc = self.options.sdoc
		self.soloselez = self.options.soloselez
		self.allLayers = self.options.allLayers
		self.createHtmlJsCss = self.options.createHtmlJsCss
		self.tagliopagina = self.options.tagliopagina
		self.space = self.options.space
		self.dpi = self.options.dpi
		self.divevent = "divevent" #nome classe per rettangoli eventi
		
		if(self.createHtmlJsCss==True):
			self.export_type="png"
		
		self.listQA = {}
		
		svg = self.document.getroot()
		scale = self.svg.unittouu('1px')
		self.svg_width = math.ceil(self.svg.width / scale)
		self.svg_height = math.ceil(self.svg.height / scale)

		options = Options(self)
#		logging.debug(options)
		
		# check/create the output folder
		if not os.path.exists(os.path.join(self.pathexport)):
			os.makedirs(os.path.join(self.pathexport))
		
		self.listQA = self.get_listqueryall()

#		#se tutti i layer o solo quello attivo
		#inkex.utils.debug(str(self.allLayers))
		if(self.allLayers==False):
			#inkex.utils.debug("solo attivo")
			layers = self.get_layers(options.current_file, True)
			#inkex.utils.debug("n layers:"+str(len(layers)))
			for tmplayerId in layers:
#				#inkex.utils.debug("***************exportFromLayer:"+tmplayerId)
#				retexp=self.exportFromLayer(tmplayerId,True)
				retexp=self.exportFromLayer(tmplayerId,self.allLayers)
		else:
			layers = self.get_layers(options.current_file, False)
			#inkex.utils.debug("n layers:"+str(len(layers)))
			for tmplayerId in layers:
#				#inkex.utils.debug("***************exportFromLayer:"+tmplayerId)
#				retexp=self.exportFromLayer(tmplayerId,False)
				retexp=self.exportFromLayer(tmplayerId,not (self.allLayers))


#		#inkex.utils.debug(self.pathexport)
#		show_layer_ids = [layer[0] for layer in layers if layer[2] == "fixed" or layer[0] == layer_id]

		
	def exportFromLayer(self, layerId, onlySelected):
		obLayerTmp=self.svg.getElementById(layerId)
		#accende il layer
#		#inkex.utils.debug(obLayerTmp.attrib['style'])
#		#inkex.utils.debug(obLayerTmp.get("style","display:inline"))
		layerStatusDisplay=False
		if 'display:inline' in obLayerTmp.attrib['style']:
			layerStatusDisplay=True
		elif 'display:none' in obLayerTmp.attrib['style']:
			layerStatusDisplay=False
		else:
			layerStatusDisplay=False
		
#		#inkex.utils.debug("layerStatusDisplay:"+str(layerStatusDisplay))
#		obLayerTmp.set("style","display:inline")
		ret=self.displayLayer(obLayerTmp,True)

		svg_file = self.options.input_file
		self.document.write(svg_file)

#		#inkex.utils.debug("**")
#		#inkex.utils.debug(obLayerTmp.attrib['style'])
#		#inkex.utils.debug(obLayerTmp.get("style","display:inline"))
		
		if(self.sdoc=="#lay#" or onlySelected==False):
			active_layer=layerId
			label_attrib_name = "{%s}label" % obLayerTmp.nsmap['inkscape']
#			layer_label = obLayerTmp.attrib[label_attrib_name]
			active_layer_label=obLayerTmp.attrib[label_attrib_name]
			self.sdoc=active_layer_label
			logging.debug("active_layer_label:"+str(active_layer_label))
		
		directory = os.path.join(self.pathexport, active_layer_label, "")
		logging.debug("directory:"+directory)
		if not os.path.exists(directory):
			os.makedirs(directory)
			
		#crea uno script temporaneo nella cartella di esportazione
		self.scriptTmpName = os.path.join(directory, "__exportTempInkscape_"+self.sdoc+"__.sh")#directory+"__exportTempInkscape__.sh"
		self.scriptShellExportTxt=""

		self.strCss=""
		self.strHtm=""
		self.strJsCss=""
		self.strJs=""
		self.arJs = []
		pathHtm=""
		pathJs = ""
		pathCss = ""

		if(self.createHtmlJsCss==True):
	#		crea sottocartelle css, js, img
			dirCss=os.path.join(directory, "css", "")
			if not os.path.exists(dirCss):
				os.mkdir(dirCss)
			dirJs=os.path.join(directory, "js", "")
			if not os.path.exists(dirJs):
				os.mkdir(dirJs)
			dirImg=os.path.join(directory, "img", "")
			if not os.path.exists(dirImg):
				os.mkdir(dirImg)
			
			pathHtm=os.path.join(directory, self.sdoc+".html")
			pathJs = os.path.join(dirJs, self.sdoc+".js")
			pathCss = os.path.join(dirCss, self.sdoc+".css")
	#		comincia composizione stringa html
	#		comincia composizione stringa css
	#		comincia composizione stringa js
			
			self.strHtm += "<!DOCTYPE HTML>\n<html>\n<head>\n<title></title>\n<meta http-equiv=\"content-type\" content=\"text/html;charset=utf-8\" />\n"
			self.strHtm += "<meta http-equiv='content-type' content='text/html;charset=utf-8' />\n"
			self.strHtm += "<meta name=\"apple-mobile-web-app-status-bar-style\" content=\"black-translucent\">\n"
			self.strHtm += "<meta name=\"format-detection\" content=\"telephone=no\">\n"
			self.strHtm += "<meta name=\"viewport\" content=\"width=device-width,minimum-scale=1.0,maximum-scale=1.0\">\n"
			self.strHtm += "<link rel=\"stylesheet\" type=\"text/css\" href=\"css/animate.css\" />\n"
			self.strHtm += "<link rel=\"stylesheet\" type=\"text/css\" href=\"css/"+self.sdoc+".css\" />\n"
			self.strHtm += "<script type=\"text/javascript\" src=\"js/copax_script.js\"></script>\n"
			self.strHtm += "<script type=\"text/javascript\" src=\"js/"+self.sdoc+".js\"></script>\n"
			self.strHtm += "</head>\n"
			self.strHtm += "<!--<body onLoad=\"In_"+self.sdoc+"()\">-->\n"
			self.strHtm += "<!--<body onLoad=\"Start_"+self.sdoc+"()\">-->\n"
			self.strHtm += "<body>\n"
			self.strHtm += "<div id=\""+self.sdoc+"Container\">\n"
		else:
			dirImg=directory

#		logging.debug("inizia ciclo tra oggetti selezionati")
		indice = -1
		posx=0
		posy=0
		ww=0
		hh=0
		bb=0.0
		radice = ""
		retTexta=""
		retTextb=""
		retAr=[]
		
		self.commandActions = self.startActionShell()
		
		arElements=[]
		
		if onlySelected==True:
			if len(self.svg.selected) == 0:
				inkex.errormsg("Please select some paths first.")
				sys.exit()
			else:
				for el in self.svg.selected.values():
					arElements.append(el)
#					#inkex.utils.debug(str(el))
		else:
			for el in reversed(obLayerTmp):
				arElements.append(el)
		
#		for elemen in reversed(self.svg.selected.values()):
		for elemen in reversed(arElements):

			indice = indice+1
			if(indice<10):
				sindice = "0"+str(indice)
			else:
				sindice = str(indice)
			
			ob = elemen  #self.getElementById(self.svg.selection.items()[i])
			tmpid=ob.get("id")
			logging.debug("tmpid="+tmpid)
			idoldnew = self.getId(ob, indice)
			id=idoldnew[0]
			
			retAr = self.exportOb(idoldnew[0], idoldnew[1], sindice, dirImg, False, 1)
			retTexta+=retAr[0]
			retTextb+=retAr[1]
			
		
		self.commandActions=self.endActionShell(self.commandActions)
		
		if(self.createHtmlJsCss==True):
			self.strHtm += "</div>\n</body>\n</html>\n\n"

			self.strJs += "var "+self.sdoc+"time;\n\n"
			self.strJs += "function In_"+self.sdoc+"()\n{\n"
			self.strJs += "\t//prevents window scrolling\n"
			self.strJs += "\tdocument.body.addEventListener(\"touchmove\", function(event){event.preventDefault();});\n"
			for a in range(0, len(self.arJs)):
				self.strJs += "\t" + self.arJs[a] + " = document.getElementById(\""+self.arJs[a]+"\");\n"
			self.strJs += "//****\n"+self.strJsCss+"\n//****\n"
			self.strJs += "\t//Start_"+self.sdoc+"();\n"
			self.strJs += "\tattesaTmp=window.setTimeout(Start_"+self.sdoc+",500);\n"
			self.strJs += "\n}\n"
			self.strJs += "var attesaTmp;\n"
			self.strJs += "\n"
			self.strJs += "//var eventClick=\"touchstart\";\n"
			self.strJs += "//var eventClick=\"click\";\n"
			self.strJs += "function Start_"+self.sdoc+"()\n{\n"#}\n"
			self.strJs += "\twindow.clearTimeout(attesaTmp);\n"
			self.strJs += "\t//"+self.sdoc+"time = setTimeout( "+self.sdoc+"Anima, 50);\n"
			if(len(self.arJs)>1):
				self.strJs += "\t//" + self.arJs[0]+".obshow="+self.arJs[1]+";\n"
				self.strJs += "\t//" + self.arJs[0]+".addEventListener(eventClick, showOb, false);\n"
			else:
				self.strJs += "\t//" + self.arJs[0]+".obshow=undefined;\n"
				self.strJs += "\t//" + self.arJs[0]+".addEventListener(eventClick, showOb, false);\n"
			self.strJs += "\t//" + self.arJs[0]+".addEventListener(eventClick, gohome, false);\n"
			self.strJs += "\t//" + self.arJs[0]+".addEventListener(eventClick, gorcp, false);\n"
			self.strJs += "\t//" + self.arJs[0]+".addEventListener(eventClick, menuAction, false);\n"
			
			self.strJs += "/*********************************/\n"
			self.strJs += retTexta
			self.strJs += "/*********************************/\n"
			
			self.strJs += "}\n"

			self.strJs += "\nfunction menuAction(e){\n"
			self.strJs += "\tswitch(e.currentTarget){\n"
			self.strJs += "\t\tcase " + self.arJs[0]+":\n"
			self.strJs += "\t\t\tdocument.location=\"veeva:gotoSlide('copax_interventista_42.zip','10_Pozzilli.pdf')\";\n"
			self.strJs += "\t\t\tdocument.location=\"veeva:gotoSlide('"+self.sdoc+".html')\";\n"
			self.strJs += "\t\t\tbreak;\n"
			self.strJs += "\n\n"
			self.strJs += "/*********************************/\n"
			self.strJs += retTextb
			self.strJs += "/*********************************/\n"
			self.strJs += "\n\n"
			self.strJs += "\t}\n"
			self.strJs += "\n}\n"

			self.strJs += "\nfunction showOb(e)"
			self.strJs += "\n{\n"
			self.strJs += "\tif(e.currentTarget.obshow){\n"
			self.strJs += "\t\te.currentTarget.obshow.style.display=\"block\";\n"
			self.strJs += "\t}\n"
			self.strJs += "\n}\n"

			
			self.strJs += "\nfunction "+self.sdoc+"Anima()"
			self.strJs += "\n{\n"
			self.strJs += "\n\tclearTimeout("+self.sdoc+"time);\n"
			for a in range(0, len(self.arJs)):
				self.strJs += "\tsetDelay( "+self.arJs[a]+", 0.0 );\n"
				self.strJs += "\taddClass( "+self.arJs[a]+", \"\");\n"
			self.strJs += "\n}\n"
		
			self.strJs += "function Reset_"+self.sdoc+"()\n{\n"
			for a in range(0, len(self.arJs)):
				self.strJs += "\tremoveClass( "+self.arJs[a]+", \"\");\n"
				self.strJs += "//reset(\""+self.arJs[a]+"\");\n"
			self.strJs += "\n}\n"
			self.strJs += "function Out_"+self.sdoc+"()\n{\n}\n"
			self.strJs += "\nwindow.onload=In_"+self.sdoc+";\n"
			
			self.strHtm = self.strHtm.replace('  ', ' ')
			self.strHtm = self.strHtm.replace('"', '\'')
			self.strHtm = self.strHtm.replace(' - ', '')
			self.strHtm = self.strHtm.replace('( ', '(')
			self.strHtm = self.strHtm.replace(' )', ')')
			self.strHtm = self.strHtm.replace(' ,', ',')
			self.strHtm = self.strHtm.replace(' .', '.')
		
			self.write_txt_file(pathCss,self.strCss)
			self.write_txt_file(pathJs,self.strJs)
			self.write_txt_file(pathHtm,self.strHtm)
		
		self.write_txt_file(self.scriptTmpName,self.commandActions)
		
		#lancia comando di esportazione immagini
		comando = "bash \""+self.scriptTmpName+"\""
#		comando = "sh \""+scriptTmpName+"\""
		tmp = self.executeComm(comando)
		#elimina lo script temporaneo
		comando = "rm '"+self.scriptTmpName+"'"
		tmp = self.executeComm(comando)
		
#		self.displayLayer(obLayerTmp,layerStatusDisplay)
		
		return True
		

	def get_listqueryall(self):
		newcom = ['inkscape', '--query-all']
		newcom.append(self.options.input_file)
		bbs=dict();
		try:
			with subprocess.Popen(newcom, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as process:
				process.wait(timeout=300)
				tFStR = process.stdout  # List of all SVG objects in tFile
				tErrM = process.stderr
				for line in process.stdout:
					splitline=str(line.strip().decode('ascii')).split(',')
#					##inkex.utils.debug(splitline)
					key = splitline[0]
					data = [float(x.strip('\'')) for x in splitline[1:]]
					data.append(key)
					bbs[key] = data;
		except OSError:
			logging.debug('Error {}.'.format(newcom))
			inkex.errormsg('Error {}.'.format(newcom))
			exit()
		
		return bbs

	def executeComm(self, command):
		os.system(command)
#		return True

	
	def displayLayer(self,layer,onoff:True):
		if(onoff==True):
#			layer.attrib['style'] = 'display:inline'
			layer.set("style","display:inline")
		else:
#			layer.attrib['style'] = 'display:none'
			layer.set("style","display:none")
			
		return onoff
		
	def get_layers(self, file, onlyCurrent):
		svg_layers = self.document.xpath('//svg:g[@inkscape:groupmode="layer"]', namespaces=inkex.NSS)
		layers = []
		
		if( onlyCurrent==False):
		

			for layer in svg_layers:
				label_attrib_name = "{%s}label" % layer.nsmap['inkscape']
				layer_label = layer.attrib[label_attrib_name]
	#			
				if label_attrib_name not in layer.attrib:
					continue
	#			
				if layer_label[0:1] == "_":
					logging.debug("  Skip: label start with '_'".format(layer.attrib[label_attrib_name]))
					continue

				layer_id = layer.attrib["id"]
				label_attrib_name = "{%s}label" % layer.nsmap['inkscape']
				layer_label = layer.attrib[label_attrib_name]
				layer_type = "export"

				layers.append(layer_id)

		else:
			layer=self.svg.get_current_layer()
			layer_id = layer.attrib["id"]
			label_attrib_name = "{%s}label" % layer.nsmap['inkscape']
			layer_label = layer.attrib[label_attrib_name]
			layer_type = "export"
			layers.append(layer_id)
		return layers

	def getId(self, ob, index):
		newId=self.sdoc+"_"+ str(index)
		oldId = ob.get("id")
		
		newdata=self.listQA[oldId]
		newdata[4]=newId
		self.listQA[oldId]=newdata
		
		return [oldId,newId]
	
	def startActionShell(self):
		commA="inkscape --without-gui --actions=\""

		if self.export_type == 'svg':
			commA = commA + "export-plain-svg; "
		
		return commA
	
	def endActionShell(self,comm):
		commend=comm+"\" "+ self.options.input_file
		return commend
		
#	def export_to_file_shell(self, command):
#		command.append(self.options.input_file)

#		#aggiunge comandi alla shell temporanea che sarà lanciata alla fine del ciclo
#		comm=""
#		for c in command:
#			comm=comm+c+" "
#		self.scriptShellExportTxt=self.scriptShellExportTxt+"\n\n"+comm#+str([x for x in command[0:]])

	
	def write_txt_file(self, filepath, filecont):
		tex = open(filepath, 'w')
		tex.write(filecont)
		tex.close()
		
	def select_area(self,obtemp):
		opt = self.options
		x0 = y0 = y1 = x0 = None
		scale	   = self.svg.unittouu('1px')
#		# convert objects to path to not wrongly count the selection.bounding.box()
##		self.objects_to_paths(self.svg.selected, True)
##		self.objects_to_paths(obtemp, True)
#		bbox = obtemp.bounding_box()
##		bbox =obtemp.getBoundingBox()
##		bbox = obtemp.get_path().bounding_box()
##		bbox = obtemp.get_path().apply_transform().bounding_box()
##		bbox = obtemp.apply_transform().bounding_box()
#		logging.debug("bbox="+str(bbox))
#		logging.debug("bbox.left="+str(bbox.left))
#		logging.debug("bbox.right="+str(bbox.right))
#		logging.debug("bbox.top="+str(bbox.top))
#		logging.debug("bbox.bottom="+str(bbox.bottom))
#		logging.debug("scale="+str(scale))

##		x0 = math.ceil(bbox.left/scale)
##		x1 = math.ceil(bbox.right/scale)
##		y0 = math.ceil(bbox.top/scale)
##		y1 = math.ceil(bbox.bottom/scale)

#		x0 = (bbox.left/scale)
#		x1 = (bbox.right/scale)
#		y0 = (bbox.top/scale)
#		y1 = (bbox.bottom/scale)

#		points = [x0, y0, x1, y1]
#		##inkex.utils.debug(obtemp.get("id"))
#		##inkex.utils.debug(points)
#		##inkex.utils.debug(self.listQA)
#		
##		###############################
##		bb = self.getBoundingBox(obtemp)
##		logging.debug("#########################")
##		logging.debug(bb)
##		logging.debug("#########################")
##		###############################
		
		idtemp=obtemp.get("id")
		xywh=self.listQA[idtemp]
		x0=float(xywh[0])
		y0=float(xywh[1])
		x1=x0+float(xywh[2])
		y1=y0+float(xywh[3])
		points = [x0, y0, x1, y1]

#		###############################
		return points
	
	def getTab(self,n):
		strtmp = ""
		for itab in range(n):
			strtmp = strtmp + "\t"
		return strtmp
		
	def exportOb(self, svgid, expid, sindice, pathImg, divCont, tab):
		numIndice = int(sindice)
		
		self.arTesti=[]

		strtab = self.getTab(tab)

		obtmp=self.svg.getElementById(svgid)
		
		labelobtmp = str(obtmp.get("{"+inkex.NSS['inkscape']+"}label"))
		if(labelobtmp=="None"):
			labelobtmp="#"
		
		testo = ""
		self.arTesti=[]
		fontsize = ""
		divCont=False

		##cerca x y w h
		c = self.select_area(obtmp)

		#eliminare gli errori di inkscape sulle dimensioni
		bboxx0=float(int(c[0]*100)/100)
		bboxy0=float(int(c[1]*100)/100)
		bboxx1=float(int(c[2]*100)/100)
		bboxy1=float(int(c[3]*100)/100)
		
		bboxx0_floor = int(math.floor(bboxx0))
		bboxy0_floor = int(math.floor(bboxy0))
		bboxx1_floor = int(math.floor(bboxx1))
		bboxy1_floor = int(math.floor(bboxy1))

		ww = int(math.ceil(bboxx1-bboxx0))
		hh = int(math.ceil(bboxy1-bboxy0))

		x0=bboxx0_floor - self.space
		y0=bboxy0_floor - self.space
		x1=bboxx1_floor + self.space
		y1=bboxy1_floor + self.space
		
		if(self.tagliopagina==True):
			if(x0<0):
				x0=0
			if(y0<0):
				y0=0
			if(x1>self.svg_width):
				x1=self.svg_width
			if(y1>self.svg_height):
				y1=self.svg_height
		
		ww = int(math.ceil(x1-x0))
		hh = int(math.ceil(y1-y0))
		
		s_bboxx0=str(int(round(x0)))
		s_bboxy0=str(int(round(y0)))
		s_bboxx1=str(int(round(x1)))
		s_bboxy1=str(int(round(y1)))
		
		ddpi=str(int(round(self.dpi)))
		
		nome_img_path="" #path completo dell'immagine da esportare
		nome_img_file="" #nome del file immagine da esportare
		
#		nome_idDiv = self.spre + expid
		nome_idDiv = expid
	
		if(self.spre!=""):
			nome_img_file =  self.spre +"_"+ nome_img_file

		nome_img_file = nome_img_file + expid
		
		if(self.coordinate==True):
			nome_img_file = nome_img_file + "_" + str(int(x0)) + "_" + str(int(y0))
		
		if(self.dimensioni==True):
			nome_img_file = nome_img_file + "_" + str(int(ww)) + "x" + str(int(hh))
		
		if(self.spost!=""):
			nome_img_file = nome_img_file +"_"+ self.spost
	
#		nome_img_file = nome_img_file + ".png"
		nome_img_file = nome_img_file + "." + self.export_type
		nome_img_path = pathImg + nome_img_file
		
		#cerca rettangoli rossi
		isRedRect=False
		if(obtmp.tag == "{"+inkex.NSS['svg']+"}rect"):
			if 'opacity:0.5' in obtmp.attrib['style'] and 'fill:#ff0000' in obtmp.attrib['style']:
				isRedRect=True
	
		if(self.createHtmlJsCss==False):
			isRedRect=self.createHtmlJsCss
			
		strClass = ""
		if(labelobtmp[0:1]!="#"):
			strClass = labelobtmp
		
		self.strJsCss += "\t" + nome_idDiv+".style.position=\"absolute\";\n"
		self.strJsCss += "\t" + nome_idDiv+".style.left=\""+str(int(x0))+"px\";\n"
		self.strJsCss += "\t" + nome_idDiv+".style.top=\""+str(int(y0))+"px\";\n"
		self.strJsCss += "\t" + nome_idDiv+".style.width=\""+str(int(ww))+"px\";\n"
		self.strJsCss += "\t" + nome_idDiv+".style.height=\""+str(int(hh))+"px\";\n"
		
		if(isRedRect==False):
			self.strJsCss += "\t" + nome_idDiv+".style.backgroundImage=\"url('img/"+nome_img_file+"')\";\n"

		self.strJsCss += "\t" + nome_idDiv+".style.backgroundRepeat=\"no-repeat\";\n"

		self.strJsCss += "\t" + "//" + nome_idDiv+".style.pointerEvents=\"none\";\n"
		
		if(isRedRect==True):
			self.strJsCss += "\t" + nome_idDiv+".classList.add(\""+self.divevent+"\");\n"
			
		if(numIndice>=1):
			self.strJsCss += "\t" + "//" + nome_idDiv+".style.display=\"none\";\n//********\n"
		else:
			self.strJsCss += "\t" + "//" + nome_idDiv+".style.display=\"none\";\n//********\n"
		
		self.strHtm += strtab+"<div id=\""+nome_idDiv+"\" class=\"animated "+strClass+"\"></div>\n"

		
		if(isRedRect==False):
			self.commandActions = self.commandActions+" export-dpi:"+str(self.dpi)+";"
			if(self.soloselez==True):
				self.commandActions = self.commandActions+" export-id-only;"
			self.commandActions = self.commandActions+" export-id:"+svgid+"; export-area:"+s_bboxx0+":"+s_bboxy0+":"+s_bboxx1+":"+s_bboxy1+"; export-filename:"+nome_img_path+"; export-do; "

		self.strCss = ""
		
		self.strCss += "body{\n"
		self.strCss += "\tborder:0px solid none;\n"
		self.strCss += "\tmargin:0;\n"
		self.strCss += "}\n"

		self.strCss += "#"+self.sdoc+"Container{\n"
		self.strCss += "\t-webkit-transform:scale(0.5,0.5);\n"
		self.strCss += "\t-webkit-transform-origin: 0% 0%;\n"
		self.strCss += "\ttransform:scale(0.5,0.5);\n"
		self.strCss += "\ttransform-origin: 0% 0%;\n"
		self.strCss += "}\n"

		self.strCss += "."+self.divevent+"{\n"
		self.strCss += "\t/*border:1px solid red;*/\n"
		self.strCss += "\t/*background-color:red;*/\n"
		self.strCss += "\t/*opacity:0.5;*/\n"
		self.strCss += "}\n"


		self.strJs += "var "+nome_idDiv+";\n"
		self.arJs.append( nome_idDiv )

		retTxt1=""
		retTxt2=""
		if(isRedRect==True):
			retTxt1 = "" + nome_idDiv+".addEventListener(eventClick,menuAction,false);\n"
			retTxt2 = "\t\tcase " + nome_idDiv+":\n\t\t\tbreak;\n"
		return [retTxt1,retTxt2]

def main():
	exporter = HtmJsExporter()
	exporter.run()
	exit()

if __name__ == "__main__":
	main()

